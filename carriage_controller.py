import pandas as pd

from app import app
from dash import dcc, ctx, ALL
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate

from carriage_table import DEFAULT_CARRIAGE_ENABLED, DEFAULT_CARRIAGE_POS, DEFAULT_CARRIAGE_OSCENABLED, \
    DEFAULT_CARRIAGE_AMPLITUDE, DEFAULT_CARRIAGE_SPEED, DEFAULT_CARRIAGE_ACCEL, DEFAULT_CARRIAGE_DECEL, \
    DEFAULT_CARRIAGE_DWELL, make_carriage_html_table


def validate_carmove(value):
    try:
        speed, accel, decel, dwell = map(float, value.split('/'))
    except ValueError:
        return True
    if speed <= 0 or speed > 1000:
        return True
    if accel <= 0 or accel > 1000:
        return True
    if decel <= 0 or decel > 1000:
        return True
    if dwell < 0 or dwell > 1000:
        return True

    return False


app.callback(Output({'type': 'carmove1-value-all', 'index': '0'}, "invalid"),
             Input({'type': 'carmove1-value-all', 'index': '0'}, "value"), )(validate_carmove)

app.callback(Output({'type': 'carmove2-value-all', 'index': '0'}, "invalid"),
             Input({'type': 'carmove2-value-all', 'index': '0'}, "value"), )(validate_carmove)

app.callback(Output({'type': 'carmove1', 'index': '0'}, "invalid"),
             Input({'type': 'carmove1', 'index': '0'}, "value"), )(validate_carmove)

app.callback(Output({'type': 'carmove2', 'index': '0'}, "invalid"),
             Input({'type': 'carmove2', 'index': '0'}, "value"), )(validate_carmove)


@app.callback(
    Output({'type': 'carenabled', 'index': ALL}, 'value'),
    Input('carenabled-set-all', 'n_clicks'),
    Input('carenabled-reset-all', 'n_clicks'),
    State({'type': 'carenabled', 'index': ALL}, 'value')
)
def carenabled_all_onclick(n1, n2, cbs):
    if ctx.triggered_id == 'carenabled-set-all':
        return [True] * len(cbs)
    elif ctx.triggered_id == 'carenabled-reset-all':
        return [False] * len(cbs)
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'oscenabled', 'index': ALL}, 'value'),
    Input('oscenabled-set-all', 'n_clicks'),
    Input('oscenabled-reset-all', 'n_clicks'),
    State({'type': 'oscenabled', 'index': ALL}, 'value')
)
def oscenabled_all_onclick(n1, n2, cbs):
    if ctx.triggered_id == 'oscenabled-set-all':
        return [True] * len(cbs)
    elif ctx.triggered_id == 'oscenabled-reset-all':
        return [False] * len(cbs)
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'carriagepos', 'index': ALL}, 'value'),
    Input('carriagepos-set-all', 'n_clicks'),
    State('carriagepos-value-all', 'value'),
    State({'type': 'carriagepos', 'index': ALL}, 'value')
)
def carriagepos_set_all_onclick(n1, v, cbs):
    if ctx.triggered_id == 'carriagepos-set-all' and v:
        return [v] * len(cbs)
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'amplitude', 'index': ALL}, 'value'),
    Input('amplitude-set-all', 'n_clicks'),
    State('amplitude-value-all', 'value'),
    State({'type': 'amplitude', 'index': ALL}, 'value')
)
def amplitude_set_all_onclick(n1, v, cbs):
    if ctx.triggered_id == 'amplitude-set-all' and v:
        return [v] * len(cbs)
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'carmove1', 'index': ALL}, 'value'),
    Input('carmove1-set-all', 'n_clicks'),
    State({'type': 'carmove1-value-all', 'index': '0'}, 'value'),
    State({'type': 'carmove1-value-all', 'index': '0'}, 'invalid'),
    State({'type': 'carmove1', 'index': ALL}, 'value')
)
def carmove1_set_all_onclick(n1, v, invalid, cbs):
    if ctx.triggered_id == 'carmove1-set-all' and not invalid:
        return [v] * len(cbs)
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'carmove2', 'index': ALL}, 'value'),
    Input('carmove2-set-all', 'n_clicks'),
    State({'type': 'carmove2-value-all', 'index': '0'}, 'value'),
    State({'type': 'carmove2-value-all', 'index': '0'}, 'invalid'),
    State({'type': 'carmove2', 'index': ALL}, 'value')
)
def carmove2_set_all_onclick(n1, v, invalid, cbs):
    if ctx.triggered_id == 'carmove2-set-all' and not invalid:
        return [v] * len(cbs)
    else:
        raise PreventUpdate


