import os

from dash import Dash, Input, Output, dcc, html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


DATA_FILE = "8 May 2025 - 7 May 2026 @haqyxd.csv"

COLORS = {
    "bg": "#F5F7FA",
    "panel": "#FFFFFF",
    "ink": "#172033",
    "muted": "#667085",
    "line": "#D9E2EC",
    "navy": "#102A43",
    "teal": "#006D77",
    "aqua": "#37B7C3",
    "gold": "#D99A21",
    "red": "#C24141",
    "green": "#138A63",
    "purple": "#6D5BD0",
}

METRICS = ["Video Views", "Profile Views", "Likes", "Comments", "Shares", "Total Engagement"]
PERFORMANCE_METRICS = METRICS + ["Interaction Rate"]
MIX_METRICS = ["Likes", "Profile Views", "Shares", "Comments"]


df = pd.read_csv(DATA_FILE)
df.columns = df.columns.str.strip()
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
df = df.drop_duplicates()
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
df = df.sort_values("Date")

for metric in METRICS:
    df[metric] = pd.to_numeric(df[metric], errors="coerce").fillna(0)

summary_row_removed = False
if len(df) > 1:
    last_row = df.iloc[-1][METRICS]
    previous_totals = df.iloc[:-1][METRICS].sum()
    if (last_row - previous_totals).abs().le(0.001).all():
        df = df.iloc[:-1].copy()
        summary_row_removed = True

df["Month"] = df["Date"].dt.strftime("%b %Y")
df["Month Sort"] = df["Date"].dt.to_period("M")
df["Engagement Rate"] = (df["Total Engagement"] / df["Video Views"]).where(df["Video Views"] > 0, 0)
df["Interaction Rate"] = ((df["Likes"] + df["Comments"] + df["Shares"]) / df["Video Views"]).where(
    df["Video Views"] > 0, 0
)
data_start = df["Date"].min()
data_end = df["Date"].max()
reporting_period = f"{data_start:%d %b %Y} - {data_end:%d %b %Y}"


app = Dash(__name__)
app.title = "HaqyXD Business Analytics"


def compact_number(value):
    value = float(value or 0)
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def metric_options(extra=None, include_rates=False):
    items = PERFORMANCE_METRICS.copy() if include_rates else METRICS.copy()
    if extra:
        items.extend(extra)
    return [{"label": item, "value": item} for item in items]


def month_options():
    months = df.sort_values("Month Sort")["Month"].drop_duplicates()
    return [{"label": "All Months", "value": "All"}] + [{"label": m, "value": m} for m in months]


def radio(id_name, options, value):
    return dcc.RadioItems(
        id=id_name,
        options=options,
        value=value,
        className="segmented",
        inputClassName="segmented-input",
        labelClassName="segmented-option",
    )


def kpi(label, value, note, tone="teal"):
    return html.Div(
        [
            html.Div(className=f"kpi-bar {tone}"),
            html.P(label, className="kpi-label"),
            html.H2(value, className="kpi-value"),
            html.P(note, className="kpi-note"),
        ],
        className="kpi-card",
    )


def chart_card(title, description, controls, graph_id, wide=False):
    classes = "chart-card chart-wide" if wide else "chart-card"
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.P("Interactive analysis", className="section-kicker"),
                            html.H3(title),
                            html.P(description, className="chart-description"),
                        ],
                        className="chart-heading",
                    ),
                    html.Div(controls, className="chart-controls"),
                ],
                className="chart-head",
            ),
            dcc.Graph(id=graph_id, config={"displayModeBar": False}, className="graph"),
        ],
        className=classes,
    )


def guide_item(title, body):
    return html.Div([html.Span(title), html.Strong(body)], className="guide-item")


def control_group(label, child):
    return html.Div([html.Span(label), child], className="control-group")


def insight_item(title, body, tone="teal"):
    return html.Div(
        [
            html.Div(className=f"insight-marker {tone}"),
            html.Div([html.Span(title), html.Strong(body)]),
        ],
        className="insight-item",
    )


def style_figure(fig, height=390):
    fig.update_layout(
        height=height,
        template="plotly_white",
        paper_bgcolor=COLORS["panel"],
        plot_bgcolor=COLORS["panel"],
        font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=12, color=COLORS["ink"]),
        margin=dict(l=64, r=34, t=26, b=56),
        hoverlabel=dict(bgcolor=COLORS["navy"], font_color="white", font_size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=True, gridcolor=COLORS["line"], zeroline=False, linecolor=COLORS["line"])
    fig.update_yaxes(showgrid=True, gridcolor=COLORS["line"], zeroline=False, linecolor=COLORS["line"])
    return fig


