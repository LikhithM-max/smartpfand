import streamlit as st
import sqlite3
from datetime import datetime
import cv2
from pyzbar.pyzbar import decode

DB_NAME = "pfand.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    st.write("Initializing database…")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bottle_returns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bottle_id TEXT UNIQUE,
            timestamp TEXT,
            amount INTEGER DEFAULT 10
        )
    """)
    conn.commit()
    conn.close()

def add_bottle(bottle_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO bottle_returns (bottle_id, timestamp) VALUES (?, ?)",
                    (bottle_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def return_bottle(bottle_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM bottle_returns WHERE bottle_id = ?", (bottle_id,))
    row = cur.fetchone()
    if row:
        cur.execute("DELETE FROM bottle_returns WHERE bottle_id = ?", (bottle_id,))
        conn.commit()
        conn.close()
        return {"bottle_id": bottle_id, "timestamp": row[2], "amount": "₹10"}
    conn.close()
    return None

def get_all_bottles():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM bottle_returns")
    rows = cur.fetchall()
    conn.close()
    return rows

def scan_qr_code():
    st.info("📷 Scanning QR code… Press Q to cancel")
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        decoded = decode(frame)
        if decoded:
            cap.release()
            cv2.destroyAllWindows()
            return decoded[0].data.decode("utf-8")
        cv2.imshow("Scan QR (Q to quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    return None

st.set_page_config(page_title="SmartPfand QR", layout="centered")
st.title("♻️ SmartPfand – QR Code Bottle Return System")
init_db()

mode = st.radio("Choose action", ["Deposit Bottle", "Return Bottle", "View Bottles"])

if mode != "View Bottles":
    use_qr = st.checkbox("Use QR scanner")
    bottle_id = None
    if use_qr and st.button("Scan QR"):
        bottle_id = scan_qr_code()
        if bottle_id:
            st.success(f"Scanned: {bottle_id}")
        else:
            st.warning("No QR code found.")
    else:
        bottle_id = st.text_input("Enter bottle ID")

    if st.button("Submit"):
        if not bottle_id:
            st.error("Enter or scan a bottle ID.")
        elif mode == "Deposit Bottle":
            st.success("Deposited!") if add_bottle(bottle_id) else st.warning("Already exists.")
        else:
            receipt = return_bottle(bottle_id)
            if receipt:
                st.success("Returned!")
                st.code(f"Receipt\n-------\nBottle ID: {receipt['bottle_id']}\nReturned At: {receipt['timestamp']}\nAmount: {receipt['amount']}")
            else:
                st.error("Bottle not found or already returned.")
else:
    st.subheader("Bottles in system")
    all_bottles = get_all_bottles()
    if all_bottles:
        for row in all_bottles:
            st.write(f"• {row[1]} at {row[2]}")
    else:
        st.info("No bottles logged yet.")
