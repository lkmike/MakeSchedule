from datetime import date, datetime, timedelta

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import dcc, ctx, ALL

from app import app

from utils import PLANETS, stellar_presets


@app.callback(
    Output('stellar-ra', 'value'),
    Output('stellar-dec', 'value'),
    Output('stellar-name', 'value'),
    Input('stellar-source', 'value'),
    Input('stellar-source-submit-button', 'n_clicks')
)
def source_onclick(v, n):
    if v and ctx.triggered_id == 'stellar-source-submit-button':
        if v in PLANETS:
            return '', '', v
        else:
            coords = list(stellar_presets.values())[int(v) - 1]
            return coords['ra'], coords['dec'], coords['name']
    else:
        raise PreventUpdate


@app.callback(
    Output('aia-datetime-input', 'value'),
    Input('aia-datetime-now-button', 'n_clicks'),
    Input('aia-datetime-midnight-button', 'n_clicks')
)
def aia_datetime_onclick(n1, n2):
    if 'aia-datetime-now-button' == ctx.triggered_id:
        return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    elif 'aia-datetime-midnight-button' == ctx.triggered_id:
        return date.today().strftime('%Y-%m-%dT%H:%M:%S')


@app.callback(
    Output('schedule-begin-datetime-input', 'value'),
    Input('schedule-begin-date-today-button', 'n_clicks'),
    Input('schedule-begin-date-tomorrow-button', 'n_clicks'), prevent_initial_call=True
)
def schedule_begin_onclick(n1, n2):
    if 'schedule-begin-date-today-button' == ctx.triggered_id:
        return (date.today()).strftime('%Y-%m-%dT%H:%M:%S')
    elif 'schedule-begin-date-tomorrow-button' == ctx.triggered_id:
        return (datetime.fromisoformat(f"{date.today().strftime('%Y-%m-%d')}")
                + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S')


@app.callback(
    Output('schedule-end-datetime-input', 'value'),
    Input('schedule-end-date-today-button', 'n_clicks'),
    Input('schedule-end-date-tomorrow-button', 'n_clicks'), prevent_initial_call=True
)
def schedule_end_onclick(n1, n2):
    if 'schedule-end-date-today-button' == ctx.triggered_id:
        return (datetime.fromisoformat(f"{date.today().strftime('%Y-%m-%d')}")
                + timedelta(hours=23, minutes=59)).strftime('%Y-%m-%dT%H:%M:%S')
    elif 'schedule-end-date-tomorrow-button' == ctx.triggered_id:
        return (datetime.fromisoformat(f"{date.today().strftime('%Y-%m-%d')}")
                + timedelta(days=1, hours=23, minutes=59)).strftime('%Y-%m-%dT%H:%M:%S')


@app.callback(
    Output('azimuths', 'value'),
    Input('azimuths-12-button', 'n_clicks'),
    Input('azimuths-4-button', 'n_clicks'),
    Input('azimuths-2-button', 'n_clicks'),
    Input('azimuths-1-button', 'n_clicks'), prevent_initial_call=True
)
def azimuth_set_onclick(n1, n2, n3, n4):
    if 'azimuths-1-button' == ctx.triggered_id:
        return str(list(map(lambda x: f'{x:+}', list(range(30, -31, -1))))).replace("'", '')[1:-1]
    elif 'azimuths-2-button' == ctx.triggered_id:
        return str(list(map(lambda x: f'{x:+}', list(range(30, -31, -2))))).replace("'", '')[1:-1]
    elif 'azimuths-4-button' == ctx.triggered_id:
        return str(list(map(lambda x: f'{x:+}', list(range(28, -29, -4))))).replace("'", '')[1:-1]
    elif 'azimuths-12-button' == ctx.triggered_id:
        return str(list(map(lambda x: f'{x:+}', list(range(24, -25, -12))))).replace("'", '')[1:-1]


@app.callback(
    Output('job-name', 'value'),
    Input('schedule-begin-datetime-input', 'value'),
)
def make_file_base_name(v):
    month_lookup = {1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: 'a', 11: 'b', 12: 'c'}
    try:
        dt: datetime = datetime.fromisoformat(v)
    except TypeError:
        return None
    return f'{str(dt.year)[-1]}{month_lookup[dt.month]}{dt.day:02}x'


@app.callback(
    Output("modal_csmake", "is_open"),
    Input("csmake_close", "n_clicks"), prevent_initial_call=True
)
def modal_csmake_close_onclick(n):
    if n:
        return False


@app.callback(
    Output('use-solar-object', 'disabled'),
    Input('stellar-name', 'value'),
)
def enable_solar_point(source_name: str):
    return not (source_name == '[Sun]')


@app.callback(
    Output('solar-object-name', 'disabled'),
    Output('solar-ref-time', 'disabled'),
    Output('solar-lon', 'disabled'),
    Output('solar-lat', 'disabled'),
    Input('use-solar-object', 'value'),
)
def use_solar_point(disabled: int):
    return [not bool(disabled)] * 4


