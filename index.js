console.log("vslam backend, index.js");

// Singleton of wasm ImagePreprocessor
var preprocessor;

// Module singleton will grow and include emscripten bindings when main.js initialize wasm module
var Module = {
    onRuntimeInitialized: async ()=>{
        console.log("WebAssembly Module loaded", Module, Module.Preprocessor);
        preprocessor = new Module.Preprocessor(200);
        console.log("preprocessor initialized");
        setTimeout(()=>{console.log("setup", window.setup);console.log(setup);setup();}, 1000); // setup is defined in index.js
    }
};

// video from camera
const video = document.getElementById('video');

// internal hidden canvas to capture images from video
const inputCanvas = document.getElementById('input');
const inputImageContext = inputCanvas.getContext('2d', {alpha: false, willReadFrequently: true, /*desynchronized: true*/});;

// canvas to show annotated output
const outputCanvas = document.getElementById('output');
const outputImageContext = outputCanvas.getContext('2d', {desynchronized: true, alpha: false});

// text placeholders
const duration = document.getElementById("preprocess-duration");
const resolution = document.getElementById("resolution");

// Video control buttons
var loopIntervalId;
const playButton = document.getElementById("play");
playButton.addEventListener('click', e => {
    loopIntervalId = setInterval(loop, 1000);
});
const pauseButton = document.getElementById("pause");
pauseButton.addEventListener('click', e => {
    clearInterval(loopIntervalId);
});
const stepButton = document.getElementById("step");
stepButton.addEventListener('click', e => {
    clearInterval(loopIntervalId);
    loop();
});

var myCheckbox = document.getElementById("myCheckbox");

// Open websocket connection
const url = 'ws://' + location.hostname + ':8765';
console.log('Ejecutando test para websockets', url);
const webSocket = new WebSocket(url); // host includes port
webSocket.onopen = (e)=>webSocket.send('Connection open!');

console.log("index.js finished");

/////////////////////////////////////////////////////////////////////////////////////

// wasm ready, Module and preprocessor available
async function setup(){
    console.log("setup...");
    // Open camera
    video.srcObject = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video:{
            width: {ideal: 640},
            height: {ideal: 480},
            facingMode: 'environment'   // rear camera
        }
    });

    video.onloadedmetadata = (e)=>{
        console.log("Video width: " + video.videoWidth);
        console.log("Video height: " + video.videoHeight);
        // set the canvas to the dimensions of the video feed
        inputCanvas.width = video.videoWidth;
        inputCanvas.height = video.videoHeight;
        outputCanvas.width = video.videoWidth;
        outputCanvas.height = video.videoHeight;
    };

    await video.play();

    // starts the annotation loop
    loopIntervalId = setInterval(loop, 300);
}

var features; // for debugging
// Annotation loop
function loop(){
    console.log("-------------------------------");
    // Capture image from video and put it in the heap, so wasm can grab it
    const width = video.videoWidth;
    const height = video.videoHeight;
    resolution.innerText = width + " x " + height;
    inputImageContext.drawImage(video, 0, 0, width, height);
    imgData = inputImageContext.getImageData(0, 0, width, height);    // uint8clampedarray, compatible with Uint8Array

    if(myCheckbox.checked){
        // Send raw image
        console.log("Image");
        webSocket.send(imgData.data.slice());// RGBA
        return;
    }

    const numBytes = imgData.data.length * imgData.data.BYTES_PER_ELEMENT;
    const dataPtr = Module._malloc(numBytes);   // Allocate memory in the heap
    const dataOnHeap = new Uint8Array(Module.HEAPU8.buffer, dataPtr, numBytes);
    dataOnHeap.set(imgData.data);

    // Preprocess image on buffer
    //var features;
    try{
        let startTime = performance.now();
        features = preprocessor.preprocess(dataOnHeap.byteOffset, width, height, 0);
        let preprocessDuration = performance.now() - startTime;

        duration.innerText = Math.floor(preprocessDuration);
        console.log("preprocess duration", preprocessDuration);

        // Send features to server
        if(features){
            console.log("features byteLength: ", features.array.byteLength);
            uint8Buffer = features.array.slice(); // slice() copies the typed array, so it's not longer has a SharedArrayBuffer, which can't be sent
            byteLength = uint8Buffer.byteLength;
            length = uint8Buffer.length;    // = byteLength
            console.log("uint8Buffer byteLength and length: ", byteLength, length); // Always the same
            console.log("Last byte: ", uint8Buffer[length - 1]);    // Always 255
            console.log("1st row:", uint8Buffer.slice(0,32));
            //console.log("last row:", uint8Buffer.slice(length-38,length));
            dataView = new DataView(uint8Buffer.buffer);
            dataViewByteLength = dataView.byteLength
            console.log("dataViewByteLength:", dataViewByteLength);
            for(i=0; i<5; i++){
                console.log(i, dataView.getFloat32(dataViewByteLength-38+4*i, true))
            }
            if(uint8Buffer[length - 1] == 255){   // debug flag
                console.log("Debug:");
                var descriptorSum = 0;
                for(var i=0; i<32; i++){
                    descriptorSum += uint8Buffer[i];
                }
                var debugSum = dataView.getFloat32(dataViewByteLength - 22, true);   // index 4 float, last row: -38+4*4 = -22
                if(debugSum != descriptorSum){
                    console.log("ERROR in descriptor checksum (desc, debug):", descriptorSum, debugSum);
                } else {
                    console.log("Descriptors are fine!");
                }
            } else {
                console.log("No debug!");
            }

            webSocket.send(uint8Buffer);

        }

    } catch(err) {
        console.error("error", err);
    } finally {
        Module._free(dataPtr);
        console.log("image memory released");
    }

    // Show annotated image
    annotatedImage = preprocessor.getAnnotations();
    if(annotatedImage){
        outputImageContext.putImageData(new ImageData(new Uint8ClampedArray(annotatedImage.array), annotatedImage.width, annotatedImage.height), 0, 0);
    }
}