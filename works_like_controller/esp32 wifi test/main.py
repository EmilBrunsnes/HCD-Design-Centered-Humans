import json
import network
import uasyncio as asyncio
import sys
import time
from machine import Pin, ADC
import random

# Wifi settings
AP_SSID = "None of your damn buisness"
AP_PASS = "password123"

# Collecting the html page
with open("index.html", "r") as f:
    html_content = f.read()

# Joystick hardware setup
xAxis = ADC(Pin(32, Pin.IN)) # create an ADC object acting on a pin
xAxis.atten(xAxis.ATTN_11DB)
yAxis = ADC(Pin(35, Pin.IN)) # create an ADC object acting on a pin
yAxis.atten(yAxis.ATTN_11DB)
button = Pin(18, Pin.IN, Pin.PULL_UP)

# Joystick sensitivity thresholds
upper_min_to_move = 2250
lower_min_to_move = 1450
lower_two_step_threshold = 400
upper_two_step_threshold = 3600

joystick_sensitivity_delay = 200

# Position tracking
cursor_position = (0,0)
confirmed_pixel = []


# Matrix settings
MATRIX_SIZE = (100, 50)
saved_matrix = [["w" for _ in range(MATRIX_SIZE[1])] for _ in range(MATRIX_SIZE[0])]

COLOR_CODES = {
            "r": "red",
            "g": "green",
            "b": "blue",
            "y": "yellow",
            "c": "cyan",
            "m": "magenta",
            "w": "white",
            "k": "black"
        }


current_color = ""

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


def move_cursor(direction, amount):
    global cursor_position
    if direction == "right" and cursor_position[0] < MATRIX_SIZE[0] - 1:
        cursor_position = (cursor_position[0] + amount, cursor_position[1])
    elif direction == "left" and cursor_position[0] > 0:
        cursor_position = (cursor_position[0] - amount, cursor_position[1])
    elif direction == "up" and cursor_position[1] > 0:
        cursor_position = (cursor_position[0], cursor_position[1] - amount)
    elif direction == "down" and cursor_position[1] < MATRIX_SIZE[1] - 1:
        cursor_position = (cursor_position[0], cursor_position[1] + amount)


def fill_random_matrix(colours):
    global saved_matrix
    for r in range(MATRIX_SIZE[0]):
        for c in range(MATRIX_SIZE[1]):
            if random.random() < 0.1:
                saved_matrix[r][c] = random.choice(colours)

def optimize_initial_payload():
    for r, row_data in enumerate(saved_matrix):
        for c, color in enumerate(row_data):
            if color != "w":
                yield r, c, color

def check_for_joystick_movement():
    global confirmed_pixel
    global current_color
    global saved_matrix

    xValue = xAxis.read()
    yValue = yAxis.read()
    btnValue = button.value()

    if lower_min_to_move < xValue < lower_two_step_threshold:
        print("Left 1")
        move_cursor("left", 1)
    elif upper_min_to_move < xValue < upper_two_step_threshold:
        print("Righ 1t")
        move_cursor("right", 1)
    elif lower_min_to_move < yValue < lower_two_step_threshold:
        print("Up 1")
        move_cursor("up", 1)
    elif upper_min_to_move < yValue < upper_two_step_threshold:
        print("Down 1")
        move_cursor("down", 1)
    elif xValue <= lower_two_step_threshold:
        print("Left 2 2")
        move_cursor("left", 2)
    elif xValue >= upper_two_step_threshold:
        print("Right 2")
        move_cursor("right", 2)
    elif yValue <= lower_two_step_threshold:
        print("Up 2")
        move_cursor("up", 2)
    elif yValue >= upper_two_step_threshold:
        print("Down 2")
        move_cursor("down", 2)
    elif btnValue == 0:
        current_color = "r"
        confirmed_pixel = [cursor_position[0], cursor_position[1], current_color]
        saved_matrix[cursor_position[1]][cursor_position[0]] = current_color
        print("Button pressed")

async def handle_client(reader, writer):
    last_position = (0, 0)
    last_confirmed_pixel = []
    payload = ""
    has_initialized = False

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

                if not has_initialized:
                    for r, c, color in optimize_initial_payload():
                        data_dict = {
                            "t": "d",
                            "x": r,
                            "y": c,
                            "c": color
                        }
                        payload = json.dumps(data_dict)
                        sse_message = f"data: {payload}\n\n"
                        writer.write(sse_message.encode("utf-8"))
                        await writer.drain()

                    print("Sent initial payload")
                    has_initialized = True

                elif last_confirmed_pixel != confirmed_pixel and confirmed_pixel != []:
                    last_confirmed_pixel = confirmed_pixel.copy()
                    data_dict = {
                        "t": "d",
                        "x": cursor_position[0],
                        "y": cursor_position[1],
                        "c": current_color
                    }
                    print("Sent pixel")
                
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
    global confirmed_pixel
    global current_color
    global saved_matrix
    sreader = asyncio.StreamReader(sys.stdin)

    while True:
        await asyncio.sleep_ms(joystick_sensitivity_delay)
        #keyboard_input = await sreader.read(1)  # Wait for a single character input
        
        check_for_joystick_movement()




async def main():
    fill_random_matrix(list(COLOR_CODES.keys()))
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

