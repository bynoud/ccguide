
from flask_socketio import Namespace, emit

MAIN_EVENT = 'ziga_guide'

class GuideNamespace(Namespace):

    def __init__(self, namespace, chessServer):
        super(GuideNamespace, self).__init__(namespace)
        self.chessServer = chessServer

    def on_connect(self):
        print('connected guide')
        emit(MAIN_EVENT,  {'status':'ok', 'mess': 'connectedClass'})
        self.chessServer.ziga_regiter_client(self)
        # srv['gameLoopThread'] = Thread(target=waitForBoard)
        # srv['gameLoopThread'].start()

    def on_disconnect(self):
        print('disconnected guide')
        self.chessServer.ziga_del_client()

    def on_user(self, data):
        print('guide/user', data)
        self.chessServer.guide_ws_handler(data)

    def emitClient(self, data):
        print('Emit to client', data)
        self.emit(MAIN_EVENT, data)
