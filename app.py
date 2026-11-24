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
    "24h": ("24 hours", 1440, "30min"),  
}

refresh = {"10s": 10_000, "60s": 60_000}

all = "Todos"
with engine.connect() as c:
    service = [all] + [r[0] for r in c.execute(text("SELECT DISTINCT svc FROM logs ORDER BY 1"))]

def selector(label, child):
    return html.Div([html.Label(label), child], className="selector")

def kpi(id_, label):
    return html.Div ([html.Div(label, className="kpi-label"), 
                      html.Div(id=id_, className="kpi-value")], className="kpi")

app = Dash(__name__, title="logs")

app.layout = html.Div(
    [
        html.H2("Dashboard de logs", className="title"),
        html.Div(
            [
                selector( "Servicio", dcc.Dropdown(service, all, id="svc", clearable=False)),
                selector( "Ventana de tiempo", dcc.RadioItems(list(time), "1h", id="time", inline=True)),
                selector( "Refrescar cada", dcc.RadioItems(list(refresh), "10s", id="refresh", inline=True)),
            ],
            className="selectors",
        ),
        html.H3("KPIs", className="section"),
        html.Div(
            [
                kpi("avg", "Promedio response time (ms)"),
                kpi("p95", "P95 response time (ms)"),
                kpi("p99", "P99 response time (ms)"),
                kpi("rpm", "Throughput (logs/min)"),
                kpi("4xx", "Errores 4xx"),
                kpi("5xx", "Errores 5xx"),
            ],
            className="kpis",
        ),
        html.H3("Graficas", className="section"),
        dcc.Graph(id="prm-graph", className="graph"),
        dcc.Graph(id="errors-graph", className="graph"),
        dcc.Graph(id="rt-graph", className="graph"),

        dcc.Interval(id="interval", interval= 10_000),
    ],
    className="page",
)

def load(time_value, svc_value):
    sql = "SELECT ts, svc, status_code, duration FROM logs WHERE ts >= NOW() - cast(:w as interval)"
    valores = {"w": time[time_value][0]}
    if svc_value != all:
        sql += " AND svc = :s"
        valores["s"] = svc_value
    with engine.connect() as c:
        return pd.read_sql(text(sql), c, params=valores)

@app.callback(Output("interval", "interval"), Input("refresh", "value"))
def update_interval(value):
    return refresh[value]

@app.callback(
    Output("avg", "children"), Output("p95", "children"), Output("p99", "children"), Output("rpm", "children"),
    Output("4xx", "children"), Output("5xx", "children"), Output("prm-graph", "figure"), Output("errors-graph", "figure"),
    Output("rt-graph", "figure"),
    Input("time", "value"), Input("svc", "value"), Input("interval", "n_intervals")
)
def update_kpis(time_value, svc_value, _):
    # Implementation for updating KPIs
    df = load(time_value, svc_value)
    if df.empty:
        vacio = px.scatter(title="Sin datos en esta ventana")
        return "–", "–", "–", "0", "0", "0", vacio, vacio, vacio

    df["ts"] = df.ts.dt.tz_convert("America/Bogota")

    bucket = time[time_value][2]
    bucket_min = pd.Timedelta(bucket).total_seconds() / 60
    minutes = time[time_value][1]

    rpm = df.set_index("ts").resample(bucket).size() / bucket_min
    rpm = rpm.rename("rpm").reset_index()
    fig_rpm = px.line(rpm, x="ts", y="rpm", title="Throughput (logs/min)")
    end = pd.Timestamp.now(tz="America/Bogota")
    fig_rpm.update_xaxes(range=[end - pd.Timedelta(minutes=minutes), end])

    errs = df[df.status_code >= 400].copy()
    errs["tipo"] = errs.status_code.apply(lambda x: "4xx" if x < 500 else "5xx")
    errores = errs.set_index("ts").groupby("tipo").resample(bucket).size()
    errores = errores.rename("errores").reset_index()
    fig_errors = px.bar(errores, x="ts", y="errores", color="tipo", title="Errores 4xx y 5xx")
    fig_errors.update_xaxes(range=[end - pd.Timedelta(minutes=minutes), end])

    g = df.set_index("ts").resample(bucket).duration
    rt = pd.DataFrame({ "promedio": g.mean(), "p95": g.quantile(0.95), "p99": g.quantile(0.99)})
    rt = rt.reset_index().melt("ts", var_name="medida", value_name="ms")
    fig_rt = px.line(rt, x="ts", y="ms", color="medida", title="Response time (ms)")
    fig_rt.update_xaxes(range=[end - pd.Timedelta(minutes=minutes), end])

    return (
        f"{df.duration.mean():.0f}",                      
        f"{df.duration.quantile(0.95):.0f}",              
        f"{df.duration.quantile(0.99):.0f}",              
        f"{len(df) / minutes:.1f}",                       
        f"{df.status_code.between(400, 499).sum():,}",    
        f"{df.status_code.between(500, 599).sum():,}",
        fig_rpm,
        fig_errors,
        fig_rt,
    )    

if __name__ == "__main__":
    app.run(debug=True)
