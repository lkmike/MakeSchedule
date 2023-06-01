from dash.dependencies import Input, Output, State
from dash import dcc, html, ctx, ALL

from dash.exceptions import PreventUpdate

import os
from os.path import basename
from zipfile import ZipFile

import re

from app import app
from utils import *
from model import ObservationTable

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
    print('schedule begin')
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
    Output('table-container-culminations', 'children'),
    Output('run-csmake', 'disabled'),
    Output('load-csi', 'disabled'),
    Input('stellar-name', 'value'),
    Input('stellar-ra', 'value'),
    Input('stellar-dec', 'value'),
    Input('azimuths', 'value'),
    Input('schedule-begin-datetime-input', 'value'),
    Input('schedule-end-datetime-input', 'value'),
)
def recalculate_culminations(object_name: str, ra: str, dec: str, azimuths: str, begin_time: str, end_time: str):
    before = DEFAULT_BEFORE
    after = DEFAULT_AFTER
    try:
        azimuths_ = azimuths.replace(',', ' ').split()
        begin_datetime = datetime.fromisoformat(begin_time)
        end_datetime = datetime.fromisoformat(end_time)
        date_utc = datetime.fromisoformat(begin_time).strftime('%Y%m%d')
        n = (end_datetime - begin_datetime).days + 2

        if n > 10:
            raise ValueError

        if object_name in PLANETS:
            # Убираем [] из названия объекта
            object_name = object_name[1:-1]
            dont_use_config = True
            az = '\n'.join(map(lambda x: f'{int(x):.4f}', azimuths_))
            s = get_efrat_job_object(object_name, az, date_utc, str(n))

        else:
            dont_use_config = True
            ra = re.sub(r'[hms]', '', ra)
            dec = re.sub(r'[dms]', '', dec)
            az = '\n'.join(map(lambda x: f'{int(x):.4f}', azimuths_))
            s = get_efrat_job_stellar(object_name, ra, dec, az, date_utc, str(n))

        s_bytes = str.encode(s)
        p = subprocess.run('export LD_LIBRARY_PATH=./efrat/stellar; efrat/stellar/efrat', stdout=subprocess.PIPE,
                           input=s_bytes, shell=True)

        if p.returncode != 0:
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle('Ошибка')),
                dbc.ModalBody(html.P(p.stderr.decode())),
                dbc.ModalFooter(dbc.Button('Закрыть', id='modal-close', className='ms-auto', n_clicks=0, )),
            ], id='modal-culminations-error', is_open=False, )
            raise PreventUpdate

        efrat_stdout = p.stdout.decode()
        efrat_strings = efrat_stdout.split('\n')

        print(efrat_stdout)

        table_num = []
        for i, el in enumerate(efrat_strings[:-1]):
            # В конце строки 0x00
            a = el[:-1].replace('- ', '-').split()
            # year = a[0]
            # md = list(map(lambda x: f'{int(x):02}', a[1:3]))
            # date_parts = [year] + md

            # hm = list(map(lambda x: f'{int(x):02}', a[3:5]))
            # ss = f'{float(a[5]):06.3f}'
            # time_parts = hm + [ss]

            # date_local_string = str(date.fromisoformat('-'.join(date_parts)))
            # datetime_local_out = datetime.fromisoformat(f"{date_local_string}T{':'.join(time_parts)}")

            s_us = float(a[5])
            ss = a[5].split('.')
            second = int(ss[0])
            usecond = int((s_us - second) * 1000000)

            # Это еще не окончательная дата
            if second == 60:
                datetime_local_out = datetime(year=int(a[0]), month=int(a[1]), day=int(a[2]), hour=int(a[3]),
                                              minute=int(a[4]) + 1, second=0, microsecond=usecond)
            else:
                datetime_local_out = datetime(year=int(a[0]), month=int(a[1]), day=int(a[2]), hour=int(a[3]),
                                              minute=int(a[4]), second=second, microsecond=usecond)

            # Долбаный efrat не знает про отвод часов на час назад, зато efratp2015 использует только UT/UTC
            if dont_use_config:
                datetime_local_out = (datetime_local_out + timedelta(hours=-1))

            az_out_str = f'{float(a[6]):+03.0f}'
            h_per = float(a[7])

            A_obj = float(a[8])
            h_obj = float(a[9])

            RA_h = int(a[10])
            RA_m = int(a[11])
            RA_s = float(a[12])

            RA_degrees = (RA_h + (RA_m + RA_s / 60) / 60) / 24 * 360

            # Знак склонения в выводе ефрата иногда прилеплен к градусам, иногда нет, переводить в десятичную меру
            # с осторожностью!
            dec_d = int(a[13])
            dec_m = int(a[14])
            dec_s = float(a[15])
            if dec_d < 0:
                dec_degrees = -dms_to_deg(-dec_d, dec_m, dec_s)
            else:
                dec_degrees = dms_to_deg(dec_d, dec_m, dec_s)

            sid_time_h = int(a[16])
            sid_time_m = int(a[17])
            sid_time_s = float(a[18])
            # sid_time: str = f'{sid_time_h}:{sid_time_m}:{sid_time_s}'
            sid_time_degrees = (sid_time_h + (sid_time_m + sid_time_s / 60) / 60) / 24 * 360

            refr = float(a[19])
            NutRA = float(a[20])
            P_obj = float(a[21])
            P_diag = float(a[22])

            Va = float(a[23])
            Vh = float(a[24])

            if begin_datetime <= datetime_local_out <= end_datetime:
                idx = str(i)
                table_num.append([
                    idx,
                    az_out_str,
                    datetime_local_out,
                    h_per,
                    # make_dropdown({'type': 'aperture', 'index': str(i)}, '167'),
                    DEFAULT_APERTURE,
                    # make_checkbox({'type': 'retract', 'index': str(i)}),
                    DEFAULT_RETRACT,
                    # make_input({'type': 'before', 'index': str(i)}, 4),
                    DEFAULT_BEFORE,
                    # make_input({'type': 'after', 'index': str(i)}, 4),
                    DEFAULT_AFTER,
                    # make_checkbox({'type': 'track', 'index': str(i)}),
                    DEFAULT_TRACK,
                    A_obj,
                    h_obj,
                    RA_degrees,
                    dec_degrees,
                    sid_time_degrees,
                    refr,
                    NutRA,
                    P_obj,
                    P_diag,
                    Va,
                    Vh
                ])

        table_num_np = np.array(table_num, dtype=object)
        ObservationTable.table = pd.DataFrame({
            'idx': table_num_np[:, 0],
            'Azimuth': table_num_np[:, 1],
            'DateTime': table_num_np[:, 2],
            'H_per': table_num_np[:, 3],
            'Aperture': table_num_np[:, 4],
            'Retract': table_num_np[:, 5],
            'Before': table_num_np[:, 6],
            'After': table_num_np[:, 7],
            'Track': table_num_np[:, 8],
            'A_obj': table_num_np[:, 9],
            'h_obj': table_num_np[:, 10],
            'RA_degrees': table_num_np[:, 11],
            'Dec_degrees': table_num_np[:, 12],
            'Sid_time_degrees': table_num_np[:, 13],
            'Refraction': table_num_np[:, 14],
            'Nutation': table_num_np[:, 15],
            'Pos_angle_obj': table_num_np[:, 16],
            'Pos_angle_diag': table_num_np[:, 17],
            'Vad': table_num_np[:, 18],
            'Vhd': table_num_np[:, 19],
        })

        table_out_df = pd.DataFrame({
            html.Div('Азимут', style=head_style, className='h-100'): ObservationTable.table['Azimuth'],
            html.Div('Дата', style=head_style, className='h-100'):
                ObservationTable.table['DateTime'].apply(lambda x: x.strftime('%Y-%m-%d')),
            html.Div('Время', style=head_style, className='h-100'):
                ObservationTable.table['DateTime'].apply(lambda x: x.strftime('%H:%M:%S')),
            html.Div('Высота', style=head_style, className='h-100'):
                ObservationTable.table['H_per'].apply(lambda x: deg_to_dms(x)),
            html.Div([
                html.Div('Апертура', style=head_style, className='me-2 align-bottom', id='tt-aperture'),
                dbc.Tooltip('Размер апертуры, щитов', target='tt-aperture', placement='top'),
                html.Div([
                    make_dropdown({'type': 'aperture-value-all', 'index': '0'}, '167', marginleft='0px'),
                    dbc.Button('↓', id='aperture-set-all', size='sm', class_name='align-bottom'),
                    dbc.Tooltip('Установить значение для всех азимутов', target='aperture-set-all', placement='bottom')
                ], className='d-inline-block')
            ]): ObservationTable.table[['idx', 'Aperture']].apply(
                lambda x: make_dropdown({'type': 'aperture', 'index': str(x['idx'])}, x['Aperture']), axis=1),
            html.Div([
                html.Div('Отвод', style=head_style, className='me-2 align-bottom', id='tt-retract'),
                dbc.Tooltip('Отвод центральных щитов', target='tt-retract', placement='top'),
                html.Div([
                    dbc.Button('✓', id='retract-set-all', size='sm', style=head_style, class_name='align-bottom'),
                    dbc.Tooltip('Выбрать все', target='retract-set-all', placement='bottom'),
                    dbc.Button('✗', id='retract-reset-all', size='sm', class_name='align-bottom'),
                    dbc.Tooltip('Сбросить все', target='retract-reset-all', placement='bottom')
                ], className='d-inline-block')
            ]): ObservationTable.table[['idx', 'Retract']].apply(
                lambda x: make_checkbox({'type': 'retract', 'index': str(x['idx'])}, x['Retract']), axis=1),
            html.Div([
                html.Div('До', style=head_style, className='me-2 align-bottom', id='tt-before'),
                dbc.Tooltip('От установки антенны до кульминации, мин', target='tt-before', placement='top'),
                html.Div([
                    make_input('before-value-all', before),
                    dbc.Button('↓', id='before-set-all', size='sm', class_name='align-bottom'),
                    dbc.Tooltip('Установить значение для всех азимутов', target='before-set-all', placement='bottom')
                ], className='d-inline-block')
            ]): ObservationTable.table[['idx', 'Before']].apply(
                lambda x: make_input({'type': 'before', 'index': str(x['idx'])}, x['Before']), axis=1),
            html.Div([
                html.Div('После', style=head_style, className='me-2 align-bottom', id='tt-after'),
                dbc.Tooltip('От кульминации до начала следующей установки антенны, мин', target='tt-after',
                            placement='top'),
                html.Div([
                    make_input('after-value-all', after),
                    dbc.Button('↓', id='after-set-all', size='sm', class_name='align-bottom'),
                    dbc.Tooltip('Установить значение для всех азимутов', target='after-set-all', placement='bottom')
                ], className='d-inline-block')
            ]): ObservationTable.table[['idx', 'After']].apply(
                lambda x: make_input({'type': 'after', 'index': str(x['idx'])}, x['After']), axis=1),
            html.Div([
                html.Div('Движение', style=head_style, className='me-2 align-bottom', id='tt-track'),
                dbc.Tooltip('Включить в расписание движения облучателя в режиме сопровождения', target='tt-track',
                            placement='top'),
                html.Div([
                    dbc.Button('✓', id='track-set-all', size='sm', style=head_style, class_name='align-bottom'),
                    dbc.Tooltip('Выбрать все', target='track-set-all', placement='bottom'),
                    dbc.Button('✗', id='track-reset-all', size='sm', style=head_style, class_name='align-bottom'),
                    dbc.Tooltip('Сбросить все', target='track-reset-all', placement='bottom')
                ], className='d-inline-block')
            ]): ObservationTable.table[['idx', 'Track']].apply(
                lambda x: make_checkbox({'type': 'track', 'index': str(x['idx'])}, x['Track']), axis=1),
        })

        return html.Div(dbc.Table.from_dataframe(table_out_df, striped=True, bordered=True),
                        style={'font-size': '0.9em'}), False, False  # , None, None

    # except TypeError:
    #     print('TypeError')
    #     ObservationTable.table = None
    #     return None, True, True
    # except ValueError:
    #     print('ValueError')
    #     ObservationTable.table = None
    #     return None, True, True
    except AttributeError:
        print('AttributeError')
        ObservationTable.table = None
        return None, True, True
    except IndexError:
        print('IndexError')
        ObservationTable.table = None
        return None, True, True


