import dash
from dash import dcc, html
import pandas as pd
from plotly import express as px
import plotly.graph_objects as go


def bar_chart(
        data: pd.DataFrame,
        x: str,
        y: str,
        title: str,
        x_label: str,
        y_label: str,
        group: str = None,
        color_mapping: dict[str, str] = None,
        remove_button: list[str] = [],
        group_order: list[str] = None,
        average: bool = False,
) -> dcc.Graph:
    """
    Creates a bar chart.

    data: pandas.DataFrame with columns `x` and `y`.
    - `x`: categorical (or convertible) for x-axis categories.
    - `y`: numeric values for bar heights (aggregated by sum).
    - optional `group`: categorical column to group/color bars.
    - optional `Study_ID`: allowed but unused here.

    Returns a Dash `dcc.Graph`.
    """
    if group:
        if group_order is not None:
            data[group] = pd.Categorical(data[group], categories=group_order, ordered=True)
            data = data.sort_values([group, x])

        order = data.groupby(x)[y].sum().sort_values(ascending=False).index.tolist()
        data[x] = pd.Categorical(data[x], categories=order, ordered=True)

        fig = px.bar(data, x=x, y=y, color=group, title=title, barmode='group', text=y)
    else:

        order = data.groupby(x)[y].sum().sort_values(ascending=False).index.tolist()
        data[x] = pd.Categorical(data[x], categories=order, ordered=True)

        fig = px.bar(data, x=x, y=y, title=title, barmode='group', text=y)


    if 'order' in locals() and order:
        fig.update_xaxes(categoryorder='array', categoryarray=order)
    elif pd.api.types.is_categorical_dtype(data[x].dtype):
        fig.update_xaxes(categoryorder='array', categoryarray=list(data[x].cat.categories))


    # Update x and y axis labels
    fig.update_xaxes(title_text=x_label)
    fig.update_yaxes(title_text=y_label)

    # Ensure text labels appear above bars
    fig.update_traces(textposition='outside', textfont_size=10)

    # Update the color mapping if provided
    if color_mapping:
        if group:  # Color by group
            for group_val in data[group].unique():
                color = color_mapping.get(group_val, None)
                fig.for_each_trace(lambda trace: trace.update(
                    marker_color=color) if trace.name == group_val else ())
        else:  # Color by x values
            for x_val in data[x].unique():
                color = color_mapping.get(x_val, None)
                fig.for_each_trace(lambda trace: trace.update(
                    marker_color=color) if trace.name == x_val else ())

    fig.update_layout(plot_bgcolor='#f8f8f8')
    add_interaction_annotation(fig)


    if average:
        # add average number of participants per substance as a line
        data['Average'] = data[y].mean()
        fig.add_trace(
            dict(
                x=data[x],
                y=data['Average'],
                mode='lines',
                name='Average',
                line=dict(color='black', width=2)
            )
        )

    config = {
        'modeBarButtonsToRemove': remove_button,  # Remove specific buttons
        'displaylogo': False,  # Optionally hide the Plotly logo
    }

    return dcc.Graph(figure=fig, config=config)


def box_plot_graph(
        data: pd.DataFrame,
        x: str,
        y: str,
        title: str,
        x_label: str,
        y_label: str,
        group: str = None,
        color_mapping: dict[str, str] = None,
        id: str = None,
) -> dcc.Graph:
    """
    Creates a translucent box plot with overlaid points.

    data: pandas.DataFrame with columns `x` (categorical) and `y` (numeric).
    - optional `Study_ID`: included in point `customdata` when present.
    - `color_mapping`: optional dict mapping `x` values to Plotly colors.

    Returns a Dash `dcc.Graph`.
    """
    # exclude Psychdelic mushrooms Unkown and LSD from the plot
    data = data[~data[x].isin(['Psychedelic mushrooms', 'Unknown', 'LSD'])]

    fig = box_plot(data, x, y, title, x_label, y_label, group, color_mapping)
    add_interaction_annotation(fig)
    config = {
        'displaylogo': False,
    }
    return dcc.Graph(figure=fig, config=config, id=id)


