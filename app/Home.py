
# app/Home.py 
import streamlit as st
import requests
import os # Importamos la librería os para manejar rutas si es necesario

st.set_page_config(page_title="OTV (One-Time Vault)", page_icon="🔐", layout="centered")
st.title("🔐 One-Time Vault (OTV) v2 — E2E Wrapped Key")

# === Ajustes locales ===
API_BASE  = "https://127.0.0.1:8000"
UI_ORIGIN = "https://localhost:8501"

# === RUTA DEL CERTIFICADO RAIZ DE MKCERT ===
CA_CERT_PATH = r"C:\Users\PC-01\AppData\Local\mkcert\rootCA.pem"

st.caption("✨ Encriptación E2E con wrapped keys (RSA-OAEP + AES-GCM). El servidor nunca ve la clave. Lectura de una sola vez (OTV).")

# ---- /health ----
with st.expander("🏥 Probar conexión con API (/health)", expanded=False):
    if st.button("Verificar /health"):
        try:
            # TEMPORAL: Ignora verificación SSL mientras configuras mkcert
            r = requests.get(f"{API_BASE}/health", timeout=2, verify=False)
            st.success(f"✅ API respondiendo: {r.json()}")
        except Exception as e:
            st.error(f"❌ Error de conexión: {e}")

st.divider()

# ====================================================================
# ======================= CREAR SECRETO ===============================
# ====================================================================

st.header("📝 Crear Secreto (Remitente)")

