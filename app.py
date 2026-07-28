import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime
import google.generativeai as genai
from PIL import Image

# --- CONFIGURACIÓN DE IA ---
genai.configure(api_key="")

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestor de Camisetas - Módulo", page_icon="🟣", layout="centered")

# --- 1. INYECCIÓN DE ESTILOS CSS (Fuentes Gamer y Colores Púrpura) ---
st.markdown("""
<style>
@import url('https://googleapis.com');

html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.1rem;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Orbitron', sans-serif !important;
    color: #c77dff !important;
    text-shadow: 0px 0px 8px rgba(199, 125, 255, 0.4);
}

div[data-testid="stAlert"] {
    background-color: rgba(60, 9, 108, 0.4) !important;
    border-left: 4px solid #9d4edd !important;
    color: #e0aaff !important;
}

section[data-testid="stFileUploadDropzone"] {
    border: 2px dashed #9d4edd !important;
    background-color: rgba(36, 0, 70, 0.3) !important;
    border-radius: 10px;
    transition: all 0.3s ease;
}

section[data-testid="stFileUploadDropzone"]:hover {
    border: 2px solid #e0aaff !important;
    background-color: rgba(90, 24, 154, 0.4) !important;
}

.title-container {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 5px;
    margin-top: 20px;
}
.title-container h1, .title-container h2 {
    margin: 0;
    padding: 0;
}
</style>
""", unsafe_allow_html=True)

# --- 2. CREACIÓN DEL ICONO SVG VIRTUAL (Cero enlaces rotos) ---
svg_camiseta = """
<svg xmlns="http://w3.org" viewBox="0 0 24 24" width="45" height="45">
  <defs>
    <linearGradient id="jerseyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#e0aaff;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#5a189a;stop-opacity:1" />
    </linearGradient>
  </defs>
  <path fill="url(#jerseyGrad)" d="M15.42 2.33a2.98 2.98 0 0 1-6.84 0l-3.3.99a2 2 0 0 0-1.28 1.28L2 11.23a1 1 0 0 0 .95 1.32h2.24l.65 8.44a2 2 0 0 0 2 1.84h8.32a2 2 0 0 0 2-1.84l.65-8.44h2.24a1 1 0 0 0 .95-1.32L20 4.6a2 2 0 0 0-1.28-1.28l-3.3-.99z"/>
</svg>
"""

# --- 3. LÓGICA DE SEGURIDAD (LA CERRADURA) ---
PALABRA_SECRETA = "U-29-TITULOS-SISTEMA-PRO"

if 'acceso_concedido' not in st.session_state:
    st.session_state['acceso_concedido'] = False
    st.session_state['client_name'] = ""

if not st.session_state['acceso_concedido']:
    st.markdown('<div class="title-container"><h1>🔒 Acceso restringido a Clientes</h1></div>', unsafe_allow_html=True)
    llave_ingresada = st.text_input("Ingrese su Llave de Acceso", type="password")
    
    if st.button("Ingresar al Sistema"):
        if llave_ingresada:
            try:
                partes = llave_ingresada.split("-")
                if len(partes) == 3:
                    nombre_cliente = partes[0]
                    fecha_str = partes[1]
                    hash_ingresado = partes[2]
                    
                    texto_a_hashear = f"{nombre_cliente}|{fecha_str}|{PALABRA_SECRETA}"
                    hash_real = hashlib.md5(texto_a_hashear.encode()).hexdigest()[:6].upper()
                    
                    if hash_ingresado == hash_real:
                        st.session_state['acceso_concedido'] = True
                        st.session_state['client_name'] = nombre_cliente
                        st.rerun()
                    else:
                        st.error("❌ Llave de acceso inválida.")
                else:
                    st.error("❌ Formato de llave incorrecto.")
            except Exception:
                st.error("❌ Error al procesar la llave.")
        else:
            st.warning("⚠️ Ingrese una llave para continuar.")
    
    st.stop()

# --- 4. APLICACIÓN PRINCIPAL (EL SISTEMA) ---
st.markdown(f'<div class="title-container">{svg_camiseta}<h1>Procesador Action FerPro </h1></div>', unsafe_allow_html=True)
st.success(f"Bienvenido, **{st.session_state['client_name']}**. Licencia activa y validada algorítmicamente.")

