import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection():
    # Credenciales de tu proyecto
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: 
    st.session_state.user = None

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.5rem; text-align: center; margin-bottom: 20px; }
    .confirm-box { padding: 15px; border: 1px solid #ff4b4b; border-radius: 10px; background-color: rgba(255, 75, 75, 0.1); margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN SIMPLIFICADO ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        with st.form("login_form"):
            # Ahora aceptamos alias cortos
            u_input = st.text_input("Institución (Cambridge / Daguerre)").strip().lower()
            p = st.text_input("Contraseña", type="password")
            
            if st.form_submit_button("Ingresar"):
                # Mapeo de nombres cortos a correos reales
                email_real = ""
                if u_input == "cambridge":
                    email_real = "cambridge.fabianbelledi@gmail.com"
                elif u_input == "daguerre":
                    email_real = "daguerre.fabianbelledi@gmail.com"
                
                if email_real != "":
                    try:
                        res = supabase.table("usuarios").select("*").eq("email", email_real).eq("password_text", p).execute()
                        if res.data:
                            st.session_state.user = res.data[0]
                            st.rerun()
                        else:
                            st.error("Contraseña incorrecta para esa institución.")
                    except Exception as e:
                        st.error("Error crítico de conexión. Reintentando...")
                else:
                    st.error("Institución no reconocida. Usá 'Cambridge' o 'Daguerre'.")

else:
    user = st.session_state.user
    st.sidebar.write(f"Sede: {'Cambridge' if 'cambridge' in user['email'] else 'Daguerre'}")
    if st.sidebar.button("CERRAR SESIÓN"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- CONSULTA DE CURSOS (CON PROTECCIÓN CONTRA PANTALLA NEGRA) ---
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data:
            df_cursos = pd.DataFrame(res_c.data)
    except:
        pass # Evita que la app se ponga negra si la tabla está vacía

    # --- TAB ALUMNOS (ARREGLADO) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if not df_cursos.empty:
            with st.form("form_ins_alu", clear_on_submit=True):
                opciones = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()]
                c_sel = st.selectbox("Asignar a Curso", opciones)
                nom_a = st.text_input("Nombre")
                ape_a = st.text_input("Apellido")
                if st.form_submit_button("Inscribir"):
                    if nom_a and ape_a:
                        st.session_state.confirm_alu = {"nom": nom_a, "ape": ape_a, "curso": c_sel}
            
            if st.session_state.get('confirm_alu'):
                d = st.session_state.confirm_alu
                st.warning(f"¿Confirmás inscribir a {d['nom']} {d['ape']}?")
                if st.button("✅ SÍ, INSCRIBIR"):
                    try:
                        nuevo = supabase.table("alumnos").insert({"nombre": d['nom'], "apellido": d['ape']}).execute()
                        c_n, c_h = d['curso'].split(" | ")
                        supabase.table("inscripciones").insert({
                            "alumno_id": nuevo.data[0]['id'], 
                            "profesor_id": user['id'], 
                            "nombre_curso_materia": c_n, 
                            "horario": c_h, 
                            "anio_lectivo": 2026
                        }).execute()
                        del st.session_state.confirm_alu
                        st.success("Alumno inscrito exitosamente.")
                        st.rerun()
                    except:
                        st.error("Error al guardar. Verificá la conexión.")
        else:
            st.info("Primero cargá una materia en la pestaña 'Cursos'.")

    # --- TAB CURSOS (PARA LIMPIAR REPETIDOS) ---
    with tabs[4]:
        st.subheader("Tus Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows():
                col1, col2 = st.columns([4, 1])
                col1.write(f"📘 **{cur['nombre_curso_materia']}** ({cur['horario']})")
                if col2.button("Borrar", key=f"del_{cur['id']}"):
                    supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                    st.rerun()
        
        with st.form("nuevo_c"):
            st.write("➕ Añadir Materia")
            nc = st.text_input("Nombre")
            hc = st.text_input("Horario")
            if st.form_submit_button("Añadir"):
                supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                st.rerun()
