from machine import ADC,Pin
import time

xAxis = ADC(Pin(32, Pin.IN)) # create an ADC object acting on a pin
xAxis.atten(xAxis.ATTN_11DB)
yAxis = ADC(Pin(35, Pin.IN)) # create an ADC object acting on a pin
yAxis.atten(yAxis.ATTN_11DB)
button = Pin(18, Pin.IN, Pin.PULL_UP)

while True:
    xValue = xAxis.read()  # read a raw analog value in the range 0-4095
    yValue = yAxis.read()  # read a raw analog value in the range 0-4095
    btnValue = button.value()
    print(f"X:{xValue}, Y:{yValue}, Button:{btnValue}")
    time.sleep(0.1)

'''
elif keyboard_input in COLOR_CODES.keys():
    current_color = keyboard_input
    confirmed_pixel = [cursor_position[0], cursor_position[1], current_color]
    saved_matrix[cursor_position[1]][cursor_position[0]] = current_color
    print(optimize_initial_payload())'''