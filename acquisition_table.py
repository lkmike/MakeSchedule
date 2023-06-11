import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from utils import *

resolutions = ['7.8 МГц', '3.9 МГц', '1.95 МГц', '976 кГц', '488 кГц', '244 кГц', '122 кГц']
polarizations = ['Левая', 'Правая', 'Авто']


def make_attenuation_input(identifier, value):
    return dbc.Input(value=value, id=identifier, type='number', style=head_input_style, class_name='border-dark',
                     size='sm', min=-31.5, max=0, step=0.5)


def make_reg_input(identifier, value):
    return dbc.Input(value=value, id=identifier, type='number', style=head_input_style, class_name='border-dark',
                     size='sm', min=0, max=15, step=0.1)


def make_resolution_dropdown(identifier, label, marginleft='0px'):
    return make_dropdown(identifier, label, items=resolutions, marginleft=marginleft, width='6em')


def make_polarization_dropdown(identifier, label, marginleft: str = '0px'):
    items = list(map(lambda x: f'{x} дБ', np.arange(0, -32, -0.5)))
    return make_dropdown(identifier, label, items=polarizations, marginleft=marginleft, width='6em')


def azimuth_head():
    return html.Div('Азимут', style=head_style, className='py-3 h-100')


def azimuth_column(pd_table):
    return pd_table['azimuth']


def date_head():
    return html.Div('Дата', style=head_style, className='py-3 h-100')


def date_column(pd_table):
    return pd_table['date_time'].apply(lambda x: x.strftime('%Y-%m-%d'))


def resolution_head():
    return html.Div([
        html.Div('Разрешение', style=head_style, className='me-2 align-bottom', id='tt-resolution'),
        dbc.Tooltip('Разрешение по частоте', target='tt-resolution', placement='top'),
        html.Div([
            make_resolution_dropdown({'type': 'resolution-value-all', 'index': '0'}, resolutions[1]),
            dbc.Button('↓', id='resolution-set-all', size='sm', class_name='align-bottom'),
            dbc.Tooltip('Установить значение для всех азимутов', target='aperture-set-all', placement='bottom')
        ], className='d-block')
    ])


def resolution_column(pd_table):
    return pd_table[['idx', 'resolution']].apply(
        lambda x: make_resolution_dropdown({'type': 'resolution', 'index': str(x['idx'])}, x['resolution']), axis=1)


def attenuation_head(attenuation):
    return html.Div([
        html.Div('Ослабление', style=head_style, className='me-2 align-bottom', id='tt-attenuation'),
        dbc.Tooltip('Установка общего аттенюатора', target='tt-attenuation', placement='top'),
        html.Div([
            make_attenuation_input('attenuation-value-all', attenuation),
            dbc.Button('↓', id='attenuation-set-all', size='sm', class_name='align-bottom'),
            dbc.Tooltip('Установить значение для всех азимутов', target='attenuation-set-all', placement='bottom')
        ], className='d-block')
    ])


def attenuation_column(pd_table):
    return pd_table[['idx', 'attenuation']].apply(
        lambda x: make_attenuation_input({'type': 'attenuation', 'index': str(x['idx'])}, x['attenuation']), axis=1)


def polarization_head():
    return html.Div([
        html.Div('Поляризация', style=head_style, className='me-2 align-bottom', id='tt-polarization'),
        dbc.Tooltip('Левая/правая/автоматическое переключение', target='tt-polarization', placement='top'),
        html.Div([
            make_polarization_dropdown({'type': 'polarization-value-all', 'index': '0'}, polarizations[-1]),
            dbc.Button('↓', id='polarization-set-all', size='sm', class_name='align-bottom'),
            dbc.Tooltip('Установить значение для всех азимутов', target='polarization-set-all', placement='bottom')
        ], className='d-block')
    ])


def polarization_column(pd_table):
    return pd_table[['idx', 'polarization']].apply(
        lambda x: make_polarization_dropdown({'type': 'polarization', 'index': str(x['idx'])}, x['polarization']),
        axis=1)


def regstart_head(attenuation):
    return html.Div([
        html.Div('Запуск', style=head_style, className='me-2 align-bottom', id='tt-regstart'),
        dbc.Tooltip('Промежуток времени между началом импульса калибровки в начале регистрации и кульминацией', target='tt-regstart', placement='top'),
        html.Div([
            make_reg_input('regstart-value-all', attenuation),
            dbc.Button('↓', id='regstart-set-all', size='sm', class_name='align-bottom'),
            dbc.Tooltip('Установить значение для всех азимутов', target='regstart-set-all', placement='bottom')
        ], className='d-block')
    ])


def regstart_column(pd_table):
    return pd_table[['idx', 'regstart']].apply(
        lambda x: make_reg_input({'type': 'regstart', 'index': str(x['idx'])}, x['regstart']), axis=1)


def regstop_head(attenuation):
    return html.Div([
        html.Div('Остановка', style=head_style, className='me-2 align-bottom', id='tt-regstop'),
        dbc.Tooltip('Промежуток времени между кульминацией и началом импульса калибровки в конце регистрации ', target='tt-regstop', placement='top'),
        html.Div([
            make_reg_input('regstop-value-all', attenuation),
            dbc.Button('↓', id='regstop-set-all', size='sm', class_name='align-bottom'),
            dbc.Tooltip('Установить значение для всех азимутов', target='regstop-set-all', placement='bottom')
        ], className='d-block')
    ])


def regstop_column(pd_table):
    return pd_table[['idx', 'regstop']].apply(
        lambda x: make_reg_input({'type': 'regstop', 'index': str(x['idx'])}, x['regstop']), axis=1)


def make_acquisition_html_table(pd_table, attenuation, regstart, regstop):
    table_out_df = pd.DataFrame({
        azimuth_head(): azimuth_column(pd_table),
        date_head(): date_column(pd_table),
        resolution_head(): resolution_column(pd_table),
        attenuation_head(attenuation): attenuation_column(pd_table),
        polarization_head(): polarization_column(pd_table),
        regstart_head(regstart): regstart_column(pd_table),
        regstop_head(regstop): regstop_column(pd_table),
    })
    result = html.Div(dbc.Table.from_dataframe(table_out_df, striped=True, bordered=True),
                      style={'font-size': '0.9em'}),
    return result


