import math
from datetime import date, datetime, timedelta
from pytz import timezone
import copy

import astropy as astropy
import dash_bootstrap_components
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd

import shutil
import tempfile
import subprocess

import astropy.units as u
from dash import html
from dash.exceptions import PreventUpdate
from sunpy import coordinates
from astropy.coordinates import SkyCoord
import astropy.time

DEFAULT_BEFORE = 6.1
DEFAULT_AFTER = 6.6
DEFAULT_APERTURE = '61'
DEFAULT_RETRACT = False
DEFAULT_TRACK = True
DEFAULT_ATTENUATION = -10

DEFAULT_REGSTART = DEFAULT_BEFORE - 0.1
DEFAULT_REGSTOP = DEFAULT_AFTER - 0.1

DEFAULT_CARRIAGEPOS = 0


TIMEZONE = timezone('Europe/Moscow')

PLANETS = ['[Sun]', '[Moon]', '[Mercury]', '[Venus]', '[Earth]', '[Mars]', '[Jupiter]', '[Saturn]',
           '[Uranus]', '[Neptune]', '[Pluto]']

stellar_presets = {
    'stellar-source-crab': {'ra': '05h34m32s', 'dec': '22d00m52.0s', 'name': 'Crab'},
    'stellar-source-cyga': {'ra': '19h57m44.5s', 'dec': '40d35m46.0s', 'name': 'CygA'},
    'stellar-source-3c84': {'ra': '03h19m48.16s', 'dec': '41d30m42.2s', 'name': '3c84'},
    'stellar-source-3c273': {'ra': '12h29m06.6s', 'dec': '02d03m08.6s', 'name': '3c273'}
}


def get_efrat_job_stellar(source_name, ra, dec, azimuths, date_utc, n_days):
    return f"""mode per
path_data "efrat/stellar/DATA"
format 1
object Stellar
coord {source_name} {ra} {dec} 0.0 0.0 1 0.0 0.0
azimuth (
{azimuths}
)
date_utc {date_utc} {n_days}
double_alt
end
"""


def get_efrat_job_object(source_name, azimuths, date_utc, n_days):
    if f'[{source_name}]' not in PLANETS:
        print('get_efrat_job_object', source_name)
        return None

    return f"""mode per
path_data "efrat/stellar/DATA"
format 1
object {source_name}
azimuth (
{azimuths}
)
date_utc {date_utc} {n_days}
double_alt
end
"""


head_style = {'margin-right': '2px', 'display': 'inline-block', 'vertical-align': 'center'}
head_input_style = {'margin-right': '2px', 'display': 'inline-block', 'vertical-align': 'center',
                    'width': '6em'}


def make_dropdown(identifier, label, items, marginleft='0', width='6em'):
    item_ids = []
    for e in items:
        item_id = copy.deepcopy(identifier)
        item_id['type'] = item_id['type'] + ':item'
        item_id['val'] = e
        item_ids.append(item_id)

    st = copy.deepcopy(head_style)
    st['margin-left'] = marginleft
    # st['min-width'] = width

    result = []
    for i, e in enumerate(items):
        result.append(dbc.DropdownMenuItem(e, id=item_ids[i]))

    return html.Div(
        dbc.DropdownMenu(children=result, label=label, style=st, size='sm', class_name='d-grid w-100', id=identifier),
        style={'display': 'inline-block', 'width': width})


def make_aperture_dropdown(identifier, label, marginleft='0px'):
    return make_dropdown(identifier, label, items=['167', '61', '51', '41'],
                         marginleft=marginleft, width='6em')


def make_resolution_dropdown(identifier, label, marginleft='0px'):
    return make_dropdown(identifier, label,
                         items=['7.8 МГц', '3.9 МГц', '1.95 МГц', '976 кГц', '488 кГц', '244 кГц', '122 кГц'],
                         marginleft=marginleft, width='6em')


def make_attenuation_dropdown(identifier, label, marginleft: str = '0px'):
    items = list(map(lambda x: f'{x} дБ', np.arange(0, -32, -0.5)))
    return make_dropdown(identifier, label,
                         items=items,
                         marginleft=marginleft, width='6em')


