# Important notes:

- When changing matrix size, remember to change it both in `main.py` and `script.js`

## SSE messages format

Library with:

- **"t"** = message type (m for move, d for draw, i for intial setup)
- **"x" and "y"** = new positions for cursor / positions of new pixel
- **"c"** = color index

## Color indexes:

"r": "red"  
"g": "green"  
"b": "blue"  
"y": "yellow"  
"c": "cyan"  
"m": "magenta"  
"w": "white"  
"k": "black"

# Flashing the esp32 with micropython

- Connect the board
- _pip install esptool_
- while holding down `boot` button on esp: _python -m esptool --chip esp32 erase_flash_
- go to location of `micropython_flash.bin`
- while holding down `boot` button on esp: _python -m esptool --chip esp32 --port COM5 write_flash -z 0x1000 micropython_flash.bin_

# To use micropython in VS Code:

- Add the `MicroPico`extension to vs code
- Follow instructions to create a project
- Write main code in `main.py`

<u> **To upload all files:** </u> ctrl + shift + P then select Upload project
<u> **To run current file:** </u> Click run in activity bar
