import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from io import BytesIO
import os

# ----------------------------
# 🔐 Diccionario de usuarios
USUARIOS_AUTORIZADOS = {
    "admin": "admin123",
    "paola": "clavepaola",
    "invitado": "demo123"
}
# ----------------------------

# Configurar la página
st.set_page_config(page_title="Reporte de Movimientos de Tarjetas", layout="wide")

# ----------------------------
# 🔐 Control de login
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Iniciar sesión")
    usuario = st.text_input("👤 Usuario")
    clave = st.text_input("🔑 Contraseña", type="password")

    if st.button("Iniciar sesión"):
        if usuario in USUARIOS_AUTORIZADOS and USUARIOS_AUTORIZADOS[usuario] == clave:
            st.success("✅ Autenticado correctamente.")
            st.session_state.autenticado = True
            st.rerun()  # ✅ corregido
        else:
            st.error("❌ Usuario o contraseña incorrectos.")
    st.stop()
# ----------------------------

# 💡 Si está autenticado, continúa con la app
st.title("📊 Reporte de Movimientos de Tarjetas")

# Leer variables de entorno (opcional)
user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
host = os.getenv("MYSQL_HOST")
port = os.getenv("MYSQL_PORT")
database = os.getenv("MYSQL_DB")

# URL de conexión a base de datos
DB_URL = f"mysql+pymysql://admin:Admin+MySql-df58@10.30.10.98:3306/MYSQL_PTECH_DWH01"
engine = create_engine(DB_URL)

# Ingreso del documento
numero_documento = st.text_input("🔍 Ingrese el número de documento del cliente:")

if numero_documento:
    query = text("""
        SELECT * FROM ZEUS_MOVIMIENTOS
        WHERE NUMERO_DOCUMENTO = :numero_documento
        ORDER BY FECHA DESC
    """)

    try:
        with engine.connect() as connection:
            df = pd.read_sql(query, connection, params={"numero_documento": numero_documento})

        if df.empty:
            st.warning("⚠️ No se encontraron movimientos para ese número de documento.")
        else:
            st.success(f"✅ Se encontraron {len(df)} movimientos.")
            st.dataframe(df, use_container_width=True)

            # Exportar a Excel en memoria
            output = BytesIO()
            df.to_excel(output, index=False, engine="openpyxl")
            output.seek(0)

            st.download_button(
                label="📥 Descargar como Excel",
                data=output,
                file_name=f"movimientos_{numero_documento}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("👈 Ingrese un número de documento para ver los movimientos.")
