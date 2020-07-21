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
    if name not in cc_envs: init(name)
    return cc_envs[name]

def default_cfg():
    config = Config(config_type="mini")
    config.opts.new = False
    config.opts.device_list = "0"
    config.resource.create_directories()
    # cmd = play
    setup_logger(config.resource.play_log_path)
    config.opts.piece_style = "WOOD"
    config.opts.bg_style = "WOOD"
    config.internet.distributed = False
    config.opts.light = False
    return config

def init(name="default"):
    config: Config = default_cfg()
    set_session_config(per_process_gpu_memory_fraction=1, allow_growth=True, device_list=config.opts.device_list)
    cc_envs[name] = CCServer(config, name)

ziga_cmd_consumer, ziga_cmd_sumitter = Pipe()
# guide_cmd_consumer, guide_cmd_sumitter = Pipe()

play_level = [
    {
        "simulation_num_per_move": 800,
        "search_threads": 100
    },
    {
        "simulation_num_per_move": 1500,
        "search_threads": 100
    },
    {
        "simulation_num_per_move": 2000,
        "search_threads": 100
    },
    {
        "simulation_num_per_move": 3000,
        "search_threads": 200
    },
    {
        "simulation_num_per_move": 6000,
        "search_threads": 200
    },
]

class CCServer:
    def __init__(self, config: Config, name="default"):
        self.name = name
        self.config = config
        self.env: CChessEnv = CChessEnv()
        self.model: CChessModel = None
        self.pipe = None
        self.ai: CChessPlayer = None

        # pwhc = PlayWithHumanConfig()
        # pwhc.update_play_config(self.config.play)
        self.ai_level = 0
        self.update_config()

        self.auto_upd = True
        self.ai_enabled = False

        self.ai_guide_only = False
        self.ziga_discard = False
        self.ziga_clients = None
        self.move_hist = []

        # self.ziga_proc = Process(target=self.ziga_ws_looping)

        self.init()
        # self.reset(human_first)
        # self.ziga_proc.start()

    def start(self):
        # self.init()
        self.reset()
        self._thr = Thread(target=self.ziga_ws_looping)
        self._thr.daemon = True
        self._thr.start()

    def exit(self):
        print('start shutdown', self._thr, self._thr.is_alive())
        if self._thr and self._thr.is_alive():
            print('send exit commd')
            ziga_cmd_sumitter.send({'cmd':'exit'})
            self._thr.join()
        print('shutdown done')

    def update_config(self):
        print("level", self.ai_level)
        self.config.play.simulation_num_per_move = play_level[self.ai_level]["simulation_num_per_move"]
        self.config.play.c_puct = 1
        self.config.play.noise_eps = 0.01
        self.config.play.tau_decay_rate = 0
        self.config.play.search_threads = play_level[self.ai_level]["search_threads"]
        self.config.play.dirichlet_alpha = 0.2

    def load_model(self):
        self.model = CChessModel(self.config)
        print("Start loading model")
        if not load_best_model_weight(self.model):
            print("Best model is not loaded")
            self.model.build()
        print("Model loaded")

    def init(self):
        if self.ai:
            self.ai.close()
        self.load_model()
        self.pipe = self.model.get_pipes()
        self.ai = CChessPlayer(self.config, search_tree=defaultdict(VisitState), pipes=self.pipe,
                                enable_resign=True, debugging=False)

    def reset(self, human_first=True):
        self.human_first = human_first
        self.ziga_discard = False
        self.env.reset()
        return self.get_board()
        if self.ai_enabled and not self.ai_guide_only and not human_first:
            return self.ai_move()
        else:
            return self.get_board()

    def enable_ai(self, enb):
        self.ai_enabled = enb
        return {"ai_enb":enb}

    def set_ai_level(self, lvl):
        self.ai_level = lvl
        return {"ai_lvl":lvl}

    def get_board(self):
        chess = self.env.board.chessmans
        board = []
        for x in range(9):
            col = []
            for y in range(10):
                if chess[x][y] != None: col.append(chess[x][y].name_cn)
                else: col.append("")
            board.append(col)
        return {"board":board, "turn": "D" if self.env.red_to_move else "T", 
                "winner": self.get_winner()}

    def get_winner(self):
        if self.env.board.is_end():
            print("The game is over %s\n%s", (self.env.board.winner.value, self.env.board.screen))
            return self.env.board.winner.value
        else:
            return ""

    def get_legal_moves(self, x, y):
        # self.env.board.calc_chessmans_moving_list()
        chessman = self.env.board.chessmans[x][y]
        moves = []
        if chessman != None and chessman.is_red == self.env.board.is_red_turn:
            print("get_legal_moves [%0d, %0d] red %0d %s" % (x, y, chessman.is_red, chessman.name))
            for point in chessman.moving_list: moves.append("%0d%0d " % (point.x, point.y))
        
        return {"moves":moves}

    # return 0 if moved successfully
    def chess_move(self, x, y, to_x, to_y):
        chessman = self.env.board.chessmans[x][y]
        aimove = {}
        if chessman != None and chessman.move(to_x, to_y):
            if self.ai_enabled:
                aimove = self.ai_move()
        return {**aimove, **self.get_board()}

    def ai_move(self):
        print("STart ai_move", self.env.red_to_move)
        action, policy = self.ai.action(self.env.get_state(), self.env.num_halfmoves)
        if not self.env.red_to_move:
            action = flip_move(action)
        if action is None:
            print("AI surrendered!")
            return {"ai": {"status":"surrendered"}}
        print(f"AI chooses to move {action}")
        #self.env.step(action)
        if self.env.board.move_action_str(action):
            ret = {"moveFrom": action[:2], "moveTo": action[2:], **self.get_board()}
        else:
            ret = self.get_board()
            logger.error("Move Failed, action=%s, is_red_turn=%d, board=\n%s" % (action, 
                self.env.red_to_move, self.env.board.screen))
        self.env.num_halfmoves += 1
        return ret

    def get_ai_move(self):
        print("STart ai_move", self.env.red_to_move)
        self.update_config()
        action, policy = self.ai.action(self.env.get_state(), self.env.num_halfmoves)
        if action is None:
            print("AI surrendered!")
            return None
        if not self.env.red_to_move:
            action = flip_move(action)
        return (int(action[0]), int(action[1]),
                int(action[2]), int(action[3]))


    #=============================

    def ziga_call_client(self, ret, fn_name='board_updated'):
        print('call client', fn_name, ret, self.ziga_clients)
        try:
            self.ziga_clients.emitClient(ret)
        except Exception as e:
            print('No client or error', ret, fn_name, e)



    def ziga_ws_looping(self):
        print("siga_ws_proc started")
        # Just make sure all lib are load
        self.ai.action(self.env.get_state(), self.env.num_halfmoves)

        # return (action, lastcmd)
        def get_actions():
            action = None
            while True:
                if action is None:
                    action = ziga_cmd_consumer.recv() # blocking
                print("Got action", action)
                cmd = action['cmd']
                if cmd == 'exit':
                    if self.ai: self.ai.close()
                    break   # end of
                if cmd == 'move':
                    preaction = action
                    action = ziga_cmd_consumer.recv() if ziga_cmd_consumer.poll() else None 
                    yield (preaction, action is None or action['cmd'] != 'move')
                else:
                    yield (action, True)
                    action = None
            print("End of get_actions")

        print("Start fetching actions...")

        for action, lastcmd in get_actions():    # blocking
            print("XXX", action, lastcmd)

            if action['cmd'] == 'restart':
                human_first = not action['isRed']
                if self.human_first == human_first:
                    self.ziga_call_client({'status': 'warning', 'mess': 'User already on the selected side. No update is made'})
                elif not self.ziga_restart_game(human_first):
                    # failed to restore game
                    self.move_hist = []
                    self.ziga_discard = True
                else:
                    self.ziga_call_client({'status': 'ok', 'mess': 'Game is restored', **self.ziga_board()})

            elif action['cmd'] == 'newgame':
                self.reset(False)
                self.move_hist = []
                self.ai_level = 0
                self.ai_enabled = False

                self.ziga_call_client({'status':'warning', 
                    'mess': 'A new game started. Assume User on RED. You can restart the game with different side',
                    'cmd': 'new-game-found',
                    **self.ziga_board()})
                
            elif action['cmd'] == 'move' and not self.ziga_discard:
                moveok = self.ziga_move(int(action['fx']), int(action['fy']), 
                                        int(action['tx']), int(action['ty']))
                if not moveok:
                    print('Move %s is not successed', action)
                    self.ziga_discard = True
                    self.ziga_call_client({'status': 'error', 'mess': 'Board is not in sync. Stop follow'})
                elif lastcmd:
                    moves = {}
                    print("Is AI turn?", self.ai_enabled, self.human_first, self.env.red_to_move)
                    if self.ziga_ai_turn():
                        self.ziga_call_client({'status': 'ok', 'mess': 'AI is calculating next move ...', **self.ziga_board()})
                        moves = self.get_ai_move()
                    if moves is None:
                        self.ziga_call_client({'status': 'warning', 'mess': 'AI surrendered'})
                    else:
                        self.ziga_call_client({'status': 'ok', 'mess': 'Board updated', "aimove": moves, **self.ziga_board()})

        print("End of looping")

    def ziga_ai_turn(self):
        if not self.ai_enabled: return False
        if self.human_first: return not self.env.red_to_move
        return self.env.red_to_move

    def ziga_restart_game(self, human_first):
        print('Start to restore game', human_first, self.move_hist)
        self.reset(human_first)
        for move in self.move_hist:
            if not self.ziga_move(move[0], move[1], move[2], move[3], True):
                print("History restore failed", human_first)
                # self.ziga_call_client({'status':'error', 'mess': 'Could not restore the game'})
                return False
        print("History is restored", human_first)
        # self.ziga_call_client({'status': 'ok', 'mess': 'Game is restored'})
        return True

    def ziga_regiter_client(self, client):
        self.ziga_clients = client
    def ziga_del_client(self):
        self.ziga_clients = None

    def ziga_ws_handler(self, action):
        print('add action', action)
        ziga_cmd_sumitter.send(action)

    def guide_ws_handler(self, data):
        print('user send action', data)
        # guide_cmd_sumitter.send(data)
        ziga_cmd_sumitter.send(data)

    # return True if moved successfully
    def ziga_move(self, x, y, to_x, to_y, nohist=False):
        # if self.human_first:
        #     x = 8 - x
        #     y = 9 -y
        #     to_x = 8 - to_x
        #     to_y = 9 - to_y
        # chessman = self.env.board.chessmans[x][y]
        # print("prepare to move", x, y, to_x, to_y, self.human_first, chessman, self.env.board.is_red_turn)
        if not nohist: self.move_hist.append([x, y, to_x, to_y])
        ret = self.env.board.move(x, y, to_x, to_y)
        if not self.env.red_to_move: self.env.num_halfmoves += 1
        return ret

    def ziga_board(self):
        chess = self.env.board.chessmans
        board = []
        for x in range(9):
            col = []
            for y in range(10):
                if chess[x][y] != None: col.append(chess[x][y].name_cn)
                else: col.append("")
            board.append(".".join(col))
        return {
            "board":"|".join(board),
            "turn": "D" if self.env.red_to_move else "T",
            "aiEnabled": self.ai_enabled,
            "aiLevel": self.ai_level}

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
        
