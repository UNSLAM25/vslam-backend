# VSLAM backend

This repository holds demos and tests of Python web server interacting with VSLAM.

completeSystem.py is the actual complete vslam backend.

Holds a copy of wasm files from wasm-preprocessor repository, and a modified copy of index.html and index.js from web-preprocessor repository to access the webcam and execute webassembly.

Like web-preprocessor reposotory, this one has a very simple Python web server without security.  Usually it won't work because its lack of certificates.  To make the page work in chrome (PC or mobile), you need to add the server url to chrome://flags/#unsafely-treat-insecure-origin-as-secure only once, enable it and relaunch your browser.

# Installation

It is a long and painful journey.
It involves building a modified stella_vslam project and making a Python module out of it, like `stellavslam.cpython-310-x86_64-linux-gnu.so`.
UNDER CONTRUCTION

`stellavslam.cpython-310-x86_64-linux-gnu.so` file is provided for convenience and without guarantee, **you shouldn't even try to run a native file like this** if you don't really trust the author.  With this in mind, if you are a Linux user you probably already know this, and if you are a Windows user this file won't work for you (unless wsl, if you know what I mean).

`stellavslam.cpython-310-x86_64-linux-gnu.so` is only a Python binder, you need `libstella_vslam.so` and `libpangolin_viewer.so` installed in your system: that's what building stella_vslam does.


## Python libraries
Other than it, this repository is made of Python and web files, with at least one library needed:

 - Numpy
 - Websockets
 - OpenCV, not needed in completeSystem.py, only used in camTest.py and pangolin-bindings-test.py

Installation with pip (you can use other Python package manager like conda, whatever you choose you need to install it first)

    pip install numpy
    pip install websockets
    pip install opencv-contrib-python

You don't really need contrib in opencv, you can use other opencv packages instead.

# Web page file system

- index.html
- index.css
- index.js runs the page and invoke the preprocess method once a second
- wasm folder has three files produced by emscripten, with the preprocessor itself

Provided http servers can serve files from symbolic links.

# Modular Python servers

This repository has many Python files, some are programs, some are modules to be imported, and some are both: modules than can be run as programs.

This Python programs are the only onse using stella_vslam module:

- camTest.py
- completeSystem.py
- pangolin-bindings-test.py

The other Python programs are web servers not interacting with vslam.

## httpServer.py

Starts a simple http server on given port (defaults to 8000) serving local files.  You can assign a port if starting it as a module, but it only works on port 8000 when run as a program.

It can be run asynchronously on a dedicated thread.
It gets the local IP and prints its IP based index.html url, to facilitate a link.
Not being a secure https server, it also gives directions to twitch chrome://flags for testing and developing.

## getMyIp.py

This module finds out the local machine's IP.
It's useful to provide a link so other devices can open web pages from it.

The only function is get_my_ip_address() with an optional IP argument to try to open a socket against.  Defaults to 8.8.8.8, Google domain name system's IP, known for being always up.

## websocketServerExample.py

This module can run as a program.  It starts a websocket server on given port (defaults to 8765) with example code processing incoming websockets as default listener.  You can provide your own listener instead.

Server can run ascynchronously to be launched on a dedicated thread.  Sample can be found in httpAndWebsocketsServerExample.py .

## httpAndWebsocketsServerExample.py

This sample runs in threads a web server and a websocket server.


## completeSystem.py

This program brings all together running in threads a web server, both vslam viewers, and a websocket server bound to vslam.

The clean way to quit is by pressing Terminate button on Pangolin viewer.

## camTest.py

This test don't start any server, it runs vslam locally on a video feed por testing purpouses.
