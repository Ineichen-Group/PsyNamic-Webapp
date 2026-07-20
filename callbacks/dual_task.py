from collections import OrderedDict

from dash import ctx, no_update
from dash.dependencies import Input, Output

from callbacks.utils import log_time
from components.layout import get_filter_buttons
from data.queries import get_all_labels
from pages.explore.dual_task import (create_bar_chart, create_pie_chart,
                                     get_dual_task_data)
from style.colors import (SECONDARY_COLOR, get_color, get_color_mapping,
                          rgb_to_hex)


def get_all_info_per_task(task: str) -> OrderedDict[str, list[str]]:
    info = OrderedDict()
    labels = get_all_labels(task)
    info[task] = labels
    return info


def get_label_color_from_click_data(click_data) -> tuple[str, str]:
    label = click_data['points'][0]['label']
    color = click_data['points'][0].get('color')
    return label, color


def register(app):
    @app.callback(
        Output("active-filters", "data", allow_duplicate=True),
        Output("active-filter-buttons", "children", allow_duplicate=True),
        Output('validation-message', 'children'),
        Output('task1-pie-graph', 'figure'),
        Output('task2-bar-graph', 'figure'),
        Output('active-infos', 'data'),
        Output('active-infos-buttons', 'children'),
        Input('jux_dropdown1', 'value'),
        Input('jux_dropdown2', 'value'),
        Input('task1-pie-graph', 'clickData'),
        prevent_initial_call=True
    )
    @log_time
    def update_dual_task_view(task1: str, task2: str, click_data):
        if 'dropdown' in ctx.triggered_id:
            if task1 == task2:
                return no_update, no_update, "Choose two different tasks.", no_update
            else:
                active_info_buttons = get_filter_buttons(task1, get_all_labels(task1)) + \
                    get_filter_buttons(task2, get_all_labels(task2))
                active_infos = OrderedDict(
                    {task1: get_all_labels(task1), task2: get_all_labels(task2)})
                task1_data, task2_data, ids, tags = get_dual_task_data(
                    task1, task2)
                pie_chart = create_pie_chart(
                    task1_data, task1, get_color_mapping(task1, get_all_labels(task1)))
                bar_chart = create_bar_chart(
                    task2_data, task2, get_color(task2, 'hex'))
                return {}, "", "", pie_chart, bar_chart, active_infos, active_info_buttons

        elif 'task1-pie-graph' in ctx.triggered_id:
            label, color = get_label_color_from_click_data(click_data)
            color_mapping = get_color_mapping(task1, get_all_labels(task1))
            task1_data, task2_data, ids, tags = get_dual_task_data(
                task1, task2, label)
            if rgb_to_hex(color) == SECONDARY_COLOR:
                hilight_color = color_mapping.get(label, '#000000')
                pie_chart = create_pie_chart(
                    task1_data, task1, color_mapping, highlight=label, highlight_color=hilight_color)
                color = hilight_color
            else:
                pie_chart = create_pie_chart(task1_data, task1, get_color_mapping(
                    task1, get_all_labels(task1)), highlight=label, highlight_color=color)
            bar_chart = create_bar_chart(task2_data, task2, color)
            active_info_buttons = get_filter_buttons(
                task2, get_all_labels(task2))
            active_filters_buttons = get_filter_buttons(task1, [label])
            active_infos = OrderedDict({task2: get_all_labels(task2)})
            active_filters = OrderedDict({task1: [label]})

            return active_filters, active_filters_buttons, "", pie_chart, bar_chart, active_infos, active_info_buttons
