import datetime

import pandas as pd
import numpy as np

from app import app
from dash import dcc, ctx, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import os
from os.path import basename

from datetime import timedelta
from zipfile import ZipFile
import json

import dash_bootstrap_components as dbc

import tempfile

from utils import make_object_label, get_csmakes_result, run_csmakes, calculate_rpm, generate_motion_entry, \
    generate_operator_entry, generate_skip_observer_entry, generate_observer_transit_entry, \
    generate_observer_entry_body, generate_observer_entry_head, feed_offset_to_time, write_at_job, \
    write_operator_schedule, write_observer_schedule, write_stop, write_at_rmall

from defaults import TIMEZONE, DRIVE_TO_CM_SCALE, FAST_FEED_POSITION, resolution_to_avgpts, polarization_to_pol, \
    polarization_to_auto, PULSE_DURATION, SECONDS_BEFORE_OBS_RUN_BEGINS, SECONDS_AFTER_OBS_RUN_ENDS, RUNS_GAP


@app.callback(
    Output('csi-sink', 'children'),
    Input('run-csmake', 'n_clicks'),
    State('job-name', 'value'),
    State('stellar-name', 'value'),
    State('use-solar-object', 'value'),
    State('solar-object-name', 'value'),
    State('antenna-table', 'data'),
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
    State('antenna-table', 'data'),
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
    State('antenna-table', 'data'),
    State('acquisition-table', 'data'),
    State('carriage-table', 'data'),
    prevent_initial_call=True
)
def load_track_onclick(n: int, s_per_degree_at_300: float, start_position: str, correction: float,
                       object_name: str, job_name: str, use_solar_object, solar_object_name, json_antenna,
                       json_acquisition, json_carriage):
    ant_table = pd.read_json(json_antenna[1:-1], orient='split')
    acq_table = pd.read_json(json_acquisition[1:-1], orient='split')
    car_table = pd.read_json(json_carriage[1:-1], orient='split')

    object_label = make_object_label(object_name, use_solar_object, solar_object_name)

    at_job: str = ''
    observer_schedule: str = ''
    operator_schedule: str = ''

    runs = get_continuous_runs(ant_table)

    json_jobs = []
    run_begins = []
    run_ends = []

    common_table = pd.concat(
        [ant_table, acq_table.loc[:, ((acq_table.columns != 'azimuth') & (acq_table.columns != 'date_time'))],
         car_table.loc[:, ((car_table.columns != 'azimuth') & (car_table.columns != 'date_time'))]], axis=1)

    for (idx, azimuth, date_time, h_per, aperture, retract, before, after, track, a_obj, h_obj, vad, vhd, dec_degrees,
         p_diag, ra_degrees, sid_time_degrees, resolution, attenuation, polarization, regstart, regstop, carenabled,
         carriagepos, oscenabled, amplitude, speed1, accel1, decel1, dwell1, speed2, accel2, decel2, dwell2) \
            in common_table[['azimuth', 'date_time', 'h_per', 'aperture', 'retract', 'before', 'after', 'track',
                             'a_obj', 'h_obj', 'vad', 'vhd', 'dec_degrees', 'pos_angle_diag', 'ra_degrees',
                             'sid_time_degrees', 'resolution', 'attenuation', 'polarization', 'regstart', 'regstop',
                             'carenabled', 'carriagepos', 'oscenabled', 'amplitude', 'speed1', 'accel1', 'decel1',
                             'dwell1', 'speed2', 'accel2', 'decel2', 'dwell2']].itertuples():

        s_per_degree, rpm = calculate_rpm(a_obj=a_obj, h_obj=h_obj, dec_degrees=dec_degrees,
                                          seconds_per_degree300=s_per_degree_at_300, ra_degrees=ra_degrees,
                                          sid_time_degrees=sid_time_degrees)

        culmination = date_time
        culm_p2 = culmination - 2 * s_per_degree
        culmination_p1 = culmination - s_per_degree
        culmimnation_m1 = culmination + s_per_degree

        az_p2 = f'{int(float(azimuth) + 2):+03}'
        azimuth_p1 = f'{int(float(azimuth) + 1):+03}'
        azimuth_m1 = f'{int(float(azimuth) - 1):+03}'

        if not track:
            obs_start = culmination + timedelta(minutes=-4)
            rolling_start = culmination + timedelta(minutes=4) + timedelta(seconds=3)
            at_motion_entry = ''
            operator_entry = generate_operator_entry(azimuth, start_time=obs_start, rolling_start=rolling_start)
            observer_entry = generate_observer_transit_entry(azimuth, culmination, obs_start, rolling_start)
            json_motion_entry = {}

        else:
            rolling_start = culmination + timedelta(minutes=after) + timedelta(seconds=5)

            if start_position == '1':
                at_motion_entry, json_motion_entry = generate_motion_entry(azimuth, start_time=culmination_p1,
                                                                           stop_time=culmimnation_m1,
                                                                           speed=rpm, culmination=culmination)
                operator_entry = generate_operator_entry(azimuth_p1, culmination_p1, rolling_start)
                observer_entry = generate_skip_observer_entry(az_p2, culm_p2)
            elif start_position == '2':
                at_motion_entry, json_motion_entry = generate_motion_entry(azimuth, start_time=culm_p2,
                                                                           stop_time=culmimnation_m1,
                                                                           speed=rpm, culmination=culmination)
                operator_entry = generate_operator_entry(az_p2, culm_p2, rolling_start)
                observer_entry = generate_observer_entry_head(az_p2, culm_p2)
            else:
                raise ValueError

            observer_entry += generate_observer_entry_body(after, azimuth_m1, azimuth_p1, azimuth,
                                                           culmimnation_m1, culmination_p1, culmination, rpm)

        if carenabled:
            feed_offset_drive = FAST_FEED_POSITION - carriagepos
        else:
            feed_offset_drive = 0
        feed_offset = DRIVE_TO_CM_SCALE * feed_offset_drive
        feed_offset_time = feed_offset_to_time(feed_offset, dec_degrees)
        local_culmination = (culmination + feed_offset_time).tz_localize(TIMEZONE)
        pulse1_rlc_begin = -regstart * 60
        pulse1_rlc_end = pulse1_rlc_begin + PULSE_DURATION
        pulse2_rlc_begin = regstop * 60
        pulse2_rlc_end = pulse2_rlc_begin + PULSE_DURATION
        record_duration_rlc_begin = -before * 60
        record_duration_rlc_end = after * 60

        carriage_motion = make_carriage_motion_entry(culmination, local_culmination, pulse1_rlc_begin, pulse2_rlc_begin,
                                                     carriagepos, oscenabled, amplitude,
                                                     speed1, accel1, decel1, dwell1,
                                                     speed2, accel2, decel2, dwell2)

        json_dict = {
            'azimuth': azimuth,
            'object': object_label,
            'culmination': culmination.tz_localize(TIMEZONE).isoformat(),
            'feed_offset': feed_offset,
            'feed_offset_time': feed_offset_time.total_seconds(),
            'record_duration_rlc': [record_duration_rlc_begin, record_duration_rlc_end],
            'pulse1_rlc': [pulse1_rlc_begin, pulse1_rlc_end],
            'pulse2_rlc': [pulse2_rlc_begin, pulse2_rlc_end],
            'dec': dec_degrees,
            'ra': ra_degrees,
            'fits_words': {},
            'cabin_motion': {
                'profile': [json_motion_entry]
            },
            'carriage_motion': carriage_motion,
            'acquisition_parameters': {
                'average_points': resolution_to_avgpts[resolution],
                'attenuator_common': attenuation,
                'polarization': polarization_to_pol[polarization],
                'auto_polarization_switch': polarization_to_auto[polarization],
            },
            'override_mainobs': False
        }
        json_jobs.append(json_dict)

        if idx in runs['idx_begin'].unique():
            profile = json_dict['cabin_motion'].get('profile')
            cabin_min_t = get_min_time_from_motion_profile(profile)

            profile = json_dict['carriage_motion'].get('profile')
            carriage_min_t = get_min_time_from_motion_profile(profile)

            run_begin = min(local_culmination + datetime.timedelta(seconds=pulse1_rlc_begin),
                            local_culmination + datetime.timedelta(seconds=record_duration_rlc_begin),
                            cabin_min_t, carriage_min_t) - datetime.timedelta(seconds=SECONDS_BEFORE_OBS_RUN_BEGINS)
            run_begins.append(run_begin)

        if idx in runs['idx_end'].unique():
            profile = json_dict['cabin_motion'].get('profile')
            cabin_max_t = get_max_time_from_motion_profile(profile)

            profile = json_dict['carriage_motion'].get('profile')
            carriage_max_t = get_max_time_from_motion_profile(profile)

            run_end = max(local_culmination + datetime.timedelta(seconds=pulse2_rlc_end),
                          local_culmination + datetime.timedelta(seconds=record_duration_rlc_end),
                          cabin_max_t, carriage_max_t) + datetime.timedelta(seconds=SECONDS_AFTER_OBS_RUN_ENDS)
            run_ends.append(run_end)

        at_job += at_motion_entry
        operator_schedule += operator_entry
        observer_schedule += observer_entry

    for e in list(zip(run_begins, run_ends)):
        json_jobs = [{
            'setup': True,
            'observation': [e[0].isoformat(), e[1].isoformat()]
        }] + json_jobs

    with tempfile.TemporaryDirectory() as dir_name:
        with open(f'{dir_name}/modifications.json', 'w') as f:
            json.dump(json_jobs, f, indent=2)
        write_at_job(at_job, object_label, ant_table, dir_name)
        write_at_rmall(dir_name)
        write_stop(dir_name)
        write_operator_schedule(operator_schedule, object_label, ant_table, dir_name)
        write_observer_schedule(observer_schedule, object_label, ant_table, dir_name)

        arch_name = f'{job_name}_track'
        zip_name = f'{dir_name}/{arch_name}.zip'
        with ZipFile(zip_name, 'w') as zip_obj:
            file_list = ['at_job', 'at_rmall', 'stop', 'operator.txt', 'observer.txt', 'modifications.json']
            for el in file_list:
                file_path = f'{dir_name}/{el}'
                zip_obj.write(file_path, f'{arch_name}/{basename(file_path)}')

        return dcc.send_file(zip_name)


