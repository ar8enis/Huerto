import streamlit as st
import database as db
import auth
from inventario import mostrar_inventario
from terreno import mostrar_terreno
from bitacora import mostrar_bitacora
from finanzas import mostrar_finanzas
from notas import mostrar_notas # <--- NUEVA IMPORTACIÓN

# --- CONFIGURACIÓN ---
ADMIN_EMAIL = "tu_correo@gmail.com" # CAMBIA ESTO POR TU EMAIL

st.set_page_config(page_title="Huerto Manager Pro", layout="wide", page_icon="🍊")
db.crear_tablas()

# --- ESTADO DE SESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- INTERFAZ DE ACCESO (LOGIN / REGISTRO) ---
def pantalla_acceso():
    st.title("🍊 Huerto Manager Pro")
    tab_login, tab_registro, tab_reset = st.tabs(["Entrar", "Crear Cuenta", "Olvidé mi clave"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Correo electrónico")
            pw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Iniciar Sesión", use_container_width=True):
                user = auth.iniciar_sesion(email, pw)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.u_id = user.id
                    st.session_state.u_email = user.email
                    st.rerun()
                else:
                    st.error("Correo o contraseña incorrectos.")

    with tab_registro:
        st.write("Registra tu huerto para comenzar a gestionar.")
        with st.form("reg_form"):
            new_email = st.text_input("Correo electrónico")
            new_pw = st.text_input("Contraseña (mín 6 caracteres)", type="password")
            if st.form_submit_button("Registrarse", use_container_width=True):
                exito, msg = auth.registrar_usuario(new_email, new_pw)
                if exito: st.success(msg)
                else: st.error(msg)

    with tab_reset:
        st.write("Recupera el acceso a tu cuenta.")
        reset_email = st.text_input("Ingresa tu correo registrado")
        if st.button("Enviar link de recuperación"):
            if auth.recuperar_clave(reset_email):
                st.info("📨 Se ha enviado un link a tu correo para cambiar la clave.")
            else:
                st.error("No se pudo enviar el correo.")

# --- PANEL DE ADMINISTRADOR ---
def mostrar_admin():
    st.title("🛡️ Panel de Control Administrativo")
    st.write("Bienvenido, Administrador.")
    st.info("Como administrador, tienes acceso a la gestión de usuarios y permisos del sistema.")

# --- LÓGICA PRINCIPAL ---
if not st.session_state.logged_in:
    pantalla_acceso()
else:
    u_id = st.session_state.u_id
    u_email = st.session_state.u_email

    with st.sidebar:
        st.title("🍊 Huerto Pro")
        st.write(f"👤 {u_email}")
        
        # AÑADIDO "📸 Notas" AL MENÚ
        menu_options = ["🏠 Dashboard", "📦 Inventario", "🚜 Terreno", "📅 Bitácora", "📸 Notas", "💰 Finanzas"]
        if u_email == ADMIN_EMAIL:
            menu_options.append("🛡️ Admin")
            
        menu = st.radio("Menú", menu_options)
        
        if st.button("Cerrar Sesión"):
            auth.cerrar_sesion()
            st.rerun()

    if menu == "🏠 Dashboard":
        st.title(f"Tablero de Control - {u_email}")
        c, o, v = db.calcular_resumen_financiero(u_id)
        val_b = db.obtener_valor_total_bodega(u_id)
        lotes = db.obtener_terrenos(u_id)
        total_arb = sum(l[3] for l in lotes)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Árboles Totales", f"{total_arb} 🌳")
        col2.metric("Inversión Bodega", f"${val_b:,.2f}")
        col3.metric("Gastos Operación", f"${o:,.2f}")
        col4.metric("Ventas", f"${v:,.2f}", delta=f"${v-(c+o):,.2f} Balance")

        st.divider()
        st.subheader("Tareas Próximas")
        pendientes = db.obtener_eventos(u_id, estado="Pendiente")[:3]
        if pendientes:
            for p in pendientes: st.write(f"🔔 **{p[2]}** en {p[8]} (Vence: {p[4]})")
        else: st.write("Todo al día.")

    elif menu == "📦 Inventario": mostrar_inventario(u_id)
    elif menu == "🚜 Terreno": mostrar_terreno(u_id)
    elif menu == "📅 Bitácora": mostrar_bitacora(u_id)
    elif menu == "📸 Notas": mostrar_notas(u_id) # <--- LÓGICA PARA MOSTRAR NOTAS
    elif menu == "💰 Finanzas": mostrar_finanzas(u_id)
    elif menu == "🛡️ Admin": mostrar_admin()
