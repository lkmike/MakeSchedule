import PIL.Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

import sunpy.map
import numpy as np

from app import app

import pandas as pd
from datetime import datetime
import astropy
from sunpy import map
import dash
from dash import ctx
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
from dash import dcc
import plotly.graph_objects as go

import io
from PIL import Image

import pylab


@app.callback(
    Output('fits-plot', 'children'),
    Input('load-fits', 'n_clicks'),
    prevent_initial_call=False
)
def fits_plot(n):
    print('here')
    if ctx.triggered_id != 'load-fits':
        raise PreventUpdate

    fits_filename = './AIA20230619_005100_0171.fits'

    raw_map = sunpy.map.Map(fits_filename)

    size_in = 4
    dpi = 128
    arcsec_pp = 1024 / size_in / dpi * 2.4

    figure = plt.figure(frameon=False, figsize=(size_in, size_in))
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

    im = Image.open(img_buf)
    im = im.transpose(PIL.Image.FLIP_TOP_BOTTOM)

    fig = go.Figure()

    fig.add_trace(go.Image(z=im, dx=arcsec_pp, dy=arcsec_pp,
                           x0=-size_in * dpi * arcsec_pp / 2,
                           y0=-size_in * dpi * arcsec_pp / 2, name=''))
    fig.update_traces(hovertemplate='θ<sub>x</sub>: %{x:.>8.0f}<br>θ<sub>y</sub>: %{y:.>8.0f}')
    # fig.layout.hoverlabel.align = 'right'
    fig.layout.xaxis.visible = False
    fig.layout.yaxis.autorange = True
    fig.layout.yaxis.visible = False
    fig.layout.margin.l = 0
    fig.layout.margin.r = 0
    fig.layout.margin.t = 0
    fig.layout.margin.b = 0
    fig.layout.hoverlabel = {'font_family': 'monospace'}

    return dcc.Graph(figure=fig, style={'width': '100%', 'height': '100%'})
