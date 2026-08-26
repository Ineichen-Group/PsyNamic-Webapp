import json
from urllib.parse import parse_qs, urlencode

import dash_bootstrap_components as dbc
from dash import ALL, callback_context, html, no_update
from dash.dependencies import Input, Output, State

from callbacks.utils import log_time
from components.layout import build_paper_details, build_tag_buttons
from data.queries import get_studies_details, get_study_tags, search_papers

PAGE_SIZE = 50  # Number of search results to display per page
pagination_hidden_style = {"display": "none"}

pagination_visible_style = {
    "display": "flex",
    "justifyContent": "center",
}


def register(app):
    """Register callbacks for the explore/search page."""

    hidden_results_style = {
        "display": "none",
        "maxHeight": "800px",
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

        return "?" + urlencode({
            "query": query.strip(),
            "page": 1,
        })

    # -------------------------------------------------------------------------
    # Callback 2: URL change drives ALL page rendering & input sync
    # -------------------------------------------------------------------------
    @app.callback(
        Output("search-paper-details", "children"),
        Output("search-results", "children"),
        Output("search-results", "style"),
        Output("last-search-store", "data"),
        Output("search-input", "value"),
        Output("search-results-count", "children"),
        Output("search-pagination", "active_page"),
        Output("search-pagination", "max_value"),
        Output("search-pagination", "style"),
        Input("url", "pathname"),
        Input("url", "search"),
        prevent_initial_call=False,
    )
    @log_time
    def render_page_from_url(pathname, search):
        if pathname != "/explore/search":
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        # -------------------------------------------------------------------------
        # No URL search parameters
        # -------------------------------------------------------------------------
        if not search:
            return (
                "",
                "",
                hidden_results_style,
                None,
                no_update,
                "",
                1,
                1,
                pagination_hidden_style,
            )

        # -------------------------------------------------------------------------
        # Parse URL query parameters
        # -------------------------------------------------------------------------
        try:
            qs = parse_qs(search.lstrip("?"))
        except Exception:
            return (
                "",
                "",
                hidden_results_style,
                None,
                no_update,
                "",
                1,
                1,
                pagination_hidden_style,
            )

        # =========================================================================
        # Case A: Search Query URL
        # Example: ?query=lsd&page=2
        # =========================================================================
        if "query" in qs:
            search_term = qs["query"][0]
            try:
                page = int(qs.get("page", ["1"])[0])
            except (ValueError, TypeError):
                page = 1

            page = max(1, page)

            start_row = (page - 1) * PAGE_SIZE
            end_row = start_row + PAGE_SIZE

            studies, total_count = search_papers(
                search_term,
                start_row=start_row,
                end_row=end_row,
            )

            total_pages = max(
                1,
                (total_count + PAGE_SIZE - 1) // PAGE_SIZE,
            )

            # If somebody manually enters ?page=999,
            # don't leave them on an empty page.
            if page > total_pages:
                page = total_pages

                start_row = (page - 1) * PAGE_SIZE
                end_row = start_row + PAGE_SIZE

                studies, _ = search_papers(
                    search_term,
                    start_row=start_row,
                    end_row=end_row,
                )

            # ---------------------------------------------------------------------
            # No matching papers
            # ---------------------------------------------------------------------
            if not studies:
                return (
                    "",                         # search-paper-details
                    "",                         # search-results
                    hidden_results_style,       # hide results container
                    [],                         # last-search-store
                    search_term,                # search-input
                    "0 results found",          # search-results-count
                    1,                          # pagination.active_page
                    1,                          # pagination.max_value
                    pagination_hidden_style,    # pagination.style
                )

            items = []

            for s in studies:
                authors = s.get("authors", "")
                year = s.get("year")

                author_year = (
                    f" – {authors} ({year})"
                    if year
                    else ""
                )

                subtitle = ""

                if s.get("pubmed_id"):
                    subtitle = (
                        f"PubMed ID: {s.get('pubmed_id')} | "
                    )

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
                        id={
                            "type": "search-result",
                            "id": s["id"],
                        },
                        action=True,
                    )
                )

            # ---------------------------------------------------------------------
            # Show pagination only when there is more than one page
            # ---------------------------------------------------------------------
            pagination_style = (
                pagination_visible_style
                if total_count > PAGE_SIZE
                else pagination_hidden_style
            )


            return (
                "",
                dbc.ListGroup(items),
                visible_results_style,
                studies,
                search_term,
                f"{total_count} result{'s' if total_count != 1 else ''} found",
                page,
                total_pages,
                pagination_style,
            )

        # =========================================================================
        # Case B: Study Details URL
        # Example: ?study_id=7050
        # =========================================================================
        if "study_id" in qs:
            try:
                paper_id = int(qs["study_id"][0])
            except ValueError:
                return (
                    "",
                    "",
                    hidden_results_style,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    pagination_hidden_style,
                )

            studies = get_studies_details(
                ids=[paper_id],
                start_row=0,
                end_row=1,
            )

            # ---------------------------------------------------------------------
            # Paper doesn't exist
            # ---------------------------------------------------------------------
            if not studies:
                return (
                    "",
                    "",
                    hidden_results_style,
                    [],
                    search_term,
                    "0 results found",
                    1,
                    1,
                    pagination_hidden_style,
                )

            paper = studies[0]

            study_tags = get_study_tags([paper_id])

            paper_obj = paper.copy()
            paper_obj["tags"] = study_tags.get(
                paper_id,
                [],
            )

            details = build_paper_details(
                paper,
                tags_component=build_tag_buttons(paper_obj),
            )

            # ---------------------------------------------------------------------
            # No pagination on single-paper details page
            # ---------------------------------------------------------------------
            return (
                details,
                "",
                hidden_results_style,
                no_update,
                no_update,
                no_update,
                1,
                1,
                pagination_hidden_style,
            )

        # -------------------------------------------------------------------------
        # Unknown URL parameters
        # -------------------------------------------------------------------------
        return (
            "",
            "",
            hidden_results_style,
            None,
            no_update,
            "",
            1,
            1,
            pagination_hidden_style,
        )
    # -------------------------------------------------------------------------
    # Callback 3: Clicking a search result item updates URL to ?study_id=...
    # -------------------------------------------------------------------------

    @app.callback(
        Output(
            {"type": "search-result", "id": ALL},
            "active",
            allow_duplicate=True,
        ),
        Output("url", "search", allow_duplicate=True),
        Input(
            {"type": "search-result", "id": ALL},
            "n_clicks",
        ),
        State(
            {"type": "search-result", "id": ALL},
            "id",
        ),
        prevent_initial_call=True,
    )
    @log_time
    def select_search_paper(n_clicks_list, ids_list):
        active_no_update = [no_update] * len(ids_list)

        ctx = callback_context

        if not ctx.triggered:
            return active_no_update, no_update

        # Find which component triggered the callback.
        triggered_prop_id = ctx.triggered[0]["prop_id"]

        try:
            triggered_id = json.loads(
                triggered_prop_id.split(".")[0]
            )
        except (ValueError, json.JSONDecodeError):
            return active_no_update, no_update

        # Find the corresponding result in ids_list.
        try:
            triggered_index = next(
                i
                for i, item_id in enumerate(ids_list)
                if item_id == triggered_id
            )
        except StopIteration:
            return active_no_update, no_update

        # IMPORTANT:
        # Ignore callback invocations caused by the result components
        # being created/replaced rather than actually clicked.
        n_clicks = n_clicks_list[triggered_index]

        if not n_clicks or n_clicks < 1:
            return active_no_update, no_update

        paper_id = triggered_id.get("id")

        if not paper_id:
            return active_no_update, no_update

        active_states = [
            item_id.get("id") == paper_id
            for item_id in ids_list
        ]

        return active_states, f"?study_id={paper_id}"

    @app.callback(
        Output("url", "search", allow_duplicate=True),
        Input("search-pagination", "active_page"),
        State("url", "search"),
        prevent_initial_call=True,
    )
    def change_search_page(page, search):
        if not search or not page:
            return no_update

        qs = parse_qs(search.lstrip("?"))

        if "query" not in qs:
            return no_update

        query = qs["query"][0]

        current_page = int(qs.get("page", ["1"])[0])

        # Prevent unnecessary URL updates when the URL already
        # represents the selected page.
        if page == current_page:
            return no_update

        return "?" + urlencode({
            "query": query,
            "page": page,
        })
