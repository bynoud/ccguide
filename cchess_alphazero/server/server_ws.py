from collections import defaultdict
from threading import Thread
from multiprocessing import Pipe, Process
from logging import getLogger

from cchess_alphazero.lib.logger import setup_logger
import cchess_alphazero.environment.static_env as senv
from cchess_alphazero.environment.chessboard import Chessboard
from cchess_alphazero.environment.chessman import *
from cchess_alphazero.agent.model import CChessModel
from cchess_alphazero.agent.player import CChessPlayer, VisitState
from cchess_alphazero.agent.api import CChessModelAPI
from cchess_alphazero.config import Config, PlayWithHumanConfig
from cchess_alphazero.environment.env import CChessEnv
from cchess_alphazero.environment.lookup_tables import Winner, ActionLabelsRed, flip_move
from cchess_alphazero.lib.model_helper import load_best_model_weight
from cchess_alphazero.lib.tf_util import set_session_config

logger = getLogger(__name__)

cc_envs = {}

def get_server(name="default"):
    if name not in cc_envs: cc_envs[name] = CCServerWS(name)
    return cc_envs[name]

ziga_cmd_consumer, ziga_cmd_sumitter = Pipe()


class CCServerWS:
    def __init__(self, name="default"):
        self.name = name

        self.ai_guide_only = False
        self.ziga_discard = False
        self.ziga_callbacks = {}

        # self.ziga_proc = Process(target=self.ziga_ws_looping)

        # self.init()
        # self.reset(human_first)
        # self.ziga_proc.start()

    def start(self):
        Thread(target=self.ziga_ws_looping).start()


    def ziga_ws_looping(self):
        print("siga_ws_proc started")

        while True:
            action = ziga_cmd_consumer.recv() # blocking
            while action != None:
                print('getboard cmd', action)
                if (ziga_cmd_consumer.poll()):
                    action = ziga_cmd_consumer.recv()
                else:
                    action = None
            if self.ziga_discard:
                ret = {'status': 'error', 'mess': 'Board is not in sync. Stop follow'}
            else:
                ret = self.ziga_board()
            print('finish 1 round', self.ziga_callbacks)
            try:
                self.ziga_callbacks['board_updated'](ret)
            except Exception as e:
                print("no callback or error", e)

    def ziga_reg_callback(self, name, fn):
        self.ziga_callbacks[name] = fn
    def ziga_del_callback(self, name, fn):
        del self.ziga_callbacks[name]

    def ziga_ws_handler(self, action):
        print('add action', action)
        ziga_cmd_sumitter.send(action)

    # return True if moved successfully
    def ziga_move(self, x, y, to_x, to_y):
        print(' -- ', x, y, to_x, to_y)
        # return self.env.board.move(x, y, to_x, to_y)

    def ziga_board(self):
        return {"board": "XXX"}

    # # blocking
    # def ziga_get_board(self):
    #     action = self.ziga_cmd_q.get()  # blocking
    #     while action != None:
    #         print('getboard cmd', action)
    #         if action['cmd'] == 'newgame':
    #             self.reset()
    #             return {'status': 'new-game-found'}
    #         elif action['cmd'] == 'move' and not self.ziga_discard:
    #             if not self.ziga_move(
    #                 int(action['fx']), int(action['fy']), 
    #                 int(action['tx']), int(action['ty'])):
    #                 self.ziga_discard = True
    #         try:
    #             action = self.ziga_cmd_q.get_nowait()
    #         except:
    #             action = None
    #     if self.ziga_discard:
    #         return {'status': 'error', 'mess': 'Board is not in sync. Stop follow'}
    #     else:
    #         return self.ziga_board()
        
