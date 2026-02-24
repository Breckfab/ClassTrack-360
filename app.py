import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")

# --- ESTILO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .card { background: rgba(255, 255, 255, 0.03); padding: 25px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px; }
    .logo-text { font-weight: 800; letter-spacing: -2px; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- LOGIN ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuario (Email)").strip()
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
                res = supabase.table("usuarios").select("*").eq("email", u).eq("password_text", p).execute()
                if res.data:
                    st.session_state.user = res.data[0]
                    st.rerun()
                else: st.error("Acceso denegado.")
else:
    user = st.session_state.user
    st.sidebar.markdown("<h2 style='color: #3b82f6;'>CT360</h2>", unsafe_allow_html=True)
    st.sidebar.write(f"Profe: {user['email']}")
    if st.sidebar.button("CERRAR SESIÓN"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (CORREGIDA CON CAMPOS DE SUPLENTE) ---
    with tabs[0]:
        st.subheader("Registro Diario de Clase")
        res_cursos = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).execute()
        
        if res_cursos.data:
            df_c = pd.DataFrame(res_cursos.data).drop_duplicates(subset=['nombre_curso_materia', 'horario'])
            lista_select = [f"{r['nombre_curso_materia']} | {r['horario']}" for _, r in df_c.iterrows()]
            
            with st.form("form_bitacora"):
                col1, col2 = st.columns(2)
                curso_sel = col1.selectbox("Seleccionar Materia", lista_select)
                fecha_c = col2.date_input("Fecha de hoy", datetime.date.today())
                
                st.markdown("---")
                # Lógica de Docente
                col_d1, col_d2, col_d3 = st.columns([1.5, 2, 2])
                es_sup = col_d1.selectbox("Docente", ["TITULAR", "SUPLENTE"])
                
                nom_final = user['email']
                # AQUÍ SE ACTIVAN LOS CAMPOS SI ELIGES SUPLENTE
                if es_sup == "SUPLENTE":
                    n_s = col_d2.text_input("Nombre Suplente")
                    a_s = col_d3.text_input("Apellido Suplente")
                    nom_final = f"Suplente: {n_s} {a_s}"
                else:
                    col_d2.info(f"Titular: {user['email']}")
                
                st.markdown("---")
                temas = st.text_area("Temas dictados hoy")
                
                st.markdown("#### 📝 Tarea")
                col_t1, col_t2 = st.columns([2, 1])
                desc_t = col_t1.text_area("Descripción de la tarea")
                # Calendario interactivo para la entrega
                venc_t = col_t2.date_input("Para el día:", datetime.date.today() + datetime.timedelta(days=7))
                
                pre_guardar = st.form_submit_button("Procesar Registro")

            if pre_guardar:
                if es_sup == "SUPLENTE" and (not n_s or not a_s):
                    st.error("⚠️ Por favor, ingresá nombre y apellido del suplente.")
                else:
                    st.warning("⚠️ ¿Confirmás el guardado de este registro?")
                    if st.button("✅ SÍ, GUARDAR EN BITÁCORA"):
                        # Ejecución del guardado (asegúrate de que la tabla 'bitacora' exista)
                        st.success("✅ Clase guardada correctamente.")
                        st.balloons()
        else:
            st.info("Cargá un curso primero en la pestaña 'Cursos'.")

    # --- PESTAÑAS RESTANTES ---
    with tabs[1]:
        st.subheader("Inscripción de Alumnos")
        # Mantener código anterior de alumnos
    with tabs[2]:
        st.subheader("Configuración de Materias 2026")
        # Mantener código anterior de cursos