create_html = f"""
<div style="font-family: system-ui, sans-serif; max-width: 900px;">

  <div style="background:#e3f2fd;padding:12px;border-radius:5px;margin-bottom:12px;border-left:4px solid #1976D2;">
    <strong>📝 Paso 1: Prepara tu mensaje</strong>
  </div>

  <label style="font-weight:600;">Secreto (se cifrará localmente en tu navegador):</label>
  <textarea id="plain" rows="5" style="width:100%;padding:10px;margin:8px 0;border:1px solid #bbb;border-radius:4px;font-family:monospace;"></textarea>

  <div style="display:flex;gap:12px;align-items:center;margin:12px 0;">
    <label style="font-weight:600;">⏱️ TTL (segundos):</label>
    <input id="ttl" type="number" min="60" max="{7*24*3600}" step="60" value="3600" style="width:140px;padding:8px;border:1px solid #bbb;border-radius:4px;">
    <span style="color:#666;font-size:0.9em;">(1 hora = 3600, 1 día = 86400)</span>
  </div>

  <div style="background:#f3e5f5;padding:12px;border-radius:5px;margin:12px 0;border-left:4px solid #7b1fa2;">
    <strong>🔐 Paso 2: Usa wrapped key para E2E SEGURO</strong>
  </div>

  <p style="font-size:0.95em;color:#333;line-height:1.6;margin:8px 0;">
    La clave AES (que cifra tu mensaje) se <strong>envuelve</strong> con la <strong>public key RSA</strong> del receptor (RSA-OAEP SHA-256).
    <br>
    Solo quien tenga la <strong>private key</strong> correspondiente podrá descifrarlo.
    <br>
    El servidor NUNCA ve ni almacena la clave AES en texto plano.
  </p>

  <label style="font-weight:600;">🔑 PublicKey del receptor (RSA SPKI base64url):</label>
  <input id="recipientPub" placeholder="Pegar public key del receptor aquí o usar el botón de generar abajo" style="width:100%;padding:10px;margin:8px 0;border:1px solid #bbb;border-radius:4px;font-family:monospace;font-size:0.85em;">

  <div style="display:flex;gap:8px;align-items:center;margin-top:10px;flex-wrap:wrap;">
    <button id="genKeyBtn" style="padding:10px 14px;cursor:pointer;background:#7b1fa2;color:white;border:none;border-radius:4px;font-weight:600;">🔑 Generar par de claves</button>
    <button id="pastePubBtn" style="padding:10px 14px;cursor:pointer;background:#1976D2;color:white;border:none;border-radius:4px;font-weight:600;">📋 Pegar PublicKey</button>
  </div>

  <div id="genBox" style="display:none;margin-top:12px;border-left:4px solid #4CAF50;padding:12px;background:#f1f8e9;border-radius:4px;">

    <div style="font-weight:600;color:#2e7d32;margin-bottom:10px;font-size:1.05em;">✅ Claves generadas (para este dispositivo/sesión):</div>
    
    <div style="margin-bottom:12px;">
      <label style="font-weight:600;color:#2e7d32;">Public Key (comparte esto al remitente):</label>
      <textarea id="genPub" readonly style="width:100%;padding:10px;margin:6px 0;background:#fff;border:1px solid #aed581;border-radius:4px;font-family:monospace;font-size:0.85em;height:60px;"></textarea>
      <button id="copyGenPub" style="padding:8px 12px;cursor:pointer;background:#4CAF50;color:white;border:none;border-radius:4px;">📋 Copiar PublicKey</button>
    </div>

    <div>
      <label style="font-weight:600;color:#c62828;">Private Key (guarda en SECRETO - no compartas):</label>
      <textarea id="genPriv" readonly style="width:100%;padding:10px;margin:6px 0;background:#fff;border:1px solid #ef5350;border-radius:4px;font-family:monospace;font-size:0.85em;height:60px;"></textarea>
      <button id="copyGenPriv" style="padding:8px 12px;cursor:pointer;background:#c62828;color:white;border:none;border-radius:4px;">📋 Copiar PrivateKey</button>
    </div>

    <p style="margin-top:10px;color:#c62828;font-size:0.9em;">
      ⚠️ <strong>Importante:</strong> Guarda tu Private Key en un lugar seguro. La necesitarás para descifrarlo después.
    </p>
  </div>

  <div style="background:#fff3e0;padding:12px;border-radius:5px;margin:12px 0;border-left:4px solid #f57c00;">
    <strong>✉️ Paso 3: Cifrar y crear enlace</strong>
  </div>

  <button id="createBtn" style="padding:12px 18px;cursor:pointer;background:#f57c00;color:white;border:none;border-radius:4px;font-weight:600;font-size:1.05em;">🔒 Cifrar y crear enlace</button>

  <div id="msg" style="margin-top:10px;color:#444;font-weight:500;"></div>

  <div id="linkBox" style="display:none;margin-top:12px;border:2px solid #4CAF50;padding:12px;background:#f1f8e9;border-radius:4px;">
    <div style="font-weight:600;color:#2e7d32;font-size:1.05em;margin-bottom:8px;">✅ Enlace listo para compartir (ONE-TIME READ):</div>
    <textarea id="result" style="width:100%;padding:10px;margin:8px 0;border:1px solid #4CAF50;border-radius:4px;font-family:monospace;font-size:0.85em;height:50px;" readonly></textarea>
    <button id="copyBtn" style="padding:8px 12px;cursor:pointer;background:#2196F3;color:white;border:none;border-radius:4px;font-weight:600;">📋 Copiar enlace</button>
    <p style="margin-top:8px;color:#2e7d32;font-size:0.9em;">
      ✨ El receptor solo podrá leer este secreto UNA VEZ. Después será destruido automáticamente.
    </p>
  </div>
</div>

<script>
const API_BASE = "{API_BASE}";
const UI_ORIGIN = "{UI_ORIGIN}";
const TTL_MAX = {7*24*3600};
const textEncoder = new TextEncoder();

function b64uToBytes(str) {{
  str = str.replace(/-/g, '+').replace(/_/g, '/');
  while (str.length % 4) str += '=';
  const bin = atob(str);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}}

function bytesToB64u(bytes) {{
  let bin = '';
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}}

async function generateRsaKeyPairEncoded() {{
  const kp = await crypto.subtle.generateKey(
    {{
      name: 'RSA-OAEP',
      modulusLength: 2048,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: 'SHA-256'
    }},
    true,
    ['encrypt', 'decrypt']
  );
  const spki = new Uint8Array(await crypto.subtle.exportKey('spki', kp.publicKey));
  const pkcs8 = new Uint8Array(await crypto.subtle.exportKey('pkcs8', kp.privateKey));
  return {{
    kp,
    pubB64u: bytesToB64u(spki),
    privB64u: bytesToB64u(pkcs8)
  }};
}}

async function handleCreateSecret() {{
  const msg = document.getElementById('msg');
  const linkBox = document.getElementById('linkBox');
  msg.style.color = '#1976D2';
  msg.textContent = '⏳ Preparando cifrado...';
  linkBox.style.display = 'none';

  try {{
    const plain = document.getElementById('plain').value;
    const ttl = Number(document.getElementById('ttl').value);
    const pubInput = document.getElementById('recipientPub').value.trim();

    if (!plain.trim()) {{
      throw new Error('Ingresa un secreto para cifrar.');
    }}
    if (!pubInput) {{
      throw new Error('Ingresa la public key RSA del receptor.');
    }}
    if (!ttl || ttl < 60 || ttl > TTL_MAX) {{
      throw new Error(`TTL inválido. Debe estar entre 60 y ${{TTL_MAX}} segundos.`);
    }}

    let rsaPub;
    try {{
      const decodedPub = b64uToBytes(pubInput);
      rsaPub = await crypto.subtle.importKey(
        'spki',
        decodedPub.buffer,
        {{ name: 'RSA-OAEP', hash: 'SHA-256' }},
        false,
        ['encrypt']
      );
    }} catch (err) {{
      throw new Error('Public key inválida (esperaba RSA SPKI base64url).');
    }}

    const aesKey = await crypto.subtle.generateKey(
      {{ name: 'AES-GCM', length: 256 }},
      true,
      ['encrypt', 'decrypt']
    );
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const cipherBuf = await crypto.subtle.encrypt(
      {{ name: 'AES-GCM', iv }},
      aesKey,
      textEncoder.encode(plain)
    );
    const cipherBytes = new Uint8Array(cipherBuf);
    const packed = new Uint8Array(iv.byteLength + cipherBytes.byteLength);
    packed.set(iv);
    packed.set(cipherBytes, iv.byteLength);
    const ciphertextB64u = bytesToB64u(packed);

    const aesRaw = new Uint8Array(await crypto.subtle.exportKey('raw', aesKey));
    const wrappedBytes = new Uint8Array(
      await crypto.subtle.encrypt({{ name: 'RSA-OAEP' }}, rsaPub, aesRaw)
    );
    const wrappedB64u = bytesToB64u(wrappedBytes);

    const payload = {{
      ciphertext: ciphertextB64u,
      wrapped_key: wrappedB64u,
      policy: {{
        max_reads: 1,
        ttl_seconds: ttl,
        canary: false
      }}
    }};

    const resp = await fetch(API_BASE + '/secret', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify(payload)
    }});

    if (!resp.ok) {{
      const errText = await resp.text();
      throw new Error(`Error del servidor (${{resp.status}}): ${{errText}}`);
    }}

    const data = await resp.json();
    const shareLink = UI_ORIGIN + '?id=' + encodeURIComponent(data.id);
    document.getElementById('result').value = shareLink;
    linkBox.style.display = 'block';
    msg.style.color = 'green';
    msg.textContent = '✅ Secreto cifrado y almacenado. Comparte el enlace.';
  }} catch (err) {{
    msg.style.color = 'crimson';
    msg.textContent = '❌ ' + err.message;
  }}
}}

document.getElementById('createBtn').addEventListener('click', handleCreateSecret);

document.getElementById('genKeyBtn').addEventListener('click', async () => {{
  const msg = document.getElementById('msg');
  try {{
    msg.style.color = '#1976D2';
    msg.textContent = '⏳ Generando claves RSA (2048 bits)...';
    const {{ pubB64u, privB64u }} = await generateRsaKeyPairEncoded();
    document.getElementById('genPub').value = pubB64u;
    document.getElementById('genPriv').value = privB64u;
    document.getElementById('genBox').style.display = 'block';
    msg.style.color = '#2196F3';
    msg.textContent = '✓ Claves listas. Comparte la public key con el remitente.';
  }} catch (err) {{
    msg.style.color = 'crimson';
    msg.textContent = '❌ Error generando claves: ' + err.message;
  }}
}});

document.getElementById('copyGenPub').addEventListener('click', () => {{
  navigator.clipboard.writeText(document.getElementById('genPub').value);
  alert('✓ PublicKey copiada.');
}});
document.getElementById('copyGenPriv').addEventListener('click', () => {{
  navigator.clipboard.writeText(document.getElementById('genPriv').value);
  alert('✓ PrivateKey copiada. Guárdala en secreto.');
}});

document.getElementById('pastePubBtn').addEventListener('click', async () => {{
  try {{
    const txt = await navigator.clipboard.readText();
    document.getElementById('recipientPub').value = txt.trim();
  }} catch (err) {{
    alert('❌ No se pudo leer el portapapeles: ' + err.message);
  }}
}});

document.getElementById('copyBtn').addEventListener('click', () => {{
  navigator.clipboard.writeText(document.getElementById('result').value);
  alert('✓ Enlace copiado.');
}});
</script>
"""

