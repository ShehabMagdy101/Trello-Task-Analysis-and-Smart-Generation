Your domain naturally has layers that should never be violated in the wrong direction:
┌─────────────────────────────────┐
│         Presentation            │  Streamlit pages, UI components
├─────────────────────────────────┤
│         Application             │  Orchestration — Today Generator,
│                                 │  Preplanner, Judger, Goal Tracker
├─────────────────────────────────┤
│           Domain                │  Task, Goal, Habit, UserContext
│                                 │  Pure business logic, no I/O
├─────────────────────────────────┤
│        Infrastructure           │  Trello API, Google Sheets,
│                                 │  CSV persistence, LLM calls
└─────────────────────────────────┘