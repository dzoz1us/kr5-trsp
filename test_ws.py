import asyncio
import websockets
import json

async def test():
    print("Testing WebSocket...")
    try:
        async with websockets.connect("ws://localhost:8000/ws/rooms/test?username=alice") as ws:
            print("Connected!")
            msg = await ws.recv()
            print(f"Received: {msg}")
            
            await ws.send(json.dumps({"type": "message", "text": "Hello!"}))
            print("Message sent!")
            
            response = await ws.recv()
            print(f"Response: {response}")
            
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())