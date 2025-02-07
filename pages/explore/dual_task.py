import pandas as pd
from dash import html, dcc
import dash_bootstrap_components as dbc
from plotly import express as px
from collections import defaultdict

from components.layout import filter_component, studies_display, filter_button
from data.queries import get_filtered_freq, get_all_tasks, get_ids, get_pred, get_freq, get_all_labels
from style.colors import get_color_mapping, SECONDARY_COLOR, get_color


def dual_task_graphs(df_task1: pd.DataFrame = None, df_task2: pd.DataFrame = None, task1: str = None, task2: str = None) -> html.Div:
    all_tasks = get_all_tasks()

    if task1 and task2:
        task1_col_map = get_color_mapping(task1, df_task1[task1].unique()) if df_task1 is not None else {}
        task2_color = get_color(task2, 'hex') if df_task2 is not None else None

    return html.Div([
        html.H1("Dual Task Analysis", className="my-4"),
        html.P("Select two classification tasks from dropdowns to view a pie chart (Task 1) and a bar chart (Task 2). Click on a pie segment to filter Task 2."),
        html.Div(id="validation-message", className="mt-4 text-danger"),
        dbc.Row([
            dbc.Col([
                # Add a label for the dropdown
                html.Label("Choose Task 1", className="mt-2"),
                dcc.Dropdown(all_tasks, id="jux_dropdown1", placeholder="Select a Task", value=task1 if task1 else None,style={'width': '75%'}
                             ),
                dcc.Graph(id='task1-pie-graph',
                          figure=create_pie_chart(df_task1, task1, task1_col_map) if df_task1 is not None else {}),
            ], width=6),
            dbc.Col([
                html.Label("Choose Task 2", className="mt-2"),
                dcc.Dropdown(all_tasks, id="jux_dropdown2", placeholder="Select a Task", value=task2 if task2 else None, style={'width': '75%'}),
                dcc.Graph(id='task2-bar-graph',
                          figure=create_bar_chart(df_task2, task2, task2_color) if df_task2 is not None else {}),
            ], width=6)
        ])
    ], className="container")



def create_pie_chart(df, column, col_map, highlight=None, highlight_color=None):
    fig = px.pie(df, values='Frequency', names=column, title=f'Task 1: {column}', color=column, color_discrete_map=col_map)
    if highlight:
        fig.update_traces(marker=dict(colors=[
                          highlight_color if s == highlight else SECONDARY_COLOR for s in df[column]]))
        fig.update_traces(
            pull=[0.1 if s == highlight else 0 for s in df[column]])
        
    return fig


def create_bar_chart(df, column: str, color: str):
    print(color)
    # all bars are the same color
    fig = px.bar(df, x='Frequency', y=column,
                 title=f'Task 2: {column}', orientation='h')
    fig.update_traces(marker_color=color)
    return fig


def get_dual_task_data(task1, task2, task1_label=None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:

    study_tags = defaultdict(list)
    task1_data = get_freq(task1)
    task1_col_map = get_color_mapping(task1, task1_data[task1].unique())

    if task1_label:
        task2_data = get_filtered_freq(task2, task1, task1_label)
        ids = get_ids(task1, task1_label)
        pred_task2 = get_pred(task2)
        task2_col_map = get_color_mapping(task2, task2_data[task2].unique())

        for id in ids:
            # Add label for task1
            tag_info = {
                'task': task1,
                'label': task1_label,
                'color': task1_col_map[task1_label]
            }
            study_tags[id].append(tag_info)
            # Add label for task2
            task2_label_list = pred_task2.loc[pred_task2['paper_id'] == id, 'label'].tolist(
            )
            for label in task2_label_list:
                tag_info = {
                    'task': task2,
                    'label': label,
                    'color': task2_col_map[label]
                }
                study_tags[id].append(tag_info)

        return task1_data, task2_data, study_tags

    else:
        ids = get_ids(task1)
        task1_col_map = get_color_mapping(task1, task1_data[task1].unique())

        task2_data = get_freq(task2)
        pred_task2 = get_pred(task2)
        task2_col_map = get_color_mapping(task2, task2_data[task2].unique())

        pred_task1 = get_pred(task1)
        task1_col_map = get_color_mapping(task1, task1_data[task1].unique())
        for id in ids:
            # Add label for task 1
            task1_label_list = pred_task1.loc[pred_task1['paper_id'] == id, 'label'].tolist(
            )
            for label in task1_label_list:
                tag_info = {
                    'task': task1,
                    'label': label,
                    'color': task1_col_map[label]
                }
                study_tags[id].append(tag_info)

            # Add label for task 2
            task2_label_list = pred_task2.loc[pred_task2['paper_id'] == id, 'label'].tolist(
            )
            for label in task2_label_list:
                tag_info = {
                    'task': task2,
                    'label': label,
                    'color': task2_col_map[label]
                }
                study_tags[id].append(tag_info)

    return task1_data, task2_data, study_tags


def dual_task_layout(task1, task2, task1_label=None):
    # if neither task1 or task2 is selected, return the default layout
    if not task1 and not task2:
        return dual_task_graphs(), filter_component([]), studies_display()

    if task1_label:
        df_task1, df_task2, study_tags = get_dual_task_data(
            task1, task2, task1_label)
        labels_task1 = get_all_labels(task1)
        task1_col_map = get_color_mapping(task1, labels_task1)
        filter_buttons = [filter_button(
            task1_col_map[task1_label], task1, task1_label)]
    else:
        df_task1, df_task2, study_tags = get_dual_task_data(task1, task2)
        filter_buttons = []
    graph = dual_task_graphs(df_task1, df_task2, task1, task2)
    return graph, filter_component(filter_buttons), studies_display(study_tags)