def make_polarization_dropdown(identifier, label, marginleft: str = '0px'):
    items = list(map(lambda x: f'{x} дБ', np.arange(0, -32, -0.5)))
    return make_dropdown(identifier, label,
                         items=['Л', 'П', 'Авто'],
                         marginleft=marginleft, width='6em')


# def make_aperture_dropdown(identifier, label, marginleft: str = '30px'):
#     item_ids = []
#     for e in ['167', '61', '51', '41']:
#         item_id = copy.deepcopy(identifier)
#         item_id['type'] = item_id['type'] + ':item'
#         item_id['val'] = e
#         item_ids.append(item_id)
#
#     st = copy.deepcopy(head_style)
#     st['margin-left'] = marginleft
#
#     return dbc.DropdownMenu(children=[
#         dbc.DropdownMenuItem('167', id=item_ids[0]),
#         dbc.DropdownMenuItem('61', id=item_ids[1]),
#         dbc.DropdownMenuItem('51', id=item_ids[2]),
#         dbc.DropdownMenuItem('41', id=item_ids[3]),
#     ], label=label, style=st, size='sm', id=identifier)


def make_checkbox(identifier, value):
    return dbc.Checkbox(value=value, id=identifier, style={'margin-left': '30px'})


def make_duration_input(identifier, value):
    return dbc.Input(value=value, id=identifier, type='number', style=head_input_style, size='sm', min=1, max=15,
                     step=0.1)


def make_attenuation_input(identifier, value):
    return dbc.Input(value=value, id=identifier, type='number', style=head_input_style, size='sm', min=-31.5, max=0,
                     step=0.5)


def make_reg_input(identifier, value):
    return dbc.Input(value=value, id=identifier, type='number', style=head_input_style, size='sm', min=0, max=15,
                     step=0.1)


def make_carriagepos_input(identifier, value):
    return dbc.Input(value=value, id=identifier, type='number', style=head_input_style, size='sm', min=-150000, max=150000,
                     step=0.1)


def dms_to_deg(d: int, m: int, s: float) -> float:
    return d + (m + s / 60) / 60


def deg_to_dms(deg: float):
    si = '- ' if (np.sign(deg) < 0) else ''
    val = abs(deg)
    ms, d = np.modf(val)
    dd = f'{int(d):02}'
    s, m = np.modf(ms * 60)

    # Граничный случай, когда секунды округляются до 60.0
    if int(10 * float(f'{float(s * 60):04.01f}')) == 600:
        mm = f'{int(m):02}'
        ss = f'{0:04.01f}'
    else:
        mm = f'{int(m):02}'
        ss = f'{float(s * 60):04.01f}'
    return f'{si} {dd}:{mm}:{ss}'


def main_csi_header_template_use_cfg(beg_datetime: datetime, end_datetime: datetime):
    return f'''----------------------------------------------
Term      BegDate BegTime EndDate EndTime
----------------------------------------------
set       {beg_datetime.strftime('%Y.%m.%d %H:%M:%S')} {end_datetime.strftime('%Y.%m.%d %H:%M:%S')}

Problem   = SunObs
Include   = JoinPAR.csi
Feed      = 3
AzF       = 180
Class     = Setting
CSmode    = STD+Prep
--------------------------------------------------------------------
Source    ObsTime         Duration       Join     //     H(f)
--------------------------------------------------------------------
'''


def main_csi_entry_template_use_cfg(source: str, az: str, culmination: datetime, before: timedelta, after: timedelta,
                                    hf: float):
    return f"{source}{az}    {culmination.strftime('%H:%M:%S.%f')[:-4]}     " \
           f"-{before.seconds / 60:4.2f}/{after.seconds / 60:4.2f}     P{az}     //     {deg_to_dms(hf)}\n"


def main_csi_header_template_use_script(beg_datetime: datetime, end_datetime: datetime):
    return f'''---------------------------------------------------------------------------
Term      BegDate    BegTime  EndDate    EndTime
---------------------------------------------------------------------------
set       {beg_datetime.strftime('%Y.%m.%d %H:%M:%S')} {end_datetime.strftime('%Y.%m.%d %H:%M:%S')}

Problem   = SunObs
Include   = JoinPAR.csi
Feed      = 3
AzF       = 180
Class     = Horizon
CSmode    = STD+Prep
Nmin      = 1

---------------------------------------------------------------------------
Source         ObsTime        Rotate         Duration       Aperture
---------------------------------------------------------------------------
'''


