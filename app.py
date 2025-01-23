import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, State

from pages.about import about_layout
from pages.contact import contact_layout
from pages.home import home_layout
from pages.explore.dual_task import dual_task_graphs
from pages.explore.time import time_graph, get_time_data
from pages.insights.views import rct_view, efficacy_safety_view

from components.layout import header_layout, footer_layout, search_filter_component, studies_display, content_layout
from callbacks import register_callbacks

# Load data
frequency_df = get_time_data()

# Initialize the Dash app with suppress_callback_exceptions=True
app = dash.Dash(__name__, external_stylesheets=[
                dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME], suppress_callback_exceptions=True)

app.layout = html.Div([
    header_layout(),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content', className='mx-5 my-2'),
    footer_layout()
])


@app.callback(dash.Output('page-content', 'children'),
              [dash.Input('url', 'pathname')])
def display_page(pathname: str):
    if pathname == '/about':
        return about_layout()
    elif pathname == '/contact':
        return contact_layout()
    elif pathname.startswith('/explore'):
        filtered_display = studies_display()
        search_filter = search_filter_component()
        if pathname == '/explore/time':
            return content_layout([time_graph(), search_filter, filtered_display])
        elif pathname == '/explore/dual-task':
            return content_layout([dual_task_graphs(), search_filter, filtered_display])
        else:
            return content_layout([home_layout(), search_filter, filtered_display])
    elif pathname.startswith('/insights'):
        if pathname == '/insights/rct':
            return content_layout([rct_view()])
        elif pathname == '/insights/efficacy-safety':
            return content_layout([efficacy_safety_view()])
        
# Register all callbacks and pass data
register_callbacks(app, {'frequency_df': frequency_df})


if __name__ == '__main__':
    app.run_server(debug=True)
