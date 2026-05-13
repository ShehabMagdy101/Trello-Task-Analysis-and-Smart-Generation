from __future__ import annotations

import json
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import dotenv_values

from config import settings

st.set_page_config(page_title="Task Calendar", page_icon="📅", layout="wide")

LOCAL_EVENT_STORAGE_KEY = "smart-tasking-local-calendar-events"
SYNCFUSION_VERSION = "27.2.5"


def _to_utc_datetime(value: Any) -> pd.Timestamp | None:
    timestamp = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(timestamp):
        return None
    return timestamp


@st.cache_data
def load_pending_tasks() -> list[dict[str, Any]]:
    pending_path = Path(settings.PENDING_DATA_PATH)
    fallback_path = Path(settings.ALL_DATA_PATH)

    if pending_path.exists():
        tasks = pd.read_csv(pending_path)
    elif fallback_path.exists():
        tasks = pd.read_csv(fallback_path)
        if "status" in tasks.columns:
            tasks = tasks[tasks["status"] == "Not Done"]
    else:
        return []

    if "status" in tasks.columns:
        tasks = tasks[tasks["status"].fillna("Not Done") != "Done"]

    task_events: list[dict[str, Any]] = []
    today = datetime.now(timezone.utc).date()

    for index, row in tasks.iterrows():
        due_timestamp = _to_utc_datetime(row.get("card_due"))
        has_due_date = due_timestamp is not None
        if due_timestamp is None:
            due_date = today
        else:
            due_date = due_timestamp.date()

        start_time = datetime.combine(due_date, time(9, 0), tzinfo=timezone.utc)
        end_time = start_time + timedelta(hours=1)
        card_name = str(row.get("card") or "Untitled task")
        list_name = str(row.get("list") or "No Trello list")
        card_id = row.get("card_id")
        card_id = "" if pd.isna(card_id) else str(card_id)
        is_overdue = has_due_date and due_date < today

        task_events.append(
            {
                "Id": f"trello-{card_id or index}",
                "Subject": card_name,
                "StartTime": start_time.isoformat(),
                "EndTime": end_time.isoformat(),
                "IsAllDay": True,
                "Description": f"Trello list: {list_name}",
                "Location": list_name,
                "Source": "trello",
                "CardId": card_id,
                "IsReadonly": not bool(card_id),
                "HasDueDate": has_due_date,
                "IsOverdue": is_overdue,
                "CategoryColor": "#ef4444" if is_overdue else "#2563eb",
            }
        )

    return task_events


