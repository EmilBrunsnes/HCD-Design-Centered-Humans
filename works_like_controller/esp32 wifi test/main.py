import json
import network
import uasyncio as asyncio
import sys
import time

# Wifi settings
AP_SSID = "None of your damn buisness"
AP_PASS = "password123"

# Collecting the html page
with open("index.html", "r") as f:
    html_content = f.read()

# Position tracking
cursor_position = (0,0)
ready_to_send = False

# Matrix settings
MATRIX_SIZE = (100, 50)
saved_matrix = [["w" for _ in range(MATRIX_SIZE[1])] for _ in range(MATRIX_SIZE[0])]

def create_wifi_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(
        essid=AP_SSID, 
        password=AP_PASS, 
        authmode=network.AUTH_WPA_WPA2_PSK)
        
    while not ap.active():
        time.sleep(0.1)
    print(f"AP Ready at http://{ap.ifconfig()[0]}")



def move_right():
    global cursor_position
    if cursor_position[0] < MATRIX_SIZE[0] - 1:
        cursor_position = (cursor_position[0] + 1, cursor_position[1])
    #print(f"Moved right to {cursor_position}")

def move_left():
    global cursor_position
    if cursor_position[0] > 0:
        cursor_position = (cursor_position[0] - 1, cursor_position[1])
    #print(f"Moved left to {cursor_position}")

def move_up():
    global cursor_position
    if cursor_position[1] > 0:
        cursor_position = (cursor_position[0], cursor_position[1] - 1)
    #print(f"Moved up to {cursor_position}")

def move_down():
    global cursor_position
    if cursor_position[1] < MATRIX_SIZE[1] - 1:
        cursor_position = (cursor_position[0], cursor_position[1] + 1)
    #print(f"Moved down to {cursor_position}")


async def handle_client(reader, writer):
    global ready_to_send
    last_position = (0, 0)
    payload = ""

    try:
        request_line = await reader.readline() # Read the first line of the HTTP request
        if not request_line:
            await writer.aclose()
            return
    
        request_parts = request_line.decode().split(' ') # Split the request line into parts
        if len(request_parts) < 2:
            await writer.aclose()
            return
        path = request_parts[1]

        while True:
            line = await reader.readline() # Read the rest of the HTTP headers
            if not line or line == b'\r\n':
                break

        
        # Setting up the html page when the user first connects to the server
        if path == "/":
            writer.write('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
            writer.write(html_content)
            await writer.drain()
            await writer.aclose()
        
        elif path == "/style.css":
            writer.write('HTTP/1.1 200 OK\r\nContent-Type: text/css\r\n\r\n')
            try:
                with open("style.css", "r") as f:
                    writer.write(f.read())
            except OSError:
                pass # File doesn't exist
            await writer.drain()
            await writer.aclose()

        # --- NEW CODE: Handling the JS file ---
        elif path == "/script.js":
            writer.write('HTTP/1.1 200 OK\r\nContent-Type: application/javascript\r\n\r\n')
            try:
                with open("script.js", "r") as f:
                    writer.write(f.read())
            except OSError:
                pass # File doesn't exist
            await writer.drain()
            await writer.aclose()

        # Once the page is up and starts checking for updates
        elif path == "/events":
            writer.write('HTTP/1.1 200 OK\r\n')
            writer.write('Content-Type: text/event-stream\r\n')
            writer.write('Cache-Control: no-cache\r\n')
            writer.write('Connection: keep-alive\r\n\r\n')
            await writer.drain()

            while True:
                data_dict = None

                if ready_to_send:
                    data_dict = {
                        "t": "p",
                        "x": cursor_position[0],
                        "y": cursor_position[1],
                        "c": "r"
                    }
                    print("Sent pixel")
                    ready_to_send = False
                
                elif cursor_position != last_position:
                    data_dict = {
                        "t": "m",
                        "x": cursor_position[0],
                        "y": cursor_position[1],
                        "c": 0
                    }
                    print(f"Changed position to {cursor_position}")
                    last_position = cursor_position

                if data_dict is not None:
                    #print("--> sent")
                    payload = json.dumps(data_dict)
                    sse_message = f"data: {payload}\n\n"
                    writer.write(sse_message.encode("utf-8"))
                    await writer.drain()

                await asyncio.sleep_ms(200) # Send updates every 200 ms
            
        else:
            writer.write('HTTP/1.1 404 Not Found\r\n\r\n')
            await writer.drain()
            await writer.aclose()
        
    except OSError as e:
        print(f"Client connection error: {e}")
        await writer.aclose()

async def handle_keyboard():
    global ready_to_send
    sreader = asyncio.StreamReader(sys.stdin)

    while True:
        keyboard_input = await sreader.read(1)  # Wait for a single character input

        if keyboard_input == "w":
            move_up()
        elif keyboard_input == "a":
            move_left()
        elif keyboard_input == "s":
            move_down()
        elif keyboard_input == "d":
            move_right()
        elif keyboard_input == "r":
            ready_to_send = True
            print("Ready to send")


async def main():
    create_wifi_ap()

    asyncio.create_task(handle_keyboard())
    server = await asyncio.start_server(handle_client, "0.0.0.0", 80)

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try: 
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped")