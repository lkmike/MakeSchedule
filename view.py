import dash.dcc
from dash import dcc, html
import dash_bootstrap_components as dbc

from dash_bootstrap_templates import load_figure_template
import dash_split_pane

from datetime import datetime

# import model
# from controller import *

print('view enters')

load_figure_template('darkly')

# fig_style = {'height': '100%', 'width': '100%'}
card_style = {'width': '100%',
              'padding': '0px',
              'border-width': '0px'
              }  # , 'margin-top': '10px', 'margin-bottom': '0px', 'margin-left': '5px', 'margin-right': '5px'}

fits_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

pan_ctrl = dbc.Card([dbc.CardBody([
    dbc.Row([
        dbc.Col(dbc.Input(id='aia-datetime-input', type='datetime-local', value=fits_time, step='1',
                          size='sm'), width=5),
        dbc.Col(html.Div(
            [dbc.Button('В полночь', id='aia-datetime-midnight-button', color='secondary', className='me-2 w-100',
                        size='sm')], className='d-grid d-block'), width=2),
        dbc.Col(html.Div(
            [dbc.Button('Сейчас', id='aia-datetime-now-button', color='secondary', className='me-2 w-100', size='sm')],
            className='d-grid d-block'), width=2),
        dbc.Col(html.Div(
            [dbc.Button('Загрузить', id='aia-load-button', color='primary', className='me-2 w-100', size='sm')],
            className='d-grid d-block'), width=3),
    ])]),
], style=card_style)

pan_aia_plot = dbc.Card([dbc.CardBody(
    'A'
)], class_name='flex-grow-1', style=card_style)

pan_sun_point = dbc.Card([dbc.CardBody(
    'B'
)], style=card_style)

tab_aia = dbc.Card([
    pan_ctrl,
    pan_aia_plot,
    pan_sun_point
], class_name='h-100 force-fill-height d-flex flex-column', style=card_style)

tab_email = dbc.Card([dbc.CardBody([
    dbc.Input(id='jsoc-email', size='sm', type='email', value='m.k.lebedev@gmail.com'),
    dbc.Card(dbc.CardBody([html.P(['Адрес должен быть зарегистрирован в JSOC, чтобы можно было скачивать оттуда '
                                   'данные. Это можно сделать здесь: ',
                                   dcc.Link('http://jsoc.stanford.edu/ajax/exportdata.html',
                                            href='http://jsoc.stanford.edu/ajax/exportdata.html', target='window'),
                                   '.'])])),
])], style=card_style),

tab_sun = dbc.Container(dbc.Tabs([
    dbc.Tab(tab_aia, label='FITS', id='fits-tab',
            active_label_class_name='text-info'),
    dbc.Tab(tab_email, label='Адрес электронной почты для JSOC', id='email-tab',
            active_label_class_name='text-info'),
]))

