import sys
import time
import threading
import math
import keyboard # pip install keyboard
from adbutils import adb
import xml.etree.ElementTree as ET










# CONFIG
# ────────────────────────────────────────────────
def print_pokewalk_logo():
    ab = """  _____      _     __          __   _ _    
 |  __ \    | |    \ \        / /  | | |   
 | |__) |__ | | ____\ \  /\  / /_ _| | | __
 |  ___/ _ \| |/ / _ \ \/  \/ / _` | | |/ /
 | |  | (_) |   <  __/\  /\  / (_| | |   < 
 |_|   \___/|_|\_\___| \/  \/ \__,_|_|_|\_\
                                           
                                                                                                                                                                                                                                 """
    print(ab)
DEFAULT_SPEED_KMH = 5.0
UPDATE_INTERVAL = 0.25 # how often we update when holding key
STEP_METERS = 1.4 # realistic step size per update
current_lat = 37.7749
current_lon = -122.4194
current_speed_kmh = DEFAULT_SPEED_KMH
device = None

def connect():
    global device
    try:
        devs = adb.device_list()
        if devs:
            device = devs[0]
    except:
        pass

def send_teleport(lat, lon):
    if device is None:
        return
    try:
        cmd = f'am start-foreground-service -a theappninjas.gpsjoystick.TELEPORT --ef lat {lat:.7f} --ef lng {lon:.7f}'
        device.shell(cmd)
    except:
        pass

# For fake map display
def print_mini_map():
    print("\033[2J\033[H", end='') # clear screen + home (works on most terminals)
    print("PokeWalk Made by Chucny")
    print_pokewalk_logo()
    print(f"Lat: {current_lat:.7f} Lon: {current_lon:.7f} Speed: {current_speed_kmh:.1f} km/h")
    print("-" * (MAP_SIZE * 2 + 1))
    print("↑ ↓ ← → ")
    print("q / Ctrl+C = quit\n")
def walking_thread():
    global current_lat, current_lon
    while True:
        dx = dy = 0
        if keyboard.is_pressed('up'): dy = -1
        if keyboard.is_pressed('down'): dy = 1
        if keyboard.is_pressed('left'): dx = -1
        if keyboard.is_pressed('right'): dx = 1
        if keyboard.is_pressed('w'): dy = -2
        if keyboard.is_pressed('s'): dy = 2
        if keyboard.is_pressed('a'): dx = -2
        if keyboard.is_pressed('d'): dx = 2

        if dx != 0 or dy != 0:
            norm = math.hypot(dx, dy)
            if norm > 0:
                dx /= norm
                dy /= norm
            meters = current_speed_kmh / 3.6 * UPDATE_INTERVAL
            dlat = dy * (meters / 111320.0)
            dlon = dx * (meters / (111320.0 * math.cos(math.radians(current_lat))))
            current_lat += dlat
            current_lon += dlon
            send_teleport(current_lat, current_lon)
            print_mini_map()
        time.sleep(UPDATE_INTERVAL)
def main():
    global current_speed_kmh, current_lat, current_lon
    connect()
    send_teleport(current_lat, current_lon)
    print("PokeWalk – TEST MODE (no phone needed)")
    print("Arrow keys = walk, s 12.5 = set speed, paste coords + Enter = teleport\n")
    print_mini_map()
    threading.Thread(target=walking_thread, daemon=True).start()
    try:
        while True:
            line = input("> ").strip().lower()
            if not line:
                continue
            if line in ('q', 'quit', 'exit'):
                print("Bye!")
                break
            if line.startswith('s '):
                try:
                    speed_str = line[2:].strip()
                    new_speed = float(speed_str)
                    if new_speed < 0.1:
                        new_speed = 0.1
                    current_speed_kmh = new_speed
                    print(f"Speed set to {current_speed_kmh:.1f} km/h")
                    print_mini_map()
                except ValueError:
                    print("Usage: s 10.5")
                continue
            if line.startswith('gpx '):
                try:
                    path = line[4:].strip()
                    tree = ET.parse(path)
                    points = []
                    for trkpt in tree.findall(".//{*}trkpt"):
                        lat = float(trkpt.get("lat"))
                        lon = float(trkpt.get("lon"))
                        points.append((lat, lon))
                    if points:
                        def follow_gpx():
                            global current_lat, current_lon
                            for lat, lon in points:
                                if not keyboard.is_pressed('q'):
                                    current_lat = lat
                                    current_lon = lon
                                    send_teleport(current_lat, current_lon)
                                    print_mini_map()
                                    time.sleep(1)  # adjust timing as needed
                        threading.Thread(target=follow_gpx, daemon=True).start()
                except:
                    pass
                continue
            # Try coordinates
            try:
                cleaned = line.replace(',', ' ')
                parts = [float(x) for x in cleaned.split() if x]
                if len(parts) == 2:
                    current_lat = parts[0]
                    current_lon = parts[1]
                    send_teleport(current_lat, current_lon)
                    print_mini_map()
                else:
                    print("Need two numbers (lat lon)")
            except ValueError:
                print("Unknown command or bad coordinates")
    except KeyboardInterrupt:
        print("\nStopped.")
if __name__ == "__main__":
    try:
        import keyboard
    except ImportError:
        print("Please install:")
        print(" pip install keyboard")
        print("(run as admin/root if needed)")
        sys.exit(1)
    main()
