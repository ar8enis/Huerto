import streamlit as st
from datetime import date
import database as db

def mostrar_inventario(u_id):
    st.title("📦 Gestión de Inventario")
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Existencias", "🛒 Compras", "🚜 Usos", "🤝 Préstamos"])

    # --- PESTAÑA 1: EXISTENCIAS (STOCK REAL) ---
    with tab1:
        exist = db.obtener_existencias(u_id)
        costos = db.obtener_costos_promedio(u_id)
        compras = db.obtener_compras(u_id)
        
        # Mapeo de info (Nombre -> [Unidad, Es_Herramienta])
        # Indices: nombre (2), unidad (4), es_herramienta (8)
        d_info = {c[2]: {"uni": c[4], "her": c[8]} for c in compras}
        
        if not exist:
            st.warning("No hay productos en bodega.")
        else:
            val_total = db.obtener_valor_total_bodega(u_id)
            st.metric("Valor Total en Bodega", f"${val_total:,.2f}")
            st.divider()

            for n, u_f, s in exist:
                cp = costos.get(n, 0)
                es_h = d_info.get(n, {}).get("her", 0)
                uni = d_info.get(n, {}).get("uni", "unid")
                
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 1.5, 1])
                    with c1:
                        st.write(f"### {'🛠️' if es_h else '🧪'} {n}")
                        st.write(f"**Stock:** {s:g} {uni}")
                    with c2:
                        st.write(f"Costo Prom: ${cp:,.2f}")
                        st.write(f"Valor Stock: :green[${s*cp:,.2f}]")
                    with c3:
                        with st.popover("Registrar"):
                            st.write("**Movimiento**")
                            cant = st.number_input("Cantidad", min_value=0.1, value=1.0, key=f"q_{n}")
                            dest = st.text_input("Destino/Persona", key=f"d_{n}")
                            tipo = st.radio("Tipo:", ["Uso", "Préstamo"], key=f"t_{n}")
                            if st.button("Confirmar", key=f"b_{n}", use_container_width=True):
                                if tipo == "Uso":
                                    db.registrar_salida(u_id, n, cant, str(date.today()), dest, "")
                                else: 
                                    db.registrar_prestamo(u_id, n, dest, cant, str(date.today()), "")
                                    db.registrar_salida(u_id, n, cant, str(date.today()), f"Préstamo a {dest}", "")
                                st.rerun()
                        with st.popover("Alerta"):
                            n_min = st.number_input("Avisarme si baja de:", value=0.0, key=f"min_{n}")
                            if st.button("Guardar Alerta", key=f"bm_{n}"):
                                db.actualizar_stock_minimo(u_id, n, n_min)
                                st.rerun()

    # --- PESTAÑA 2: COMPRAS (ENTRADAS) ---
    with tab2:
        with st.expander("➕ Registrar Nueva Compra", expanded=False):
            sug = db.obtener_nombres_unicos(u_id)
            nom_sel = st.selectbox("Producto:", ["--- Escribir Nuevo ---"] + sug)
            nom = st.text_input("Nombre:") if nom_sel == "--- Escribir Nuevo ---" else nom_sel
            
            es_h = st.checkbox("¿Es una Herramienta?")
            col1, col2 = st.columns(2)
            fec = col1.date_input("Fecha Compra", value=date.today())
            pre = col2.number_input("Precio Unitario ($)", min_value=0.0)
            
            col3, col4 = st.columns(2)
            can = col3.number_input("Cantidad Comprada", min_value=1.0, value=1.0)
            uni = col4.selectbox("Unidad", ["Bultos", "Litros", "Kg", "Unid"])
            
            kil = st.number_input("Kg por bulto", value=25.0) if uni == "Bultos" else 0.0
            
            if st.button("Guardar Compra", use_container_width=True):
                if nom:
                    db.agregar_item(u_id, nom, can, uni, pre, str(fec), kil, 1 if es_h else 0, "")
                    st.success("Registrado")
                    st.rerun()

        st.subheader("Historial de Compras")
        for c in db.obtener_compras(u_id):
            with st.container(border=True):
                cl1, cl2, cl3 = st.columns([2,1,1])
                # c[2] es nombre, c[3] es cantidad, c[4] es unidad, c[6] fecha, c[5] precio
                cl1.write(f"**{c[2]}** | {c[3]} {c[4]}")
                cl1.caption(f"Fecha: {c[6]}")
                cl2.write(f"Total: ${c[5]*c[3]:,.2f}")
                if cl3.button("🗑️", key=f"dc_{c[0]}"):
                    db.eliminar_compra(c[0])
                    st.rerun()

    # --- PESTAÑA 3: USOS (HISTORIAL) ---
    with tab3:
        st.subheader("Historial de Movimientos de Bodega")
        for s in db.obtener_salidas(u_id):
            with st.container(border=True):
                cx1, cx2, cx3 = st.columns([2,1,1])
                # s[2] nombre, s[5] lote/destino, s[4] fecha, s[3] cantidad
                cx1.write(f"**{s[2]}**")
                cx1.caption(f"📅 {s[4]} | Destino: {s[5]}")
                cx2.error(f"-{s[3]:g}")
                if cx3.button("🗑️", key=f"ds_{s[0]}"):
                    db.eliminar_salida(s[0])
                    st.rerun()

    # --- PESTAÑA 4: PRÉSTAMOS ---
    with tab4:
        st.subheader("Control de Préstamos")
        filtro = st.radio("Mostrar:", ["Solo Pendientes", "Todos"], horizontal=True)
        lista_p = db.obtener_prestamos(u_id, solo_pendientes=(filtro == "Solo Pendientes"))
        
        if not lista_p:
            st.info("No hay préstamos registrados.")
        else:
            for p in lista_p:
                # p: 0:id, 1:u_id, 2:item, 3:persona, 4:cant, 5:f_pres, 6:f_dev, 7:estado
                color = "green" if p[7] == "Devuelto" else "orange"
                with st.container(border=True):
                    col_info, col_status, col_del = st.columns([2, 1.5, 0.5])
                    with col_info:
                        st.write(f"**{p[2]}** ({p[4]:g} unid.)")
                        st.write(f"👤 Presta a: **{p[3]}**")
                        st.caption(f"📅 Prestado: {p[5]} | 🔙 Devuelto: {p[6] if p[6] else '---'}")
                    with col_status:
                        st.write(f"Estatus: :{color}[{p[7]}]")
                        if p[7] == 'Pendiente':
                            if st.button("↩️ Devolver", key=f"dv_{p[0]}", use_container_width=True):
                                db.devolver_prestamo(p[0], str(date.today()))
                                # Regresar al stock
                                ref = db.obtener_compras(u_id)
                                u_i = next((x[4] for x in ref if x[2] == p[2]), "Unid")
                                e_h = next((x[8] for x in ref if x[2] == p[2]), 0)
                                db.agregar_item(u_id, p[2], p[4], 0.0, str(date.today()), 0.0, e_h, f"Devol de {p[3]}")
                                st.rerun()
                    with col_del:
                        if st.button("🗑️", key=f"dp_{p[0]}"):
                            db.eliminar_prestamo(p[0])
                            st.rerun()
