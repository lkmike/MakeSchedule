from app import app
import pandas
import dash
from dash import dcc, ctx, ALL
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate

from utils import *

from antenna_table import make_antenna_html_table, apertures
from acquisition_table import make_acquisition_html_table
from carriage_table import make_carriage_html_table



@app.callback(
    Output({'type': 'aperture-value-all', 'index': '0'}, "label"),
    list(map(lambda x: Input({'type': 'aperture-value-all:item', 'index': '0', 'val': x}, "n_clicks"), apertures)),
)
def update_aperture_value(*inputs):
    trigger_id = ctx.triggered_id
    if not trigger_id:
        raise PreventUpdate
    if trigger_id.val in apertures:
        return trigger_id.val
    else:
        raise PreventUpdate


@app.callback(
    Output({'type': 'aperture', 'index': ALL}, "label"),
    list(map(lambda x: Input({'type': 'aperture:item', 'index': ALL, 'val': x}, "n_clicks"), apertures)) +
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
    elif trigger.val in apertures:
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
        Output('table-container-acquisition', 'children'),
        Output('table-container-carriage', 'children'),
        Output('job-summary', 'children'),
        Output('run-csmake', 'disabled'),
        Output('load-csi', 'disabled'),
        Output('load-track', 'disabled'),
        Output('obs-table', 'data'),
        Output('feed-table', 'data'),
        Output('carriage-table', 'data'),
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
        State('carriage-table', 'data'),
    ],
    background=True,
    progress=[Output('modal-progress', 'is_open'), Output('update-progress', 'value'),
              Output('update-progress', 'max')],
)
def recalculate_culminations(set_progress, object_name: str, ra: str, dec: str, azimuths: str, begin_time: str,
                             end_time: str, use_solar_object: int, solar_object_name: str, solar_ref_time: str,
                             solar_lon: int, solar_lat: int,
                             aperture, retract, before, after, track, std,
                             tcc, js, rc, lc, tfd,
                             json_antenna, json_feed, json_carriage):
    set_progress((True, 100, 100))

    trigger = ctx.triggered_id

    antenna_row_updates = ['aperture', 'retract', 'before', 'after', 'track', 'std']
    acquisition_row_updates = ['resolution', 'attenuation', 'polarization', 'regstart', 'regstop']
    carriage_row_updates = ['amplitude', 'speed1', 'speed2', 'accel1', 'accel2', 'decel1', 'decel2', 'dwell1', 'dwell2']

    row_updates = antenna_row_updates + acquisition_row_updates + carriage_row_updates

    antenna_table = None
    if json_antenna and hasattr(trigger, 'type') and trigger.type in row_updates:
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
    if json_feed and hasattr(trigger, 'type') and trigger.type in row_updates:
        feed_table = pd.read_json(json_feed[1:-1], orient='split')

    carriage_table = None
    if json_carriage and hasattr(trigger, 'type') and trigger.type in row_updates:
        carriage_table = pd.read_json(json_carriage[1:-1], orient='split')

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
            # feed_table['carriagepos'] = [DEFAULT_CARRIAGEPOS] * feed_table.shape[0]

        json_feed_out = "'" + feed_table.to_json(date_format='iso', orient='split') + "'"

        if carriage_table is not None:
            carriage_table['azimuth'] = antenna_table['azimuth']
            carriage_table['date_time'] = antenna_table['date_time']
        else:
            carriage_table = antenna_table[['idx', 'azimuth', 'date_time']]
            # carriage_table['regstart'] = antenna_table['before'] - 0.1
            # carriage_table['regstop'] = antenna_table['after'] - 0.1
            carriage_table['carenabled'] = [DEFAULT_CARRIAGE_ENABLED] * feed_table.shape[0]
            carriage_table['carriagepos'] = [DEFAULT_CARRIAGEPOS] * feed_table.shape[0]
            carriage_table['oscenabled'] = [DEFAULT_CARRIAGE_OSCENABLED] * feed_table.shape[0]
            carriage_table['amplitude'] = [DEFAULT_CARRIAGE_AMPLITUDE] * feed_table.shape[0]
            carriage_table['speed1'] = [DEFAULT_CARRIAGE_SPEED] * feed_table.shape[0]
            carriage_table['speed2'] = [DEFAULT_CARRIAGE_SPEED] * feed_table.shape[0]
            carriage_table['accel1'] = [DEFAULT_CARRIAGE_ACCEL] * feed_table.shape[0]
            carriage_table['accel2'] = [DEFAULT_CARRIAGE_ACCEL] * feed_table.shape[0]
            carriage_table['decel1'] = [DEFAULT_CARRIAGE_DECEL] * feed_table.shape[0]
            carriage_table['decel2'] = [DEFAULT_CARRIAGE_DECEL] * feed_table.shape[0]
            carriage_table['dwell1'] = [DEFAULT_CARRIAGE_DWELL] * feed_table.shape[0]
            carriage_table['dwell2'] = [DEFAULT_CARRIAGE_DWELL] * feed_table.shape[0]

        json_carriage_out = "'" + carriage_table.to_json(date_format='iso', orient='split') + "'"

        is_sun = (object_name == '[Sun]')
        antenna_html_table = make_antenna_html_table(antenna_table, DEFAULT_BEFORE, DEFAULT_AFTER, is_sun,
                                                     use_solar_object)
        feed_html_table = make_acquisition_html_table(feed_table, DEFAULT_ATTENUATION, DEFAULT_REGSTART,
                                                      DEFAULT_REGSTOP)
        carriage_html_table = make_carriage_html_table(carriage_table)

        object_label = make_object_label(object_name, use_solar_object, solar_object_name)
        return antenna_html_table, feed_html_table, carriage_html_table, \
            f'#### {object_label}: {begin_datetime.strftime("%Y-%m-%d %H:%M:%S")} — ' \
            f'{end_datetime.strftime("%Y-%m-%d %H:%M:%S")}', \
            False, False, False, json_antenna_out, json_feed_out, json_carriage_out

    except (TypeError, ValueError, AttributeError) as ex:
        print('recalculate_culminations exception:', ex)
        return None, None, None, '#### &nbsp;', True, True, True, None, None, None
    finally:
        set_progress((False, 100, 100))
