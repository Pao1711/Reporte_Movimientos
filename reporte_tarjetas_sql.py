import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from io import BytesIO
import os

# Leer datos de conexión desde variables de entorno
user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
host = os.getenv("MYSQL_HOST")
port = os.getenv("MYSQL_PORT")
database = os.getenv("MYSQL_DB")

DB_URL = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
engine = create_engine(DB_URL)

st.set_page_config(page_title="Reporte de Movimientos de Tarjetas", layout="wide")
st.title("📊 Reporte de Movimientos de Tarjetas")

numero_documento = st.text_input("🔍 Ingrese el número de documento del cliente:")

if numero_documento:
    query = text("""
        SELECT * FROM ZEUS_MOVIMIENTOS
WHERE NUMERO_DOCUMENTO IN ('1057593731')
AND DESCRIPCION = 'ABONO'
ORDER BY FECHA DESC;
    """)

    try:
        with engine.connect() as connection:
            df = pd.read_sql(query, connection, params={"numero_documento": numero_documento})

        if df.empty:
            st.warning("⚠️ No se encontraron movimientos para ese número de documento.")
        else:
            st.success(f"✅ Se encontraron {len(df)} movimientos.")
            st.dataframe(df, use_container_width=True)

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