tab_stellar = dbc.Container([
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([dbc.Label('Объект'),
                         dbc.Row(dbc.Col(
                             dbc.Select(options=[
                                 {'label': 'Краб', 'value': '1'},
                                 {'label': 'Лебедь А', 'value': '2'},
                                 {'label': '3c84', 'value': '3'},
                                 {'label': '3c273', 'value': '4'},
                                 {'label': 'Солнце', 'value': '[Sun]'},
                                 {'label': 'Луна', 'value': '[Moon]'}
                             ], id='stellar-source', size='sm', value='[Sun]', class_name='bg-dark text-secondary')
                         ))], width=3),
                dbc.Col([dbc.Label('‌'),
                         dbc.Row(dbc.Col(dbc.Button('>', id='stellar-source-submit-button', size='sm')))], width=1),
                dbc.Col([dbc.Label('Название'),
                         dbc.Row(dbc.Col(dbc.Input(id='stellar-name', size='sm', value='[Sun]')))], width=2),
                dbc.Col([dbc.Label('α'),
                         dbc.Row(dbc.Col(dbc.Input(id='stellar-ra', size='sm', value='')))], width=3),
                dbc.Col([dbc.Label('δ'),
                         dbc.Row(dbc.Col(dbc.Input(id='stellar-dec', size='sm', value='')))], width=3),
            ]),
        ]),

        dbc.CardBody([
            dbc.Row([dbc.Col([dbc.Label("Координаты на Солнце", class_name='d-inline-block'),
                              dbc.Checkbox(value=False, disabled=False, id='use-solar-object',
                                           class_name='m-3 d-inline-block')], width=7)]),
            dbc.Row([
                dbc.Col([dbc.Label('ID'),
                         dbc.Row(dbc.Col(dbc.Input(id='solar-object-name', size='sm', value='NOAA_')))], width=3),
                dbc.Col([dbc.Label([html.I('t'), html.Sub(" ref")]),
                         dbc.Row([
                             dbc.Col(dbc.Input(id='solar-ref-time', value='2023-06-01T21:03:09', debounce=True,
                                               step='1', size='sm')),
                             html.Div([], id='solar-ref-time-sink')
                         ])], width=5),
                dbc.Col([dbc.Label(['θ', html.Sub(html.I("x ")), ', ″']),
                         dbc.Row(dbc.Col(
                             dbc.Input(id='solar-lon', type='number', value='-875', min=-1100, max=1100, step=1,
                                       size='sm')
                         ))], width=2),
                dbc.Col([dbc.Label(['θ', html.Sub(html.I("y ")), ', ″']),
                         dbc.Row(dbc.Col(
                             dbc.Input(id='solar-lat', type='number', value='-112', min=-1100, max=1100, step=1,
                                       size='sm')
                         ))], width=2),
            ])
        ]),
    ], style=card_style),
    dbc.Card([dbc.CardBody([])], style=card_style)
], class_name='mw-100')

source_tabs = dbc.Tabs([
    dbc.Tab(tab_stellar, label='Объекты без затей', active_label_class_name='text-info'),
    dbc.Tab(tab_sun, label='Точка на Солнце', class_name='h-100',
            active_label_class_name='text-info'),
])

left_pan = dbc.Card(
    children=[tab_stellar], class_name='h-100'
)

common_ctrl = dbc.Container([
    dbc.Card([dbc.CardBody([dbc.Row([
        dbc.Col([dbc.Label('Начало наблюдений'),
                 dbc.Row(
                     # [dbc.Col(dbc.Input(id='schedule-begin-datetime-input', type='datetime-local', size='sm'), width=6),
                     [dbc.Col(dbc.Input(id='schedule-begin-datetime-input', type='datetime-local', size='sm',
                                        value=(datetime.fromisoformat('2023-06-02T00:00:00')).strftime(
                                            '%Y-%m-%dT%H:%M:%S')), width=6),
                      dbc.Col(html.Div([dbc.Button('Сегодня', id='schedule-begin-date-today-button',
                                                   color='secondary', className='me-2', size='sm',
                                                   style={'minWidth': '73px', 'width': '40%'}),
                                        dbc.Button('Завтра', id='schedule-begin-date-tomorrow-button',
                                                   color='secondary', className='me-2', size='sm',
                                                   style={'minWidth': '73px', 'width': '40%'})],
                                       className='d-block'), width=6)
                      ])], width=6),
        dbc.Col([dbc.Label('Конец наблюдений'),
                 dbc.Row(
                     # [dbc.Col(dbc.Input(id='schedule-end-datetime-input', type='datetime-local', size='sm'), width=6),
                     [dbc.Col(dbc.Input(id='schedule-end-datetime-input', type='datetime-local', size='sm',
                                        value=(datetime.fromisoformat('2023-06-02T23:00:00')).strftime(
                                            '%Y-%m-%dT%H:%M:%S')), width=6),
                      dbc.Col(html.Div([dbc.Button('Сегодня', id='schedule-end-date-today-button',
                                                   color='secondary', className='me-2', size='sm',
                                                   style={'minWidth': '73px', 'width': '40%'}),
                                        dbc.Button('Завтра', id='schedule-end-date-tomorrow-button',
                                                   color='secondary', className='me-2', size='sm',
                                                   style={'minWidth': '73px', 'width': '40%'})],
                                       className='d-block'), width=6)
                      ])]),
    ])])], style=card_style),
    dbc.Card([
        dbc.CardBody([dbc.Label('Список азимутов:'),
                      dbc.Row([
                          # dbc.Col(html.Div([dbc.Textarea(id='azimuths', rows=3, size='sm')],
                          #                  className='d-grid d-block', ), width=8),
                          dbc.Col(html.Div([dbc.Textarea(id='azimuths', rows=3, size='sm',
                                                         value='+24, +20, +16, +12, +8, +4, +0, -4, -8, -12, -16, -20, -24')],
                                           className='d-grid d-block', ), width=8),
                          dbc.Col([html.Div([dbc.Button('+24:-24 через 12', id='azimuths-12-button', size='sm',
                                                        color='secondary', className='me-1 w-100'),
                                             dbc.Button('+28:-28 через 4', id='azimuths-4-button', size='sm',
                                                        color='secondary', className='me-1 w-100')
                                             ], className='d-grid gap-2')], width=2),
                          dbc.Col([html.Div([dbc.Button('+30:-30 через 2', id='azimuths-2-button', size='sm',
                                                        color='secondary', className='me-1 w-100'),
                                             dbc.Button('+30:-30 через 1', id='azimuths-1-button', size='sm',
                                                        color='secondary', className='me-1 w-100'),
                                             ], className='d-grid gap-2')], width=2)])])
    ], style=card_style),
], style={'padding': '0px', 'max-width': '100%'})

