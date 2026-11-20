import os

import pandas as pd
import plotly.express as px
from dash import Dash, dash_table, Input, Output, dcc, html
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
url = os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://", 1)
engine = create_engine(url, pool_pre_ping=True)

with engine.connect() as c:
    df = pd.read_sql(text("SELECT * FROM logs ORDER BY ts DESC LIMIT 100"), c)

time = {
    "1h": ("1 hour", 60, "1min"),
    "3h": ("3 hours", 180, "3min"),
    "24h": ("12 hours", 1440, "30min"),  
}

refresh = {"10s": 10_000, "60s": 60_000}

all = "Todos"
with engine.connect() as c:
    service = [all] + [r[0] for r in c.execute(text("SELECT DISTINCT svc FROM logs ORDER BY 1"))]

def selector(label, child):
    return html.Div([html.Label(label), child], className="selector")

app = Dash(__name__, title="logs")

app.layout = html.Div(
    [
        html.H2("Logs"),
        html.Div(
            [
                selector( "Servicio", dcc.Dropdown(service, all, id="svc", clearable=False)),
                selector( "Ventana de tiempo", dcc.RadioItems(list(time), "1h", id="time", inline=True)),
                selector( "Refrescar cada", dcc.RadioItems(list(refresh), "10s", id="refresh", inline=True)),
            ],
            className="selectors",
        )
    ]
)
if __name__ == "__main__":
    app.run(debug=True)