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

app = Dash(__name__)

app.layout = html.Div([
    html.H2("Conexion base de datos", className="title"),  
    html.P(f"Total registros: {len(df)}", className="total"),
    html.Div(
        dash_table.DataTable(df.to_dict("records"), page_size=10), className="table-container"
    ),
])

if __name__ == "__main__":
    app.run(debug=True)