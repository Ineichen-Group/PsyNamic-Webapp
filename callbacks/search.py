import json
from urllib.parse import parse_qs

import dash_bootstrap_components as dbc
from dash import ALL, callback_context, html, no_update
from dash.dependencies import Input, Output, State

from callbacks.utils import log_time
from components.layout import build_paper_details, build_tag_buttons
from data.queries import get_studies_details, get_study_tags, search_papers


def register(app):
    """Register callbacks for the explore/search page."""

    hidden_results_style = {
        "display": "none",
        "maxHeight": "400px",
        "overflowY": "auto",
        "border": "1px solid #ced4da",
        "padding": "0.5rem",
        "borderRadius": "0.25rem",
        "backgroundColor": "#fff",
    }

    visible_results_style = {**hidden_results_style, "display": "block"}

    # -------------------------------------------------------------------------
    # Callback 1: User action updates URL query string
    # -------------------------------------------------------------------------
    @app.callback(
        Output("url", "search"),
        Input("search-button", "n_clicks"),
        Input("search-input", "n_submit"),
        State("search-input", "value"),
        prevent_initial_call=True,
    )
    def update_url_from_search(n_clicks, n_submit, query):
        triggered_id = callback_context.triggered_id

        # Ignore callback invocations caused by component mount/hydration.
        if triggered_id == "search-button" and (n_clicks or 0) < 1:
            return no_update
        if triggered_id == "search-input" and (n_submit or 0) < 1:
            return no_update

        # Do not clear existing URL params (e.g. ?study_id=...) on empty input.
        if not query or not query.strip():
            return no_update

        return f"?query={query.strip()}"

    # -------------------------------------------------------------------------
    # Callback 2: URL change drives ALL page rendering & input sync
    # -------------------------------------------------------------------------
    @app.callback(
        Output("search-paper-details", "children"),
        Output("search-results", "children"),
        Output("search-results", "style"),
        Output("last-search-store", "data"),
        Output("search-input", "value"),
        Input("url", "pathname"),
        Input("url", "search"),
        prevent_initial_call=False,  # Run on initial page load from direct URL
    )
    @log_time
    def render_page_from_url(pathname, search):
        if pathname != "/explore/search":
            return no_update, no_update, no_update, no_update, no_update

        if not search:
            return "", "", hidden_results_style, None, no_update

        try:
            qs = parse_qs(search.lstrip("?"))
        except Exception:
            return "", "", hidden_results_style, None, no_update

        # -------------------------
        # Case A: Search Query URL (?query=...)
        # -------------------------
        if "query" in qs:
            search_term = qs["query"][0]
            studies = search_papers(
                search_term,
                start_row=0,
                end_row=50,
            )

            if not studies:
                return (
                    html.Div("No matching papers found."),
                    "",
                    visible_results_style,
                    [],
                    search_term,
                )

            items = []
            for s in studies:
                authors = s.get("authors", "")
                year = s.get("year")
                author_year = f" – {authors} ({year})" if year else ""

                subtitle = ""
                if s.get("pubmed_id"):
                    subtitle = f"PubMed ID: {s.get('pubmed_id')} | "

                if s.get("doi"):
                    subtitle += f"DOI: {s.get('doi')} | "

                subtitle = subtitle.rstrip(" | ")

                items.append(
                    dbc.ListGroupItem(
                        [
                            html.Div(
                                f"{s.get('title', '')}{author_year}",
                                className="fw-bold",
                            ),
                            html.Div(
                                subtitle,
                                className="text-muted small",
                            ),
                        ],
                        id={"type": "search-result", "id": s["id"]},
                        action=True,
                    )
                )
            return (
                "",
                dbc.ListGroup(items),
                visible_results_style,
                studies,
                search_term,  # Sync input box with URL parameter
            )

        # -------------------------
        # Case B: Study Details URL (?study_id=...)
        # -------------------------
        if "study_id" in qs:
            try:
                paper_id = int(qs["study_id"][0])
            except ValueError:
                return "", "", hidden_results_style, no_update, no_update

            studies = get_studies_details(
                ids=[paper_id],
                start_row=0,
                end_row=1,
            )

            if not studies:
                return (
                    html.Div("Paper not found"),
                    "",
                    hidden_results_style,
                    no_update,
                    no_update,
                )

            paper = studies[0]
            study_tags = get_study_tags([paper_id])
            paper_obj = paper.copy()
            paper_obj["tags"] = study_tags.get(paper_id, [])

            details = build_paper_details(
                paper,
                tags_component=build_tag_buttons(paper_obj),
            )

            return (
                details,
                "",
                hidden_results_style,
                no_update,
                no_update,
            )

        return "", "", hidden_results_style, None, no_update

    # -------------------------------------------------------------------------
    # Callback 3: Clicking a search result item updates URL to ?study_id=...
    # -------------------------------------------------------------------------
    @app.callback(
        Output({"type": "search-result", "id": ALL}, "active", allow_duplicate=True),
        Output("url", "search", allow_duplicate=True),
        Input({"type": "search-result", "id": ALL}, "n_clicks"),
        State({"type": "search-result", "id": ALL}, "id"),
        prevent_initial_call=True,
    )
    @log_time
    def select_search_paper(n_clicks_list, ids_list):
        active_no_update = [no_update] * len(ids_list)
        ctx = callback_context

        if not ctx.triggered:
            return active_no_update, no_update

        triggered = ctx.triggered[0]["prop_id"].split(".")[0]

        try:
            parsed = json.loads(triggered)
            paper_id = parsed.get("id")
        except Exception:
            return active_no_update, no_update

        if not paper_id:
            return active_no_update, no_update

        active_states = [iddict.get("id") == paper_id for iddict in ids_list]

        return active_states, f"?study_id={paper_id}"