antenna_tab = dbc.Container([
    dbc.Row([dbc.Card(id='table-container-culminations', class_name=f'{card_style} border-0', body=True)],
            style={'min-height': 'calc(100% - 90px)', 'max-height': 'calc(100% - 90px)'},
            class_name='flex-grow-1 overflow-auto border-0'),
], fluid=True, class_name='force-fill-height h-100 d-flex flex-column overflow-hidden')

acquisition_tab = dbc.Container([
    dbc.Row([dbc.Card(id='table-container-acquisition', class_name=f'{card_style} border-0', body=True)],
            style={'min-height': 'calc(100% - 90px)', 'max-height': 'calc(100% - 90px)'},
            class_name='flex-grow-1 overflow-auto border-0'),
], fluid=True, class_name='force-fill-height h-100 d-flex flex-column overflow-hidden')

carriage_tab = dbc.Container([
    dbc.Row([dbc.Card(id='table-container-carriage', class_name=f'{card_style} border-0', body=True)],
            style={'min-height': 'calc(100% - 90px)', 'max-height': 'calc(100% - 90px)'},
            class_name='flex-grow-1 overflow-auto border-0'),
], fluid=True, class_name='force-fill-height h-100 d-flex flex-column overflow-hidden')

tracking_tab = dbc.Container([
    dbc.Col([
        dbc.Row([
            html.P([
                'Расчет производится для установок антенны в азимутах через 4°. Перед началом наблюдения в '
                'очередном азимуте облучатель должен быть установлен оператором на репер за 1° или 2° до оси '
                'азимута. Движение прекращается через 1° после оси азимута. '
            ]),
            html.P([
                'Формируются расписания движения по реперам для оператора и наблюдателя, скрипт ',
                html.Span('at_job ', className='text-info'),
                'для установки заданий для привода облучателя, скрипт ',
                html.Span('stop ', className='text-info'),
                'для остановки движения в любое время и скрипт ', html.Span('at_rmall ', className='text-info'),
                'для отмены всех заданий для привода, установленных в данный момент.'
            ]),
            html.P([
                'При помощи поля ',
                html.Span('Коррекция ', className='text-info'),
                'можно ввести поправочный коэффициент к скорости движения облучателя, если практика расходится '
                'с теорией. В этом случае надо отменить все действующие задания привода и установить новые.'
            ])
        ], style={'padding-top': '20px', 'padding-bottom': '20px', }),

        dbc.Card([
            dbc.Row([dbc.Col(dbc.Row([
                dbc.Col([
                    dbc.Label('1° @ 300 об/мин, с'),
                    dbc.Row(dbc.Col(dbc.Input(id='tracking-300rpm-s', type='number', min=100, max=500, value=286,
                                              size='sm')))
                ], width=3),
                dbc.Col([dbc.Label('Старт'),
                         dbc.Row(dbc.Col(dbc.Select(options=[
                             {'label': 'За 1° до оси', 'value': '1'},
                             {'label': 'За 2° до оси', 'value': '2'}
                         ], id='tracking-start', size='sm', value='1'), width=12))], width=3),
                dbc.Col([], width=3),
                dbc.Col([dbc.Label('Коррекция'),
                         dbc.Row(dbc.Col(
                             dbc.Input(id='tracking-correction', type='number', min=0.75, max=1.5, value=1.0,
                                       step=0.001, size='sm')))
                         ], width=3),
            ]), width=10)]),
        ], body=True, class_name='border-0')
    ])

], fluid=True, class_name='force-fill-height h-100 d-flex flex-column overflow-hidden')

