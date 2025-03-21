from collections import defaultdict
from dash import html, dcc
import dash_bootstrap_components as dbc
from style.colors import get_color_mapping
from components.layout import filter_component, studies_display, filter_button
from components.graphs import bar_chart
from data.queries import get_freq_grouped, get_ids, get_pred_filtered, get_all_labels
from callbacks import rgb_to_hex


def get_filter_buttons(task, labels):
    """
    Creates filter buttons based on task and labels.
    """
    color_mapping = get_color_mapping(task, labels)
    buttons = []
    for label in labels:
        buttons.append(filter_button(
            color_mapping[label], label, task))
    return buttons


def get_study_tags(labels, task, group_task, color_mapping_task):
    """
    Creates a study tag mapping for given task and labels.
    """
    study_tags = defaultdict(list)
    for label in labels:
        ids = get_ids(task, label)
        for id in ids:
            tag_info = {
                'task': task,
                'label': label,
                'color': rgb_to_hex(color_mapping_task[label])
            }
            study_tags[id].append(tag_info)

    # Fetch and add group task labels
    group_task_pred = get_pred_filtered(group_task, [id for ids in [
                                        get_ids(task, label) for label in labels] for id in ids])
    color_mapping_group_task = get_color_mapping(
        group_task, get_all_labels(group_task))

    for id in study_tags:
        for s in group_task_pred[group_task_pred['paper_id'] == id]['label'].tolist():
            tag_info_subst = {
                'task': group_task,
                'label': s,
                'color': rgb_to_hex(color_mapping_group_task[s])
            }
            study_tags[id].append(tag_info_subst)

    return study_tags


def view_layout(title: str, graph: dcc.Graph, filter_buttons: list[dbc.Button], info_buttons: list[dbc.Button] = None, study_tags: dict[str, list[html.Div]] = None) -> html.Div:
    return html.Div([
        html.H1(f'{title}', className="my-4"),
        graph,
        html.H4("Filtered Studies"),
        filter_component(
            filter_buttons, info_buttons if info_buttons else None),
        studies_display(study_tags)
    ])


def rct_view():
    title = "Assessing evidence strength: How many Randomized Controlled Trials (RCTs) and Systematic Reviews are there per substance?"
    task = 'Study Type'
    labels = [
        'Randomized-controlled trial (RCT)', 'Systematic review/meta-analysis', 'Other']
    group_task = 'Substances'
    graph_title = 'Number of RCTs and Systematic Reviews per Substance'

    data_rct = get_freq_grouped(task, group_task, labels=labels)
    filter_buttons = get_filter_buttons(task, labels[:-1])  # Excluding 'Other'
    group_labels = get_all_labels(group_task)
    info_buttons = get_filter_buttons(
        group_task, group_labels)

    graph = bar_chart(data_rct, group_task, 'Frequency', graph_title, group_task, 'Frequency',
                      task, get_color_mapping(task, labels), ['pan', 'select', 'lasso2d'], labels)

    study_tags = get_study_tags(
        labels[:-1], task, group_task, get_color_mapping(task, labels))

    return view_layout(title, graph, filter_buttons, info_buttons, study_tags)


def efficacy_safety_view():
    title = "Effectiveness and safety: Is there enough studies measuring efficacy and safety endpoints per substance?"
    task = "Study Purpose"
    labels = ["Efficacy endpoints", "Safety endpoints"]
    group_task = 'Substances'
    graph_title = 'Number of studies measuring efficacy and safety endpoints per substance'

    data = get_freq_grouped(task, group_task, labels=labels)
    filter_buttons = get_filter_buttons(task, labels)
    group_labels = get_all_labels(group_task)
    info_buttons = get_filter_buttons(
        group_task, group_labels)

    graph = bar_chart(data, group_task, 'Frequency', graph_title, group_task, 'Frequency',
                      task, get_color_mapping(task, labels), ['pan', 'select', 'lasso2d'], labels)
    study_tags = get_study_tags(
        labels, task, group_task, get_color_mapping(task, labels))

    return view_layout(title, graph, filter_buttons, info_buttons, study_tags)


