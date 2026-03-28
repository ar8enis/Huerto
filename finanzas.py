import streamlit as st
import database as db
import pandas as pd

def mostrar_finanzas(u_id): # Recibimos u_id
    st.title("💰 Finanzas y Rentabilidad")
    
    # Pasamos u_id a la función de cálculo
    t_c, t_o, t_v = db.calcular_resumen_financiero(u_id)
    
    # Visualización de métricas principales
    balance = t_v - (t_c + t_o)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Balance Neto", f"${balance:,.2f}", delta=f"${t_v:,.2f} Ingresos Totales")
    with col2:
        total_gastos = t_c + t_o
        st.metric("Gastos Totales", f"${total_gastos:,.2f}", delta_color="inverse")

    # Registro de Ventas
    with st.expander("📝 Registrar Nueva Venta de Cosecha"):
        # Obtenemos los lotes del usuario para que elija uno
        lotes_raw = db.obtener_terrenos(u_id)
        nombres_lotes = [l[2] for l in lotes_raw] # Índice 2 es el nombre en el nuevo sistema
        
        if not nombres_lotes:
            st.warning("Primero debes registrar un terreno para poder asignar ventas.")
        else:
            with st.form("form_venta", clear_on_submit=True):
                f = st.date_input("Fecha de venta")
                l = st.selectbox("Lote de origen", nombres_lotes)
                c1, c2 = st.columns(2)
                c = c1.number_input("Cantidad de Cajas", min_value=0.1, step=1.0)
                p = c2.number_input("Precio por Caja ($)", min_value=0.1, step=1.0)
                cliente = st.text_input("Cliente / Comprador (Opcional)")
                
                if st.form_submit_button("Guardar Venta"):
                    # Pasamos u_id y los parámetros requeridos
                    db.registrar_venta(u_id, str(f), l, c, p, cliente)
                    st.success("Venta registrada correctamente")
                    st.rerun()

    st.divider()
    st.subheader("📈 Análisis de Rentabilidad por Lote")
    
    if not lotes_raw:
        st.info("No hay datos de terrenos para analizar.")
    else:
        # Mostramos un resumen por cada lote del usuario
        for l in lotes_raw:
            # Índices multi-usuario: 2:nombre, 4:arboles
            nombre_lote = l[2]
            num_arboles = l[4]
            
            # Consultamos ventas de este lote (necesitaríamos una función específica o filtrar aquí)
            # Por ahora mostramos la info básica del lote
            with st.container(border=True):
                st.write(f"### Lote: {nombre_lote}")
                st.write(f"🌳 Árboles: {num_arboles}")
                # Aquí podrías agregar más lógica de filtrado por lote en el futuro
