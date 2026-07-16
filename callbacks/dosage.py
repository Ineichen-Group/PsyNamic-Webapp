
import logging

from dash import ALL, callback_context, no_update
from dash.dependencies import Input, Output, State

from callbacks.utils import log_time
from components.graphs import box_plot_graph
from data.dosage_norm import remove_several_substances_dosages
from data.queries import (get_dosage_samples, get_ids, get_studies_details_ner,
                          nr_studies)
from style.colors import get_color_mapping


def register(app):
    register_pagination_dosages_callbacks(app)
    register_dosage_graph_callbacks(app)


def register_dosage_graph_callbacks(app):
    @app.callback(
        Output('dosage-study-grid', 'getRowsResponse', allow_duplicate=True),
        Output('filtered-study-ids', 'data', allow_duplicate=True),
        Output('count-filtered', 'children', allow_duplicate=True),
        Output({'type': 'dosage-box-plot', 'index': ALL},
               'figure', allow_duplicate=True),
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
            n_graphs = max(len(selectedDatas) if selectedDatas is not None else 0, len(
                clickDatas) if clickDatas is not None else 0)
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
                rest_subs = [
                    s for s in substances if s not in lsd_subs + ibogaine_subs]
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
                cd0 = custom[0] if isinstance(
                    custom, (list, tuple)) else custom
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
        Output('dosage-study-grid', "getRowsResponse"),
        Output('count-filtered', 'children', allow_duplicate=True),
        Input('dosage-study-grid', "getRowsRequest"),
        Input("filter-tags", "data"),
        State("filtered-study-ids", "data"),
        prevent_initial_call='initial_duplicate',
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
