# Documentación Técnica: Wrapped Key Implementation

## Resumen Ejecutivo

OTV v2 implementa **wrapped keys** para proteger la clave AES-GCM que cifra los mensajes. En lugar de enviar la clave en la URL o como plaintext, se envuelve (cifra) con la **public key** del receptor usando **Curve25519 + NaCl**.

---

## 1. ¿Por qué Wrapped Key?

### Problema en v1 (Legacy)
```
Flujo antiguo:
1. Remitente genera AES_key
2. Cifra: plaintext --[AES-GCM]--> ciphertext
3. Envía al servidor: ciphertext (seguro)
4. URL: https://localhost:8501/?id=ABC#key=BASE64URL_AES_KEY
   ⚠️ Problema: La clave AES está en el fragmento (#key=...)
   - Si se comparte por HTTP: visible en logs
   - Si se comparte por chat no cifrado: visible
   - Browser history: podría estar ahí
```

### Solución en v2 (Wrapped Key)
```
Flujo nuevo:
1. Remitente recibe publicKey_receptor
2. Remitente genera AES_key y IV
3. Cifra: plaintext --[AES-GCM]--> ciphertext
4. Envuelve AES_key: AES_key --[crypto_box_seal(pub_receptor)]--> wrapped_key
5. Envía al servidor: {ciphertext, wrapped_key}
6. URL: https://localhost:8501/?id=ABC
   ✅ Ventaja: La clave AES NO está en la URL
   ✅ La clave aún está protegida (wrapped_key) en el servidor
   ✅ Solo quien tiene private_receptor puede descifrarlo
```

---

## 2. Criptografía Utilizada

### 2.1 AES-GCM (para el mensaje)
- **Algoritmo**: AES-GCM 256 bits
- **IV**: 12 bytes (random, generado por cliente)
- **Implementación**: WebCrypto (nativa en navegador)
- **Ventajas**: Autenticada (tag de 128 bits), sin necesidad de MAC adicional

```javascript
// Cliente
const key = await crypto.subtle.generateKey(
  { name: "AES-GCM", length: 256 },
  true,
  ["encrypt", "decrypt"]
);
const iv = crypto.getRandomValues(new Uint8Array(12));
const ciphertext = await crypto.subtle.encrypt(
  { name: "AES-GCM", iv },
  key,
  plaintext
);
```

### 2.2 Curve25519 + NaCl Box (para la envoltura)
- **Algoritmo**: crypto_box (ECDH + ChaCha20-Poly1305)
- **Curva**: Curve25519 (256 bits)
- **Implementación**: Libsodium.js (Sodium.js)
- **Función**: `crypto_box_seal()` / `crypto_box_seal_open()`

```javascript
// Cliente (crear)
const pub_receptor = sodium.from_base64(pubKeyB64u, sodium.base64_variants.URLSAFE_NO_PADDING);
const wrapped_aes = sodium.crypto_box_seal(aes_raw_key, pub_receptor);

// Cliente (leer)
const pub_receptor = sodium.crypto_scalarmult_base(private_receptor);
const aes_raw_key = sodium.crypto_box_seal_open(wrapped_aes, pub_receptor, private_receptor);
```

---

## 3. Formato de Datos

### 3.1 Ciphertext (en base de datos)
```
ciphertext_b64u = base64url(IV || ciphertext_aes_gcm + tag)

Estructura binaria:
[IV (12 bytes) || ciphertext_aes_gcm || tag (16 bytes)]
Total: 12 + length(mensaje_cifrado) + 16 bytes
```

Ejemplo:
```
ciphertext (base64url): "rNfQtU0Tl5M-2g3W4rE5fQ8gHjKxPqLmNoRs..."
             ↓
        base64decode()
             ↓
[12 bytes IV][... ciphertext ...][16 bytes tag]
```

### 3.2 Wrapped Key (en base de datos)
```
wrapped_key_b64u = base64url(crypto_box_seal(aes_raw_key, pub_receptor))

Estructura:
Curve25519 ephemeral_public_key (32 bytes) || ciphertext || tag
= 32 + 16 + 32 = 80 bytes (aprox)
```

---

## 4. Flujo Completo: Paso a Paso

### 4.1 CREAR Secreto

