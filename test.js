const url = 'ws://' + location.hostname + ':8765';
console.log('Ejecutando test para websockets', url);
const webSocket = new WebSocket(url); // host includes port
webSocket.onopen = (e)=>webSocket.send('Connection open!');
webSocket.onmessage = e=>console.log(e.data);
setInterval(sendData, 1000);

function sendData(){
    var state = webSocket.readyState;
    console.log('State:', state);
    switch(state){
        case 1: // OPEN
        // send some data
        webSocket.send('Sending some text.');
        console.log('ws sent');
        break;

        case 3: // CLOSED
        // Retry
    }
}