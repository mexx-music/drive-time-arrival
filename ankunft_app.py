if st.button("📦 Route analysieren & ETA berechnen"):

    alle_orte = [startort] + zwischenstopps + [zielort]
    route_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": alle_orte[0],
        "destination": alle_orte[-1],
        "waypoints": "|".join(alle_orte[1:-1]) if len(alle_orte) > 2 else "",
        "key": GOOGLE_API_KEY
    }

    response = requests.get(route_url, params=params)
    data = response.json()

    if data["status"] != "OK":
        st.error("❌ Fehler bei der Routenberechnung.")
    else:
        legs = data["routes"][0]["legs"]
        gesamt_dauer_min = sum(leg["duration"]["value"] for leg in legs) // 60
        gesamt_distanz_km = sum(leg["distance"]["value"] for leg in legs) / 1000

        if gesamt_dauer_min == 0:
            gesamt_dauer_min = round(gesamt_distanz_km / geschwindigkeit * 60)

        rest = gesamt_dauer_min
        tag = 0
        ankunft = start_time
        verbleibende_10h = sum(zehner_fahrten)
        verbleibende_9h = sum(neuner_ruhen)

        while rest > 0:
            tag += 1
            heutige_lenkzeit = 540
            if verbleibende_10h > 0:
                heutige_lenkzeit = 600
                verbleibende_10h -= 1

            fahrzeit_heute = min(heutige_lenkzeit, rest)
            rest -= fahrzeit_heute

            if tag == 1 and tankpause:
                ankunft += timedelta(minutes=30)

            ankunft += timedelta(minutes=fahrzeit_heute)

            if rest <= 0:
                break

            ruhezeit = 660
            if verbleibende_9h > 0:
                ruhezeit = 540
                verbleibende_9h -= 1
            ankunft += timedelta(minutes=ruhezeit)

            if we_aktiv and ankunft >= we_beginn and ankunft < we_ende:
                ankunft += (we_ende - ankunft)

        st.success(f"🛣️ Strecke: {round(gesamt_distanz_km)} km")
        st.success(f"⏱️ Fahrzeit (Google): {gesamt_dauer_min} Minuten")
        st.success(f"📅 ETA (mit allen Regeln): **{ankunft.strftime('%A, %d.%m.%Y – %H:%M')} Uhr**")

        zeige_google_karte(alle_orte)
