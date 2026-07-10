import logging
import time
import json
import pandas as pd
from data.dosage_norm import remove_several_substances_dosages
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import html


from dash import callback_context, no_update, dcc, ALL
from dash.dependencies import Input, Output, State

from pages.explore.dual_task import (
    get_dual_task_data,
    create_pie_chart,
    create_bar_chart,
    dual_study_grid,
    get_dual_filters,
    dual_task_graphs,
)

from components.layout import filter_button, tag_component, get_tags, filter_data, highlighted_text, get_filter_buttons
from style.colors import rgb_to_hex, get_color_mapping, SECONDARY_COLOR, get_color
from data.queries import get_studies_details, get_filtered_study_ids, get_time_data, nr_studies, get_all_labels, get_studies_details_ner, ner_tags_type, get_dosage_samples, get_ids
from data.queries import search_papers, get_all_tasks, get_study_tags
from components.graphs import box_plot_graph
STYLE_NORMAL = {'border': '1px solid #ccc'}
STYLE_ERROR = {'border': '2px solid red'}


# =====================================================
# Utility Helpers
# =====================================================

def log_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        logging.info(f"{func.__name__} executed in {duration:.4f} seconds")
        return result
    return wrapper


def build_tag_buttons(paper):
    """
    Extracted shared tag-building logic used in both modals.
    """
    tags = []
    prev_task = None
    task_dict = {"task": "", "buttons": [], "model": ""}

    for tag in paper.get("tags", []):
        if tag["task"] != prev_task:
            if task_dict["task"]:
                tags.append(task_dict)

            prev_task = tag["task"]
            task_dict = {
                "task": tag["task"],
                "buttons": [filter_button(tag["color"], tag["label"], tag["task"])],
                "model": "BERT",
            }
        else:
            task_dict["buttons"].append(
                filter_button(tag["color"], tag["label"], tag["task"])
            )

    if task_dict["task"]:
        tags.append(task_dict)

    return tag_component(tags)


def _split_prediction_input(paper):
    """Split prediction_input into title and body when the source text includes both."""
    prediction_input = (
        paper.get('prediction_input')
        or paper.get('abstract')
        or ''
    )
    title = paper.get('title', '') or ''

    for separator in ('.^\n', '.^.'):
        if separator in prediction_input:
            split_title, body = prediction_input.split(separator, 1)
            return (split_title or title), body, len(split_title) + len(separator)

    return title, prediction_input, 0


def _split_highlight_cutpoints(cutpoints, title_length, body_offset):
    """Split raw cutpoints into title-relative and body-relative spans."""
    title_cutpoints = []
    body_cutpoints = []

    if not cutpoints:
        return title_cutpoints, body_cutpoints

    for cp in cutpoints:
        start = cp.get('start', 0)
        end = cp.get('end', 0)

        if end <= title_length:
            title_cutpoints.append(cp.copy())
            continue

        if start >= body_offset:
            body_cp = cp.copy()
            body_cp['start'] = max(0, start - body_offset)
            body_cp['end'] = max(0, end - body_offset)
            body_cutpoints.append(body_cp)
            continue

        if start < title_length:
            title_cp = cp.copy()
            title_cp['start'] = start
            title_cp['end'] = min(end, title_length)
            if title_cp['end'] > title_cp['start']:
                title_cutpoints.append(title_cp)

        if end > body_offset:
            body_cp = cp.copy()
            body_cp['start'] = max(0, start - body_offset)
            body_cp['end'] = max(0, end - body_offset)
            if body_cp['end'] > body_cp['start']:
                body_cutpoints.append(body_cp)

    return title_cutpoints, body_cutpoints


def _build_paper_header(paper, highlighted_title):
    """Build the shared paper header with URL, ids, and title."""
    paper_url = paper.get('url') or ''
    internal_id = paper.get('id') or ''
    pubmed_id = paper.get('pubmed_id') or ''

    return [
        html.Div([
            html.Span("URL: "),
            html.A(paper_url, href=paper_url, target='_blank'),
        ]),
        html.Div(
            f"Internal ID: {internal_id} | PubMed ID: {pubmed_id}",
            className='text-muted small',
        ),
        html.H3(highlighted_title),
    ]


