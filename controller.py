import json

import astropy.time
import dash
import pandas as pd
from dash.dependencies import Input, Output, State
from dash import dcc, ctx, ALL

import os
from os.path import basename
from zipfile import ZipFile

from app import app
from antenna_table import make_antenna_table
from feed_table import make_feed_table
from utils import *
from utils import run_efrat, write_observer_schedule, write_operator_schedule, write_stop, write_at_rmall, write_at_job, \
    generate_observer_entry_body, generate_observer_entry_head, generate_skip_observer_entry, \
    generate_observer_transit_entry

print("controller enters")


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


@dash.callback(
    output=[
        Output('table-container-culminations', 'children'),
        Output('table-container-feed', 'children'),
        Output('job-summary', 'children'),
        Output('run-csmake', 'disabled'),
        Output('load-csi', 'disabled'),
        Output('load-track', 'disabled'),
        Output('obs-table', 'data'),
        Output('feed-table', 'data'),
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
        State('obs-table', 'data'),
        State('feed-table', 'data'),
    ],
    background=True,
    progress=[Output('modal-progress', 'is_open'), Output('update-progress', 'value'),
              Output('update-progress', 'max')],
)
def recalculate_culminations(set_progress, object_name: str, ra: str, dec: str, azimuths: str, begin_time: str,
                             end_time: str, use_solar_object: int, solar_object_name: str, solar_ref_time: str,
                             solar_lon: int, solar_lat: int,
                             aperture, retract, before, after, track, std,
                             tcc, js, rc, lc, tfd, json_antenna, json_feed):
    set_progress((True, 100, 100))

    trigger = ctx.triggered_id

    antenna_table = None
    if json_antenna and not trigger == 'azimuths':
        antenna_table = pd.read_json(json_antenna[1:-1], orient='split')

    try:
        if trigger.type in ['aperture', 'retract', 'before', 'after', 'track']:
            exec(f'antenna_table["{trigger.type}"] = {trigger.type}')
            set_progress((False, 100, 100))
            return tcc, js, rc, lc, tfd, "'" + antenna_table.to_json(date_format='iso', orient='split') + "'"
        elif trigger.type == 'std':
            antenna_table['std'] = std
    except AttributeError:
        pass

    feed_table = None
    if json_feed and not trigger == 'azimuths':
        feed_table = pd.read_json(json_feed[1:-1], orient='split')

    try:
        azimuths_ = azimuths.replace(',', ' ').split()
        az = '\n'.join(map(lambda x: f'{int(x):.4f}', azimuths_))

        begin_datetime = datetime.fromisoformat(begin_time)
        end_datetime = datetime.fromisoformat(end_time)

        date_utc = datetime.fromisoformat(begin_time).strftime('%Y%m%d')
        n = (end_datetime - begin_datetime).days + 2

        if n > 10:
            raise ValueError

        dont_use_config = True

        if object_name in PLANETS:
            # Убираем [] из названия объекта
            object_name_ = object_name[1:-1]
            s = get_efrat_job_object(object_name_, az, date_utc, str(n))

        else:
            ra = ra.replace('h', '').replace('m', '').replace('s', '')
            dec = dec.replace('d', '').replace('m', '').replace('s', '')
            s = get_efrat_job_stellar(object_name, ra, dec, az, date_utc, str(n))

        efrat_strings = run_efrat(s)
        for e in efrat_strings:
            print(e)

        table_num = []
        for i, el in enumerate(efrat_strings[:-1]):
            standard = 0
            try:
                standard = antenna_table['std'].iloc[i]
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
                    standard = antenna_table['std'].iloc[i]
                except (AttributeError, IndexError, TypeError):
                    pass
                table_row = fill_table_string_from_efrat(i, efrat_strings[0], begin_datetime, end_datetime,
                                                         standard, dont_use_config)

                if table_row:
                    mod_table_num.append(table_row)

            table_num = mod_table_num

        if not table_num:
            raise ValueError

        antenna_table = pd.DataFrame(data=table_num,
                                     columns=['idx', 'azimuth', 'date_time', 'h_per', 'aperture', 'retract', 'before',
                                              'after', 'track', 'a_obj', 'h_obj', 'ra_degrees', 'dec_degrees',
                                              'sid_time_degrees', 'refraction', 'nutation', 'pos_angle_obj',
                                              'pos_angle_diag', 'vad', 'vhd', 'std'])

        json_antenna_out = "'" + antenna_table.to_json(date_format='iso', orient='split') + "'"

        if feed_table is not None:
            feed_table['azimuth'] = antenna_table['azimuth']
            feed_table['date_time'] = antenna_table['date_time']
        else:
            feed_table = antenna_table[['idx', 'azimuth', 'date_time']]
            feed_table['resolution'] = ['3.9 МГц'] * feed_table.shape[0]
            feed_table['attenuation'] = [DEFAULT_ATTENUATION] * feed_table.shape[0]
            feed_table['polarization'] = ['Авто'] * feed_table.shape[0]
            feed_table['regstart'] = antenna_table['before'] - 0.1
            feed_table['regstop'] = antenna_table['after'] - 0.1
            feed_table['carriagepos'] = [DEFAULT_CARRIAGEPOS] * feed_table.shape[0]

        json_feed_out = "'" + feed_table.to_json(date_format='iso', orient='split') + "'"

        is_sun = (object_name == '[Sun]')
        antenna_html_table = make_antenna_table(antenna_table, DEFAULT_BEFORE, DEFAULT_AFTER, is_sun, use_solar_object)
        feed_html_table = make_feed_table(feed_table, DEFAULT_ATTENUATION, DEFAULT_REGSTART, DEFAULT_REGSTOP, DEFAULT_CARRIAGEPOS)

        object_label = make_object_label(object_name, use_solar_object, solar_object_name)
        return antenna_html_table, feed_html_table, \
            f'{object_label}: {begin_datetime.strftime("%Y-%m-%d %H:%M:%S")} — ' \
            f'{end_datetime.strftime("%Y-%m-%d %H:%M:%S")}', \
            False, False, False, json_antenna_out, json_feed_out

    except (TypeError, ValueError, AttributeError) as ex:
        print('recalculate_culminations exception:', ex)
        return None, None, '&nbsp;', True, True, True, None, None
    finally:
        set_progress((False, 100, 100))


