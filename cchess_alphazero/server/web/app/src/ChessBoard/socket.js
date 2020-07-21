import io from 'socket.io-client';

export const appURL = "http://localhost:5000";
export const socket = io(appURL + '/guide', {secure: true, reconnect: true, rejectUnauthorized: false});