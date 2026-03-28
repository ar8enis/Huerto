import streamlit as st
from datetime import date, datetime
import database as db
from streamlit_calendar import calendar

def mostrar_notas(u_id):
    st.title("📸 Notas y Evidencias de Campo")
    
    tab_ver, tab_nueva = st.tabs(["📂 Historial Mensual", "📝 Nueva Nota"])

    # --- TAB: NUEVA NOTA ---
    with tab_nueva:
        st.subheader("Registrar hallazgo o comentario")
        with st.form("form_nota", clear_on_submit=True):
            f_n = st.date_input("Fecha de la nota:", value=date.today())
            tit_n = st.text_input("Título (ej: Plaga detectada, Inicio de cosecha...)")
            con_n = st.text_area("Descripción detallada:")
            
            fotos = st.file_uploader("Subir fotos de evidencia:", 
                                   type=['png', 'jpg', 'jpeg'], 
                                   accept_multiple_files=True)
            
            if st.form_submit_button("Guardar Nota"):
                if tit_n:
                    lista_binarios = [x.read() for x in fotos]
                    db.guardar_nota_con_fotos(u_id, tit_n, con_n, str(f_n), lista_binarios)
                    st.success("✅ Nota guardada correctamente.")
                    st.rerun()
                else:
                    st.error("Por favor, agrega un título.")

    # --- TAB: HISTORIAL ---
    with tab_ver:
        # 1. Filtros de búsqueda
        col_m, col_a = st.columns(2)
        ms_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        mes_sel = col_m.selectbox("Mes:", ms_nombres, index=date.today().month-1)
        anio_sel = col_a.number_input("Año:", min_value=2020, max_value=2030, value=date.today().year)
        
        mes_num = ms_nombres.index(mes_sel) + 1

        # 2. Calendario Ocultable
        with st.expander("📅 Ver Calendario de este mes", expanded=False):
            todas = db.obtener_notas_campo(u_id)
            evs_cal = []
            for n in todas:
                # Índices: 0:id, 1:u_id, 2:titulo, 3:contenido, 4:fecha
                evs_cal.append({
                    "title": f"📷 {n[2]}",
                    "start": n[4],
                    "color": "#3498db"
                })
            
            calendar(events=evs_cal, options={
                "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
                "initialDate": f"{anio_sel}-{mes_num:02d}-01"
            })

        st.divider()

        # 3. Listado de Notas (Filtradas por mes y año)
        notas_filtradas = db.obtener_notas_filtradas(u_id, mes_num, anio_sel)
        
        if not notas_filtradas:
            st.info(f"No hay notas registradas para {mes_sel} {anio_sel}.")
        else:
            for n in notas_filtradas:
                # n: 0:id, 1:u_id, 2:titulo, 3:contenido, 4:fecha
                fecha_bonita = datetime.strptime(n[4], "%Y-%m-%d").strftime("%d/%m/%Y")
                
                with st.expander(f"📅 {fecha_bonita} - {n[2]}"):
                    c_txt, c_del = st.columns([4, 1])
                    c_txt.write(n[3])
                    
                    if c_del.button("🗑️ Eliminar", key=f"del_nota_{n[0]}"):
                        db.eliminar_nota_campo(n[0])
                        st.rerun()
                    
                    # Mostrar fotos
                    imagenes = db.obtener_fotos_de_nota(n[0])
                    if imagenes:
                        st.write("---")
                        cols = st.columns(3)
                        for idx, img in enumerate(imagenes):
                            with cols[idx % 3]:
                                st.image(img, use_container_width=True)