def main_csi_entry_template_use_script(source: str, az: str, culmination: datetime, before: timedelta, after: timedelta,
                                       aperture: int):
    aperture_lookup = {
        167: '130:00:00',
        61: '52:00:00',
        51: '44:00:00',
        41: '36:00:00'
    }
    return f"{f'{source}{az}':15}" + \
        f"{culmination.strftime('%H:%M:%S.%f')[:-4]:15}" + \
        f"{f'{az}:00:00.0':15}" + \
        f"{f'-{before.seconds / 60:4.2f}/{after.seconds / 60:4.2f}':15}" + \
        f"{aperture_lookup[aperture]}" + \
        '\n'


def write_main_csi(file_name: str, object_name: str, table: pd.DataFrame):
    join_lookup = {
        '+30': 'J_P+30', '+28': 'J_P+28', '+26': 'J_P+26', '+24': 'J_P+24', '+22': 'J_P+22', '+20': 'J_P+20',
        '+18': 'J_P+18', '+16': 'J_P+16', '+14': 'J_P+14', '+12': 'J_P+12', '+10': 'J_P+10', '+08': 'J_P+8',
        '+06': 'J_P+6', '+04': 'J_P+4', '+02': 'J_P+2', '+00': 'J_P+0', '-02': 'J_P-2', '-04': 'J_P-4', '-06': 'J_P-6',
        '-08': 'J_P-8', '-10': 'J_P-10', '-12': 'J_P-12', '-14': 'J_P-14', '-16': 'J_P-16', '-18': 'J_P-18',
        '-20': 'J_P-20', '-22': 'J_P-22', '-24': 'J_P-24', '-26': 'J_P-26', '-28': 'J_P-28', '-30': 'J_P-30',
    }
    with open(file_name, 'w') as f:
        start_time = table['date_time'].iloc[0] - timedelta(minutes=30)
        stop_time = table['date_time'].iloc[-1] + timedelta(minutes=30)

        f.write(main_csi_header_template_use_script(start_time, stop_time))

        current_date: date = table['date_time'].iloc[0].date()
        f.write(f"\nObsDate = {current_date.strftime('%Y.%m.%d')}\n\n")

        for (azimuth, date_time, h_per, aperture, retract, before, after, track) \
                in zip(table['azimuth'], table['date_time'],
                       table['h_per'], table['aperture'],
                       table['retract'], table['before'],
                       table['after'], table['track']):
            if date_time.date() > current_date:
                current_date = date_time.date()
                f.write(f"\nObsDate = {current_date.strftime('%Y.%m.%d')}\n\n")

            if retract:
                f.write(f"\nJoin = {join_lookup[azimuth]}\n")

            f.write(main_csi_entry_template_use_script(object_name, azimuth, date_time, timedelta(minutes=before),
                                                       timedelta(minutes=after), aperture))

            if retract:
                f.write(f"Join = J_NOT\n\n")


def flat_csi_header_template(beg_datetime: datetime, end_datetime: datetime):
    return f'''
------------------------------------------------------------
Term      BegDate    BegTime  EndDate    EndTime
------------------------------------------------------------
set       {beg_datetime.strftime('%Y.%m.%d %H:%M:%S')} {end_datetime.strftime('%Y.%m.%d %H:%M:%S')}

Quota     = SunObs
Observer  = SunObs
Feed      = 3
AzF       = S+F
Sector    = 6-119F
Class     = Horizon
Azimuth   = 0:00:00

------------------------------------------------------------
Source         ObsTime        Duration       Altitude
------------------------------------------------------------
'''


def flat_csi_entry_template(source: str, az: str, culmination: datetime, before: timedelta, after: timedelta,
                            h_per: float):
    return f"{f'{source}{az}':15}" + \
        f"{culmination.strftime('%H:%M:%S.%f')[:-4]:15}" + \
        f"{f'-{before.seconds / 60:4.2f}/{after.seconds / 60:4.2f}':15}" + \
        f"{deg_to_dms(h_per):15}" + \
        '\n'