def empty_figure(message="No data available"):
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=14, color=COLORS["muted"]),
    )
    return style_figure(fig)


def filter_data(selected_month, start_date, end_date):
    dff = df.copy()
    if selected_month != "All":
        dff = dff[dff["Month"] == selected_month]
    if start_date and end_date:
        dff = dff[
            (dff["Date"] >= pd.to_datetime(start_date))
            & (dff["Date"] <= pd.to_datetime(end_date))
        ]
    return dff.sort_values("Date")


@app.callback(
    Output("month-filter", "value"),
    Output("date-range", "start_date"),
    Output("date-range", "end_date"),
    Output("trend-metric", "value"),
    Output("trend-agg", "value"),
    Output("trend-scale", "value"),
    Output("rank-metric", "value"),
    Output("rank-count", "value"),
    Output("rank-scale", "value"),
    Output("mix-mode", "value"),
    Output("heatmap-metric", "value"),
    Output("scatter-x", "value"),
    Output("scatter-y", "value"),
    Output("scatter-scale", "value"),
    Input("reset-button", "n_clicks"),
    prevent_initial_call=True,
)
def reset_dashboard(_):
    return (
        "All",
        data_start.date(),
        data_end.date(),
        "Video Views",
        "W",
        "linear",
        "Interaction Rate",
        10,
        "linear",
        "bar",
        "Video Views",
        "Video Views",
        "Likes",
        "log",
    )


