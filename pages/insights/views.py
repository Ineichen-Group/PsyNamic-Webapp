from collections import defaultdict
from dash import html, dcc
import dash_bootstrap_components as dbc
from style.colors import get_color_mapping
from components.layout import filter_component, studies_display, filter_button  # , filter_tag
from components.graphs import bar_chart
from data.queries import get_freq_grouped, get_ids, get_pred_filtered, get_all_labels, get_freq
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
    title = "Assessing evidence strength: How many Randomized Controlled Trials (RCTs) and Systematic Reviews are there per substance?"
    task = 'Study Type'
    labels = [
        'Randomized-controlled trial (RCT)', 'Systematic review/meta-analysis', 'Other']
    group_task = 'Substances'
    data_rct = get_freq_grouped(task, group_task, labels=labels)
    graph_title = 'Number of RCTs and Systematic Reviews per Substance'
    filter_buttons = []
    color_mapping_task = get_color_mapping(task, labels)
    for label in labels:
        if label != 'Other':
            filter_buttons.append(filter_button(
                color_mapping_task[label], label, task, False))
    graph = bar_chart(data_rct, group_task, 'Frequency', graph_title, group_task,
                      'Frequency', task, color_mapping_task, ['pan', 'select', 'lasso2d'], labels)
    study_tags = defaultdict(list)
    group_task_all_labels = get_all_labels(group_task)
    color_mapping_group_task = get_color_mapping(
        group_task, group_task_all_labels)

    id_groups = [get_ids(task, label)
                 for label in labels[:-1]]  # exclude 'Other'

    # Add tags for RCTs and Systematic Reviews
    for label, ids in zip(labels[:-1], id_groups):
        for id in ids:
            tag_info = {
                'task': task,
                'label': label,
                'color': rgb_to_hex(color_mapping_task[label])
            }
            study_tags[id].append(tag_info)
    # collaps all ids to one list
    all_ids = set([id for ids in id_groups for id in ids])
    group_task_pred = get_pred_filtered(group_task, all_ids)
    for id in all_ids:
        for s in group_task_pred[group_task_pred['paper_id'] == id]['label'].tolist():
            tag_info_subst = {
                'task': group_task,
                'label': s,
                'color': rgb_to_hex(color_mapping_group_task[s])
            }
            study_tags[id].append(tag_info_subst)

    return explore_layout(title, graph, filter_buttons, study_tags)


def efficacy_safety_view():
    title = "Effectiveness and safety: Is there enough studies measuring efficacy and safety endpoints per substance?"
    task = "Study Purpose"
    labels = ["Efficacy endpoints", "Safety endpoints"]
    group_task = 'Substances'
    data = get_freq_grouped(task, group_task, labels=labels)
    graph_title = 'Number of studies measuring efficacy and safety endpoints per substance'
    color_mapping = get_color_mapping(task, labels)
    color_mapping_group_task = get_color_mapping(
        group_task, get_all_labels(group_task))
    filter_buttons = []
    for label in labels:
        filter_buttons.append(filter_button(
            color_mapping[label], label, task, False))
    graph = bar_chart(data, group_task, 'Frequency', graph_title, group_task,
                      'Frequency', task, color_mapping, ['pan', 'select', 'lasso2d'], labels)
    study_tags = defaultdict(list)

    all_ids = set()
    for label in labels:
        ids = get_ids(task, label)
        all_ids.update(ids)
        for id in ids:
            tag_info = {
                'task': task,
                'label': label,
                'color': rgb_to_hex(color_mapping[label])
            }
            study_tags[id].append(tag_info)

    group_task_pred = get_pred_filtered(group_task, all_ids)
    for id in ids:
        for s in group_task_pred[group_task_pred['paper_id'] == id]['label'].tolist():
            tag_info_subst = {
                'task': group_task,
                'label': s,
                'color': rgb_to_hex(color_mapping_group_task[s])
            }
            study_tags[id].append(tag_info_subst)
    return explore_layout(title, graph, filter_buttons, study_tags)


def longitudinal_view():
    title = "Do we have enough longitudinal studies and cross-sectional studies for each substance?"
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
    all_ids = set()
    for label in labels:
        filered_ids = get_ids(task, label)
        all_ids.update(filered_ids)
        for id in filered_ids:
            tag_info = {
                'task': task,
                'label': label,
                'color': rgb_to_hex(color_mapping[label])
            }
            study_tags[id].append(tag_info)
    group_task_pred = get_pred_filtered(group_task, all_ids)
    color_mapping_group_task = get_color_mapping(
        group_task, get_all_labels(group_task))
    for id in all_ids:
        for s in group_task_pred[group_task_pred['paper_id'] == id]['label'].tolist():
            tag_info_subst = {
                'task': group_task,
                'label': s,
                'color': rgb_to_hex(color_mapping_group_task[s])
            }
            study_tags[id].append(tag_info_subst)

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
    all_ids = set()
    for label in labels:
        filered_ids = get_ids(task, label)
        all_ids.update(filered_ids)
        for id in filered_ids:
            tag_info = {
                'task': task,
                'label': label,
                'color': rgb_to_hex(color_mapping[label])
            }
            study_tags[id].append(tag_info)
    group_task_pred = get_pred_filtered(group_task, all_ids)
    color_mapping_group_task = get_color_mapping(
        group_task, get_all_labels(group_task))
    for id in all_ids:
        for s in group_task_pred[group_task_pred['paper_id'] == id]['label'].tolist():
            tag_info_subst = {
                'task': group_task,
                'label': s,
                'color': rgb_to_hex(color_mapping_group_task[s])
            }
            study_tags[id].append(tag_info_subst)

    return explore_layout(title, graph, filter_buttons, study_tags)


def nr_part_view():
    title = "Study Participation: How many participants are included per study?"
    task = "Number of Participants"
    group_task = 'Substances'

    data = get_freq_grouped(task, group_task)
    labels = ['1-20', '21-40', '41-60', '61-80', '81-100',
              '100-199', '200-499', '500-999', '≥1000', 'Unknown']
    graph_title = 'Number of Prticipants per Substance'
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


def study_protocol_view():
    title = "How many study protocols are available?"
    task = "Study Type"
    label = "Study protocol"
    color_mapping = get_color_mapping(task, [label])

    ids = get_ids(task, label)
    study_tags = defaultdict(list)
    for id in ids:
        tag_info = {
            'task': task,
            'label': label,
            'color': rgb_to_hex(color_mapping[label])
        }
        study_tags[id].append(tag_info)
    # Count ids and write frequency in a span

    freq_span = html.Span(
        f"Total number of study protocols: {len(ids)}", className="my-4")

    return html.Div([
        html.H1(f'{title}', className="my-4"),
        freq_span,
        filter_component(filter_button(
            color_mapping[label], label, task, False)),
        studies_display(study_tags)
    ]
    )
