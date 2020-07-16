import React, { Component } from 'react';

import { confirmAlert } from 'react-confirm-alert';
import 'react-confirm-alert/src/react-confirm-alert.css';

import './ChessBoard.css';
import ChessMoveFns from './chessMove';
import {socket} from './socket';

const appURL = "http://localhost:5000";

const emptyBoard = () => {
    let board = [];
    for (let x=0; x<9; x++) {
        board[x] = [];
        for (let y=0; y<10; y++) board[x][y] = "";
    }

    return board;
}

const piece2side = name => name.charAt(0)
const piece2kind = name => name.charAt(1)
const isSameSide = (p1, p2) => {
    if (p1 === "" || p2 === "") return false;
    return p1.charAt(0) === p2.charAt(0);
}

const chessFacename = {
    TX: '車',
    DX: '俥',
    TP: '砲',
    DP: '炮',
    TM: '馬',
    DM: '傌',
    TK: '将',
    DK: '帅',
    TS: '士',
    DS: '仕',
    TT: '象',
    DT: '相',
    TC: '卒',
    DC: '兵'
}

const chessMoveList= (coor, board) => {
    console.log("checking move for ", coor);
    const [x, y] = [Number(coor.charAt(0)), Number(coor.charAt(1))];
    const kind = board[x][y].charAt(1);
    const mm = ChessMoveFns[kind](x, y, board).map(c => { console.log(c); return `${c[0]}${c[1]}`});
    console.log("found moves", mm);
    return mm;
}

const ChessTile = (props) => {
    let classes = ["ChessTile", props.piece];
    if (props.clickable) classes.push("Clickable");
    let piece = null;
    if (props.piece !== "") {
        let classes = ["ChessPiece", props.piece.charAt(0)];
        if (props.focused) classes.push("Focus");
        if (props.selected) classes.push("Selected");
        piece = <div className={classes.join(" ")}><span>{chessFacename[props.piece]}</span></div>
    } else if (props.focused) { // focus on empty tile
        piece = <div className="Highligh1"></div>
    }
    let hl = null;
    if (props.highligh) {
        hl = <div className="Highligh"></div>
    }
    
    return (
        <div className={classes.join(" ")} onClick={props.clickable ? props.clicked : null}>{piece}{hl}</div>
    )
}

class ChessBoardGuide extends Component {

    constructor(props) {
        super(props);
        this.state = {
            board: emptyBoard(),
            curTurn: "",
            legalMoves: [],
            rotateBoard: true,
            selectedTile: "",
            lastMoveFrom: "",
            lastMoveTo: "",
            aiStatus: "",
            aiLevel: 0,
            aiGuideFrom: '',
            aiGuideTo: ''
        };

        // socket.on('ziga-guide', this.ziga_guide_recv.bind(this));
    }

    resetState(human_first) {
        this.setState({
            board: emptyBoard(),
            curTurn: "",
            legalMoves: [],
            human_first: human_first,
            selectedTile: "",
            lastMoveFrom: "",
            lastMoveTo: "",
            aiStatus: "",
            aiLevel: 0,
            aiGuideFrom: '',
            aiGuideTo: ''

        });
    }

    componentDidMount() {    
        socket.on('ziga_guide', this.ziga_guide_recv.bind(this))
      }
        

    ziga_guide_recv(msg) {
        console.log('ziga-guide ???', msg);
        if (msg.cmd === 'new-game-found') this.setState({human_first: false});
        if (msg.board != undefined) this.updateBoardStr(msg.board);
        if (msg.status) this.setState({aiStatus: `[${msg.status}] ${msg.mess}`})
        if (msg.aimove) this.setState({aiGuideFrom: `${msg.aimove[0]}${msg.aimove[1]}`,
                                       aiGuideTo: `${msg.aimove[2]}${msg.aimove[3]}`})
    }