def _build_paper_details(paper, ner_category=None, body_label="Abstract", tags_component=None):
    """Build a detail card with consistent title/body highlighting."""
    paper_id = paper.get('id')
    ner_tags = ner_tags_type(paper_id, ner_category) if ner_category else ner_tags_type(paper_id)
    paper_title, body_text, body_offset = _split_prediction_input(paper)
    title_tags, body_tags = _split_highlight_cutpoints(
        ner_tags,
        len(paper_title),
        body_offset,
    )

    highlighted_title = highlighted_text(paper_title, title_tags) if title_tags else paper_title
    highlighted_body = highlighted_text(body_text, body_tags) if body_tags else body_text

    children = [
        *_build_paper_header(paper, highlighted_title),
        html.H5(body_label),
        html.Div(highlighted_body, className='mb-3'),
    ]

    if tags_component:
        children.extend([
            html.H5("Tags"),
            tags_component,
        ])

    return html.Div(children, className='p-3 border rounded')


# =====================================================
# Registration
# =====================================================

def register_callbacks(app):
    register_time_view_callbacks(app)
    register_studyview_callbacks(app)
    register_dual_task_view_callbacks(app)
    register_pagination_callbacks(app)
    register_modal_callbacks(app)
    register_download_csv_callback(app)
    register_filter_callback(app)
    register_pagination_dosages_callbacks(app)
    register_dosage_graph_callbacks(app)
    register_search_callbacks(app)


# =====================================================
# Time View
# =====================================================

def register_time_view_callbacks(app):

    @app.callback(
        Output({"type": "studies-grid", "index": 6},
               "getRowsResponse", allow_duplicate=True),
        Output("time-graph", "figure"),
        Output("count-filtered", "children"),
        Input("start-year", "value"),
        Input("end-year", "value"),
        prevent_initial_call=True
    )
    @log_time
    def update_time_view(start_year, end_year):
        df, ids = get_time_data(start_year=start_year, end_year=end_year)

        fig = px.bar(
            df,
            x="Year",
            y="Frequency",
            title="Frequency of Publications per Year",
            labels={"Frequency": "Frequency"},
        )

        studies = get_studies_details(ids=ids)

        return (
            {"rowData": studies, "rowCount": len(ids)},
            fig,
            len(ids),
        )
# =====================================================
# Study View (Collapse)
# =====================================================


def register_studyview_callbacks(app):

    @app.callback(
        Output({'type': 'collapse', 'index': ALL}, 'is_open'),
        Input({'type': 'collapse-button', 'index': ALL}, 'n_clicks'),
        State({'type': 'collapse', 'index': ALL}, 'is_open'),
    )
    def toggle_collapse(n_clicks_list, is_open_list):
        ctx = callback_context

        if not ctx.triggered:
            return is_open_list

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        index = int(button_id.split('{"index":')[1].split(',')[0])

        new_is_open_list = [False] * len(is_open_list)
        new_is_open_list[index] = not is_open_list[index]

        return new_is_open_list


