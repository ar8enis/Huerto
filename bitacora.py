import streamlit as st
from datetime import date, datetime
import database as db
from streamlit_calendar import calendar

def calcular_urgencia(f):
    try:
        d = (datetime.strptime(f, "%Y-%m-%d").date() - date.today()).days
        return "red" if d <= 5 else "orange" if d <= 10 else "green"
    except: return "gray"

def mostrar_bitacora():
    st.title("📅 Bitácora")
    t1, t2, t3 = st.tabs(["⏳ Pendientes", "➕ Nueva", "📜 Historial"])

    lotes_registrados = [l[1] for l in db.obtener_terrenos()]

    with t2:
        if not lotes_registrados:
            st.warning("⚠️ Primero registra un terreno en el módulo 'Terreno'.")
        else:
            sug = db.obtener_nombres_actividades()
            c1, c2 = st.columns(2)
            act = c1.selectbox("Actividad:", list(set(["Abonar", "Fumigar", "Riego"] + sug + ["Otro"])))
            if act == "Otro": act = st.text_input("¿Cuál?")
            
            lote_sel = c2.selectbox("Terreno / Lote:", lotes_registrados)
            f_com = st.date_input("Fecha Programada")
            
            st.subheader(" Checklist Recursos")
            exist = db.obtener_existencias(); costos = db.obtener_costos_promedio()
            otros = db.obtener_otros_nombres_recursos()
            ops = ["👷 Peón", "👷🛠️ Especialista"] + [e[0] for e in exist] + otros + ["➕ Otro"]
            sel = st.multiselect("Recursos:", ops); recs = []
            
            for i in sel:
                with st.container(border=True):
                    c1, c2, c3 = st.columns(3)
                    if i == "➕ Otro":
                        n = c1.text_input("Nombre:"); q = c2.number_input("Cant", key=f"q{i}", value=1.0); c = c3.number_input("Costo", key=f"c{i}")
                        if n: recs.append((n, q, c, "Otro"))
                    elif "Peón" in i:
                        q = c1.number_input(f"Cant {i}", min_value=1, key=f"q{i}"); c = c2.number_input("Jornal", value=200.0, key=f"c{i}")
                        recs.append((i, q, c, "Mano Obra"))
                    else:
                        q = c1.number_input(f"Uso de {i}", min_value=0.1, key=f"q{i}"); c = c2.number_input("Costo", value=float(costos.get(i,0)), key=f"c{i}")
                        recs.append((i, q, c, "Insumo"))
            
            if st.button("Agendar"):
                db.agregar_evento(act, str(date.today()), str(f_com), "", recs, lote_sel)
                st.rerun()

    with t1:
        evs = db.obtener_eventos(estado="Pendiente")
        
        # Procesamos los eventos para el calendario de forma segura
        cevs = []
        for x in evs:
            # Evitamos el error de índice revisando si el lote existe en la tupla
            nombre_lote = x[7] if len(x) > 7 else "S/L"
            cevs.append({
                "title": f"{nombre_lote} - {x[1]}", 
                "start": x[3], 
                "color": "red" if calcular_urgencia(x[3])=="red" else "orange"
            })
        
        calendar(events=cevs)
        
        for e in evs:
            urg = calcular_urgencia(e[3]); em = "🔴" if urg=="red" else "🟡" if urg=="orange" else "🟢"
            lote_nombre = e[7] if len(e) > 7 else "Sin Lote"
            
            with st.container(border=True):
                c1, c2 = st.columns([3,1])
                with c1:
                    st.write(f"### {em} {e[1]}")
                    st.write(f"🚜 **Lote:** {lote_nombre} | 📅 **Fecha:** {e[3]}")
                    recs_e = db.obtener_recursos_evento(e[0])
                    for r in recs_e: st.caption(f"• {r[0]}: {r[1]:g}")
                if c2.button("✅", key=f"f{e[0]}"):
                    for r in recs_e:
                        if r[3] == "Insumo": db.registrar_salida(r[0], r[1], str(date.today()), lote_nombre, f"Tarea {e[1]}")
                    db.completar_evento_db(e[0], str(date.today())); st.rerun()

    with t3:
        for h in db.obtener_eventos(estado="Completado"):
            lote_h = h[7] if len(h) > 7 else "Sin Lote"
            with st.container(border=True):
                st.write(f"✅ {h[1]} en **{lote_h}** | Finalizado: {h[4]}")
                re = db.obtener_recursos_evento(h[0])
                st.caption(", ".join([f"{x[0]} ({x[1]:g})" for x in re]))