app.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.P("Business analytics dashboard", className="eyebrow"),
                        html.H1("HaqyXD TikTok Performance Intelligence"),
                        html.P(
                            "A clear, decision-ready view of daily reach, engagement, spikes, and audience response.",
                            className="subtitle",
                        ),
                    ],
                    className="hero-copy",
                ),
                html.Div(
                    [
                        html.Div([html.Span("Daily data period"), html.Strong(reporting_period)], className="hero-stat"),
                        html.Div([html.Span("Peak day views"), html.Strong(compact_number(df["Video Views"].max()))], className="hero-stat"),
                        html.Div([html.Span("Total engagement"), html.Strong(compact_number(df["Total Engagement"].sum()))], className="hero-stat"),
                    ],
                    className="hero-stats",
                ),
            ],
            className="hero",
        ),
        html.Div(
            [
                guide_item("1. Filter", "Narrow the month or date range to focus the analysis."),
                guide_item("2. Interact", "Click trend points, ranked bars, or scatter points for drill-down details."),
                guide_item("3. Interpret", "Use insights, heatmap, and recommendations to explain patterns."),
            ],
            className="guide-panel",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Month"),
                        dcc.Dropdown(id="month-filter", options=month_options(), value="All", clearable=False),
                    ],
                    className="filter-item",
                ),
                html.Div(
                    [
                        html.Label("Date range"),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=data_start,
                            max_date_allowed=data_end,
                            start_date=data_start,
                            end_date=data_end,
                            display_format="DD MMM YYYY",
                        ),
                    ],
                    className="filter-item date-item",
                ),
                html.Button("Reset Filters", id="reset-button", n_clicks=0, className="reset-button"),
            ],
            className="filter-panel",
        ),
        html.Div(id="filter-summary", className="filter-summary"),
        html.Div(id="kpis", className="kpi-grid"),
        html.Div(id="story", className="story-panel"),
        html.Div(
            [
                chart_card(
                    "Performance trend",
                    "Shows how the selected metric changes over time. Use aggregation to reduce noise without hiding the real scale.",
                    [
                        control_group(
                            "Metric",
                            dcc.Dropdown(id="trend-metric", options=metric_options(), value="Video Views", clearable=False),
                        ),
                        control_group(
                            "Aggregation",
                            radio(
                                "trend-agg",
                                [
                                    {"label": "Daily", "value": "D"},
                                    {"label": "Weekly", "value": "W"},
                                    {"label": "Monthly", "value": "ME"},
                                ],
                                "W",
                            ),
                        ),
                        control_group(
                            "Axis scale",
                            radio(
                                "trend-scale",
                                [
                                    {"label": "Linear", "value": "linear"},
                                    {"label": "Log", "value": "log"},
                                ],
                                "linear",
                            ),
                        ),
                    ],
                    "trend-chart",
                    wide=True,
                ),
                chart_card(
                    "Ranked performance",
                    "Ranks best-performing days by quality or volume. Click any bar to drill into that exact day.",
                    [
                        control_group(
                            "Metric",
                            dcc.Dropdown(
                                id="rank-metric",
                                options=metric_options(include_rates=True),
                                value="Interaction Rate",
                                clearable=False,
                            ),
                        ),
                        control_group(
                            "Rows",
                            radio(
                                "rank-count",
                                [
                                    {"label": "5", "value": 5},
                                    {"label": "10", "value": 10},
                                    {"label": "15", "value": 15},
                                ],
                                10,
                            ),
                        ),
                        control_group(
                            "Axis scale",
                            radio(
                                "rank-scale",
                                [
                                    {"label": "Linear", "value": "linear"},
                                    {"label": "Log", "value": "log"},
                                ],
                                "linear",
                            ),
                        ),
                    ],
                    "rank-chart",
                ),
                html.Div(id="detail-panel", className="detail-card"),
                chart_card(
                    "Engagement mix",
                    "Shows the share of audience actions. This helps identify whether engagement is driven by likes, shares, comments, or profile visits.",
                    [
                        control_group(
                            "View",
                            radio(
                                "mix-mode",
                                [
                                    {"label": "Bar", "value": "bar"},
                                    {"label": "Donut", "value": "donut"},
                                ],
                                "bar",
                            ),
                        )
                    ],
                    "mix-chart",
                ),
                chart_card(
                    "Timing pattern heatmap",
                    "Reveals when performance clusters by month and day of week. Darker cells indicate stronger activity.",
                    [
                        control_group(
                            "Metric",
                            dcc.Dropdown(id="heatmap-metric", options=metric_options(), value="Video Views", clearable=False),
                        )
                    ],
                    "heatmap-chart",
                ),
                chart_card(
                    "Metric relationship",
                    "Compares any two metrics to reveal whether reach is translating into engagement.",
                    [
                        control_group(
                            "X-axis",
                            dcc.Dropdown(id="scatter-x", options=metric_options(), value="Video Views", clearable=False),
                        ),
                        control_group(
                            "Y-axis",
                            dcc.Dropdown(id="scatter-y", options=metric_options(["Engagement Rate"]), value="Likes", clearable=False),
                        ),
                        control_group(
                            "Axis scale",
                            radio(
                                "scatter-scale",
                                [
                                    {"label": "Linear", "value": "linear"},
                                    {"label": "Log", "value": "log"},
                                ],
                                "log",
                            ),
                        ),
                    ],
                    "scatter-chart",
                    wide=True,
                ),
            ],
            className="chart-grid",
        ),
        html.Div(id="recommendations", className="recommendation-panel"),
        html.Div(
            [
                html.Span("Prepared for SCCVK3133 Data Visualization"),
                html.Strong("HaqyXD TikTok Analytics Dashboard"),
                html.Span("Built with Python Dash and Plotly"),
            ],
            className="dashboard-footer",
        ),
    ],
    className="page",
)


