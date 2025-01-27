import dash
from dash import dcc, html
import pandas as pd
from plotly import express as px


def dropdown(options: list[str], identifier: str, default: str = "Select an Option", label: str = None, width: str = "100%") -> html.Span:
    """
    Creates a dropdown menu with Dash given a list of strings as input.

    Parameters:
    options (list of str): List of options for the dropdown menu.
    placeholder (str): Placeholder text for the dropdown.
    label (str): Label for the dropdown.
    width (str): CSS width for the dropdown container.

    Returns:
    html.Div: A Dash html.Div containing the dropdown menu.
    """
    # Create the dropdown menu
    dropdown = dcc.Dropdown(
        id=identifier,
        options=[{'label': option, 'value': option} for option in options],
        value=default,
        # Ensure the dropdown itself spans its container
        style={'width': '100%'}
    )

    # Create the label element if provided
    label_element = html.Label(label) if label else None

    # Wrap the dropdown and label in a Div and return
    return html.Span([label_element, dropdown] if label else [dropdown], style={'display': 'inline-block', 'width': width, 'verticalAlign': 'top'})


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
        group_order: list[str] = None
) -> dcc.Graph:
    """
    Creates a basic bar chart with Dash given a DataFrame and column names.

    # s. https://plotly.com/python/configuration-options/ for removing buttons
    """
    if group:
        if group_order:
            data[group] = pd.Categorical(data[group], categories=group_order, ordered=True)
            data = data.sort_values([group, x])
        # order x values alphabetically
        fig = px.bar(data, x=x, y=y, color=group, title=title, barmode='group')

    else:
        data = data.sort_values(x)
        fig = px.bar(data, x=x, y=y, title=title, barmode='group')
    # Update the x and y axis labels
    fig.update_xaxes(title_text=x_label)
    fig.update_yaxes(title_text=y_label)

    # Update the color mapping if provided
    x_values = data[x].unique()
    group_values = data[group].unique() if group else [None]

    if color_mapping:
        if group:  # Color by group
            group_values = data[group].unique()
            for group_val in group_values:
                color = color_mapping.get(group_val, None)
                fig.for_each_trace(lambda trace: trace.update(
                    marker_color=color) if trace.name == group_val else ())
        else:  # Color by x values
            x_values = data[x].unique()
            for x_val in x_values:
                color = color_mapping.get(x_val, None)
                fig.for_each_trace(lambda trace: trace.update(
                    marker_color=color) if trace.name == x_val else ())
    fig.update_layout(plot_bgcolor='#f8f9fa')

    config = {
        'modeBarButtonsToRemove': remove_button,  # Remove specific buttons
        'displaylogo': False,  # Optionally hide the Plotly logo
    }

    return dcc.Graph(figure=fig, config=config)
