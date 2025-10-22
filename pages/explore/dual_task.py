from collections import OrderedDict
import pandas as pd
from dash import html, dcc
import dash_bootstrap_components as dbc
from plotly import express as px

from components.layout import filter_component, filter_button, study_grid
from data.queries import (
    get_filtered_freq,
    get_all_tasks,
    get_ids,
    get_freq,
    get_all_labels,
    nr_studies,
)
from style.colors import get_color_mapping, SECONDARY_COLOR, get_color


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


def create_pie_chart(df, column, col_map, highlight=None, highlight_color=None):
    fig = px.pie(df, values='Frequency', names=column,
                 title=f'Task 1: {column}', color=column, color_discrete_map=col_map)
    if highlight:
        fig.update_traces(marker=dict(colors=[
                          highlight_color if s == highlight else SECONDARY_COLOR for s in df[column]]))
        fig.update_traces(
            pull=[0.1 if s == highlight else 0 for s in df[column]])

    return fig


def create_bar_chart(df, column: str, color: str):
    fig = px.bar(df, x='Frequency', y=column,
                 title=f'Task 2: {column}', orientation='h')
    fig.update_traces(marker_color=color)
    return fig


def get_dual_task_data(task1, task2, task1_label=None) -> tuple[pd.DataFrame, pd.DataFrame, list[int], dict]:
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
    if task1_label:
        df_task1, df_task2, ids, tags = get_dual_task_data(
            task1, task2, task1_label)
        buttons = get_dual_filters(task1, task1_label)

    else:
        df_task1, df_task2, ids, tags = get_dual_task_data(task1, task2)
        buttons = []

    graph = dual_task_graphs(df_task1, df_task2, task1, task2)
    return graph, html.H4("Filtered Studies"), filter_component(buttons), dual_study_grid(ids, tags)


def dual_study_grid(ids: list[int], tags: OrderedDict) -> html.Div:
    return html.Div([
        dcc.Store(id='filtered-study-ids', data=ids, storage_type='session'),
        dcc.Store(id='filter-tags', data=tags, storage_type='session'),
        study_grid(nr_studies(), len(ids), 'January 2024', tags, id={"type": "studies-grid", "index": 6})
    ], id='dual-study-grid')


def get_dual_filters(task1: str = None, task1_label: str = None) -> html.Div:
    if not task1_label:
        return []
    labels_task1 = get_all_labels(task1)
    task1_col_map = get_color_mapping(task1, labels_task1)
    button = filter_button(
        task1_col_map[task1_label], task1_label, task1)
    return [button]
