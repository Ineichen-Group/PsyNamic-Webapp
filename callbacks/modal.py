from dash import html, no_update, ALL, ctx
from dash.dependencies import MATCH, Input, Output, State

from components.layout import (_split_highlight_cutpoints,
                               _split_prediction_input, build_tag_buttons,
                               highlighted_text)
from data.queries import ner_tags_type


def _build_modal_content(paper: dict) -> tuple[bool, str, str, str, str, str, list]:
    """Shared modal content builder for standard study grids."""
    if not paper:
        return False, no_update, no_update, no_update, no_update, no_update, no_update

    title = f"{paper['title']} ({paper.get('year', '')})"
    abstract = paper.get("abstract", "")
    link_text = paper.get("url", "")
    link_href = paper.get("url", "")
    buttons = build_tag_buttons(paper)

    return True, title, link_href, link_text, abstract, "", buttons


def register(app):
    @app.callback(
        [
            Output({"type": "study-grid-modal", "index": MATCH}, "is_open"),
            Output({"type": "paper-title", "index": MATCH}, "children"),
            Output({"type": "paper-link", "index": MATCH}, "href"),
            Output({"type": "paper-link", "index": MATCH}, "children"),
            Output({"type": "paper-abstract", "index": MATCH}, "children"),
            Output({"type": "paper-dosage-normalization",
                   "index": MATCH}, "children"),
            Output({"type": "modal-tags", "index": MATCH}, "children"),
        ],
        Input({"type": "study-grid", "index": MATCH}, "selectedRows"),
        State({"type": "study-grid", "index": MATCH}, "id"),
        prevent_initial_call=True
    )
    def show_study_modal(selected_rows_list: list[dict], grid_id: dict[str, str]) -> tuple[bool, str, str, str, str, str, list]:
        """Callback to display the modal with study details when a row is selected in the study grid."""
        if not selected_rows_list:
            return (
                False,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        # AG Grid selectedRows is a list of rows
        paper = next(
            (row for row in selected_rows_list if row),
            None
        )

        if not paper:
            return (
                False,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        current_grid = grid_id["index"]

        if current_grid == "dosage-study-grid":
            paper_title, body_text, body_offset = _split_prediction_input(
                paper)

            title_tags, body_tags = _split_highlight_cutpoints(
                ner_tags_type(
                    paper.get("id"),
                    "Dosage",
                ),
                len(paper_title),
                body_offset,
            )

            highlighted_title = (
                highlighted_text(paper_title, title_tags)
                if title_tags
                else paper_title
            )

            highlighted_abstract = (
                highlighted_text(body_text, body_tags)
                if body_tags
                else body_text
            )

            title = html.H3(
                [
                    highlighted_title,
                    f" ({paper.get('year', '')})",
                ]
            )

            dosage_normalization = paper.get(
                "dosage_display",
                paper.get("dosage", ""),
            )

            dosage_block = (
                html.Div(
                    [
                        html.Strong("Dosage normalization: "),
                        html.Span(dosage_normalization),
                    ]
                )
                if dosage_normalization
                else ""
            )

            link_text = paper.get("url", "")
            link_href = paper.get("url", "")
            buttons = build_tag_buttons(paper)

            return (
                True,
                title,
                link_href,
                link_text,
                highlighted_abstract,
                dosage_block,
                buttons,
            )

        return _build_modal_content(paper)

    @app.callback(
        Output({'type': 'collapse', 'index': ALL}, 'is_open'),
        Input({'type': 'collapse-button', 'index': ALL}, 'n_clicks'),
        State({'type': 'collapse', 'index': ALL}, 'is_open'),
    )
    def toggle_collapse(_, is_open_list: list[bool]) -> list[bool]:
        """Callback to toggle the collapse of the modal sections based on the button clicks."""

        if not ctx.triggered:
            return is_open_list

        button_id = ctx.triggered_id
        index = int(button_id.split('{"index":')[1].split(',')[0])

        new_is_open_list = [False] * len(is_open_list)
        new_is_open_list[index] = not is_open_list[index]

        return new_is_open_list