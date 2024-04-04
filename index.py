from app import app, server

from controller import *

import logging

logging.getLogger('werkzeug').setLevel(logging.ERROR)


if __name__ == "__main__":
    app.run_server(
        # host=APP_HOST,
        port=8888,
        debug=False,
        # dev_tools_props_check=DEV_TOOLS_PROPS_CHECK
    )