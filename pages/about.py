from dash import html


def about_layout():
    return html.Div([
        html.H1('About PsyNamic!'),
        html.P('Coming soon...'),
        # add image
        html.Img(src="assets/pipeline.png", style={'width': '80%'}),
    ],)