@app.callback(
    Output({'type': 'aperture-value-all', 'index': '0'}, "label"),
    Input({'type': 'aperture-value-all:item', 'index': '0', 'val': '167'}, "n_clicks"),
    Input({'type': 'aperture-value-all:item', 'index': '0', 'val': '61'}, "n_clicks"),
    Input({'type': 'aperture-value-all:item', 'index': '0', 'val': '51'}, "n_clicks"),
    Input({'type': 'aperture-value-all:item', 'index': '0', 'val': '41'}, "n_clicks"),
)
def update_aprture_value(i1, i2, i3, i4):
    trigger_id = ctx.triggered_id
    if not trigger_id:
        raise PreventUpdate
    if trigger_id.val in ['167', '61', '51', '41']:
        return trigger_id.val
    else:
        raise PreventUpdate


@app.callback(
    Output('sink', 'children'),
    Input({'type': 'aperture', 'index': ALL}, "label"),
    Input({'type': 'retract', 'index': ALL}, 'value'),
    Input({'type': 'before', 'index': ALL}, 'value'),
    Input({'type': 'after', 'index': ALL}, 'value'),
    Input({'type': 'track', 'index': ALL}, 'value'),
)
def update_observation_table(aperture, retract, before, after, track):
    trigger = ctx.triggered_id
    if not trigger:
        raise PreventUpdate
    if trigger.type == 'aperture':
        ObservationTable.table['Aperture'] = aperture
    elif trigger.type == 'retract':
        ObservationTable.table['Retract'] = retract
    elif trigger.type == 'before':
        ObservationTable.table['Before'] = before
    elif trigger.type == 'after':
        ObservationTable.table['After'] = after
    elif trigger.type == 'track':
        ObservationTable.table['Track'] = track

    raise PreventUpdate


