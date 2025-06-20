import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from io import BytesIO
import os
from datetime import date

# ----------------------------
# Diccionario de usuarios
USUARIOS_AUTORIZADOS = {
    "admin": "admin123",
    "paola": "Anthony29$.."
}
# ----------------------------

# Configura la página
st.set_page_config(page_title="Reporte de Movimientos de Tarjetas", layout="wide")

# ----------------------------
# Control de login
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
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos.")
    st.stop()

# ----------------------------
# Si está autenticado, continúa con la app
st.title("📊 Reporte: Movimientos de Tarjetas")

# Leer variables de entorno
user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
host = os.getenv("MYSQL_HOST")
port = os.getenv("MYSQL_PORT")
database = os.getenv("MYSQL_DB")

# URL de conexión a base de datos
DB_URL = f"mysql+pymysql://admin:Admin+MySql-df58@10.30.10.98:3306/MYSQL_PTECH_DWH01"
engine = create_engine(DB_URL)

# ----------------------------
# Inicialización de filtros
if "documento" not in st.session_state:
    st.session_state.documento = ""
if "fecha_inicio" not in st.session_state:
    st.session_state.fecha_inicio = None
if "fecha_fin" not in st.session_state:
    st.session_state.fecha_fin = None

# Botón para limpiar filtros
if st.button("🧹 Borrar filtros"):
    st.session_state.documento = ""
    st.session_state.fecha_inicio = None
    st.session_state.fecha_fin = None
    st.rerun()

# ----------------------------
# Filtros de búsqueda
numero_documento = st.text_input("🔍 Ingrese el número de documento del cliente (opcional):", key="documento")

col1, col2 = st.columns(2)
with col1:
    fecha_inicio = st.date_input("📅 Fecha inicio (opcional)", key="fecha_inicio", value=None)
with col2:
    fecha_fin = st.date_input("📅 Fecha fin (opcional)", key="fecha_fin", value=None)

# ----------------------------
# Botón para ejecutar búsqueda
if st.button("🔎 Buscar movimientos"):

    # Validación: debe haber al menos un filtro
    if not numero_documento and not fecha_inicio and not fecha_fin:
        st.error("❌ Debe ingresar un número de documento o un rango de fechas.")
        st.stop()

    # Validación de fechas
    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        st.error("❌ La fecha de inicio no puede ser posterior a la fecha de fin.")
        st.stop()

    try:
        with engine.connect() as connection:
            filtros = []
            parametros = {}

            if numero_documento:
                filtros.append("NUMERO_DOCUMENTO = :numero_documento")
                parametros["numero_documento"] = numero_documento

            filtros.append("CODIGO_RESPUESTA = '00'")

            if fecha_inicio and fecha_fin:
                filtros.append("FECHA BETWEEN :fecha_inicio AND :fecha_fin")
                parametros["fecha_inicio"] = fecha_inicio
                parametros["fecha_fin"] = fecha_fin

            filtro_sql = " AND ".join(filtros)
            query = text(f"""
                SELECT * FROM ZEUS_MOVIMIENTOS
                WHERE {filtro_sql}
                ORDER BY FECHA DESC
            """)

            df = pd.read_sql(query, connection, params=parametros)

        if df.empty:
            st.warning("⚠️ No se encontraron movimientos con los filtros aplicados.")
        else:
            st.success(f"✅ Se encontraron {len(df)} movimientos.")

            # Mostrar tabla si se filtró por número de documento
            if numero_documento:
                st.dataframe(df, use_container_width=True)

            # Permitir descarga si se filtró por fecha
            if fecha_inicio and fecha_fin:
                output = BytesIO()
                df.to_excel(output, index=False, engine="openpyxl")
                output.seek(0)

                file_suffix = (
                    f"{numero_documento}_{fecha_inicio}_{fecha_fin}"
                    if numero_documento and fecha_inicio and fecha_fin
                    else numero_documento or f"{fecha_inicio}_{fecha_fin}"
                )

                st.download_button(
                    label="📥 Descargar como Excel",
                    data=output,
                    file_name=f"movimientos_{file_suffix}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"❌ Error al consultar: {e}")
