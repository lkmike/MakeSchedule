from datetime import date, datetime, timedelta

from pytz import timezone

# Расписания антенны
DEFAULT_DURATION_BEFORE = 6.1
DEFAULT_DURATION_AFTER = 6.6
DEFAULT_APERTURE = '61'
DEFAULT_RETRACT = False
DEFAULT_TRACK = True

# Движение каретки
DEFAULT_CARRIAGE_POS = 0
DEFAULT_CARRIAGE_ENABLED = False
DEFAULT_CARRIAGE_OSCENABLED = False
DEFAULT_CARRIAGE_AMPLITUDE = 50000
DEFAULT_CARRIAGE_SPEED1 = 200
DEFAULT_CARRIAGE_ACCEL1 = 200
DEFAULT_CARRIAGE_DECEL1 = 200
DEFAULT_CARRIAGE_DWELL1 = 2
DEFAULT_CARRIAGE_MOTION1 = '/'.join(list(map(str, [DEFAULT_CARRIAGE_SPEED1, DEFAULT_CARRIAGE_ACCEL1,
                                                   DEFAULT_CARRIAGE_DECEL1, DEFAULT_CARRIAGE_DWELL1])))
DEFAULT_CARRIAGE_SPEED2 = 800
DEFAULT_CARRIAGE_ACCEL2 = 200
DEFAULT_CARRIAGE_DECEL2 = 200
DEFAULT_CARRIAGE_DWELL2 = 2
DEFAULT_CARRIAGE_MOTION2 = '/'.join(list(map(str, [DEFAULT_CARRIAGE_SPEED2, DEFAULT_CARRIAGE_ACCEL2,
                                                   DEFAULT_CARRIAGE_DECEL2, DEFAULT_CARRIAGE_DWELL2])))

# Геометрия и кинематика каретки
DRIVE_TO_CM_SCALE = 1 / 8424 * 3
FAST_FEED_POSITION = 121000
SENSITIVE_FEED_POSITION = -46332
SOLAR_FEED_POSITION = 0

# Сбор
RESOLUTIONS = ['7.8 МГц', '3.9 МГц', '1.95 МГц', '976 кГц', '488 кГц', '244 кГц', '122 кГц']
AVG_POINTS = [64, 32, 16, 8, 4, 2, 1]
resolution_to_avgpts = dict(zip(RESOLUTIONS, AVG_POINTS))

POLARIZATIONS = ['Левая', 'Правая', 'Авто']
polarization_to_pol = dict(zip(POLARIZATIONS, [False, True, False]))
polarization_to_auto = dict(zip(POLARIZATIONS, [False, False, True]))

DEFAULT_ACQUISITION_RESOLUTION = RESOLUTIONS[1]
DEFAULT_ACQUISITION_POLARIZATION = POLARIZATIONS[2]
DEFAULT_ACQUISITION_ATTENUATION = -10
DEFAULT_REGSTART = DEFAULT_DURATION_BEFORE - 0.1
DEFAULT_REGSTOP = DEFAULT_DURATION_AFTER - 0.1
PULSE_DURATION = 5

SECONDS_BEFORE_OBS_RUN_BEGINS = 120
SECONDS_AFTER_OBS_RUN_ENDS = 120

#  Прочее
MAX_DAYS = 10
TIMEZONE = timezone('Europe/Moscow')
PLANETS = ['[Sun]', '[Moon]', '[Mercury]', '[Venus]', '[Earth]', '[Mars]', '[Jupiter]', '[Saturn]',
           '[Uranus]', '[Neptune]', '[Pluto]']
STELLAR_PRESETS = {
    'stellar-source-crab': {'ra': '05h34m32s', 'dec': '22d00m52.0s', 'name': 'Crab'},
    'stellar-source-cyga': {'ra': '19h57m44.5s', 'dec': '40d35m46.0s', 'name': 'CygA'},
    'stellar-source-3c84': {'ra': '03h19m48.16s', 'dec': '41d30m42.2s', 'name': '3c84'},
    'stellar-source-3c273': {'ra': '12h29m06.6s', 'dec': '02d03m08.6s', 'name': '3c273'}
}


def begin_observations_today():
    return (date.today()).strftime('%Y-%m-%dT%H:%M:%S')


def begin_observations_tomorrow():
    return (datetime.fromisoformat(f"{date.today().strftime('%Y-%m-%d')}")
            + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S')


def end_observations_today():
    return (datetime.fromisoformat(f"{date.today().strftime('%Y-%m-%d')}")
            + timedelta(hours=23, minutes=59)).strftime('%Y-%m-%dT%H:%M:%S')


def end_observations_tomorrow():
    return (datetime.fromisoformat(f"{date.today().strftime('%Y-%m-%d')}")
            + timedelta(days=1, hours=23, minutes=59)).strftime('%Y-%m-%dT%H:%M:%S')


DEFAULT_BEGIN_OBSERVATIONS = begin_observations_today
DEFAULT_END_OBSERVATIONS = end_observations_tomorrow
DEFAULT_AZIMUTH_LIST = '+24, +12, +0, -12, -24'
DEFAULT_SOLAR_X = 0
DEFAULT_SOLAR_Y = 0


def presumable_aia_time():
    current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
    return (current_hour - timedelta(hours=1)).astimezone(timezone('UTC')).isoformat()


DEFAULT_AIA_TIME = presumable_aia_time
DEFAULT_OBJECT = '[Sun]'
DEFAULT_OBJECT_ID = '[Sun]'

RUNS_GAP = timedelta(hours=12)


def debug_time(i):
    gen = [0, 1, 3, 4, 6, 7, 9, 10, 12, 13, 15, 16, 18, 19, 21, 22, 24, 25]
    return datetime.now() + timedelta(minutes=5) + gen[i] * timedelta(minutes=9)


DEBUG = False

if DEBUG:

    RUNS_GAP = timedelta(minutes=12)
    # DEFAULT_OBJECT = '2' # CygA
    # DEFAULT_OBJECT_ID = 'CygA'
    DEFAULT_AZIMUTH_LIST = '+24, +12'

    DEFAULT_TRACK = False

    DEFAULT_DURATION_BEFORE = 2.6
    DEFAULT_DURATION_AFTER = 2.6

    DEFAULT_CARRIAGE_POS = SOLAR_FEED_POSITION
    DEFAULT_CARRIAGE_ENABLED = True
    DEFAULT_CARRIAGE_OSCENABLED = True
    DEFAULT_CARRIAGE_AMPLITUDE = 50000
    DEFAULT_CARRIAGE_SPEED1 = 200
    DEFAULT_CARRIAGE_ACCEL1 = 200
    DEFAULT_CARRIAGE_DECEL1 = 200
    DEFAULT_CARRIAGE_DWELL1 = 2
    DEFAULT_CARRIAGE_MOTION1 = '/'.join(list(map(str, [DEFAULT_CARRIAGE_SPEED1, DEFAULT_CARRIAGE_ACCEL1,
                                                       DEFAULT_CARRIAGE_DECEL1, DEFAULT_CARRIAGE_DWELL1])))
    DEFAULT_CARRIAGE_SPEED2 = 200
    DEFAULT_CARRIAGE_ACCEL2 = 200
    DEFAULT_CARRIAGE_DECEL2 = 200
    DEFAULT_CARRIAGE_DWELL2 = 2
    DEFAULT_CARRIAGE_MOTION2 = '/'.join(list(map(str, [DEFAULT_CARRIAGE_SPEED2, DEFAULT_CARRIAGE_ACCEL2,
                                                       DEFAULT_CARRIAGE_DECEL2, DEFAULT_CARRIAGE_DWELL2])))
