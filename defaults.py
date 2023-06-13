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

