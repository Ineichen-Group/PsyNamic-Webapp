from collections import defaultdict
from dash import html, dcc
import dash_bootstrap_components as dbc
from style.colors import get_color_mapping
from components.layout import filter_component, studies_display, filter_button, study_grid
from components.graphs import bar_chart
from data.queries import get_freq_grouped, get_ids, get_pred_filtered, get_all_labels, nr_studies
from callbacks import rgb_to_hex
from collections import OrderedDict


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


def view_layout(title: str, graph: dcc.Graph, filter_buttons: list[dbc.Button],  ids: list[int], info_buttons: list[dbc.Button] = None, tags: OrderedDict = None) -> html.Div:

    return html.Div([
        html.H1(f'{title}', className="my-4"),
        graph,
        html.H4("Filtered Studies"),
        filter_component(
            filter_buttons, info_buttons if info_buttons else None),
        dcc.Store(id="filtered-study-ids", data=ids, storage_type="memory"),
        dcc.Store(id="filter-tags", data=tags, storage_type="memory"),
        study_grid(nr_studies(), len(ids), 'today', tags=True)
    ])
    


def rct_view():
    title = "Assessing evidence strength: How many Randomized Controlled Trials (RCTs) and Systematic Reviews are there per substance?"
    task = 'Study Type'
    labels = [
        'Randomized-controlled trial (RCT)', 'Systematic review/meta-analysis', 'Other']
    group_task = 'Substances'
    graph_title = 'Number of RCTs and Systematic Reviews per Substance'

    color_mapping = get_color_mapping(task, labels)

    data_rct = get_freq_grouped(task, group_task, labels=labels)
    data_rct_freq = data_rct_freq = data_rct.groupby([group_task, task]).size().reset_index(name='Frequency')
    graph = bar_chart(data_rct_freq, group_task, 'Frequency', graph_title, group_task, 'Frequency',
                      task, color_mapping, ['pan', 'select', 'lasso2d'], labels)

    filter_buttons = get_filter_buttons(task, labels[:-1])
    group_labels = get_all_labels(group_task)
    info_buttons = get_filter_buttons(
        group_task, group_labels)
    
    ids = data_rct[data_rct[task].isin(labels[:-1])]['Study_ID'].unique().tolist()

    # Setting tags
    tags = OrderedDict()
    tags[task] = labels[:-1]
    tags[group_task] = group_labels 


    return view_layout(title, graph, filter_buttons, ids, info_buttons, tags)


def efficacy_safety_view():
    title = "Effectiveness and safety: Is there enough studies measuring efficacy and safety endpoints per substance?"
    task = "Study Purpose"
    labels = ["Efficacy endpoints", "Safety endpoints"]
    group_task = 'Substances'
    graph_title = 'Number of studies measuring efficacy and safety endpoints per substance'

    data = get_freq_grouped(task, group_task, labels=labels)
    data_freq = data.groupby([group_task, task]).size().reset_index(name='Frequency')

    graph = bar_chart(data_freq, group_task, 'Frequency', graph_title, group_task, 'Frequency',
                      task, get_color_mapping(task, labels), ['pan', 'select', 'lasso2d'], labels)

    filter_buttons = get_filter_buttons(task, labels)
    group_labels = get_all_labels(group_task)
    info_buttons = get_filter_buttons(
        group_task, group_labels)

    ids = data[data[task].isin(labels)]['Study_ID'].unique().tolist()

    # Setting tags
    tags = OrderedDict()
    tags[task] = labels
    tags[group_task] = group_labels

    return view_layout(title, graph, filter_buttons, ids, info_buttons, tags)


def longitudinal_view():
    title = "Do we have enough longitudinal studies and cross-sectional studies for each substance?"
    task = "Data Type"
    labels = ["Longitudinal short", "Longitudinal long", "Cross-sectional"]
    group_task = 'Substances'
    graph_title = 'Number of studies per substance for different data types'

    data = get_freq_grouped(task, group_task, labels=labels)
    data_freq = data.groupby([group_task, task]).size().reset_index(name='Frequency')

    graph = bar_chart(data_freq, group_task, 'Frequency', graph_title, group_task, 'Frequency',
                      task, get_color_mapping(task, labels), ['pan', 'select', 'lasso2d'], labels)


    filter_buttons = get_filter_buttons(task, labels)
    info_buttons = get_filter_buttons(
        group_task, get_all_labels(group_task))
    
    ids = data[data[task].isin(labels)]['Study_ID'].unique().tolist()

    return view_layout(title, graph, filter_buttons, ids, info_buttons)


def sex_bias_view():
    title = "Is there sex bias per substance?"
    task = "Sex of Participants"
    labels = ["Male", "Female", "Both sexes", "Unknown"]
    group_task = 'Substances'
    graph_title = 'Sex of participants of studies per substance'

    data = get_freq_grouped(task, group_task, labels=labels)
    data_freq = data.groupby([group_task, task]).size().reset_index(name='Frequency')

    filter_buttons = get_filter_buttons(task, labels)
    graph = bar_chart(data_freq, group_task, 'Frequency', graph_title, group_task, 'Frequency',
                      task, get_color_mapping(task, labels), ['pan', 'select', 'lasso2d'], labels)

    info_buttons = get_filter_buttons(
        group_task, get_all_labels(group_task))
    
    ids = data[data[task].isin(labels)]['Study_ID'].unique().tolist()

    return view_layout(title, graph, filter_buttons, ids, info_buttons)


def nr_part_view():
    title = "Study Participation: How many participants are included per study?"
    task = "Number of Participants"
    group_task = 'Substances'
    labels = ['1-20', '21-40', '41-60', '61-80', '81-100',
              '100-199', '200-499', '500-999', '≥1000', 'Unknown']
    graph_title = 'Number of Participants per Substance'

    data = get_freq_grouped(task, group_task)
    data_freq = data.groupby([group_task, task]).size().reset_index(name='Frequency')
    filter_buttons = get_filter_buttons(task, labels)
    graph = bar_chart(data_freq, group_task, 'Frequency', graph_title, group_task, 'Frequency',
                      task, get_color_mapping(task, labels), ['pan', 'select', 'lasso2d'], labels)

    info_buttons = get_filter_buttons(
        group_task, get_all_labels(group_task))
    
    ids = data[data[task].isin(labels)]['Study_ID'].unique().tolist()

    return view_layout(title, graph, filter_buttons, ids, info_buttons)


def study_protocol_view():
    return
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
    # return html.Div([
    #     html.H1(f'{title}', className="my-4"),
    #     studies_display()
    # ])
    id = 'study_view_test'

    tags = False
    last_update = 'today'
    total_nr = nr_studies()
    ids = list(get_ids('Substances', 'LSD'))
    # Persist ids into store
    
    return html.Div([
        html.H1(f'{title}', className="my-4"),
        studies_display()
    ])
