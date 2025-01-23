from dash import html, dcc
import dash_bootstrap_components as dbc

# import study_view
from style.colors import get_color_mapping
from components.layout import search_filter_component, studies_display, filter_button
from components.graphs import bar_chart
from data.queries import get_freq

def explore_layout(title: str, graph: dcc.Graph, filters: dict, filter_buttons: list[dbc.Button]) -> html.Div:
    return html.Div([
        html.H1(f'{title}', className="my-4"),
        graph,
        search_filter_component(filter_buttons),
        studies_display()
    ])

def rct_view():
    title = "How many RCTs and non-RCTs are there per substance?"
    # add bar chart with placeholder data
    # data = {
    #     'Substance': ['Substance A', 'Substance B', 'Substance C'],
    #     'Count': [10, 20, 30]
    # }

    data_rct = get_freq('Study Type', 'Study Type', filter_task_label='Randomized-controlled trial (RCT)')
    print(data_rct)

    # graph = bar_chart(data, 'Substance', 'Count', title, 'Substance', 'Count')

    # filters = {
    #     "Study Type": ["Randomized-controlled trial (RCT)", "Systematic review/meta-analysis"]
    # }
    # filter_buttons = []
    # for key, values in filters.items():
    #     color_mapping = get_color_mapping(key, values)
    #     for v in values:
    #         filter_buttons.append(filter_button(color_mapping[v], v, key, False))

    # return explore_layout(title, graph, filters, filter_buttons)

def efficacy_safety_view():
    pass

def longitudinal_view():
    pass

