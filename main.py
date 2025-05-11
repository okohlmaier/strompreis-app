from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import csv
import os
from datetime import datetime
import requests

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

DATA_FILE = "strompreise.csv"
API_URL = "https://apis.smartenergy.at/market/v1/price"

# Stelle sicher, dass die CSV-Datei existiert und eine Kopfzeile hat
def init_csv():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "value"])

# Hole aktuelle Daten von der smartENERGY API und speichere sie
@app.get("/fetch")
def fetch_and_store():
    response = requests.get(API_URL)
    data = response.json()["data"]
    init_csv()

    with open(DATA_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        for entry in data:
            timestamp = entry["date"]
            value = entry["value"]
            writer.writerow([timestamp, value])

    return {"status": "ok", "entries_saved": len(data)}

# GUI mit Diagramm und Tabelle
@app.get("/", response_class=HTMLResponse)
def show_prices():
    import pandas as pd
    import plotly.graph_objs as go
    from plotly.offline import plot

    init_csv()
    df = pd.read_csv(DATA_FILE, parse_dates=["timestamp"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["value"], mode='lines', name='Strompreis'))
    fig.update_layout(title="Strompreisverlauf", xaxis_title="Zeit", yaxis_title="Preis (ct/kWh)")

    chart_html = plot(fig, output_type='div', include_plotlyjs='cdn')

    table_html = df.tail(48).to_html(index=False)

    html_content = f"""
    <html>
        <head><title>Strompreise</title></head>
        <body>
            <h1>Aktuelle & Historische Strompreise</h1>
            {chart_html}
            <h2>Letzte 48 Einträge</h2>
            {table_html}
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