#### Cliente (Remitente)
```javascript
// 1. Remitente genera claves (Curve25519)
const kp_remitente = sodium.crypto_box_keypair();
pub_remitente = sodium.to_base64(kp_remitente.publicKey, ...);
priv_remitente = sodium.to_base64(kp_remitente.privateKey, ...);

// 2. Receptor comparte su public key al remitente
pub_receptor = "<base64url public key del receptor>";

// 3. Remitente cifra el mensaje
const aes_key = await crypto.subtle.generateKey({name:"AES-GCM", length:256}, true, ["encrypt"]);
const aes_raw = new Uint8Array(await crypto.subtle.exportKey("raw", aes_key));
const iv = crypto.getRandomValues(new Uint8Array(12));
const msg_plaintext = "Mi secreto es...";
const msg_encrypted = await crypto.subtle.encrypt({name:"AES-GCM", iv}, aes_key, msg_plaintext);

// 4. Remitente envuelve la clave AES con la public key del receptor
const pub_receptor_raw = sodium.from_base64(pub_receptor, ...);
const aes_wrapped = sodium.crypto_box_seal(aes_raw, pub_receptor_raw);

// 5. Empacar: IV || ciphertext || tag
const packed = new Uint8Array(iv.length + msg_encrypted.length);
packed.set(iv, 0);
packed.set(new Uint8Array(msg_encrypted), iv.length);
const ciphertext_b64u = b64u(packed);
const wrapped_key_b64u = sodium.to_base64(aes_wrapped, ...);

// 6. Enviar al servidor
const resp = await fetch("https://localhost:8000/secret", {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({
    ciphertext: ciphertext_b64u,
    wrapped_key: wrapped_key_b64u,
    policy: {max_reads: 1, ttl_seconds: 3600}
  })
});
const result = await resp.json();
const secret_id = result.id;

// 7. Construir enlace
const link = `https://localhost:8501/?id=${secret_id}`;
```

#### Servidor (Backend)
```python
# api/main.py - POST /secret
@app.post("/secret", response_model=CreateSecretOut)
def create_secret(payload: CreateSecretIn):
    with SessionLocal() as db:
        secret_id = pysecrets.token_urlsafe(16)[:22]
        
        # Almacenar tal cual (NO descifrar)
        rec = Secret(
            id=secret_id,
            ciphertext=payload.ciphertext,        # ← base64url(IV || ciphertext)
            wrapped_key=payload.wrapped_key,      # ← base64url(crypto_box_seal(...))
            policy_json=payload.policy.model_dump_json(),
            created_at=now,
            expires_at=...,
            burned=False,
            read_count=0,
        )
        db.add(rec)
        db.commit()
        
        return {"id": secret_id}
```

### 4.2 LEER Secreto

#### Cliente (Receptor)
```javascript
// 1. Receptor abre el link
const url = new URL(window.location.href);
const secret_id = url.searchParams.get("id");

// 2. Receptor ingresa su private key
const priv_receptor_b64u = "<su private key generada>";
const priv_receptor = sodium.from_base64(priv_receptor_b64u, ...);

// 3. Calcular su public key (determinístico)
const pub_receptor = sodium.crypto_scalarmult_base(priv_receptor);

// 4. Descargar secreto del servidor
const resp = await fetch(`https://localhost:8000/s/${secret_id}`);
const data = await resp.json();
const ciphertext_b64u = data.ciphertext;       // IV || ciphertext
const wrapped_key_b64u = data.wrapped_key;     // crypto_box_seal(aes_key, ...)

// 5. Abrir el wrapped_key
const wrapped = sodium.from_base64(wrapped_key_b64u, ...);
const aes_raw = sodium.crypto_box_seal_open(wrapped, pub_receptor, priv_receptor);

// 6. Importar clave AES
const aes_key = await crypto.subtle.importKey("raw", aes_raw, "AES-GCM", false, ["decrypt"]);

// 7. Desempacar ciphertext
const packed = b64uToBytes(ciphertext_b64u);
const iv = packed.slice(0, 12);
const ct = packed.slice(12);

