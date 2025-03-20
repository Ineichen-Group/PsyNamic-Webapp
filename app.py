import dash
import dash_bootstrap_components as dbc
import os
from dash import html, dcc, State

from pages.about import about_layout
from pages.contact import contact_layout
from pages.home import home_layout
from pages.explore.dual_task import dual_task_layout
from pages.explore.time import time_layout
from pages.insights.views import rct_view, efficacy_safety_view, longitudinal_view, sex_bias_view, nr_part_view, study_protocol_view, dosages_view

from components.layout import header_layout, footer_layout, filter_component, studies_display, content_layout
from callbacks import register_callbacks

from sqlalchemy import create_engine
from settings import DATABASE_URL

# Initialize the Database Connection
engine = create_engine(DATABASE_URL)

# Function to check database connection
def test_database_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 'Database Connected!'")
            print(result.fetchone()[0])  # Should print "Database Connected!"
    except Exception as e:
        print("Database Connection Failed:", e)

test_database_connection()  # Test connection

# Dash App Initialization
app = dash.Dash(__name__, external_stylesheets=[
                dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME], suppress_callback_exceptions=True)
server = app.server

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
        search_filter = filter_component()  
        if pathname == '/explore/time':
            return content_layout(time_layout())
        elif pathname == '/explore/dual-task':
            return content_layout(dual_task_layout('Substances', 'Condition'), id='dual-task-layout')
        else:
            return content_layout([home_layout(), search_filter, filtered_display])
    elif pathname.startswith('/insights'):
        if pathname == '/insights/evidence-strength':
            return content_layout([rct_view()])
        elif pathname == '/insights/efficacy-safety':
            return content_layout([efficacy_safety_view()])
        elif pathname == '/insights/long-term':
            return content_layout([longitudinal_view()])
        elif pathname == '/insights/sex-bias':
            return content_layout([sex_bias_view()])
        elif pathname == '/insights/participants':
            return content_layout([nr_part_view()])
        elif pathname == '/insights/study-protocol':
            return content_layout([study_protocol_view()])
        elif pathname == '/insights/dosage':
            return content_layout([dosages_view()])

register_callbacks(app)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8050))
    app.run_server(debug=True, host='0.0.0.0', port=port)