from dash import html, dcc
import dash_bootstrap_components as dbc

# import study_view
from style.colors import get_color_mapping
from components.layout import search_filter_component, studies_display, filter_button
from components.graphs import bar_chart
from data.queries import get_filtered_freq, get_freq, get_freq_grouped
from style.colors import get_color_mapping

def explore_layout(title: str, graph: dcc.Graph, filters: dict, filter_buttons: list[dbc.Button]) -> html.Div:
    return html.Div([
        html.H1(f'{title}', className="my-4"),
        graph,
        search_filter_component(filter_buttons),
        studies_display()
    ])

def rct_view():
    title = "Assessing Evidence Strength: RCTs and Systematic Reviews per Substance"
    task = 'Study Type'
    labels = ['Randomized-controlled trial (RCT)', 'Systematic review/meta-analysis', 'Other']
    group_task = 'Substances'
    data_rct = get_freq_grouped(task, labels, group_task)
    graph_title = 'Number of RCTs and Systematic Reviews per Substance'
    filter_buttons = []
    color_mapping = get_color_mapping(task, labels)
    for label in labels:
        if label != 'Other':
            filter_buttons.append(filter_button(color_mapping[label], label, task, False))
    
    graph = bar_chart(data_rct, group_task, 'Frequency', graph_title, group_task, 'Frequency', task, color_mapping, ['pan', 'select', 'lasso2d'], labels)
    filters = {
        task: labels
    }

    return explore_layout(title, graph, filters, filter_buttons)

def efficacy_safety_view():
    title = "Is there enough research on efficacy and safety endpoints per substance?"
    task = "Study Purpose"
    labels = ["Efficacy endpoints", "Safety endpoints"]
    group_task = 'Substances'
    data = get_freq_grouped(task, labels, group_task)
    graph_title = 'Number of studies measuring efficacy and safety endpoints per substance'
    color_mapping = get_color_mapping(task, labels)
    filter_buttons = []
    for label in labels:
        filter_buttons.append(filter_button(color_mapping[label], label, task, False))
    graph = bar_chart(data, group_task, 'Frequency', graph_title, group_task, 'Frequency', task, color_mapping, ['pan', 'select', 'lasso2d'], labels)
    filters = {
        task: labels
    }
    return explore_layout(title, graph, filters, filter_buttons)

def longitudinal_view():
    title = "Is there enough research on longitudinal studies per substance?"
    task = "Data Type"
    labels = ["Longitudinal short", "Longitudinal long", "Cross-sectional"]
    group_task = 'Substances'
    data = get_freq_grouped(task, labels, group_task)
    graph_title = 'Number of studies per substance for different data types'
    color_mapping = get_color_mapping(task, labels)
    filter_buttons = []
    for label in labels:
        filter_buttons.append(filter_button(color_mapping[label], label, task, False))
    graph = bar_chart(data, group_task, 'Frequency', graph_title, group_task, 'Frequency', task, color_mapping, ['pan', 'select', 'lasso2d'], labels)
    filters = {
        task: labels
    }
    return explore_layout(title, graph, filters, filter_buttons)

def sex_bias_view():
    title = "Is there sex bias per substance?"
    task = "Sex of Participants"
    labels = ["Male", "Female", "Both sexes", "Unknown" ]
    group_task = 'Substances'
    data = get_freq_grouped(task, labels, group_task)
    graph_title = 'Sex of participants of studies per substance'
    color_mapping = get_color_mapping(task, labels)
    filter_buttons = []
    for label in labels:
        filter_buttons.append(filter_button(color_mapping[label], label, task, False))
    graph = bar_chart(data, group_task, 'Frequency', graph_title, group_task, 'Frequency', task, color_mapping, ['pan', 'select', 'lasso2d'], labels)
    filters = {
        task: labels
    }
    return explore_layout(title, graph, filters, filter_buttons)


