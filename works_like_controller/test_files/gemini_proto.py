import network
import socket
import machine
import time
import os # We use os.urandom for ultra-fast, memory-efficient random bytes

AP_SSID = 'ESP32_Matrix'
AP_PASS = 'matrix123' 

BUTTON_PIN = 4 
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

# --- MAXIMIZED GRID SETTINGS ---
MATRIX_WIDTH = 64
MATRIX_HEIGHT = 64
TOTAL_PIXELS = MATRIX_WIDTH * MATRIX_HEIGHT
BYTES_PER_FRAME = TOTAL_PIXELS * 3 # 3 bytes (R, G, B) per pixel

# Pre-allocate a single, flat block of memory. 
# This completely prevents MemoryErrors and fragmentation.
matrix_state = bytearray(BYTES_PER_FRAME)
button_flag = False

def create_access_point():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_SSID, password=AP_PASS, authmode=network.AUTH_WPA_WPA2_PSK)
    while not ap.active():
        time.sleep(0.1)
    print(f"AP Ready at http://{ap.ifconfig()[0]}")

def generate_colors():
    global matrix_state
    # os.urandom generates random bytes at C-level speeds.
    # It instantly fills our 12KB array without looping.
    try:
        matrix_state[:] = os.urandom(BYTES_PER_FRAME)
    except AttributeError:
        # Fallback if your specific ESP32 firmware lacks os.urandom
        import random
        for i in range(BYTES_PER_FRAME):
            matrix_state[i] = random.getrandbits(8)

# Renamed to avoid the variable collision that broke your code!
def handle_button_press(pin):
    global button_flag
    button_flag = True

button.irq(trigger=machine.Pin.IRQ_FALLING, handler=handle_button_press)

def start_server():
    global button_flag
    
    with open('index.html', 'r') as f:
        html_content = f.read()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 80))
    s.listen(5)
    s.settimeout(0.2) 

    generate_colors()

    while True:
        if button_flag:
            generate_colors()
            button_flag = False

        try:
            conn, addr = s.accept()
            request = conn.recv(1024).decode('utf-8')
            
            if not request:
                conn.close()
                continue
            
            if 'GET /data' in request:
                conn.send('HTTP/1.1 200 OK\n')
                # Tell the browser we are sending raw binary bytes, not text!
                conn.send('Content-Type: application/octet-stream\n')
                conn.send('Connection: close\n\n')
                # Send the pre-allocated memory block directly over the socket
                conn.sendall(matrix_state)
            else:
                conn.send('HTTP/1.1 200 OK\n')
                conn.send('Content-Type: text/html\n')
                conn.send('Connection: close\n\n')
                conn.sendall(html_content)
                
            conn.close()
            
        except OSError:
            pass

create_access_point()
start_server()