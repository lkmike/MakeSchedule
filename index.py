from app import app, server

from controller import *

if __name__ == "__main__":
    app.run_server(
        # host=APP_HOST,
        # port=APP_PORT,
        debug=False,
        # dev_tools_props_check=DEV_TOOLS_PROPS_CHECK
    )