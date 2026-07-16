
import json
from collections import OrderedDict

import dash
import dash_bootstrap_components as dbc
from dash import ALL, ctx
from dash.dependencies import Input, Output, State

from callbacks.utils import log_time
from components.layout import filter_button, get_tags
from data.queries import get_all_labels


def remove_filters_from_active_filter(active_filters: OrderedDict[str, list[str]], filters_to_remove: list[int]) -> OrderedDict[str, list[str]]:
    """Removes specified filters from the active filters."""
    # active filter: {'Age of Participants': ['Pediatric (< 18 years old)', 'Unknown', 'Not applicable'],
    #                  'Condition': ['Depression']}
    # filters_to_remove: [0, 0, 0, 1] --> depression shall be removed
    updated_filters = OrderedDict()
    flattened_filters = [
        (task, label)
        for task, labels in active_filters.items()
        for label in labels
    ]

    remove_index = filters_to_remove.index(1)
    task_to_remove, label_to_remove = flattened_filters[remove_index]
    for task, labels in active_filters.items():
        remaining_labels = [
            label
            for label in labels
            if not (task == task_to_remove and label == label_to_remove)
        ]

        if remaining_labels:
            updated_filters[task] = remaining_labels

    return updated_filters, label_to_remove


def create_filter_buttons(active_filters: OrderedDict[str, list[str]]) -> list[dbc.Button]:
    """Creates a list of dbc.Buttons for the active filters."""
    tags = get_tags(active_filters)

    return [
        filter_button(
            tag["color"],
            tag["label"],
            tag["task"],
            editable=True
        )
        for task in tags
        for tag in tags[task]
    ]


def get_active_filters_from_checklist(selected_task: str, selected_labels: list[str], active_filters: OrderedDict[str, list[str]]) -> OrderedDict[str, list[str]]:
    """Creates an OrderedDict of active filters based on the selected task and labels and adds them to the existing active filters."""
    if active_filters is None:
        return OrderedDict({selected_task: selected_labels})
    else:
        active_filters[selected_task] = selected_labels
        return active_filters


