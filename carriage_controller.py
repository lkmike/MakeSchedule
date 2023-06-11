from app import app
from dash import dcc, ctx, ALL
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate


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
