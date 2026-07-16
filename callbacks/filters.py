
import json

import dash_bootstrap_components as dbc
from dash import ALL, callback_context, html, no_update
from dash.dependencies import Input, Output, State

from callbacks.utils import log_time
from components.layout import filter_button, get_tags
from data.queries import get_all_labels, get_filtered_study_ids


def register(app):

    @app.callback(
        Output("checkbox-container", "children"),
        Input("task-dropdown", "value"),
        State("filter-store", "data"),
        prevent_initial_call=False,
    )
    def update_checkboxes(selected_task, current_filters):
        if not selected_task:
            return ""

        current_filters = current_filters or {}
        # Fetch labels at runtime to avoid relying on module-level cached `filter_data`
        labels = get_all_labels(selected_task)
        checked_labels = current_filters.get(selected_task, [])

        return dbc.Checklist(
            options=[{"label": label, "value": label} for label in labels],
            id="label-checklist",
            inline=True,
            value=checked_labels,
        )

    @app.callback(
        Output("selected-filters", "children"),
        Output("filter-store", "data"),
        Output("filtered-study-ids", "data"),
        Output("filter-tags", "data"),
        Output("label-checklist", "value"),
        Input("add-filter-btn", "n_clicks"),
        Input({'type': 'filter-button', 'task': ALL, 'label': ALL}, 'n_clicks'),
        State("task-dropdown", "value"),
        State("label-checklist", "value"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    @log_time
    def modify_filter(add_clicks, remove_clicks, selected_task, selected_labels, current_filters):

        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update, no_update

        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        current_filters = (current_filters or {}).copy()

        # -----------------------------
        # ADD FILTER
        # -----------------------------
        if triggered_id == "add-filter-btn":
            if not selected_task or not selected_labels:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    selected_labels,
                )

            current_filters[selected_task] = selected_labels

        # -----------------------------
        # REMOVE FILTER
        # -----------------------------
        else:
            button_data = json.loads(triggered_id)
            task = button_data['task']
            label = button_data['label']

            if task in current_filters and label in current_filters[task]:
                current_filters[task].remove(label)
                if not current_filters[task]:
                    del current_filters[task]

            selected_labels = [
                l for l in (selected_labels or [])
                if l != label
            ]

        # -----------------------------
        # Rebuild UI + IDs
        # -----------------------------
        ordered_tags = get_tags(current_filters)

        filter_buttons = [
            filter_button(tag['color'], tag['label'],
                          tag['task'], editable=True)
            for task in ordered_tags
            for tag in ordered_tags[task]
        ]

        filtered_ids = get_filtered_study_ids(current_filters)

        return (
            filter_buttons,
            current_filters,
            filtered_ids,
            current_filters,
            selected_labels,
        )