    userSideConfirm() {
        confirmAlert({
            title: 'Select side',
            message: 'A new game started. Are you on RED?',
            buttons: [
              {
                label: 'Yes',
                onClick: () => {
                    this.setState({human_first: false});
                    socket.emit('user', {isRed: true})
                }
              },
              {
                label: 'No',
                onClick: () => {
                    this.setState({human_first: true});
                    socket.emit('user', {isRed: false})
                }
              }
            ]
        });
    }

    updateBoardStr(bs) {
        let board = [];
        bs.split('|').forEach(scol => {
            let col = [];
            scol.split('.').forEach(piece => col.push(piece));
            board.push(col);
        })
        this.setState({board: board});
    }

    updateBoardState(nextBoard) {
        this.setState({board: nextBoard});
    }

    render() {
        // let rows = [];
        // for (let r=0; r<10; r++) {
        //     rows[r] = <ChessRow Y={9-r} board={this.state.board} key={`CR${r}`}></ChessRow>;
        // }
        let rows = [9,8,7,6,5,4,3,2,1,0]; // big row on top
        let cols = [0,1,2,3,4,5,6,7,8];
        if (this.state.human_first) {
            rows.reverse();
            cols.reverse();
        }
        return <div>
            <div className="ChessBoard">
                {rows.map(r => 
                    <div className="ChessRow" key={`CR${r}`}>
                        {cols.map(c => {
                            const piece = this.state.board[c][r];
                            const side = piece2side(piece);
                            const tile = `${c}${r}`;
                            const highligh = this.state.legalMoves.includes(tile);
                            //console.log("tile", tile, piece, this.state);
                            return <ChessTile key={tile} 
                                piece={piece} 
                                highligh={this.state.aiGuideTo === tile}
                                clickable={false}
                                clicked={this.chessTileClicked.bind(this, tile, piece)}
                                selected={this.state.aiGuideFrom === tile}
                                focused={false}
                            ></ChessTile>
                        }
                        )}
                    </div>
                )}
            </div>

            <div className="BoardStatus">
                <p>AI status: {this.state.aiStatus}</p>
                <p>AI level: {this.state.aiLevel}</p>
            </div>

            <form>
                <label>Allow AI to move: 
                    <input type="checkbox" defaultChecked={this.state.aiMove} 
                        disabled={this.state.human_first ? this.state.curTurn === 'T' : this.state.curTurn === 'D'}
                        onChange={this.aiMoveChange.bind(this)}></input>
                </label>
                <label >AI level: 
                    {[0,1,2,3,4].map(lvl => 
                       <a key={`ai_level_${lvl}`}>
                           <input type="radio" name={`ai_level_${lvl}`}  
                                  disabled={this.state.human_first ? this.state.curTurn === 'T' : this.state.curTurn === 'D'}
                                  value={lvl} 
                                  checked={this.state.aiLevel==lvl}
                                  onChange={this.aiLevelChange.bind(this, lvl)}/>{lvl}</a> 
                    )}
                </label>
            </form>

            <button onClick={this.reset.bind(this, false)}>Restart. User first</button>
            <button onClick={this.reset.bind(this, true)}>Restart. Guess first</button>
            <button onClick={this.getAIMove.bind(this)}>Get AI move</button>

            {/* <button onClick={this.rotateBoard.bind(this)}>Rotate</button> */}

            {/* <form onSubmit={this.selectPiece.bind(this)}>
                <label>XY: <input type="text" name="sxy" 
                    value={this.state.selectedPiece}
                    onChange={(ev) => { this.setState({selectedPiece: ev.target.value}); console.log(this.state);}}></input>
                </label>
                <button type="submit">Select</button>
            </form>
            
            <form onSubmit={this.movePiece.bind(this)}>
                <label>XY: <input type="text" name="mxy" 
                    value={this.state.lastMoveTo}
                    onChange={(ev) => { this.setState({lastMoveTo: ev.target.value})}}></input>
                </label>
                <button type="submit">Move</button>
            </form>

            <button onClick={this.updateBoard.bind(this)}>Update</button>
            <button onClick={this.reset.bind(this)}>Reset</button> */}

        </div>
    }

