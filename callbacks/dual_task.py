from collections import OrderedDict

from dash import ctx, no_update
from dash.dependencies import Input, Output

from callbacks.utils import log_time
from components.layout import build_filter_info_buttons
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
        Input({"type": "include-study-protocol-toggle", "index": "dual-task"}, 'value'),
        prevent_initial_call=True
    )
    @log_time
    def update_dual_task_view(task1: str, task2: str, click_data, include_study_protocol_toggle):
        include_study_protocols = "include" in (include_study_protocol_toggle or [])
        trigger = ctx.triggered_id
        is_toggle_trigger = isinstance(trigger, dict) and trigger.get("type") == "include-study-protocol-toggle"

        if isinstance(trigger, str) and 'dropdown' in trigger:
            if task1 == task2:
                return no_update, no_update, "Choose two different tasks.", no_update, no_update, no_update, no_update
            else:
                labels_task1 = get_all_labels(task1)
                labels_task2 = get_all_labels(task2)

                active_infos = OrderedDict({task1: labels_task1, task2: labels_task2})
                active_filter_buttons = build_filter_info_buttons(active_infos, editable=False, map_all_labels=True)
                task1_data, task2_data, ids, tags = get_dual_task_data(
                    task1,
                    task2,
                    include_study_protocols=include_study_protocols,
                )
                pie_chart = create_pie_chart(
                    task1_data, task1, get_color_mapping(task1, get_all_labels(task1)))
                bar_chart = create_bar_chart(
                    task2_data, task2, get_color(task2, 'hex'))
                return {}, "", "", pie_chart, bar_chart, active_infos, active_filter_buttons

        elif isinstance(trigger, str) and 'task1-pie-graph' in trigger:
            label, color = get_label_color_from_click_data(click_data)
            color_mapping = get_color_mapping(task1, get_all_labels(task1))
            task1_data, task2_data, ids, tags = get_dual_task_data(
                task1,
                task2,
                label,
                include_study_protocols=include_study_protocols,
            )
            if rgb_to_hex(color) == SECONDARY_COLOR:
                hilight_color = color_mapping.get(label, '#000000')
                pie_chart = create_pie_chart(
                    task1_data, task1, color_mapping, highlight=label, highlight_color=hilight_color)
                color = hilight_color
            else:
                pie_chart = create_pie_chart(task1_data, task1, get_color_mapping(
                    task1, get_all_labels(task1)), highlight=label, highlight_color=color)
                
            labels_task2 = get_all_labels(task2)
            active_infos = OrderedDict({task2: labels_task2})
            active_info_buttons = build_filter_info_buttons(
                active_infos, editable=False, map_all_labels=True)
            active_filters = OrderedDict({task1: [label]})
            active_filters_buttons = build_filter_info_buttons(
                active_filters, editable=False, map_all_labels=True)  
            bar_chart = create_bar_chart(task2_data, task2, color)
            return active_filters, active_filters_buttons, "", pie_chart, bar_chart, active_infos, active_info_buttons

        elif is_toggle_trigger and task1 and task2:
            task1_data, task2_data, ids, _ = get_dual_task_data(
                task1,
                task2,
                include_study_protocols=include_study_protocols,
            )
            active_infos = OrderedDict({task1: get_all_labels(task1), task2: get_all_labels(task2)})
            active_info_buttons = build_filter_info_buttons(active_infos, editable=False, map_all_labels=True)
            pie_chart = create_pie_chart(
                task1_data, task1, get_color_mapping(task1, get_all_labels(task1))
            )
            bar_chart = create_bar_chart(task2_data, task2, get_color(task2, 'hex'))
            return {}, "", "", pie_chart, bar_chart, active_infos, active_info_buttons

        return no_update, no_update, no_update, no_update, no_update, no_update, no_update
