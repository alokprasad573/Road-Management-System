from __future__ import annotations

from datetime import datetime

from flask import Response

from storage import (
    get_all_potholes,
    get_counts,
    get_hourly_counts,
    get_severity_counts,
    get_status_counts,
    get_zone_counts,
)

try:
    import dash
    import plotly.graph_objects as go
    from dash import Input, Output, State, callback_context, dash_table, dcc, html
except ImportError:  # pragma: no cover
    dash = None
    go = None
    Input = Output = State = callback_context = dash_table = dcc = html = None


COLORS = {
    "bg": "#0b0f1a",
    "panel": "#111827",
    "orange": "#f97316",
    "green": "#22c55e",
    "red": "#ef4444",
    "yellow": "#eab308",
    "blue": "#38bdf8",
    "text": "#e5e7eb",
    "muted": "#94a3b8",
}


def mount_dashboard(server):
    """Mount the Plotly Dash dashboard on the shared Flask server."""
    if dash is None:
        @server.get("/dashboard/")
        def dashboard_unavailable() -> Response:
            return Response(
                "<h1>RoadWatch AI Dashboard</h1><p>Dash is not installed in this environment.</p>",
                mimetype="text/html",
            )

        print("[DASH][WARN] Dash is not installed. Serving fallback dashboard route.")
        return None

    app = dash.Dash(
        __name__,
        server=server,
        routes_pathname_prefix="/dashboard/",
        suppress_callback_exceptions=True,
    )
    app.title = "RoadWatch AI Dashboard"
    app.layout = _build_layout()
    _register_callbacks(app)
    return app


def _panel_style() -> dict:
    """Shared style for dashboard panels."""
    return {
        "backgroundColor": COLORS["panel"],
        "border": "1px solid #1f2937",
        "borderRadius": "18px",
        "padding": "18px",
        "boxShadow": "0 12px 30px rgba(0,0,0,0.2)",
    }


def _card(title: str, value_id: str, color: str):
    """Create a statistic card component."""
    return html.Div(
        [
            html.Div(title, style={"color": COLORS["muted"], "fontSize": "12px"}),
            html.Div(id=value_id, style={"color": color, "fontSize": "30px", "fontWeight": "700"}),
        ],
        style=_panel_style(),
    )


def _filter_button_style(color: str) -> dict:
    """Return shared styling for filter buttons."""
    return {
        "backgroundColor": color,
        "color": "#05070d",
        "border": "none",
        "borderRadius": "999px",
        "padding": "8px 14px",
        "fontWeight": "700",
        "cursor": "pointer",
    }

def _chart_layout(title: str) -> dict:
    """Return shared Plotly chart layout settings."""
    return {
        "title": {"text": title, "font": {"color": COLORS["text"]}},
        "paper_bgcolor": COLORS["panel"],
        "plot_bgcolor": COLORS["panel"],
        "font": {"color": COLORS["text"], "family": "'IBM Plex Mono', 'Courier New', monospace"},
        "margin": {"l": 40, "r": 20, "t": 50, "b": 30},
    }


