OTV — One-Time Vault (E2E, one-shot secrets)

Web app para compartir secretos mediante enlaces de un solo uso.
El secreto se cifra en el navegador con WebCrypto (AES-GCM 256); el servidor solo almacena el ciphertext y metadatos mínimos.
Incluye TLS local, semántica de una sola lectura y log de auditoría encadenado.

Proyecto de curso: Ética y Seguridad de los Datos · Grupo de 4 estudiantes · Semana 1 (Días 1–2 completados).

⸻

🧭 Estado del proyecto (hitos alcanzados)
	•	Día 1
	•	✅ Estructura del proyecto (UI + API) y DB SQLite
	•	✅ TLS local (mkcert) para API (FastAPI) y UI (Streamlit)
	•	✅ Endpoints: POST /secret, GET /s/{id} (one-shot), DELETE /s/{id}, GET /log, GET /health
	•	✅ Log de auditoría encadenado (hash(prev)+evento → hash), exportable via /log
	•	Día 2
	•	✅ Cifrado E2E real en el navegador con WebCrypto AES-GCM 256
	•	✅ Construcción de enlace ?id=<ID>#key=<BASE64URL>, donde #key no viaja al servidor
	•	✅ Lector que descifra localmente y respeta lectura única (410 Gone en reintento)

Próximos pasos sugeridos (Días 3–5): UX 404/410, borrado criptográfico extendido, verificador de cadena de log, canary tokens, CSP/HSTS/PoW/rate-limit.

⸻

🧱 Arquitectura (alto nivel)
	•	Frontend (UI) — Streamlit
	•	Presenta dos vistas: Crear secreto y Leer secreto
	•	Incrusta JS con st.components.v1.html para usar WebCrypto en el navegador
	•	Cifra localmente con AES-GCM 256 (clave e IV generados en el cliente)
	•	Construye la URL con ?id=... y #key=... (la clave se queda en el fragmento)
	•	Backend (API) — FastAPI
	•	Persistencia en SQLite (otv.db)
	•	Endpoints:
	•	POST /secret → guarda solo ciphertext y policy
	•	GET /s/{id} → devuelve el ciphertext si no fue leído/expirado y lo marca como quemado
	•	DELETE /s/{id} → “Destruir ahora” (marca burned)
	•	GET /log → exporta el audit log encadenado
	•	GET /health → ping
	•	Log encadenado: hash = SHA-256(prev_hash + JSON(evento))
	•	Seguridad (hasta ahora)
	•	TLS local (mkcert) para UI y API
	•	Cifrado E2E en cliente, clave nunca toca el servidor
	•	Semántica one-shot (segunda lectura → 410 Gone)

⸻

📁 Estructura de carpetas / archivos

otv/
├─ app/                        # Frontend (Streamlit)
│  ├─ Home.py                  # UI: crear/leer secreto; WebCrypto en JS embebido
│  └─ .streamlit/
│     └─ config.toml           # TLS para Streamlit (rutas a .pem)
├─ api/                        # Backend (FastAPI)
│  ├─ main.py                  # Endpoints REST + CORS + lógica one-shot
│  ├─ db.py                    # Motor SQLite, init y append del audit log encadenado
│  └─ models.py                # Modelos SQLAlchemy (Secret, AuditLog)
├─ requirements.txt            # Dependencias (FastAPI, Uvicorn, SQLAlchemy, Streamlit)
├─ otv.db                      # SQLite (se crea en runtime)
├─ localhost+2.pem             # Certificado TLS local (mkcert)        ← no commitear
├─ localhost+2-key.pem         # Clave privada TLS local (mkcert)      ← no commitear
└─ README.md                   # Este documento

¿Para qué sirve cada archivo?
	•	app/Home.py
UI de usuario. Inserta dos componentes HTML/JS:
	•	Crear: genera clave AES-GCM e IV, cifra el secreto, envía solo ciphertext a la API y muestra enlace ?id=...#key=....
	•	Leer: consume ?id y #key, trae el ciphertext una sola vez, descifra localmente y muestra el secreto.
	•	app/.streamlit/config.toml
Configura TLS en Streamlit (rutas a .pem generados con mkcert), CORS y puerto.
	•	api/models.py
Define tablas:
	•	secrets(id, ciphertext, policy_json, created_at, expires_at, burned, read_count)
	•	audit_log(id, ts, event_type, secret_id, prev_hash, hash, meta_json)
	•	api/db.py
Crea DB/tablas, registra un evento génesis si falta, y expone append_log() (encadenamiento hash).
	•	api/main.py
Servicio FastAPI, CORS, endpoints, y semántica “one-shot” (lee → quema).
	•	requirements.txt
Librerías del proyecto (instalar con pip install -r requirements.txt).

⸻

🔗 Flujo de datos (resumen E2E)
	1.	Crear
	•	Navegador: generateKey(AES-GCM 256) + IV(12B) → encrypt() → packed = IV || ciphertext+tag
	•	Envía a API: POST /secret { ciphertext: base64url(packed), policy }
	•	API guarda ciphertext y metadatos mínimos
	•	UI muestra: https://localhost:8501/?id=<ID>#key=<BASE64URLKEY>
	2.	Leer (una sola vez)
	•	Navegador con el enlace: extrae id y #key
	•	Pide GET /s/{id} → API devuelve ciphertext y marca como burned
	•	Navegador: importKey(raw) + decrypt(AES-GCM, iv) → muestra secreto
	•	Reintento: API responde 410 Gone
	3.	Log de transparencia
	•	Cada create/read/burn se registra como evento encadenado (prev_hash → hash)
	•	GET /log exporta la cadena (verificable externamente)

