
from collections import OrderedDict
import re

import dash_bootstrap_components as dbc
from dash import ALL, ctx, no_update
from dash.dependencies import Input, Output, State

from callbacks.utils import log_time
from components.layout import build_filter_info_buttons, checkbox_filter_selection
from data.queries import get_all_labels, get_boolean_query_tags, get_ids_from_boolean_query

_OPERATOR_TOKEN_RE = re.compile(r'(\(|\)|\bAND\b|\bOR\b|\bNOT\b)')


def _coerce_year(value):
    """Normalize year input values from Dash components to int or None."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _get_expression_state(text: str) -> tuple[bool, int]:
    """Derives (expecting_atom, open_paren_depth) from the (possibly partial) filter text,
    used to decide which operator/bracket/Add filter buttons are currently valid to press."""
    tokens = []
    for part in _OPERATOR_TOKEN_RE.split(text or ""):
        part = part.strip()
        if not part:
            continue
        tokens.append(part if part in ("(", ")", "AND", "OR", "NOT") else "ATOM")

    expecting_atom = True
    depth = 0
    for token in tokens:
        if token == "(":
            depth += 1
            expecting_atom = True
        elif token == ")":
            depth -= 1
            expecting_atom = False
        elif token in ("AND", "OR", "NOT"):
            expecting_atom = True
        else:  # ATOM
            expecting_atom = False

    return expecting_atom, max(depth, 0)


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
        Output("advanced-filter-tags", "data", allow_duplicate=True),
        Input("add-filter-btn", "n_clicks"),
        Input("add-year-filter-btn", "n_clicks"),
        Input({'type': 'filter-button', 'task': ALL, 'label': ALL}, 'n_clicks'),
        Input("clear-search-btn", "n_clicks"),
        State("active-filters", "data"),
        State("label-checklist", "value"),
        State("task-dropdown", "value"),
        State("advanced-mode", "data"),
        State("filter-text", "value"),
        State("advanced-year-from", "value"),
        State("advanced-year-to", "value"),
        prevent_initial_call=True
    )
    def modify_filter(
        _,
        __,
        remove_filter_clicks: list[int],
        clear_search_clicks: int,
        active_filters: OrderedDict[str, list[str]],
        label_checklist,
        task: str,
        advanced_mode: bool,
        current_filter_text: str,
        year_from,
        year_to,
    ):
        """Modifies the active filters based on user interactions."""
        # RadioItems (single-select, advanced mode) yields a bare value instead of a list
        if not isinstance(label_checklist, list):
            label_checklist = [label_checklist] if label_checklist else []
        # Case 1: Add/remove filters using the Add Filter button
        if ctx.triggered_id in ("add-filter-btn", "add-year-filter-btn"):
            # Advanced mode: append "Task = Label" to the manually built expression instead of
            # overwriting active_filters/rebuilding the whole search string.
            if advanced_mode:
                year_from = _coerce_year(year_from)
                year_to = _coerce_year(year_to)

                if year_from is not None and year_to is not None and int(year_from) > int(year_to):
                    year_from, year_to = year_to, year_from

                year_clauses = []
                if year_from is not None:
                    year_clauses.append(f"Year >= {int(year_from)}")
                if year_to is not None:
                    year_clauses.append(f"Year <= {int(year_to)}")

                year_token = None
                if len(year_clauses) == 2:
                    year_token = f"({year_clauses[0]} AND {year_clauses[1]})"
                elif len(year_clauses) == 1:
                    year_token = year_clauses[0]

                label = label_checklist[0] if label_checklist else None
                task_token = f"{task} = {label}" if task and label else None

                if ctx.triggered_id == "add-filter-btn":
                    token = task_token
                else:
                    token = year_token

                if token:
                    token = token.strip()
                else:
                    token = None
                if not token:
                    return no_update, no_update, no_update, no_update, no_update

                current_text = (current_filter_text or "").rstrip()
                if not current_text:
                    new_text = token
                else:
                    expecting_atom, _ = _get_expression_state(current_text)
                    connector = "" if expecting_atom else " AND"
                    new_text = f"{current_text}{connector} {token}"

                return no_update, no_update, no_update, new_text, no_update

            new_active_filters = get_active_filters_from_checklist(
                task,
                label_checklist,
                active_filters
            )

            if new_active_filters == active_filters:
                return no_update, no_update, no_update, no_update, no_update

            elif len(new_active_filters) == 1 and new_active_filters[task] == []:
                return {}, [], [], "", {}

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
                    no_update,
                )

        # Case 2: A filter button is clicked to remove a filter
        # Case 3: Clear search button clicked
        elif ctx.triggered_id == "clear-search-btn":
            return {}, [], [], "", {}

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
                no_update,
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
        Output("filter-text-error", "children", allow_duplicate=True),
        Output("active-filter-buttons", "children", allow_duplicate=True),
        Output("advanced-filter-tags", "data", allow_duplicate=True),
        Input("apply-filter-btn", "n_clicks"),
        State("filter-text", "value"),
        prevent_initial_call=True,
    )
    def apply_advanced_filter(n_clicks, query_text):
        """Parses the manually edited filter text as a boolean expression and filters studies by it."""
        try:
            ids = get_ids_from_boolean_query(query_text)
            tags = get_boolean_query_tags(query_text)
        except ValueError as e:
            return no_update, True, str(e), no_update, no_update

        # Read-only: the removable 'x' filter buttons don't map onto an arbitrary boolean expression.
        buttons = build_filter_info_buttons(tags, editable=False, map_all_labels=False)

        return ids, False, "", buttons, tags

    @app.callback(
        Output({"type": "operator-btn", "op": ALL}, "disabled"),
        Output("add-filter-btn", "disabled"),
        Output("add-year-filter-btn", "disabled"),
        Input("filter-text", "value"),
        Input("task-dropdown", "value"),
        Input("label-checklist", "value"),
        Input("advanced-year-from", "value"),
        Input("advanced-year-to", "value"),
        State({"type": "operator-btn", "op": ALL}, "id"),
        State("advanced-mode", "data"),
        prevent_initial_call=False,
    )
    def update_button_availability(filter_text, task, label_value, year_from, year_to, operator_ids, advanced_mode):
        """Enables only the operator/bracket/Add filter buttons that are syntactically valid next."""
        if not advanced_mode:
            return [False] * len(operator_ids), False, True

        year_from = _coerce_year(year_from)
        year_to = _coerce_year(year_to)

        expecting_atom, paren_depth = _get_expression_state(filter_text)
        has_task_selection = bool(task) and bool(label_value)
        has_year_selection = year_from is not None or year_to is not None

        allowed = {
            "(": expecting_atom,
            "NOT": expecting_atom,
            "AND": not expecting_atom,
            "OR": not expecting_atom,
            ")": not expecting_atom and paren_depth > 0,
        }

        operator_disabled = [not allowed[op_id["op"]] for op_id in operator_ids]
        add_filter_disabled = not has_task_selection
        add_year_filter_disabled = not has_year_selection

        return operator_disabled, add_filter_disabled, add_year_filter_disabled


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