@app.callback(
    Output({'type': 'aperture-value-all', 'index': '0'}, "label"),
    Input({'type': 'aperture-value-all:item', 'index': '0', 'val': '167'}, "n_clicks"),
    Input({'type': 'aperture-value-all:item', 'index': '0', 'val': '61'}, "n_clicks"),
    Input({'type': 'aperture-value-all:item', 'index': '0', 'val': '51'}, "n_clicks"),
    Input({'type': 'aperture-value-all:item', 'index': '0', 'val': '41'}, "n_clicks"),
)
def update_aperture_value(i1, i2, i3, i4):
    trigger_id = ctx.triggered_id
    if not trigger_id:
        raise PreventUpdate
    if trigger_id.val in ['167', '61', '51', '41']:
        return trigger_id.val
    else:
        raise PreventUpdate


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
    Output({'type': 'aperture', 'index': ALL}, "label"),
    Input({'type': 'aperture:item', 'index': ALL, 'val': '167'}, "n_clicks"),
    Input({'type': 'aperture:item', 'index': ALL, 'val': '61'}, "n_clicks"),
    Input({'type': 'aperture:item', 'index': ALL, 'val': '51'}, "n_clicks"),
    Input({'type': 'aperture:item', 'index': ALL, 'val': '41'}, "n_clicks"),
    Input('aperture-set-all', 'n_clicks'),
    State({'type': 'aperture', 'index': ALL}, "id"),
    State({'type': 'aperture', 'index': ALL}, "label"),
    State({'type': 'aperture-value-all', 'index': '0'}, 'label'),
)
def aperture_value_set_all_onclick(i1, i2, i3, i4, n, ids, labels, v):
    trigger = ctx.triggered_id
    if not trigger:
        raise PreventUpdate
    if trigger == 'aperture-set-all':
        return [v] * len(labels)
    elif trigger.val in ['167', '61', '51', '41']:
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
    State({'type': 'track', 'index': ALL}, 'value')
)
def std_set_all_onclick(n1, n2, cbs):
    if ctx.triggered_id == 'std-set-all':
        return [True] * len(cbs)
    elif ctx.triggered_id == 'std-reset-all':
        return [False] * len(cbs)
    else:
        raise PreventUpdate


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