@app.callback(
    Output("filter-summary", "children"),
    Output("kpis", "children"),
    Output("story", "children"),
    Output("recommendations", "children"),
    Output("trend-chart", "figure"),
    Output("rank-chart", "figure"),
    Output("mix-chart", "figure"),
    Output("heatmap-chart", "figure"),
    Output("scatter-chart", "figure"),
    Output("detail-panel", "children"),
    Input("month-filter", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("trend-metric", "value"),
    Input("trend-agg", "value"),
    Input("trend-scale", "value"),
    Input("rank-metric", "value"),
    Input("rank-count", "value"),
    Input("rank-scale", "value"),
    Input("mix-mode", "value"),
    Input("heatmap-metric", "value"),
    Input("scatter-x", "value"),
    Input("scatter-y", "value"),
    Input("scatter-scale", "value"),
    Input("trend-chart", "clickData"),
    Input("rank-chart", "clickData"),
    Input("scatter-chart", "clickData"),
)
def update_dashboard(
    selected_month,
    start_date,
    end_date,
    trend_metric,
    trend_agg,
    trend_scale,
    rank_metric,
    rank_count,
    rank_scale,
    mix_mode,
    heatmap_metric,
    scatter_x,
    scatter_y,
    scatter_scale,
    trend_click,
    rank_click,
    scatter_click,
):
    dff = filter_data(selected_month, start_date, end_date)
    if dff.empty:
        filter_summary = build_filter_summary(selected_month, start_date, end_date, dff)
        cards = [
            kpi("Total Views", "0", "No records"),
            kpi("Total Engagement", "0", "No records"),
            kpi("Peak Reach Day", "-", "No records", "gold"),
            kpi("Best Efficiency Day", "-", "No records"),
        ]
        story = html.Div("No records match the selected filters.", className="story-copy")
        recommendations = html.Div("No recommendations available for the selected filters.", className="story-copy")
        detail = build_empty_detail_panel()
        return (
            filter_summary,
            cards,
            story,
            recommendations,
            empty_figure(),
            empty_figure(),
            empty_figure(),
            empty_figure(),
            empty_figure(),
            detail,
        )

    total_views = dff["Video Views"].sum()
    total_engagement = dff["Total Engagement"].sum()
    peak_reach_row = dff.loc[dff["Video Views"].idxmax()]
    best_efficiency_row = dff.loc[dff["Interaction Rate"].idxmax()]

    filter_summary = build_filter_summary(selected_month, start_date, end_date, dff)
    cards = [
        kpi("Total Views", compact_number(total_views), f"{len(dff):,} reporting days"),
        kpi("Total Engagement", compact_number(total_engagement), "Source-defined total engagement"),
        kpi("Peak Reach Day", peak_reach_row["Date"].strftime("%d %b %Y"), f"{compact_number(peak_reach_row['Video Views'])} video views", "gold"),
        kpi("Best Efficiency Day", best_efficiency_row["Date"].strftime("%d %b %Y"), f"{best_efficiency_row['Interaction Rate']:.2%} interaction rate"),
    ]

    trend_median = dff[trend_metric].median()
    trend_peak = dff.loc[dff[trend_metric].idxmax()]
    story = build_story_panel(dff, trend_metric, rank_metric)

    trend_fig = make_trend_chart(dff, trend_metric, trend_agg, trend_scale)
    rank_fig = make_rank_chart(dff, rank_metric, rank_count, rank_scale)
    mix_fig = make_mix_chart(dff, mix_mode)
    heatmap_fig = make_heatmap_chart(dff, heatmap_metric)
    scatter_fig = make_scatter_chart(dff, scatter_x, scatter_y, scatter_scale)
    detail = build_detail_panel(dff, trend_metric, trend_click, rank_click, scatter_click)
    recommendations = build_recommendation_panel(dff)

    return filter_summary, cards, story, recommendations, trend_fig, rank_fig, mix_fig, heatmap_fig, scatter_fig, detail


def build_story_panel(dff, trend_metric, rank_metric):
    trend_median = dff[trend_metric].median()
    trend_peak = dff.loc[dff[trend_metric].idxmax()]
    mix_totals = {metric: dff[metric].sum() for metric in MIX_METRICS}
    top_action = max(mix_totals, key=mix_totals.get)
    top_action_share = mix_totals[top_action] / sum(mix_totals.values()) if sum(mix_totals.values()) else 0
    best_efficiency = dff.loc[dff["Interaction Rate"].idxmax()]
    peak_rank = dff.loc[dff[rank_metric].idxmax()]

    return html.Div(
        [
            insight_item(
                "Key trend",
                f"{trend_metric} normally sits around {compact_number(trend_median)} per day, "
                f"with the strongest spike on {trend_peak['Date']:%d %b %Y} "
                f"at {compact_number(trend_peak[trend_metric])}.",
                "teal",
            ),
            insight_item(
                "Engagement driver",
                f"{top_action} contributes {top_action_share:.1%} of measured audience actions, "
                "so engagement is currently concentrated in one dominant behaviour.",
                "gold",
            ),
            insight_item(
                "Recommendation",
                f"Review content posted around {best_efficiency['Date']:%d %b %Y} "
                f"({best_efficiency['Interaction Rate']:.2%} interaction rate) and compare it with "
                f"{peak_rank['Date']:%d %b %Y}, the current leader for {rank_metric.lower()}.",
                "purple",
            ),
        ],
        className="insight-grid",
    )


def build_recommendation_panel(dff):
    top_views_day = dff.loc[dff["Video Views"].idxmax()]
    top_efficiency_day = dff.loc[dff["Interaction Rate"].idxmax()]
    mix_totals = {metric: dff[metric].sum() for metric in MIX_METRICS}
    total_actions = sum(mix_totals.values())
    top_action = max(mix_totals, key=mix_totals.get)
    top_action_share = mix_totals[top_action] / total_actions if total_actions else 0
    avg_interaction = dff["Interaction Rate"].mean()

    weekday_performance = (
        dff.assign(Weekday=dff["Date"].dt.day_name())
        .groupby("Weekday", as_index=False)
        .agg({"Video Views": "mean", "Interaction Rate": "mean"})
        .sort_values(["Video Views", "Interaction Rate"], ascending=False)
    )
    best_weekday = weekday_performance.iloc[0]

    profile_conversion = (dff["Profile Views"].sum() / dff["Video Views"].sum()) if dff["Video Views"].sum() else 0

    return html.Div(
        [
            html.Div(
                [
                    html.P("Insight-based recommendations", className="section-kicker"),
                    html.H3("Recommended Actions"),
                    html.P(
                        "These actions are generated from the currently selected dashboard data.",
                        className="chart-description",
                    ),
                ],
                className="recommendation-heading",
            ),
            html.Div(
                [
                    insight_item(
                        "Repeat high-reach content",
                        f"Use {top_views_day['Date']:%d %b %Y} as the content benchmark because it reached "
                        f"{compact_number(top_views_day['Video Views'])} views. Review its topic, hook, caption, "
                        "and posting style before planning the next batch.",
                        "teal",
                    ),
                    insight_item(
                        "Prioritise engagement quality",
                        f"Study {top_efficiency_day['Date']:%d %b %Y}, which achieved "
                        f"{top_efficiency_day['Interaction Rate']:.2%} interaction rate versus the selected-period "
                        f"average of {avg_interaction:.2%}. This is the best clue for content that converts viewers "
                        "into active responses.",
                        "purple",
                    ),
                    insight_item(
                        "Post around stronger timing",
                        f"Schedule more tests on {best_weekday['Weekday']} because it has the strongest average reach "
                        f"({compact_number(best_weekday['Video Views'])} views per day) in the selected data.",
                        "gold",
                    ),
                    insight_item(
                        "Balance audience actions",
                        f"{top_action} currently makes up {top_action_share:.1%} of measured actions. Keep using what "
                        "drives that behaviour, but add clearer prompts for comments and shares so engagement is not "
                        "too dependent on one action type.",
                        "teal",
                    ),
                    insight_item(
                        "Improve profile conversion",
                        f"Profile views are {profile_conversion:.2%} of video views. Add a clearer call-to-action in "
                        "captions or pinned comments to turn reach into profile visits and potential followers.",
                        "purple",
                    ),
                    insight_item(
                        "Use data for the next experiment",
                        "Pick one content variable to test at a time: posting day, hook style, topic, or CTA. This makes "
                        "the next dashboard update easier to explain with evidence.",
                        "gold",
                    ),
                ],
                className="insight-grid recommendation-grid",
            ),
        ],
        className="recommendation-card",
    )


def build_filter_summary(selected_month, start_date, end_date, dff):
    if dff.empty:
        date_text = "No records in selected range"
    else:
        date_text = f"{dff['Date'].min():%d %b %Y} - {dff['Date'].max():%d %b %Y}"
    month_text = "All Months" if selected_month == "All" else selected_month
    return html.Div(
        [
            html.Span("Current view"),
            html.Strong(f"{month_text} | {date_text} | {len(dff):,} daily records"),
        ]
    )


def make_trend_chart(dff, metric, aggregation, scale):
    trend = dff.set_index("Date")[[metric]].resample(aggregation).sum().reset_index()
    next_dates = trend["Date"].shift(-1)
    trend["Period Start"] = trend["Date"]
    trend["Period End"] = (next_dates - pd.Timedelta(days=1)).fillna(dff["Date"].max())
    trend["Period End"] = trend["Period End"].clip(upper=dff["Date"].max())
    if aggregation == "D":
        trend["Label"] = trend["Date"].dt.strftime("%d %b %Y")
        trend["Period End"] = trend["Period Start"]
        subtitle = "Daily values"
    elif aggregation == "W":
        trend["Label"] = trend["Date"].dt.strftime("Week of %d %b %Y")
        subtitle = "Weekly total"
    elif aggregation == "ME":
        trend["Label"] = trend["Date"].dt.strftime("%b %Y")
        subtitle = "Monthly total"
    else:
        trend["Label"] = trend["Date"].dt.strftime("%d %b %Y")
        subtitle = "Selected period"

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=trend["Date"],
            y=trend[metric],
            mode="lines+markers",
            line=dict(color=COLORS["teal"], width=3),
            marker=dict(size=7, color=COLORS["teal"], line=dict(color="white", width=1)),
            customdata=trend[["Label", metric, "Period Start", "Period End"]],
            hovertemplate="%{customdata[0]}<br>" + metric + ": %{customdata[1]:,.0f}<extra></extra>",
            name=subtitle,
        )
    )

    peak = trend.loc[trend[metric].idxmax()]
    fig.add_trace(
        go.Scatter(
            x=[peak["Date"]],
            y=[peak[metric]],
            mode="markers+text",
            marker=dict(size=13, color=COLORS["gold"], line=dict(color="white", width=2)),
            text=[compact_number(peak[metric])],
            textposition="top center",
            name="Peak",
            hovertemplate="Peak<br>%{y:,.0f}<extra></extra>",
        )
    )

    fig.update_xaxes(title="")
    fig.update_yaxes(title=metric, tickformat="~s", type=scale, rangemode="tozero")
    fig.update_layout(showlegend=False)
    return style_figure(fig, 390)