@app.callback(
    Output('job-name', 'value'),
    Input('schedule-begin-datetime-input', 'value'),
)
def make_file_base_name(v):
    month_lookup = {1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: 'a', 11: 'b', 12: 'c'}
    # if ctx.triggered_id == 'schedule-begin-datetime-input':
    dt: datetime = datetime.fromisoformat(v)
    return f'{str(dt.year)[-1]}{month_lookup[dt.month]}{dt.day:02}x'


@app.callback(
    Output("modal_csmake", "is_open"),
    Input("csmake_close", "n_clicks"), prevent_initial_call=True
)
def modal_csmake_close_onclick(n):
    if n:
        return False


@app.callback(
    Output('csi-sink', 'children'),
    Input('run-csmake', 'n_clicks'),
    State('job-name', 'value'),
    State('stellar-name', 'value'), prevent_initial_call=True
)
def run_csmake_onclick(n, job_name, object_name):
    # print(ctx.triggered_id)
    if ctx.triggered_id == 'run-csmake':
        if object_name in PLANETS:
            # Убираем [] из названия объекта
            object_name = object_name[1:-1]
        m, f = setup_and_run_csmakes(job_name, object_name, ObservationTable.table)
        return None, dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle('csmake и csmake2')),
            dbc.ModalBody([html.Div([html.P(x, style={'margin': '0'}) for x in m.split('\n')],
                                    style={'margin-bottom': '2em'}),
                           html.Div([html.P(x, style={'margin': '0'}) for x in f.split('\n')])]),
            dbc.ModalFooter(html.Button('Закрыть', id='csmake_close', className='btn btn-primary btn-sm"',
                                        style={'height': '30.833px', 'padding-top': '0', 'padding-bottom': '0'},
                                        autoFocus='autofocus'))
        ], id='modal_csmake', is_open=True, scrollable=True)


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
    Output('dcc-download-csi', 'data'),
    Input('load-csi', 'n_clicks'),
    State('job-name', 'value'),
    State('stellar-name', 'value'), prevent_initial_call=True
)
def load_csi_onclick(n, job_name, object_name):
    if object_name in PLANETS:
        # Убираем [] из названия объекта
        object_name = object_name[1:-1]

    df = ObservationTable.table
    if (df is None) or (not ctx.triggered_id == 'load-csi'):
        raise PreventUpdate

    file_list = ['csephem', 'csmake', 'csmake2']
    src_path = 'efrat/common/'
    with tempfile.TemporaryDirectory() as td_name:
        for fn in file_list:
            shutil.copyfile(f'{src_path}/{fn}', f'{td_name}/{fn}')

        write_flat_csi(f'{td_name}/{job_name}f.csi', object_name, df)
        write_main_csi(f'{td_name}/{job_name}c.csi', object_name, df)

        p = subprocess.run(f'cd {td_name}; '
                           f'export PATH=$PATH:.; '
                           f'chmod 755 csmake; '
                           f'chmod 755 csmake2; '
                           f'chmod 755 csephem; '
                           f'csmake {job_name}c.csi', capture_output=True, shell=True)

        q = subprocess.run(f'cd {td_name}; '
                           f'export PATH=$PATH:.; '
                           f'chmod 755 csmake; '
                           f'chmod 755 csmake2; '
                           f'chmod 755 csephem; '
                           f'csmake2 {job_name}f.csi', capture_output=True, shell=True)

        downloads_list = [f'{job_name}c.csi', f'{job_name}f.csi']
        lst_list = [f'{job_name}c.lst', f'{job_name}f.lst']

        for fn in lst_list:
            if os.path.exists(f'{td_name}/{fn}'):
                downloads_list.append(fn)

        arch_name = f'{job_name}_antenna'
        zip_name = f'{td_name}/{arch_name}.zip'
        with ZipFile(zip_name, 'w') as zip_obj:
            for fn in downloads_list:
                file_path = f'{td_name}/{fn}'
                zip_obj.write(file_path, f'{arch_name}/{basename(file_path)}')

        return dcc.send_file(zip_name)


