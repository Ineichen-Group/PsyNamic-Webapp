from collections import defaultdict
from dash import html, dcc
import dash_bootstrap_components as dbc
from style.colors import get_color_mapping
from components.layout import filter_component, studies_display, filter_button  # , filter_tag
from components.graphs import bar_chart
from data.queries import get_freq_grouped, get_ids
from callbacks import rgb_to_hex  # TODO: move this to colors


def explore_layout(title: str, graph: dcc.Graph, filter_buttons: list[dbc.Button], study_tags: dict[str, list[html.Div]] = None) -> html.Div:
    return html.Div([
        html.H1(f'{title}', className="my-4"),
        graph,
        filter_component(filter_buttons),
        # studies_display(tag_data)
        studies_display(study_tags)
    ])


def rct_view():
    title = "Assessing Evidence Strength: RCTs and Systematic Reviews per Substance"
    task = 'Study Type'
    labels = [
        'Randomized-controlled trial (RCT)', 'Systematic review/meta-analysis', 'Other']
    group_task = 'Substances'
    data_rct = get_freq_grouped(task, group_task, labels=labels)
    graph_title = 'Number of RCTs and Systematic Reviews per Substance'
    filter_buttons = []
    color_mapping = get_color_mapping(task, labels)
    for label in labels:
        if label != 'Other':
            filter_buttons.append(filter_button(
                color_mapping[label], label, task, False))
    graph = bar_chart(data_rct, group_task, 'Frequency', graph_title, group_task,
                      'Frequency', task, color_mapping, ['pan', 'select', 'lasso2d'], labels)
    study_tags = defaultdict(list)
    for label in labels[:-1]: # exclude 'Other'
        filtered_study_ids = get_ids(task, label)
        for id in filtered_study_ids:
            tag_info = {
                'task': task,
                'label': label,
                'color': rgb_to_hex(color_mapping[label])
            }
            study_tags[id].append(tag_info)
    return explore_layout(title, graph, filter_buttons, study_tags)


def efficacy_safety_view():
    title = "Is there enough research on efficacy and safety endpoints per substance?"
    task = "Study Purpose"
    labels = ["Efficacy endpoints", "Safety endpoints"]
    group_task = 'Substances'
    data = get_freq_grouped(task, group_task, labels=labels)
    graph_title = 'Number of studies measuring efficacy and safety endpoints per substance'
    color_mapping = get_color_mapping(task, labels)
    filter_buttons = []
    for label in labels:
        filter_buttons.append(filter_button(
            color_mapping[label], label, task, False))
    graph = bar_chart(data, group_task, 'Frequency', graph_title, group_task,
                      'Frequency', task, color_mapping, ['pan', 'select', 'lasso2d'], labels)
    study_tags = defaultdict(list)
    for label in labels:
        filered_ids = get_ids(task, label)
        for id in filered_ids:
            tag_info = {
                'task': task,
                'label': label,
                'color': rgb_to_hex(color_mapping[label])
            }
            study_tags[id].append(tag_info)
    return explore_layout(title, graph, filter_buttons, study_tags)


def longitudinal_view():
    title = "Is there enough research on longitudinal studies per substance?"
    task = "Data Type"
    labels = ["Longitudinal short", "Longitudinal long", "Cross-sectional"]
    group_task = 'Substances'
    data = get_freq_grouped(task, group_task, labels=labels)
    graph_title = 'Number of studies per substance for different data types'
    color_mapping = get_color_mapping(task, labels)
    filter_buttons = []
    for label in labels:
        filter_buttons.append(filter_button(
            color_mapping[label], label, task, False))
    graph = bar_chart(data, group_task, 'Frequency', graph_title, group_task,
                      'Frequency', task, color_mapping, ['pan', 'select', 'lasso2d'], labels)
    study_tags = defaultdict(list)
    for label in labels:
        filered_ids = get_ids(task, label)
        for id in filered_ids:
            tag_info = {
                'task': task,
                'label': label,
                'color': rgb_to_hex(color_mapping[label])
            }
            study_tags[id].append(tag_info)
    return explore_layout(title, graph, filter_buttons, study_tags)


def sex_bias_view():
    title = "Is there sex bias per substance?"
    task = "Sex of Participants"
    labels = ["Male", "Female", "Both sexes", "Unknown"]
    group_task = 'Substances'
    data = get_freq_grouped(task, group_task, labels=labels)
    graph_title = 'Sex of participants of studies per substance'
    color_mapping = get_color_mapping(task, labels)
    filter_buttons = []
    for label in labels:
        filter_buttons.append(filter_button(
            color_mapping[label], label, task, False))
    graph = bar_chart(data, group_task, 'Frequency', graph_title, group_task,
                      'Frequency', task, color_mapping, ['pan', 'select', 'lasso2d'], labels)

    study_tags = defaultdict(list)
    for label in labels:
        filered_ids = get_ids(task, label)
        for id in filered_ids:
            tag_info = {
                'task': task,
                'label': label,
                'color': rgb_to_hex(color_mapping[label])
            }
            study_tags[id].append(tag_info)
    return explore_layout(title, graph, filter_buttons, study_tags)


def nr_part_view():
    title = "Number of participants per substance"
    task = "Number of Participants"
    group_task = 'Substances'
    
    data = get_freq_grouped(task, group_task)
    labels = ['1-20', '21-40', '41-60', '61-80', '81-100', '100-199', '200-499', '500-999', '≥1000', 'Unknown']
    graph_title = 'Number of participants per substance'
    color_mapping = get_color_mapping(task, labels)

    graph = bar_chart(data, group_task, 'Frequency', graph_title, group_task,
                      'Frequency', task, color_mapping, ['pan', 'select', 'lasso2d'], labels)

    filter_buttons = []
    for label in labels:
        filter_buttons.append(filter_button(
            color_mapping[label], label, task, False))
    study_tags = defaultdict(list)
    for label in labels:
        filered_ids = get_ids(task, label)
        for id in filered_ids:
            tag_info = {
                'task': task,
                'label': label,
                'color': rgb_to_hex(color_mapping[label])
            }
            study_tags[id].append(tag_info)
    return explore_layout(title, graph, filter_buttons, study_tags)