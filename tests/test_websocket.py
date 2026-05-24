import asyncio
import websockets
import json

async def test_websocket():
    print("=" * 50)
    print("TEST WEBSOCKET CHAT")
    print("=" * 50)
    
    try:
        # Connect Alice
        print("\n1. Connecting Alice...")
        async with websockets.connect("ws://localhost:8000/ws/rooms/test?username=Alice") as alice:
            msg = await alice.recv()
            print(f"   Alice received: {msg}")
            
            # Connect Bob
            print("\n2. Connecting Bob...")
            async with websockets.connect("ws://localhost:8000/ws/rooms/test?username=Bob") as bob:
                msg = await bob.recv()
                print(f"   Bob received: {msg}")
                
                # Alice sends message
                print("\n3. Alice sends message...")
                await alice.send(json.dumps({"type": "message", "text": "Hello everyone!"}))
                print("   Alice sent: 'Hello everyone!'")
                
                # Check both receive
                msg_alice = await alice.recv()
                msg_bob = await bob.recv()
                print(f"\n4. Results:")
                print(f"   Alice received: {msg_alice}")
                print(f"   Bob received: {msg_bob}")
                
                # Check users list
                print("\n5. Checking users in room...")
                import requests
                resp = requests.get("http://localhost:8000/rooms/test/users")
                print(f"   Users: {resp.json()}")
                
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nMake sure the server is running: uvicorn app.main:app --reload")

def test_long_message():
    print("\n" + "=" * 50)
    print("TEST LONG MESSAGE")
    print("=" * 50)
    
    async def run():
        try:
            async with websockets.connect("ws://localhost:8000/ws/rooms/test?username=tester") as ws:
                await ws.recv()
                
                long_text = "x" * 301
                await ws.send(json.dumps({"type": "message", "text": long_text}))
                
                error = await ws.recv()
                print(f"\nResult: {error}")
        except Exception as e:
            print(f"\nERROR: {e}")
    
    asyncio.run(run())

def test_no_username():
    print("\n" + "=" * 50)
    print("TEST WITHOUT USERNAME")
    print("=" * 50)
    
    async def run():
        try:
            async with websockets.connect("ws://localhost:8000/ws/rooms/test") as ws:
                pass
        except Exception as e:
            print(f"\nResult: Connection closed (code 1008) - {e}")
    
    asyncio.run(run())

if __name__ == "__main__":
    asyncio.run(test_websocket())
    test_long_message()
    test_no_username()