st.components.v1.html(create_html, height=1200, scrolling=True)

st.divider()

st.components.v1.html(create_html, height=1200, scrolling=True)

st.divider()

# ====================================================================
# ========================== LEER SECRETO =============================
# ====================================================================

st.header("📖 Leer Secreto (Receptor)")

read_html = f"""
<div style="font-family: system-ui, sans-serif; max-width: 900px;">
  <div id="status" style="margin:12px 0;color:#444;font-weight:500;font-size:1.05em;padding:8px;background:#f5f5f5;border-radius:4px;"></div>
  
  <div id="secretOutBox" style="display:none;margin-top:12px;border:2px solid #4CAF50;padding:12px;background:#f1f8e9;border-radius:4px;">
    <div style="font-weight:600;color:#2e7d32;margin-bottom:8px;">✅ Secreto descifrado:</div>
    <textarea id="secretOut" style="width:100%;padding:10px;border:1px solid #4CAF50;border-radius:4px;font-family:monospace;font-size:0.9em;height:80px;resize:vertical;" readonly></textarea>
    <button id="copySecretBtn" style="padding:8px 12px;cursor:pointer;background:#4CAF50;color:white;border:none;border-radius:4px;margin-top:8px;">📋 Copiar secreto</button>
  </div>

  <div style="background:#e8f5e9;padding:12px;border-radius:5px;margin:12px 0;border-left:4px solid #2e7d32;">
    <strong>🔑 Tu Private Key (necesario para descifrar)</strong>
  </div>
  
  <label style="font-weight:600;">Private Key (base64url):</label>
  <input id="privKey" style="width:100%;padding:10px;margin:8px 0;border:1px solid #bbb;border-radius:4px;font-family:monospace;font-size:0.85em;" placeholder="Ingresa tu private key aquí o úsalo del botón abajo">

  <div style="display:flex;gap:8px;align-items:center;margin-top:10px;flex-wrap:wrap;">
    <button id="pastePrivBtn" style="padding:10px 14px;cursor:pointer;background:#1976D2;color:white;border:none;border-radius:4px;font-weight:600;">📋 Pegar PrivateKey</button>
    <button id="genKeyReadBtn" style="padding:10px 14px;cursor:pointer;background:#7b1fa2;color:white;border:none;border-radius:4px;font-weight:600;">🔑 Generar nuevo par</button>
  </div>

  <div id="genBoxRead" style="display:none;margin-top:12px;border-left:4px solid #4CAF50;padding:12px;background:#f1f8e9;border-radius:4px;">
    <div style="font-weight:600;color:#2e7d32;margin-bottom:10px;font-size:1.05em;">✅ Claves generadas:</div>
    
    <div style="margin-bottom:12px;">
      <label style="font-weight:600;color:#2e7d32;">Public Key (comparte esto al remitente):</label>
      <textarea id="genPubRead" readonly style="width:100%;padding:10px;margin:6px 0;background:#fff;border:1px solid #aed581;border-radius:4px;font-family:monospace;font-size:0.85em;height:60px;"></textarea>
      <button id="copyGenPubRead" style="padding:8px 12px;cursor:pointer;background:#4CAF50;color:white;border:none;border-radius:4px;">📋 Copiar PublicKey</button>
    </div>

    <div>
      <label style="font-weight:600;color:#c62828;">Private Key (guarda en SECRETO):</label>
      <textarea id="genPrivRead" readonly style="width:100%;padding:10px;margin:6px 0;background:#fff;border:1px solid #ef5350;border-radius:4px;font-family:monospace;font-size:0.85em;height:60px;"></textarea>
      <button id="copyGenPrivRead" style="padding:8px 12px;cursor:pointer;background:#c62828;color:white;border:none;border-radius:4px;">📋 Copiar PrivateKey</button>
    </div>
  </div>

  <div style="background:#fff3e0;padding:12px;border-radius:5px;margin:12px 0;border-left:4px solid #f57c00;">
    <strong>📧 Leer manualmente (opcional)</strong>
  </div>
  <label style="font-weight:600;">Enlace del secreto:</label>
  <input id="manual" placeholder="https://localhost:8501/?id=..." style="width:100%;padding:10px;margin:8px 0;border:1px solid #bbb;border-radius:4px;font-family:monospace;font-size:0.85em;">
  <button id="manualBtn" style="padding:10px 14px;cursor:pointer;background:#f57c00;color:white;border:none;border-radius:4px;font-weight:600;margin-top:8px;">📖 Leer secreto</button>
</div>

<script>
const API_BASE  = "{API_BASE}";
const textDecoder = new TextDecoder();

function b64uToBytes(s) {{
  s = s.replace(/-/g,'+').replace(/_/g,'/');
  while (s.length % 4) s += '=';
  const bin = atob(s);
  const out = new Uint8Array(bin.length);
  for (let i=0;i<bin.length;i++) out[i] = bin.charCodeAt(i);
  return out;
}}

function bytesToB64u(bytes) {{
  let bin = '';
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
}}

async function tryRead(id, privB64u) {{
  const status = document.getElementById('status');
  const outBox = document.getElementById('secretOutBox');
  const out    = document.getElementById('secretOut');

  try {{
    status.style.color='#1976D2';
    status.textContent='⏳ Leyendo secreto del servidor...';

    const resp = await fetch(API_BASE + "/s/" + encodeURIComponent(id));
    if (!resp.ok) {{
      const errText = await resp.text();
      const code = resp.status;
      if (code === 410) {{
        throw new Error("Este secreto ya fue leído una vez (OTV). Se destruyó automáticamente.");
      }} else if (code === 404) {{
        throw new Error("Secreto no encontrado.");
      }} else {{
        throw new Error(`Servidor error ${{code}}: ${{errText}}`);
      }}
    }}

    status.style.color='#1976D2';
    status.textContent='✓ Secreto recibido. Descifrando localmente...';

    const data = await resp.json();
    const packed = b64uToBytes(data.ciphertext);

    const iv = packed.slice(0,12);
    const ct = packed.slice(12);

    const privInput = privB64u || document.getElementById('privKey').value.trim();
    if (!privInput) {{
      throw new Error("Se requiere tu Private Key para descifrar este secreto.");
    }}

    let rsaPriv;
    try {{
      const decodedPriv = b64uToBytes(privInput);
      rsaPriv = await crypto.subtle.importKey(
        'pkcs8',
        decodedPriv.buffer,
        {{ name: 'RSA-OAEP', hash: 'SHA-256' }},
        false,
        ['decrypt']
      );
    }} catch (e) {{
      throw new Error("Private Key inválida (se espera PKCS8 base64url): " + e.message);
    }}

    if (!data.wrapped_key) {{
      throw new Error("❌ Este secreto no tiene wrapped_key. Formato no soportado.");
    }}

    let aesRaw;
    try {{
      const wrappedBytes = b64uToBytes(data.wrapped_key);
      const decrypted = await crypto.subtle.decrypt(
        {{ name: 'RSA-OAEP' }},
        rsaPriv,
        wrappedBytes
      );
      aesRaw = new Uint8Array(decrypted);
    }} catch (e) {{
      throw new Error("Error abriendo wrapped_key (RSA-OAEP). ¿Private key correcta? Detalles: " + e.message);
    }}

    if (!aesRaw) {{
      throw new Error("No se pudo abrir wrapped_key. Verifica tu Private Key.");
    }}

    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      aesRaw,
      {{ name: 'AES-GCM' }},
      false,
      ['decrypt']
    );

    status.style.color='#1976D2';
    status.textContent='✓ Desencriptando...';

    const ptBuf = await crypto.subtle.decrypt({{name:'AES-GCM', iv}}, cryptoKey, ct);
    out.value = textDecoder.decode(ptBuf);
    outBox.style.display = 'block';

    status.style.color='green';
    status.textContent='✅ ¡Secreto descifrado! (OTV: Ya fue leído, no podrá volver a leerlo)';
  }}
  catch(e) {{
    status.style.color='crimson';
    status.textContent='❌ Error: ' + e.message;
  }}
}}

document.getElementById('manualBtn').addEventListener('click', () => {{
  try {{
    const url = new URL(document.getElementById('manual').value.trim());
    const id = url.searchParams.get('id');
    if (!id) throw new Error("No se encontró parámetro 'id' en la URL.");
    tryRead(id, null);
  }} catch (e) {{
    document.getElementById('status').style.color='crimson';
    document.getElementById('status').textContent = "❌ URL inválida: " + e.message;
  }}
}});

// Intenta leer automáticamente si hay ?id en la URL actual
try {{
  const url = new URL(window.location.href);
  const id = url.searchParams.get('id');
  if (id) {{
    document.getElementById('status').textContent = '⏳ Parámetro ?id detectado. Ingresa tu Private Key y presiona "Leer secreto".';
  }}
}} catch{{}}

// Generar par de claves en la vista de lectura
document.getElementById('genKeyReadBtn').addEventListener('click', async () => {{
  try {{
    const kp = await crypto.subtle.generateKey(
      {{
        name: 'RSA-OAEP',
        modulusLength: 2048,
        publicExponent: new Uint8Array([1,0,1]),
        hash: 'SHA-256'
      }},
      true,
      ['encrypt','decrypt']
    );
    const pubBuf = new Uint8Array(await crypto.subtle.exportKey('spki', kp.publicKey));
    const privBuf = new Uint8Array(await crypto.subtle.exportKey('pkcs8', kp.privateKey));
    const pub = bytesToB64u(pubBuf);
    const priv = bytesToB64u(privBuf);
    document.getElementById('genPubRead').value = pub;
    document.getElementById('genPrivRead').value = priv;
    document.getElementById('genBoxRead').style.display = 'block';
    document.getElementById('privKey').value = priv;
    document.getElementById('status').style.color='#2196F3';
    document.getElementById('status').textContent = '✓ Par de claves generado. Comparte tu Public Key al remitente.';
  }} catch (e) {{
    document.getElementById('status').style.color='crimson';
    document.getElementById('status').textContent = '❌ Error generando claves: ' + e.message;
  }}
}});

document.getElementById('copyGenPubRead').addEventListener('click', () => {{
  navigator.clipboard.writeText(document.getElementById('genPubRead').value);
  alert('✓ PublicKey copiada al portapapeles');
}});
document.getElementById('copyGenPrivRead').addEventListener('click', () => {{
  navigator.clipboard.writeText(document.getElementById('genPrivRead').value);
  alert('✓ PrivateKey copiada al portapapeles (¡Guarda en secreto!)');
}});

document.getElementById('copySecretBtn').addEventListener('click', () => {{
  navigator.clipboard.writeText(document.getElementById('secretOut').value);
  alert('✓ Secreto copiado al portapapeles');
}});

document.getElementById('pastePrivBtn').addEventListener('click', async () => {{
  try {{
    const txt = await navigator.clipboard.readText();
    document.getElementById('privKey').value = txt.trim();
  }} catch (e) {{
    alert('❌ No se pudo leer el portapapeles: ' + e.message);
  }}
}});
</script>
"""

