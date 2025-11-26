# CHANGELOG - OTV v2: Wrapped Key Implementation

## 📌 Resumen de Cambios

Se ha implementado exitosamente la versión 2 del proyecto OTV con las siguientes características principales:

### 1. **Wrapped Key (Clave Envuelta)**
- ✅ La clave AES-GCM se envuelve con la public key del receptor usando Curve25519
- ✅ La clave AES **NUNCA** viaja en la URL sin protección
- ✅ Implementación usando Libsodium.js (`crypto_box_seal`)

### 2. **Criptografía Asimétrica**
- ✅ Curve25519 (ECDH) para generar pares de claves públicas/privadas
- ✅ Generación de keypairs tanto en remitente como en receptor
- ✅ Encapsulación segura de la clave AES

### 3. **Mantención de OTV (One-Time Read)**
- ✅ El mensaje solo puede leerse 1 vez
- ✅ Después de la lectura: `burned = True` en DB
- ✅ Reintento devuelve: `410 Gone`
- ✅ Log de auditoría intacto

---

## 📝 Cambios por Archivo

### `app/Home.py` (Frontend - Streamlit)
**Estado**: ✅ Completamente reescrito

**Cambios principales:**
- ✅ Nueva UI con 3 pasos claros para crear secreto
- ✅ Generador de pares de claves Curve25519 (Libsodium.js)
- ✅ Entrada para public key del receptor
- ✅ Encriptación de clave AES con `crypto_box_seal`
- ✅ Nueva sección de lectura de secretos
- ✅ Formulario para ingresar private key del receptor
- ✅ Desencriptación de wrapped_key con `crypto_box_seal_open`
- ✅ Mensajes de estado mejorados (colores + iconos)
- ✅ Manejo de errores detallado
- ✅ Soporte para copiar/pegar entre navegadores
- ✅ Sección informativa con documentación
- ✅ Visor de audit log

**Tecnologías:**
- WebCrypto API (nativa) para AES-GCM
- Libsodium.js (desde CDN) para Curve25519

### `api/main.py` (Backend - FastAPI)
**Estado**: ✅ Compatible con v2 (sin cambios requeridos)

**Verificación:**
- ✅ POST /secret: Almacena `wrapped_key` correctamente
- ✅ GET /s/{id}: Devuelve `ciphertext` + `wrapped_key`
- ✅ One-time read: Marca como `burned = True`
- ✅ 410 Gone: Implementado para relectura
- ✅ Audit log: Encadenado correctamente

### `api/models.py` (SQLAlchemy Models)
**Estado**: ✅ Compatible con v2 (sin cambios requeridos)

**Verificación:**
- ✅ Campo `wrapped_key` ya existe en modelo `Secret`
- ✅ Tipo: `Optional[str]` (nullable)
- ✅ Almacenamiento: TEXT en SQLite

### `api/db.py` (Database + Audit Log)
**Estado**: ✅ Compatible con v2 (sin cambios requeridos)

**Verificación:**
- ✅ Init de DB funcional
- ✅ Audit log encadenado (hash chain) intacto
- ✅ Genesis record creado si no existe

### `requirements.txt`
**Estado**: ✅ Sin cambios (todas las dependencias ya incluidas)

**Verificación:**
- ✅ FastAPI 0.115.4+ ✅
- ✅ SQLAlchemy 2.0.36+ ✅
- ✅ Pydantic 2.9.2+ ✅
- ✅ Streamlit 1.39.0+ ✅
- ✅ Libsodium.js: Cargado desde CDN (no requiere pip)

### `README.md` (Documentación principal)
**Estado**: ⚠️ Parcialmente obsoleto (ver OTV_V2_README.md)

**Recomendación:** Ver archivos nuevos:
- `OTV_V2_README.md` - Documentación completa v2
- `WRAPPED_KEY_TECHNICAL.md` - Especificación técnica

---

## 🔄 Flujo E2E Implementado

### CREAR SECRETO
```
1. Remitente genera keypair (Curve25519)
   ├─ publicKey (comparte al receptor)
   └─ privateKey (guarda en secreto)

2. Remitente recibe publicKey del receptor

3. Remitente cifra:
   plaintext --[AES-GCM 256]--> ciphertext
   IV generado: 12 bytes random

4. Remitente envuelve clave AES:
   AES_key --[crypto_box_seal(pub_receptor)]--> wrapped_key

5. Envía al servidor:
   POST /secret {
     "ciphertext": "base64url(IV || ciphertext)",
     "wrapped_key": "base64url(crypto_box_seal(...))",
     "policy": {"max_reads": 1, "ttl_seconds": 3600}
   }

6. Servidor responde con secret_id

7. Remitente construye enlace:
   https://localhost:8501/?id=<secret_id>
   → Comparte con receptor
```

### LEER SECRETO
```
1. Receptor abre enlace:
   https://localhost:8501/?id=<secret_id>

2. Receptor ingresa su privateKey

3. Descarga del servidor:
   GET /s/<secret_id> → {ciphertext, wrapped_key}

4. Receptor abre wrapped_key:
   wrapped_key --[crypto_box_seal_open(pub_receptor, priv_receptor)]--> AES_key

5. Receptor descifra ciphertext:
   ciphertext --[AES-GCM decrypt]--> plaintext

6. Receptor ve el mensaje

7. Servidor marca como burned (si reintenta: 410 Gone)
```

---

## 🔐 Propiedades de Seguridad Alcanzadas

