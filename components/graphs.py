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


def box_plot(
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
    # Create base box plot colored by category (x) so each substance has its own box
    fig = px.box(data, x=x, y=y, color=x, title=title, points=False)

    # Style boxes: semi-transparent and no legend entries
    for trace in fig.data:
        cat = trace.name
        color = None
        if color_mapping and cat in color_mapping:
            color = color_mapping[cat]
        if color:
            trace.marker = trace.marker or {}
            trace.marker.color = color
            trace.fillcolor = color
        trace.opacity = 0.35
        trace.showlegend = False

    # Overlay scatter of individual points (one dot per dosage mention)
    if 'Study_ID' in data.columns:
        # Use a strip plot so points remain clickable. Some plotly versions
        # don't support a `jitter` kwarg on px.strip(), so omit it here.
        # Create strip plot colored by category; use color_discrete_map if provided
        if color_mapping:
            scatter_fig = px.strip(data, x=x, y=y, color=x, color_discrete_map=color_mapping, custom_data=['Study_ID'])
        else:
            scatter_fig = px.strip(data, x=x, y=y, color=x, custom_data=['Study_ID'])

        # Merge strip (points) traces into the box figure, keeping customdata
        for tr in scatter_fig.data:
            tr_marker = tr.marker or {}
            tr_marker['size'] = 7
            tr_marker['opacity'] = 0.9
            tr.marker = tr_marker

            # Set hovertemplate to show Study_ID clearly (customdata is an array)
            tr.hovertemplate = f"Study ID: %{{customdata[0]}}<br>{y}: %{{y}}<extra></extra>"

            fig.add_trace(tr)

    # Update axes labels
    fig.update_xaxes(title_text=x_label)
    fig.update_yaxes(title_text=y_label)

    fig.update_layout(plot_bgcolor='#f8f8f8')


    add_interaction_annotation(fig)


    config = {
        'displaylogo': False,
    }

    return dcc.Graph(figure=fig, config=config, id=id)


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