def make_rank_chart(dff, metric, count, scale):
    ranked = dff.sort_values(metric, ascending=False).head(int(count)).copy()
    ranked = ranked.sort_values(metric)
    ranked["Date Label"] = ranked["Date"].dt.strftime("%d %b %Y")
    text_template = "%{text:.2%}" if metric == "Interaction Rate" else "%{text:~s}"
    tick_format = ".1%" if metric == "Interaction Rate" else "~s"
    hover_format = ":.2%" if metric == "Interaction Rate" else ":,.0f"

    fig = px.bar(
        ranked,
        x=metric,
        y="Date Label",
        orientation="h",
        text=metric,
        custom_data=[
            "Date",
            "Video Views",
            "Profile Views",
            "Likes",
            "Comments",
            "Shares",
            "Total Engagement",
            "Interaction Rate",
        ],
        color=metric,
        color_continuous_scale=["#BFE9ED", COLORS["teal"]],
    )
    fig.update_traces(
        texttemplate=text_template,
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}<br>" + metric + ": %{x" + hover_format + "}<extra></extra>",
    )
    fig.update_layout(coloraxis_showscale=False, showlegend=False)
    fig.update_xaxes(title=metric, tickformat=tick_format, type=scale)
    fig.update_yaxes(title="")
    return style_figure(fig, 390)


