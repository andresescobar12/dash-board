# Dashboard de logs

Dashboard en Dash (Python) sobre la tabla `logs` de PostgreSQL.

## Métricas

- Response time promedio
- Response time p95 y p99
- Throughput (RPM, requests por minuto)
- Conteo de errores 4xx y 5xx

Controles:
- **Servicio:** todos o uno solo.
- **Ventana de tiempo:** 1h, 3h o 24h.
- **Actualización automática:** cada 10s o cada 60s.

## Requisitos

- Python 3.10+
- Acceso a la base de datos PostgreSQL

## Cómo correrlo

1. Clona el repo y entra a la carpeta:
   ```bash
   git clone <url-del-repo>
   cd Dash_board
   ```
2. (Opcional) Crea un entorno virtual:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux / macOS
   source .venv/bin/activate
   ```
3. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Crea un archivo `.env` en la raíz del proyecto con el connection string de Postgres:
   ```
   DATABASE_URL=postgresql://usuario:clave@host:5432/base_de_datos
   ```
   El archivo `.env` está en `.gitignore`, así que no se sube al repositorio.
5. Ejecuta:
   ```bash
   python app.py
   ```
6. Abre http://127.0.0.1:8050

## Esquema de la tabla `logs`

| columna | tipo |
|---|---|
| id | bigint |
| ts | timestamp |
| ingested_at | timestamp |
| svc | varchar |
| url | varchar |
| http_method | varchar |
| status_code | integer |
| log | text |
| duration | integer (ms) |