def register_dosage_graph_callbacks(app):
    @app.callback(
        Output('dosage-study-grid', 'getRowsResponse', allow_duplicate=True),
        Output('filtered-study-ids', 'data', allow_duplicate=True),
        Output('count-filtered', 'children', allow_duplicate=True),
        Output({'type': 'dosage-box-plot', 'index': ALL}, 'figure', allow_duplicate=True),
        Input({'type': 'dosage-box-plot', 'index': ALL}, 'selectedData'),
        Input({'type': 'dosage-box-plot', 'index': ALL}, 'clickData'),
        Input('dosage-reset-btn', 'n_clicks'),
        State('filtered-study-ids', 'data'),
        prevent_initial_call=True,
    )
    def update_filtered_ids(selectedDatas, clickDatas, reset_clicks, current_ids):
        ctx = callback_context
        # determine how many dosage graphs are present (length of pattern-matching inputs)
        try:
            n_graphs = max(len(selectedDatas) if selectedDatas is not None else 0, len(clickDatas) if clickDatas is not None else 0)
        except Exception:
            n_graphs = 1
        figs_no_update = [no_update] * max(1, n_graphs)

        if not ctx.triggered:
            return no_update, no_update, no_update, figs_no_update
        triggered = ctx.triggered_id

        if triggered == 'dosage-reset-btn':
            ids = get_ids()
            # fetch first page for grid
            studies = get_studies_details_ner(
                ids=ids if ids else [], start_row=0, end_row=20)
            row_count = len(ids) if ids else nr_studies()
            # rebuild original figure (cleared selection)
            df = remove_several_substances_dosages(get_dosage_samples())
            if df is None or df.empty:
                fig = None
            else:
                substance_labels = sorted(df['Substance'].unique().tolist())
                col_map = get_color_mapping('Substances', substance_labels)

                # Rebuild one figure per non-empty group to preserve individual
                # heights/sizing used in the view (rest=700, ibogaine=200, lsd=200).
                substances = sorted(df['Substance'].dropna().unique().tolist())
                lsd_subs = ['LSD']
                ibogaine_subs = ['Ibogaine']
                rest_subs = [s for s in substances if s not in lsd_subs + ibogaine_subs]
                groups = [rest_subs, ibogaine_subs, lsd_subs]

                figs = []
                for i, subs in enumerate(groups):
                    sub_df = df[df['Substance'].isin(subs)]
                    if sub_df.empty:
                        continue
                    if subs == ibogaine_subs:
                        h = 200
                    elif subs == lsd_subs:
                        h = 200
                    else:
                        h = 700

                    add_ann = False if subs == ibogaine_subs or subs == lsd_subs else True
                    fig_i = box_plot_graph(
                        sub_df,
                        x='Substance',
                        y='Dosage_mg',
                        title='',
                        x_label='Substance',
                        y_label='Dosage (mg)',
                        group=None,
                        color_mapping=col_map,
                        height=h,
                        add_annotation=add_ann,
                        id='dosage-box-plot',
                    ).figure
                    figs.append(fig_i)

            # If no groups produced a figure, ensure we return placeholders
            if not figs:
                figs = [None] * max(1, n_graphs)
            return {"rowData": studies, "rowCount": row_count}, ids, row_count, figs

        ids_set = set()

        # Determine which input triggered and extract its payload
        triggered_payload = ctx.triggered[0].get('value')
        if triggered_payload and isinstance(triggered_payload, dict) and 'points' in triggered_payload:
            # selection or click from a specific plot
            for pt in triggered_payload['points']:
                custom = pt.get('customdata')
                if custom is None or (hasattr(custom, '__len__') and len(custom) == 0):
                    continue

                # normalize the Study_ID value to a hashable Python scalar
                cd0 = custom[0] if isinstance(custom, (list, tuple)) else custom
                # unwrap numpy scalar if present
                try:
                    if hasattr(cd0, 'item'):
                        cd0 = cd0.item()
                except Exception:
                    pass

                # fallback to string if still unhashable
                try:
                    hash(cd0)
                    ids_set.add(cd0)
                except TypeError:
                    ids_set.add(str(cd0))

        if not ids_set:
            return no_update, no_update, no_update, figs_no_update

        ids = list(ids_set)
        studies = get_studies_details_ner(ids=ids, start_row=0, end_row=20)
        row_count = len(ids)

        # Do not modify figures on selection — only update the study grid and
        # filtered ids. Return a list of `no_update` for the wildcard figure
        # output so the client retains its current visual state (prevents
        # server-driven figure changes).
        return {"rowData": studies, "rowCount": row_count}, ids, row_count, figs_no_update


