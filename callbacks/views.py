from dash import Input, Output, State, ctx, no_update

from components.graphs import bar_chart, get_ids_from_selected_data
from data.queries import get_all_labels, get_freq_grouped
from style.colors import get_color_mapping


def _build_insight_figure_and_ids(pathname: str, include_study_protocols: bool):
    if pathname == "/insights/evidence-strength":
        task = "Study Type"
        labels = [
            "Randomized-controlled trial (RCT)",
            "Systematic review/meta-analysis",
            "Other",
        ]
        group_task = "Substances"
        data_freq = get_freq_grouped(
            task,
            group_task,
            labels=labels,
            aggregate=True,
            include_study_protocols=include_study_protocols,
        )
        graph = bar_chart(
            data=data_freq,
            x=group_task,
            y="Frequency",
            title="Number of RCTs and Systematic Reviews per Substance",
            x_label=group_task,
            y_label="Frequency",
            group=task,
            color_mapping=get_color_mapping(task, labels),
            group_order=labels,
        ).figure
        filtered_df = data_freq[data_freq[task].isin(labels[:-1])]
        ids = filtered_df["Study_ID"].explode().dropna().unique().tolist()
        return graph, ids

    if pathname == "/insights/efficacy-safety":
        task = "Study Purpose"
        labels = ["Efficacy endpoints", "Safety endpoints"]
        group_task = "Substances"
        data_freq = get_freq_grouped(
            task,
            group_task,
            labels=labels,
            aggregate=True,
            include_study_protocols=include_study_protocols,
        )
        graph = bar_chart(
            data=data_freq,
            x=group_task,
            y="Frequency",
            title="Number of studies measuring efficacy and safety endpoints per substance",
            x_label=group_task,
            y_label="Frequency",
            group=task,
            color_mapping=get_color_mapping(task, labels),
            group_order=labels,
        ).figure
        filtered_df = data_freq[data_freq[task].isin(labels[:-1])]
        ids = filtered_df["Study_ID"].explode().dropna().unique().tolist()
        return graph, ids

    if pathname == "/insights/long-term":
        task = "Data Type"
        labels = ["Longitudinal short", "Longitudinal long", "Cross-sectional"]
        group_task = "Substances"
        data_freq = get_freq_grouped(
            task,
            group_task,
            labels=labels,
            aggregate=True,
            include_study_protocols=include_study_protocols,
        )
        graph = bar_chart(
            data=data_freq,
            x=group_task,
            y="Frequency",
            title="Number of studies per substance for different data types",
            x_label=group_task,
            y_label="Frequency",
            group=task,
            color_mapping=get_color_mapping(task, labels),
            group_order=labels,
        ).figure
        filtered_df = data_freq[data_freq[task].isin(labels)]
        ids = filtered_df["Study_ID"].explode().dropna().unique().tolist()
        return graph, ids

    if pathname == "/insights/sex-bias":
        task = "Sex of Participants"
        labels = ["Male", "Female", "Both sexes", "Unknown"]
        group_task = "Substances"
        data_freq = get_freq_grouped(
            task,
            group_task,
            labels=labels,
            aggregate=True,
            include_study_protocols=include_study_protocols,
        )
        graph = bar_chart(
            data=data_freq,
            x=group_task,
            y="Frequency",
            title="Sex of participants of studies per substance",
            x_label=group_task,
            y_label="Frequency",
            group=task,
            color_mapping=get_color_mapping(task, labels),
            group_order=labels,
        ).figure
        filtered_df = data_freq[data_freq[task].isin(labels)]
        ids = filtered_df["Study_ID"].explode().dropna().unique().tolist()
        return graph, ids

    if pathname == "/insights/participants":
        task = "Number of Participants"
        labels = get_all_labels(task)
        group_task = "Substances"
        data_freq = get_freq_grouped(
            task,
            group_task,
            labels=labels,
            aggregate=True,
            include_study_protocols=include_study_protocols,
        )
        graph = bar_chart(
            data=data_freq,
            x=group_task,
            y="Frequency",
            title="Number of Participants per Substance",
            x_label=group_task,
            y_label="Frequency",
            group=task,
            color_mapping=get_color_mapping(task, labels),
            group_order=labels,
        ).figure
        filtered_df = data_freq[data_freq[task].isin(labels)]
        ids = filtered_df["Study_ID"].explode().dropna().unique().tolist()
        return graph, ids

    return None, None


def register(app):

    @app.callback(
        Output("selected-ids", "data", allow_duplicate=True),
        Output("view-bar-chart", "figure", allow_duplicate=True),
        Output("default-view-ids", "data", allow_duplicate=True),
        Output("default-view-figure", "data", allow_duplicate=True),
        Input("reset-btn", "n_clicks"),
        Input("view-bar-chart", "selectedData"),
        Input({"type": "include-study-protocol-toggle", "index": "insight-chart"}, "value"),
        State("default-view-ids", "data"),
        State("default-view-figure", "data"),
        State("url", "pathname"),
        prevent_initial_call=True,
    )
    def update_selected_ids_and_view(
        _reset_clicks,
        selected_data,
        include_study_protocol_toggle,
        default_view_ids,
        default_view_figure,
        pathname,
    ):
        trigger = ctx.triggered_id
        is_toggle_trigger = isinstance(trigger, dict) and trigger.get("type") == "include-study-protocol-toggle"

        if trigger == "reset-btn":
            # Replace the whole figure
            return (
                default_view_ids,
                default_view_figure,
                no_update,
                no_update,
            )

        if is_toggle_trigger:
            include_study_protocols = "include" in (include_study_protocol_toggle or [])
            figure, ids = _build_insight_figure_and_ids(pathname, include_study_protocols)
            if figure is None:
                return no_update, no_update, no_update, no_update
            return ids, figure, ids, figure

        if not selected_data or not selected_data.get("points"):
            return no_update, no_update, no_update, no_update

        selected_ids = get_ids_from_selected_data([selected_data])

        return (
            selected_ids if selected_ids else no_update,
            no_update,
            no_update,
            no_update,
        )

    @app.callback(
        Output("study-protocol-count", "children"),
        Input("filtered-study-ids", "data"),
        State("url", "pathname"),
        prevent_initial_call=False,
    )
    def update_study_protocol_count(filtered_ids, pathname):
        if pathname != "/insights/study-protocol":
            return no_update

        count = len(filtered_ids or [])
        return f"Total number of study protocols: {count}"