def write_flat_csi(file_name: str, object_name: str, df: pd.DataFrame):
    with open(file_name, 'w') as f:
        start_time = df['date_time'].iloc[0] - timedelta(minutes=30)
        stop_time = df['date_time'].iloc[-1] + timedelta(minutes=30)

        f.write(flat_csi_header_template(start_time, stop_time))

        current_date: date = df['date_time'].iloc[0].date()
        f.write(f"\nObsDate = {current_date.strftime('%Y.%m.%d')}\n\n")

        for (azimuth, date_time, h_per, aperture, retract, before, after, track) \
                in zip(df['azimuth'], df['date_time'],
                       df['h_per'], df['aperture'],
                       df['retract'], df['before'],
                       df['after'], df['track']):
            if date_time.date() > current_date:
                current_date = date_time.date()
                f.write(f"\nObsDate = {current_date.strftime('%Y.%m.%d')}\n\n")

            f.write(flat_csi_entry_template(object_name, azimuth, date_time, timedelta(minutes=before),
                                            timedelta(minutes=after), h_per))


def run_csmakes(dir_name, file_name_stub, object_name, df):
    file_list = ['csephem', 'csmake', 'csmake2']
    src_path = 'efrat/common/'
    for fn in file_list:
        shutil.copyfile(f'{src_path}/{fn}', f'{dir_name}/{fn}')
    write_flat_csi(f'{dir_name}/{file_name_stub}f.csi', object_name, df)
    write_main_csi(f'{dir_name}/{file_name_stub}c.csi', object_name, df)
    p = subprocess.run(f'cd {dir_name}; '
                       f'export PATH=$PATH:.; '
                       f'chmod 755 csmake; '
                       f'chmod 755 csmake2; '
                       f'chmod 755 csephem; '
                       f'csmake {file_name_stub}c.csi', capture_output=True, shell=True)
    q = subprocess.run(f'cd {dir_name}; '
                       f'export PATH=$PATH:.; '
                       f'chmod 755 csmake; '
                       f'chmod 755 csmake2; '
                       f'chmod 755 csephem; '
                       f'csmake2 {file_name_stub}f.csi', capture_output=True, shell=True)
    return p, q


def get_csmakes_result(file_name_stub: str, object_name: str, df: pd.DataFrame):
    with tempfile.TemporaryDirectory() as dir_name:
        p, q = run_csmakes(dir_name, file_name_stub, object_name, df)
        return 'Главное зеркало:\n' + p.stderr.decode(encoding='koi8-r'), 'Плоский:\n' + q.stderr.decode('koi8-r')