@app.callback(
    Output('dcc-download-motion', 'data'),
    Input('track-feed-download', 'n_clicks'),
    State('tracking-300rpm-s', 'value'),
    State('tracking-start', 'value'),
    State('tracking-correction', 'value'),
    State('stellar-name', 'value'),
    State('job-name', 'value'),

    prevent_initial_call=True
)
def track_download_onclick(n: int, s_per_degree_at_300: float, start_position: str, correction: float,
                            object_name: str, job_name: str):
    if object_name in PLANETS:
        # Убираем [] из названия объекта
        object_name = object_name[1:-1]

    df: pd.DataFrame = ObservationTable.table
    at_job: str = ''
    observer_schedule: str = ''
    operator_schedule: str = ''

    for (azimuth, date_time, h_per, aperture, retract, before, after, track, A_obj, h_obj, Vad, Vhd, dec_degrees,
         P_diag, RA_degrees, sid_time_degrees) \
            in zip(df['Azimuth'], df['DateTime'], df['H_per'], df['Aperture'], df['Retract'], df['Before'], df['After'],
                   df['Track'], df['A_obj'], df['h_obj'], df['Vad'], df['Vhd'], df['Dec_degrees'], df['Pos_angle_diag'],
                   df['RA_degrees'], df['Sid_time_degrees']):

        s_per_degree, rpm = calculate_rpm(A_obj=A_obj, h_obj=h_obj, Vad=Vad, Vhd=Vhd, dec_degrees=dec_degrees,
                                          seconds_per_degree300=s_per_degree_at_300, P_diag=P_diag,
                                          RA_degrees=RA_degrees, sid_time_degrees=sid_time_degrees)

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
            motion_entry = ''
            operator_entry = generate_operator_entry(azimuth, start_time=obs_start, rolling_start=rolling_start)
            observer_entry = f'\n{azimuth}: Транзит; кульминация в {culmination.strftime("%H:%M:%S")}; ' \
                             f'начало в {obs_start.strftime("%H:%M:%S")}, ' \
                             f'перекатка в {rolling_start.strftime("%H:%M:%S")}\n'

        else:

            rolling_start: datetime = culmination + timedelta(minutes=after) + timedelta(seconds=5)

            if start_position == '1':
                motion_entry = generate_motion_entry(azimuth, start_time=culm_plus_one, stop_time=culm_minus_one,
                                                     speed=rpm, culmination=culmination)
                operator_entry = generate_operator_entry(az_p1, culm_plus_one, rolling_start)
                observer_entry = f'\n{az_p2} ({culm_plus_two.strftime("%H:%M:%S")}) пропускаем\n'
            elif start_position == '2':
                motion_entry = generate_motion_entry(azimuth, start_time=culm_plus_two, stop_time=culm_minus_one,
                                                     speed=rpm, culmination=culmination)
                operator_entry = generate_operator_entry(az_p2, culm_plus_two, rolling_start)
                observer_entry = f'\n{az_p2}: {culm_plus_two.strftime("%H:%M:%S")}\n'
            else:
                raise ValueError

            observer_entry += f'{az_p1}: {culm_plus_one.strftime("%H:%M:%S")}\n' \
                              f'{azimuth}: {culmination.strftime("%H:%M:%S")} (кульминация) {rpm:6.2f} rpm\n' \
                              f'{az_m1}: {culm_minus_one.strftime("%H:%M:%S")} ' \
                              f'антенна уходит в {(culmination + timedelta(minutes=after)).strftime("%H:%M:%S")}\n'

        at_job += motion_entry
        operator_schedule += operator_entry
        observer_schedule += observer_entry

    with tempfile.TemporaryDirectory() as td_name:
        with open(f'{td_name}/at_job', 'w') as f:
            f.write('#!/bin/sh\n\n')
            f.write(f'# Объект {object_name}, наблюдения {df["DateTime"].iloc[0].strftime("%Y-%m-%d")}\n\n')
            f.write(at_job)
            f.write('\n')
        p = subprocess.run(f'chmod 755 {td_name}/at_job', shell=True)

        with open(f'{td_name}/at_rmall', 'w') as f:
            f.write('#!/bin/sh\n')
            f.write(f'# Отмена всех заданий at\n\n')
            f.write("for i in `atq | awk '{print $1}'`; do atrm $i; done\n")
        p = subprocess.run(f'chmod 755 {td_name}/at_rmall', shell=True)

        with open(f'{td_name}/stop', 'w') as f:
            f.write('#!/bin/sh\n')
            f.write(f'# Остановка движения облучателя\n\n')
            f.write("/home/sun/tmp/tcpMB/tcpio -m10 -u1 -r192.168.9.14 -l2 -p503\n")
        p = subprocess.run(f'chmod 755 {td_name}/stop', shell=True)

        operator_head = f'Объект {object_name}, наблюдения {df["DateTime"].iloc[0].strftime("%Y-%m-%d")}\n\n'
        with open(f'{td_name}/operator.txt', 'w') as f:
            f.write(operator_head)
            f.write(operator_schedule)

        observer_head = f'Объект {object_name}, наблюдения {df["DateTime"].iloc[0].strftime("%Y-%m-%d")}\n\n'
        with open(f'{td_name}/observer.txt', 'w') as f:
            f.write(observer_head)
            f.write(observer_schedule)

        arch_name = f'{job_name}_track'
        zip_name = f'{td_name}/{arch_name}.zip'
        with ZipFile(zip_name, 'w') as zip_obj:
            file_path = f'{td_name}/at_job'
            zip_obj.write(file_path, f'{arch_name}/{basename(file_path)}')
            file_path = f'{td_name}/at_rmall'
            zip_obj.write(file_path, f'{arch_name}/{basename(file_path)}')
            file_path = f'{td_name}/stop'
            zip_obj.write(file_path, f'{arch_name}/{basename(file_path)}')
            file_path = f'{td_name}/operator.txt'
            zip_obj.write(file_path, f'{arch_name}/{basename(file_path)}')
            file_path = f'{td_name}/observer.txt'
            zip_obj.write(file_path, f'{arch_name}/{basename(file_path)}')

        return dcc.send_file(zip_name)

    raise PreventUpdate

