import pandas as pd

from app import app
from dash import dcc, ctx, ALL
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate

from acquisition_table import resolutions, polarizations, DEFAULT_ACQUISITION_RESOLUTION, \
    DEFAULT_ACQUISITION_POLARIZATION, DEFAULT_ACQUISITION_ATTENUATION, make_acquisition_html_table


@app.callback(
    Output({'type': 'resolution-value-all', 'index': '0'}, "label"),
    list(map(lambda x: Input({'type': 'resolution-value-all:item', 'index': '0', 'val': x}, "n_clicks"), resolutions)),
)
def update_resolution_value(*inputs):
    trigger_id = ctx.triggered_id
    if not trigger_id:
        raise PreventUpdate
    if trigger_id.val in resolutions:
        return trigger_id.val
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'resolution', 'index': ALL}, "label"),
    list(map(lambda x: Input({'type': 'resolution:item', 'index': ALL, 'val': x}, "n_clicks"), resolutions)) +
    [Input('resolution-set-all', 'n_clicks')],
    State({'type': 'resolution', 'index': ALL}, "id"),
    State({'type': 'resolution', 'index': ALL}, "label"),
    State({'type': 'resolution-value-all', 'index': '0'}, 'label'),
)
def resolution_value_set_all_onclick(*inputs):
    ids, labels, v = inputs[-3:]
    trigger = ctx.triggered_id
    if not trigger:
        raise PreventUpdate
    if trigger == 'resolution-set-all':
        return [v] * len(labels)
    elif trigger.val in resolutions:
        id_indices = [e['index'] for e in ids]
        labels_dict = dict(zip(id_indices, labels))
        labels_dict[trigger.index] = trigger.val
        return list(labels_dict.values())
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'polarization-value-all', 'index': '0'}, "label"),
    list(map(lambda x: Input({'type': 'polarization-value-all:item', 'index': '0', 'val': x}, "n_clicks"),
             polarizations)),
)
def update_polarization_value(*inputs):
    trigger_id = ctx.triggered_id
    if not trigger_id:
        raise PreventUpdate
    if trigger_id.val in polarizations:
        return trigger_id.val
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'polarization', 'index': ALL}, "label"),
    list(map(lambda x: Input({'type': 'polarization:item', 'index': ALL, 'val': x}, "n_clicks"), polarizations)) +
    [Input('polarization-set-all', 'n_clicks')],
    State({'type': 'polarization', 'index': ALL}, "id"),
    State({'type': 'polarization', 'index': ALL}, "label"),
    State({'type': 'polarization-value-all', 'index': '0'}, 'label'),
)
def polarization_value_set_all_onclick(*inputs):
    ids, labels, v = inputs[-3:]
    trigger = ctx.triggered_id
    if not trigger:
        raise PreventUpdate
    if trigger == 'polarization-set-all':
        return [v] * len(labels)
    elif trigger.val in polarizations:
        id_indices = [e['index'] for e in ids]
        labels_dict = dict(zip(id_indices, labels))
        labels_dict[trigger.index] = trigger.val
        return list(labels_dict.values())
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'attenuation', 'index': ALL}, 'value'),
    Input('attenuation-set-all', 'n_clicks'),
    State('attenuation-value-all', 'value'),
    State({'type': 'attenuation', 'index': ALL}, 'value')
)
def attenuation_set_all_onclick(n1, v, cbs):
    if ctx.triggered_id == 'attenuation-set-all' and v:
        return [v] * len(cbs)
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'regstart', 'index': ALL}, 'value'),
    Input('regstart-set-all', 'n_clicks'),
    State('regstart-value-all', 'value'),
    State({'type': 'regstart', 'index': ALL}, 'value')
)
def regstart_set_all_onclick(n1, v, cbs):
    if ctx.triggered_id == 'regstart-set-all' and v:
        return [v] * len(cbs)
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'regstop', 'index': ALL}, 'value'),
    Input('regstop-set-all', 'n_clicks'),
    State('regstop-value-all', 'value'),
    State({'type': 'regstop', 'index': ALL}, 'value')
)
def regstop_set_all_onclick(n1, v, cbs):
    if ctx.triggered_id == 'regstop-set-all' and v:
        return [v] * len(cbs)
    else:
        raise PreventUpdate


@app.callback(
    output=[
        Output('table-container-acquisition', 'children'),
        Output('acquisition-table', 'data'),
    ],
    inputs=[
        Input({'type': 'resolution', 'index': ALL}, "label"),
        Input({'type': 'attenuation', 'index': ALL}, "label"),
        Input({'type': 'polarization', 'index': ALL}, "label"),
        Input({'type': 'regstart', 'index': ALL}, "label"),
        Input({'type': 'regstop', 'index': ALL}, "label"),
        Input('antenna-table', 'data')
    ],
    state=[
        State('table-container-acquisition', 'children'),
        State('acquisition-table', 'data'),
    ],
    prevent_initial_call=True
)
def update_acquisition_table(resolution, attenuation, polarization, regstart, regstop, json_antenna, existing_table,
                             json_data):
    trigger = ctx.triggered_id
    row_updates = ['resolution', 'attenuation', 'polarization', 'regstart', 'regstop']

    df = None
    if json_data:
        df = pd.read_json(json_data[1:-1], orient='split')

    # Если источник обновления - элемент самой таблицы, сохраняем соответствующий столбец
    # в модель и возвращаем таблицу в том виде, как она есть
    if hasattr(trigger, 'type') and trigger.type in row_updates and df is not None:
        exec(f'df["{trigger.type}"] = {trigger.type}')
        return existing_table, "'" + df.to_json(date_format='iso', orient='split') + "'"

    # Другой вариант - обновление столбцов азимута и даты при пересчете таблицы кульминаций
    if trigger == 'antenna-table' and json_antenna is not None:
        at = pd.read_json(json_antenna[1:-1], orient='split')
        if df is not None:
            df['azimuth'] = at['azimuth']
            df['date_time'] = at['date_time']
        else:
            df = at[['idx', 'azimuth', 'date_time']].copy()
            df['resolution'] = [DEFAULT_ACQUISITION_RESOLUTION] * df.shape[0]
            df['attenuation'] = [DEFAULT_ACQUISITION_ATTENUATION] * df.shape[0]
            df['polarization'] = [DEFAULT_ACQUISITION_POLARIZATION] * df.shape[0]
            df['regstart'] = at['before'] - 0.1
            df['regstop'] = at['after'] - 0.1

        json_out = "'" + df.to_json(date_format='iso', orient='split') + "'"
        html_table = make_acquisition_html_table(df)

        return html_table, json_out

    return None, None
