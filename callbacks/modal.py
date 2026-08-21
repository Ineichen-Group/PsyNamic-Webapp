from dash import ALL, ctx, dcc, html, no_update
from dash.dependencies import MATCH, Input, Output, State
import dash_bootstrap_components as dbc

from callbacks.utils import log_time
from components.layout import (_split_highlight_cutpoints,
                               _split_prediction_input, build_tag_buttons,
                               highlighted_text, build_structured_abstract)
from data.queries import get_paper_ner_tags


def build_modal_components(paper: dict, grid_type: str) -> tuple[list, html.Div]:
    """Build modal header title and structured body content for all grid types."""
    if not paper:
        return [], html.Div()

    year_str = f" – {paper.get('authors', '')} ({paper.get('year', '')})" if paper.get(
        "year") else ""
    paper_url = paper.get("url", "")
    paper_id = paper.get("id")

    cutpoints = []
    if grid_type == "dosage-study-grid":
        paper_title, body_text, body_offset = _split_prediction_input(paper)
        raw_tags = get_paper_ner_tags(paper_id, ner_type="Dosage")
        title_tags, cutpoints = _split_highlight_cutpoints(
            raw_tags, len(paper_title), body_offset
        )
        header_title = [
            highlighted_text(
                paper_title, title_tags) if title_tags else paper_title,
            year_str,
        ]
    else:
        body_text = paper.get("abstract")
        header_title = [paper.get("title", ""), year_str]

    abstract_content = build_structured_abstract(
        body_text, cutpoints=cutpoints)

    dosage_norm = paper.get("dosage_display", paper.get("dosage", ""))
    dosage_block = (
        html.Div(
            [
                html.Strong("Dosage normalization: "),
                html.Span(dosage_norm),
            ],
            className="modal-dosage-block",
        )
        if (grid_type == "dosage-study-grid" and dosage_norm)
        else None
    )

    # Link to search/explore overview page
    search_link = f"/explore/search?study_id={paper_id}" if paper_id else None

    body_content = html.Div(
        [
            html.Div(
                [
                    html.Strong("URL: "),
                    html.A(
                        paper_url,
                        href=paper_url,
                        target="_blank",
                        rel="noopener noreferrer",
                    ),
                ],
                className="modal-paper-link",
            )
            if paper_url
            else None,
            abstract_content,
            dosage_block,
            html.Div(build_tag_buttons(paper), className="modal-tags mt-3"),
            html.Div(
                [
                    dcc.Link(
                        dbc.Button(
                            [
                                html.I(className="fas fa-arrow-right-to-bracket me-2"),
                                "View Study",
                            ],
                            color="primary",
                            size="sm",
                        ),
                        href=search_link,
                        refresh=False,
                    )
                ],
                className="modal-footer-link mt-4 pt-3 border-top",
            )
            if search_link
            else None,
        ]
    )
    return header_title, body_content


def register(app):
    @app.callback(
        [
            Output({"type": "study-grid-modal", "index": MATCH}, "is_open"),
            Output({"type": "paper-modal-title", "index": MATCH}, "children"),
            Output({"type": "paper-modal-content", "index": MATCH}, "children"),
        ],
        Input({"type": "study-grid", "index": MATCH}, "selectedRows"),
        State({"type": "study-grid", "index": MATCH}, "id"),
        prevent_initial_call=True,
    )
    @log_time
    def show_study_modal(selected_rows_list: list[dict], grid_id: dict[str, str]):
        """Displays modal with structured paper details when a row is selected."""
        if not selected_rows_list:
            return False, no_update, no_update

        paper = next((row for row in selected_rows_list if row), None)
        if not paper:
            return False, no_update, no_update

        grid_type = grid_id.get("index", "") if isinstance(
            grid_id, dict) else ""
        header_title, modal_body = build_modal_components(paper, grid_type)

        return True, header_title, modal_body

    @app.callback(
        Output({"type": "collapse", "index": ALL}, "is_open"),
        Input({"type": "collapse-button", "index": ALL}, "n_clicks"),
        State({"type": "collapse", "index": ALL}, "is_open"),
    )
    @log_time
    def toggle_collapse(_, is_open_list: list[bool]) -> list[bool]:
        """Toggles accordion/collapse section states dynamically."""
        if not ctx.triggered:
            return no_update

        triggered = ctx.triggered_id
        if not isinstance(triggered, dict) or "index" not in triggered:
            return no_update

        target_index = triggered["index"]

        return [
            not current_state if i == target_index else False
            for i, current_state in enumerate(is_open_list)
        ]
