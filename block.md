source venv_project_ethics/bin/activate
--deactivate


# Estructura del proyecto
project/
├─ app/                    # Streamlit (UI)
│  ├─ Home.py
│  └─ .streamlit/
│     └─ config.toml
├─ api/                    # FastAPI (backend mínimo)
│  ├─ main.py
│  ├─ db.py
│  └─ models.py
├─ requirements.txt
└─ README-LOCAL.md


# Requirements
fastapi==0.115.4
uvicorn[standard]==0.30.6
pydantic==2.9.2
sqlalchemy==2.0.36
python-multipart==0.0.9
streamlit==1.39.0
EOF


# Modelo de datos (base)
Usaremos SQLite 

Tabla secrets:
- id (string corto), ciphertext (texto base64url), policy_json (texto),
created_at (datetime UTC), expires_at (datetime UTC, opcional),
burned (bool), read_count (int).

Tabla audit_log (log encadenado):
- id (autoincrement), ts (datetime UTC), event_type (texto),
secret_id (texto, opcional), prev_hash (hex), hash (hex), meta_json (texto).


# TLS
Es nuestro "candado":
1.	Cifrado en tránsito (nadie pincha tu tráfico)
2.	Autenticación del servidor (el navegador valida el certificado contra una CA de confianza).

Usaremos mkcert (fácil) para generar un certificado válido para tu máquina.


# Run
Backend
- Raiz (terminal 1) -> levantar el backend (FastAPI) con TLS
uvicorn api.main:app \
  --host 127.0.0.1 --port 8000 \
  --ssl-keyfile ./localhost+2-key.pem \
  --ssl-certfile ./localhost+2.pem

Fronted
- Raiz (terminal 2) -> levantar Streamlit con TLS
streamlit run app/Home.py