def get_min_time_from_motion_profile(profile):
    m_t = datetime.datetime(year=2100, month=1, day=1).astimezone(TIMEZONE)
    if profile is not None:
        for e in profile:
            t = e.get('time')
            if t is not None:
                dt = datetime.datetime.fromisoformat(t)
                if dt < m_t:
                    m_t = dt
    return m_t


def get_max_time_from_motion_profile(profile):
    m_t = datetime.datetime(year=1970, month=1, day=1).astimezone(TIMEZONE)
    if profile is not None:
        for e in profile:
            t = e.get('time')
            if t is not None:
                dt = datetime.datetime.fromisoformat(t)
                if dt > m_t:
                    m_t = dt
    return m_t


def get_continuous_runs(df):
    first = df['date_time'].diff()
    first = (first > RUNS_GAP)
    first.iloc[0] = True
    last = df['date_time'].diff(periods=-1)
    last = (-last > RUNS_GAP)
    last.iloc[-1] = True
    is_first = df[['idx', 'date_time']][first]
    is_first.reset_index(inplace=True, drop=True)
    is_last = df[['idx', 'date_time']][last]
    is_last.reset_index(inplace=True, drop=True)
    assert len(is_first) == len(is_last)
    runs = pd.concat([is_first, is_last], axis=1)
    runs.columns = ['idx_begin', 'run_begin', 'idx_end', 'run_end']
    # result = []
    # for (_, run_begin, run_end) in runs.itertuples():
    #     result.append({
    #         'setup': True,
    #         'run_begin': run_begin.isoformat(),
    #         'run_end': run_end.isoformat(),
    #     })
    return runs


