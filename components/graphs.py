import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc


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
    """Creates a bar chart with Study_ID attached as customdata for selections."""

    data = data.copy()

    # Apply group ordering
    if group and group_order is not None:
        data[group] = pd.Categorical(
            data[group],
            categories=group_order,
            ordered=True,
        )
        data = data.sort_values([group, x])

    # Sort x-axis categories by frequency
    order = (
        data.groupby(x, observed=False)[y]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )

    data[x] = pd.Categorical(
        data[x],
        categories=order,
        ordered=True,
    )

    # Create figure
    px_kwargs = dict(
        data_frame=data,
        x=x,
        y=y,
        title=title,
        text=y,
    )

    if group:
        px_kwargs.update(
            {
                "color": group,
                "barmode": "group",
            }
        )

    # IMPORTANT:
    # Pass Study_ID directly to Plotly so selectedData contains it
    if "Study_ID" in data.columns:
        px_kwargs["custom_data"] = ["Study_ID"]

    fig = px.bar(**px_kwargs)

    # Axis labels
    fig.update_xaxes(title_text=x_label)
    fig.update_yaxes(title_text=y_label)

    # Preserve category ordering
    fig.update_xaxes(
        categoryorder="array",
        categoryarray=order,
    )

    # Text labels
    fig.update_traces(
        textposition="outside",
        textfont_size=10,
    )

    # Apply colors
    if color_mapping:
        if group:
            for trace in fig.data:
                if trace.name in color_mapping:
                    trace.update(
                        marker_color=color_mapping[trace.name]
                    )
        else:
            for trace in fig.data:
                if trace.name in color_mapping:
                    trace.update(
                        marker_color=color_mapping[trace.name]
                    )

    # Background
    fig.update_layout(
        plot_bgcolor="#f8f8f8"
    )

    add_interaction_annotation(fig)

    # Optional average line
    if average:
        avg_value = data[y].mean()

        fig.add_trace(
            dict(
                x=data[x],
                y=[avg_value] * len(data[x]),
                mode="lines",
                name="Average",
                line=dict(
                    color="black",
                    width=2,
                ),
            )
        )

    config = {
        'modeBarButtonsToRemove': remove_button,  # Remove specific buttons
        'displaylogo': False,  # Optionally hide the Plotly logo
    }

    return dcc.Graph(
        id={
            "type": "view-graph",
            "index": title.lower().replace(" ", "-"),
        },
        figure=fig,
        config=config,
    )

def box_plot_graph(
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
    add_annotation: bool = True,
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
    data = data[~data[x].isin(['Psychedelic mushrooms', 'Unknown'])]

    fig = box_plot(data, x, y, title, x_label, y_label, group,
                   color_mapping, height=height, width=width)
    if add_annotation:
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
                data_all.groupby(x, observed=False)[y].median().sort_values(
                    ascending=False).index.tolist()
            )
        except Exception:
            order = data_all[x].unique().tolist()
    else:
        order = []

    # ensure categorical ordering for consistent plotting
    if order:
        data_all[x] = pd.Categorical(
            data_all[x], categories=order, ordered=True)

    # Use the full dataset for standard box calculation (quartiles and whiskers)
    data_filtered = data_all.copy()
    if order and x in data_filtered.columns:
        data_filtered[x] = pd.Categorical(
            data_filtered[x], categories=order, ordered=True)

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
        for cat, sub in data_all.groupby(x, observed=False):
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
        fig.update_yaxes(categoryorder='array',
                         categoryarray=order, autorange='reversed')

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


def extract_study_id(point: dict) -> int | list[int] | None:
    """Extract study ID(s) from a Plotly point's customdata.

    Handles:
    - scalar IDs: customdata=123
    - aggregated IDs: customdata=[1,2,3]
    - wrapped aggregated IDs: customdata=[[1,2,3]]
    """
    customdata = point.get("customdata")

    if customdata is None:
        return None

    # Convert numpy arrays/tuples to normal lists
    if hasattr(customdata, "tolist"):
        customdata = customdata.tolist()

    # Handle list/tuple customdata
    if isinstance(customdata, (list, tuple)):
        if not customdata:
            return None

        # Case: customdata=[[1,2,3]]
        # (old Plotly wrapping style)
        if isinstance(customdata[0], (list, tuple)):
            customdata = customdata[0]

        # Case: customdata=[1,2,3]
        if isinstance(customdata, (list, tuple)):
            ids = []
            for item in customdata:
                if hasattr(item, "item"):
                    item = item.item()
                ids.append(int(item))
            return ids

    # Case: customdata=123
    if hasattr(customdata, "item"):
        customdata = customdata.item()

    return int(customdata)

def get_ids_from_selected_data(selected_data: list[dict]) -> list[int]:
    """Extract study IDs from a list of Plotly selectedData dicts."""
    ids = set()

    for graph_selection in selected_data:
        if not graph_selection:
            continue

        for point in graph_selection.get("points", []):
            study_id = extract_study_id(point)

            if study_id is not None:
                if isinstance(study_id, list):
                    ids.update(study_id)
                else:
                    ids.add(study_id)

    return list(ids)


def get_ids_from_click_data(click_data: list[dict]) -> list[int]:
    """Extract study IDs from a list of Plotly clickData dicts."""
    ids = set()

    for graph_click in click_data:
        if not graph_click:
            continue

        for point in graph_click.get("points", []):
            point_ids = extract_study_ids(point)
            ids.update(point_ids)

    return list(ids)
