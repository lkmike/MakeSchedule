import tempfile
import numpy as np

import PIL.Image
import io

import requests
import sunpy
from matplotlib import pyplot as plt
from sunpy.net.vso import VSOClient

from app import app

# import pandas as pd
from pytz import timezone

from dash import ctx, html, dash_table
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import dcc
import dash_bootstrap_components as dbc

import plotly.graph_objects as go

from defaults import TIMEZONE
from fits_view import AIA_CHANNELS

import astropy.units as u
from sunpy.net import Fido, attrs as attr
from datetime import datetime, timedelta
from sunpy.map import Map


print('fits controller')


@app.callback(
    Output('aia-wavelength', 'label'),
    list(map(lambda x: Input({'type': 'aia_ch', 'val': x}, "n_clicks"), AIA_CHANNELS)),
)
def update_channel_value(*_):
    trigger_id = ctx.triggered_id
    if not trigger_id or trigger_id.val not in AIA_CHANNELS:
        raise PreventUpdate
    return trigger_id.val


@app.callback(
    Output('modal-fits', 'is_open', allow_duplicate=True),
    Input('load-fits-cancel', 'n_clicks'),
    prevent_initial_call=True
)
def modal_fits_cancel(_):
    if ctx.triggered_id == 'load-fits-cancel':
        return False


@app.callback(
    Output('modal-fits', 'is_open'),
    Output('fits-plot', 'children'),
    Output('solar-ref-time', 'value'),
    Input('load-fits-ok', 'n_clicks'),
    State({'type': 'query_result_table', 'index': '0'}, 'active_cell'),
    State({'type': 'query_result_table', 'index': '0'}, 'data')
)
def modal_fits_ok(_, cell, data):
    print('Modal OK')
    if ctx.triggered_id == 'load-fits-ok':
        try:
            row = cell['row']
            dtime = datetime.fromisoformat(data[row]['Start Time']).astimezone(timezone('UTC'))
            query = (attr.Time(dtime - timedelta(seconds=5), dtime + timedelta(seconds=5)),
                     attr.Instrument('AIA'),
                     attr.Wavelength(data[row]['Wavelength'] * u.Angstrom))
            result = Fido.search(*query)
            vso_client = MyVSOClient()
            url, file_name = vso_client.get_url(result[0])
            assert url is not None
            print(url)
            with tempfile.TemporaryDirectory() as dir_name:
                response = requests.get(url)
                file_path = f'{dir_name}/{file_name}'
                open(file_path, "wb").write(response.content)
                graph, tref = fits_plot_and_time(file_path)
                return False, graph, tref
            # file_path = '/home/michael/PycharmProjects/MakeSchedule/AIA20230624_073300_0171.fits'
            # graph, tref = fits_plot_and_time(file_path)
            # return False, graph, tref
        except (IndexError, KeyError):
            pass

    raise PreventUpdate




@app.callback(
    Output('modal-fits', 'is_open', allow_duplicate=True),
    Input('load-fits', 'n_clicks'),
    prevent_initial_call=True
)
def load_aia_onclick(_):
    if ctx.triggered_id != 'load-fits':
        raise PreventUpdate
    return True



@app.callback(
    Output('query-result', 'children'),
    Input('fits-send-request', 'n_clicks'),
    State('load-fits-time', 'value'),
    State('aia-wavelength', 'label'),
    prevent_initial_call=True
)
def send_query(_, s_time, wl):
    dtime = datetime.fromisoformat(s_time).astimezone(TIMEZONE)

    if abs((dtime - datetime.now().astimezone(TIMEZONE)).total_seconds()) < 3600:
        dtime = dtime.now()
        query = (attr.Time(dtime - timedelta(hours=4), dtime),
                 attr.Instrument('AIA'),
                 attr.Wavelength(int(wl) * u.Angstrom))
        result = Fido.search(*query)
        result = result[0, -1:]
    else:
        query = (attr.Time(dtime - timedelta(hours=2), dtime + timedelta(hours=2)),
                 attr.Instrument('AIA'),
                 attr.Wavelength(int(wl) * u.Angstrom))
        result = Fido.search(*query)
        result = result[0, :]

    if len(result) == 0:
        return dbc.Table([html.Thead(html.Tr([html.Th('Ничего не найдено')]))])
    else:
        tb = result.copy()
        cwl = (tb['Wavelength'])[:, 0]
        tb.remove_column('Wavelength')
        tb.add_column(cwl)
        names = ['Start Time', 'Instrument', 'Wavelength', 'fileid']
        df = tb[names].to_pandas()
        # return dash_table.
        # print(df)
        dt = dash_table.DataTable(
            id={'type': 'query_result_table', 'index': '0'},
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_data={
                'color': '#d7d8d9',
                'backgroundColor': '#3c4248',
                'font-size': '12px'
            },
            style_data_conditional=[
                {
                    "if": {"state": "selected"},
                    "backgroundColor": "inherit !important",
                    "border": "inherit !important",
                },
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#2f353b',
                }
            ],
            style_header={
                'backgroundColor': '#3c4248',
                'color': '#f7f7f7',
                'fontWeight': 'bold',
                'border': '1px solid black'
            },
            style_cell={
                'border': '1px solid black'
            },
        )
        print(dt)
        return dt


