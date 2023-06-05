import dash
import dash_bootstrap_components as dbc

from view import layout

# from dash.long_callback import DiskcacheLongCallbackManager
import diskcache

import flask
server = flask.Flask(__name__)


cache = diskcache.Cache("./cache")
# long_callback_manager = DiskcacheLongCallbackManager(cache)
background_callback_manager = dash.DiskcacheManager(cache)

dbc_css = 'https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.4/dbc.min.css'

app = dash.Dash(
    __name__,
    server=server,
    background_callback_manager=background_callback_manager,
    external_stylesheets=[dbc.themes.SLATE, dbc.icons.FONT_AWESOME,
                          dbc_css],
)
app.config.suppress_callback_exceptions = True

app.layout = layout

# if __name__ == '__main__':
#     app.run_server(debug=False)
