from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from io import BytesIO
from datetime import date, datetime
import pandas as pd
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
host = os.getenv("MYSQL_HOST")
port = os.getenv("MYSQL_PORT")
database = os.getenv("MYSQL_DB")

DB_URL = f"mysql+pymysql://admin:Admin+MySql-df58@10.30.10.98:3306/MYSQL_PTECH_DWH01"
engine = create_engine(DB_URL)

app = FastAPI()

class FiltroGeneral(BaseModel):
    numero_documento: str | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    como_excel: bool = False

def generar_nombre_archivo(nombre_tabla: str, filtros: FiltroGeneral) -> str:
    nombre_base = nombre_tabla.lower()
    if filtros.fecha_inicio and filtros.fecha_fin:
        if filtros.fecha_inicio == filtros.fecha_fin:
            fecha_str = filtros.fecha_inicio.strftime("%Y%m%d")
        else:
            fecha_str = f"{filtros.fecha_inicio.strftime('%Y%m%d')}_{filtros.fecha_fin.strftime('%Y%m%d')}"
        return f"{nombre_base}_{fecha_str}.xlsx"
    return f"{nombre_base}.xlsx"

def ejecutar_consulta(nombre_tabla: str, filtros: FiltroGeneral):
    condiciones = []
    parametros = {}

    tiene_documento = filtros.numero_documento is not None and filtros.numero_documento != ""
    tiene_rango_fechas = filtros.fecha_inicio is not None and filtros.fecha_fin is not None

    if not tiene_documento and not tiene_rango_fechas:
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar al menos un número de documento o un rango de fechas completo."
        )

    if tiene_documento:
        campo = "NUMERO_DOCUMENTO" if nombre_tabla == "ZEUS_MOVIMIENTOS" else "DOCUMENTO"
        condiciones.append(f"{campo} = :numero_documento")
        parametros["numero_documento"] = filtros.numero_documento

    if tiene_rango_fechas:
        if filtros.fecha_inicio > filtros.fecha_fin:
            raise HTTPException(status_code=400, detail="La fecha de inicio no puede ser posterior a la fecha de fin.")

        fecha_inicio_dt = datetime.combine(filtros.fecha_inicio, datetime.min.time())
        fecha_fin_dt = datetime.combine(filtros.fecha_fin, datetime.max.time())

        condiciones.append("FECHA BETWEEN :fecha_inicio AND :fecha_fin")
        parametros["fecha_inicio"] = fecha_inicio_dt
        parametros["fecha_fin"] = fecha_fin_dt

    if nombre_tabla == "ZEUS_MOVIMIENTOS":
        condiciones.append("CODIGO_RESPUESTA = '00'")

    query = text(f"""
        SELECT * FROM {nombre_tabla}
        WHERE {' AND '.join(condiciones)}
        ORDER BY FECHA DESC
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params=parametros)

    if df.empty:
        return JSONResponse(status_code=404, content={"detalle": "No se encontraron registros"})

    if filtros.como_excel:
        output = BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)
        filename = generar_nombre_archivo(nombre_tabla, filtros)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    df = df.fillna("")
    return df.to_dict(orient="records")

@app.post("/movimientos")
def obtener_movimientos(filtros: FiltroGeneral):
    return ejecutar_consulta("ZEUS_MOVIMIENTOS", filtros)

@app.post("/cierrediario")
def obtener_cierre_diario(filtros: FiltroGeneral):
    return ejecutar_consulta("ZEUS_CORTE_DIARIO", filtros)

app.mount("/", StaticFiles(directory="static", html=True), name="static")