@app.callback(
    Output('fits-name', 'children'),
    Input({'type': 'query_result_table', 'index': '0'}, 'active_cell'),
    State({'type': 'query_result_table', 'index': '0'}, 'data')
)
def select_item(cell, data):
    print('here')
    if cell:
        print('cell')
        row = cell['row']
        print(' '.join(list(map(str, data[row].values()))))
        return [' '.join(list(map(str, data[row].values())))]
    else:
        print('not cell')
        return ['‌‌']


# @app.callback(
#     Output('fits-plot', 'children'),
#     Input('load-fits', 'n_clicks'),
#     prevent_initial_call=False
# )
def fits_plot_and_time(fits_filename):

    raw_map = sunpy.map.Map(fits_filename)

    size_in = 4
    dpi = 128
    arcsec_pp = 1024 / size_in / dpi * 2.4

    # figure = \
    plt.figure(frameon=False, figsize=(size_in, size_in))
    ax = plt.axes([0, 0, 1, 1])
    ax.set_axis_off()
    norm = raw_map.plot_settings['norm']
    norm.vmin, norm.vmax = np.percentile(raw_map.data, [1, 99.9])
    ax.imshow(raw_map.data,
              norm=norm,
              cmap=raw_map.plot_settings['cmap'],
              origin="lower")

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=dpi)

    im = PIL.Image.open(img_buf)
    im = im.transpose(PIL.Image.FLIP_TOP_BOTTOM)

    fig = go.Figure()

    fig.add_trace(go.Image(z=im, dx=arcsec_pp, dy=arcsec_pp,
                           x0=-size_in * dpi * arcsec_pp / 2,
                           y0=-size_in * dpi * arcsec_pp / 2, name=''))
    fig.update_traces(hovertemplate='θ<sub>x</sub>: %{x:.>8.0f}<br>θ<sub>y</sub>: %{y:.>8.0f}')
    fig.layout.xaxis.visible = False
    fig.layout.yaxis.autorange = True
    fig.layout.yaxis.visible = False
    fig.layout.margin.l = 0
    fig.layout.margin.r = 0
    fig.layout.margin.t = 0
    fig.layout.margin.b = 0
    fig.layout.hoverlabel = {'font_family': 'monospace'}

    from astropy.time import TimezoneInfo

    t_obs_datetime = raw_map.date.to_datetime(timezone=TimezoneInfo(utc_offset=3*u.hour))
    print(raw_map.date)
    print(t_obs_datetime)
    t_obs = t_obs_datetime.replace(tzinfo=timezone('UTC')).isoformat()

    return dcc.Graph(figure=fig, style={'width': '100%', 'height': '100%'}, id='AIA-plot'), t_obs


@app.callback(
    Output('solar-lon', 'value'),
    Output('solar-lat', 'value'),
    Input('AIA-plot', 'clickData'),
    prevent_initial_call=True
)
def aia_plot_onclick(cd):
    if ctx.triggered_id == 'AIA-plot' and cd is not None:
        print(cd)
        return int(cd['points'][0]['x']), int(cd['points'][0]['y'])
    else:
        raise PreventUpdate


class MyVSOClient(VSOClient):
    def get_url(self, query_response):
        VSOGetDataResponse = self.api.get_type("VSO:VSOGetDataResponse")
        data_request = self.make_getdatarequest(query_response)
        data_response = VSOGetDataResponse(self.api.service.GetData(data_request))
        print(data_response)
        url = data_response['getdataresponseitem'][0]['getdataitem']['dataitem'][0]['url']
        file_name = data_response['getdataresponseitem'][0]['getdataitem']['dataitem'][0]['fileiditem']['fileid'][0]
        return url, file_name

    def make_getdatarequest(self, response, methods=None, info=None):
        if methods is None:
            methods = self.method_order + ['URL']
        return self.create_getdatarequest(
            {g[0]['Provider']: list(g['fileid']) for g in response.group_by('Provider').groups},
            methods, info
        )
