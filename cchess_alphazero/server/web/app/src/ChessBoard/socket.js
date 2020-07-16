import io from 'socket.io-client';

const appURL = "http://localhost:5000";
export const socket = io(appURL + '/guide');