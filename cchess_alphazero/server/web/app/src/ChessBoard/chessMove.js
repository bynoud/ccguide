
const comp2xy = (coor) => [Number(coor.charAt(0)), Number(coor.charAt(1))];
const piece2side = (piece) => (piece === "") ? "" : piece.charAt(0);

const moveable = (myside, x, y, board) => {
    if (x < 0 || y < 0 || x > 8 || y > 9) return false;
    return (piece2side(board[x][y]) !== myside);
}

const moveFilter = (curCoor, offCoor, board, fn=null) => {
    const side = piece2side(board[curCoor[0]][curCoor[1]]); 
    const cx = curCoor[0] + offCoor[0];
    const cy = curCoor[1] + offCoor[1];
    if (!moveable(side, cx, cy, board)) return false;
    return (fn !== null) ? fn(cx, cy, offCoor[0], offCoor[1], side) : true;
}

const kingMove = (x, y, board) => {
    return [[0,1], [0,-1], [1,0], [-1,0]].filter(c => moveFilter([x,y], c, board, (cx,cy) => {
        if (cx < 3 || cx > 5) return false;
        if (cy > 2 && cy < 7) return false;
        return true;
    })).map(c => [x+c[0], y+c[1]]);
}

const mandarinMove = (x, y, board) => {
    return [[1,1], [-1,1], [-1,-1], [1,-1]].filter(c => moveFilter([x,y], c, board, (cx,cy) => {
        if (cx < 3 || cx > 5) return false;
        if (cy > 2 && cy < 7) return false;
        return true;
    })).map(c => [x+c[0], y+c[1]]);
}

const elephantMove = (x, y, board) => {
    return [[2,2], [-2,2], [-2,-2], [2,-2]].filter(c => moveFilter([x,y], c, board, (cx,cy) => {
        console.log("T", x, y, cx, cy, c, x+c[0]/2, y+c[1]/2, board[x+c[0]/2][y+c[1]/2]);
        if ((y < 5 && cy >= 5) || (y > 4 && cy <= 4)) return false;
        return (piece2side(board[x+c[0]/2][y+c[1]/2]) === "");
    })).map(c => [x+c[0], y+c[1]]);
}

const rookTravel = (side, x, y, sx, endx, sy, endy, board) => {
    let cx = x+sx;
    let cy = y+sy;
    const r = [];
    while (cx !== endx && cy !== endy) {
        const cside = piece2side(board[cx][cy]);
        if (cside === side) break;
        r.push([cx, cy])
        if (cside !== "") break;
        cx += sx;
        cy += sy;
    }
    return r;
}
const rookMove = (x, y, board) => {
    const side = piece2side(board[x][y]);
    const moves = [
        ...rookTravel(side, x, y, 1, 9, 0, 10, board),
        ...rookTravel(side, x, y, -1, -1, 0, 10, board),
        ...rookTravel(side, x, y, 0, 9, 1, 10, board),
        ...rookTravel(side, x, y, 0, 9, -1, -1, board)
    ];
    return moves;
}

const cannonTravel = (side, x, y, sx, endx, sy, endy, board) => {
    let cx = x+sx;
    let cy = y+sy;
    let jump = false;
    const r = [];
    while (cx !== endx && cy !== endy) {
        const cside = piece2side(board[cx][cy]);
        if (cside !== "") {
            if (!jump) {
                jump = true;
            } else {
                if (cside !== side) r.push([cx, cy]);
                break;
            }
        } else {
            if (!jump) r.push([cx, cy])
        }
        cx += sx;
        cy += sy;
    }
    return r;
}
const cannonMove = (x, y, board) => {
    const side = piece2side(board[x][y]);
    const moves = [
        ...cannonTravel(side, x, y, 1, 9, 0, 10, board),
        ...cannonTravel(side, x, y, -1, -1, 0, 10, board),
        ...cannonTravel(side, x, y, 0, 9, 1, 10, board),
        ...cannonTravel(side, x, y, 0, 9, -1, -1, board)
    ]
    return moves;
}

const horseMove = (x, y, board) => {
    return [[2,1], [2,-1], [1,2], [1,-2], [-1,2], [-1,-2], [-2,1], [-2,-1]].filter(c => moveFilter([x,y], c, board, (cx,cy) => {
        if (c[0] === 2 || c[0] === -2) return piece2side(board[x+c[0]/2][y]) === "";
        else return piece2side(board[x][y+c[1]/2]) === "";
    })).map(c => [x+c[0], y+c[1]]);
}

const pawnMove = (x, y, board) => {
    return [[0,1],[0,-1],[1,0],[-1,0]].filter(c => moveFilter([x, y], c, board, (cx, cy, ox, oy, side) => {
        return (side === 'D') ? ( (oy === -1) ? false :
                                (y < 5 && oy !== 1) ? false : true )
                              : ( (oy === 1) ? false :
                                (y > 4 && oy !== -1) ? false : true);
    })).map(c => [x+c[0], y+c[1]]);
}

const ChessMoveFns = {
    "K": kingMove,
    "S": mandarinMove,
    "T": elephantMove,
    "X": rookMove,
    "P": cannonMove,
    "M": horseMove,
    "C": pawnMove
};

export default ChessMoveFns;
