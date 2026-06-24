# Development guide
This document serves as the absolute ground truth for AI development agents (`Cursor`, `Windsurf`, `GitHub Copilot`) and human developers modifying the backend (Python/Docker) and web frontend. 

## Intent
This document provides guide and context to agents and human developers for experimentation purposes, thus providing references to facilitate code modifications.

This context asumes developers want to expand the basic capabilities of this system for applications, providing warnings and marking forbiden code.  Those are not suitable for developers with other intentions, like improving the underlying hybrid visual slam system.

# Backend and frontend system
This is a complex visual slam system wrapping stella_vslam, but here it is presented as a simple backend python web sever and a frontend web page.

- completeSystem.py: python web server, serving http://*host*/index.html, and websocket server
- web/index.html: default page served
- web/index.js: index.html main code
- web/websocket.js: index.html websocket communication module

## Backend: completeSystem.py
Basic http server serving files on web folder, and a websocket server.
Default servers ports can be changed with command line parameters when running.
See *Communications* section for the protocol reference over websocket.

completeSystem runs in many threads:

- vslamSystem: visual slam stella_vslam backend system
- runHttpserver: simple http server
- runWebsocketServer: websocket server
- vslamViewer: visual slam iridescence viewer for stella_vslam

vslamViewer runs in the main thread blocking it, showing a window with an user interface, until the user asks the application for shutdown.  The control returns to completeSystem main threads who pproperly shutdown the system.

Developers may be interested in upgrading http to https and modify the http server code.  If not, developers main focus may be in `onWebsocket` listener, receiving data and requests from the web page.  The line `async for message in websocketServer:` properly loops through each message telling two kinds apart:

- text messages, allowing for a JSON protocol described ahead in Communications section
- bytes messages, exclusively for vslam communications

Develpers should expand JSON communication, and avoid messing with bytes communications.

Any communication from server to web page should be done in this point as a response to a websocket inbound.

This is the only point after initialization where completeSystem code calls vslam system, usually only `vslamSystem.feed_monocular_frame()`.


## Frontend: index.js and websocket.js
Developers may be interested in improving the look of index.html and its user interaction modifying index.js.  This javascript file includes the frontend hybrid visual slam part consisting in:

- camera image capture
- processing in wasm module
- formating the result to send to the server

The actual communication happens in websocket.js.  This is a little and simple file.  Developers with intention in improving communicacionts shoud do it in this file.

# Communications
Websocket communications in this system are master-slave like: server only responds to web page queries.  So outgoing messages are sent from `onWebsocket` listener exclusively.

Bytes communications are reserver for the system.  Text communications are assumed to be JSON like and are entirely at the developer's disposal.

All generated code MUST strictly adhere to the architecture, schemas, and rules defined below.

## 🏗️ Core Architecture & Protocol Nature

* **Stateless & Atomic:** All network communications are purely **atomic, fire-and-forget, and stateless**.
* **No Delivery Guarantees:** There are NO ACKs (acknowledgments), handshake verifications, or retry mechanisms implemented at the application layer. The system sends a message and immediately discards its state.
* **Target Environments:**
* Backend: Python inside a Docker container (Hot-reload active via volume mapping).
* Frontend: Web Client.
* External Network: UDP Subscribers.


## ⏱️ Global Timestamp Policy

The `timestamp` field is an optional configuration applied across all JSON messages based on utility.

* **Data Type:** 64-bit Integer representing Unix Epoch time in **milliseconds (ms)**.
* **Clock Sync:** Timestamps are consistent *only* within the same emitter session. Emitter clocks (Web Client vs. Server) are NOT synchronized. Server logic must treat client timestamps as relative values.
* **Critical Business Rule:** For physical measurements, the `timestamp` represents the exact moment the hardware sensor captured the data. For example, before sending a binary image descriptor, the web client transmits a preamble JSON whose `timestamp` marks the exact millisecond the camera shutter was triggered. This is the highest-priority timestamp in the system.

---

## 🎛️ Strict Type Definitions & Message Schemas

### Base Schema

Every single JSON payload transmitted in this system MUST inherit from this base structure.

```typescript
type MessageType = "pose" | "startup" | "descriptor" | "image" | "subscribe";

interface BaseMessage {
  type: MessageType;
  timestamp?: number; // Optional unix epoch in milliseconds
}

```

---

### 1. Pose Update Message (`"type": "pose"`)

**Direction:** Server ➔ Web Clients & UDP Subscribers.
**Trigger:** Emitted every time VSLAM successfully or unsuccessfully processes an image descriptor.

