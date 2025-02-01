from data.prepare_data import PREDICTIONS
import pandas as pd
from dash import html, dcc
from plotly import express as px
import dash_bootstrap_components as dbc
from components.graphs import dropdown
from components.layout import filter_component, studies_display, filter_button
from data.queries import get_filtered_freq, get_all_tasks, get_ids, get_pred
from collections import defaultdict
from style.colors import get_color_mapping, rgb_to_hex, SECONDARY_COLOR


def dual_task_graphs(df_task1: pd.DataFrame, df_task2: pd.DataFrame) -> html.Div:
    default_task1, default_task2 = 'Substances', 'Condition'
    dropdown1_id, dropdown2_id, message_id = "jux_dropdown1", "jux_dropdown2", "validation-message"
    all_tasks = get_all_tasks()
    
    task1_all_labels = df_task1[default_task1].unique()
    col_map = get_color_mapping(default_task1, task1_all_labels)
    
    return html.Div([
        html.H1("Dual Task Analysis", className="my-4"),
        html.P("Select two classification tasks from dropdowns to view a pie chart (Task 1) and a bar chart (Task 2). Click on a pie segment to filter Task 2."),
        html.Div(id=message_id, className="mt-4 text-danger"),
        dbc.Row([
            dbc.Col([
                dropdown(all_tasks, identifier=dropdown1_id, default=default_task1, label="Select a Task", width="50%"),
                dcc.Graph(id='task1-pie-graph', figure=create_pie_chart(df_task1, default_task1, col_map)),
            ], width=6),
            dbc.Col([
                dropdown(all_tasks, identifier=dropdown2_id, default=default_task2, label="Select a Task", width="50%"),
                dcc.Graph(id='task2-bar-graph', figure=create_bar_chart(df_task2, default_task2, None)),
            ], width=6)
        ]),
    ], className="container")


def create_pie_chart(df, column, col_map, highlight=None, highlight_color=None):
    fig = px.pie(df, values='Frequency', names=column, title=f'Task 1: {column}', color=column, color_discrete_map=col_map)
    if highlight:
        fig.update_traces(marker=dict(colors=[highlight_color if s == highlight else SECONDARY_COLOR for s in df[column]]))
        fig.update_traces(pull=[0.1 if s == highlight else 0 for s in df[column]])
    return fig


def create_bar_chart(df, column, color):
    return px.bar(df, x='Frequency', y=column, title=f'Task 2: {column}', orientation='h', color_discrete_sequence=[color] if color else None)


def get_dual_task_data(task1, task2, task1_label=None):
    task1_data = get_filtered_freq(task1)
    ids = get_ids(task1)
    study_tags = defaultdict(list)

    if task1_label:
        task2_data = get_filtered_freq(task2, task1, task1_label)
        for id in get_ids(task1, task1_label):
            study_tags[id].append({'task': task1, 'label': task1_label, 'color': '#A020F0'})
    else:
        task2_data = get_filtered_freq(task2)
        pred = get_pred(task2)
        for id in ids:
            label_list = pred.loc[pred['paper_id'] == id, 'label'].tolist()
            study_tags[id].extend({'task': task2, 'label': label, 'color': '#A020F0'} for label in label_list)

    return task1_data, task2_data, study_tags


def dual_task_layout():
    df_task1, df_task2, study_tags = get_dual_task_data('Substances', 'Condition')
    graph = dual_task_graphs(df_task1, df_task2)
    filter_buttons = [filter_button('primary', 'Substances', 'Task 1')]
    return graph, filter_component(filter_buttons), studies_display(study_tags)
