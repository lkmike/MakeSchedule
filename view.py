import dash.dcc
from dash import dcc, html
import dash_bootstrap_components as dbc

from dash_bootstrap_templates import load_figure_template
import dash_split_pane

from datetime import datetime

from defaults import FAST_FEED_POSITION, SENSITIVE_FEED_POSITION, SOLAR_FEED_POSITION, DEFAULT_BEGIN_OBSERVATIONS, \
    DEFAULT_END_OBSERVATIONS, DEFAULT_AZIMUTH_LIST, DEFAULT_SOLAR_X, DEFAULT_SOLAR_Y, DEFAULT_AIA_TIME, DEBUG, \
    DEFAULT_OBJECT, DEFAULT_OBJECT_ID
from fits_view import fits_modal
from utils import card_style

print('view enters')

load_figure_template('darkly')

# fig_style = {'height': '100%', 'width': '100%'}

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

if DEBUG:
    debug_label = dash.dcc.Markdown('# ОТЛАДКА', className='text-danger d-flex')
else:
    debug_label = html.Div()

tab_stellar = dbc.Container([
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([dbc.Label('‌‌'),
                         dbc.Row(dbc.Col(
                             dbc.Select(options=[
                                 {'label': 'Краб', 'value': '1'},
                                 {'label': 'Лебедь А', 'value': '2'},
                                 {'label': '3c84', 'value': '3'},
                                 {'label': '3c273', 'value': '4'},
                                 {'label': 'Солнце', 'value': '[Sun]'},
                                 {'label': 'Луна', 'value': '[Moon]'}
                             ], id='stellar-source', size='sm', value=DEFAULT_OBJECT,
                                 class_name='bg-dark text-secondary')
                         ))], width=3),
                dbc.Col([dbc.Label('‌'),
                         dbc.Row(dbc.Col(dbc.Button('>', id='stellar-source-submit-button', size='sm')))], width=1),
                dbc.Col([dbc.Label('Объект'),
                         dbc.Row(dbc.Col(dbc.Input(id='stellar-name', size='sm', value=DEFAULT_OBJECT_ID)))], width=2),
                dbc.Col([dbc.Label('α'),
                         dbc.Row(dbc.Col(dbc.Input(id='stellar-ra', size='sm', value='')))], width=3),
                dbc.Col([dbc.Label('δ'),
                         dbc.Row(dbc.Col(dbc.Input(id='stellar-dec', size='sm', value='')))], width=3),
            ]),
        ]),

        dbc.CardBody([
            dbc.Row([dbc.Col([dbc.Label("Координаты на Солнце", class_name='d-inline-block'),
                              dbc.Checkbox(value=False, disabled=False, id='use-solar-object',
                                           class_name='m-3 d-inline-block')], width=12)]),
            dbc.Row([
                dbc.Col([dbc.Label('ID'),
                         dbc.Row(dbc.Col(dbc.Input(id='solar-object-name', size='sm', value='AR')))], width=3),
                dbc.Col([dbc.Label([html.I('t'), html.Sub(" ref")]),
                         dbc.Row([
                             dbc.Col(dbc.Input(id='solar-ref-time', value=DEFAULT_AIA_TIME(), debounce=True,
                                               step='1', size='sm')),
                             html.Div([], id='solar-ref-time-sink')
                         ])], width=5),
                dbc.Col([dbc.Label(['θ', html.Sub(html.I("x ")), ', ″']),
                         dbc.Row(dbc.Col(
                             dbc.Input(id='solar-lon', type='number', value=DEFAULT_SOLAR_X, min=-1100, max=1100,
                                       step=1,
                                       size='sm', style={'min-width': '63px'})
                         ))], width=2, style={'min-width': '68px'}),
                dbc.Col([dbc.Label(['θ', html.Sub(html.I("y ")), ', ″']),
                         dbc.Row(dbc.Col(
                             dbc.Input(id='solar-lat', type='number', value=DEFAULT_SOLAR_Y, min=-1100, max=1100,
                                       step=1,
                                       size='sm', style={'min-width': '63px'})
                         ))], width=2, style={'min-width': '68px'}),
            ])
        ]),

        dbc.CardBody([
            dbc.Row([dbc.Button('Загрузить FITS', id='load-fits', color='primary', className='me-2', size='sm',
                                style={'minWidth': '200px', 'width': '200px'})], class_name='mt-3'),
        ]),

        html.Div(id='load-aia-sink', style={'visibility': 'hidden'}),

        dbc.CardBody([
            dbc.Row([
                html.Div(
                    html.Div(id='fits-plot',
                             style={'position': 'absolute', 'top': 0, 'bottom': 0, 'left': 0, 'right': 0}),
                    style={'width': '85%', 'padding-top': '85%', 'position': 'relative'}
                )
            ], className='justify-content-center')
        ])
    ], style=card_style),

    dbc.Card([dbc.CardBody([debug_label])], style=card_style,
             class_name='flex-fill h-100 justify-content-center align-content-center')
], class_name='mw-100', style={'min-width': '451px'})

