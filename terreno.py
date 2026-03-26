import streamlit as st
import database as db

def mostrar_terreno():
    st.title("🚜 Gestión de Terrenos")
    
    t1, t2 = st.tabs(["📋 Mis Lotes", "➕ Nuevo Terreno"])

    with t2:
        with st.form("form_terreno", clear_on_submit=True):
            nom = st.text_input("Nombre del Lote (Ej: Sector Norte)")
            var = st.selectbox("Variedad de Naranja", ["Valencia", "Navel", "Salustiana", "Otro"])
            c1, c2, c3 = st.columns(3)
            arb = c1.number_input("Nº Árboles", min_value=1)
            sup = c2.number_input("Superficie", min_value=0.1)
            uni = c3.selectbox("Unidad", ["Hectáreas", "Metros²", "Tareas"])
            
            if st.form_submit_button("Guardar Terreno"):
                if nom:
                    db.agregar_terreno(nom, var, arb, sup, uni)
                    st.success("Terreno registrado.")
                    st.rerun()

    with t1:
        lotes = db.obtener_terrenos()
        if not lotes:
            st.info("No hay terrenos registrados.")
        else:
            total_arboles = sum(l[3] for l in lotes)
            st.metric("Total Árboles en el Huerto", f"{total_arboles} 🌳")
            st.divider()
            
            for l in lotes:
                id_t, nombre, variedad, arboles, superficie, unidad = l
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.write(f"### {nombre}")
                        st.write(f"🍊 Variedad: **{variedad}** | 🌳 Árboles: **{arboles}**")
                        st.caption(f"📐 Tamaño: {superficie} {unidad}")
                    
                    with c2:
                        if st.button("✏️", key=f"ed_{id_t}"):
                            st.session_state[f"editando_{id_t}"] = True
                    
                    with c3:
                        if st.button("🗑️", key=f"del_{id_t}"):
                            db.eliminar_terreno(id_t)
                            st.rerun()
                
                # Formulario de edición simple si se pulsa el lápiz
                if st.session_state.get(f"editando_{id_t}", False):
                    with st.form(f"edit_f_{id_t}"):
                        n_arb = st.number_input("Nuevo número de árboles", value=arboles)
                        n_nom = st.text_input("Nuevo nombre", value=nombre)
                        if st.form_submit_button("Actualizar"):
                            db.actualizar_terreno(id_t, n_nom, variedad, n_arb, superficie, unidad)
                            st.session_state[f"editando_{id_t}"] = False
                            st.rerun()