def generate_motion_entry(azimuth, start_time: datetime, stop_time: datetime, speed: float,
                          culmination: datetime = None):
    # Начинаем раньше на 4 с - время на запуск процессов и ускорение вагона
    start_allowance = 4
    actual_start_time: datetime = start_time - timedelta(seconds=start_allowance)
    at_start_time: datetime = datetime(
        year=actual_start_time.year,
        month=actual_start_time.month,
        day=actual_start_time.day,
        hour=actual_start_time.hour,
        minute=actual_start_time.minute,
        second=0
    )
    at_start_delay = timedelta(seconds=actual_start_time.second)

    at_stop_time: datetime = datetime(
        year=stop_time.year,
        month=stop_time.month,
        day=stop_time.day,
        hour=stop_time.hour,
        minute=stop_time.minute,
        second=0
    )
    at_stop_delay = timedelta(seconds=stop_time.second)

    # У привода десятичный знак - запятая
    speed_str = str(speed).replace('.', ',')

    # Д.б. motor_mode_*(t: datetime)
    MOTOR_MODE_OPERATOR: str = ''
    MOTOR_MODE_COMPUTER: str = ''

    culmination_str = f' Culmination @ {culmination.strftime("%H:%M:%S")}' if culmination else ''
    at_entry = \
        MOTOR_MODE_COMPUTER + \
        f'# {azimuth} Start @ {start_time.strftime("%H:%M:%S")} {culmination_str} \n' \
        f'echo "sleep {at_start_delay.seconds}; ' \
        f'/home/sun/tmp/tcpMB/tcpio -m13 -u1 -s2 -r192.168.9.14 -l2 -p503; ' \
        f'sleep 0.1; ' \
        f'/home/sun/tmp/tcpMB/tcpio -m10 -u1 -r192.168.9.14 -l2 -p503; ' \
        f'sleep 0.1; ' \
        f'/home/sun/tmp/tcpMB/tcpio -m1 -u1 -r192.168.9.14 -l2 -p503; ' \
        f'sleep 1; ' \
        f'/home/sun/tmp/tcpMB/tcpio -m3 -u1 -r192.168.9.14 -l2 -p503 -s{speed_str};  ' \
        f'sleep 0.1; ' \
        f'/home/sun/tmp/tcpMB/tcpio -m8 -u1 -r192.168.9.14 -l2 -p503 "' \
        f'| at {at_start_time.strftime("%H:%M")} \n' \
        f'# Stop @ {stop_time.strftime("%H:%M:%S")}; \n' \
        f'echo "sleep {at_stop_delay.seconds}; ' \
        f'/home/sun/tmp/tcpMB/tcpio -m10 -u1 -r192.168.9.14 -l2 -p503; ' \
        f'sleep 5; ' \
        f'/home/sun/tmp/tcpMB/tcpio -m13 -u1 -s0 -r192.168.9.14 -l2 -p503  "' \
        f'| at {at_stop_time.strftime("%H:%M")}\n\n' + \
        MOTOR_MODE_OPERATOR

    json_entry = {'start_time': start_time.isoformat(), 'stop_time': stop_time.isoformat(), 'speed': speed}
    return at_entry, json_entry

    # return \
    #     MOTOR_MODE_COMPUTER + \
    #     f'# {azimuth} Start @ {start_time.strftime("%H:%M:%S")} {culmination_str} \n' \
    #     f'echo "sleep {at_start_delay.seconds}; ' \
    #     f'/home/sun/tmp/tcpMB/tcpio -m8 -u1 -r192.168.9.14 -l2 -p503; ' \
    #     f'sleep 1; ' \
    #     f'/home/sun/tmp/tcpMB/tcpio -m3 -u1 -r192.168.9.14 -l2 -p503 -s{speed_str} " ' \
    #     f'| at {at_start_time.strftime("%H:%M")} \n' \
    #     f'# Stop @ {stop_time.strftime("%H:%M:%S")}; \n' \
    #     f'echo "sleep {at_stop_delay.seconds}; ' \
    #     f'/home/sun/tmp/tcpMB/tcpio -m10 -u1 -r192.168.9.14 -l2 -p503 " ' \
    #     f'| at {at_stop_time.strftime("%H:%M")}\n\n' + \
    #     MOTOR_MODE_OPERATOR


def generate_operator_entry(start_position: str, start_time: datetime, rolling_start: datetime):
    set_time: datetime = start_time - timedelta(seconds=40)
    return f'Установить в азимут {start_position} к {set_time.strftime("%H:%M:%S")} \n\n' + \
        f'Начало перекатки в {rolling_start.strftime("%H:%M:%S")}\n'


def calculate_rpm(a_obj, h_obj, dec_degrees, seconds_per_degree300, ra_degrees, sid_time_degrees):
    def deg2rad(x: float) -> float:
        return np.pi * x / 180

    a_obj_rad = deg2rad(a_obj)
    h = deg2rad(h_obj)
    dec = deg2rad(dec_degrees)
    # print('calculate_rpm', ra_degrees, dec_degrees)

    # Нечто, возникающее из-за дифракции для 6 см/ 5 ГГц и 61 щита;
    # чем длиннее волна и чем уже апертура, тем оно меньше;
    # Так наблюдали краб 23.12
    # magic = 0.843
    # Так по расчету диаграмм
    magic = 0.849 * 1.02536 * 0.968421
    magic = 0.849 * 1.02536
    # краб 24.12
    # magic = 0.897
    # краб 24.12 после +16
    # magic = 0.873

    cosdec = np.cos(dec)
    sindec = np.sin(dec)

    ha = deg2rad(sid_time_degrees) - deg2rad(ra_degrees)

    sinha = np.sin(ha)
    cosha = np.cos(ha)
    tanha = np.tan(ha)

    # Позиционнвй угол диаграммы
    omega = np.arctan(sindec * tanha)
    cosomega = np.cos(omega)

    # "/с; 15"/с - скорость изменения часового угла
    v_feed = (cosha * cosdec + sinha * tanha * cosdec * sindec ** 2) \
             / np.sqrt(1 - (sinha * cosdec) ** 2) * 15 * magic * cosomega

    # v_feed / 3600 - скорость в градусах в секунду
    rpm = 300 * seconds_per_degree300 * v_feed / 3600
    return timedelta(seconds=3600 / v_feed), rpm


