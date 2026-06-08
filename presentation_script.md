# HaqyXD TikTok Analytics Dashboard Presentation Script

## 1. Introduction

This dashboard analyses HaqyXD TikTok performance from 7 May 2025 to 5 May 2026. The purpose is to understand reach, engagement, timing patterns, and the relationship between views and audience actions.

The dataset includes daily metrics such as video views, profile views, likes, comments, shares, and total engagement.

## 2. Data Preparation

Before analysis, the dataset was cleaned to make sure calculations were accurate. The final CSV row was identified as a summary total row, not a daily record, because its values matched the sum of the previous rows. Therefore, it was excluded from the daily analysis.

After cleaning, the dashboard uses 364 daily records.

## 3. Dashboard Structure

The dashboard starts with KPI cards showing total views, total engagement, peak reach day, and best efficiency day.

Peak reach day is based on the highest video views. Best efficiency day is based on interaction rate, calculated from likes, comments, and shares divided by video views.

## 4. Interactivity

The dashboard includes filters for month and date range. There is also a reset button to return to the default full-period view.

Each chart has its own controls. For example, the trend chart can switch between daily, weekly, and monthly aggregation. Ranked performance can change metric, number of rows, and axis scale. The engagement mix can switch between bar and donut views.

The dashboard also includes drill-down features. Users can click a trend point to view a period summary, click a ranked bar to inspect a specific day, or click a scatter point to inspect a day in detail.

## 5. Key Visualizations

The performance trend chart shows how selected metrics change over time. It helps identify major spikes and long-term patterns.

The ranked performance chart highlights the best-performing days by either volume metrics or interaction rate.

The engagement mix chart shows which audience actions contribute most to engagement. In this dataset, likes dominate the measured engagement actions.

The timing heatmap shows performance patterns by month and day of week. This helps identify when activity tends to be stronger.

The metric relationship chart compares two metrics, such as video views and likes, to see whether reach translates into engagement.

## 6. Main Insights

One key insight is that the strongest reach does not always mean the strongest efficiency. A day with very high views may not have the highest interaction rate.

Another insight is that engagement is heavily concentrated in likes, while comments and shares form a much smaller portion of measured actions.

The heatmap helps identify timing patterns that can support future posting strategies.

## 7. Recommendations

First, analyse the content posted around high interaction-rate days because those posts generated stronger audience response relative to reach.

Second, review the content around peak reach periods to understand what caused the largest exposure.

Third, improve strategies that encourage shares and comments, because the engagement mix shows that these actions are much lower than likes.

Finally, use the heatmap timing pattern to guide future posting schedules.

## 8. Conclusion

Overall, the dashboard turns TikTok analytics into a structured and interactive decision-making tool. It supports accurate calculations, meaningful interpretation, multiple visualization types, and interactive drill-down analysis.
