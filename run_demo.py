import os
import sys
import http.server
import socketserver
import webbrowser
import subprocess

OUTPUT_DIR = "outputs"
DASHBOARD = os.path.join(OUTPUT_DIR, "fraud_radar_dashboard.html")

def run_script(script):
    print(f"Running {script}...")
    proc = subprocess.Popen([sys.executable, script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        print(line.rstrip())
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"{script} failed with exit code {proc.returncode}")

def serve_and_open():
    port = 8000
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}/{DASHBOARD.replace(os.sep, '/')}"
        print(f"Dashboard live at {url}")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.server_close()

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Step 1: Detect anomalies")
    run_script("detect.py")

    print("Step 2: Build dashboard")
    run_script("report.py")

    print("Step 3: Launch server")
    serve_and_open()

if __name__ == "__main__":
    main()