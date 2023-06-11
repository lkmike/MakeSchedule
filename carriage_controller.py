from app import app
from dash.dependencies import Input, Output, State


# app.clientside_callback(
#     '''
#     function(value):
#     {
#         let speed, accel, decel, dwell
#         [speed, accel, decel, dwell] = value.split('/').map(Number);
#         if (array.any(element => {return typeof element !== 'number';}))
#         {
#             return "Conversion error";
#         }
#         if ((speed < 0) || (speed > 1000)) {return 'Speed X'}
#         if ((accel <= 0) || (accel > 1000)) {return 'Acc X'}
#         if ((decel <= 0) || (decel > 1000)) {return 'Dec X'}
#         if ((dwell <= 0) || (dwell > 1000)) {return 'Dwell X'}
#         return false;
#     }
#     ''',
#     Output({'type': 'carmove1-value-all', 'index': '0'}, "error"),
#     Input({'type': 'carmove1-value-all', 'index': '0'}, "value"),
# )

@app.callback(
    Output({'type': 'carmove1-value-all', 'index': '0'}, "invalid"),
    Input({'type': 'carmove1-value-all', 'index': '0'}, "value"),
)
def validate_carmove(value):
    try:
        speed, accel, decel, dwell = map(float, value.split('/'))
    except ValueError:
        return True
    if speed <= 0 or speed > 1000:
        return True
    if accel <= 0 or accel > 1000:
        return True
    if decel <= 0 or decel > 1000:
        return True
    if dwell < 0 or dwell > 1000:
        return True

    return False
