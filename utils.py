from datetime import date, datetime, timedelta
import copy
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd

import shutil
import tempfile
import subprocess

print('utils')

DEFAULT_BEFORE = 6.1
DEFAULT_AFTER = 6.6
DEFAULT_APERTURE = '61'
DEFAULT_RETRACT = False
DEFAULT_TRACK = True

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
        print(source_name)
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
                    'width': '4em'}


def make_dropdown(identifier, label, marginleft: str = '30px'):
    item_ids = []
    for e in ['167', '61', '51', '41']:
        item_id = copy.deepcopy(identifier)
        item_id['type'] = item_id['type'] + ':item'
        item_id['val'] = e
        item_ids.append(item_id)

    st = copy.deepcopy(head_style)
    st['margin-left'] = marginleft

    return dbc.DropdownMenu(children=[
        dbc.DropdownMenuItem('167', id=item_ids[0]),
        dbc.DropdownMenuItem('61', id=item_ids[1]),
        dbc.DropdownMenuItem('51', id=item_ids[2]),
        dbc.DropdownMenuItem('41', id=item_ids[3]),
    ], label=label, style=st, size='sm', id=identifier)


def make_checkbox(identifier, value):
    return dbc.Checkbox(value=value, id=identifier, style={'margin-left': '30px'})


def make_input(identifier, value):
    return dbc.Input(value=value, id=identifier, type='number', style=head_input_style, size='sm', min=1, max=15,
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
    return f"{source}{az}    {culmination.strftime('%H:%M:%S.%f')[:-4]}     -{before.seconds / 60:4.2f}/{after.seconds / 60:4.2f}     P{az}     //     {deg_to_dms(hf)}\n"


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
                                       aperture: str):
    aperture_lookup = {
        '167': '130:00:00',
        '61': '52:00:00',
        '51': '44:00:00',
        '41': '36:00:00'
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
        start_time = table['DateTime'].iloc[0] - timedelta(minutes=30)
        stop_time = table['DateTime'].iloc[-1] + timedelta(minutes=30)

        f.write(main_csi_header_template_use_script(start_time, stop_time))

        current_date: date = table['DateTime'].iloc[0].date()
        f.write(f"\nObsDate = {current_date.strftime('%Y.%m.%d')}\n\n")

        for (azimuth, date_time, h_per, aperture, retract, before, after, track) \
                in zip(table['Azimuth'], table['DateTime'],
                       table['H_per'], table['Aperture'],
                       table['Retract'], table['Before'],
                       table['After'], table['Track']):
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
        start_time = df['DateTime'].iloc[0] - timedelta(minutes=30)
        stop_time = df['DateTime'].iloc[-1] + timedelta(minutes=30)

        f.write(flat_csi_header_template(start_time, stop_time))

        current_date: date = df['DateTime'].iloc[0].date()
        f.write(f"\nObsDate = {current_date.strftime('%Y.%m.%d')}\n\n")

        for (azimuth, date_time, h_per, aperture, retract, before, after, track) \
                in zip(df['Azimuth'], df['DateTime'],
                       df['H_per'], df['Aperture'],
                       df['Retract'], df['Before'],
                       df['After'], df['Track']):
            if date_time.date() > current_date:
                current_date = date_time.date()
                f.write(f"\nObsDate = {current_date.strftime('%Y.%m.%d')}\n\n")

            f.write(flat_csi_entry_template(object_name, azimuth, date_time, timedelta(minutes=before),
                                            timedelta(minutes=after), h_per))


def setup_and_run_csmakes(file_name_stub: str, object_name: str, df: pd.DataFrame):
    file_list = ['csephem', 'csmake', 'csmake2']
    src_path = 'efrat/common/'
    with tempfile.TemporaryDirectory() as td_name:
        for fn in file_list:
            shutil.copyfile(f'{src_path}/{fn}', f'{td_name}/{fn}')

        write_flat_csi(f'{td_name}/{file_name_stub}f.csi', object_name, df)
        write_main_csi(f'{td_name}/{file_name_stub}c.csi', object_name, df)

        p = subprocess.run(f'cd {td_name}; '
                           f'export PATH=$PATH:.; '
                           f'chmod 755 csmake; '
                           f'chmod 755 csmake2; '
                           f'chmod 755 csephem; '
                           f'csmake {file_name_stub}c.csi', capture_output=True, shell=True)

        q = subprocess.run(f'cd {td_name}; '
                           f'export PATH=$PATH:.; '
                           f'chmod 755 csmake; '
                           f'chmod 755 csmake2; '
                           f'chmod 755 csephem; '
                           f'csmake2 {file_name_stub}f.csi', capture_output=True, shell=True)

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
    return \
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


def calculate_rpm(A_obj, h_obj, Vad, Vhd, dec_degrees, seconds_per_degree300, P_diag, RA_degrees, sid_time_degrees):
    def deg2rad(x: float) -> float:
        return np.pi * x / 180

    A = deg2rad(A_obj)
    h = deg2rad(h_obj)
    dec = deg2rad(dec_degrees)
    print(RA_degrees)
    print(dec_degrees)

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

    ha = deg2rad(sid_time_degrees) - deg2rad(RA_degrees)

    sinha = np.sin(ha)
    cosha = np.cos(ha)
    tanha = np.tan(ha)

    # Позиционнвй угол диаграммы
    omega = np.arctan(sindec * tanha)
    cosomega = np.cos(omega)

    # "/с; 15"/с - скоростть изменения часового угла
    v_feed = (cosha * cosdec + sinha * tanha * cosdec * sindec ** 2) \
             / np.sqrt(1 - (sinha * cosdec) ** 2) * 15 * magic * cosomega

    # v_feed / 3600 - скорость в градусах в секунду
    rpm = 300 * seconds_per_degree300 * v_feed / 3600
    return timedelta(seconds=3600 / v_feed), rpm