def render_calendar(task_events: list[dict[str, Any]], trello_credentials: dict[str, str | None]) -> None:
    payload = {
        "taskEvents": task_events,
        "trello": trello_credentials,
        "storageKey": LOCAL_EVENT_STORAGE_KEY,
    }
    payload_json = json.dumps(payload)

    component_html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link href="https://cdn.syncfusion.com/ej2/{SYNCFUSION_VERSION}/material.css" rel="stylesheet" />
  <script src="https://cdn.syncfusion.com/ej2/{SYNCFUSION_VERSION}/dist/ej2.min.js"></script>
  <style>
    :root {{
      color-scheme: light;
      --trello-blue: #2563eb;
      --overdue-red: #ef4444;
      --local-green: #16a34a;
      --muted: #64748b;
      --border: #e2e8f0;
      --surface: #ffffff;
      --soft: #f8fafc;
    }}

    body {{
      margin: 0;
      background: #f1f5f9;
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    .calendar-shell {{
      display: flex;
      flex-direction: column;
      gap: 14px;
      min-height: 100vh;
      padding: 12px;
      box-sizing: border-box;
    }}

    .toolbar-card {{
      align-items: center;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      box-shadow: 0 10px 25px rgba(15, 23, 42, 0.06);
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      justify-content: space-between;
      padding: 14px 16px;
    }}

    .headline h2 {{
      color: #0f172a;
      font-size: 20px;
      line-height: 1.2;
      margin: 0 0 4px;
    }}

    .headline p {{
      color: var(--muted);
      font-size: 13px;
      margin: 0;
    }}

    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }}

    .pill {{
      align-items: center;
      background: var(--soft);
      border: 1px solid var(--border);
      border-radius: 999px;
      color: #334155;
      display: inline-flex;
      font-size: 12px;
      font-weight: 600;
      gap: 7px;
      padding: 7px 10px;
    }}

    .dot {{
      border-radius: 999px;
      display: inline-block;
      height: 10px;
      width: 10px;
    }}

    .calendar-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      box-shadow: 0 10px 25px rgba(15, 23, 42, 0.06);
      overflow: hidden;
      padding: 10px;
    }}

    #Calendar {{ min-height: 760px; }}

    .status-bar {{
      background: #0f172a;
      border-radius: 12px;
      color: #e2e8f0;
      font-size: 12px;
      line-height: 1.45;
      padding: 10px 12px;
    }}

    .status-bar.error {{ background: #7f1d1d; }}
    .status-bar.success {{ background: #14532d; }}
    .status-bar.warn {{ background: #713f12; }}

    .e-schedule .e-appointment.trello-task {{ border-left: 5px solid var(--trello-blue); }}
    .e-schedule .e-appointment.overdue-task {{ border-left-color: var(--overdue-red); }}
    .e-schedule .e-appointment.local-event {{ border-left: 5px solid var(--local-green); }}
  </style>
</head>
<body>
  <div class="calendar-shell">
    <section class="toolbar-card">
      <div class="headline">
        <h2>Task Calendar</h2>
        <p>Drag Trello tasks to reschedule their due dates. Add or edit local-only events directly in this page.</p>
      </div>
      <div class="legend">
        <span class="pill"><span class="dot" style="background: var(--trello-blue)"></span>Trello pending task</span>
        <span class="pill"><span class="dot" style="background: var(--overdue-red)"></span>Overdue task</span>
        <span class="pill"><span class="dot" style="background: var(--local-green)"></span>Local calendar event</span>
      </div>
    </section>
    <div id="status" class="status-bar">Loading calendar…</div>
    <section class="calendar-card"><div id="Calendar"></div></section>
  </div>
  <script>
    const payload = {payload_json};
    const taskEvents = payload.taskEvents.map((event) => normalizeEventDates(event));
    const trello = payload.trello || {{}};
    const storageKey = payload.storageKey;

    function normalizeEventDates(event) {{
      return {{
        ...event,
        StartTime: new Date(event.StartTime),
        EndTime: new Date(event.EndTime),
      }};
    }}

    function serializeLocalEvent(event) {{
      return {{
        ...event,
        StartTime: new Date(event.StartTime).toISOString(),
        EndTime: new Date(event.EndTime).toISOString(),
      }};
    }}

    function getLocalEvents() {{
      try {{
        const raw = window.localStorage.getItem(storageKey);
        if (!raw) return [];
        return JSON.parse(raw).map((event) => normalizeEventDates(event));
      }} catch (error) {{
        console.warn('Could not read local events', error);
        return [];
      }}
    }}

    function saveLocalEvents(events) {{
      const localEvents = events
        .filter((event) => event.Source === 'local')
        .map((event) => serializeLocalEvent(event));
      window.localStorage.setItem(storageKey, JSON.stringify(localEvents));
    }}

    function showStatus(message, type = '') {{
      const status = document.getElementById('status');
      status.textContent = message;
      status.className = `status-bar ${{type}}`;
    }}

    function dueIsoForTrello(startTime) {{
      const due = new Date(startTime);
      due.setHours(20, 59, 0, 0);
      return due.toISOString();
    }}

    async function updateTrelloDueDate(event) {{
      if (event.Source !== 'trello') return;
      if (!event.CardId) throw new Error('This Trello task does not have a card id in the local dataset. Refresh data first.');
      if (!trello.apiKey || !trello.apiToken) throw new Error('Missing Trello API credentials in app.env.');

      const params = new URLSearchParams({{
        key: trello.apiKey,
        token: trello.apiToken,
        due: dueIsoForTrello(event.StartTime),
      }});
      const response = await fetch(`https://api.trello.com/1/cards/${{encodeURIComponent(event.CardId)}}?${{params.toString()}}`, {{
        method: 'PUT',
      }});
      if (!response.ok) {{
        const detail = await response.text();
        throw new Error(`Trello update failed (${{response.status}}): ${{detail.slice(0, 180)}}`);
      }}
    }}

    function normalizeCreatedEvent(event) {{
      if (!event.Id) event.Id = `local-${{Date.now()}}-${{Math.round(Math.random() * 100000)}}`;
      if (!event.Source) event.Source = 'local';
      if (!event.CategoryColor) event.CategoryColor = '#16a34a';
      event.IsReadonly = false;
      return event;
    }}

    ej.schedule.Schedule.Inject(
      ej.schedule.Day,
      ej.schedule.Week,
      ej.schedule.WorkWeek,
      ej.schedule.Month,
      ej.schedule.Agenda,
      ej.schedule.DragAndDrop,
      ej.schedule.Resize
    );

    const scheduleObj = new ej.schedule.Schedule({{
      height: '760px',
      width: '100%',
      selectedDate: new Date(),
      currentView: 'Week',
      views: ['Day', 'Week', 'WorkWeek', 'Month', 'Agenda'],
      allowDragAndDrop: true,
      allowResizing: true,
      eventSettings: {{
        dataSource: [...taskEvents, ...getLocalEvents()],
        fields: {{
          id: 'Id',
          subject: {{ name: 'Subject', title: 'Title' }},
          startTime: {{ name: 'StartTime', title: 'Start' }},
          endTime: {{ name: 'EndTime', title: 'End' }},
          description: {{ name: 'Description', title: 'Notes' }},
          isAllDay: {{ name: 'IsAllDay' }},
        }},
      }},
      eventRendered: function(args) {{
        const data = args.data;
        args.element.style.backgroundColor = data.CategoryColor || (data.Source === 'local' ? '#16a34a' : '#2563eb');
        args.element.classList.add(data.Source === 'local' ? 'local-event' : 'trello-task');
        if (data.IsOverdue) args.element.classList.add('overdue-task');
      }},
      popupOpen: function(args) {{
        if (args.type === 'Editor' && args.data && args.data.Source === 'trello') {{
          args.cancel = true;
          showStatus('Trello tasks are edited by dragging them to a new date. Use Trello for title/details edits.', 'warn');
        }}
      }},
      actionBegin: function(args) {{
        if (args.requestType === 'eventCreate') {{
          const records = Array.isArray(args.data) ? args.data : [args.data];
          records.forEach(normalizeCreatedEvent);
        }}

        if (args.requestType === 'eventRemove') {{
          const records = Array.isArray(args.data) ? args.data : [args.data];
          if (records.some((event) => event.Source === 'trello')) {{
            args.cancel = true;
            showStatus('Trello tasks cannot be deleted from the calendar. Move or close them in Trello instead.', 'warn');
          }}
        }}
      }},
      actionComplete: async function(args) {{
        if (['eventCreated', 'eventChanged', 'eventRemoved'].includes(args.requestType)) {{
          saveLocalEvents(scheduleObj.eventsData);
        }}

        if (args.requestType === 'eventChanged') {{
          const changedEvents = Array.isArray(args.data) ? args.data : [args.data];
          for (const event of changedEvents) {{
            if (event.Source === 'trello') {{
              try {{
                await updateTrelloDueDate(event);
                event.IsOverdue = new Date(event.StartTime).setHours(0, 0, 0, 0) < new Date().setHours(0, 0, 0, 0);
                event.CategoryColor = event.IsOverdue ? '#ef4444' : '#2563eb';
                showStatus(`Synced “${{event.Subject}}” to Trello for ${{new Date(event.StartTime).toLocaleDateString()}}. Refresh data to update CSV reports.`, 'success');
              }} catch (error) {{
                showStatus(error.message, 'error');
              }}
            }}
          }}
        }}
      }},
      dataBound: function() {{
        const overdueCount = taskEvents.filter((event) => event.IsOverdue).length;
        showStatus(`${{taskEvents.length}} pending Trello tasks loaded (${{overdueCount}} overdue). Local events are saved in this browser only.`);
      }},
    }});

    scheduleObj.appendTo('#Calendar');
  </script>
</body>
</html>
"""
    components.html(component_html, height=980, scrolling=True)


st.title("📅 Calendar")
st.caption(
    "Use Week or Month view to schedule pending Trello tasks. Dragging a Trello task updates its card due date; "
    "events you create here stay local to this browser and do not touch Trello."
)

credentials = dotenv_values("./app.env")
trello_credentials = {
    "apiKey": credentials.get("TRELLO_API_KEY"),
    "apiToken": credentials.get("TRELLO_API_TOKEN"),
}

pending_events = load_pending_tasks()
if not pending_events:
    st.warning(
        f"No pending tasks were found. Refresh Trello data or check {settings.PENDING_DATA_PATH}."
    )

render_calendar(pending_events, trello_credentials)