st.markdown(f'<div class="title-container">{svg_camiseta}<h2>Listas de Camisetas</h2></div>', unsafe_allow_html=True)
st.write("") 

# Zona de carga
st.markdown("### 📸 1. Zona para subir la foto")
foto = st.file_uploader("Sube la foto de la lista (JPG, PNG)", type=["jpg", "png", "jpeg"])

if foto:
    st.image(foto, caption="Foto cargada lista para escanear", use_container_width=True)
    
    # --- BOTÓN Y MOTOR DE IA ---
    if st.button("🚀 Escanear y Extraer Datos"):
        with st.spinner("La IA está leyendo la imagen, por favor espera..."):
            try:
                img = Image.open(foto)
                modelo = genai.GenerativeModel('models/gemini-flash-latest')
                
                instruccion = """
                Lee esta imagen de una lista de pedidos de camisetas deportivas.
                Extrae exactamente 3 campos por fila: NOMBRE, NUMERO y TALLA.

                REGLAS STRICTAS DE TRANSCRIPCIÓN:
                1. CAMPO NOMBRE: Transcribe el nombre EXACTAMENTE como está escrito. Conserva de forma LITERAL cualquier número (ej. P3R3Z), símbolo (@, $, #, *), arroba o combinación rara dentro del nombre. NO autocorrijas, NO asumas errores ortográficos ni cambies caracteres.
                2. CAMPO NUMERO: Corresponde únicamente al dorsal de la camiseta.
                3. CAMPO TALLA: Corresponde a la medida (S, M, L, XL, etc.).
                
                Formato de salida estrictamente en CSV separado por comas, sin comillas ni markdown:
                NOMBRE,NUMERO,TALLA
                """
                
                respuesta = modelo.generate_content([instruccion, img])
                
                lineas = respuesta.text.strip().replace("```", "").split('\n')
                datos_procesados = []
                
                for linea in lineas:
                    partes = linea.split(',')
                    if len(partes) >= 3 and partes[0].strip().upper() != "NOMBRE":
                        datos_procesados.append({
                            "Nombre": partes[0].strip().upper(),
                            "Numero": partes[1].strip().upper(),
                            "Talla": partes[2].strip().upper()
                        })
                
                st.session_state['datos_ia'] = pd.DataFrame(datos_procesados)
                
            except Exception as e:
                st.error(f"❌ Error técnico real: {e}")

    st.divider()

    # --- ZONA DE TABLA EDITABLE ---
    st.markdown("### 📝 2. Datos Extraídos (Editables)")
    
    if 'datos_ia' not in st.session_state:
        df_mostrar = pd.DataFrame(columns=["Nombre", "Numero", "Talla"])
    else:
        df_mostrar = st.session_state['datos_ia']
        
    tabla_final = st.data_editor(df_mostrar, num_rows="dynamic", use_container_width=True)
    
    st.divider()
    
    # --- ZONA DE DESCARGA Y MACRO (CORREGIDA AL 100%) ---
    st.markdown("### 📤 3. Opciones de Exportación")
    
    # --- FILTRO DE LIMPIEZA ---
    # Detecta y elimina cualquier fila donde el nombre contenga la palabra "NOMBRE" (ej. "1. Nombre")
    tabla_limpia = tabla_final[~tabla_final['Nombre'].astype(str).str.upper().str.contains('NOMBRE', na=False)]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Usamos la 'tabla_limpia' para generar el CSV sin la basura
        csv_excel = tabla_limpia.to_csv(index=False, sep=';', header=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Descargar para Excel (.csv)",
            data=csv_excel,
            file_name='pedidos_camisetas.csv',
            mime='text/csv'
        )
        
    with col2:
        st.markdown("**Copiar para Macro**")
        
        # 1. Usamos tabla_limpia para que el texto tampoco tenga la basura de encabezados
        # 2. Generamos el texto nativo separado por tabulaciones (\t)
        texto_macro = tabla_limpia.to_csv(index=False, sep='\t', header=False)
        
        # 3. El componente st.code genera una caja oscura nativa. 
        # Al pasar el mouse, aparece un botón de copiado automático en la esquina superior derecha. 
        # También te permite sombrear con el mouse si prefieres hacerlo manual.
        st.code(texto_macro, language="text")
