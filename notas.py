import streamlit as st
from datetime import date
import database as db
from streamlit_calendar import calendar

def mostrar_notas():
    st.title("📸 Notas y Fotos")
    t1, t2 = st.tabs(["📂 Historial", "📝 Nueva"])

    with t2:
        with st.form("fn"):
            f = st.date_input("Fecha"); tit = st.text_input("Título"); con = st.text_area("Contenido")
            pts = st.file_uploader("Fotos:", accept_multiple_files=True)
            if st.form_submit_button("Guardar"):
                bins = [x.read() for x in pts]
                db.guardar_nota_con_fotos(tit, con, str(f), bins); st.rerun()

    with t1:
        ms = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        c1, c2 = st.columns(2); m_n = c1.selectbox("Mes", ms, index=date.today().month-1); a_s = c2.number_input("Año", value=date.today().year)
        m_u = ms.index(m_n)+1
        nts = db.obtener_notas_filtradas(m_u, a_s)
        for n in nts:
            with st.expander(f"📅 {n[3]} - {n[1]}"):
                st.write(n[2])
                imgs = db.obtener_fotos_de_nota(n[0])
                cols = st.columns(3)
                for i, img in enumerate(imgs): cols[i%3].image(img)
                if st.button("Eliminar", key=f"dn{n[0]}"): db.eliminar_nota_campo(n[0]); st.rerun()