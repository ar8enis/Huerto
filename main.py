import streamlit as st
import database as db
from inventario import mostrar_inventario
from bitacora import mostrar_bitacora
from terreno import mostrar_terreno
from notas import mostrar_notas
from finanzas import mostrar_finanzas
from reportes import mostrar_reportes

st.set_page_config(page_title="Huerto Manager", layout="wide")
db.crear_tablas()

with st.sidebar:
    als = db.obtener_alertas_stock()
    for a in als: st.error(f"⚠️ {a['nombre']}: {a['actual']:g}")
    m = st.radio("Menú", ["Inventario", "Terreno", "Bitácora", "Notas", "Finanzas", "Reportes"])

if m == "Inventario": mostrar_inventario()
elif m == "Terreno": mostrar_terreno() # (Crea un terreno.py simple similar a finanzas)
elif m == "Bitácora": mostrar_bitacora()
elif m == "Notas": mostrar_notas()
elif m == "Finanzas": mostrar_finanzas()
elif m == "Reportes": mostrar_reportes()