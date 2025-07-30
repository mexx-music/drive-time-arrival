def calculate_route(coords):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    body = {"coordinates": coords, "instructions": False}
    
    try:
        res = requests.post(url, headers=headers, json=body, timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"❌ ORS Fehlercode {res.status_code}: {res.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Verbindung zu ORS fehlgeschlagen: {e}")
        return None
