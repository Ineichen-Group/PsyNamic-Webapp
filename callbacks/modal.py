from dash import ALL, html, no_update
from dash.dependencies import Input, Output, State

from components.layout import (_split_highlight_cutpoints,
                               _split_prediction_input, build_tag_buttons,
                               highlighted_text)
from data.queries import ner_tags_type


def _build_modal_content(selected_rows):
    """Shared modal content builder."""

    if not selected_rows:
        return False, no_update, no_update, no_update, no_update, no_update, no_update

    paper = selected_rows[0]

    title = f"{paper['title']} ({paper.get('year', '')})"
    abstract = paper.get("abstract", "")
    link_text = paper.get("url", "")
    link_href = paper.get("url", "")
    buttons = build_tag_buttons(paper)

    return True, title, link_href, link_text, abstract, "", buttons


def register(app):

    # =====================================================
    # Regular Studies Grid Modal
    # =====================================================
    @app.callback(
        [
            Output("paper-modal", "is_open", allow_duplicate=True),
            Output("paper-title", "children", allow_duplicate=True),
            Output("paper-link", "href", allow_duplicate=True),
            Output("paper-link", "children", allow_duplicate=True),
            Output("paper-abstract", "children", allow_duplicate=True),
            Output("paper-dosage-normalization", "children", allow_duplicate=True),
            Output("modal-tags", "children", allow_duplicate=True),
        ],
        Input({"type": "studies-grid", "index": ALL}, "selectedRows"),
        prevent_initial_call=True
    )
    def show_study_modal(selected_rows_list):

        if not selected_rows_list:
            return False, no_update, no_update, no_update, no_update, no_update, no_update

        selected_row_data = next(
            (rows for rows in selected_rows_list if rows),
            None
        )

        if not selected_row_data:
            return False, no_update, no_update, no_update, no_update, no_update, no_update

        return _build_modal_content(selected_row_data)

    # =====================================================
    # Dosage Grid Modal
    # =====================================================

    @app.callback(
        [
            Output("dosage-modal", "is_open", allow_duplicate=True),
            Output("paper-title", "children", allow_duplicate=True),
            Output("paper-link", "href", allow_duplicate=True),
            Output("paper-link", "children", allow_duplicate=True),
            Output("paper-abstract", "children", allow_duplicate=True),
            Output("paper-dosage-normalization", "children", allow_duplicate=True),
            Output("modal-tags", "children", allow_duplicate=True),
        ],
        Input("dosage-study-grid", "selectedRows"),
        prevent_initial_call=True
    )
    def show_dosage_modal(selected_rows_list):

        if not selected_rows_list:
            return False, no_update, no_update, no_update, no_update, no_update, no_update

        paper = selected_rows_list[0]
        if not paper:
            return False, no_update, no_update, no_update, no_update, no_update, no_update

        paper_title, body_text, body_offset = _split_prediction_input(paper)
        title_tags, body_tags = _split_highlight_cutpoints(
            ner_tags_type(paper.get('id'), 'Dosage'),
            len(paper_title),
            body_offset,
        )

        highlighted_title = highlighted_text(paper_title, title_tags) if title_tags else paper_title
        text_with_tag = highlighted_text(body_text, body_tags) if body_tags else body_text

        title = html.H3([highlighted_title, f" ({paper.get('year', '')})"])
        link_text = paper.get("url", "")
        link_href = paper.get("url", "")
        dosage_normalization = paper.get("dosage_display", paper.get("dosage", ""))
        dosage_block = (
            html.Div([
                html.Strong("Dosage normalization: "),
                html.Span(dosage_normalization),
            ]) if dosage_normalization else ""
        )
        buttons = build_tag_buttons(paper)

        return True, title, link_href, link_text, text_with_tag, dosage_block, buttons

    # =====================================================
    # Clear selection (shared logic)
    # =====================================================

    @app.callback(
        Output({"type": "studies-grid", "index": ALL},
               "selectedRows", allow_duplicate=True),
        Input("paper-modal", "is_open"),
        State({"type": "studies-grid", "index": ALL}, "selectedRows"),
        prevent_initial_call=True,
    )
    def clear_studies_selection(is_open, selected_rows_lists):
        if is_open:
            # For wildcard multi-outputs we must return a list/tuple with one
            # value per matched output. Returning `no_update` directly is
            # invalid. Return the existing selections unchanged instead.
            return selected_rows_lists if selected_rows_lists is not None else []
        return [[] for _ in (selected_rows_lists or [])]

    @app.callback(
        Output("dosage-study-grid", "selectedRows", allow_duplicate=True),
        Input("dosage-modal", "is_open"),
        prevent_initial_call=True,
    )
    def clear_dosage_selection(is_open):
        if is_open:
            return no_update
        return []

