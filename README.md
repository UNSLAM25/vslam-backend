# VSLAM backend

This repository holds demos and tests of Python web server interacting with VSLAM.

Hols a copy of wasm files from wasm-preprocessor repository, and a modified copy of index.html and index.js from web-preprocessor repository to access the webcam and execute webassembly.

Like web-preprocessor reposotory, this one has a very simple Python web server without security.  Usually it won't work because its lack of certificates.  To make the page work in chrome (PC or mobile), you need to add the server url to chrome://flags/#unsafely-treat-insecure-origin-as-secure only once, enable it and relaunch your browser


# Web page file system

- index.html
- index.css
- index.js runs the page and invoke the preprocess method once a second
- wasm folder has three files produced by emscripten, with the preprocessor itself

Provided http servers can serve files from symbolic links.

# Modular Python servers

This repository has many Python files, some are programs, some are modules to be imported, and some are both: modules than can be run as programs.

## httpServer.py

Starts a simple http server on given port (defaults to 8000) serving local files.  You can assign a port if starting it as a module, but it only works on port 8000 when run as a program.

It can be run asynchronously on a dedicated thread.
It gets the local IP and prints its IP based index.html url, to facilitate a link.
Not being a secure https server, it also gives directions to twitch chrome://flags for testing and developing.

## getMyIp.py

This module finds out the local machine's IP.
It's useful to provide a link so other devices can open web pages from it.

## websocketServerExample.py

This module can run as a program.  It starts a websocket server on given port (defaults to 8765) with example code processing incoming websockets.
Server can run ascynchronously to be launched on a dedicated thread.  Sample can be found in httpAndWebsocketsServerExample.py .

## httpAndWebsocketsServerExample.py

This sample runs in threads a web server and a websocket server.


## completeSystem.py

This program brings all together running in threads a web server, both vslam viewers, and a websocket server bound to vslam.

## camTest.py

This test don't start any server, it runs vslam locally on a video feed por testing purpouses.
