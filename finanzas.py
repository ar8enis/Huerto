import streamlit as st
import database as db
import pandas as pd

def mostrar_finanzas():
    st.title("💰 Finanzas")
    t_c, t_o, t_v = db.calcular_resumen_financiero()
    st.metric("Balance", f"${t_v - (t_c + t_o):,.2f}", delta=f"${t_v:,.2f} Ingresos")
    
    with st.expander("Registrar Venta"):
        f = st.date_input("Fecha"); l = st.text_input("Lote"); c = st.number_input("Cajas"); p = st.number_input("Precio/Caja")
        if st.button("Vender"): db.registrar_venta(str(f), l, c, p, ""); st.rerun()

    st.subheader("Análisis de Rentabilidad")
    lotes = db.obtener_terrenos()
    for l in lotes:
        # Aquí podrías filtrar ventas por lote para un análisis real
        st.write(f"Lote: {l[1]} | Árboles: {l[3]}")