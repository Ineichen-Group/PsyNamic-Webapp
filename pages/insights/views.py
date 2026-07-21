from collections import OrderedDict
from typing import Optional

import dash_bootstrap_components as dbc
from dash import dcc, html

from components.graphs import bar_chart, box_plot_graph
from components.layout import studies_display
from data.dosage_norm import remove_several_substances_dosages
from data.queries import (get_all_labels, get_dosage_samples, get_freq_grouped,
                          get_ids)
from style.colors import get_color_mapping


def view_layout(
    title: str,
    graph: dcc.Graph | html.Div,
    page_key: str,
    active_filters: OrderedDict,
    active_infos: OrderedDict,
    ids: Optional[list[int]] = None,
) -> html.Div:
    """Generates the standardized view wrapper containing a title, graph, and study list.

    Args:
        title: Page heading display text.
        graph: Dash Graph component or HTML container displaying data visualizations.
        page_key: Unique identifier for the page context.
        active_filters: Ordered dictionary mapping filter keys to active values.
        active_infos: Ordered dictionary mapping info keys to active values.
        ids: Optional list of filtered study database IDs.

    Returns:
        A Dash html.Div component structuring the view.
    """
    return html.Div([
        html.H1(f"{title}", className="my-4"),
        graph,
        studies_display(
            page_key=page_key,
            ids=ids,
            filters=active_filters,
            infos=active_infos,
        ),
    ])


def rct_view() -> html.Div:
    """Renders the view analyzing Randomized Controlled Trials (RCTs) vs. Systematic Reviews per substance.

    Returns:
        A Dash html.Div component with RCT frequency visualization and study lists.
    """
    title = (
        "Assessing evidence strength: How many Randomized Controlled Trials (RCTs) "
        "and Systematic Reviews are there per substance?"
    )
    task = "Study Type"
    key = "rct-view"
    labels = ["Randomized-controlled trial (RCT)", "Systematic review/meta-analysis", "Other"]
    group_task = "Substances"
    graph_title = "Number of RCTs and Systematic Reviews per Substance"

    color_mapping = get_color_mapping(task, labels)
    data_rct = get_freq_grouped(task, group_task, labels=labels)
    data_rct_freq = (
        data_rct.groupby([group_task, task])
        .size()
        .reset_index(name="Frequency")
    )

    graph = bar_chart(
        data_rct_freq,
        group_task,
        "Frequency",
        graph_title,
        group_task,
        "Frequency",
        task,
        color_mapping,
        ["pan", "select", "lasso2d"],
        labels,
    )

    active_filters = OrderedDict({task: labels})
    active_infos = OrderedDict({group_task: get_all_labels(group_task)})
    ids = (
        data_rct[data_rct[task].isin(labels[:-1])]["Study_ID"]
        .unique()
        .tolist()
    )

    return view_layout(title, graph, key, active_filters, active_infos, ids=ids)


def efficacy_safety_view() -> html.Div:
    """Renders the view displaying study counts measuring efficacy and safety endpoints per substance.

    Returns:
        A Dash html.Div component with efficacy/safety endpoint visualizations.
    """
    title = (
        "Effectiveness and safety: Is there enough studies measuring "
        "efficacy and safety endpoints per substance?"
    )
    task = "Study Purpose"
    key = "efficacy-safety-view"
    labels = ["Efficacy endpoints", "Safety endpoints"]
    group_task = "Substances"
    graph_title = "Number of studies measuring efficacy and safety endpoints per substance"

    data = get_freq_grouped(task, group_task, labels=labels)
    data_freq = (
        data.groupby([group_task, task])
        .size()
        .reset_index(name="Frequency")
    )

    graph = bar_chart(
        data_freq,
        group_task,
        "Frequency",
        graph_title,
        group_task,
        "Frequency",
        task,
        get_color_mapping(task, labels),
        ["pan", "select", "lasso2d"],
        labels,
    )

    active_filters = OrderedDict({task: labels})
    active_infos = OrderedDict({group_task: get_all_labels(group_task)})
    ids = data[data[task].isin(labels)]["Study_ID"].unique().tolist()

    return view_layout(title, graph, key, active_filters, active_infos, ids)


def longitudinal_view() -> html.Div:
    """Renders the view comparing study counts across longitudinal vs cross-sectional data types per substance.

    Returns:
        A Dash html.Div component displaying study design distribution.
    """
    title = "Do we have enough longitudinal studies and cross-sectional studies for each substance?"
    task = "Data Type"
    key = "longitudinal-view"
    labels = ["Longitudinal short", "Longitudinal long", "Cross-sectional"]
    group_task = "Substances"
    graph_title = "Number of studies per substance for different data types"

    data = get_freq_grouped(task, group_task, labels=labels)
    data_freq = (
        data.groupby([group_task, task])
        .size()
        .reset_index(name="Frequency")
    )

    graph = bar_chart(
        data_freq,
        group_task,
        "Frequency",
        graph_title,
        group_task,
        "Frequency",
        task,
        get_color_mapping(task, labels),
        ["pan", "select", "lasso2d"],
        labels,
    )

    ids = data[data[task].isin(labels)]["Study_ID"].unique().tolist()
    active_filters = OrderedDict({task: labels})
    active_infos = OrderedDict({group_task: get_all_labels(group_task)})

    return view_layout(
        title,
        graph,
        key,
        active_filters=active_filters,
        active_infos=active_infos,
        ids=ids,
    )