def efrat_to_datetime(year, month, day, hour, minute, second):
    def repair_overflow(v1, v2, threshold, minval=0):
        if v2 == threshold:
            return v1 + 1, minval
        elif v2 > threshold:
            raise ValueError
        else:
            return v1, v2

    n_second = math.floor(float(second))
    usec = float(second) - n_second
    n_year, n_month, n_day, n_hour, n_minute, n_second = map(int, [year, month, day, hour, minute, n_second])
    n_minute, n_second = repair_overflow(n_minute, n_second, 60)
    n_hour, n_minute = repair_overflow(n_hour, n_minute, 60)
    n_day, n_hour = repair_overflow(n_day, n_hour, 24)
    if n_month in [1, 3, 5, 7, 8, 10, 12]:
        n_month, n_day = repair_overflow(n_month, n_day, 32, minval=1)
    elif n_month == 2:
        if n_year % 4:
            n_month, n_day = repair_overflow(n_month, n_day, 29, minval=1)
        else:
            n_month, n_day = repair_overflow(n_month, n_day, 30, minval=1)
    else:
        n_month, n_day = repair_overflow(n_month, n_day, 31, minval=1)
    n_year, n_month = repair_overflow(n_year, n_month, 13, minval=1)

    result = datetime.fromisoformat(f'{n_year:4}-{n_month:02}-{n_day:02}T{n_hour:02}:{n_minute:02}:{n_second:02}')
    result = result.replace(microsecond=int(usec * 1e6))
    return result


def fill_table_string_from_efrat(index, efrat_string, begin_datetime, end_datetime, std, dont_use_config):
    # В конце строки 0x00
    a = efrat_string[:-1].replace('- ', '-').split()

    datetime_local_out = efrat_to_datetime(*a[0:6])
    # Долбаный efrat не знает про отвод часов на час назад, зато efratp2015 использует только UT/UTC
    if dont_use_config:
        datetime_local_out = (datetime_local_out + timedelta(hours=-1))
    az_out_str = f'{float(a[6]):+03.0f}'
    h_per = float(a[7])
    a_obj = float(a[8])
    h_obj = float(a[9])
    ra_h = int(a[10])
    ra_m = int(a[11])
    ra_s = float(a[12])
    ra_degrees = (ra_h + (ra_m + ra_s / 60) / 60) / 24 * 360
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
    nut_ra = float(a[20])
    p_obj = float(a[21])
    p_diag = float(a[22])
    va = float(a[23])
    vh = float(a[24])
    if begin_datetime <= datetime_local_out <= end_datetime:
        idx = str(index)
        return [idx, az_out_str, datetime_local_out, h_per, DEFAULT_APERTURE, DEFAULT_RETRACT, DEFAULT_BEFORE,
                DEFAULT_AFTER, DEFAULT_TRACK, a_obj, h_obj, ra_degrees, dec_degrees, sid_time_degrees, refr, nut_ra,
                p_obj, p_diag, va, vh, std]