@app.callback(
    Output('csi-sink', 'children'),
    Input('run-csmake', 'n_clicks'),
    State('job-name', 'value'),
    State('stellar-name', 'value'),
    State('use-solar-object', 'value'),
    State('solar-object-name', 'value'),
    State('obs-table', 'data'),
    prevent_initial_call=True
)
def run_csmake_onclick(n, job_name, object_name, use_solar_object, solar_object_name, json_data):
    if ctx.triggered_id == 'run-csmake':
        pd_table = pd.read_json(json_data[1:-1], orient='split')
        object_label = make_object_label(object_name, use_solar_object, solar_object_name)
        m, f = get_csmakes_result(job_name, object_label, pd_table)
        return dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle('csmake и csmake2')),
            dbc.ModalBody([html.Div([html.P(x, style={'margin': '0'}) for x in m.split('\n')],
                                    style={'margin-bottom': '2em'}),
                           html.Div([html.P(x, style={'margin': '0'}) for x in f.split('\n')])]),
            dbc.ModalFooter(html.Button('Закрыть', id='csmake_close', className='btn btn-primary btn-sm"',
                                        style={'height': '30.833px', 'padding-top': '0', 'padding-bottom': '0'},
                                        autoFocus='autofocus'))
        ], id='modal_csmake', is_open=True, scrollable=True)


@app.callback(
    Output('dcc-download-csi', 'data'),
    Input('load-csi', 'n_clicks'),
    State('job-name', 'value'),
    State('stellar-name', 'value'),
    State('use-solar-object', 'value'),
    State('solar-object-name', 'value'),
    State('obs-table', 'data'),
    prevent_initial_call=True
)
def load_csi_onclick(n, job_name, object_name, use_solar_object, solar_object_name, json_data):
    pd_table = pd.read_json(json_data[1:-1], orient='split')
    object_label = make_object_label(object_name, use_solar_object, solar_object_name)

    if (pd_table is None) or (not ctx.triggered_id == 'load-csi'):
        raise PreventUpdate

    with tempfile.TemporaryDirectory() as dir_name:
        run_csmakes(dir_name, job_name, object_label, pd_table)
        downloads_list = [f'{job_name}c.csi', f'{job_name}f.csi']
        lst_list = [f'{job_name}c.lst', f'{job_name}f.lst']

        for fn in lst_list:
            if os.path.exists(f'{dir_name}/{fn}'):
                downloads_list.append(fn)

        arch_name = f'{job_name}_antenna'
        zip_name = f'{dir_name}/{arch_name}.zip'
        with ZipFile(zip_name, 'w') as zip_obj:
            for fn in downloads_list:
                file_path = f'{dir_name}/{fn}'
                zip_obj.write(file_path, f'{arch_name}/{basename(file_path)}')

        return dcc.send_file(zip_name)


