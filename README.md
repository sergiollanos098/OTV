# 🔐 OTV — One-Time Vault (v2)

**Sistema de intercambio de secretos de un solo uso con cifrado E2E mediante Wrapped Keys.**

OTV permite compartir información sensible (contraseñas, claves API) asegurando que **solo el destinatario pueda leerla una única vez**. [cite_start]El servidor actúa como un almacén "Cero Conocimiento" (Zero-Knowledge): nunca ve el mensaje en texto plano ni la clave de cifrado[cite: 312].

---

## 🚀 Características Principales

* [cite_start]**Wrapped Key Architecture:** La clave de cifrado (AES) viaja encriptada ("envuelta") con la clave pública (RSA) del destinatario[cite: 314, 315].
* **Cifrado Híbrido E2E:**
    * [cite_start]**AES-GCM (256-bit):** Para cifrar el mensaje.
    * [cite_start]**RSA-OAEP (2048-bit):** Para intercambiar la clave AES de forma segura.
* [cite_start]**Semántica OTV (One-Time Vault):** El secreto se destruye automáticamente tras la primera lectura (el servidor responde `410 Gone` en intentos posteriores)[cite: 305, 362].
* [cite_start]**Auditoría:** Log encadenado (Hash Chain) que registra eventos (creación, lectura, borrado) sin revelar contenidos[cite: 299, 308].
* [cite_start]**Zero-Knowledge:** El servidor almacena `ciphertext` + `wrapped_key`, pero no tiene la llave privada para descifrarlos[cite: 316, 341].

---

## 🛠️ Arquitectura y Flujo

El proyecto consta de un backend en **FastAPI** (API REST) y un frontend en **Streamlit**. [cite_start]Todo el cifrado ocurre en el navegador del cliente usando **WebCrypto API**[cite: 6, 311].

### Flujo de Intercambio (Alice → Bob)

1.  **Bob (Receptor)** genera un par de claves RSA en su navegador. [cite_start]Se queda la `Private Key` y comparte la `Public Key` con Alice.
2.  **Alice (Remitente)** escribe el secreto:
    * El navegador genera una clave `AES` efímera y cifra el mensaje.
    * El navegador cifra ("envuelve") la clave `AES` usando la `Public Key` de Bob.
    * [cite_start]Envía al servidor: `Texto Cifrado` + `Clave Envuelta`[cite: 337, 340].
3.  [cite_start]**El Servidor** guarda los datos cifrados y genera un enlace único[cite: 303].
4.  **Bob** abre el enlace e introduce su `Private Key`:
    * [cite_start]Su navegador descifra la `Clave Envuelta` usando su `Private Key`[cite: 373].
    * [cite_start]Con la clave `AES` recuperada, descifra el mensaje[cite: 377].
5.  **Autodestrucción:** El servidor marca el secreto como "quemado" (`burned=True`). [cite_start]Nadie más puede leerlo[cite: 305].

---

## ⚙️ Instalación y Ejecución

### Requisitos previos
* [cite_start]Python 3.10+[cite: 41].
* [cite_start]**mkcert** (Necesario porque WebCrypto requiere contexto seguro HTTPS).

### 1. Configuración del entorno

```bash
# Clonar y entrar al directorio
git clone [https://github.com/sergiollanos098/OTV.git](https://github.com/sergiollanos098/OTV.git)
cd OTV

# Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
2. Generar certificados SSL localesPara que el cifrado funcione en localhost, necesitamos certificados válidos1:Bashmkcert -install
mkcert localhost 127.0.0.1 ::1
# Esto generará 'localhost+2.pem' y 'localhost+2-key.pem' en la raíz.
3. Ejecutar la aplicaciónNecesitarás dos terminales abiertas:Terminal 1: Backend (FastAPI)Bashuvicorn api.main:app --host 127.0.0.1 --port 8000 --ssl-keyfile ./localhost+2-key.pem --ssl-certfile ./localhost+2.pem
Terminal 2: Frontend (Streamlit)Bashstreamlit run app/Home.py
Accede a la aplicación en: https://localhost:85012.🧩 Estructura del ProyectoPlaintextotv/
├── api/
│   ├── main.py       # Endpoints (POST /secret, GET /s/{id})
│   ├── db.py         # Lógica SQLite y Hash Chain de auditoría
│   └── models.py     # Modelos SQLAlchemy (Secret, AuditLog)
├── app/
│   └── Home.py       # UI Streamlit + Lógica Criptográfica JS (WebCrypto)
├── otv.db            # Base de datos local (se crea automáticamente)
└── requirements.txt  # Dependencias
🔒 Detalles de Seguridad (Técnico)ComponenteTecnologíaPropósitoCifrado SimétricoAES-GCM 256Confidencialidad e integridad del mensaje3.Cifrado AsimétricoRSA-OAEP 2048 (SHA-256)Protección de la clave AES (Key Wrapping)4.AlmacenamientoSQLiteGuarda solo blobs cifrados (ciphertext, wrapped_key)5.TransporteTLS 1.2+HTTPS obligatorio para ejecutar WebCrypto6.⚠️ DisclaimerEste es un proyecto académico para el curso de Ética y Seguridad de los Datos. Aunque utiliza estándares criptográficos robustos, no debe utilizarse en entornos de producción críticos sin una auditoría de seguridad y configuraciones de infraestructura adicionales (HSTS, WAF, gestión de secretos en servidor, etc.)7.
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
