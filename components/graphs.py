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
        style={'width': '100%'}  # Ensure the dropdown itself spans its container
    )
    
    # Create the label element if provided
    label_element = html.Label(label) if label else None
    
    # Wrap the dropdown and label in a Div and return
    return html.Span([label_element, dropdown] if label else [dropdown], style={'display': 'inline-block', 'width': width, 'verticalAlign': 'top'})


# basic bar chart
def bar_chart(data: pd.DataFrame, x: str, y: str, title: str, x_label: str, y_label: str) -> dcc.Graph:
    """
    Creates a basic bar chart with Dash given a DataFrame and column names.
    
    Parameters:
    data (pd.DataFrame): Data to plot.
    x (str): Column name for the x-axis.
    y (str): Column name for the y-axis.
    title (str): Title for the chart.
    x_label (str): Label for the x-axis.
    y_label (str): Label for the y-axis.
    
    Returns:
    dcc.Graph: A Dash dcc.Graph object containing the bar chart.
    """
    # Create the bar chart
    fig = px.bar(data, x=x, y=y, title=title)
    
    # Update the x and y axis labels
    fig.update_xaxes(title_text=x_label)
    fig.update_yaxes(title_text=y_label)
    
    return dcc.Graph(figure=fig)