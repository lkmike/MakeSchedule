from app import app
from dash import dcc, ctx, ALL
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate

import os
from os.path import basename
from zipfile import ZipFile
import json

from utils import *


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
