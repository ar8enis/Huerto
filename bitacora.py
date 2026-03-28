import streamlit as st
from datetime import date, datetime
import database as db
from streamlit_calendar import calendar

def calcular_urgencia(f):
    try:
        # Convertimos la fecha de compromiso (YYYY-MM-DD) a objeto date para comparar
        d = (datetime.strptime(f, "%Y-%m-%d").date() - date.today()).days
        return "red" if d <= 5 else "orange" if d <= 10 else "green"
    except: return "gray"

def mostrar_bitacora(u_id):
    st.title("📅 Bitácora de Actividades")
    t1, t2, t3 = st.tabs(["⏳ Tareas Pendientes", "➕ Nueva Actividad", "📜 Historial"])

    # Obtenemos terrenos filtrados por usuario. Índice 2 es el nombre del lote
    lotes_raw = db.obtener_terrenos(u_id)
    lotes_registrados = [l[2] for l in lotes_raw]

    # --- TAB 2: NUEVA ACTIVIDAD ---
    with t2:
        if not lotes_registrados:
            st.warning("⚠️ Primero registra un terreno en el módulo 'Terreno' para poder asignar tareas.")
        else:
            sug = db.obtener_nombres_actividades(u_id)
            c1, c2 = st.columns(2)
            act = c1.selectbox("Actividad:", list(set(["Abonar", "Fumigar", "Riego", "Poda", "Cosecha"] + sug + ["Otro"])))
            if act == "Otro": act = st.text_input("¿Cuál actividad?")
            
            lote_sel = c2.selectbox("Terreno / Lote destino:", lotes_registrados)
            f_com = st.date_input("Fecha Programada para realizar")
            
            st.subheader("📋 Checklist de Recursos")
            exist = db.obtener_existencias(u_id) # (nombre, unidad, stock)
            costos = db.obtener_costos_promedio(u_id)
            otros = db.obtener_otros_nombres_recursos()
            
            ops = ["👷 Peón", "👷🛠️ Especialista"] + [e[0] for e in exist] + otros + ["➕ Otro"]
            sel = st.multiselect("Recursos necesarios para este día:", ops)
            recs = []
            
            for i in sel:
                with st.container(border=True):
                    c1_r, c2_r, c3_r = st.columns(3)
                    if i == "➕ Otro":
                        n = c1_r.text_input("Nombre del recurso:"); q = c2_r.number_input("Cant", key=f"q{i}", value=1.0); c = c3_r.number_input("Costo unitario", key=f"c{i}")
                        if n: recs.append((n, q, c, "Otro"))
                    elif "Peón" in i:
                        q = c1_r.number_input(f"Cant {i}", min_value=1, key=f"q{i}"); c = c2_r.number_input("Jornal/Pago", value=200.0, key=f"c{i}")
                        recs.append((i, q, c, "Mano Obra"))
                    else:
                        # Buscar stock disponible
                        stock_disp = next((e[2] for e in exist if e[0] == i), 0.0)
                        q = c1_r.number_input(f"Uso de {i} (Disp: {stock_disp:g})", min_value=0.1, max_value=float(stock_disp) if stock_disp > 0 else 0.1, key=f"q{i}")
                        c = c2_r.number_input("Costo estimado", value=float(costos.get(i,0)), key=f"c{i}")
                        recs.append((i, q, c, "Insumo"))
            
            if st.button("📅 Agendar Actividad", use_container_width=True):
                if act:
                    for r in recs:
                        if r[3] == "Otro": db.guardar_nuevo_nombre_recurso(r[0])
                    db.agregar_evento(u_id, act, str(date.today()), str(f_com), "", recs, lote_sel)
                    st.success(f"Actividad '{act}' agendada.")
                    st.rerun()

    # --- TAB 1: PENDIENTES ---
    with t1:
        evs = db.obtener_eventos(u_id, estado="Pendiente")
        
        # Índices de tabla bitacora multi-usuario:
        # 0:id, 1:u_id, 2:act, 3:f_creada, 4:f_compromiso, 5:f_comp, 6:est, 7:notas, 8:lote
        
        cevs = []
        for x in evs:
            l_name = x[8] if len(x) > 8 else "S/L"
            color = calcular_urgencia(x[4])
            cevs.append({
                "title": f"{l_name} - {x[2]}", 
                "start": x[4], 
                "color": "#dc3545" if color == "red" else "#ffc107" if color == "orange" else "#28a745"
            })
        
        if cevs:
            calendar(events=cevs)
        
        st.subheader("Lista de Tareas")
        for e in evs:
            urg = calcular_urgencia(e[4])
            em = "🔴" if urg=="red" else "🟡" if urg=="orange" else "🟢"
            l_nombre = e[8] if len(e) > 8 else "Sin Lote"
            
            with st.container(border=True):
                c1, c2 = st.columns([3,1])
                with c1:
                    st.write(f"### {em} {e[2]}")
                    st.write(f"🚜 **Lote:** {l_nombre} | 📅 **Para el:** {e[4]}")
                    recs_e = db.obtener_recursos_evento(e[0])
                    for r in recs_e: 
                        st.caption(f"• {r[0]}: {r[1]:g} (${r[2]:,.2f} c/u)")
                
                if c2.button("✅ Terminar", key=f"f{e[0]}"):
                    for r in recs_e:
                        if r[3] == "Insumo": 
                            db.registrar_salida(u_id, r[0], r[1], str(date.today()), l_nombre, f"Tarea {e[2]}")
                    db.completar_evento_db(e[0], str(date.today()))
                    st.rerun()

    # --- TAB 3: HISTORIAL ---
    with t3:
        hist = db.obtener_eventos(u_id, estado="Completado")
        if not hist:
            st.info("No hay actividades completadas todavía.")
        for h in hist:
            l_h = h[8] if len(h) > 8 else "Sin Lote"
            with st.container(border=True):
                st.write(f"✅ **{h[2]}** en **{l_h}**")
                st.caption(f"Programado: {h[4]} | Finalizado: {h[5]}")
                re_h = db.obtener_recursos_evento(h[0])
                if re_h:
                    st.write("Recursos usados:")
                    st.caption(", ".join([f"{x[0]} ({x[1]:g})" for x in re_h]))
