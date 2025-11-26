# 🚀 GUÍA RÁPIDA - OTV v2 Wrapped Key

## ⚡ 5 Minutos para Empezar

### 1. Instalar Dependencias
```bash
cd /ruta/a/otv
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Certificados TLS (opcional pero recomendado)
```bash
# Instalar mkcert
brew install mkcert         # macOS
# o: choco install mkcert    # Windows

# Generar certificados
mkcert -install
mkcert localhost 127.0.0.1 ::1
```

### 3. Iniciar Backend (Terminal 1)
```bash
uvicorn api.main:app \
  --host 127.0.0.1 --port 8000 \
  --ssl-keyfile ./localhost+2-key.pem \
  --ssl-certfile ./localhost+2.pem
```

### 4. Iniciar Frontend (Terminal 2)
```bash
streamlit run app/Home.py
```

### 5. Abrir en Navegador
```
https://localhost:8501
```

---

## 📖 Uso Básico

### Escenario: Alice → Bob

#### Alice (Remitente)

1. **Generar claves para este dispositivo**
   - Click en "🔑 Generar par de claves"
   - ✅ Se generan: `publicKey_Alice` + `privateKey_Alice`
   - 📋 Copiar `publicKey_Alice`

2. **Recibir clave de Bob**
   - Bob generó: `publicKey_Bob`
   - Alice pega `publicKey_Bob` en el campo "PublicKey del receptor"

3. **Cifrar y enviar**
   - Escribir mensaje en el campo "Secreto"
   - Click "🔒 Cifrar y crear enlace"
   - ✅ Se genera URL: `https://localhost:8501/?id=ABC123`
   - 📋 Copiar URL y enviar a Bob

#### Bob (Receptor)

1. **Generar claves para este dispositivo**
   - En la sección "Leer Secreto"
   - Click "🔑 Generar nuevo par"
   - ✅ Se generan: `publicKey_Bob` + `privateKey_Bob`
   - 📋 Copiar `publicKey_Bob` y enviar a Alice

2. **Recibir enlace de Alice**
   - Alice envió: `https://localhost:8501/?id=ABC123`
   - Bob abre el enlace
   - ⚠️ O pega el enlace en "Leer manualmente"

3. **Descifrar**
   - Bob ingresa su `privateKey_Bob`
   - Click "📖 Leer secreto"
   - ✅ Mensaje se descifra localmente y se muestra

4. **Si Bob intenta leer de nuevo**
   - Error: **410 Gone** (mensaje ya fue quemado)

---

## 🔐 ¿Cómo Funciona la Seguridad?

### El Mensaje Está 3 Veces Protegido:

```
1️⃣ AES-GCM (Cliente → Servidor)
   plaintext --[AES-GCM 256]--> ciphertext
   
2️⃣ Wrapped Key (En el Servidor)
   AES_key --[crypto_box_seal(publicKey_Bob)]--> wrapped_key
   
3️⃣ One-Time Read (OTV)
   1ª lectura → OK
   2ª lectura → 410 Gone (destruido)
```

### ¿Qué Ve el Servidor?

```
Base de Datos:
- secret_id: "ABC123"
- ciphertext: "<cifrado>"
- wrapped_key: "<cifrado>"
- policy_json: "..."
- burned: false → true (después de leer)
- read_count: 0 → 1

❌ NUNCA ve:
- plaintext
- AES_key
- privateKey_Bob
```

---

## 🎯 Verificar que Funciona

### 1. Health Check
```bash
curl -k https://localhost:8000/health
# Response: {"ok": true, "time": "..."}
```

### 2. Ver Logs
En la UI, click en "🔗 Ver Audit Log"
```
[
  {"event_type": "genesis", ...},
  {"event_type": "create", "secret_id": "ABC123", ...},
  {"event_type": "read", "secret_id": "ABC123", ...}
]
```

### 3. Probar Base de Datos
```bash
sqlite3 otv.db "SELECT * FROM secrets LIMIT 1;"
```

---

## ⚠️ Problemas Comunes

### "Connection refused"
```
✓ Verifica que ambos servidores estén corriendo
✓ Backend en http://127.0.0.1:8000
✓ Frontend en http://localhost:8501
```

### "Failed to fetch" / CORS error
```
✓ Asegúrate de usar HTTPS consistently (o ambos HTTP en dev)
✓ Backend debe tener CORS abierto (ya está)
```

### "No se pudo abrir wrapped_key"
```
✓ Verifica que la privateKey es correcta
✓ Asegúrate de que es del par de claves correcto
✓ Prueba copiando de nuevo (sin espacios)
```

### "410 Gone"
```
✓ Este es el comportamiento esperado
✓ El secreto ya fue leído una vez (OTV)
✓ No se puede leer dos veces
```

---

## 📚 Documentación Completa

- **OTV_V2_README.md** - Documentación completa + API reference
- **WRAPPED_KEY_TECHNICAL.md** - Especificación técnica detallada
- **CHANGELOG.md** - Historial de cambios v2

---

## 🔧 Configuración Avanzada

### Cambiar TTL (Expiración)
En "TTL (segundos)", cambiar valor:
- 60 = 1 minuto
- 3600 = 1 hora (default)
- 86400 = 1 día
- 604800 = 1 semana

### Desactivar TLS (Development)
```bash
# Backend sin TLS:
uvicorn api.main:app --host 127.0.0.1 --port 8000

# Frontend: cambiar en Home.py:
API_BASE = "http://127.0.0.1:8000"
UI_ORIGIN = "http://localhost:8501"
```

### Ver Base de Datos
```bash
sqlite3 otv.db ".tables"        # Ver tablas
sqlite3 otv.db ".schema"        # Ver esquema
sqlite3 otv.db "SELECT * FROM secrets LIMIT 5;"  # Ver secretos
```

---

## 🌍 Compatibilidad

| Navegador | Soportado |
|-----------|-----------|
| Chrome/Edge 79+ | ✅ |
| Firefox 34+ | ✅ |
| Safari 11+ | ✅ |
| Opera 66+ | ✅ |
| IE 11 | ❌ |

---

## 🎓 Conceptos Clave

### Curve25519
- Algoritmo asimétrico moderno
- 256 bits de seguridad
- Más rápido que RSA

### AES-GCM
- Cifrado de bloques + autenticación
- 256 bits (muy seguro)
- Integrado en navegadores modernos

### WebCrypto
- API estándar en navegadores
- No requiere librerías externas (excepto Libsodium.js)

### Libsodium.js
- Binding de Libsodium para JavaScript
- Cargado desde CDN (https://unpkg.com)
- Proporciona funciones criptográficas

### One-Time Vault (OTV)
- Concepto: lectura única
- Implementación: flag `burned` + timestamp
- Garantía: 410 Gone en relectura

---

## 🚀 Próximas Mejoras

### v2.1
- [ ] Canary tokens (detectar espías)
- [ ] Rate-limiting

### v2.2
- [ ] Autenticación de remitente (Ed25519)
- [ ] Despliegue en producción

### v3.0
- [ ] PostgreSQL (escalabilidad)
- [ ] Hardening completo (CSP, HSTS)
- [ ] Auditoría de seguridad externa

---

## 📞 ¿Preguntas?

Ver documentación completa:
```bash
cat OTV_V2_README.md          # Guía de usuario completa
cat WRAPPED_KEY_TECHNICAL.md  # Especificación técnica
cat CHANGELOG.md              # Cambios realizados
```

---

**¡Listo! Ahora estás preparado para usar OTV v2 con Wrapped Keys. 🔐**