st.components.v1.html(read_html, height=1000, scrolling=True)

st.divider()

# ====================================================================
# ===================== INFORMACIÓN Y AYUDA ===========================
# ====================================================================

with st.expander("ℹ️ ¿Cómo funciona OTV v2?", expanded=False):
    st.markdown("""
    ### Flujo de datos E2E con Wrapped Key
    
    **1. CREAR (Remitente):**
    - Genera una pareja de claves RSA 2048 bits (publicKey + privateKey)
    - Comparte su publicKey al receptor
    - El remitente cifra el mensaje con AES-GCM 256 (clave única)
    - La clave AES se envuelve (wraps) con la publicKey del receptor (RSA-OAEP SHA-256)
    - Se envía al servidor: `ciphertext` (mensaje cifrado) + `wrapped_key` (clave envuelta)
    - **El servidor NUNCA ve la clave AES en texto plano**
    
    **2. LEER (Receptor):**
    - El receptor recibe el enlace con el ID del secreto
    - Pega su privateKey en el formulario
    - Descarga el secreto del servidor
    - Abre el wrapped_key con su privateKey (RSA-OAEP)
    - Obtiene la clave AES original
    - Descifra el mensaje localmente
    - **OTV Garantía:** El secreto se marca como "burned" → no se puede leer 2 veces
    
    ### Características de Seguridad
    
    - ✅ **E2E encriptado:** Cifrado en cliente, servidor nunca ve el plaintext
    - ✅ **Wrapped Key:** La clave AES no viaja por la URL o sin protección
    - ✅ **RSA-OAEP + AES-GCM:** Criptografía moderna y segura
    - ✅ **One-Time Read:** Lectura única, se destruye tras primer acceso
    - ✅ **TTL:** Expiración automática (TTL configurable)
    - ✅ **Audit Log:** Cadena de eventos (trazabilidad)
    
    ### ¿Qué es Wrapped Key?
    
    - **Sin wrapped key (antiguo):** Clave AES en plaintext en URL → inseguro
    - **Con wrapped key (nuevo):** Clave AES cifrada con publicKey → solo quien tiene privateKey la puede abrir
    - Usa algoritmo **RSA-OAEP (WebCrypto)** para la envoltura
    
    ### Requisitos
    
    - Backend FastAPI con SQLite
    - Frontend Streamlit con WebCrypto nativo
    - TLS local (recomendado)
    """)

with st.expander("🔗 Ver Audit Log", expanded=False):
    if st.button("Cargar /log"):
        try:
            r = requests.get(f"{API_BASE}/log", timeout=5)
            if r.ok:
                logs = r.json()
                st.json(logs[-20:] if len(logs) > 20 else logs)
            else:
                st.error(f"Error: {r.status_code}")
        except Exception as e:
            st.error(f"No se pudo conectar: {e}")

