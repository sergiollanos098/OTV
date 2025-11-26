# 📋 Índice del Proyecto OTV v2

## Archivos Principales

### 🔧 Backend (API)
- **`api/main.py`** - Servidor FastAPI con endpoints REST
  - POST /secret - Crear secreto con wrapped key
  - GET /s/{id} - Obtener secreto (1 sola vez)
  - DELETE /s/{id} - Eliminar secreto
  - GET /log - Ver audit log

- **`api/models.py`** - Modelos SQLAlchemy
  - Secret: almacena ciphertext + wrapped_key
  - AuditLog: cadena de hash con eventos

- **`api/db.py`** - Base de datos e inicialización
  - SQLite local
  - Hash chain para auditoría

### 🎨 Frontend (UI)
- **`app/Home.py`** - Interfaz Streamlit (COMPLETAMENTE REESCRITA)
  - Sección: Crear Secreto (3 pasos)
  - Sección: Leer Secreto (desencapsulación)
  - Integración: Libsodium.js + WebCrypto
  - Manejo: errores robustos

### 📚 Documentación
1. **`PROJECT_SUMMARY.md`** ← COMIENZA AQUÍ (Este archivo)
   - Resumen ejecutivo de todo el proyecto
   - Estado de requisitos
   - Quick reference

2. **`QUICK_START.md`** ← SEGUNDO PASO
   - Guía de 5 minutos
   - Comandos para iniciar
   - Ejemplo de uso

3. **`OTV_V2_README.md`** ← REFERENCIA COMPLETA
   - Guía de usuario detallada
   - API reference con ejemplos
   - Arquitectura
   - Troubleshooting

4. **`WRAPPED_KEY_TECHNICAL.md`** ← DETALLES TÉCNICOS
   - Especificación criptográfica
   - Diagrama de flujo
   - Análisis de seguridad
   - Performance notes

5. **`CHANGELOG.md`**
   - Cambios v1 → v2
   - Feature matrix
   - Propiedades de seguridad

### 📦 Dependencias
- **`requirements.txt`** - Paquetes Python
  - fastapi==0.115.4
  - uvicorn[standard]==0.30.6
  - pydantic==2.9.2
  - sqlalchemy==2.0.36
  - python-multipart==0.0.9
  - streamlit==1.39.0

---

## 🚀 Flujo de Inicio Rápido

### Paso 1: Leer Documentación (5 min)
```
1. Abre: QUICK_START.md
2. Lee: Requisitos básicos + arquitectura
```

### Paso 2: Instalar & Configurar (5 min)
```powershell
cd c:\Users\PC-01\Desktop\OTV
python -m venv venv_project_ethics  # Si no existe
venv_project_ethics\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Paso 3: Iniciar Backend (terminal 1)
```powershell
uvicorn api.main:app --host 127.0.0.1 --port 8000 --ssl-keyfile ./localhost+2-key.pem --ssl-certfile ./localhost+2.pem
```
✅ Backend listo en: https://localhost:8000

### Paso 4: Iniciar Frontend (terminal 2)
```powershell
streamlit run app/Home.py
```
✅ Frontend listo en: https://localhost:8501

### Paso 5: Usar el Sistema
1. Acceder a https://localhost:8501
2. Generar keypair (Curve25519)
3. Crear secreto con mensaje
4. Compartir link + public key del remitter
5. Receptor: ingresar su private key
6. Leer mensaje (automáticamente se quema)

---

## 📊 Estado de Requisitos

| # | Requisito | Estado | Ubicación |
|---|-----------|--------|-----------|
| 1 | Wrapped key (no URL keys) | ✅ | app/Home.py (línea ~280) + api/main.py |
| 2 | Keypair generation (Curve25519) | ✅ | app/Home.py + Libsodium.js (CDN) |
| 3 | One-time read (OTV semantics) | ✅ | api/main.py (burned flag + 410 Gone) |

---

## 🔐 Mecanismo de Seguridad

```
CREAR SECRETO:
  plaintext 
    ↓ [AES-GCM 256]
  ciphertext + rawKey
    ↓ [Curve25519 crypto_box_seal]
  wrapped_key
    ↓ [POST a servidor]
  BASE DE DATOS: {ciphertext, wrapped_key, burned=False}

LEER SECRETO (PRIMERA VEZ):
  GET /s/{id} ← servidor retorna ciphertext + wrapped_key
  receptor tiene: priv_key + pub_remitter
    ↓ [crypto_box_seal_open]
  rawKey
    ↓ [AES-GCM decrypt]
  plaintext
  servidor marca: burned = True

