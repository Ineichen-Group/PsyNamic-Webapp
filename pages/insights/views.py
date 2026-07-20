from collections import OrderedDict

import dash_bootstrap_components as dbc
from dash import dcc, html

from components.graphs import bar_chart, box_plot_graph
from components.layout import (dosage_study_grid, get_filter_buttons,
                               studies_display)
from data.dosage_norm import remove_several_substances_dosages
from data.queries import (get_all_labels, get_dosage_samples, get_freq_grouped,
                          get_ids, get_studies_details_ner, latest_update,
                          nr_studies)
from style.colors import get_color_mapping


def view_layout(title: str, graph: dcc.Graph, page_key:str, active_filters: OrderedDict, active_infos: OrderedDict, ids: list[int] = None) -> html.Div:
    return html.Div([
        html.H1(f'{title}', className="my-4"),
        graph,
        studies_display(page_key=page_key, ids=ids, filters=active_filters, infos=active_infos),
    ])


def rct_view():
    title = "Assessing evidence strength: How many Randomized Controlled Trials (RCTs) and Systematic Reviews are there per substance?"
    task = 'Study Type'
    key = "rct-view"
    labels = [
        'Randomized-controlled trial (RCT)', 'Systematic review/meta-analysis', 'Other']
    group_task = 'Substances'
    graph_title = 'Number of RCTs and Systematic Reviews per Substance'

    color_mapping = get_color_mapping(task, labels)

    data_rct = get_freq_grouped(task, group_task, labels=labels)
    data_rct_freq = data_rct_freq = data_rct.groupby(
        [group_task, task]).size().reset_index(name='Frequency')
    graph = bar_chart(data_rct_freq, group_task, 'Frequency', graph_title, group_task, 'Frequency',
                      task, color_mapping, ['pan', 'select', 'lasso2d'], labels)

    active_filters = OrderedDict({task: labels})
    active_infos = OrderedDict({group_task: get_all_labels(group_task)})
    ids = data_rct[data_rct[task].isin(labels[:-1])]['Study_ID'].unique().tolist()
    
    return view_layout(title, graph, key, active_filters, active_infos, ids=ids)


def efficacy_safety_view():
    title = "Effectiveness and safety: Is there enough studies measuring efficacy and safety endpoints per substance?"
    task = "Study Purpose"
    key = "efficacy-safety-view"
    labels = ["Efficacy endpoints", "Safety endpoints"]
    group_task = 'Substances'
    graph_title = 'Number of studies measuring efficacy and safety endpoints per substance'

    data = get_freq_grouped(task, group_task, labels=labels)
    data_freq = data.groupby(
        [group_task, task]).size().reset_index(name='Frequency')

    graph = bar_chart(data_freq, group_task, 'Frequency', graph_title, group_task, 'Frequency',
                      task, get_color_mapping(task, labels), ['pan', 'select', 'lasso2d'], labels)

    # filter_buttons = get_filter_buttons(task, labels)
    # info_buttons = get_filter_buttons(
    #     group_task, group_labels)
    active_filters = OrderedDict({task: labels})
    active_infos = OrderedDict({group_task: get_all_labels(group_task)})

    ids = data[data[task].isin(labels)]['Study_ID'].unique().tolist()


    return view_layout(title, graph, key, active_filters, active_infos, ids)


def longitudinal_view():
    title = "Do we have enough longitudinal studies and cross-sectional studies for each substance?"
    task = "Data Type"
    key = "longitudinal-view"
    labels = ["Longitudinal short", "Longitudinal long", "Cross-sectional"]
    group_task = 'Substances'
    graph_title = 'Number of studies per substance for different data types'

    data = get_freq_grouped(task, group_task, labels=labels)
    data_freq = data.groupby(
        [group_task, task]).size().reset_index(name='Frequency')

    graph = bar_chart(data_freq, group_task, 'Frequency', graph_title, group_task, 'Frequency',
                      task, get_color_mapping(task, labels), ['pan', 'select', 'lasso2d'], labels)

    # filter_buttons = get_filter_buttons(task, labels)
    # info_buttons = get_filter_buttons(
    #     group_task, get_all_labels(group_task))

    ids = data[data[task].isin(labels)]['Study_ID'].unique().tolist()
    active_filters = OrderedDict({task: labels})
    active_infos = OrderedDict({group_task: get_all_labels(group_task)})
    # tags = OrderedDict()
    # tags[task] = labels
    # tags[group_task] = get_all_labels(group_task)

    return view_layout(title, graph, key, active_filters=active_filters, active_infos=active_infos, ids=ids)


def sex_bias_view():
    title = "Is there sex bias per substance?"
    task = "Sex of Participants"
    key = "sex-bias-view"
    labels = ["Male", "Female", "Both sexes", "Unknown"]
    group_task = 'Substances'
    graph_title = 'Sex of participants of studies per substance'

    data = get_freq_grouped(task, group_task, labels=labels)
    data_freq = data.groupby(
        [group_task, task]).size().reset_index(name='Frequency')

    # filter_buttons = get_filter_buttons(task, labels)
    graph = bar_chart(data_freq, group_task, 'Frequency', graph_title, group_task, 'Frequency',
                      task, get_color_mapping(task, labels), ['pan', 'select', 'lasso2d'], labels)

    # info_buttons = get_filter_buttons(
    #     group_task, get_all_labels(group_task))
    active_filters = OrderedDict({task: labels})
    active_infos = OrderedDict({group_task: get_all_labels(group_task)})

    ids = data[data[task].isin(labels)]['Study_ID'].unique().tolist()
    # tags = OrderedDict()
    # tags[task] = labels
    # tags[group_task] = get_all_labels(group_task)

    return view_layout(title, graph, key, active_filters=active_filters, active_infos=active_infos, ids=ids)


