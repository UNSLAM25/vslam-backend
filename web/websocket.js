// Open websocket connection
const url = `ws://${location.hostname}:8765`;
const webSocket = new WebSocket(url);
webSocket.onopen = (e) => webSocket.send("Connection open!");
webSocket.onmessage = (msg) => {
    console.log("Received message from WS: ", msg.data);
}

function sendDescriptor(uint8Buffer) {
    const descriptorMessage = {
        type: 'descriptor',
        timestamp: new Date().getTime()
    }

    webSocket.send(JSON.stringify(descriptorMessage));
    webSocket.send(uint8Buffer);
}