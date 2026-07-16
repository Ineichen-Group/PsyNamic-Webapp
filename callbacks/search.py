import dash_bootstrap_components as dbc
from dash import ALL, callback_context, html, no_update
from dash.dependencies import Input, Output, State

from callbacks.utils import log_time
from components.layout import build_paper_details, build_tag_buttons
from data.queries import (get_all_labels, get_all_tasks, get_studies_details,
                          get_study_tags, search_papers)


def register(app):
    """Register callbacks for the explore/search page."""

    hidden_results_style = {
        'display': 'none',
        'maxHeight': '400px',
        'overflowY': 'auto',
        'border': '1px solid #ced4da',
        'padding': '0.5rem',
        'borderRadius': '0.25rem',
        'backgroundColor': '#fff'
    }

    visible_results_style = {**hidden_results_style, 'display': 'block'}

    @app.callback(
        Output('search-results', 'children', allow_duplicate=True),
        Output('search-results', 'style', allow_duplicate=True),
        Output('search-paper-details', 'children', allow_duplicate=True),
        Output('last-search-store', 'data', allow_duplicate=True),
        Input('search-button', 'n_clicks'),
        State('search-input', 'value'),
        prevent_initial_call='initial_duplicate',
    )
    @log_time
    def perform_search(n_clicks, query):
        if not query:
            return "", hidden_results_style, html.Div("Please enter a search term."), None

        studies = search_papers(query, start_row=0, end_row=50)

        if not studies:
            return html.Div("No matching papers found."), hidden_results_style, "", None

        items = []
        for s in studies:
            year = s.get('year') or ''
            subtitle = f"{s.get('pubmed_id') or s.get('doi') or ''} {year}"
            items.append(
                dbc.ListGroupItem([
                    html.Div(s.get('title'), className='fw-bold'),
                    html.Div(subtitle, className='text-muted small')
                ], id={'type': 'search-result', 'id': s['id']}, action=True)
            )

        # Clear any existing details until a paper is clicked; store results
        return dbc.ListGroup(items), visible_results_style, "", studies

    @app.callback(
        Output({'type': 'search-result', 'id': ALL},
               'active', allow_duplicate=True),
        Output('search-paper-details', 'children', allow_duplicate=True),
        Output('url', 'search', allow_duplicate=True),
        Output('search-results', 'children', allow_duplicate=True),
        Output('search-results', 'style', allow_duplicate=True),
        Input({'type': 'search-result', 'id': ALL}, 'n_clicks'),
        State({'type': 'search-result', 'id': ALL}, 'id'),
        prevent_initial_call=True,
    )
    @log_time
    def show_search_paper(n_clicks_list, ids_list):
        active_no_update = [no_update] * len(ids_list)
        ctx = callback_context
        if not ctx.triggered:
            return active_no_update, no_update, no_update, no_update, no_update

        triggered_item = ctx.triggered[0]
        triggered = triggered_item['prop_id'].split('.')[0]
        # if the click value is falsy (0 or None), ignore
        if not triggered_item.get('value'):
            return active_no_update, no_update, no_update, no_update, no_update
        try:
            import json as _json
            parsed = _json.loads(triggered)
            paper_id = parsed.get('id')
        except Exception:
            return active_no_update, no_update, no_update, no_update, no_update

        # Fetch base paper info
        studies = get_studies_details(ids=[paper_id], start_row=0, end_row=1)
        if not studies:
            # clear active states
            active_states = [False] * len(ids_list)
            return active_states, html.Div("Paper not found"), no_update, no_update, hidden_results_style

        paper = studies[0]

        # Build classification tags
        tasks = get_all_tasks() or []
        tags_map = {task: get_all_labels(task) for task in tasks}
        study_tags = get_study_tags([paper_id], tags_map).get(paper_id, [])
        paper_obj = paper.copy()
        paper_obj['tags'] = study_tags
        tag_buttons = build_tag_buttons(paper_obj)

        details = build_paper_details(paper, tags_component=tag_buttons)
        # build active list based on ids_list
        active_states = [False] * len(ids_list)
        for idx, iddict in enumerate(ids_list):
            # iddict is like {'type': 'search-result', 'id': <id>}
            if iddict and iddict.get('id') == paper_id:
                active_states[idx] = True
                break

        # update URL search param so linkable (internal id only)
        search_str = f"?study_id={paper_id}"

        # clear the search results display (we're on a dedicated paper view)
        return active_states, details, search_str, "", hidden_results_style

    @app.callback(
        Output('search-paper-details', 'children', allow_duplicate=True),
        Output('search-results', 'children', allow_duplicate=True),
        Output('search-results', 'style', allow_duplicate=True),
        Input('url', 'search'),
        State('last-search-store', 'data'),
        prevent_initial_call='initial_duplicate',
    )
    @log_time
    def load_paper_from_url(search, last_search):
        # When `search` contains ?study_id=... show the paper details and hide results.
        # When `search` is empty, restore the last search results (if any) and clear details.
        if not search:
            # restore results from store
            if not last_search:
                return "", "", hidden_results_style
            items = []
            for s in last_search:
                year = s.get('year') or ''
                subtitle = f"{s.get('pubmed_id') or s.get('doi') or ''} {year}"
                items.append(
                    dbc.ListGroupItem([
                        html.Div(s.get('title'), className='fw-bold'),
                        html.Div(subtitle, className='text-muted small')
                    ], id={'type': 'search-result', 'id': s['id']}, action=True)
                )
            return "", dbc.ListGroup(items), visible_results_style

        # parse query string like ?study_id=123
        try:
            from urllib.parse import parse_qs
            qs = parse_qs(search.lstrip('?'))
            study_ids = qs.get('study_id') or []
            if not study_ids:
                return "", "", hidden_results_style
            paper_id = int(study_ids[0])
        except Exception:
            return "", "", hidden_results_style

        studies = get_studies_details(ids=[paper_id], start_row=0, end_row=1)
        if not studies:
            return html.Div("Paper not found"), "", hidden_results_style

        paper = studies[0]

        tasks = get_all_tasks() or []
        tags_map = {task: get_all_labels(task) for task in tasks}
        study_tags = get_study_tags([paper_id], tags_map).get(paper_id, [])
        paper_obj = paper.copy()
        paper_obj['tags'] = study_tags
        tag_buttons = build_tag_buttons(paper_obj)

        details = build_paper_details(paper, tags_component=tag_buttons)

        # hide the search results when showing details
        return details, "", hidden_results_style
