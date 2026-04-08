from flask import Flask, request, jsonify, render_template, send_file
import csv, os, time

app = Flask(__name__)

# -------- CONFIG --------
DATA_FILE = "sensor_data.csv"
API_KEY = "12b5112c62284ea0b3da0039f298ec7a85ac9a1791044052b6df970640afb1c5"

last_seen = 0
collect_data = True
latest_cmd = ""
view_mode = "live"   # live / full

# -------- INIT FILE --------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id","sensor1","sensor2","sensor3","time"])

# -------- RECEIVE DATA --------
@app.route("/api/data")
def receive():
    global last_seen, collect_data

    key = request.args.get("key")
    if key != API_KEY:
        return "Invalid Key", 403

    last_seen = time.time()

    if not collect_data:
        return "Stopped"

    try:
        s1 = request.args.get("s1")
        s2 = request.args.get("s2")
        s3 = request.args.get("s3")
        now = request.args.get("time")

        with open(DATA_FILE, "r") as f:
            rows = list(csv.DictReader(f))

        # Duplicate check
        for r in rows:
            if r["time"] == now and r["sensor1"] == s1:
                return "Duplicate"

        new_id = int(rows[-1]["id"]) + 1 if rows else 1

        with open(DATA_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([new_id, s1, s2, s3, now])

        return "OK"

    except Exception as e:
        return "Error", 500

# -------- GET DATA --------
@app.route("/api/all")
def all_data():
    global view_mode

    try:
        with open(DATA_FILE, "r") as f:
            rows = list(csv.DictReader(f))

        if view_mode == "live":
            return jsonify(rows[-50:])
        else:
            return jsonify(rows)

    except:
        return jsonify([])

# -------- FULL VIEW --------
@app.route("/api/full")
def full_data():
    global view_mode
    view_mode = "full"
    return all_data()

# -------- RESET VIEW --------
@app.route("/api/reset")
def reset_view():
    global view_mode
    view_mode = "live"
    return "Reset Done"

# -------- DOWNLOAD --------
@app.route("/download")
def download():
    return send_file(DATA_FILE, as_attachment=True)

# -------- STATUS --------
@app.route("/status")
def status():
    if time.time() - last_seen < 15:
        return jsonify({"status": "Connected"})
    else:
        return jsonify({"status": "Disconnected"})

# -------- CONTROL --------
@app.route("/start")
def start():
    global collect_data
    collect_data = True
    return "Started"

@app.route("/stop")
def stop():
    global collect_data
    collect_data = False
    return "Stopped"

# -------- COMMAND SYSTEM --------
@app.route("/api/cmd")
def get_cmd():
    global latest_cmd
    cmd = latest_cmd
    latest_cmd = ""
    return cmd

# -------- QUERY --------
@app.route("/query")
def query():
    global latest_cmd

    cmd = request.args.get("cmd")

    try:
        if not cmd:
            return "No command"

        parts = cmd.strip().split()

        # DELETE SERVER DATA
        if parts[0].lower() == "delete" and len(parts) == 3:
            start = int(parts[1])
            end = int(parts[2])

            with open(DATA_FILE, "r") as f:
                rows = list(csv.DictReader(f))

            rows = [r for r in rows if not (start <= int(r["id"]) <= end)]

            with open(DATA_FILE, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["id","sensor1","sensor2","sensor3","time"])
                writer.writeheader()
                writer.writerows(rows)

            return "Deleted (Server)"

        # SEARCH
        elif parts[0].lower() == "search" and len(parts) == 3:
            start = int(parts[1])
            end = int(parts[2])

            with open(DATA_FILE, "r") as f:
                rows = list(csv.DictReader(f))

            result = [r for r in rows if start <= int(r["id"]) <= end]
            return jsonify(result)

        # SHOW ALL
        elif parts[0].lower() == "all":
            with open(DATA_FILE, "r") as f:
                return jsonify(list(csv.DictReader(f)))

        # CLEAR SD
        elif parts[0].lower() == "clear_sd":
            latest_cmd = "CLEAR_SD"
            return "SD Clear Command Sent"

        # SYNC SD
        elif parts[0].lower() == "sync_sd":
            latest_cmd = "SYNC"
            return "SD Sync Started"

        else:
            return "Unknown Command"

    except Exception as e:
        return "Error: " + str(e)

# -------- HOME --------
@app.route("/")
def home():
    return render_template("index.html")

# -------- RUN --------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
