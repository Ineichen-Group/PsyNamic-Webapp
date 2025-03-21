from dash import html
import dash_bootstrap_components as dbc
import random



def home_layout():
    insight_views = [
    ("Evidence Strength", "/insights/evidence-strength", "Assessing evidence strength: How many Randomized Controlled Trials (RCTs) and Systematic Reviews are there per substance?"),
    ("Efficacy & Safety", "/insights/efficacy-safety", "Effectiveness and safety: Is there enough studies measuring efficacy and safety endpoints per substance?"),
    ("Long-term Effects", "/insights/long-term", "Do we have enough longitudinal studies and cross-sectional studies for each substance?"),
    ("Sex Bias", "/insights/sex-bias", "Is there sex bias per substance?"),
    ("Study Participation", "/insights/participants", "Study Participation: How many participants are included per study?"),
    ("Study Protocols", "/insights/study-protocol", "How many study protocols are available?"),
    ("Dosages", "/insights/dosage", "Inspecting dosage: How are different substances dosed?")
    ]

    random_insights = random.sample(insight_views, 3)
    insight_cards = [
        dbc.Col([
            html.A(
                dbc.Card([
                    dbc.CardBody([
                        html.H5(title, className='card-title'),
                        html.P(description, style={'font-size': '16px'}),
                    ]),
                ], color="light", outline=True, className='mb-4 card-hover'),
                href=link,
            ),
        ], width=12, md=4) for title, link, description in random_insights
    ]



    return html.Div([
        html.Div([
            html.H1(['Welcome to ', html.B('PsyNamic')]),
            html.H1(),
        ]),
        html.H3('A Living Systematic Review of Psychedelic Therapy in Psychiatric Disorders', style={
                'margin-bottom': '30px'}),
        # html.Img(src="assets/pipeline.png",
        #          style={'width': '80%', 'margin-bottom': '30px', 'display': 'block'}),
        dbc.Row([
            dbc.Col([
                html.Img(src="assets/paper.png",
                         style={'height': '5em', 'margin-bottom': '10px'}),
                html.H4('Automated Research Retrieval'),
                html.P("3,335 studies retrieved and updated in real-time (last update: 01.01.2024).", style={
                       'font-size': '16px'}),
            ], width=12, md=4, className='text-center mb-4'),

            dbc.Col([
                html.Img(src="assets/ai_automation_with_cog.png",
                         style={'height': '5em', 'margin-bottom': '10px'}),
                html.H4('AI-Powered Insights'),
                html.P('Specialized language models filter for relevant publications and extract information such as study type, condition, substance, and more.',
                       style={'font-size': '16px'}),
            ], width=12, md=4, className='text-center mb-4'),

            dbc.Col([
                html.Img(src="assets/light_bulb.png",
                         style={'height': '5em', 'margin-bottom': '10px'}),
                html.H4('Evidence Synthesis'),
                html.P('An overview of the latest research on psychedelic therapy, streamlining reviews and accelerating evidence synthesis.', style={
                       'font-size': '16px'}),
            ], width=12, md=4, className='text-center mb-4'),

        ], className='mb-2'),

        html.Div([
            html.H4("Let's Get Started..."),
            html.P('Get insights into, for example:', style={
                   'font-size': '16px', })
        ]),

        dbc.Row(insight_cards),
        
        html.Div([
            html.P('Or explore the data:', style={
                'font-size': '16px'})
        ]),

                dbc.Row([
            dbc.Col([
                html.A(
                    dbc.Card([
                        dbc.CardBody([
                            html.H5('Dual Task',
                                    className='card-title'),
                            html.P('Juxtapose two information categories.')
                        ]),
                    ], color="light", outline=True, className='mb-4 card-hover', ),
                    href='/explore/dual-task',
                ),
            ], width=12, md=4),

            dbc.Col([
                html.A(
                    dbc.Card([
                        dbc.CardBody([
                            html.H5('Time',
                                    className='card-title'),
                            html.P('Visualize the distribution of studies over time.')
                        ]),
                    ], color="light", outline=True, className='mb-4 card-hover',),
                    href='/explore/time',
                ),
            ], width=12, md=4),

        ], className='mb-2'),
])