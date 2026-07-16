from dash import ALL, callback_context
from dash.dependencies import Input, Output, State


def register(app):

    @app.callback(
        Output({'type': 'collapse', 'index': ALL}, 'is_open'),
        Input({'type': 'collapse-button', 'index': ALL}, 'n_clicks'),
        State({'type': 'collapse', 'index': ALL}, 'is_open'),
    )
    def toggle_collapse(n_clicks_list, is_open_list):
        ctx = callback_context

        if not ctx.triggered:
            return is_open_list

        button_id = ctx.triggered_id
        index = int(button_id.split('{"index":')[1].split(',')[0])

        new_is_open_list = [False] * len(is_open_list)
        new_is_open_list[index] = not is_open_list[index]

        return new_is_open_list


