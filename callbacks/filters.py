
from collections import OrderedDict

import dash_bootstrap_components as dbc
from dash import ALL, ctx, no_update
from dash.dependencies import Input, Output, State

from callbacks.utils import log_time
from components.layout import build_filter_info_buttons
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


def get_active_filters_from_checklist(selected_task: str, selected_labels: list[str], active_filters: OrderedDict[str, list[str]]) -> OrderedDict[str, list[str]]:
    """Creates an OrderedDict of active filters based on the selected task and labels and adds them to the existing active filters."""
    active_filters = OrderedDict(active_filters or {})
    active_filters[selected_task] = selected_labels
    return active_filters


def register(app):
    @app.callback(
        Output("checkbox-container", "children"),
        Input("task-dropdown", "value"),
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
        Output("active-filter-buttons", "children", allow_duplicate=True),
        Output("label-checklist", "value"),
        Input("add-filter-btn", "n_clicks"),
        Input({'type': 'filter-button', 'task': ALL, 'label': ALL}, 'n_clicks'),
        State("active-filters", "data"),
        State("label-checklist", "value"),
        State("task-dropdown", "value"),
        prevent_initial_call=True
    )
    def modify_filter(_, remove_filter_clicks: list[int], active_filters: OrderedDict[str, list[str]], label_checklist: list[str], task: str):
        """Modifies the active filters based on user interactions with the checklist and filter buttons."""
        # Case 1: checkboxes are adjusted and the "Add Filter" button is clicked, can mean adding or removing
        if ctx.triggered_id == "add-filter-btn":
            new_active_filters = get_active_filters_from_checklist(
                task, label_checklist, active_filters)
            if new_active_filters[task] == []:
                return no_update, no_update, no_update
            else:
                active_filters = new_active_filters
                buttons = build_filter_info_buttons(active_filters, editable=True, map_all_labels=False)
                return active_filters, buttons, label_checklist
        # Case 2: a filter button is clicked to remove a filter
        else:
            active_filters, label_to_remove = remove_filters_from_active_filter(
                active_filters, remove_filter_clicks)
            buttons = build_filter_info_buttons(active_filters, editable=True, map_all_labels=False)
            if label_to_remove in label_checklist:
                label_checklist.remove(label_to_remove)
            return active_filters, buttons, label_checklist
