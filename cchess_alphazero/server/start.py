
import os, sys

_PATH_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if _PATH_ not in sys.path:
    sys.path.append(_PATH_)
    sys.path.append(os.path.dirname(_PATH_))
print("XXXXX", __file__, _PATH_)


from flask import Flask, request
from flask import render_template
from flask_cors import CORS
from flaskwebgui import FlaskUI

from flask_sockets import Sockets

from cc_server import get_server, CCServer


app = Flask(__name__)
# app.config['SECRET_KEY'] = 'secret!'
CORS(app)
# socketio = Sockets(app, cors_allowed_origins="*")
sockets = Sockets(app)

# ui = FlaskUI(app, host='0.0.0.0', socketio=socketio)


# @app.route("/")
# def hello():  
#     return render_template('index.html')

# @app.route("/home", methods=['GET'])
# def home(): 
#     return render_template('home.html')

# @app.route('/', methods = ['POST'])
# def cchess():
#     print("POST %s", request.json)
#     func = request.json['func']
#     # mid = request.json.mid
#     env: CCServer = get_server()

#     if (func == "init"):
#         return env.reset(request.json['hf'])
#     elif (func == "get-board"):
#         return env.get_board()
#     elif (func == "get-legal-moves"):
#         xy = getStr("xy")
#         return env.get_legal_moves(int(xy[0]), int(xy[1]))
#     elif (func == "move-to"):
#         xy, xy2 = getStr("xy"), getStr("xy2")
#         return env.chess_move(int(xy[0]), int(xy[1]), int(xy2[0]), int(xy2[1]))
#     elif (func == "get-ai-move"):
#         return env.ai_move()
#     elif (func == "enable-ai"):
#         return env.enable_ai(getInt('pl'))
#     elif (func == "set-ai-level"):
#         return env.set_ai_level(getInt('pl'))
#     else:
#         return ""

@sockets.route('/echo')
def echo_socket(ws):
    while True:
        message = ws.receive()
        ws.send(message[::-1])

@app.route('/')
def hello():
    return 'Hello World!'

@app.route('/echo_test', methods=['GET'])
def echo_test():
    return render_template('echo_test.html')

def getStr(name, default=None):
    try:
        return request.json[name]
    except (KeyError) as err:
        if default != None: return default
        else: raise err

def getInt(name, default=None):
    try:
        return int(request.json[name])
    except (KeyError, ValueError) as err:
        if default != None: return default
        else: raise err


if __name__ == "__main__":
    app.run()