import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from defaults import DEFAULT_CARRIAGE_POS, DEFAULT_CARRIAGE_AMPLITUDE, DEFAULT_CARRIAGE_MOTION1, \
    DEFAULT_CARRIAGE_MOTION2

from utils import head_style, head_input_style, make_checkbox


def make_carriagepos_input(identifier, value):
    return dbc.Input(value=value, id=identifier, type='number', style={**head_input_style, **{'width': '7em'}},
                     class_name='border-dark', size='sm', min=-150000, max=150000, step=1,
                     list='carriage-position-hints')


def make_amplitude_input(identifier, value):
    return dbc.Input(value=value, id=identifier, type='number', style={**head_input_style, **{'min-width': '7em'}},
                     class_name='border-dark w-75', size='sm', min=0, max=200000, step=1)


def make_carmove_input(identifier, value):
    return dbc.Input(value=value, debounce=True, id=identifier, type='text',
                     style={**head_input_style, **{'min-width': '10em'}}, class_name='border-dark w-75', size='sm')


def azimuth_head():
    return html.Div('Азимут', style=head_style, className='pb-3 h-100')


def azimuth_column(pd_table):
    return pd_table['azimuth'].apply(lambda x: f'{int(x):+03d}')


def date_head():
    return html.Div('Дата', style=head_style, className='pb-3 h-100')


def date_column(pd_table):
    return pd_table['date_time'].apply(lambda x: x.strftime('%Y-%m-%d'))


def carenabled_head():
    return html.Div([
        html.Div('Разрешить‌', style=head_style, className='me-2 align-bottom', id='tt-carenabled'),
        dbc.Tooltip('Разрешить движение каретки', target='tt-carenabled', placement='top'),
        html.Div([
            dbc.Button('✓', id='carenabled-set-all', size='sm', style=head_style, class_name='align-bottom'),
            dbc.Tooltip('Выбрать все', target='carenabled-set-all', placement='bottom'),
            dbc.Button('✗', id='carenabled-reset-all', size='sm', class_name='align-bottom'),
            dbc.Tooltip('Сбросить все', target='carenabled-reset-all', placement='bottom')
        ], className='d-block')
    ])


def carenabled_column(pd_table):
    return pd_table[['idx', 'carenabled']].apply(
        lambda x: make_checkbox({'type': 'carenabled', 'index': str(x['idx'])}, x['carenabled']), axis=1)


def carriagepos_head(position=DEFAULT_CARRIAGE_POS):
    return html.Div([
        html.Div('Положение', style=head_style, className='me-2 align-bottom', id='tt-carriagepos'),
        dbc.Tooltip('Центральное положение каретки', target='tt-carriagepos', placement='top'),
        html.Div([
            make_carriagepos_input('carriagepos-value-all', position),
            dbc.Button('↓', id='carriagepos-set-all', size='sm', class_name='align-bottom'),
            dbc.Tooltip('Установить значение для всех азимутов', target='carriagepos-set-all', placement='bottom')
        ], className='d-block', style={'max-width': '123px', 'min-width': '123px'})
    ])


def carriagepos_column(pd_table):
    return pd_table[['idx', 'carriagepos']].apply(
        lambda x: make_carriagepos_input({'type': 'carriagepos', 'index': str(x['idx'])}, x['carriagepos']), axis=1)


def oscenabled_head():
    return html.Div([
        html.Div('Осцилл.', style=head_style, className='me-2 align-bottom', id='tt-oscenabled'),
        dbc.Tooltip('Разрешить осцилляцию вокруг центрального положения', target='tt-oscenabled', placement='top'),
        html.Div([
            dbc.Button('✓', id='oscenabled-set-all', size='sm', style=head_style, class_name='align-bottom'),
            dbc.Tooltip('Выбрать все', target='oscenabled-set-all', placement='bottom'),
            dbc.Button('✗', id='oscenabled-reset-all', size='sm', class_name='align-bottom'),
            dbc.Tooltip('Сбросить все', target='oscenabled-reset-all', placement='bottom')
        ], className='d-block')
    ])