@app.callback(
    output=[
        Output('table-container-carriage', 'children'),
        Output('carriage-table', 'data'),
    ],
    inputs=[
        Input({'type': 'carenabled', 'index': ALL}, "label"),
        Input({'type': 'carriagepos', 'index': ALL}, "label"),
        Input({'type': 'oscenabled', 'index': ALL}, "label"),
        Input({'type': 'amplitude', 'index': ALL}, "label"),
        Input({'type': 'carmove1', 'index': ALL}, "label"),
        Input({'type': 'carmove2', 'index': ALL}, "label"),
        Input('antenna-table', 'data')
    ],
    state=[
        State('table-container-carriage', 'children'),
        State('carriage-table', 'data'),
    ],
    prevent_initial_call=True
)
def update_carriage_table(carenabled, carriagepos, oscenabled, amplitude, carmove1, carmove2, json_antenna,
                          existing_table, json_data):
    trigger = ctx.triggered_id
    print(trigger)
    simple_row_updates = ['carenabled', 'carriagepos', 'oscenabled', 'amplitude']
    complex_row_updates = ['carmove1', 'carmove2']
    row_updates = simple_row_updates + complex_row_updates

    df = None
    if json_data:
        df = pd.read_json(json_data[1:-1], orient='split')

    if hasattr(trigger, 'type') and trigger.type in row_updates and df is not None:
        if trigger.type in simple_row_updates:
            exec(f'df["{trigger.type}"] = {trigger.type}')
        elif trigger.type == 'carmove1':
            df.loc[trigger.index, ['speed1', 'accel1', 'decel1', 'dwell1']] = carmove1.split('/')
        elif trigger.type == 'carmove2':
            df.loc[trigger.index, ['speed2', 'accel2', 'decel2', 'dwell2']] = carmove2.split('/')
        return existing_table, "'" + df.to_json(date_format='iso', orient='split') + "'"

    if trigger == 'antenna-table' and json_antenna is not None:
        at = pd.read_json(json_antenna[1:-1], orient='split')
        if df is not None:
            df['azimuth'] = at['azimuth']
            df['date_time'] = at['date_time']
        else:
            df = at[['idx', 'azimuth', 'date_time']].copy()
            df['carenabled'] = [DEFAULT_CARRIAGE_ENABLED] * df.shape[0]
            df['carriagepos'] = [DEFAULT_CARRIAGE_POS] * df.shape[0]
            df['oscenabled'] = [DEFAULT_CARRIAGE_OSCENABLED] * df.shape[0]
            df['amplitude'] = [DEFAULT_CARRIAGE_AMPLITUDE] * df.shape[0]
            df['speed1'] = [DEFAULT_CARRIAGE_SPEED] * df.shape[0]
            df['accel1'] = [DEFAULT_CARRIAGE_ACCEL] * df.shape[0]
            df['decel1'] = [DEFAULT_CARRIAGE_DECEL] * df.shape[0]
            df['dwell1'] = [DEFAULT_CARRIAGE_DWELL] * df.shape[0]
            df['speed2'] = [DEFAULT_CARRIAGE_SPEED] * df.shape[0]
            df['accel2'] = [DEFAULT_CARRIAGE_ACCEL] * df.shape[0]
            df['decel2'] = [DEFAULT_CARRIAGE_DECEL] * df.shape[0]
            df['dwell2'] = [DEFAULT_CARRIAGE_DWELL] * df.shape[0]

        json_out = "'" + df.to_json(date_format='iso', orient='split') + "'"
        html_table = make_carriage_html_table(df)

        return html_table, json_out

    return None, None