def get_rolled_point_ra_dec(ref_point, ref_time: astropy.time.Time,
                            obs_time: astropy.time.Time) -> tuple:
    r_point = SkyCoord(ref_point[0] * u.arcsec, ref_point[1] * u.arcsec,
                       frame=coordinates.frames.Helioprojective, observer='earth', obstime=ref_time)
    rolled_point = astropy.coordinates.SkyCoord(
        coordinates.RotatedSunFrame(base=r_point, duration=(obs_time - ref_time).value * astropy.units.d,
                                    rotation_model='howard'))
    cf = coordinates.Helioprojective(obstime=obs_time, observer='earth')
    gcrs_point = rolled_point.transform_to(cf).transform_to('gcrs')
    ra, dec = gcrs_point.to_string('hmsdms', precision=2).split()
    return ra, dec


def run_efrat(s):
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
    return efrat_strings


def make_object_label(object_name, use_solar_object, solar_object_name):
    object_label = object_name
    if object_name in PLANETS:
        object_label = object_label[1:-1]
        if use_solar_object:
            object_label += f':{solar_object_name}'
        object_label.replace(' ', ':')
    return object_label


def write_observer_schedule(observer_schedule, object_label, pd_table, dir_name):
    observer_heading = f'Объект {object_label}, наблюдения {pd_table["date_time"].iloc[0].strftime("%Y-%m-%d")}\n\n'
    with open(f'{dir_name}/observer.txt', 'w') as f:
        f.write(observer_heading)
        f.write(observer_schedule)


def write_operator_schedule(operator_schedule, object_label, pd_table, dir_name):
    operator_heading = f'Объект {object_label}, наблюдения {pd_table["date_time"].iloc[0].strftime("%Y-%m-%d")}\n\n'
    with open(f'{dir_name}/operator.txt', 'w') as f:
        f.write(operator_heading)
        f.write(operator_schedule)


def write_stop(dir_name):
    with open(f'{dir_name}/stop', 'w') as f:
        f.write('#!/bin/sh\n')
        f.write(f'# Остановка движения облучателя\n\n')
        f.write("/home/sun/tmp/tcpMB/tcpio -m10 -u1 -r192.168.9.14 -l2 -p503\n")
    p = subprocess.run(f'chmod 755 {dir_name}/stop', shell=True)


def write_at_rmall(dir_name):
    with open(f'{dir_name}/at_rmall', 'w') as f:
        f.write('#!/bin/sh\n')
        f.write(f'# Отмена всех заданий at\n\n')
        f.write("for i in `atq | awk '{print $1}'`; do atrm $i; done\n")
    p = subprocess.run(f'chmod 755 {dir_name}/at_rmall', shell=True)


def write_at_job(at_job, object_label, pd_table, dir_name):
    with open(f'{dir_name}/at_job', 'w') as f:
        f.write('#!/bin/sh\n\n')
        f.write(f'# Объект {object_label}, наблюдения {pd_table["date_time"].iloc[0].strftime("%Y-%m-%d")}\n\n')
        f.write(at_job)
        f.write('\n')
    p = subprocess.run(f'chmod 755 {dir_name}/at_job', shell=True)


def generate_observer_entry_body(after, az_m1, az_p1, azimuth, culm_minus_one, culm_plus_one, culmination, rpm):
    return f'{az_p1}: {culm_plus_one.strftime("%H:%M:%S")}\n' \
           f'{azimuth}: {culmination.strftime("%H:%M:%S")} (кульминация) {rpm:6.2f} rpm\n' \
           f'{az_m1}: {culm_minus_one.strftime("%H:%M:%S")} ' \
           f'антенна уходит в {(culmination + timedelta(minutes=after)).strftime("%H:%M:%S")}\n'


def generate_observer_entry_head(az_p2, culm_plus_two):
    observer_entry = f'\n{az_p2}: {culm_plus_two.strftime("%H:%M:%S")}\n'
    return observer_entry


def generate_skip_observer_entry(az_p2, culm_plus_two):
    return f'\n{az_p2} ({culm_plus_two.strftime("%H:%M:%S")}) пропускаем\n'


def generate_observer_transit_entry(azimuth, culmination, obs_start, rolling_start):
    return f'\n{azimuth}: Транзит; кульминация в {culmination.strftime("%H:%M:%S")}; ' \
           f'начало в {obs_start.strftime("%H:%M:%S")}, ' \
           f'перекатка в {rolling_start.strftime("%H:%M:%S")}\n'