@app.callback(
    Output('dcc-download-motion', 'data'),
    Input('load-track', 'n_clicks'),
    State('tracking-300rpm-s', 'value'),
    State('tracking-start', 'value'),
    State('tracking-correction', 'value'),
    State('stellar-name', 'value'),
    State('job-name', 'value'),
    State('use-solar-object', 'value'),
    State('solar-object-name', 'value'),
    State('obs-table', 'data'),
    prevent_initial_call=True
)
def load_track_onclick(n: int, s_per_degree_at_300: float, start_position: str, correction: float,
                       object_name: str, job_name: str, use_solar_object, solar_object_name, json_data):
    pd_table = pd.read_json(json_data[1:-1], orient='split')
    object_label = make_object_label(object_name, use_solar_object, solar_object_name)

    at_job: str = ''
    json_job = '['
    observer_schedule: str = ''
    operator_schedule: str = ''

    first_item = True
    json_jobs = []
    for (_, azimuth, date_time, h_per, aperture, retract, before, after, track, a_obj, h_obj, vad, vhd, dec_degrees,
         p_diag, ra_degrees, sid_time_degrees) \
            in pd_table[['azimuth', 'date_time', 'h_per', 'aperture', 'retract', 'before', 'after', 'track', 'a_obj',
                         'h_obj', 'vad', 'vhd', 'dec_degrees', 'pos_angle_diag', 'ra_degrees',
                         'sid_time_degrees']].itertuples():

        s_per_degree, rpm = calculate_rpm(a_obj=a_obj, h_obj=h_obj, dec_degrees=dec_degrees,
                                          seconds_per_degree300=s_per_degree_at_300, ra_degrees=ra_degrees,
                                          sid_time_degrees=sid_time_degrees)

        culmination: datetime = date_time
        culm_plus_two: datetime = culmination - 2 * s_per_degree
        culm_plus_one: datetime = culmination - s_per_degree
        culm_minus_one: datetime = culmination + s_per_degree

        az_p2 = f'{int(float(azimuth) + 2):+03}'
        az_p1 = f'{int(float(azimuth) + 1):+03}'
        az_m1 = f'{int(float(azimuth) - 1):+03}'

        if not track:
            obs_start: datetime = culmination + timedelta(minutes=-4)
            rolling_start: datetime = culmination + timedelta(minutes=4) + timedelta(seconds=3)
            at_motion_entry = ''
            operator_entry = generate_operator_entry(azimuth, start_time=obs_start, rolling_start=rolling_start)
            observer_entry = generate_observer_transit_entry(azimuth, culmination, obs_start, rolling_start)

        else:
            rolling_start: datetime = culmination + timedelta(minutes=after) + timedelta(seconds=5)

            if start_position == '1':
                at_motion_entry, json_motion_entry = generate_motion_entry(azimuth, start_time=culm_plus_one,
                                                                           stop_time=culm_minus_one,
                                                                           speed=rpm, culmination=culmination)
                operator_entry = generate_operator_entry(az_p1, culm_plus_one, rolling_start)
                observer_entry = generate_skip_observer_entry(az_p2, culm_plus_two)
            elif start_position == '2':
                at_motion_entry, json_motion_entry = generate_motion_entry(azimuth, start_time=culm_plus_two,
                                                                           stop_time=culm_minus_one,
                                                                           speed=rpm, culmination=culmination)
                operator_entry = generate_operator_entry(az_p2, culm_plus_two, rolling_start)
                observer_entry = generate_observer_entry_head(az_p2, culm_plus_two)
            else:
                raise ValueError

            json_dict = {
                'comment': f'azimuth {azimuth}, culmination {culmination}',
                'setup': True,
                'cabin_motion': {
                    'profile': [json_motion_entry]
                }
            }
            json_jobs.append(json_dict)

            observer_entry += generate_observer_entry_body(after, az_m1, az_p1, azimuth, culm_minus_one, culm_plus_one,
                                                           culmination, rpm)

        at_job += at_motion_entry
        operator_schedule += operator_entry
        observer_schedule += observer_entry

    with tempfile.TemporaryDirectory() as dir_name:
        with open(f'{dir_name}/modifications.json', 'w') as f:
            json.dump(json_jobs, f, indent=2)
        write_at_job(at_job, object_label, pd_table, dir_name)
        write_at_rmall(dir_name)
        write_stop(dir_name)
        write_operator_schedule(operator_schedule, object_label, pd_table, dir_name)
        write_observer_schedule(observer_schedule, object_label, pd_table, dir_name)

        arch_name = f'{job_name}_track'
        zip_name = f'{dir_name}/{arch_name}.zip'
        with ZipFile(zip_name, 'w') as zip_obj:
            file_list = ['at_job', 'at_rmall', 'stop', 'operator.txt', 'observer.txt', 'modifications.json']
            for el in file_list:
                file_path = f'{dir_name}/{el}'
                zip_obj.write(file_path, f'{arch_name}/{basename(file_path)}')

        return dcc.send_file(zip_name)
