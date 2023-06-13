import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from utils import head_style, head_input_style, make_dropdown, make_checkbox, deg_to_dms

from defaults import DEFAULT_DURATION_BEFORE, DEFAULT_DURATION_AFTER

APERTURES = ['167', '61', '51', '41']


def make_aperture_dropdown(identifier, label, marginleft='0px'):
    return make_dropdown(identifier, label, items=APERTURES,
                         marginleft=marginleft, width='6em')


def make_duration_input(identifier, value):
    return dbc.Input(value=value, id=identifier, type='number', style=head_input_style, class_name='border-dark',
                     size='sm', min=1, max=15, step=0.1)


def std_head():
    return html.Div([
        html.Div('Штатный', style=head_style, className='me-2 align-bottom', id='tt-std'),
        dbc.Tooltip('Установки для центра Солнца', target='tt-std', placement='top'),
        html.Div([
            dbc.Button('✓', id='std-set-all', size='sm', style=head_style, class_name='align-bottom'),
            dbc.Tooltip('Выбрать все', target='std-set-all', placement='bottom'),
            dbc.Button('✗', id='std-reset-all', size='sm', style=head_style, class_name='align-bottom'),
            dbc.Tooltip('Сбросить все', target='std-reset-all', placement='bottom')
        ], className='d-block')
    ])


def std_column(pd_table):
    return pd_table[['idx', 'std']].apply(
        lambda x: make_checkbox({'type': 'std', 'index': str(x['idx'])}, x['std']), axis=1)


def motion_head():
    return html.Div([
        html.Div('Сопр.', style=head_style, className='me-2 align-bottom', id='tt-track'),
        dbc.Tooltip('Включить в расписание движения облучателя в режиме сопровождения', target='tt-track',
                    placement='top'),
        html.Div([
            dbc.Button('✓', id='track-set-all', size='sm', style=head_style, class_name='align-bottom'),
            dbc.Tooltip('Выбрать все', target='track-set-all', placement='bottom'),
            dbc.Button('✗', id='track-reset-all', size='sm', style=head_style, class_name='align-bottom'),
            dbc.Tooltip('Сбросить все', target='track-reset-all', placement='bottom')
        ], className='d-block', style={'max-width': '61px', 'min-width': '61px'})
    ])


def motion_column(pd_table):
    return pd_table[['idx', 'track']].apply(
        lambda x: make_checkbox({'type': 'track', 'index': str(x['idx'])}, x['track']), axis=1)


def after_head(after):
    return html.Div([
        html.Div('После, мин', style=head_style, className='me-2 align-bottom', id='tt-after'),
        dbc.Tooltip('От кульминации до начала следующей установки антенны, мин', target='tt-after',
                    placement='top'),
        html.Div([
            make_duration_input('after-value-all', after),
            dbc.Button('↓', id='after-set-all', size='sm', class_name='align-bottom'),
            dbc.Tooltip('Установить значение для всех азимутов', target='after-set-all', placement='bottom')
        ], className='d-block', style={'max-width': '110px', 'min-width': '110px'})
    ])


def after_column(pd_table):
    return pd_table[['idx', 'after']].apply(
        lambda x: make_duration_input({'type': 'after', 'index': str(x['idx'])}, x['after']), axis=1)


def before_head(before):
    return html.Div([
        html.Div('До, мин', style=head_style, className='me-2 align-bottom', id='tt-before'),
        dbc.Tooltip('От установки антенны до кульминации, мин', target='tt-before', placement='top'),
        html.Div([
            make_duration_input('before-value-all', before),
            dbc.Button('↓', id='before-set-all', size='sm', class_name='align-bottom'),
            dbc.Tooltip('Установить значение для всех азимутов', target='before-set-all', placement='bottom')
        ], className='d-block', style={'max-width': '110px', 'min-width': '110px'})
    ])


def before_column(pd_table):
    return pd_table[['idx', 'before']].apply(
        lambda x: make_duration_input({'type': 'before', 'index': str(x['idx'])}, x['before']), axis=1)


def retract_head():
    return html.Div([
        html.Div('Отвод  ‌', style=head_style, className='me-2 align-bottom', id='tt-retract'),
        dbc.Tooltip('Отвод центральных щитов', target='tt-retract', placement='top'),
        html.Div([
            dbc.Button('✓', id='retract-set-all', size='sm', style=head_style, class_name='align-bottom'),
            dbc.Tooltip('Выбрать все', target='retract-set-all', placement='bottom'),
            dbc.Button('✗', id='retract-reset-all', size='sm', class_name='align-bottom'),
            dbc.Tooltip('Сбросить все', target='retract-reset-all', placement='bottom')
        ], className='d-block', style={'max-width': '61px', 'min-width': '61px'})
    ])


def retract_column(pd_table):
    return pd_table[['idx', 'retract']].apply(
        lambda x: make_checkbox({'type': 'retract', 'index': str(x['idx'])}, x['retract']), axis=1)


def aperture_head():
    return html.Div([
        html.Div('Апертура', style=head_style, className='me-2 align-bottom', id='tt-aperture'),
        dbc.Tooltip('Размер апертуры, щитов', target='tt-aperture', placement='top'),
        html.Div([
            make_aperture_dropdown({'type': 'aperture-value-all', 'index': '0'}, APERTURES[0]),
            dbc.Button('↓', id='aperture-set-all', size='sm', class_name='align-bottom'),
            dbc.Tooltip('Установить значение для всех азимутов', target='aperture-set-all', placement='bottom')
        ], className='d-block', style={'max-width': '110px', 'min-width': '110px'})
    ])


def aperture_column(pd_table):
    return pd_table[['idx', 'aperture']].apply(
        lambda x: make_aperture_dropdown({'type': 'aperture', 'index': str(x['idx'])}, x['aperture']), axis=1)


def height_head():
    return html.Div('Высота', style=head_style, className='py-3 h-100')


def height_column(pd_table):
    return pd_table['h_per'].apply(lambda x: deg_to_dms(x))


def time_head():
    return html.Div('Время', style=head_style, className='py-3 h-100')


def time_column(pd_table):
    return pd_table['date_time'].apply(lambda x: x.strftime('%H:%M:%S'))


def date_head():
    return html.Div('Дата', style=head_style, className='py-3 h-100')


def date_column(pd_table):
    return pd_table['date_time'].apply(lambda x: x.strftime('%Y-%m-%d'))


def azimuth_head():
    return html.Div('Азимут', style=head_style, className='py-3 h-100')


def azimuth_column(pd_table):
    return pd_table['azimuth']


def make_antenna_html_table(pd_table, is_sun, use_solar_object):
    table_out_df = pd.DataFrame({
        azimuth_head(): azimuth_column(pd_table),
        date_head(): date_column(pd_table),
        time_head(): time_column(pd_table),
        height_head(): height_column(pd_table),
        aperture_head(): aperture_column(pd_table),
        retract_head(): retract_column(pd_table),
        before_head(DEFAULT_DURATION_BEFORE): before_column(pd_table),
        after_head(DEFAULT_DURATION_AFTER): after_column(pd_table),
        motion_head(): motion_column(pd_table),
    })
    if is_sun and use_solar_object:
        table_out_df['std'] = std_column(pd_table)
        table_out_df.rename(columns={'std': std_head()}, inplace=True)

    result = html.Div(dbc.Table.from_dataframe(table_out_df, striped=True, bordered=True),
                      style={'font-size': '0.9em'}),
    return result
