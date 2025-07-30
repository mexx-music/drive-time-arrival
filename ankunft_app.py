import streamlit as st
import requests

# API Keys
OPENCAGE_API_KEY = "0b4cb9e750d1457fbc16e72fa5fa1ca3"
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjA4MjNjY2EzNDM3YjRhMzhiZmYzNjNmODk0ZGRhNGI1IiwiaCI6Im11cm11cjY0In0=0"

def geocode_location(place):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={place}&key={OPENCAGE_API_KEY}&limit=1"
    res = requests.get(url)
    data = res.json()
    if data["results"]:
        coords = data["results"][0]["geometry"]
        return [coords["lng"], coords["lat"]]
    return None