def _build_layout():
    """Create the dashboard layout."""
    return html.Div(
        [
            dcc.Interval(id="refresh", interval=3000, n_intervals=0),
            dcc.Store(id="status-filter", data="All"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div("ROADWATCH AI", style={"fontSize": "36px", "fontWeight": "700"}),
                            html.Div(
                                "AUTHORITY OPERATIONS CENTER · LIVE",
                                style={"color": COLORS["muted"], "marginTop": "6px"},
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Div(id="live-clock", style={"fontSize": "20px", "textAlign": "right"}),
                            html.Div(
                                "LIVE",
                                style={
                                    "marginTop": "8px",
                                    "display": "inline-block",
                                    "padding": "6px 12px",
                                    "backgroundColor": COLORS["green"],
                                    "color": "#03130a",
                                    "borderRadius": "999px",
                                    "fontWeight": "700",
                                },
                            ),
                        ]
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "marginBottom": "20px",
                },
            ),
            html.Div(
                [
                    _card("Potholes Detected", "card-total", COLORS["blue"]),
                    _card("Pending Repair", "card-pending", COLORS["red"]),
                    _card("In Progress", "card-progress", COLORS["yellow"]),
                    _card("Fixed", "card-fixed", COLORS["green"]),
                    _card("High Severity", "card-high", COLORS["orange"]),
                    _card("Fix Rate %", "card-rate", COLORS["green"]),
                ],
                style={"display": "grid", "gridTemplateColumns": "repeat(6, 1fr)", "gap": "14px", "marginBottom": "20px"},
            ),
            html.Div(
                [
                    dcc.Graph(id="hourly-chart", style=_panel_style()),
                    dcc.Graph(id="status-chart", style=_panel_style()),
                    dcc.Graph(id="severity-chart", style=_panel_style()),
                ],
                style={"display": "grid", "gridTemplateColumns": "1.5fr 1fr 1fr", "gap": "14px", "marginBottom": "20px"},
            ),
            html.Div(
                [
                    dcc.Graph(id="zone-chart", style=_panel_style()),
                    dcc.Graph(id="funnel-chart", style=_panel_style()),
                ],
                style={"display": "grid", "gridTemplateColumns": "1.5fr 1fr", "gap": "14px", "marginBottom": "20px"},
            ),
            html.Div(id="zone-progress", style={**_panel_style(), "marginBottom": "20px"}),
            html.Div(
                [
                    html.Div(
                        [
                            html.Button("All", id="filter-all", n_clicks=0, style=_filter_button_style(COLORS["blue"])),
                            html.Button("Pending", id="filter-pending", n_clicks=0, style=_filter_button_style(COLORS["red"])),
                            html.Button("In Progress", id="filter-progress", n_clicks=0, style=_filter_button_style(COLORS["yellow"])),
                            html.Button("Fixed", id="filter-fixed", n_clicks=0, style=_filter_button_style(COLORS["green"])),
                        ],
                        style={"display": "flex", "gap": "10px", "marginBottom": "12px"},
                    ),
                    dash_table.DataTable(
                        id="live-table",
                        columns=[
                            {"name": "Type", "id": "hazard_type"},
                            {"name": "Zone", "id": "zone"},
                            {"name": "Address", "id": "address"},
                            {"name": "Severity", "id": "severity"},
                            {"name": "Status", "id": "status"},
                            {"name": "Maps Link", "id": "maps_link", "presentation": "markdown"},
                            {"name": "Time", "id": "timestamp"},
                        ],
                        style_as_list_view=True,
                        style_header={"backgroundColor": "#172033", "color": COLORS["text"], "border": "none"},
                        style_cell={
                            "backgroundColor": COLORS["panel"],
                            "color": COLORS["text"],
                            "border": "none",
                            "padding": "10px",
                            "fontFamily": "'IBM Plex Mono', 'Courier New', monospace",
                            "textAlign": "left",
                            "whiteSpace": "normal",
                            "height": "auto",
                        },
                        style_data_conditional=[
                            {"if": {"filter_query": '{status} = "Pending"'}, "color": COLORS["red"]},
                            {"if": {"filter_query": '{status} = "Fixed"'}, "color": COLORS["green"]},
                            {"if": {"filter_query": '{status} = "In Progress"'}, "color": COLORS["yellow"]},
                        ],
                        page_size=20,
                    ),
                ],
                style=_panel_style(),
            ),
        ],
        style={
            "minHeight": "100vh",
            "background": "radial-gradient(circle at top left, #172033 0%, #0b0f1a 55%)",
            "padding": "24px",
            "fontFamily": "'IBM Plex Mono', 'Courier New', monospace",
            "color": COLORS["text"],
        },
    )