def nr_part_view():
    title = "Study Participation: How many participants are included per study?"
    task = "Number of Participants"
    group_task = 'Substances'
    labels = ['1-20', '21-40', '41-60', '61-80', '81-100',
              '100-199', '200-499', '500-999', '≥1000', 'Unknown']
    graph_title = 'Number of Participants per Substance'
    key = "nr-part-view"

    data = get_freq_grouped(task, group_task)
    data_freq = data.groupby(
        [group_task, task]).size().reset_index(name='Frequency')
    filter_buttons = get_filter_buttons(task, labels)
    graph = bar_chart(data_freq, group_task, 'Frequency', graph_title, group_task, 'Frequency',
                      task, get_color_mapping(task, labels), ['pan', 'select', 'lasso2d'], labels)

    info_buttons = get_filter_buttons(
        group_task, get_all_labels(group_task))

    ids = data[data[task].isin(labels)]['Study_ID'].unique().tolist()
    tags = OrderedDict()
    tags[task] = labels
    tags[group_task] = get_all_labels(group_task)

    return view_layout(title, graph, key, active_filters=OrderedDict({task: labels}), active_infos=OrderedDict({group_task: get_all_labels(group_task)}), ids=ids)

def study_protocol_view():
    title = "How many study protocols are available?"
    task = "Study Type"
    label = "Study protocol"
    key = "study-protocol-view"
    filters = OrderedDict({task: [label]})

    ids = get_ids(task, label)

    freq_span = html.P(
        f"Total number of study protocols: {len(ids)}", className="mb-4")

    return html.Div([
        html.H1(f'{title}', className="my-4"),
        freq_span,
        studies_display(page_key=key, ids=ids, filters=filters, tags=False)

    ])


def dosages_view():
    title = "Inspecting dosage: How are different substances dosed?"
    id = 'study_view_test'


    last_update = latest_update()
    total_nr = nr_studies()
    # Populate dosage view with papers that have Dosage NER tags
    studies_with_dosage = get_studies_details_ner(start_row=0, end_row=None)
    ids = [s['id'] for s in studies_with_dosage]

    # Fetch absolute dosage samples per substance and draw a box plot (values in mg)
    df = remove_several_substances_dosages(get_dosage_samples())
    if df is None or df.empty:
        graph = html.P("No absolute dosage data available.")
    else:
        # get color mapping for substances
        substance_labels = sorted(df['Substance'].unique().tolist())
        col_map = get_color_mapping('Substances', substance_labels)

        # Build three plots: LSD, Ibogaine, and the rest (stacked vertically)
        substances = sorted(df['Substance'].dropna().unique().tolist())
        lsd_subs = ['LSD']
        ibogaine_subs = ['Ibogaine']
        rest_subs = [s for s in substances if s not in lsd_subs + ibogaine_subs]

        graphs = []
        # Order: rest on top, then Ibogaine, then LSD (stacked vertically)
        groups = [rest_subs, ibogaine_subs, lsd_subs]
        for i, subs in enumerate(groups):
            sub_df = df[df['Substance'].isin(subs)]
            if sub_df.empty:
                continue
            # No separate titles per user request; page H1 provides context
            # smaller height for Ibogaine and LSD (LSD even smaller)
            if subs == ibogaine_subs:
                h = 200
            elif subs == lsd_subs:
                h = 200
            else:
                h = 700

            # Disable annotation for the lower two small plots (Ibogaine and LSD)
            add_ann = False if subs == ibogaine_subs or subs == lsd_subs else True
            # use a pattern-matching id so the callback can listen to all dosage plots
            plot_id = {"type": "dosage-box-plot", "index": i}

            g = box_plot_graph(
                sub_df,
                x='Substance',
                y='Dosage_mg',
                title='',
                x_label='Substance',
                y_label='Dosage (mg)',
                group=None,
                color_mapping=col_map,
                height=h,
                add_annotation=add_ann,
                    id=plot_id,
            )
            graphs.append(g)

        if not graphs:
            graph = html.P("No absolute dosage data available.")
        else:
            # Stack graphs vertically (each full-width)
            # Reduce vertical gaps: small vertical padding and small margin between rows
            rows = [dbc.Row(dbc.Col(g, width=12), className="py-1", style={"marginBottom": "6px"}) for g in graphs]
            graph = html.Div(rows, style={"marginTop": "6px"})

    return html.Div([
        html.H1(f'{title}', className="my-4"),
        graph,
        dbc.Row([
            dbc.Col(dbc.Button("Reset selection", id="dosage-reset-btn", color="secondary", className="mb-3"), width="auto"),
        ]),
        dosage_study_grid(total_nr, len(ids), last_update),
        # dcc.Store(id="filtered-study-ids", data=ids, storage_type="memory"),
        #dcc.Store(id="active-filters", data={}, storage_type="memory"),

    ])