def register_pagination_dosages_callbacks(app):
    @app.callback(
        Output('dosage-study-grid', "getRowsResponse", allow_duplicate=True),
        Output('count-filtered', 'children', allow_duplicate=True),
        Input('dosage-study-grid', "getRowsRequest"),
        Input("filter-tags", "data"),
        State("filtered-study-ids", "data"),
        prevent_initial_call=True
    )
    def fetch_studies_infinite(request, filtered_ids, tags):
        if not request:
            return no_update, no_update

        start_row = request["startRow"]
        end_row = request["endRow"]

        sort_model = request.get(
            "sortModel", [{"colId": "year", "sort": "desc"}])
        filter_model = request.get("filterModel", {})

        studies = get_studies_details_ner(
            ids=filtered_ids if filtered_ids else [],
            start_row=start_row,
            end_row=end_row,
            sort_model=sort_model,
            filter_model=filter_model,
            tags=tags
        )
        if len(studies) == 0:
            row_count = 0
        else:
            row_count = len(filtered_ids) if filtered_ids else nr_studies()

        return {
            "rowData": studies,
            "rowCount": row_count
        }, row_count

# =====================================================
# Dual Task View
# =====================================================


def register_dual_task_view_callbacks(app):
    # Split behavior into two callbacks for clarity and to avoid overlapping
    # triggered logic: one handles dropdown changes and renders the full
    # dual-task graph; the other handles pie-segment clicks and updates the
    # pie/bar figures + filters/grid.
    @app.callback(
        [
            Output('validation-message', 'children'),
            Output('dual-task-graph', 'children'),
            Output('task1-pie-graph', 'figure'),
            Output('task2-bar-graph', 'figure'),
            Output('active-filters', 'children'),
            Output('info-buttons', 'children'),
            Output('dual-study-grid', 'children'),
        ],
        [
            Input('jux_dropdown1', 'value'),
            Input('jux_dropdown2', 'value'),
            Input('task1-pie-graph', 'clickData'),
        ],
        prevent_initial_call=True,
    )
    @log_time
    def update_dual_task_view(dropdown1_value, dropdown2_value, click_data):
        ctx = callback_context
        triggered = (ctx.triggered[0]['prop_id'].split(
            '.')[0]) if ctx.triggered else None

        if dropdown1_value and dropdown2_value and dropdown1_value == dropdown2_value:
            return "Choose two different tasks.", no_update, no_update, no_update, no_update, no_update, no_update

        # If a pie segment was clicked, handle that interaction
        if triggered == 'task1-pie-graph':
            if not click_data:
                return no_update, no_update, no_update, no_update, no_update, no_update, no_update

            if not dropdown1_value or not dropdown2_value:
                return "Choose two tasks first.", no_update, no_update, no_update, no_update, no_update, no_update

            label = click_data['points'][0]['label']
            color = click_data['points'][0].get('color')

            task1_data, task2_data, ids, tags = get_dual_task_data(
                dropdown1_value, dropdown2_value, label)

            task1_all_labels = get_all_labels(dropdown1_value)
            col_map = get_color_mapping(dropdown1_value, task1_all_labels)

            if color and rgb_to_hex(color) == SECONDARY_COLOR:
                color = col_map.get(label, '#000000')

            pie_chart = create_pie_chart(
                task1_data, dropdown1_value, col_map, highlight=label, highlight_color=color)
            bar_chart = create_bar_chart(task2_data, dropdown2_value, color)

            filters = get_dual_filters(dropdown1_value, label)
            grid = dual_study_grid(ids, tags)
            info_buttons = get_filter_buttons(
                dropdown2_value, get_all_labels(dropdown2_value))
            return "", no_update, pie_chart, bar_chart, filters, info_buttons, grid

        if not dropdown1_value or not dropdown2_value:
            return "", html.Div(), no_update, no_update, no_update, no_update, no_update

        # Build the combined dual-task graph and fresh figures (clears previous highlights)
        df_task1, df_task2, ids, tags = get_dual_task_data(
            dropdown1_value, dropdown2_value)
        graph = dual_task_graphs(
            df_task1, df_task2, dropdown1_value, dropdown2_value)

        task1_all_labels = get_all_labels(dropdown1_value)
        col_map = get_color_mapping(
            dropdown1_value, task1_all_labels) if df_task1 is not None else {}
        pie_fig = create_pie_chart(
            df_task1, dropdown1_value, col_map) if df_task1 is not None else {}
        bar_color = get_color(
            dropdown2_value, 'hex') if dropdown2_value else None
        bar_fig = create_bar_chart(
            df_task2, dropdown2_value, bar_color) if df_task2 is not None else {}

        # Clear active filters when switching tasks
        filters = []
        grid = dual_study_grid(ids, tags)
        info_buttons = get_filter_buttons(dropdown1_value, get_all_labels(dropdown1_value)) + \
            get_filter_buttons(
                dropdown2_value, get_all_labels(dropdown2_value))
        return "", graph, pie_fig, bar_fig, filters, info_buttons, grid

