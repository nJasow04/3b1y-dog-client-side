import asyncio
from concurrent import futures
import grpc
import image_stream_pb2
import image_stream_pb2_grpc
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from PIL import Image
import io
import base64
import os
import threading

app = FastAPI()

# In-memory storage for connected WebSocket clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: str):
        to_remove = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                to_remove.add(connection)
        self.active_connections.difference_update(to_remove)

manager = ConnectionManager()

# gRPC Service Implementation
class ImageStreamServicer(image_stream_pb2_grpc.ImageStreamServicer):
    async def SendImage(self, request, context):
        image_bytes = request.image_data
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        message = f"data:image/jpeg;base64,{encoded_image}"
        asyncio.create_task(manager.broadcast(message))
        return image_stream_pb2.ImageResponse(message="Image received and broadcasted")

def serve_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_stream_pb2_grpc.add_ImageStreamServicer_to_server(ImageStreamServicer(), server)
    port = os.getenv("GRPC_PORT", "50051")
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"gRPC server started on port {port}")
    server.wait_for_termination()

# Start gRPC server in a separate thread
grpc_thread = threading.Thread(target=serve_grpc, daemon=True)
grpc_thread.start()

# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep the connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

# Optional: Simple HTML frontend for testing
@app.get("/")
async def get():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Spot Live Stream</title>
    </head>
    <body>
        <h1>Live Stream from Spot</h1>
        <img id="liveStream" src="" alt="Live Stream" />
        <script>
            var ws = new WebSocket("wss://YOUR_CLOUD_RUN_URL/ws"); // Replace with your Cloud Run URL
            ws.onmessage = function(event) {
                document.getElementById("liveStream").src = event.data;
            };
            ws.onopen = function() {
                console.log("Connected to live stream");
            };
            ws.onerror = function(error) {
                console.error("WebSocket error:", error);
            };
            ws.onclose = function() {
                console.log("WebSocket connection closed");
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html_content)