def register(app):
    @app.callback(
        Output("checkbox-container", "children"),
        Input("task-dropdown", "value"),
        # State("filter-store", "data"),
        State("active-filters", "data"),
        prevent_initial_call=False,
    )
    @log_time
    def update_checkboxes(selected_task, active_filters):
        """Updates the checklist of labels based on the selected task and active filters (= previously selected labels)."""
        if not selected_task:
            return ""

        active_filters = active_filters or {}
        # Fetch labels at runtime to avoid relying on module-level cached `filter_data`
        labels = get_all_labels(selected_task)
        checked_labels = active_filters.get(selected_task, [])

        return dbc.Checklist(
            options=[{"label": label, "value": label} for label in labels],
            id="label-checklist",
            inline=True,
            value=checked_labels,
        )

    @app.callback(
        Output("active-filters", "data", allow_duplicate=True),
        Output("active-filter-buttons", "children"),
        Output("label-checklist", "value"),
        Input("add-filter-btn", "n_clicks"),
        Input({'type': 'filter-button', 'task': ALL, 'label': ALL}, 'n_clicks'),
        State("active-filters", "data"),
        State("label-checklist", "value"),
        State("task-dropdown", "value"),
        prevent_initial_call=True
    )
    def modify_filter(add_clicks: int, remove_filter_clicks: list[int], active_filters: OrderedDict[str, list[str]], label_checklist: list[str], task: str):
        # Case 1: checkboxes are adjusted and the "Add Filter" button is clicked, can mean adding or removing
        if ctx.triggered_id == "add-filter-btn":
            active_filters = get_active_filters_from_checklist(
                task, label_checklist, active_filters)
            buttons = create_filter_buttons(active_filters)
            return active_filters, buttons, label_checklist
        # Case 2: a filter button is clicked to remove a filter
        else:
            active_filters, label_to_remove = remove_filters_from_active_filter(
                active_filters, remove_filter_clicks)
            buttons = create_filter_buttons(active_filters)
            if label_to_remove in label_checklist:
                label_checklist.remove(label_to_remove)
            return active_filters, buttons, label_checklist

    # @app.callback(
    #     Output("active-filter-buttons", "children"),
    #     Output("filter-store", "data"),
    #     Output("filtered-study-ids", "data"),
    #     Output("filter-tags", "data"),
    #     Output("label-checklist", "value"),
    #     Input("add-filter-btn", "n_clicks"),
    #     Input({'type': 'filter-button', 'task': ALL, 'label': ALL}, 'n_clicks'),
    #     State("task-dropdown", "value"),
    #     State("label-checklist", "value"),
    #     State("filter-store", "data"),
    #     prevent_initial_call=True,
    # )
    # @log_time

    # def modify_filter(add_clicks, remove_clicks, selected_task, selected_labels, current_filters):

    #     ctx = callback_context
    #     if not ctx.triggered:
    #         return no_update, no_update, no_update, no_update, no_update

    #     triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    #     current_filters = (current_filters or {}).copy()

    #     # -----------------------------
    #     # ADD FILTER
    #     # -----------------------------
    #     if triggered_id == "add-filter-btn":
    #         if not selected_task or not selected_labels:
    #             return (
    #                 no_update,
    #                 no_update,
    #                 no_update,
    #                 no_update,
    #                 selected_labels,
    #             )

    #         current_filters[selected_task] = selected_labels

    #     # -----------------------------
    #     # REMOVE FILTER
    #     # -----------------------------
    #     else:
    #         button_data = json.loads(triggered_id)
    #         task = button_data['task']
    #         label = button_data['label']

    #         if task in current_filters and label in current_filters[task]:
    #             current_filters[task].remove(label)
    #             if not current_filters[task]:
    #                 del current_filters[task]

    #         selected_labels = [
    #             l for l in (selected_labels or [])
    #             if l != label
    #         ]

    #     # -----------------------------
    #     # Rebuild UI + IDs
    #     # -----------------------------
    #     ordered_tags = get_tags(current_filters)

    #     filter_buttons = [
    #         filter_button(tag['color'], tag['label'],
    #                       tag['task'], editable=True)
    #         for task in ordered_tags
    #         for tag in ordered_tags[task]
    #     ]

    #     filtered_ids = get_filtered_study_ids(current_filters)

    #     return (
    #         filter_buttons,
    #         current_filters,
    #         filtered_ids,
    #         current_filters,
    #         selected_labels,
    #     )
    # @app.callback(
    #     Output("checkbox-container", "children"),
    #     Input("task-dropdown", "value"),
    #     State("filter-store", "data"),
    #     prevent_initial_call=False,
    # )
    # def update_checkboxes(selected_task, current_filters):
    #     if not selected_task:
    #         return ""

    #     current_filters = current_filters or {}
    #     # Fetch labels at runtime to avoid relying on module-level cached `filter_data`
    #     labels = get_all_labels(selected_task)
    #     checked_labels = current_filters.get(selected_task, [])

    #     return dbc.Checklist(
    #         options=[{"label": label, "value": label} for label in labels],
    #         id="label-checklist",
    #         inline=True,
    #         value=checked_labels,
    #     )

    # @app.callback(
    #     Output("active-filter-buttons", "children"),
    #     Output("filter-store", "data"),
    #     Output("filtered-study-ids", "data"),
    #     Output("active-filters", "data"),
    #     Output("label-checklist", "value"),
    #     Input("add-filter-btn", "n_clicks"),
    #     Input({'type': 'filter-button', 'task': ALL, 'label': ALL}, 'n_clicks'),
    #     State("task-dropdown", "value"),
    #     State("label-checklist", "value"),
    #     State("filter-store", "data"),
    #     prevent_initial_call=True,
    # )
    # @log_time
    # def modify_filter(add_clicks, remove_clicks, selected_task, selected_labels, current_filters):

    #     ctx = callback_context
    #     if not ctx.triggered:
    #         return no_update, no_update, no_update, no_update, no_update

    #     triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    #     current_filters = (current_filters or {}).copy()

    #     # -----------------------------
    #     # ADD FILTER
    #     # -----------------------------
    #     if triggered_id == "add-filter-btn":
    #         if not selected_task or not selected_labels:
    #             return (
    #                 no_update,
    #                 no_update,
    #                 no_update,
    #                 no_update,
    #                 selected_labels,
    #             )

    #         current_filters[selected_task] = selected_labels

    #     # -----------------------------
    #     # REMOVE FILTER
    #     # -----------------------------
    #     else:
    #         button_data = json.loads(triggered_id)
    #         task = button_data['task']
    #         label = button_data['label']

    #         if task in current_filters and label in current_filters[task]:
    #             current_filters[task].remove(label)
    #             if not current_filters[task]:
    #                 del current_filters[task]

    #         selected_labels = [
    #             l for l in (selected_labels or [])
    #             if l != label
    #         ]

    #     # -----------------------------
    #     # Rebuild UI + IDs
    #     # -----------------------------
    #     ordered_tags = get_tags(current_filters)

    #     filter_buttons = [
    #         filter_button(tag['color'], tag['label'],
    #                       tag['task'], editable=True)
    #         for task in ordered_tags
    #         for tag in ordered_tags[task]
    #     ]

    #     filtered_ids = get_filtered_study_ids(current_filters)

    #     return (
    #         filter_buttons,
    #         current_filters,
    #         filtered_ids,
    #         current_filters,
    #         selected_labels,
    #     )