def oscenabled_column(pd_table):
    return pd_table[['idx', 'oscenabled']].apply(
        lambda x: make_checkbox({'type': 'oscenabled', 'index': str(x['idx'])}, x['oscenabled']), axis=1)


def amplitude_head(amplitude=DEFAULT_CARRIAGE_AMPLITUDE):
    return html.Div([
        html.Div('Амплитуда', style=head_style, className='me-2 align-bottom', id='tt-amplitude'),
        dbc.Tooltip('Амплитуда движения каретки относительно центрального положения', target='tt-amplitude', placement='top'),
        html.Div([
            make_amplitude_input('amplitude-value-all', amplitude),
            dbc.Button('↓', id='amplitude-set-all', size='sm', class_name='align-bottom'),
            dbc.Tooltip('Установить значение для всех азимутов', target='amplitude-set-all', placement='bottom')
        ], className='d-block', style={'min-width': '123px'})
    ])


def amplitude_column(pd_table):
    return pd_table[['idx', 'amplitude']].apply(
        lambda x: make_amplitude_input({'type': 'amplitude', 'index': str(x['idx'])}, x['amplitude']), axis=1)


def carmove1_head(carmove1=DEFAULT_CARRIAGE_MOTION1):
    return html.Div([
        html.Div('Параметры 1', style=head_style, className='me-2 align-bottom', id='tt-carmove1'),
        dbc.Tooltip('Скорость, ускорение, замедление и пауза в прямом направлении', target='tt-carmove1', placement='top'),
        html.Div([
            make_carmove_input({'type': 'carmove1-value-all', 'index': '0'}, carmove1),
            dbc.Button('↓', id='carmove1-set-all', size='sm', class_name='align-bottom'),
            dbc.Tooltip('Установить значение для всех азимутов', target='carmove1-set-all', placement='bottom')
        ], className='d-block w-100', style={'min-width': '162px'})
    ])


def carmove1_column(pd_table):
    return pd_table[['idx', 'speed1', 'accel1', 'decel1', 'dwell1']].apply(
        lambda x: make_carmove_input({'type': 'carmove1', 'index': str(x['idx'])}, f'{int(x["speed1"])}/{int(x["accel1"])}/{int(x["decel1"])}/{int(x["dwell1"])}'), axis=1)


def carmove2_head(carmove2=DEFAULT_CARRIAGE_MOTION2):
    return html.Div([
        html.Div('Параметры 2', style=head_style, className='me-2 align-bottom', id='tt-carmove2'),
        dbc.Tooltip('Скорость, ускорение, замедление и пауза в обратном направлении', target='tt-carmove2', placement='top'),
        html.Div([
            make_carmove_input({'type': 'carmove2-value-all', 'index': '0'}, carmove2),
            dbc.Button('↓', id='carmove2-set-all', size='sm', class_name='align-bottom'),
            dbc.Tooltip('Установить значение для всех азимутов', target='carmove2-set-all', placement='bottom')
        ], className='d-block w-100', style={'min-width': '162px'})
    ])


def carmove2_column(pd_table):
    return pd_table[['idx', 'speed2', 'accel2', 'decel2', 'dwell2']].apply(
        lambda x: make_carmove_input({'type': 'carmove2', 'index': str(x['idx'])}, f'{int(x["speed2"])}/{int(x["accel2"])}/{int(x["decel2"])}/{int(x["dwell2"])}'), axis=1)


def make_carriage_html_table(pd_table):
    table_out_df = pd.DataFrame({
        azimuth_head(): azimuth_column(pd_table),
        date_head(): date_column(pd_table),
        carenabled_head(): carenabled_column(pd_table),
        carriagepos_head(): carriagepos_column(pd_table),
        oscenabled_head(): oscenabled_column(pd_table),
        amplitude_head(): amplitude_column(pd_table),
        carmove1_head(): carmove1_column(pd_table),
        carmove2_head(): carmove2_column(pd_table),
    })
    result = html.Div(dbc.Table.from_dataframe(table_out_df, striped=True, bordered=True),
                      style={'font-size': '0.9em'}),
    return result