def make_mix_chart(dff, mode):
    color_map = {
        "Likes": COLORS["gold"],
        "Profile Views": COLORS["aqua"],
        "Shares": COLORS["purple"],
        "Comments": COLORS["teal"],
    }
    mix = pd.DataFrame({"Metric": MIX_METRICS, "Value": [dff[m].sum() for m in MIX_METRICS]})
    mix["Share"] = mix["Value"] / mix["Value"].sum() if mix["Value"].sum() else 0
    mix["Label"] = mix.apply(lambda row: f"{compact_number(row['Value'])} | {row['Share']:.1%}", axis=1)
    mix = mix.sort_values("Value", ascending=False)
    leading = mix.iloc[0]

    if mode == "donut":
        fig = go.Figure(
            go.Pie(
                labels=mix["Metric"],
                values=mix["Value"],
                hole=0.68,
                sort=False,
                direction="clockwise",
                marker=dict(colors=[color_map[m] for m in mix["Metric"]], line=dict(color="white", width=3)),
                textinfo="percent",
                textposition="inside",
                insidetextorientation="radial",
                hovertemplate="%{label}<br>%{value:,.0f} actions<br>%{percent}<extra></extra>",
            )
        )
        fig.update_traces(
            pull=[0.03 if metric == leading["Metric"] else 0 for metric in mix["Metric"]],
        )
        fig.add_annotation(
            text=f"<b>{compact_number(leading['Value'])}</b><br>{leading['Metric']}<br>{leading['Share']:.1%} share",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=15, color=COLORS["navy"]),
        )
        fig.update_layout(
            showlegend=True,
            legend_title_text="",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        )
    else:
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=mix["Share"],
                y=mix["Metric"],
                orientation="h",
                marker=dict(
                    color=[color_map[m] for m in mix["Metric"]],
                    line=dict(color="rgba(255,255,255,0.9)", width=1),
                ),
                text=mix["Label"],
                textposition="outside",
                cliponaxis=False,
                customdata=mix[["Value", "Share"]],
                hovertemplate="%{y}<br>%{customdata[0]:,.0f} actions<br>%{customdata[1]:.1%} share<extra></extra>",
            )
        )
        fig.update_layout(showlegend=False)
        fig.update_xaxes(
            title="Share of measured actions",
            tickformat=".0%",
            range=[0, 1],
        )
        fig.update_yaxes(title="")

    fig.update_yaxes(categoryorder="array", categoryarray=list(mix["Metric"])[::-1])
    fig = style_figure(fig, 420)
    fig.update_layout(margin=dict(l=120, r=54, t=34, b=62))
    return fig


