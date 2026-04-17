from flask import Flask, render_template, jsonify, session
import random
import json

from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this'

def load_addresses_from_json(filename):
    """Lädt Adressen aus Overpass JSON-Datei"""
    addresses = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        for element in data.get('elements', []):

            tags = element.get('tags', {})

            lat = element.get('lat')
            lon = element.get('lon')

            # ❌ skip wenn keine Koordinaten
            if lat is None or lon is None:
                continue

            if 'addr:street' in tags:

                street = tags.get('addr:street', '')
                housenumber = tags.get('addr:housenumber', '')
                name = tags.get('name', '')

                full_address = f"{street} {housenumber}".strip()

                if name and name not in full_address:
                    full_address += f" - {name}"

                addresses.append({
                    "name": full_address,
                    "lat": lat,
                    "lon": lon,
                    "street": street,
                    "housenumber": housenumber
                })
        
        print(f"✅ {len(addresses)} Adressen geladen")
        return addresses
        
    except FileNotFoundError:
        print(f"❌ Datei {filename} nicht gefunden!")
        return []
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return []

# Laden Sie Ihre JSON-Datei
addresses = load_addresses_from_json("export.json")


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/new_game")
def new_game():
    """Startet ein neues Spiel mit einer zufälligen Adresse"""
    if not addresses:
        return jsonify({"error": "Keine Adressen verfügbar"})
    
    target = random.choice(addresses)
    
    # Speichere in Session
    session['target'] = target
    session['timestamp'] = datetime.now().isoformat()
    
    return jsonify({
        "target_name": target['name'],
        "target_lat": target['lat'],
        "target_lon": target['lon']
    })

@app.route("/check_guess", methods=['POST'])
def check_guess():
    """Überprüft den Tipp des Spielers"""
    from flask import request
    
    if 'target' not in session:
        return jsonify({"error": "Kein aktives Spiel"}), 400
    
    data = request.json
    guessed_lat = data.get('lat')
    guessed_lon = data.get('lon')
    
    target = session['target']
    
    # Berechne Distanz in Metern (Haversine Formel)
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000  # Erdradius in Meter
    
    lat1 = radians(target['lat'])
    lon1 = radians(target['lon'])
    lat2 = radians(guessed_lat)
    lon2 = radians(guessed_lon)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return jsonify({
        "correct_lat": target['lat'],
        "correct_lon": target['lon'],
        "distance": round(distance),
        "correct_name": target['name']
    })

if __name__ == "__main__":
    print(f"\n🎮 GeoGuessr-Spiel gestartet mit {len(addresses)} Adressen")
    app.run(debug=True)