def longitudinal_view():
    title = "Do we have enough longitudinal studies and cross-sectional studies for each substance?"
    task = "Data Type"
    labels = ["Longitudinal short", "Longitudinal long", "Cross-sectional"]
    group_task = 'Substances'
    graph_title = 'Number of studies per substance for different data types'

    data = get_freq_grouped(task, group_task, labels=labels)

    filter_buttons = get_filter_buttons(task, labels)

    graph = bar_chart(data, group_task, 'Frequency', graph_title, group_task, 'Frequency',
                      task, get_color_mapping(task, labels), ['pan', 'select', 'lasso2d'], labels)

    study_tags = get_study_tags(
        labels, task, group_task, get_color_mapping(task, labels))
    info_buttons = get_filter_buttons(
        group_task, get_all_labels(group_task))

    return view_layout(title, graph, filter_buttons, info_buttons=info_buttons, study_tags=study_tags)


def sex_bias_view():
    title = "Is there sex bias per substance?"
    task = "Sex of Participants"
    labels = ["Male", "Female", "Both sexes", "Unknown"]
    group_task = 'Substances'
    graph_title = 'Sex of participants of studies per substance'

    data = get_freq_grouped(task, group_task, labels=labels)
    filter_buttons = get_filter_buttons(task, labels)

    graph = bar_chart(data, group_task, 'Frequency', graph_title, group_task, 'Frequency',
                      task, get_color_mapping(task, labels), ['pan', 'select', 'lasso2d'], labels)

    study_tags = get_study_tags(
        labels, task, group_task, get_color_mapping(task, labels))

    info_buttons = get_filter_buttons(
        group_task, get_all_labels(group_task))

    return view_layout(title, graph, filter_buttons, info_buttons=info_buttons, study_tags=study_tags)


def nr_part_view():
    title = "Study Participation: How many participants are included per study?"
    task = "Number of Participants"
    group_task = 'Substances'
    labels = ['1-20', '21-40', '41-60', '61-80', '81-100',
              '100-199', '200-499', '500-999', '≥1000', 'Unknown']
    graph_title = 'Number of Participants per Substance'

    data = get_freq_grouped(task, group_task)
    filter_buttons = get_filter_buttons(task, labels)
    graph = bar_chart(data, group_task, 'Frequency', graph_title, group_task, 'Frequency',
                      task, get_color_mapping(task, labels), ['pan', 'select', 'lasso2d'], labels)

    study_tags = get_study_tags(
        labels, task, group_task, get_color_mapping(task, labels))
    info_buttons = get_filter_buttons(
        group_task, get_all_labels(group_task))

    return view_layout(title, graph, filter_buttons, info_buttons=info_buttons, study_tags=study_tags)


def study_protocol_view():
    title = "How many study protocols are available?"
    task = "Study Type"
    label = "Study protocol"
    graph_title = "Number of Study Protocols"

    # Fetch data
    color_mapping = get_color_mapping(task, [label])
    ids = get_ids(task, label)

    # Create study tags
    study_tags = defaultdict(list)
    for id in ids:
        tag_info = {
            'task': task,
            'label': label,
            'color': rgb_to_hex(color_mapping[label])
        }
        study_tags[id].append(tag_info)

    # Count ids
    freq_span = html.Span(
        f"Total number of study protocols: {len(ids)}", className="my-4")

    return html.Div([
        html.H1(f'{title}', className="my-4"),
        freq_span,
        html.H4("Filtered Studies"),
        filter_component(filter_button(
            color_mapping[label], label, task, False)),
        studies_display(study_tags)
    ])


def dosages_view():
    title = "Inspecting dosage: How are different substances dosed?"
    return html.Div([
        html.H1(f'{title}', className="my-4"),
        studies_display()
    ])
