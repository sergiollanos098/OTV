# OTV — One-Time Vault v2 (E2E Wrapped Key)

## ¿Qué es OTV?

**OTV (One-Time Vault)** es una aplicación para compartir secretos mediante enlaces de un solo uso con encriptación **end-to-end (E2E)**.

### Cambios en v2 (Wrapped Key)

1. **Wrapped Key (Clave Envuelta)**: La clave AES-GCM que cifra el mensaje ya no viaja en la URL sin protección. En su lugar, se **envuelve** con la **public key** del receptor usando Curve25519.

2. **Criptografía Asimétrica (Curve25519)**: 
   - El **remitente** proporciona la **public key** del receptor
   - La clave AES se cifra con esa public key (usando `crypto_box_seal`)
   - Solo quien tenga la **private key** correspondiente puede descifrarlo

3. **Semántica OTV intacta**: El mensaje solo se puede leer **UNA VEZ**. Después, el servidor lo marca como "burned" y devuelve **410 Gone**.

---

## 📊 Arquitectura v2

### Frontend (Streamlit + WebCrypto + Libsodium.js)
- **Crear**: Genera claves Curve25519, cifra con AES-GCM, envuelve la clave, envía al servidor
- **Leer**: Descarga el secreto, abre el wrapped_key con su private key, descifra localmente

### Backend (FastAPI + SQLite)
- **POST /secret**: Almacena `ciphertext` + `wrapped_key` (nunca ve la clave AES en plaintext)
- **GET /s/{id}**: Devuelve ciphertext + wrapped_key, marca como burned
- **DELETE /s/{id}**: Destruye inmediatamente
- **GET /log**: Audit log encadenado (hash-based chain)

---

## 🔐 Flujo Completo E2E

### CREAR (Remitente)
```
1. Remitente genera par de claves (publicKey_R, privateKey_R)
   → Comparte publicKey_R al receptor

2. Remitente cifra el mensaje:
   - Genera clave AES-GCM única + IV
   - plaintext --[AES-GCM]--> ciphertext
   
3. Remitente envuelve la clave AES:
   - AES_key --[crypto_box_seal(publicKey_R)]--> wrapped_key
   
4. Envía al servidor:
   POST /secret {
     "ciphertext": "<IV||ciphertext+tag en base64url>",
     "wrapped_key": "<AES_key cifrada en base64url>",
     "policy": { "max_reads": 1, "ttl_seconds": 3600 }
   }
   
5. Servidor responde con secret_id
   → Remitente construye enlace: https://localhost:8501/?id=<secret_id>
   → Remitente comparte enlace al receptor
```

### LEER (Receptor)
```
1. Receptor abre enlace: https://localhost:8501/?id=<secret_id>
   → Ingresa su privateKey_R en el formulario
   
2. Descarga el secreto:
   GET /s/<secret_id>
   → Servidor devuelve {ciphertext, wrapped_key} y marca como burned
   
3. Abre el wrapped_key con su private key:
   - wrapped_key --[crypto_box_seal_open(publicKey_R, privateKey_R)]--> AES_key
   
4. Descifra el ciphertext con la AES_key:
   - ciphertext --[AES-GCM decrypt]--> plaintext
   
5. Muestra el secreto al receptor
   
6. Si alguien intenta leer de nuevo:
   - Servidor responde 410 Gone (secreto ya fue quemado)
```

---

## 🛠️ Instalación y Ejecución

### Requisitos
- Python 3.10+
- `mkcert` para TLS local (opcional pero recomendado)

### 1. Setup
```bash
cd /ruta/a/otv
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. TLS Local (mkcert)
```bash
mkcert -install
mkcert localhost 127.0.0.1 ::1
# Genera: localhost+2.pem y localhost+2-key.pem
```

### 3. Backend
```bash
# Terminal 1:
uvicorn api.main:app \
  --host 127.0.0.1 --port 8000 \
  --ssl-keyfile ./localhost+2-key.pem \
  --ssl-certfile ./localhost+2.pem
