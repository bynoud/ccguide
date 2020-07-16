import React, { Component } from 'react';
import './App.css';

import ChessBoard from './ChessBoard/ChessBoard';
import ChessBoardGuide from './ChessBoard/ChessBoardGuide';

const appURL = "http://localhost:5000";
class App extends Component {
  curX = -1;
  curY = -1;

  vars = {
    tmpX: 0, tmpY: 0,
    x2: 0, y2: 0
  }

  render() {
    return (
      // <ChessBoard></ChessBoard>
      <ChessBoardGuide></ChessBoardGuide>
    );
  }

  setVar(name, event) {
    console.log("var", name, event.target.value)
    this.vars[name] = event.target.value;
    console.log(this.vars)
  }


  reset() {
    this.sendPost({func:'init', hf: true})
  }

  updateBoard() {
    this.sendPost({func:'get-board'})
  }

  selectPiece() {
    this.sendPost({func:'get-legal-moves', x: this.vars['tmpX'], y: this.vars['tmpY']});
  }

  movePiece(x, y) {
    this.sendPost({func:'move-to', x: this.vars['tmpX'], y: this.vars['tmpY'],
        x2: this.vars['x2'], y2: this.vars['y2']});
  }

  sendPost(obj) {
    fetch(appURL, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(obj)
    }).then(resp => resp.json())
    .then(json => console.log("BOARD", json))
    .catch(err => console.error("BOARD", err))
  }
}

export default App;