def make_heatmap_chart(dff, metric):
    heatmap = dff.copy()
    heatmap["Month Label"] = heatmap["Date"].dt.strftime("%b %Y")
    heatmap["Month Sort"] = heatmap["Date"].dt.to_period("M")
    heatmap["Day"] = pd.Categorical(
        heatmap["Date"].dt.day_name().str[:3],
        categories=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        ordered=True,
    )

    pivot = (
        heatmap.groupby(["Day", "Month Label", "Month Sort"], observed=False)[metric]
        .mean()
        .reset_index()
        .sort_values("Month Sort")
    )
    month_order = pivot["Month Label"].drop_duplicates().tolist()
    matrix = pivot.pivot(index="Day", columns="Month Label", values=metric).reindex(
        index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], columns=month_order
    )

    fig = go.Figure(
        go.Heatmap(
            z=matrix.values,
            x=matrix.columns,
            y=matrix.index,
            colorscale=[
                [0, "#EEF8F9"],
                [0.45, "#81D4DC"],
                [1, COLORS["teal"]],
            ],
            hovertemplate="%{y}, %{x}<br>Avg " + metric + ": %{z:,.0f}<extra></extra>",
            colorbar=dict(title=f"Avg {metric}", tickformat="~s"),
        )
    )
    strongest = pivot.loc[pivot[metric].idxmax()]
    fig.add_annotation(
        x=strongest["Month Label"],
        y=strongest["Day"],
        text="Peak pattern",
        showarrow=True,
        arrowhead=2,
        ax=0,
        ay=-36,
        bgcolor="#FFFBEB",
        bordercolor=COLORS["gold"],
        font=dict(size=11, color=COLORS["navy"]),
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="")
    return style_figure(fig, 420)


def make_scatter_chart(dff, x_metric, y_metric, scale):
    scatter = dff.copy()
    if y_metric == "Engagement Rate":
        scatter[y_metric] = scatter["Engagement Rate"]
    scatter = scatter[(scatter[x_metric] > 0) & (scatter[y_metric] > 0)]

    fig = px.scatter(
        scatter,
        x=x_metric,
        y=y_metric,
        size="Total Engagement",
        color="Engagement Rate",
        custom_data=["Date", "Video Views", "Profile Views", "Likes", "Comments", "Shares", "Total Engagement"],
        hover_data={
            "Date": "|%d %b %Y",
            x_metric: ":,.0f",
            y_metric: ":.2%" if y_metric == "Engagement Rate" else ":,.0f",
            "Total Engagement": ":,.0f",
            "Engagement Rate": ":.2%",
        },
        color_continuous_scale=["#D7F3F5", COLORS["teal"], COLORS["gold"]],
    )
    fig.update_traces(marker=dict(opacity=0.76, line=dict(width=0.8, color="white")))
    fig.update_xaxes(title=x_metric, tickformat="~s", type=scale)
    fig.update_yaxes(
        title=y_metric,
        tickformat=".0%" if y_metric == "Engagement Rate" else "~s",
        type="linear" if y_metric == "Engagement Rate" else scale,
    )
    fig.update_layout(coloraxis_colorbar=dict(title="Eng. rate"))
    return style_figure(fig, 420)


def build_empty_detail_panel():
    return html.Div(
        [
            html.P("Drill-down"),
            html.H3("Click a chart element"),
            html.Div(
                [
                    html.Div(
                        "Click a trend point for a period summary, a ranked bar for day detail, or a scatter point for content efficiency detail.",
                        className="detail-help",
                    ),
                    detail_row("Video Views", None),
                    detail_row("Profile Views", None),
                    detail_row("Likes", None),
                    detail_row("Comments", None),
                    detail_row("Shares", None),
                    detail_row("Total Engagement", None, True),
                ],
                className="detail-list",
            ),
        ]
    )


