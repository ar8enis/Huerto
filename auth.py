import streamlit as st
from supabase import create_client, Client

# --- CONEXIÓN SEGURA A SUPABASE ---
def get_supabase_client():
    try:
        # Intenta leer de st.secrets (Cloud) o de lo que haya configurado
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("⚠️ Error de configuración: No se encontraron 'SUPABASE_URL' o 'SUPABASE_KEY' en los Secrets de Streamlit.")
        st.stop()

supabase = get_supabase_client()

def registrar_usuario(email, password):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            return True, "Registro exitoso. Revisa tu correo para confirmar."
        return False, "No se pudo crear el usuario."
    except Exception as e:
        err_msg = str(e).lower()
        if "already registered" in err_msg:
            return False, "Este correo ya tiene una cuenta."
        return False, f"Error: {str(e)}"

def iniciar_sesion(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return res.user
    except Exception as e:
        # Log interno para depuración
        print(f"Error login: {e}")
        return None

def recuperar_clave(email):
    try:
        supabase.auth.reset_password_for_email(email)
        return True
    except:
        return False

def cerrar_sesion():
    supabase.auth.sign_out()
    st.session_state.clear()
