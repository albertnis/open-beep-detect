let val = 0;

const ws_path = "/ws";
const wsUrl = new URL(ws_path, window.location.href);
wsUrl.protocol = wsUrl.protocol.replace("http", "ws");

const ws = new WebSocket(wsUrl);
ws.addEventListener("message", (ev) => console.log("message is ", ev.data));

// setInterval(() => {
//   ws.send(++val);
// }, 1000);
