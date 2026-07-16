from dash import callback_context, html, no_update
from dash.dependencies import Input, Output

from data.queries import get_all_labels
from pages.explore.dual_task import (create_bar_chart, create_pie_chart,
                                     dual_study_grid, dual_task_graphs,
                                     get_dual_filters, get_dual_task_data)
from style.colors import (SECONDARY_COLOR, get_color, get_color_mapping,
                          rgb_to_hex)
from callbacks.utils import log_time
from components.layout import get_filter_buttons


def register(app):
    # Split behavior into two callbacks for clarity and to avoid overlapping
    # triggered logic: one handles dropdown changes and renders the full
    # dual-task graph; the other handles pie-segment clicks and updates the
    # pie/bar figures + filters/grid.
    @app.callback(
        [
            Output('validation-message', 'children'),
            Output('dual-task-graph', 'children'),
            Output('task1-pie-graph', 'figure'),
            Output('task2-bar-graph', 'figure'),
            Output('active-filters', 'children'),
            Output('info-buttons', 'children'),
            Output('dual-study-grid', 'children'),
        ],
        [
            Input('jux_dropdown1', 'value'),
            Input('jux_dropdown2', 'value'),
            Input('task1-pie-graph', 'clickData'),
        ],
        prevent_initial_call=True,
    )
    @log_time
    def update_dual_task_view(dropdown1_value, dropdown2_value, click_data):
        ctx = callback_context
        triggered = (ctx.triggered[0]['prop_id'].split(
            '.')[0]) if ctx.triggered else None

        if dropdown1_value and dropdown2_value and dropdown1_value == dropdown2_value:
            return "Choose two different tasks.", no_update, no_update, no_update, no_update, no_update, no_update

        # If a pie segment was clicked, handle that interaction
        if triggered == 'task1-pie-graph':
            if not click_data:
                return no_update, no_update, no_update, no_update, no_update, no_update, no_update

            if not dropdown1_value or not dropdown2_value:
                return "Choose two tasks first.", no_update, no_update, no_update, no_update, no_update, no_update

            label = click_data['points'][0]['label']
            color = click_data['points'][0].get('color')

            task1_data, task2_data, ids, tags = get_dual_task_data(
                dropdown1_value, dropdown2_value, label)

            task1_all_labels = get_all_labels(dropdown1_value)
            col_map = get_color_mapping(dropdown1_value, task1_all_labels)

            if color and rgb_to_hex(color) == SECONDARY_COLOR:
                color = col_map.get(label, '#000000')

            pie_chart = create_pie_chart(
                task1_data, dropdown1_value, col_map, highlight=label, highlight_color=color)
            bar_chart = create_bar_chart(task2_data, dropdown2_value, color)

            filters = get_dual_filters(dropdown1_value, label)
            grid = dual_study_grid(ids, tags)
            info_buttons = get_filter_buttons(
                dropdown2_value, get_all_labels(dropdown2_value))
            return "", no_update, pie_chart, bar_chart, filters, info_buttons, grid

        if not dropdown1_value or not dropdown2_value:
            return "", html.Div(), no_update, no_update, no_update, no_update, no_update

        # Build the combined dual-task graph and fresh figures (clears previous highlights)
        df_task1, df_task2, ids, tags = get_dual_task_data(
            dropdown1_value, dropdown2_value)
        graph = dual_task_graphs(
            df_task1, df_task2, dropdown1_value, dropdown2_value)

        task1_all_labels = get_all_labels(dropdown1_value)
        col_map = get_color_mapping(
            dropdown1_value, task1_all_labels) if df_task1 is not None else {}
        pie_fig = create_pie_chart(
            df_task1, dropdown1_value, col_map) if df_task1 is not None else {}
        bar_color = get_color(
            dropdown2_value, 'hex') if dropdown2_value else None
        bar_fig = create_bar_chart(
            df_task2, dropdown2_value, bar_color) if df_task2 is not None else {}

        # Clear active filters when switching tasks
        filters = []
        grid = dual_study_grid(ids, tags)
        info_buttons = get_filter_buttons(dropdown1_value, get_all_labels(dropdown1_value)) + \
            get_filter_buttons(
                dropdown2_value, get_all_labels(dropdown2_value))
        return "", graph, pie_fig, bar_fig, filters, info_buttons, grid