def make_carriage_motion_entry(culmination, local_culmination, pulse1_rlc, pulse2_rlc, position, oscenabled, amplitude,
                               speed1, accel1, decel1, dw1, speed2, accel2, decel2, dw2):
    pa = position - amplitude / 2
    pb = position + amplitude / 2

    v1 = speed1 / 60 * 360
    v2 = speed2 / 60 * 360
    a1 = accel1 / 2 / np.pi * 360
    a2 = accel2 / 2 / np.pi * 360
    d1 = decel1 / 2 / np.pi * 360
    d2 = decel2 / 2 / np.pi * 360

    period = timedelta(seconds=v1 / 2 * (1 / a1 + 1 / d1) + v2 / 2 * (1 / a2 + 1 / d2) + amplitude * (1 / v1 + 1 / v2)
                               + dw1 + dw2)
    t0_rlc = timedelta(seconds=amplitude / 2 / v1 + v1 / 2 / a1)
    n_periods_before_culmination = abs((timedelta(seconds=pulse1_rlc + 5) + t0_rlc) // period)
    n_periods_after_culminations = abs((timedelta(seconds=pulse2_rlc - 5) + t0_rlc) // period)
    n_periods = n_periods_before_culmination + n_periods_after_culminations

    start_time1 = culmination - (n_periods_before_culmination * period + t0_rlc)
    start_time2 = start_time1 + timedelta(seconds=amplitude / v1 + v1 / 2 * (1 / a1 + 1 / d1) + dw1)
    pre_start_time = start_time1 - timedelta(minutes=1)

    items = []

    if oscenabled:
        items.append({
            'time': pre_start_time.tz_localize(TIMEZONE).isoformat(),
            'position': pa,
            'speed': 800,
            'acceleration': 100,
            'deceleration': 100
        })
        for i in range(n_periods):
            items.append({
                'time': (start_time1 + i * period).tz_localize(TIMEZONE).isoformat(),
                'position': pb,
                'speed': speed1,
                'acceleration': accel1,
                'deceleration': decel1
            })
            items.append({
                'time': (start_time2 + i * period).tz_localize(TIMEZONE).isoformat(),
                'position': pa,
                'speed': speed2,
                'acceleration': accel2,
                'deceleration': decel2
            })
    else:
        items.append({
            'time': pre_start_time.tz_localize(TIMEZONE).isoformat(),
            'position': position,
            'speed': 800,
            'acceleration': 100,
            'deceleration': 100
        })

    result = {
        'start_position': position,
        'profile': items
    }

    return result