def build_detail_panel(dff, trend_metric, trend_click, rank_click, scatter_click):
    if scatter_click and scatter_click.get("points"):
        return build_day_detail_panel(dff, scatter_click, "Scatter point")
    if rank_click and rank_click.get("points"):
        return build_day_detail_panel(dff, rank_click, "Ranked bar")
    if trend_click and trend_click.get("points"):
        return build_period_detail_panel(dff, trend_metric, trend_click)
    return build_empty_detail_panel()


def build_day_detail_panel(dff, click_data, source_label):
    point = click_data["points"][0]
    custom = point.get("customdata")
    if not custom:
        return build_empty_detail_panel()

    selected_date = pd.to_datetime(custom[0]).normalize()
    selected = dff[dff["Date"].dt.normalize() == selected_date]
    if selected.empty:
        return build_empty_detail_panel()

    row = selected.iloc[0]
    average_views = dff["Video Views"].mean()
    average_engagement = dff["Total Engagement"].mean()
    view_diff = (row["Video Views"] - average_views) / average_views if average_views else 0
    engagement_diff = (
        (row["Total Engagement"] - average_engagement) / average_engagement if average_engagement else 0
    )
    return html.Div(
        [
            html.P(f"Drill-down from {source_label}"),
            html.H3(row["Date"].strftime("%d %b %Y")),
            html.Div(
                [
                    html.Div(
                        f"Views are {abs(view_diff):.1%} {'above' if view_diff >= 0 else 'below'} the selected-period average; "
                        f"engagement is {abs(engagement_diff):.1%} {'above' if engagement_diff >= 0 else 'below'} average.",
                        className="detail-help",
                    ),
                    detail_row("Video Views", row["Video Views"]),
                    detail_row("Profile Views", row["Profile Views"]),
                    detail_row("Likes", row["Likes"]),
                    detail_row("Comments", row["Comments"]),
                    detail_row("Shares", row["Shares"]),
                    detail_row("Interaction Rate", row["Interaction Rate"], True, is_percent=True),
                    detail_row("Total Engagement", row["Total Engagement"], True),
                ],
                className="detail-list",
            ),
        ]
    )


def build_period_detail_panel(dff, trend_metric, click_data):
    point = click_data["points"][0]
    custom = point.get("customdata")
    if not custom or len(custom) < 4:
        return build_empty_detail_panel()

    start_date = pd.to_datetime(custom[2]).normalize()
    end_date = pd.to_datetime(custom[3]).normalize()
    period = dff[(dff["Date"] >= start_date) & (dff["Date"] <= end_date)]
    if period.empty:
        return build_empty_detail_panel()

    peak = period.loc[period[trend_metric].idxmax()]
    title = start_date.strftime("%d %b %Y")
    if start_date != end_date:
        title = f"{start_date:%d %b} - {end_date:%d %b %Y}"

    return html.Div(
        [
            html.P("Drill-down from trend"),
            html.H3(title),
            html.Div(
                [
                    detail_row("Selected Metric Total", period[trend_metric].sum()),
                    detail_row("Reporting Days", len(period)),
                    detail_row("Peak Day", peak[trend_metric], True),
                    html.Div(f"Peak day: {peak['Date']:%d %b %Y}", className="detail-help"),
                    detail_row("Video Views", period["Video Views"].sum()),
                    detail_row("Total Engagement", period["Total Engagement"].sum(), True),
                ],
                className="detail-list",
            ),
        ]
    )


def detail_row(label, value, featured=False, is_percent=False):
    if value is None:
        shown = "-"
    elif is_percent:
        shown = f"{value:.2%}"
    else:
        shown = f"{value:,.0f}"
    class_name = "detail-row featured" if featured else "detail-row"
    return html.Div([html.Span(label), html.Strong(shown)], className=class_name)


if __name__ == "__main__":
    is_render = os.environ.get("RENDER") == "true"
    app.run(
        host="0.0.0.0" if is_render else "127.0.0.1",
        port=int(os.environ.get("PORT", 8050)),
        debug=not is_render,
        dev_tools_ui=False,
        use_reloader=False,
    )