```typescript
type SystemStatus = "ok" | "lost" | "initializing";

interface PoseMessage extends BaseMessage {
  type: "pose";
  status: SystemStatus;
  Twc?: number[][];   // 4x4 float matrix. Absent if status is "lost" or "initializing"
  pose2D?: [number, number, number]; // [x, y, alpha]. Absent if status is "lost" or "initializing"
  Trc?: number[][];   // Reserved for future use. Optional 4x4 matrix converting w to r
}

```

#### JSON Payload Example (Status: "ok")

```json
{
  "type": "pose",
  "timestamp": 1719234000000,
  "status": "ok",
  "Twc": [
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 1.0]
  ],
  "pose2D": [10.50, 5.25, 1.57]
}

```

#### Field Specifications

| Field | Type | Mandatory | Description |
| --- | --- | --- | --- |
| `status` | `String` | **Yes** | Strict Enum: `"ok"`, `"lost"`, or `"initializing"`. |
| `Twc` | `Array<Array<Float>>` | Conditional | 4x4 Matrix. Camera pose relative to VSLAM virtual world before reference correction. **MUST be omitted** if `status` is `"lost"` or `"initializing"`. |
| `pose2D` | `Array<Float>` | Conditional | Format `[x, y, alpha]`. 2D position on the horizontal reference plane and orientation angle. Uses user-defined calibration reference coordinates. **MUST be omitted** if `status` is `"lost"` or `"initializing"`. |

---

### 2. System Startup Message (`"type": "startup"`)

**Direction:** Web Client ➔ Server.
**Trigger:** Sent upon explicit user instruction to initialize the VSLAM pipeline with specific camera calibration attributes.

```typescript
interface StartupMessage extends BaseMessage {
  type: "startup";
  config: string; // Entire raw contents of a vslam config.yaml file
}

```

#### JSON Payload Example

```json
{
  "type": "startup",
  "timestamp": 1719234000000,
  "config": "camera_distortion: [0.0, 0.0]\ncamera_matrix: [320, 0, 0, 240]\nprojection: perspective"
}

```

#### Field Specifications

| Field | Type | Mandatory | Description |
| --- | --- | --- | --- |
| `config` | `String` | **Yes** | Complete raw text content of the VSLAM `config.yaml` file. The server will intercept this string, write it locally to a physical file, and feed it into the VSLAM process. |

---

### 3. Binary Preambles (`"type": "descriptor" | "image"`)

**Direction:** Web Client ➔ Server.
**Trigger:** Transmitted via WebSockets immediately prior to sending a raw binary payload.

```typescript
interface PreambleMessage extends BaseMessage {
  type: "descriptor" | "image";
}

```

#### JSON Payload Example

```json
{
  "type": "descriptor",
  "timestamp": 1719234015500
}

```

#### Structural Behavior

* **Fallback Behavior:** If the server receives a raw binary message over WebSockets without a preceding JSON preamble, it **MUST default** to treating the binary data as a `"descriptor"`.
* **Design Requirement:** Clients should always send the preamble because it carries the critical hardware timestamp of the original image capture.

---

### 4. UDP Topic Subscription (`"type": "subscribe"`)

**Direction:** External UDP Device ➔ Server.
**Trigger:** Sent by an external network node requesting stream access to the publisher's single data topic.

```typescript
interface SubscribeMessage extends BaseMessage {
  type: "subscribe";
  port?: number; // Target UDP port. If missing, use network origin port
}

```

#### JSON Payload Example

```json
{
  "type": "subscribe",
  "port": 5005,
  "timestamp": 1719234000000
}

```

#### Field Specifications & Server Behavior

| Field | Type | Mandatory | Description |
| --- | --- | --- | --- |
| `port` | `Integer` | No | Target UDP port where the external device expects data. If omitted, the server **MUST read the source port** from the incoming UDP packet header and use it as the destination. |

* **Subscription Confirmation:** To confirm a successful subscription, the server **MUST immediately reply** by sending the most recently cached `"pose"` update message to the subscriber.

---

## 🤖 Strict AI Generation Directives

When writing, refactoring, or optimizing code for this codebase, the AI Agent MUST comply with the following instructions:

1. **Never Assume State:** Do not generate wrapper code that waits for acknowledgment, tracks message delivery, or queues failed packets. Write lightweight, high-throughput network handlers.
2. **Strict Variable Naming:** Do NOT rename mathematical variables. The tokens `Twc`, `Trc`, and `pose2D` must remain exactly as defined. Do not map them to alternatives like `camera_matrix`, `world_pose`, etc.
3. **Null-Safety / Key-Absence:** When writing server parsing logic or frontend rendering components, always check if `status === "ok"` before accessing `Twc` or `pose2D`. Code generators must handle cases where these keys are entirely absent from the JSON object structure.