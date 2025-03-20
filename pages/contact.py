from dash import html
import dash_bootstrap_components as dbc

def contact_layout():
    return html.Div([
        dbc.Container([
            html.H1('Contact Us', className='my-4'),
            html.P('You can reach us at the following contacts:', className='mb-5'),

            dbc.Row([
                dbc.Col(html.H3('Principal Investigator', className='mb-3'), width=12),
                dbc.Col(html.P('Benjamin Ineichen', className='h5'), width=12),
                dbc.Col([
                    html.P([
                        'Email: ',
                        html.A('benjamin.ineichen@uzh.ch',
                               href='mailto:benjamin.ineichen@uzh.ch', className='text-primary')
                    ], className='mb-2'),
                    html.P(
                        html.A('More about Benjamin Ineichen', href='https://stride-lab.pages.uzh.ch/website/people/ineichen-benjamin-victor/',
                               target='_blank', className='text-secondary')
                    ),
                ], width=12),
            ], className='mb-5'),

            dbc.Row([
                dbc.Col(html.H3('Developer', className='mb-3'), width=12),
                dbc.Col(html.P('Vera Bernhard', className='h5'), width=12),
                dbc.Col([
                    html.P([
                        'Email: ',
                        html.A('veralara.bernhard@uzh.ch',
                               href='mailto:veralara.bernhard@uzh.ch', className='text-primary')
                    ], className='mb-2'),
                    html.P(
                        html.A('More about Vera Bernhard', href='https://stride-lab.pages.uzh.ch/website/people/bernhard-vera/',
                               target='_blank', className='text-secondary')
                    ),
                ], width=12),
            ], className='mb-5'),

            dbc.Row([
                dbc.Col(html.H3('Visit our lab', className='mb-3'), width=12),
                dbc.Col([
                    html.P(
                        html.A('Click here to visit the STRIDE Lab website',
                               href='https://stride-lab.pages.uzh.ch/website/', 
                               target='_blank', className='text-primary')
                    ),
                ], width=12),
            ], className='mt-5'),
        ])
    ])