    reset(human_first) {
        this.setState({human_first: human_first});
        //this.sendPost({func:'init', hf: human_fisrt})
        socket.emit('user', {cmd: 'restart', isRed: !human_first})
    }

    aiMoveChange(event) {
        const enb = event.target.checked
        this.setState({aiMove:  enb});
        this.sendPost({func: 'enable-ai', pl: enb}).then(r => this.setState({aiMove: r.ai_enb}))
    }

    aiLevelChange(lvl) {
        this.setState({aiLevel: lvl});
        this.sendPost({func: 'set-ai-level', pl: lvl}).then(r => this.setState({aiLevel: r.ai_lvl}))
    }

    getAIMove() {
        this.sendPost({func: 'get-ai-move'})
    }
    
    updateBoard() {
        this.sendPost({func:'get-board'})
    }

    tile2piece(tile) {
        return this.state.board[tile.charAt(0)][tile.charAt(1)]
    }

    
    chessTileClicked(tile, piece) {
        console.log("tileclicked", tile, piece, this.state);
        if (this.state.selectedTile === tile) {
            console.log("X")
            this.setState({selectedTile: "", legalMoves: []});
        } else if (this.state.selectedTile === "" ||
            isSameSide(this.tile2piece(this.state.selectedTile), piece)) {
            console.log("Y")
            this.setState({selectedTile: tile, legalMoves: []})
            // it's too slow ....
            // this.sendPost({func:'get-legal-moves', xy: tile})
            //     .then(json => this.setState({legalMoves: json.moves.map(s => s.trim())}))
            this.setState({legalMoves: chessMoveList(tile, this.state.board)});
        } else {
            this.movePiece(this.state.selectedTile, tile);
            this.setState({selectedTile: "", legalMoves: []});
        }
    }


    movePiece(xy, xy2) {
        // locally update the board, for smooth exp
        let board = [];
        for (let i=0; i<9; i++) board[i] = this.state.board[i].slice();
        const piece = board[xy.charAt(0)][xy.charAt(1)]
        board[xy2.charAt(0)][xy2.charAt(1)] = piece;
        board[xy.charAt(0)][xy.charAt(1)] = "";
        this.setState({lastMoveFrom: xy, 
            lastMoveTo: xy2, 
            curTurn: piece.charAt(0) === 'D' ? 'T' : 'D',
            board: board});
        this.sendPost({func:'move-to', xy: xy, xy2: xy2});
    }

    sendPost(obj) {
        return fetch(appURL, {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(obj)
        })
        .then(resp => resp.json())
        .then(json => { // .tap not work?
            if (json.board) this.setState({board: json.board});
            if (json.turn) this.setState({curTurn: json.turn});
            if (json.moveFrom) this.setState({lastMoveFrom: json.moveFrom});
            if (json.moveTo) this.setState({lastMoveTo: json.moveTo});
            if (json.ai && json.ai.status) alert(`AI send status : ${json.ai.status}`);
            return json;
        })
        .then(json => {console.log("BOARD", json); return json;})
        .catch(err => console.error("BOARD", err))
    }
    
    

};


// const reset = () => sendPost({func:'init', hf: true})

// const updateBoard = () => sendPost({func:'get-board'})

// const selectPiece = () => sendPost({func:'get-legal-moves', x: this.vars['tmpX'], y: this.vars['tmpY']});

// const movePiece = (x, y) => sendPost({func:'move-to',
//                                     x: this.vars['tmpX'], y: this.vars['tmpY'],
//                                     x2: this.vars['x2'], y2: this.vars['y2']});

// sendPost(obj) {
//     fetch(appURL, {
//       method: 'POST',
//       headers: {
//         'Accept': 'application/json',
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify(obj)
//     }).then(resp => resp.json())
//     .then(json => console.log(json))
//     .catch(err => console.error(err))
//   }

export default ChessBoardGuide;