# source_tabs = dbc.Tabs([
#     dbc.Tab(tab_stellar, label='Объекты без затей', active_label_class_name='text-info'),
#     dbc.Tab(tab_sun, label='Точка на Солнце', class_name='h-100',
#             active_label_class_name='text-info'),
# ])

left_pan = dbc.Card(
    children=[tab_stellar], class_name='h-100'
)

common_ctrl = dbc.Container([
    dbc.Card([dbc.CardBody([dbc.Row([
        dbc.Col([dbc.Label('Начало наблюдений'),
                 dbc.Row(
                     [dbc.Col(dbc.Input(id='schedule-begin-datetime-input', type='datetime-local', size='sm',
                                        value=DEFAULT_BEGIN_OBSERVATIONS()), width=6),
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
                     [dbc.Col(dbc.Input(id='schedule-end-datetime-input', type='datetime-local', size='sm',
                                        value=DEFAULT_END_OBSERVATIONS()), width=6),
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
                                                         value=DEFAULT_AZIMUTH_LIST)],
                                           className='d-grid d-block', ), width=8),
                          dbc.Col([html.Div([dbc.Button('+24:-24 через 12', id='azimuths-12-button', size='sm',
                                                        color='secondary', className='me-1 w-100',
                                                        style={'min-width': '119px'}),
                                             dbc.Button('+28:-28 через 4', id='azimuths-4-button', size='sm',
                                                        color='secondary', className='me-1 w-100',
                                                        style={'min-width': '119px'})
                                             ], className='d-grid gap-2')], width=2),
                          dbc.Col([html.Div([dbc.Button('+30:-30 через 2', id='azimuths-2-button', size='sm',
                                                        color='secondary', className='me-1 w-100',
                                                        style={'min-width': '119px'}),
                                             dbc.Button('+30:-30 через 1', id='azimuths-1-button', size='sm',
                                                        color='secondary', className='me-1 w-100',
                                                        style={'min-width': '119px'}),
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
                                      disabled=False),
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
    dbc.Tab(antenna_tab, label='Антенна', id='culminations-tab', class_name='h-100',
            active_label_class_name='text-light', label_class_name='text-secondary', label_style={'width': '10em'}),
    dbc.Tab(acquisition_tab, label='Сбор', id='acquisition-tab', class_name='h-100',
            active_label_class_name='text-light', label_class_name='text-secondary', label_style={'width': '10em'}),
    dbc.Tab(carriage_tab, label='Каретка', id='carriage-tab', class_name='h-100',
            active_label_class_name='text-light', label_class_name='text-secondary', label_style={'width': '10em'}),
    dbc.Tab(tracking_tab, label='Cопровождение', id='tracking-tab', class_name='h-100',
            active_label_class_name='text-light', label_class_name='text-secondary', label_style={'width': '10em'}),
]), class_name='flex-grow-1 overflow-hidden h-100')

sink = html.Div('SINK', id='sink', style={'visibility': 'hidden'})

progress_modal = html.Div([dbc.Modal([
    dbc.ModalBody(dbc.Progress(id='update-progress', animated=True, striped=True)),
], id='modal-progress', is_open=False, centered=True, keyboard=False, backdrop=False)])

carriage_position_hints = html.Datalist(children=[
    html.Option(value=SOLAR_FEED_POSITION, label='Солнечный', style={'width': '20em'}),
    html.Option(value=SENSITIVE_FEED_POSITION, label='Чувствительный', style={'width': '20em'}),
    html.Option(value=FAST_FEED_POSITION, label='Скоростной', style={'width': '20em'})
], id='carriage-position-hints')

right_pan = dbc.Container(
    children=[common_ctrl, mode_tabs, task_pane, sink, progress_modal, carriage_position_hints, fits_modal],
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

antenna_store = dcc.Store(id='antenna-table')
feed_store = dcc.Store(id='acquisition-table')
carriage_store = dcc.Store(id='carriage-table')

layout = dbc.Container([splitter_v, antenna_store, feed_store, carriage_store], fluid=True, className='dbc',
                       style={'height': '95vh'})