# =====================================================
# CSV Download
# =====================================================


def register_download_csv_callback(app):

    @app.callback(
        Output("download-csv", "data"),
        Input("download-csv-button", "n_clicks"),
        State("filtered-study-ids", "data"),
        State("filter-tags", "data"),
        prevent_initial_call=True,
    )
    @log_time
    def download_csv(n_clicks, filtered_ids, tags):
        if not n_clicks:
            return no_update

        current_data_time = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")

        studies = get_studies_details(
            ids=filtered_ids if filtered_ids else [],
            start_row=0,
            end_row=len(filtered_ids) if filtered_ids else None,
            tags=tags,
        )

        if not studies:
            return no_update

        refactored_data = []
        tasks = set(
            t['task']
            for study in studies
            for t in study.get('tags', [])
        )

        for study in studies:
            study_data = study.copy()
            tag_list = study_data.pop('tags', [])

            # Initialize empty columns per task
            for task in tasks:
                study_data[task] = []

            for tag in tag_list:
                study_data[tag['task']].append(tag['label'])

            # Convert lists to comma-separated strings
            for task in tasks:
                study_data[task] = ", ".join(study_data[task])

            refactored_data.append(study_data)

        df = pd.DataFrame(refactored_data)

        # Remove abstract column due to legal reasons
        if 'abstract' in df.columns:
            df.drop(columns=['abstract'], inplace=True)

        return dcc.send_data_frame(
            df.to_csv,
            f"psynamic_data_{current_data_time}.csv",
            index=False,
        )

# =====================================================
# Filtering
# =====================================================


def register_filter_callback(app):

    @app.callback(
        Output("checkbox-container", "children"),
        Input("task-dropdown", "value"),
        State("filter-store", "data"),
        prevent_initial_call=False,
    )
    def update_checkboxes(selected_task, current_filters):
        if not selected_task:
            return ""

        current_filters = current_filters or {}
        # Fetch labels at runtime to avoid relying on module-level cached `filter_data`
        labels = get_all_labels(selected_task)
        checked_labels = current_filters.get(selected_task, [])

        return dbc.Checklist(
            options=[{"label": label, "value": label} for label in labels],
            id="label-checklist",
            inline=True,
            value=checked_labels,
        )

    @app.callback(
        Output("selected-filters", "children"),
        Output("filter-store", "data"),
        Output("filtered-study-ids", "data"),
        Output("filter-tags", "data"),
        Output("label-checklist", "value"),
        Input("add-filter-btn", "n_clicks"),
        Input({'type': 'filter-button', 'task': ALL, 'label': ALL}, 'n_clicks'),
        State("task-dropdown", "value"),
        State("label-checklist", "value"),
        State("filter-store", "data"),
        prevent_initial_call=True,
    )
    @log_time
    def modify_filter(add_clicks, remove_clicks, selected_task, selected_labels, current_filters):

        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update, no_update

        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        current_filters = (current_filters or {}).copy()

        # -----------------------------
        # ADD FILTER
        # -----------------------------
        if triggered_id == "add-filter-btn":
            if not selected_task or not selected_labels:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    selected_labels,
                )

            current_filters[selected_task] = selected_labels

        # -----------------------------
        # REMOVE FILTER
        # -----------------------------
        else:
            button_data = json.loads(triggered_id)
            task = button_data['task']
            label = button_data['label']

            if task in current_filters and label in current_filters[task]:
                current_filters[task].remove(label)
                if not current_filters[task]:
                    del current_filters[task]

            selected_labels = [
                l for l in (selected_labels or [])
                if l != label
            ]

        # -----------------------------
        # Rebuild UI + IDs
        # -----------------------------
        ordered_tags = get_tags(current_filters)

        filter_buttons = [
            filter_button(tag['color'], tag['label'],
                          tag['task'], editable=True)
            for task in ordered_tags
            for tag in ordered_tags[task]
        ]

        filtered_ids = get_filtered_study_ids(current_filters)

        return (
            filter_buttons,
            current_filters,
            filtered_ids,
            current_filters,
            selected_labels,
        )