def sex_bias_view() -> html.Div:
    """Renders the view inspecting participant sex distribution across studies per substance.

    Returns:
        A Dash html.Div component displaying participant sex breakdowns.
    """
    title = "Is there sex bias per substance?"
    task = "Sex of Participants"
    key = "sex-bias-view"
    labels = ["Male", "Female", "Both sexes", "Unknown"]
    group_task = "Substances"
    graph_title = "Sex of participants of studies per substance"

    data = get_freq_grouped(task, group_task, labels=labels)
    data_freq = (
        data.groupby([group_task, task])
        .size()
        .reset_index(name="Frequency")
    )

    graph = bar_chart(
        data_freq,
        group_task,
        "Frequency",
        graph_title,
        group_task,
        "Frequency",
        task,
        get_color_mapping(task, labels),
        ["pan", "select", "lasso2d"],
        labels,
    )

    active_filters = OrderedDict({task: labels})
    active_infos = OrderedDict({group_task: get_all_labels(group_task)})
    ids = data[data[task].isin(labels)]["Study_ID"].unique().tolist()

    return view_layout(
        title,
        graph,
        key,
        active_filters=active_filters,
        active_infos=active_infos,
        ids=ids,
    )


def nr_part_view() -> html.Div:
    """Renders the view analyzing distribution of total participant counts per study by substance.

    Returns:
        A Dash html.Div component showcasing sample size distributions per study.
    """
    title = "Study Participation: How many participants are included per study?"
    task = "Number of Participants"
    group_task = "Substances"
    labels = [
        "1-20",
        "21-40",
        "41-60",
        "61-80",
        "81-100",
        "100-199",
        "200-499",
        "500-999",
        "≥1000",
        "Unknown",
    ]
    graph_title = "Number of Participants per Substance"
    key = "nr-part-view"

    data = get_freq_grouped(task, group_task)
    data_freq = (
        data.groupby([group_task, task])
        .size()
        .reset_index(name="Frequency")
    )
    graph = bar_chart(
        data_freq,
        group_task,
        "Frequency",
        graph_title,
        group_task,
        "Frequency",
        task,
        get_color_mapping(task, labels),
        ["pan", "select", "lasso2d"],
        labels,
    )

    ids = data[data[task].isin(labels)]["Study_ID"].unique().tolist()

    return view_layout(
        title,
        graph,
        key,
        active_filters=OrderedDict({task: labels}),
        active_infos=OrderedDict({group_task: get_all_labels(group_task)}),
        ids=ids,
    )


def study_protocol_view() -> html.Div:
    """Renders a simple summary view displaying all published study protocols.

    Returns:
        A Dash html.Div component showing total protocol counts and study items.
    """
    title = "How many study protocols are available?"
    task = "Study Type"
    label = "Study protocol"
    key = "study-protocol-view"
    filters = OrderedDict({task: [label]})

    ids = get_ids(task, label)
    freq_span = html.P(
        f"Total number of study protocols: {len(ids)}", className="mb-4"
    )

    return html.Div([
        html.H1(f"{title}", className="my-4"),
        freq_span,
        studies_display(page_key=key, ids=ids, filters=filters, tags=False),
    ])


def dosages_view() -> html.Div:
    """Renders the view displaying dosage distributions across substances using box plots.

    Returns:
        A Dash html.Div component containing dosage normalization box plots and controls.
    """
    title = "Inspecting dosage: How are different substances dosed?"

    # Fetch absolute dosage samples per substance (values in mg)
    df = remove_several_substances_dosages(get_dosage_samples())
    if df is None or df.empty:
        graph = html.P("No absolute dosage data available.")
    else:
        substance_labels = sorted(df["Substance"].unique().tolist())
        col_map = get_color_mapping("Substances", substance_labels)

        # Build three plots: LSD, Ibogaine, and the rest (stacked vertically)
        substances = sorted(df["Substance"].dropna().unique().tolist())
        lsd_subs = ["LSD"]
        ibogaine_subs = ["Ibogaine"]
        rest_subs = [s for s in substances if s not in lsd_subs + ibogaine_subs]

        graphs = []
        groups = [rest_subs, ibogaine_subs, lsd_subs]

        for i, subs in enumerate(groups):
            sub_df = df[df["Substance"].isin(subs)]
            if sub_df.empty:
                continue

            h = 200 if subs in (ibogaine_subs, lsd_subs) else 700
            add_ann = subs not in (ibogaine_subs, lsd_subs)
            plot_id = {"type": "dosage-box-plot", "index": i}

            g = box_plot_graph(
                sub_df,
                x="Substance",
                y="Dosage_mg",
                title="",
                x_label="Substance",
                y_label="Dosage (mg)",
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
            rows = [
                dbc.Row(
                    dbc.Col(g, width=12),
                    className="py-1",
                    style={"marginBottom": "6px"},
                )
                for g in graphs
            ]
            graph = html.Div(rows, style={"marginTop": "6px"})

    return html.Div([
        html.H1(f"{title}", className="my-4"),
        graph,
        dbc.Row([
            dbc.Col(
                dbc.Button(
                    "Reset selection",
                    id="dosage-reset-btn",
                    color="secondary",
                    className="mb-3",
                ),
                width="auto",
            ),
        ]),
        studies_display(
            page_key="dosage-normalization-page",
            grid_id="dosage-study-grid",
            is_dosage=True,
            tags=True,
        ),
    ])