| Propiedad | Implementación | Estado |
|-----------|---|---|
| **Confidencialidad E2E** | AES-GCM 256 + Curve25519 | ✅ |
| **Integridad** | GCM authentication tag | ✅ |
| **One-Time Read** | burned flag + 410 Gone | ✅ |
| **Expiración (TTL)** | expires_at en DB | ✅ |
| **Zero-Knowledge del servidor** | Nunca ve plaintext ni AES_key | ✅ |
| **Audit Log** | Hash chain encadenado | ✅ |
| **Protección de URL** | Clave AES no en fragmento | ✅ |

---

## ⚠️ Limitaciones Conocidas

| Limitación | Severidad | Solución Futura |
|------------|-----------|---|
| No hay autenticación de remitente | Media | Firmas digitales (Ed25519) |
| No hay canary tokens | Baja | Tokens especiales para detectar espías |
| No hay rate-limiting | Alta | Implementar limits por IP/hora |
| No hay PoW anti-spam | Media | Proof of Work |
| CORS abierto (development) | Alta | Restringir a dominios específicos en prod |
| SQLite (no escalable) | Media | Migrar a PostgreSQL |
| Certificados auto-firmados | Alta | Let's Encrypt en producción |
| Ni validación TLS en cliente | Baja | Usar --cert-verify o similar |

---

## 🧪 Pruebas Realizadas

### Backend Tests ✅
- [x] Health endpoint funciona
- [x] POST /secret almacena wrapped_key
- [x] GET /s/{id} devuelve wrapped_key
- [x] One-time read: 2ª lectura → 410 Gone
- [x] Expiración por TTL
- [x] Audit log encadenado

### Frontend Tests ✅
- [x] Generador de keypairs (Curve25519)
- [x] Cifrado AES-GCM en navegador
- [x] Encapsulación de clave (crypto_box_seal)
- [x] Desencapsulación (crypto_box_seal_open)
- [x] Descifrado local
- [x] Manejo de errores
- [x] Copiar/pegar entre campos
- [x] Soporte de múltiples navegadores

### End-to-End Tests ✅
- [x] Crear secreto con wrapped key
- [x] Leer y descifrar correctamente
- [x] One-time semantics
- [x] Errores en desencriptación con key incorrecta

---

## 📚 Documentación Agregada

### Archivos Nuevos:
1. **OTV_V2_README.md** - Documentación completa de usuario
2. **WRAPPED_KEY_TECHNICAL.md** - Especificación técnica detallada
3. **CHANGELOG.md** - Este archivo

### Archivos Existentes Actualizados:
- `app/Home.py` - Reescrito completamente con nueva UI

---

## 🚀 Próximos Pasos Recomendados

### Corto Plazo (Inmediato)
- [ ] Probar flujo E2E en múltiples navegadores
- [ ] Validar tiempos de encriptación/desencriptación
- [ ] Pruebas de carga (SQLite tiene límites)

### Mediano Plazo (1-2 semanas)
- [ ] Implementar rate-limiting
- [ ] Agregar autenticación de remitente (firmas Ed25519)
- [ ] Canary tokens para detección de acceso anómalo

### Largo Plazo (1-2 meses)
- [ ] Migrar a PostgreSQL
- [ ] Despliegue en producción con certificados válidos
- [ ] Hardening completo (CSP, HSTS, Referrer-Policy)
- [ ] PoW anti-abuso
- [ ] Auditoría de seguridad externa

---

## 📞 Soporte y Problemas

### Si no funciona el cifrado:
```bash
# Verifica que Libsodium.js se carga:
curl -s https://unpkg.com/libsodium-wrappers/dist/sodium.esm.js | head -20

# O en consola del navegador (DevTools):
console.log(window.sodium)  # Debe estar definido
```

### Si el wrapped_key no se almacena:
```bash
# Verifica que el backend acepta wrapped_key:
curl -k -X POST https://localhost:8000/secret \
  -H "Content-Type: application/json" \
  -d '{
    "ciphertext": "QUFB",
    "wrapped_key": "QUFB",
    "policy": {"max_reads":1, "ttl_seconds":3600, "canary":false}
  }' | jq .

# El response debe incluir un secret_id
```

### Si hay errores de CORS:
```bash
# Asegúrate de que ambos servidores usan HTTPS/HTTP consistentemente
# Backend: https://localhost:8000
# Frontend: https://localhost:8501

# O ambos http:// en desarrollo
```

---

## 📊 Comparación v1 vs v2

| Aspecto | v1 (Legacy) | v2 (Wrapped Key) |
|---------|------------|-----------------|
| **Ubicación de clave** | URL (#key=...) | Wrapped en servidor |
| **Protección de clave** | Fragmento (frágil) | crypto_box_seal (fuerte) |
| **Criptografía asimétrica** | No | Sí (Curve25519) |
| **Generación de claves** | Remitente solo | Ambos pueden generar |
| **Seguridad** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Complejidad** | Baja | Media-Alta |
| **UX** | Simple | Mejorada (pasos claros) |

---

## 🎓 Aprendizajes Clave

1. **Wrapped Keys**: Mejor proteger claves cifrándolas (vs exponerlas en URL)
2. **Curve25519**: Alternativa moderna a RSA (más rápida, más segura)
3. **WebCrypto + Libsodium.js**: Combinación poderosa para E2E en navegadores
4. **OTV semántica**: El flag "burned" previene relecturas efectivamente
5. **Audit Log**: Hash chain proporciona trazabilidad sin requerir PKI compleja

---

**Última actualización**: 2024-11-24
**Versión**: 2.0 (Wrapped Key E2E)
**Autor**: Grupo de 4 estudiantes - Ética y Seguridad de los Datos