```

### 4. Frontend
```bash
# Terminal 2:
streamlit run app/Home.py
```

Abre: **https://localhost:8501**

---

## 📋 Cómo Usar

### CREAR SECRETO (Remitente)
1. En la sección "📝 Crear Secreto", escribe tu mensaje
2. Presiona "🔑 Generar par de claves"
   - Se genera una pareja (publicKey + privateKey) para este dispositivo
   - **Guarda tu privateKey en lugar seguro** (la necesitarás para leer después si eres el receptor)
3. Comparte tu **publicKey** al receptor que cifrará el mensaje
4. Recibe la **publicKey** del receptor que cifrará para ti
5. Pega la publicKey del receptor en el campo
6. Presiona "🔒 Cifrar y crear enlace"
7. Copia el enlace generado y envíalo al receptor

### LEER SECRETO (Receptor)
1. Recibe el enlace: `https://localhost:8501/?id=<secret_id>`
2. En la sección "📖 Leer Secreto", tienes opciones:
   - **Opción A**: Pega el enlace en "Enlace del secreto" y presiona "📖 Leer secreto"
   - **Opción B**: O simplemente abre el enlace directamente en el navegador
3. Ingresa tu **privateKey** (la que generó el remitente)
4. El secreto se descifra localmente y se muestra
5. ⚠️ Si intentas leer de nuevo: **410 Gone** (ya fue quemado)

---

## 🔒 Detalles Técnicos de Seguridad

### Wrapped Key Mechanism
```
Sin wrapped key (antiguo):
- URL: https://localhost:8501/?id=ABC#key=BASE64URLAESKEY
- ⚠️ La clave AES viaja en el fragmento (mejor que nada, pero visible)
- ⚠️ Si se comparte por HTTP/no seguro: expuesta

Con wrapped key (v2):
- URL: https://localhost:8501/?id=ABC
- ✅ Clave AES se envuelve con publicKey del receptor
- ✅ Solo quien tenga privateKey puede abrirla
- ✅ Cifrado con Curve25519 (ECDH) + NaCl
```

### Cifrado E2E
- **Mensaje**: AES-GCM 256 bits (cliente → servidor → cliente)
- **Clave AES**: crypto_box_seal (Curve25519 + Poly1305)
- **Servidor**: NUNCA ve la clave AES en plaintext
- **Almacenamiento**: Solo ciphertext + wrapped_key

### One-Time Read (OTV)
```
POST /secret → secret_id = "ABC123"
GET /s/ABC123 (1ª lectura) → 200 OK + secreto
  └─ Servidor marca: burned = true, read_count = 1
GET /s/ABC123 (2ª lectura) → 410 Gone (error)
```

### Audit Log (Cadena Encadenada)
```
Cada evento (create, read, burn) genera:
- hash = SHA-256(prev_hash + JSON(evento))
- Cadena verificable externamente
- Ejemplo: Genesis → Create → Read → (Gone)
```

---

## 📁 Estructura del Proyecto

```
otv/
├─ app/
│  ├─ Home.py              # UI principal (Streamlit)
│  └─ .streamlit/
│     └─ config.toml       # Config TLS
├─ api/
│  ├─ main.py              # FastAPI endpoints + lógica OTV
│  ├─ db.py                # SQLite + audit log encadenado
│  └─ models.py            # SQLAlchemy models (Secret, AuditLog)
├─ requirements.txt        # Dependencias
├─ otv.db                  # SQLite (runtime)
├─ localhost+2.pem         # Cert TLS (mkcert)
├─ localhost+2-key.pem     # Key TLS (mkcert)
└─ README.md               # Este archivo
```

---

## 📚 API Reference

### POST /secret
Crear un nuevo secreto con wrapped key.

**Body:**
```json
{
  "ciphertext": "Base64url(IV || ciphertext+tag)",
  "wrapped_key": "Base64url(crypto_box_seal(AES_key, publicKey_receptor))",
  "policy": {
    "max_reads": 1,
    "ttl_seconds": 3600,
    "canary": false
  }
}
```

