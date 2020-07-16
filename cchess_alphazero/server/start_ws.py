
import os, sys
from threading import Thread
import psutil

_PATH_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if _PATH_ not in sys.path:
    sys.path.append(_PATH_)
    sys.path.append(os.path.dirname(_PATH_))

from flask import Flask, render_template, request
from flask_socketio import SocketIO, Namespace, emit
from flask_cors import CORS

from cc_server import get_server, CCServer
from guide_server import GuideNamespace


app = Flask(__name__)
app.config['SECRET_KEY'] = 'very_secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

env = None



@app.route('/')
def index():
    return "Helll"

@app.route('/debug', methods=['GET'])
def debug():
    print('debug', request.args)
    env.ziga_ws_handler(request.args.to_dict())
    return "debug OK: %s" % request.args.to_dict()

@app.route('/', methods = ['POST'])
def cchess():
    print("POST %s", request.json)
    func = request.json['func']
    # mid = request.json.mid
    env: CCServer = get_server()

    if (func == "init"):
        return env.reset(request.json['hf'])
    elif (func == "get-board"):
        return env.get_board()
    elif (func == "get-legal-moves"):
        xy = getStr("xy")
        return env.get_legal_moves(int(xy[0]), int(xy[1]))
    elif (func == "move-to"):
        xy, xy2 = getStr("xy"), getStr("xy2")
        return env.chess_move(int(xy[0]), int(xy[1]), int(xy2[0]), int(xy2[1]))
    elif (func == "get-ai-move"):
        return env.ai_move()
    elif (func == "enable-ai"):
        return env.enable_ai(getInt('pl'))
    elif (func == "set-ai-level"):
        return env.set_ai_level(getInt('pl'))
    else:
        return ""

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


# @socketio.on('connect', namespace='/guide')
# def guide_connect():
#     print('connected guide')
#     emit('ziga-guide',  {'status':'ok', 'mess': 'connectedX'})
#     def waitForBoard(mess):
#         # print('get next board')
#         # mess = env.ziga_get_board()
#         print('got next board XXXX', mess)
#         socketio.emit('ziga-guide', mess, namespace='/guide')
#     env.ziga_regiter_client({
#         'board_updated': waitForBoard,
#     })
#     # srv['gameLoopThread'] = Thread(target=waitForBoard)
#     # srv['gameLoopThread'].start()

# @socketio.on('disconnect', namespace='/guide')
# def guide_disconnect():
#     print('disconnected guide')
#     env.ziga_del_client()

# @socketio.on('user', namespace='/guide')
# def guide_user(data):
#     print('guide/user', data)
#     env.guide_ws_handler(data)


@socketio.on('connect', namespace='/ziga')
def ziga_connect():
    print('connected ziga')

@socketio.on('ziga-ws', namespace='/ziga')
def ziga_ws_recv(data):
    print('ziga-ws', data)
    env.ziga_ws_handler(data)
    
print("==== Start", __name__)
if __name__ == '__main__':
    env = get_server()
    env.start()
    env.ai_enabled = True
    env.ai_guide_only = True

    socketio.on_namespace(GuideNamespace('/guide', env))
    socketio.run(app, host='0.0.0.0')
