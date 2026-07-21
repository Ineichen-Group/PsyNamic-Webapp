from collections import OrderedDict

import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html
from plotly import express as px

from components.graphs import add_interaction_annotation
from components.layout import filter_info_button, studies_display
from data.queries import (get_all_labels, get_all_tasks, get_filtered_freq,
                          get_freq, get_ids)
from style.colors import SECONDARY_COLOR, get_color, get_color_mapping


def dual_task_graphs(df_task1: pd.DataFrame = None, df_task2: pd.DataFrame = None, task1: str = None, task2: str = None) -> html.Div:
    all_tasks = get_all_tasks()

    if task1 and task2:
        task_1_labels = get_all_labels(task1)
        task1_col_map = get_color_mapping(
            task1, task_1_labels) if df_task1 is not None else {}
        task2_color = get_color(task2, 'hex') if df_task2 is not None else None

    return html.Div([
        html.H1("Dual Task Analysis", className="my-4"),
        html.P("Select two classification tasks from dropdowns to view a pie chart (Task 1) and a bar chart (Task 2). Click on a pie segment to filter Task 2."),
        html.Div(id="validation-message", className="mt-4 text-danger"),
        dbc.Row([
            dbc.Col([
                # Add a label for the dropdown
                html.Label("Choose Task 1", className="mt-2"),
                dcc.Dropdown(all_tasks, id="jux_dropdown1", placeholder="Select a Task", value=task1 if task1 else None, style={'width': '75%'}
                             ),
                dcc.Graph(id='task1-pie-graph',
                          figure=create_pie_chart(df_task1, task1, task1_col_map) if df_task1 is not None else {}),
            ], width=6),
            dbc.Col([
                html.Label("Choose Task 2", className="mt-2"),
                dcc.Dropdown(all_tasks, id="jux_dropdown2", placeholder="Select a Task",
                             value=task2 if task2 else None, style={'width': '75%'}),
                dcc.Graph(id='task2-bar-graph',
                          figure=create_bar_chart(df_task2, task2, task2_color) if df_task2 is not None else {}),
            ], width=6)
        ])
    ], className="container", id="dual-task-graph")


def create_pie_chart(df: pd.DataFrame, column: str, col_map: dict, highlight: str = None, highlight_color: str = None) -> px.pie:
    fig = px.pie(
        df,
        values='Frequency',
        names=column,
        title=f'Task 1: {column}',
        color=column,
        color_discrete_map=col_map
    )

    if highlight is not None:
        fig.update_traces(
            marker=dict(
                colors=[
                    highlight_color if s == highlight else SECONDARY_COLOR
                    for s in df[column]
                ]
            ),
            pull=[
                0.1 if s == highlight else 0
                for s in df[column]
            ]
        )
    else:
        # Reset to original colors
        fig.update_traces(
            marker=dict(
                colors=[
                    col_map[s]
                    for s in df[column]
                ]
            ),
            pull=[
                0
                for _ in df[column]
            ]
        )

    add_interaction_annotation(fig, x=0.75, y=0.80)

    return fig


def create_bar_chart(df: pd.DataFrame, column: str, color: str) -> px.bar:
    fig = px.bar(df, x='Frequency', y=column,
                 title=f'Task 2: {column}', orientation='h')
    fig.update_traces(marker_color=color)
    return fig


def get_dual_task_data(task1: str, task2: str, task1_label: str = None) -> tuple[pd.DataFrame, pd.DataFrame, list[int], dict]:
    task1_data = get_freq(task1)

    if task1_label:
        task2_data = get_filtered_freq(task2, task1, task1_label)
        ids = get_ids(task1, task1_label)

        tags = OrderedDict()
        tags[task1] = [task1_label]
        tags[task2] = task2_data[task2].unique().tolist()

        return task1_data, task2_data, ids, tags

    else:
        ids = get_ids(task1)
        task2_data = get_freq(task2)

        tags = OrderedDict()
        tags[task1] = task1_data[task1].unique().tolist()
        tags[task2] = task2_data[task2].unique().tolist()
    return task1_data, task2_data, ids, tags


def dual_task_layout(task1=None, task2=None, task1_label=None):
    active_filters = OrderedDict()
    active_infos = OrderedDict()
    if task1_label:
        df_task1, df_task2, ids, tags = get_dual_task_data(
            task1, task2, task1_label)
        active_filters = OrderedDict({task1: [task1_label]})
        active_infos = OrderedDict({task2: get_all_labels(task2)})
        # buttons = get_dual_filters(task1, task1_label)
        # active_infos = get_filter_buttons(task2, )

    else:
        df_task1, df_task2, ids, _ = get_dual_task_data(task1, task2)
        active_infos = OrderedDict(
            {task1: get_all_labels(task1), task2: get_all_labels(task2)})

    graph = dual_task_graphs(df_task1, df_task2, task1, task2)
    return [
        graph,
        studies_display(page_key='dual-task', ids=ids,
                        filters=active_filters, infos=active_infos),
        # html.H4("Filtered Studies"),
        # filter_component(buttons, info_buttons, id='active-filter-buttons'),
        # dcc.Store(
        #     id="filtered-study-ids",
        #     data=get_ids(),
        #     storage_type="memory"
        # ),
        # study_grid(
        #     nr_studies(),
        #     len(ids),
        #     last_update=latest_update(),
        # )
    ]


def get_dual_filters(task1: str = None, task1_label: str = None) -> html.Div:
    if not task1_label:
        return []
    labels_task1 = get_all_labels(task1)
    task1_col_map = get_color_mapping(task1, labels_task1)
    button = filter_info_button(
        task1_col_map[task1_label], task1_label, task1)
    return [button]
