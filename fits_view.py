from datetime import datetime

import dash_bootstrap_components as dbc
from dash import html

from utils import card_style

AIA_CHANNELS = ['94', '131', '171', '193', '211', '304', '335', '1600', '1700', '4500']
items = list(map(lambda x: dbc.DropdownMenuItem(x, id={"type": "aia_ch", "val": x}), AIA_CHANNELS))

load_fits_body = dbc.Container([
    dbc.Card([dbc.CardBody([
        dbc.Row([dbc.Col([dbc.Row([
            dbc.Col([
                dbc.Label('Время (примерно)'),
                dbc.Input(id='load-fits-time', type='datetime-local', size='sm',
                          value=datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), style={'background-color': '#272b30', 'color': '#aaa'}),
            ], width=8),
            dbc.Col([
                dbc.Label('Канал'),
                dbc.DropdownMenu(children=items, label='171', size='sm', class_name='d-grid', id='aia-wavelength',
                                 style={'height': '30px'})
            ], width=4),
        ])], width=7),
            dbc.Col([
                dbc.Label('‌‌', class_name='d-block'),
                dbc.Button('Отправить запрос', id='fits-send-request', type='datetime-local', size='sm',
                           style={'min-width': '200px'}),
            ], style={'text-align': 'right'}, width=5)
        ]),
    ])], style=card_style),
    dbc.Card([
        html.Div(id='query-result', style={'width': '100%', 'height': '450px', 'overflow': 'scroll'})
    ], body=True),
    dbc.Card([
        dbc.Label(['‌‌'], id='fits-name', style={'color': '#f7f7f7'})
    ], style=card_style, body=True)
])

fits_modal = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle('Выбор файла FITS')),
    dbc.ModalBody([load_fits_body], style={'max-height': '80%'}),
    dbc.ModalFooter([
        dbc.Button('Выбрать', id='load-fits-ok', className='btn btn-primary btn-sm"',
                   style={'height': '30.833px', 'padding-top': '0', 'padding-bottom': '0'}),
        dbc.Button('Отмена', id='load-fits-cancel', className='btn btn-primary btn-sm"',
                   style={'height': '30.833px', 'padding-top': '0', 'padding-bottom': '0'})
    ]),
], id='modal-fits', is_open=False, scrollable=True, class_name='modal-lg')