task_pane = dbc.Container([
    dbc.Card([
        dbc.CardBody([
            dbc.Col([
                dbc.Row([dbc.Label(dash.dcc.Markdown('#### &nbsp;', id='job-summary'))]),
                dbc.Row([
                    dbc.Col([dbc.Row([
                        html.Div([
                            dbc.Label('Имя задания', size='sm',
                                      style={'width': '6.5em', 'min-width': '6.5em'}, class_name='mx-1'),
                            dbc.Input(id='job-name', size='sm',
                                      style={'width': '10em', 'min-width': '10em', 'display': 'inline'},
                                      class_name='mx-1',
                                      disabled=True),
                        ], style={'min-width': '270px', 'width': '270px', 'display': 'inline'})
                    ])], width=4),

                    dbc.Col([dbc.Row([
                        html.Div([
                            dbc.Button('Запустить csmake и csmake2', id='run-csmake', size='sm',
                                       style={'width': '210px', 'min-width': '210px'}, class_name='mx-1',
                                       disabled=True),
                            dbc.Button('Загрузить расписания', id='load-csi', size='sm',
                                       style={'width': '210px', 'min-width': '210px'}, class_name='mx-1',
                                       disabled=True),
                            dcc.Download(id='dcc-download-csi'),
                            dbc.Button('Загрузить задания облучателя', id='load-track', size='sm',
                                       style={'width': '210px', 'min-width': '210px'}, class_name='mx-1',
                                       disabled=True),
                            dcc.Download(id='dcc-download-motion'),
                        ], style={'min-width': '680px'})
                    ])], width=7)
                ]),
                html.Div(id='csi-sink', style={'visibility': 'hidden'}),
            ])
        ], class_name='w-100 h-100')
    ], style=card_style, class_name='border-top border-dark'),
], style={'position': 'absolute', 'bottom': '0px', 'height': '102px', 'padding': '1px', 'margin': '0',
          'max-width': '100%'}
)
mode_tabs = dbc.Card(dbc.Tabs([
    dbc.Tab(antenna_tab, label='Расписания антенны', id='culminations-tab', class_name='h-100',
            active_label_class_name='text-info'),
    dbc.Tab(acquisition_tab, label='Параметры сбора', id='acquisition-tab', class_name='h-100',
            active_label_class_name='text-info'),
    dbc.Tab(tracking_tab, label='Параметры сопровождения', id='tracking-tab', class_name='h-100',
            active_label_class_name='text-info'),
    dbc.Tab(carriage_tab, label='Движение каретки', id='carriage-tab', class_name='h-100',
            active_label_class_name='text-info'),
]), class_name='flex-grow-1 overflow-hidden h-100')

sink = html.Div('SINK', id='sink', style={'visibility': 'hidden'})

progress_modal = html.Div([dbc.Modal([
    dbc.ModalBody(dbc.Progress(id='update-progress', animated=True, striped=True)),
], id='modal-progress', is_open=False, centered=True, keyboard=False, backdrop=False)])

right_pan = dbc.Container(
    children=[common_ctrl, mode_tabs, task_pane, sink, progress_modal],
    fluid=True, class_name='force-fill-height h-100 d-flex flex-column',
    style={'padding': '0px'}
)

splitter_v = dash_split_pane.DashSplitPane(
    children=[left_pan, right_pan],
    id='splitter_v',
    split='vertical',
    size='39%',
    style={'height': '100%'}
)

antenna_store = dcc.Store(id='obs-table')
feed_store = dcc.Store(id='feed-table')
carriage_store = dcc.Store(id='carriage-table')

layout = dbc.Container([splitter_v, antenna_store, feed_store, carriage_store], fluid=True, className='dbc',
                       style={'height': '95vh'})