# =====================================================
# Pagination
# =====================================================


def register_pagination_callbacks(app):

    @app.callback(
        Output({"type": "studies-grid", "index": ALL}, "getRowsResponse"),
        Output('count-filtered', 'children', allow_duplicate=True),
        Input({"type": "studies-grid", "index": ALL}, "getRowsRequest"),
        Input("filter-tags", "data"),
        State("filtered-study-ids", "data"),
        prevent_initial_call=True
    )
    @log_time
    def fetch_studies_infinite(requests, tags, filtered_ids):
        if not requests:
            return no_update, no_update

        responses = []
        row_count = len(filtered_ids) if filtered_ids else nr_studies()

        for request in requests:
            if request is None:
                responses.append({"rowData": [], "rowCount": row_count})
                continue

            studies = get_studies_details(
                ids=filtered_ids if filtered_ids else [],
                start_row=request["startRow"],
                end_row=request["endRow"],
                sort_model=request.get(
                    "sortModel", [{"colId": "year", "sort": "desc"}]),
                filter_model=request.get("filterModel", {}),
                tags=tags
            )

            if not studies:
                row_count = 0

            responses.append({
                "rowData": studies,
                "rowCount": row_count
            })

        return responses, row_count


# =====================================================
# Dosage Pagination
# =====================================================

def register_pagination_dosages_callbacks(app):

    @app.callback(
        Output('dosage-study-grid', "getRowsResponse"),
        Output('count-filtered', 'children', allow_duplicate=True),
        Input('dosage-study-grid', "getRowsRequest"),
        Input("filter-tags", "data"),
        State("filtered-study-ids", "data"),
        prevent_initial_call=True
    )
    @log_time
    def fetch_dosage_studies(request, tags, filtered_ids):
        if not request:
            return no_update, no_update

        logging.debug(f"Dosage grid request: {request}")

        studies = get_studies_details_ner(
            ids=filtered_ids if filtered_ids else [],
            start_row=request["startRow"],
            end_row=request["endRow"],
            sort_model=request.get(
                "sortModel", [{"colId": "year", "sort": "desc"}]),
            filter_model=request.get("filterModel", {}),
            tags=tags
        )

        row_count = len(filtered_ids) if filtered_ids else nr_studies()
        if not studies:
            row_count = 0

        return {"rowData": studies, "rowCount": row_count}, row_count


# =====================================================
# Modals
# =====================================================

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


def register_modal_callbacks(app):

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


def register_search_callbacks(app):
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
        prevent_initial_call=True,
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

        details = _build_paper_details(paper, tags_component=tag_buttons)
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
        prevent_initial_call=True,
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
                return "", ""
            paper_id = int(study_ids[0])
        except Exception:
            return "", ""

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

        details = _build_paper_details(paper, tags_component=tag_buttons)

        # hide the search results when showing details
        return details, "", hidden_results_style
