# ... (alles wie bisher bis zur Wochenlenkzeit-Auswahl)

st.set_page_config(page_title="DriverRoute ETA – Wochenstunden", layout="centered")
st.title("🚛 DriverRoute ETA – mit Wochenlenkzeit (Stunden-Eingabe)")

# Wochenlenkzeit auswählen
st.markdown("### 🧭 Wochenlenkzeit festlegen")
vorgabe = st.radio("Wie viele Wochenlenkzeit stehen noch zur Verfügung?", ["Voll (56h)", "Manuell eingeben"], index=0)

if vorgabe == "Voll (56h)":
    verfügbare_woche = 3360  # 56h in Minuten
else:
    verfügbare_woche_stunden = st.number_input("⏱️ Eigene Eingabe (in Stunden)", min_value=0.0, max_value=56.0, value=36.0, step=0.25)
    verfügbare_woche = int(verfügbare_woche_stunden * 60)

# ... (ab hier einfach **deinen bisherigen Code unverändert weiterlaufen lassen**)

# Der Rest bleibt vollständig identisch – keine Anpassung mehr notwendig

# Die Berechnung am Ende bleibt wie bisher:
# verbleibend_min = max(0, verfügbare_woche - total_min)
# h, m = divmod(verbleibend_min, 60)
# st.info(f"🧭 Verbleibende Wochenlenkzeit: {h} h {m} min")

# Und die ETA bleibt:
# st.markdown(f"""
#     <h2 style='text-align: center; color: green;'>
#     ✅ <u>Geplante Ankunft:</u><br>
#     🕓 <b>{ende.strftime('%A, %d.%m.%Y – %H:%M')}</b><br>
#     ({local_tz.zone})
#     </h2>
# """, unsafe_allow_html=True)
