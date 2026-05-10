import machine
import network
import uasyncio as asyncio
from machine import Pin

# Hardware setup - GPIO pins
BUTTON_PINS = {"right": 4, "left": 5}
button_right = Pin(BUTTON_PINS["right"], Pin.IN, Pin.PULL_UP)
button_left = Pin(BUTTON_PINS["left"], Pin.IN, Pin.PULL_UP)

# Wifi settings
AP_SSID = "ESP32-AP"
AP_PASS = "password123"

# Collecting the html page
with open("index.html", "r") as f:
    html_content = f.read()

# Position tracking
current_position = (0,0)

# Matrix size definitions
MATRIX_WIDTH = 100
MATRIX_HEIGHT = 50

def handle_button_press(pin, direction):
    print(f"Button on pin {pin} pressed! Going {direction}.")
    if(direction == "right"):
        move_right()
    elif(direction == "left"):
        move_left()

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


button_right.irq(
    trigger=Pin.IRQ_FALLING, 
    handler= lambda pin: handle_button_press(BUTTON_PINS["right"], "right"))
button_left.irq(
    trigger=Pin.IRQ_FALLING, 
    handler= lambda pin: handle_button_press(BUTTON_PINS["left"], "left"))

def move_right():
    global current_position
    if current_position[0] < MATRIX_WIDTH - 1:
        current_position = (current_position[0] + 1, current_position[1])
    print(f"Moved right to {current_position}")

def move_left():
    global current_position
    if current_position[0] > 0:
        current_position = (current_position[0] - 1, current_position[1])
    print(f"Moved left to {current_position}")


async def handle_client(reader, writer):
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

        # Once the page is up and starts checking for updates
        elif path == "/events":
            writer.write('HTTP/1.1 200 OK\r\n')
            writer.write('Content-Type: text/event-stream\r\n')
            writer.write('Cache-Control: no-cache\r\n')
            writer.write('Connection: keep-alive\r\n\r\n')
            await writer.drain()

            while True:
                writer.write(f"data: {current_position}\n\n") # Send the current position as an SSE event
                await writer.drain()

                await asyncio.sleep_ms(200) # Send updates every 200 ms
            
        else:
            writer.write('HTTP/1.1 404 Not Found\r\n\r\n')
            await writer.drain()
            await writer.aclose()
        
    except OSError as e:
        print(f"Client connection error: {e}")
        await writer.aclose()


async def main():
    create_wifi_ap()

    server = await asyncio.start_server(handle_client, "0.0.0.0", 80)

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try: 
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped")