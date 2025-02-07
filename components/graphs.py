import dash
from dash import dcc, html
import pandas as pd
from plotly import express as px



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
    Creates a bar chart with proper frequency labels on top of the bars.
    """
    if group:
        if group_order is not None:
            data[group] = pd.Categorical(data[group], categories=group_order, ordered=True)
            data = data.sort_values([group, x])
        # Order x values alphabetically
        fig = px.bar(data, x=x, y=y, color=group, title=title, barmode='group', text=y)
    else:
        data = data.sort_values(x)
        fig = px.bar(data, x=x, y=y, title=title, barmode='group', text=y)

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