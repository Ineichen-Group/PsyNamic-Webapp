
from collections import OrderedDict

import dash_bootstrap_components as dbc
from dash import ALL, ctx, no_update
from dash.dependencies import Input, Output, State

from callbacks.utils import log_time
from components.layout import build_filter_info_buttons, checkbox_filter_selection
from data.queries import get_all_labels, get_ids_from_boolean_query


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
        State("advanced-mode", "data"),
        prevent_initial_call=False,
    )
    @log_time
    def update_checkboxes(selected_task, active_filters, advanced_mode):
        """Updates the checklist of labels based on the selected task and active filters (= previously selected labels)."""
        checklist_cls = dbc.RadioItems if advanced_mode else dbc.Checklist
        empty_value = None if advanced_mode else []

        if not selected_task:
            return checklist_cls(id="label-checklist", options=[], value=empty_value, inline=True)

        active_filters = active_filters or {}
        # Fetch labels at runtime to avoid relying on module-level cached `filter_data`
        labels = get_all_labels(selected_task)
        checked_labels = active_filters.get(selected_task, [])
        if advanced_mode:
            checked_labels = checked_labels[0] if checked_labels else None

        return checklist_cls(
            options=[{"label": label, "value": label} for label in labels],
            id="label-checklist",
            inline=True,
            value=checked_labels,
        )

    @app.callback(
        Output("active-filters", "data", allow_duplicate=True),
        Output("active-filter-buttons", "children", allow_duplicate=True),
        Output("label-checklist", "value"),
        Output("filter-text", "value"),
        Input("add-filter-btn", "n_clicks"),
        Input({'type': 'filter-button', 'task': ALL, 'label': ALL}, 'n_clicks'),
        Input("clear-search-btn", "n_clicks"),
        State("active-filters", "data"),
        State("label-checklist", "value"),
        State("task-dropdown", "value"),
        State("advanced-mode", "data"),
        State("filter-text", "value"),
        prevent_initial_call=True
    )
    def modify_filter(
        _,
        remove_filter_clicks: list[int],
        clear_search_clicks: int,
        active_filters: OrderedDict[str, list[str]],
        label_checklist,
        task: str,
        advanced_mode: bool,
        current_filter_text: str,
    ):
        """Modifies the active filters based on user interactions."""
        # RadioItems (single-select, advanced mode) yields a bare value instead of a list
        if not isinstance(label_checklist, list):
            label_checklist = [label_checklist] if label_checklist else []
        # Case 1: Add/remove filters using the Add Filter button
        if ctx.triggered_id == "add-filter-btn":
            # Advanced mode: append "Task = Label" to the manually built expression instead of
            # overwriting active_filters/rebuilding the whole search string.
            if advanced_mode:
                label = label_checklist[0] if label_checklist else None
                if not task or not label:
                    return no_update, no_update, no_update, no_update

                token = f"{task} = {label}"
                current_text = (current_filter_text or "").rstrip()
                new_text = f"{current_text} {token}" if current_text else token

                return no_update, no_update, no_update, new_text

            new_active_filters = get_active_filters_from_checklist(
                task,
                label_checklist,
                active_filters
            )

            if new_active_filters == active_filters:
                return no_update, no_update, no_update, no_update

            elif len(new_active_filters) == 1 and new_active_filters[task] == []:
                return {}, [], [], ""

            else:
                active_filters = new_active_filters
                buttons = build_filter_info_buttons(
                    active_filters,
                    editable=True,
                    map_all_labels=False
                )

                search_string = build_search_string(active_filters)

                return (
                    active_filters,
                    buttons,
                    label_checklist,
                    search_string,
                )

        # Case 2: A filter button is clicked to remove a filter
        # Case 3: Clear search button clicked
        elif ctx.triggered_id == "clear-search-btn":
            return {}, [], [], ""

        # Case 2: A filter button is clicked to remove a filter
        else:
            active_filters, label_to_remove = remove_filters_from_active_filter(
                active_filters,
                remove_filter_clicks
            )

            buttons = build_filter_info_buttons(
                active_filters,
                editable=True,
                map_all_labels=False
            )

            if label_to_remove in label_checklist:
                label_checklist.remove(label_to_remove)

            search_string = build_search_string(active_filters)

            return (
                active_filters,
                buttons,
                label_checklist,
                search_string,
            )

    @app.callback(
        Output("filter-selection-container", "children"),
        Input("advanced-filter-btn", "value"),
        prevent_initial_call=True,
    )
    def advanced_filter_callback(advanced_enabled):
        """Switches between the standard and advanced filter UI."""
        return checkbox_filter_selection(advanced=bool(advanced_enabled))

    @app.callback(
        Output("filter-text", "value", allow_duplicate=True),
        Input({"type": "operator-btn", "op": ALL}, "n_clicks"),
        State("filter-text", "value"),
        prevent_initial_call=True,
    )
    def insert_operator_token(n_clicks_list, current_text):
        """Appends a boolean operator/bracket token to the filter text input."""
        if not any(n_clicks_list):
            return no_update

        op = ctx.triggered_id["op"]
        current_text = (current_text or "").rstrip()

        if not current_text:
            return "" if op == ")" else op

        if op == ")":
            return f"{current_text})"

        return f"{current_text} {op}"

    @app.callback(
        Output("filtered-study-ids", "data", allow_duplicate=True),
        Output("filter-text", "invalid", allow_duplicate=True),
        Input("apply-filter-btn", "n_clicks"),
        State("filter-text", "value"),
        prevent_initial_call=True,
    )
    def apply_advanced_filter(n_clicks, query_text):
        """Parses the manually edited filter text as a boolean expression and filters studies by it."""
        try:
            ids = get_ids_from_boolean_query(query_text)
        except ValueError:
            return no_update, True

        return ids, False


def build_search_string(active_filters) -> str:
    """
    Builds a search string from the active filters.

    Examples:
        {"Application Form": ["Nasal", "Oral"]}
        -> "Application Form = Nasal AND Oral"

        {
            "Application Form": ["Nasal", "Oral"],
            "Data Type": ["Cross-sectional", "Longitudinal"]
        }
        -> "(Application Form = Nasal AND Oral) AND "
           "(Data Type = Cross-sectional AND Longitudinal)"
    """
    filter_groups = []

    for task, labels in active_filters.items():
        if not labels:
            continue

        values = " AND ".join(
            f"{task} = {label}" if i == 0 else label
            for i, label in enumerate(labels)
        )

        if len(active_filters) > 1:
            values = f"({values})"

        filter_groups.append(values)

    return " AND ".join(filter_groups)
