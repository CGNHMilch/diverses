from flask import Flask, request, jsonify, redirect
import docker
import threading
import time
import requests
import os # hinzugefügt

app = Flask(__name__)
client = docker.from_env()

# Timeout-Mappe zum Tracken der Aktivität
activity_tracker = {}
INACTIVITY_TIMEOUT = 180  # Sekunden

TRANSMISSION_URL = os.environ.get("TRANSMISSION_RPC_URL", "http://192.168.1.100:9091/transmission/rpc") # Transmission-URL aus Umgebungsvariable lesen

def is_transmission_downloading():
    try:
        # Transmission RPC requires a session ID. The first request without one will fail
        # but return the ID in the headers.
        r = requests.post(TRANSMISSION_URL)
        session_id = r.headers.get("X-Transmission-Session-Id")
        if not session_id:
             # If no session ID is returned, try again with a dummy one or handle error
             # For simplicity, let's assume the first request always returns the ID or fails clearly
             # A more robust approach would handle the 409 Conflict response specifically
             r = requests.post(TRANSMISSION_URL, headers={"X-Transmission-Session-Id": "dummy"})
             session_id = r.headers.get("X-Transmission-Session-Id")
             if not session_id:
                 raise Exception("Could not get Transmission session ID")

        payload = {
            "method": "torrent-get",
            "arguments": {"fields": ["status"]}
        }
        headers = {"X-Transmission-Session-Id": session_id}
        r = requests.post(TRANSMISSION_URL, json=payload, headers=headers)
        r.raise_for_status() # Raise an exception for bad status codes
        statuses = [t["status"] for t in r.json()["arguments"]["torrents"]]
        return 4 in statuses  # 4 = Download aktiv
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Transmission-Check fehlgeschlagen: {e}")
        # Im Zweifel lieber nicht stoppen
        return True
    except Exception as e:
        print(f"[ERROR] Unerwarteter Fehler beim Transmission-Check: {e}")
        return True


def inactivity_watcher(container_name):
    while True:
        last_active = activity_tracker.get(container_name, 0)
        # Check inactivity first
        if time.time() - last_active > INACTIVITY_TIMEOUT:
            # If inactive, check Transmission status
            if not is_transmission_downloading():
                # If inactive AND Transmission is NOT downloading, stop the container
                try:
                    container = client.containers.get(container_name)
                    if container.status == 'running':
                        container.stop()
                        print(f"[INFO] Container gestoppt aufgrund Inaktivität und keinem aktivem Download: {container_name}")
                except docker.errors.NotFound:
                    print(f"[WARN] Container nicht gefunden: {container_name}")
                # Break the loop as the container is stopped or not found
                break
            else:
                # If inactive BUT Transmission IS downloading, print info and continue watching
                print(f"[INFO] Aktiver Download erkannt, Container bleibt aktiv trotz Inaktivität: {container_name}")
        # Wait before the next check
        time.sleep(30)


@app.route('/wake/<container_name>')
def wake_container(container_name):
    try:
        container = client.containers.get(container_name)
        if container.status != 'running':
            container.start()
            print(f"[INFO] Container gestartet: {container_name}")
        else:
            print(f"[INFO] Container läuft bereits: {container_name}")

        # Aktivität tracken
        activity_tracker[container_name] = time.time()

        # Starte Watcher-Thread (einmalig pro Container)
        # Check if a thread with the same name is already running
        if not any(t.name == container_name and t.is_alive() for t in threading.enumerate()):
            print(f"[INFO] Starte Watcher-Thread für Container: {container_name}")
            t = threading.Thread(target=inactivity_watcher, args=(container_name,), name=container_name, daemon=True)
            t.start()
        else:
             print(f"[INFO] Watcher-Thread für Container {container_name} läuft bereits.")


        target_url = request.args.get('redirect')
        if target_url:
            return redirect(target_url)
        return jsonify({"status": "started", "container": container_name})

    except docker.errors.NotFound:
        return jsonify({"error": "Container nicht gefunden"}), 404
    except Exception as e:
        print(f"[ERROR] Fehler beim Starten/Aufwecken des Containers: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/transmission/log')
def transmission_log():
    try:
        # Transmission RPC requires a session ID. The first request without one will fail
        # but return the ID in the headers.
        r = requests.post(TRANSMISSION_URL)
        session_id = r.headers.get("X-Transmission-Session-Id")
        if not session_id:
             r = requests.post(TRANSMISSION_URL, headers={"X-Transmission-Session-Id": "dummy"})
             session_id = r.headers.get("X-Transmission-Session-Id")
             if not session_id:
                 raise Exception("Could not get Transmission session ID")

        payload = {
            "method": "torrent-get",
            "arguments": {"fields": ["id", "name", "status", "percentDone", "rateDownload", "rateUpload"]}
        }
        headers = {"X-Transmission-Session-Id": session_id}
        r = requests.post(TRANSMISSION_URL, json=payload, headers=headers)
        r.raise_for_status() # Raise an exception for bad status codes
        torrents = r.json()["arguments"]["torrents"]
        print("[TRANSMISSION STATUS]")
        for t in torrents:
            print(f"ID: {t['id']}, Name: {t['name']}, Status: {t['status']}, "
                  f"Fortschritt: {t['percentDone']*100:.1f}%, "
                  f"DL: {t['rateDownload']/1024:.1f} kB/s, UL: {t['rateUpload']/1024:.1f} kB/s")
        return jsonify({"status": "printed to log", "count": len(torrents)})
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Transmission-Status konnte nicht abgerufen werden: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"[ERROR] Unerwarteter Fehler beim Abrufen des Transmission-Status: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=881, debug=False) # Debug-Modus für Produktion deaktiviert
