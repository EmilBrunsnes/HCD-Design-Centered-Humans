console.log("Script loaded");
let color_codes = {
            "r": "red",
            "g": "green",
            "b": "blue",
            "y": "yellow",
            "c": "cyan",
            "m": "magenta",
            "w": "white",
            "k": "black"
        }

const canvas = document.getElementById('pixelCanvas');
const cursor = document.getElementById('circle_cursor');
const ctx = canvas.getContext('2d');
        
const MATRIX_SIZE = { width: 100, height: 50 };
const PIXEL_SIZE = { width: 800 / MATRIX_SIZE.width, height: 400 / MATRIX_SIZE.height };

const evtSource = new EventSource('/events');

ctx.fillStyle = "white";
ctx.fillRect(0, 0, canvas.width, canvas.height);

const rect = canvas.getBoundingClientRect();
  

function drawPixelOnCanvas(x, y, color) {
    ctx.fillStyle = color_codes[color] || "white"; // Default to white if color code is unknown
    ctx.fillRect(x * PIXEL_SIZE.width, y * PIXEL_SIZE.height, PIXEL_SIZE.width, PIXEL_SIZE.height);
}

function moveCursorHighlight(x, y) {
    const cursor_x = x * PIXEL_SIZE.width + PIXEL_SIZE.height / 2 + rect.left;
    const cursor_y = y * PIXEL_SIZE.height + PIXEL_SIZE.height / 2 + rect.top;
            
    cursor.style.transform = `translate(${cursor_x}px, ${cursor_y}px)`;
}


evtSource.onmessage = (event) => { //wait for data from the server

    let data = JSON.parse(event.data);
    console.log("Message received") 

    if (data.t === "p") {
        drawPixelOnCanvas(data.x, data.y, data.c); // Draw the pixel on the canvas
    } 
    else if (data.t === "m") {
        moveCursorHighlight(data.x, data.y); // Move the cursor highlight
    }
};

drawPixelOnCanvas(50, 25, "g"); // Test pixels
drawPixelOnCanvas(50, 30, "y");
drawPixelOnCanvas(30, 25, "b"); 
drawPixelOnCanvas(10, 10, "c"); 
drawPixelOnCanvas(99, 49, "m");

moveCursorHighlight(20, 25); // Test cursor highlight