LEER SECRETO (INTENTO 2+):
  GET /s/{id} ← servidor retorna 410 GONE
  ✗ no se puede leer
```

---

## 📁 Estructura de Directorios

```
c:\Users\PC-01\Desktop\OTV\
│
├── api/                          (Backend)
│   ├── main.py                   ← FastAPI + endpoints
│   ├── models.py                 ← SQLAlchemy models
│   ├── db.py                     ← SQLite + audit log
│   └── __pycache__/
│
├── app/                          (Frontend)
│   └── Home.py                   ← Streamlit UI (REWRITTEN)
│
├── venv_project_ethics/          (Virtual environment)
│   └── Lib/site-packages/        (Dependencies)
│
├── Documentación/
│   ├── PROJECT_SUMMARY.md        ← COMIENZA AQUÍ
│   ├── QUICK_START.md            ← Guía 5 min
│   ├── OTV_V2_README.md          ← Guía completa
│   ├── WRAPPED_KEY_TECHNICAL.md  ← Detalles técnicos
│   └── CHANGELOG.md              ← Cambios v1→v2
│
├── requirements.txt              ← Python dependencies
├── README.md                     ← Notas originales
└── block.md                      ← Notas de proyecto
```

---

## 🔧 Comandos Útiles

### Verificar instalación:
```bash
python --version                  # Debe ser 3.10+
pip show streamlit                # Debe mostrar versión
pip show fastapi                  # Debe mostrar versión
```

### Probar API backend:
```bash
curl -k https://localhost:8000/health
# ó
Invoke-WebRequest -Uri "https://localhost:8000/health" -SkipCertificateCheck
```

### Ver estado de base de datos:
```bash
sqlite3 secrets.db
SELECT COUNT(*) FROM secret;
SELECT * FROM audit_log ORDER BY ts DESC LIMIT 5;
```

### Generar certificados SSL (si falta):
```bash
# Instalar mkcert (si no tiene)
choco install mkcert              # ó descargar manualmente

# Crear certificados
mkcert localhost 127.0.0.1
# Genera: localhost+2.pem (cert) y localhost+2-key.pem (key)
```

---

## 🆘 Troubleshooting

### Problema: "Libsodium.js no carga"
**Solución**: Verificar conexión a internet (se carga desde CDN)
- URL: https://unpkg.com/libsodium-wrappers
- Alternativa: Descargar JS localmente si es necesario

### Problema: "SSL certificate error"
**Solución**: Generar certificados localhost
```bash
mkcert localhost 127.0.0.1
```

### Problema: "Puerto 8000/8501 en uso"
**Solución**: Cambiar puerto
```bash
uvicorn api.main:app --port 9000
streamlit run app/Home.py --server.port 9501
```

### Problema: "Database locked"
**Solución**: Reiniciar backend (SQLite en desarrollo)
```bash
# Detener backend
# Borrar secrets.db (opcional)
# Reiniciar backend
```

---

## 📞 Soporte Técnico

### Para preguntas sobre:
- **Criptografía**: Ver `WRAPPED_KEY_TECHNICAL.md`
- **API**: Ver `OTV_V2_README.md` → "API Reference"
- **Uso**: Ver `QUICK_START.md` → "Usage Examples"
- **Seguridad**: Ver `CHANGELOG.md` → "Security Properties"

### Archivos principales a revisar:
1. `PROJECT_SUMMARY.md` (general overview)
2. `QUICK_START.md` (getting started)
3. `OTV_V2_README.md` (complete reference)
4. `WRAPPED_KEY_TECHNICAL.md` (technical deep dive)

---

## ✅ Checklist de Implementación

- [x] Wrapped key mechanism (AES key no en URL)
- [x] Asymmetric keypair generation (Curve25519)
- [x] Key wrapping with crypto_box_seal
- [x] Key unwrapping with crypto_box_seal_open
- [x] One-time read semantics (burned flag)
- [x] 410 Gone on retry
- [x] Zero-knowledge backend
- [x] Audit log con hash chain
- [x] UI mejorada con 3 pasos
- [x] Error handling robusto
- [x] Documentación completa (4 docs)

---

**Estado Final: ✅ 100% COMPLETADO**

El proyecto está listo para:
- ✅ Testing end-to-end
- ✅ Despliegue en desarrollo
- ✅ Demostración a stakeholders
- ⏳ Producción (con hardening adicional)

**Próximo Paso**: Abre `QUICK_START.md` para comenzar en 5 minutos.

---

**Última actualización**: Proyecto completado y documentado
**Versión**: OTV v2.0 (Wrapped Key + Curve25519)
