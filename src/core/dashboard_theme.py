"""Centralized color settings for the dashboard charts.

Edit values here to update the dashboard color palette globally.
"""

DASHBOARD_COLORS = {
    "categorical": [
        "#4F46E5",  # indigo
        "#0EA5E9",  # sky
        "#14B8A6",  # teal
        "#22C55E",  # green
        "#F59E0B",  # amber
        "#F97316",  # orange
        "#EF4444",  # red
        "#A855F7",  # purple
    ],
    "continuous_scale": "Blues",
    "heatmap_scale": "Blues",
    "qualitative_fallback": [
        "#60A5FA",
        "#34D399",
        "#FBBF24",
        "#F87171",
        "#A78BFA",
        "#22D3EE",
    ],
    "dark": {
        "template": "plotly_dark",
        "paper_bg": "#111111",
        "plot_bg": "#111111",
        "font": "white",
        "grid": "gray",
    },
}