// 8. Descifrar
const plaintext_buf = await crypto.subtle.decrypt(
  {name:"AES-GCM", iv},
  aes_key,
  ct
);
const plaintext = new TextDecoder().decode(plaintext_buf);
```

#### Servidor (Backend)
```python
# api/main.py - GET /s/{secret_id}
@app.get("/s/{secret_id}", response_model=CipherOut)
def get_once(secret_id: str):
    with SessionLocal() as db:
        rec = db.execute(select(Secret).where(Secret.id == secret_id)).scalars().first()
        if not rec:
            raise HTTPException(status_code=404, detail="Not found")
        if rec.burned or _is_expired(rec):
            raise HTTPException(status_code=410, detail="Gone")
        
        # Devolver tal cual (NO descifrar)
        ct = rec.ciphertext        # ← enviado al cliente
        wrapped = rec.wrapped_key  # ← enviado al cliente
        
        # Marcar como burned (OTV: lectura única)
        rec.read_count += 1
        rec.burned = True
        db.commit()
        
        # Siguiente intento: 410 Gone
        return {"ciphertext": ct, "wrapped_key": wrapped}
```

---

## 5. Validación de Seguridad

### 5.1 Propiedades de Seguridad Alcanzadas

| Propiedad | Implementación |
|-----------|----------------|
| **Confidencialidad** | AES-GCM 256 bits (cliente) + Curve25519 (servidor) |
| **Integridad** | GCM authentication tag (16 bytes) |
| **Autenticidad (Forward Secrecy)** | Curve25519 ECDH ephemeral |
| **One-Time Read** | `burned` flag + `read_count` |
| **Expiración** | `expires_at` (TTL) |
| **Trazabilidad** | Audit log encadenado (hash chain) |
| **Zero Knowledge** | Servidor NUNCA ve plaintext ni clave AES |

### 5.2 Amenazas Prevenidas

```
Amenaza                          | Prevención
---------------------------------|------------------------------------------
Interceptación en URL            | Clave AES no va en URL (wrapped)
Lectura múltiple                 | burned flag + 410 Gone
Expiración                       | TTL + expires_at
Modificación de ciphertext       | GCM tag authentication
Suplantación de receptor         | Necesita private key para abrir
Compromiso de servidor           | Solo tiene ciphertext + wrapped_key
Replay attack                    | Hash chain + timestamp en log
Acceso a clave en plaintext      | Nunca almacenada sin wrap
```

### 5.3 Limitaciones / Pendientes

```
Limitación                       | Solución Futura
---------------------------------|------------------------------------------
No hay autenticación de remitente| Firmas digitales (Ed25519)
No hay canary tokens             | Tokens especiales para detectar espías
No hay rate-limiting             | Implementar limits por IP
No hay PoW                       | Proof of Work anti-spam
CORS abierto (dev)               | Restringir a dominios específicos
SQLite (no escalable)            | Migrar a PostgreSQL
Certificados auto-firmados       | Usar Let's Encrypt en producción
```

---

## 6. Compatibilidad y Dependencias

### 6.1 Backend (Python)
```
- FastAPI 0.115.4+         (API REST)
- SQLAlchemy 2.0.36+       (ORM)
- Pydantic 2.9.2+          (Validación)
- python-multipart 0.0.9   (Form parsing)
- (Criptografía: solo std lib + hashlib)
```

### 6.2 Frontend (JavaScript)
```
- WebCrypto (nativa en navegadores modernos)
- Libsodium.js (CDN: https://unpkg.com/libsodium-wrappers)
- Streamlit 1.39.0+ (UI)
- Requests (Python, para health check)
```

### 6.3 Compatibilidad de Navegadores

| Navegador | WebCrypto | Libsodium.js | Compatible |
|-----------|-----------|--------------|-----------|
| Chrome 37+ | ✅ | ✅ | ✅ |
| Firefox 34+ | ✅ | ✅ | ✅ |
| Safari 11+ | ✅ | ✅ | ✅ |
| Edge 79+ | ✅ | ✅ | ✅ |
| IE 11 | ❌ | ❌ | ❌ |

---

## 7. Performance y Escalabilidad

### 7.1 Tiempos de Cifrado (estimado)
```
Operación                        | Tiempo
---------------------------------|----------
Generar AES-GCM key              | ~1 ms
Cifrar 1 MB (AES-GCM)            | ~50 ms
Generar keypair (Curve25519)     | ~5 ms
crypto_box_seal (wrapping)       | ~2 ms
crypto_box_seal_open             | ~2 ms
```

### 7.2 Tamaño de Datos

```
Mensaje original: 1 KB

Después de AES-GCM:
- IV: 12 bytes
- Ciphertext: 1000 bytes
- Tag: 16 bytes
- Total: 1028 bytes
- Base64url: ~1371 bytes

Wrapped Key:
- Ephemeral public: 32 bytes
- Ciphertext (AES key): 32 bytes
- Tag: 16 bytes
- Total: ~80 bytes
- Base64url: ~107 bytes

Almacenamiento DB: ~1500 bytes por secreto
```

### 7.3 Escalabilidad (actual)

```
SQLite (actual):
- Máx concurrent readers: bajo
- Máx concurrent writers: 1
- Good for: <10k secretos/día

Mejoras futuras:
- PostgreSQL: 100+ concurrent connections
- Redis cache: para wrapped_keys frecuentes
- S3/Blob storage: para ciphertexts grandes
```

---

## 8. Testing

### 8.1 Unit Tests (sugeridos)

```python
# tests/test_wrapped_key.py
def test_create_secret_with_wrapped_key():
    """Verifica que wrapped_key se almacena correctamente"""
    payload = {
        "ciphertext": "test_ct",
        "wrapped_key": "test_wk",
        "policy": {"max_reads": 1, "ttl_seconds": 3600}
    }
    resp = client.post("/secret", json=payload)
    assert resp.status_code == 200
    secret_id = resp.json()["id"]
    
    # Verificar que se almacenó
    rec = db.execute(select(Secret).where(Secret.id == secret_id)).scalars().first()
    assert rec.wrapped_key == "test_wk"

def test_get_once_returns_wrapped_key():
    """Verifica que GET devuelve wrapped_key"""
    # Create secret
    secret_id = "test123"
    resp = client.get(f"/s/{secret_id}")
    data = resp.json()
    assert "wrapped_key" in data
    assert data["wrapped_key"] == "test_wk"

def test_one_time_read():
    """Verifica que segunda lectura devuelve 410"""
    resp1 = client.get(f"/s/{secret_id}")
    assert resp1.status_code == 200
    
    resp2 = client.get(f"/s/{secret_id}")
    assert resp2.status_code == 410
```

### 8.2 Integration Tests

```javascript
// tests/e2e.test.js
describe("E2E Wrapped Key Flow", () => {
  it("should encrypt, wrap, and decrypt correctly", async () => {
    // 1. Generate keys (Curve25519)
    const kp = sodium.crypto_box_keypair();
    
    // 2. Create secret with wrapped key
    // ...
    
    // 3. Read and decrypt
    // ...
    
    // 4. Verify plaintext matches
    expect(decrypted).toBe(original);
  });
});
```

---

## 9. Ejemplos de Uso

### 9.1 Crear Secreto (cURL)

```bash
# 1. Generar keypair en línea (usando Node.js)
node -e "
const sodium = require('libsodium.js');
const kp = sodium.crypto_box_keypair();
console.log('pub:', Buffer.from(kp.publicKey).toString('base64'));
console.log('priv:', Buffer.from(kp.privateKey).toString('base64'));
"

# 2. Crear secreto
curl -k -X POST https://localhost:8000/secret \
  -H "Content-Type: application/json" \
  -d '{
    "ciphertext": "<base64url cifrado>",
    "wrapped_key": "<base64url envuelto>",
    "policy": {"max_reads": 1, "ttl_seconds": 3600}
  }'
```

### 9.2 Leer Secreto (cURL)

```bash
curl -k https://localhost:8000/s/<secret_id> | jq .
```

---

## 10. Referencias

- **Curve25519**: https://en.wikipedia.org/wiki/Curve25519
- **Libsodium**: https://doc.libsodium.org/
- **WebCrypto**: https://developer.mozilla.org/en-US/docs/Web/API/Web_Crypto_API
- **AES-GCM**: https://en.wikipedia.org/wiki/Galois/Counter_Mode
- **RFC 7748**: Elliptic Curves for Security (Curve25519)
- **RFC 8439**: ChaCha20 and Poly1305

---

**Última actualización**: 2024-11-24
**Versión**: 2.0 Technical Spec
