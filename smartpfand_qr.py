import gradio as gr
import cv2
import sqlite3
from datetime import datetime
import numpy as np

# --- DB Functions ---
def create_db():
    conn = sqlite3.connect("vimoksha.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS returns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        timestamp TEXT,
        amount INTEGER
    )''')
    conn.commit()
    conn.close()

def add_return(code, amount=10):
    conn = sqlite3.connect("vimoksha.db")
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute('INSERT INTO returns (code, timestamp, amount) VALUES (?, ?, ?)', (code, timestamp, amount))
        conn.commit()
        result = f"✅ QR Code: {code}\nTime: {timestamp}\nReward: ₹{amount}"
    except sqlite3.IntegrityError:
        result = f"⚠️ QR Code {code} already used!"
    conn.close()
    return result

# --- QR Detection Logic ---
def scan_qr_from_frame(frame):
    qr_detector = cv2.QRCodeDetector()
    data, bbox, _ = qr_detector.detectAndDecode(frame)

    if bbox is not None:
        for i in range(len(bbox)):
            pt1 = tuple(map(int, bbox[i][0]))
            pt2 = tuple(map(int, bbox[(i + 1) % len(bbox)][0]))
            cv2.line(frame, pt1, pt2, color=(0, 255, 0), thickness=2)

    if data:
        message = add_return(data)
    else:
        message = "No QR Code detected"

    return frame, message

# --- Gradio Interface ---
def gradio_process(image):
    if image is None:
        return None, "No frame received"
    frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    result_frame, message = scan_qr_from_frame(frame)
    result_frame = cv2.cvtColor(result_frame, cv2.COLOR_BGR2RGB)
    return result_frame, message

create_db()

demo = gr.Interface(
    fn=gradio_process,
    inputs=gr.Image(source="webcam", streaming=True),
    outputs=[gr.Image(label="Scanned Frame"), gr.Textbox(label="Result")],
    title="Vimoksha - Bottle Recycling QR Scanner",
    description="Scan a QR code on a bottle to receive ₹10."
)

if __name__ == "__main__":
    demo.launch()


  
         