**Response (200):**
```json
{
  "id": "uW2z7RFcocsj..."
}
```

### GET /s/{secret_id}
Leer un secreto una sola vez.

**Response (200):**
```json
{
  "ciphertext": "Base64url(...)",
  "wrapped_key": "Base64url(...)"
}
```

**Response (410 Gone):**
```
El secreto ya fue leído una vez (OTV)
```

### DELETE /s/{secret_id}
Quemar/destruir un secreto inmediatamente.

**Response (200):**
```json
{
  "ok": true
}
```

### GET /log
Exportar audit log (cadena encadenada).

**Response (200):**
```json
[
  {
    "id": 1,
    "ts": "2024-11-24T...",
    "event_type": "genesis",
    "secret_id": null,
    "prev_hash": "0000...",
    "hash": "0000...",
    "meta": {}
  },
  {
    "id": 2,
    "ts": "2024-11-24T...",
    "event_type": "create",
    "secret_id": "uW2z7RFcocsj...",
    "prev_hash": "0000...",
    "hash": "abc123...",
    "meta": {"ttl_seconds": 3600, "max_reads": 1}
  },
  ...
]
```

### GET /health
Health check.

**Response (200):**
```json
{
  "ok": true,
  "time": "2024-11-24T..."
}
```

---

## ⚙️ Configuración

### Streamlit (`app/.streamlit/config.toml`)
```toml
[server]
port = 8501
address = "127.0.0.1"
enableCORS = false
enableXsrfProtection = true
sslCertFile = "../localhost+2.pem"
sslKeyFile = "../localhost+2-key.pem"
```

### FastAPI CORS
```python
# En api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Dev only, restringir en producción
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🧪 Pruebas Rápidas

### Health Check
```bash
curl -k https://localhost:8000/health
```

### Crear Secreto (curl)
```bash
curl -k -X POST https://localhost:8000/secret \
  -H "Content-Type: application/json" \
  -d '{
    "ciphertext": "QUFB",
    "wrapped_key": "QUFB",
    "policy": {"max_reads": 1, "ttl_seconds": 3600, "canary": false}
  }'
```

### Leer Secreto (curl)
```bash
curl -k https://localhost:8000/s/<secret_id>
```

### Ver Audit Log
```bash
curl -k https://localhost:8000/log | jq .
```

---

## ⚠️ Nota de Seguridad

Este es un **proyecto académico** (curso Ética y Seguridad de los Datos).

**Para producción:**
- ✅ Usa certificados TLS válidos (no auto-firmados)
- ✅ Restringe CORS a dominios específicos
- ✅ Implementa rate-limiting
- ✅ Agrega autenticación si es necesario
- ✅ Usa PostgreSQL o similar en lugar de SQLite
- ✅ Implementa PoW (Proof of Work) anti-spam
- ✅ Habilita CSP, HSTS, Referrer-Policy
- ✅ Realiza auditorías de seguridad externas

---

## 📅 Roadmap

- **v2 (Actual)**: Wrapped Key + E2E Completo + OTV
- **v2.1**: Verificador de audit log en UI
- **v2.2**: Canary tokens (detección de accesos anómalos)
- **v2.3**: Rate-limiting + PoW anti-abuso
- **v3**: Despliegue en producción con hardening completo

---

## 👥 Equipo

Proyecto de curso: Ética y Seguridad de los Datos (Grupo de 4 estudiantes)

---

## 📞 Soporte

Para problemas:
1. Verifica que ambos servidores (backend + frontend) estén corriendo
2. Asegúrate de usar HTTPS (no HTTP)
3. Revisa la consola del navegador (DevTools) para errores
4. Comprueba que TLS esté correctamente configurado

---

**Última actualización**: 2024-11-24
**Versión**: 2.0 (Wrapped Key E2E)