def _register_callbacks(app) -> None:
    """Register dashboard callbacks."""

    @app.callback(
        Output("card-total", "children"),
        Output("card-pending", "children"),
        Output("card-progress", "children"),
        Output("card-fixed", "children"),
        Output("card-high", "children"),
        Output("card-rate", "children"),
        Output("live-clock", "children"),
        Input("refresh", "n_intervals"),
    )
    def update_cards(_: int):
        counts = get_counts()
        fix_rate = round((counts["fixed"] / counts["total"]) * 100, 2) if counts["total"] else 0.0
        return (
            counts["total"],
            counts["pending"],
            counts["in_progress"],
            counts["fixed"],
            counts["high_severity"],
            f"{fix_rate}%",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    @app.callback(
        Output("hourly-chart", "figure"),
        Output("status-chart", "figure"),
        Output("severity-chart", "figure"),
        Output("zone-chart", "figure"),
        Output("funnel-chart", "figure"),
        Output("zone-progress", "children"),
        Input("refresh", "n_intervals"),
    )
    def update_charts(_: int):
        hourly = get_hourly_counts(hours=8)
        statuses = get_status_counts()
        severities = get_severity_counts()
        zones = get_zone_counts()
        counts = get_counts()
        records = get_all_potholes(limit=10000)

        hourly_fig = go.Figure(
            go.Scatter(
                x=[item["hour"] for item in hourly],
                y=[item["count"] for item in hourly],
                fill="tozeroy",
                line={"color": COLORS["blue"], "width": 3},
            )
        )
        hourly_fig.update_layout(_chart_layout("Hourly Detections"))

        status_fig = go.Figure(
            go.Pie(
                labels=list(statuses.keys()),
                values=list(statuses.values()),
                hole=0.55,
                marker={"colors": [COLORS["red"], COLORS["green"], COLORS["yellow"]]},
            )
        )
        status_fig.update_layout(_chart_layout("Repair Status"))

        severity_fig = go.Figure(
            go.Pie(
                labels=list(severities.keys()),
                values=list(severities.values()),
                hole=0.55,
                marker={"colors": [COLORS["orange"], COLORS["yellow"], COLORS["blue"]]},
            )
        )
        severity_fig.update_layout(_chart_layout("Severity Split"))

        zone_fig = go.Figure(
            go.Bar(
                x=[item["count"] for item in zones],
                y=[item["zone"] for item in zones],
                orientation="h",
                marker={"color": COLORS["blue"]},
            )
        )
        zone_fig.update_layout(_chart_layout("Zones Ranked"))

        funnel_fig = go.Figure(
            go.Funnel(
                y=["Detected", "In Progress", "Fixed"],
                x=[counts["total"], counts["in_progress"], counts["fixed"]],
                marker={"color": [COLORS["blue"], COLORS["yellow"], COLORS["green"]]},
            )
        )
        funnel_fig.update_layout(_chart_layout("Repair Funnel"))

        progress_blocks = []
        for item in zones[:8]:
            zone = item["zone"]
            total = item["count"]
            fixed_zone = sum(1 for record in records if record.get("zone") == zone and record.get("status") == "Fixed")
            resolved = round((fixed_zone / total) * 100, 2) if total else 0.0
            progress_blocks.append(
                html.Div(
                    [
                        html.Div(f"{zone} · {resolved}%", style={"marginBottom": "6px"}),
                        html.Div(
                            html.Div(
                                style={
                                    "width": f"{resolved}%",
                                    "height": "10px",
                                    "backgroundColor": COLORS["green"],
                                    "borderRadius": "999px",
                                }
                            ),
                            style={"backgroundColor": "#1f2937", "borderRadius": "999px"},
                        ),
                    ],
                    style={"marginBottom": "14px"},
                )
            )
        return hourly_fig, status_fig, severity_fig, zone_fig, funnel_fig, progress_blocks

    @app.callback(
        Output("status-filter", "data"),
        Input("filter-all", "n_clicks"),
        Input("filter-pending", "n_clicks"),
        Input("filter-progress", "n_clicks"),
        Input("filter-fixed", "n_clicks"),
        State("status-filter", "data"),
    )
    def update_filter(_: int, __: int, ___: int, ____: int, current: str):
        trigger = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else ""
        mapping = {
            "filter-all": "All",
            "filter-pending": "Pending",
            "filter-progress": "In Progress",
            "filter-fixed": "Fixed",
        }
        return mapping.get(trigger, current)

    @app.callback(
        Output("live-table", "data"),
        Input("refresh", "n_intervals"),
        Input("status-filter", "data"),
    )
    def update_table(_: int, status_filter: str):
        records = get_all_potholes(limit=20)
        if status_filter != "All":
            records = [record for record in records if record.get("status") == status_filter]
        for record in records:
            record["maps_link"] = f"[Open Map]({record.get('maps_link', '#')})"
        return records