def box_plot(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    x_label: str,
    y_label: str,
    group: str = None,
    color_mapping: dict[str, str] = None,
    height: int | None = None,
    width: int | None = None,
) -> go.Figure:
    # Preserve full dataset for plotting raw points (so outliers remain visible)
    data_all = data.copy()

    # Order categories by median of y (descending) so largest median appears on top
    if not data_all.empty:
        try:
            order = (
                data_all.groupby(x)[y].median().sort_values(ascending=False).index.tolist()
            )
        except Exception:
            order = data_all[x].unique().tolist()
    else:
        order = []

    # ensure categorical ordering for consistent plotting
    if order:
        data_all[x] = pd.Categorical(data_all[x], categories=order, ordered=True)

    # Use the full dataset for standard box calculation (quartiles and whiskers)
    data_filtered = data_all.copy()
    if order and x in data_filtered.columns:
        data_filtered[x] = pd.Categorical(data_filtered[x], categories=order, ordered=True)

    # Create horizontal box plot from filtered data (y=category, x=numeric)
    # Use Plotly's default box calculation and show outliers ('outliers')
    fig = px.box(
        data_filtered,
        x=y,
        y=x,
        color=x,
        title=title,
        points='outliers',
        category_orders={x: order} if order else None,
    )

    # Style boxes: white fill with black border so median/whiskers are clear
    for trace in fig.data:
        # apply only to box traces
        if getattr(trace, 'type', '') == 'box':
            # white fill, black border
            trace.fillcolor = 'white'
            trace.line = trace.line or {}
            trace.line.color = 'black'
            trace.line.width = 1.5
            # style outlier markers on the box itself
            trace.marker = trace.marker or {}
            # hide box trace outlier markers so colored strip points remain the visible outliers
            trace.marker.opacity = 0
            trace.marker.size = 0
            trace.opacity = 1.0
            trace.showlegend = False
        else:
            # leave non-box traces untouched here
            continue

    # Overlay all raw points (including outliers) using a strip plot.
    # Prefer coloring by `Dose_Type` (as in analysis notebook) when available.
    dosage_color_map = {
        'absolute': '#1f77b4',
        'relative_weight': '#ff7f0e',
        'relative_time': '#2ca02c',
        'relative_weight_time': '#9467bd',
    }

    if 'Dose_Type' in data_all.columns:
        strip_color_col = 'Dose_Type'
        color_map = {**dosage_color_map}
    else:
        # fallback: color points by category (x)
        strip_color_col = x
        color_map = color_mapping

    strip_fig = px.strip(
        data_all,
        x=y,
        y=x,
        color=strip_color_col,
        color_discrete_map=color_map,
        category_orders={x: order} if order else None,
        custom_data=['Study_ID'] if 'Study_ID' in data_all.columns else None,
    )

    for tr in strip_fig.data:
        tr.marker = tr.marker or {}
        tr.marker.size = 6
        tr.marker.opacity = 0.5
        if 'Study_ID' in data_all.columns:
            tr.hovertemplate = (
                f"Study ID: %{{customdata[0]}}<br>"
                f"{y}: %{{x}}<extra></extra>"
            )
        fig.add_trace(tr)

    # Labels
    fig.update_xaxes(title_text=x_label)
    fig.update_yaxes(title_text=y_label)

    # Conservative numeric x-axis limits so extreme outliers don't dominate view
    vals_all = data_all[y].dropna()
    if not vals_all.empty:
        upper_whiskers = []
        for cat, sub in data_all.groupby(x):
            vals = sub[y].dropna()
            if vals.empty:
                continue
            q1 = vals.quantile(0.25)
            q3 = vals.quantile(0.75)
            iqr = q3 - q1
            upper = q3 + 1.5 * iqr
            whisker_high = vals[vals <= upper].max()
            if pd.notna(whisker_high):
                upper_whiskers.append(whisker_high)

        if upper_whiskers:
            xmax = max(upper_whiskers) * 1.05
        else:
            xmax = vals_all.mean() * 2

        xmin = max(0, vals_all.min() * 0.9)
        fig.update_xaxes(range=[xmin, xmax])

    # enforce y category order and display largest median on top
    if order:
        fig.update_yaxes(categoryorder='array', categoryarray=order, autorange='reversed')

    # Apply requested size if provided
    layout_updates = {'plot_bgcolor': '#f8f8f8'}
    if height is not None:
        layout_updates['height'] = height
    if width is not None:
        layout_updates['width'] = width
    fig.update_layout(**layout_updates)

    return fig


def add_interaction_annotation(fig, x=0.88, y=0.86, ax=36, ay=-72, text="Interact<br>with<br>the graph", font_size=13):
    """Add a paper-anchored annotation (arrow + multiline text) to `fig`.

    Uses paper coordinates so the annotation stays relative to the plot area
    and will resize with the figure. `ax`/`ay` are pixel offsets for the
    text relative to the arrow tip; these keep spacing visually constant.
    """
    ann = dict(
        x=x,
        y=y,
        xref='paper',
        yref='paper',
        text=text,
        showarrow=True,
        arrowhead=2,
        arrowcolor='rgba(0,0,0,0.7)',
        ax=ax,
        ay=ay,
        font=dict(size=font_size),
        align='center',
        bgcolor='rgba(255,255,255,0.85)',
        opacity=1.0,
        captureevents=False,
    )

    # Ensure layout.annotations exists and append
    if not hasattr(fig.layout, 'annotations') or fig.layout.annotations is None:
        fig.layout.annotations = ()

    existing = list(fig.layout.annotations)
    existing.append(ann)
    fig.layout.annotations = tuple(existing)



