import machine
import network
import uasyncio as asyncio
from machine import Pin

# Hardware setup: Button on GPIO 4
BUTTON_PIN = 4
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

AP_SSID = 'ESP32_Matrix'
AP_PASS = 'matrix123' 

# HTML content (Notice the JavaScript changes in the next section)
with open('index.html', 'r') as f:
        html_content = f.read()

def handle_button_press(pin):
    global button_flag
    button_flag = True

button.irq(trigger=machine.Pin.IRQ_FALLING, handler=handle_button_press)

button_flag = False

async def handle_client(reader, writer):
    """Handles incoming HTTP requests manually."""
    try:
        # Read the first line of the HTTP request (e.g., "GET / HTTP/1.1")
        request_line = await reader.readline()
        if not request_line:
            await writer.aclose()
            return

        # Parse the requested path
        request_parts = request_line.decode().split(' ')
        if len(request_parts) < 2:
            await writer.aclose()
            return
        path = request_parts[1]

        # Consume the rest of the HTTP headers so the browser doesn't hang
        while True:
            line = await reader.readline()
            if not line or line == b'\r\n':
                break

        # Route 1: Serve the web page
        if path == '/':
            writer.write('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
            writer.write(html_content)
            await writer.drain()
            await writer.aclose()

        # Route 2: The SSE Event Stream
        elif path == '/events':
            # Send SSE headers. The "keep-alive" tells the browser we aren't hanging up.
            writer.write('HTTP/1.1 200 OK\r\n')
            writer.write('Content-Type: text/event-stream\r\n')
            writer.write('Cache-Control: no-cache\r\n')
            writer.write('Connection: keep-alive\r\n\r\n')
            await writer.drain()
            
            last_state = button_flag
            
            # Keep this connection open forever
            while True:
                current_state = button_flag
                
                # If button changed, push a message
                if current_state != last_state:
                    if current_state == 0: # Pressed
                        writer.write('data: MOVE_RIGHT\n\n')
                    else:                  # Released
                        writer.write('data: STOP\n\n')
                    
                    await writer.drain() # Push the data to the browser
                    last_state = current_state
                    
                # Yield control to allow other clients to connect
                await asyncio.sleep_ms(20)

        # Handle 404 Not Found
        else:
            writer.write('HTTP/1.1 404 Not Found\r\n\r\n')
            await writer.drain()
            await writer.aclose()

    except OSError:
        # This triggers when the user closes the web browser tab
        pass
    finally:
        await writer.aclose()

def connect_wifi():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_SSID, password=AP_PASS, authmode=network.AUTH_WPA_WPA2_PSK)
    while not ap.active():
        time.sleep(0.1)
    print(f"AP Ready at http://{ap.ifconfig()[0]}")

async def main():
    connect_wifi()
    print("Starting raw async server on port 80...")
    # Start the asyncio TCP server
    server = await asyncio.start_server(handle_client, '0.0.0.0', 80)
    
    # Keep the event loop running forever
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped.")