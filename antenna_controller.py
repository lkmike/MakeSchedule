from app import app

import pandas as pd
from datetime import datetime
import astropy
import dash
from dash import ctx
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate

from utils import make_object_label, get_efrat_job_stellar, get_efrat_job_object, \
    run_efrat, fill_table_string_from_efrat, get_rolled_point_ra_dec
from defaults import MAX_DAYS, TIMEZONE, PLANETS

from antenna_table import make_antenna_html_table, APERTURES


@app.callback(
    Output({'type': 'aperture-value-all', 'index': '0'}, "label"),
    list(map(lambda x: Input({'type': 'aperture-value-all:item', 'index': '0', 'val': x}, "n_clicks"), APERTURES)),
)
def update_aperture_value(*inputs):
    trigger_id = ctx.triggered_id
    if not trigger_id:
        raise PreventUpdate
    if trigger_id.val in APERTURES:
        return trigger_id.val
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'aperture', 'index': ALL}, "label"),
    list(map(lambda x: Input({'type': 'aperture:item', 'index': ALL, 'val': x}, "n_clicks"), APERTURES)) +
    [Input('aperture-set-all', 'n_clicks')],
    State({'type': 'aperture', 'index': ALL}, "id"),
    State({'type': 'aperture', 'index': ALL}, "label"),
    State({'type': 'aperture-value-all', 'index': '0'}, 'label'),
)
def aperture_value_set_all_onclick(*inputs):
    ids, labels, v = inputs[-3:]
    trigger = ctx.triggered_id
    if not trigger:
        raise PreventUpdate
    if trigger == 'aperture-set-all':
        return [v] * len(labels)
    elif trigger.val in APERTURES:
        id_indices = [e['index'] for e in ids]
        labels_dict = dict(zip(id_indices, labels))
        labels_dict[trigger.index] = trigger.val
        return list(labels_dict.values())
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'before', 'index': ALL}, 'value'),
    Input('before-set-all', 'n_clicks'),
    State('before-value-all', 'value'),
    State({'type': 'before', 'index': ALL}, 'value')
)
def before_set_all_onclick(n1, v, cbs):
    if ctx.triggered_id == 'before-set-all':
        return [v] * len(cbs)
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'after', 'index': ALL}, 'value'),
    Input('after-set-all', 'n_clicks'),
    State('after-value-all', 'value'),
    State({'type': 'after', 'index': ALL}, 'value')
)
def after_set_all_onclick(n1, v, cbs):
    if ctx.triggered_id == 'after-set-all':
        return [v] * len(cbs)
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'retract', 'index': ALL}, 'value'),
    Input('retract-set-all', 'n_clicks'),
    Input('retract-reset-all', 'n_clicks'),
    State({'type': 'retract', 'index': ALL}, 'value')
)
def retract_set_all_onclick(n1, n2, cbs):
    if ctx.triggered_id == 'retract-set-all':
        return [True] * len(cbs)
    elif ctx.triggered_id == 'retract-reset-all':
        return [False] * len(cbs)
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'track', 'index': ALL}, 'value'),
    Input('track-set-all', 'n_clicks'),
    Input('track-reset-all', 'n_clicks'),
    State({'type': 'track', 'index': ALL}, 'value')
)
def track_set_all_onclick(n1, n2, cbs):
    if ctx.triggered_id == 'track-set-all':
        return [True] * len(cbs)
    elif ctx.triggered_id == 'track-reset-all':
        return [False] * len(cbs)
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'std', 'index': ALL}, 'value'),
    Input('std-set-all', 'n_clicks'),
    Input('std-reset-all', 'n_clicks'),
    State({'type': 'std', 'index': ALL}, 'value')
)
def std_set_all_onclick(n1, n2, cbs):
    if ctx.triggered_id == 'std-set-all':
        return [True] * len(cbs)
    elif ctx.triggered_id == 'std-reset-all':
        return [False] * len(cbs)
    else:
        raise PreventUpdate


@dash.callback(
    output=[
        Output('table-container-culminations', 'children'),
        Output('job-summary', 'children'),
        Output('run-csmake', 'disabled'),
        Output('load-csi', 'disabled'),
        Output('load-track', 'disabled'),
        Output('antenna-table', 'data'),
    ],
    inputs=[
        Input('stellar-name', 'value'),
        Input('stellar-ra', 'value'),
        Input('stellar-dec', 'value'),
        Input('azimuths', 'value'),
        Input('schedule-begin-datetime-input', 'value'),
        Input('schedule-end-datetime-input', 'value'),
        Input('use-solar-object', 'value'),
        Input('solar-object-name', 'value'),
        Input('solar-ref-time', 'value'),
        Input('solar-lon', 'value'),
        Input('solar-lat', 'value'),
        Input({'type': 'aperture', 'index': ALL}, "label"),
        Input({'type': 'retract', 'index': ALL}, 'value'),
        Input({'type': 'before', 'index': ALL}, 'value'),
        Input({'type': 'after', 'index': ALL}, 'value'),
        Input({'type': 'track', 'index': ALL}, 'value'),
        Input({'type': 'std', 'index': ALL}, 'value'),
    ],
    state=[
        State('table-container-culminations', 'children'),
        State('job-summary', 'children'),
        State('run-csmake', 'disabled'),
        State('load-csi', 'disabled'),
        State('load-track', 'disabled'),
        State('antenna-table', 'data'),
    ],
    background=True,
    progress=[Output('modal-progress', 'is_open'), Output('update-progress', 'value'),
              Output('update-progress', 'max')],
)
def recalculate_culminations(set_progress, object_name: str, ra: str, dec: str, azimuths: str, begin_time: str,
                             end_time: str, use_solar_object: int, solar_object_name: str, solar_ref_time: str,
                             solar_lon: int, solar_lat: int,
                             aperture, retract, before, after, track, std,
                             old_antenna_table, old_job_summary, old_run_csmake_state, old_load_csi_state,
                             old_load_track_state,
                             json_data,
                             ):
    set_progress((True, 100, 100))

    trigger = ctx.triggered_id

    row_updates = ['aperture', 'retract', 'before', 'after', 'track', 'std']

    df = None
    if json_data:
        df = pd.read_json(json_data[1:-1], orient='split')

    # Изменение состояния std приводит к пересчету кульминации, всё остальное не требует
    # запуска ефрата по новой
    if hasattr(trigger, 'type') and trigger.type in row_updates and df is not None:
        if trigger.type in ['aperture', 'retract', 'before', 'after', 'track']:
            exec(f'df["{trigger.type}"] = {trigger.type}')
            set_progress((False, 100, 100))
            return old_antenna_table, old_job_summary, old_run_csmake_state, old_load_csi_state, old_load_track_state, \
                "'" + df.to_json(date_format='iso', orient='split') + "'"
        elif trigger.type == 'std':
            df['std'] = std

    try:
        azimuths_ = azimuths.replace(',', ' ').split()
        az = '\n'.join(map(lambda x: f'{int(x):.4f}', azimuths_))

        begin_datetime = datetime.fromisoformat(begin_time)
        end_datetime = datetime.fromisoformat(end_time)

        date_utc = datetime.fromisoformat(begin_time).strftime('%Y%m%d')
        n = (end_datetime - begin_datetime).days + 2

        if n > MAX_DAYS:
            raise ValueError

        dont_use_config = True

        if object_name in PLANETS:
            # Убираем [] из названия объекта
            object_name_ = object_name[1:-1]
            s = get_efrat_job_object(object_name_, az, date_utc, str(n))
        else:
            ra = ra.replace('h', '').replace('m', '').replace('s', '').replace(' ', '')
            dec = dec.replace('d', '').replace('m', '').replace('s', '').replace(' ', '')
            s = get_efrat_job_stellar(object_name, ra, dec, az, date_utc, str(n))

        efrat_strings = run_efrat(s)
        # for e in efrat_strings:
        #     print(e)

        table_num = []
        for i, el in enumerate(efrat_strings[:-1]):
            standard = 0
            try:
                standard = df['std'].iloc[i]
            except (AttributeError, IndexError, TypeError):
                pass
            table_row = fill_table_string_from_efrat(i, el, begin_datetime, end_datetime, standard, dont_use_config)
            if table_row:
                table_num.append(table_row)

        if object_name == '[Sun]' and bool(use_solar_object):
            object_label = make_object_label(object_name, use_solar_object, solar_object_name)

            ref_point = [float(solar_lon), float(solar_lat)]
            ref_time = astropy.time.Time(datetime.fromisoformat(solar_ref_time))

            mod_table_num = []
            for i, el in enumerate(table_num):
                if el[20] == 1:
                    mod_table_num.append(el)
                    continue

                el_time_utc = el[2].astimezone(TIMEZONE)
                el_time_astropy = astropy.time.Time(el_time_utc)
                el_ra, el_dec = get_rolled_point_ra_dec(ref_point=ref_point, ref_time=ref_time,
                                                        obs_time=el_time_astropy)
                el_ra = el_ra.replace('h', '').replace('m', '').replace('s', '')
                el_dec = el_dec.replace('d', '').replace('m', '').replace('s', '')
                el_azimuth = f'{float(el[1]):.4f}'

                s = get_efrat_job_stellar(object_label, el_ra, el_dec, el_azimuth, date_utc, '1')
                efrat_strings = run_efrat(s)
                standard = 0
                try:
                    standard = df['std'].iloc[i]
                except (AttributeError, IndexError, TypeError):
                    pass
                table_row = fill_table_string_from_efrat(i, efrat_strings[0], begin_datetime, end_datetime,
                                                         standard, dont_use_config)

                if table_row:
                    mod_table_num.append(table_row)

            table_num = mod_table_num

        if not table_num:
            raise ValueError

        df = pd.DataFrame(data=table_num,
                          columns=['idx', 'azimuth', 'date_time', 'h_per', 'aperture', 'retract', 'before',
                                   'after', 'track', 'a_obj', 'h_obj', 'ra_degrees', 'dec_degrees',
                                   'sid_time_degrees', 'refraction', 'nutation', 'pos_angle_obj',
                                   'pos_angle_diag', 'vad', 'vhd', 'std'])

        json_out = "'" + df.to_json(date_format='iso', orient='split') + "'"

        is_sun = (object_name == '[Sun]')

        html_table = make_antenna_html_table(df, is_sun, use_solar_object)

        object_label = make_object_label(object_name, use_solar_object, solar_object_name)
        return html_table, \
            f'#### {object_label}: {begin_datetime.strftime("%Y-%m-%d %H:%M:%S")} — ' \
            f'{end_datetime.strftime("%Y-%m-%d %H:%M:%S")}', \
            False, False, False, json_out

    except (TypeError, ValueError, AttributeError) as ex:
        print('recalculate_culminations exception:', ex)
        return None, '#### &nbsp;', True, True, True, None
    finally:
        set_progress((False, 100, 100))