⸻

🛠️ Instalación y ejecución

0) Requisitos
	•	Python 3.10+
	•	mkcert (macOS: brew install mkcert y brew install nss si usas Firefox)

1) Clonar e instalar

cd /ruta/a/otv
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

2) TLS local (una vez)

mkcert -install
mkcert localhost 127.0.0.1 ::1
# genera: localhost+2.pem  y  localhost+2-key.pem  en la raíz del proyecto

3) Config UI (Streamlit)

app/.streamlit/config.toml (ya incluido):

[server]
port = 8501
address = "127.0.0.1"
enableCORS = false
enableXsrfProtection = true
sslCertFile = "../localhost+2.pem"
sslKeyFile  = "../localhost+2-key.pem"

Nota dev: En el backend, CORS está abierto (allow_origins=["*"]) para evitar bloqueos del iframe. Restringir en producción.

4) Arranque

Backend
Raíz (terminal 1):

uvicorn api.main:app \
  --host 127.0.0.1 --port 8000 \
  --ssl-keyfile ./localhost+2-key.pem \
  --ssl-certfile ./localhost+2.pem

Frontend
Raíz (terminal 2):

streamlit run app/Home.py

Abre la UI en: https://localhost:8501

Tip: prueba la API en https://localhost:8000/health y /docs.

⸻

🧪 Cómo interactuar / Probar

Crear secreto (E2E)
	1.	En la UI, sección “📝 Crear secreto (E2E en navegador)”.
	2.	Escribe tu secreto, elige TTL y pulsa “Cifrar y crear enlace”.
	3.	Se mostrará un enlace como:

https://localhost:8501/?id=<ID>#key=<BASE64URL>


	4.	Copia ese enlace y envíalo al destinatario.

Leer secreto (E2E)
	1.	El receptor abre el enlace (o lo pega en “Pegar enlace manualmente”).
	2.	Verá el secreto descifrado localmente.
	3.	Si recarga o reintenta con el mismo id, el backend devolverá 410 Gone.

Ver auditoría
	•	En la UI: “Ver audit log (/log)” (si lo agregas en la UI) o llama a GET /log.
	•	Verás eventos genesis, create, read, burn con cadena de hashes.

⸻

📜 API (resumen)
	•	GET /health → {"ok": true, "time": "..."}
	•	POST /secret
Body:

{
  "ciphertext": "BASE64URL(IV||ciphertext+tag)",
  "policy": {"max_reads": 1, "ttl_seconds": 3600, "canary": false}
}

Resp:

{"id": "uW2z7RFcocsj..."}


	•	GET /s/{id} → { "ciphertext": "..." } y marca como burned. Si ya fue leído/expirado: 410.
	•	DELETE /s/{id} → { "ok": true } (marca como burned).
	•	GET /log → lista de eventos encadenados.

⸻

🧩 Decisiones de diseño (por qué así)
	•	Streamlit + componente JS: te evita crear un frontend SPA completo, pero te permite ejecutar WebCrypto en el navegador (requisito del enunciado).
	•	FastAPI mínimo: endpoints simples, zero-knowledge (no ve la clave), y maneja la semántica de una sola lectura + log auditable.
	•	SQLite: baja fricción para ambiente académico; fácil de revisar y portar.
	•	TLS local (mkcert): necesario para habilitar WebCrypto y navegar en contexto seguro.

⸻

🧯 Problemas comunes (FAQ)
	•	https://localhost:8000/ → 404
Usa /health o /docs. La raíz no tiene ruta.
	•	UI dice “Failed to fetch” / “Load failed”
Normalmente es CORS en componentes embebidos (Origin: null). En dev dejamos:

allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]

Reinicia el backend y recarga la UI.

	•	Enlace sale null/?id=...
Dentro del iframe window.location.origin puede ser null.
Solución: usar UI_ORIGIN = "https://localhost:8501" para construir el enlace (ya aplicado).
	•	Conexión rechazada
Asegúrate de que uvicorn corre con TLS y que abres https://localhost:8000.
	•	Segundo intento de lectura devuelve 410
¡Está bien! Es la semántica de una sola lectura.

⸻

⚠️ Nota de seguridad (académico)
	•	Este MVP es solo para práctica. No es producción.
	•	verify=False en requests solo en local. En producción deberías usar un certificado válido y verify=True.
	•	CORS abierto (*) solo en desarrollo.
	•	El cifrado E2E real se hace con WebCrypto AES-GCM (cliente). No ciframos en el backend.

⸻

📌 Roadmap breve (siguientes días)
	•	Día 3: mejorar UX de errores (404/410), “borrado criptográfico” de claves envueltas (diseño simple)
	•	Día 4: verificador de cadena de auditoría en la UI + canary tokens (marcar apertura sospechosa)
	•	Día 5: Hardening (CSP estricta, HSTS, Referrer-Policy, PoW anti-abuso y rate-limit)
	•	Días 6–7: pruebas E2E, métricas sin PII, demo script, despliegue

⸻

🧪 Comandos útiles (debug)

Probar API por consola:

# Health (ignora validación de cert en curl)
curl -vk https://localhost:8000/health

# Crear secreto (ciphertext falso para test rápido)
curl -vk -X POST https://localhost:8000/secret \
  -H "Content-Type: application/json" \
  -d '{"ciphertext":"QUFB", "policy":{"max_reads":1,"ttl_seconds":3600,"canary":false}}'

# Leer una vez (reintentar → 410)
curl -vk https://localhost:8000/s/<ID>

# Burn inmediato
curl -vk -X DELETE https://localhost:8000/s/<ID>

# Exportar log
curl -vk https://localhost:8000/log