import streamlit as st
from datetime import date
import database as db

def mostrar_inventario():
    st.title("📦 Gestión de Inventario")
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Existencias", "🛒 Compras", "🚜 Usos", "🤝 Préstamos"])

    # --- PESTAÑA 1, 2 y 3 (Se mantienen igual que tu código) ---
    with tab1:
        exist = db.obtener_existencias(); costos = db.obtener_costos_promedio()
        compras = db.obtener_compras(); d_her = {c[1]: c[7] for c in compras}
        d_uni = {c[1]: c[3] for c in compras}
        if not exist: st.warning("Sin stock.")
        else:
            val = db.obtener_valor_total_bodega()
            st.metric("Valor Total en Bodega", f"${val:,.2f}")
            for n, u_f, s in exist:
                cp = costos.get(n, 0); es_h = d_her.get(n, 0); uni = d_uni.get(n, "")
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 1.5, 1])
                    c1.write(f"### {'🛠️' if es_h else '🧪'} {n}"); c1.write(f"Stock: {s:g} {uni}")
                    c2.write(f"Costo Prom: ${cp:,.2f}"); c2.write(f"Valor: :green[${s*cp:,.2f}]")
                    with c3:
                        with st.popover("Registrar"):
                            st.write("**Uso o Préstamo**")
                            cant = st.number_input("Cantidad", min_value=0.1, value=1.0, key=f"q_{n}")
                            dest = st.text_input("Destino/Persona", key=f"d_{n}")
                            tipo = st.radio("Tipo:", ["Uso", "Préstamo"], key=f"t_{n}")
                            if st.button("Confirmar", key=f"b_{n}"):
                                if tipo == "Uso": db.registrar_salida(n, cant, str(date.today()), dest, "")
                                else: 
                                    db.registrar_prestamo(n, dest, cant, str(date.today()), "")
                                    db.registrar_salida(n, cant, str(date.today()), f"Préstamo a {dest}", "")
                                st.rerun()
                        with st.popover("Alerta"):
                            n_min = st.number_input("Mínimo:", value=0.0, key=f"min_{n}")
                            if st.button("Guardar", key=f"bm_{n}"):
                                db.actualizar_stock_minimo(n, n_min); st.rerun()

    with tab2:
        with st.expander("➕ Nueva Compra"):
            nom = st.text_input("Nombre:")
            es_h = st.checkbox("¿Es Herramienta?")
            c1, c2 = st.columns(2); fec = c1.date_input("Fecha"); pre = c2.number_input("Precio Unit.")
            c3, c4 = st.columns(2); can = c3.number_input("Cant.", value=1.0); uni = c4.selectbox("Unidad", ["Bultos", "Litros", "Kg", "Unid"])
            kil = st.number_input("Kg por bulto", value=25.0) if uni == "Bultos" else 0.0
            if st.button("Guardar"): db.agregar_item(nom, can, uni, pre, str(fec), kil, 1 if es_h else 0, ""); st.rerun()
        for c in db.obtener_compras():
            with st.container(border=True):
                col1, col2, col3 = st.columns([2,1,1])
                col1.write(f"**{c[1]}** | {c[2]} {c[3]}"); col2.write(f"${c[4]*c[2]:,.2f}")
                if col3.button("🗑️", key=f"dc_{c[0]}"): db.eliminar_compra(c[0]); st.rerun()

    with tab3:
        for s in db.obtener_salidas():
            with st.container(border=True):
                c1, c2, c3 = st.columns([2,1,1])
                c1.write(f"**{s[1]}** | {s[4]}"); c2.error(f"-{s[2]:g}")
                if c3.button("🗑️", key=f"ds_{s[0]}"): db.eliminar_salida(s[0]); st.rerun()

    # --- PESTAÑA 4: PRÉSTAMOS (MODIFICADA) ---
    with tab4:
        st.subheader("Control de Préstamos")
        
        # Filtro de visualización
        filtro = st.radio("Mostrar:", ["Solo Pendientes", "Todos"], horizontal=True)
        solo_pendientes = True if filtro == "Solo Pendientes" else False
        
        # Obtener lista filtrada
        lista_prestamos = db.obtener_prestamos(solo_pendientes=solo_pendientes)
        
        if not lista_prestamos:
            st.info("No hay préstamos que coincidan con el filtro.")
        else:
            for p in lista_prestamos:
                # p: 0:id, 1:item, 2:persona, 3:cant, 4:f_pres, 5:f_dev, 6:estado, 7:notas
                estado = p[6]
                color_estado = "green" if estado == "Devuelto" else "orange"
                
                with st.container(border=True):
                    col_info, col_status, col_del = st.columns([2, 1.5, 0.5])
                    
                    with col_info:
                        st.write(f"**{p[1]}** ({p[3]:g} unid.)")
                        st.write(f"👤 Presta a: **{p[2]}**")
                        st.caption(f"📅 Prestado: {p[4]} | 🔙 Devuelto: {p[5] if p[5] else '---'}")
                    
                    with col_status:
                        st.write(f"Estatus: :{color_estado}[{estado}]")
                        
                        # Botón de devolución (solo si está pendiente)
                        if estado == 'Pendiente':
                            if st.button("↩️ Devolver", key=f"dv_{p[0]}"):
                                # 1. Marcar como devuelto en la tabla prestamos
                                db.devolver_prestamo(p[0], str(date.today()))
                                
                                # 2. Regresar al inventario (crear entrada de ajuste)
                                ref = db.obtener_compras()
                                u_i = next((x[3] for x in ref if x[1] == p[1]), "Unid")
                                e_h = next((x[7] for x in ref if x[1] == p[1]), 0)
                                db.agregar_item(p[1], p[3], u_i, 0.0, str(date.today()), 0.0, e_h, f"Devolución de {p[2]}")
                                
                                st.success("Devuelto!")
                                st.rerun()
                    
                    with col_del:
                        if st.button("🗑️", key=f"dp_{p[0]}"):
                            db.eliminar_prestamo(p[0])
                            st.rerun()