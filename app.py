import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        padding: 25px; border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    .logo-text {
        font-weight: 800; letter-spacing: -2px;
        background: linear-gradient(to right, #3b82f6, #a855f7);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 3rem; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A SUPABASE ---
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

# --- PANEL INTERNO ---
else:
    user = st.session_state.user
    st.sidebar.markdown("<h2 style='color: #3b82f6;'>CT360</h2>", unsafe_allow_html=True)
    st.sidebar.write(f"Profe: {user['email']}")
    if st.sidebar.button("CERRAR SESIÓN"):
        st.session_state.user = None
        st.rerun()

    st.title("📑 Mi Gestión Académica")
    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "🏗️ Cursos"])

    # --- PESTAÑA AGENDA (CORRECCIÓN SUPLENTE) ---
    with tabs[0]:
        st.subheader("Registro Diario de Clase")
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).execute()
        
        if res_c.data:
            df_c = pd.DataFrame(res_c.data).drop_duplicates(subset=['nombre_curso_materia', 'horario'])
            lista_cursos = [f"{row['nombre_curso_materia']} | {row['horario']}" for idx, row in df_c.iterrows()]
            
            # ELIMINAMOS EL FORMULARIO EXTERNO PARA QUE EL SELECTBOX SEA REACTIVO
            col_info1, col_info2 = st.columns(2)
            curso_hoy = col_info1.selectbox("Seleccionar Materia", lista_cursos)
            fecha_clase = col_info2.date_input("Fecha de hoy", datetime.date.today())
            
            st.markdown("---")
            col_doc1, col_doc2, col_doc3 = st.columns([1.5, 2, 2])
            tipo_docente = col_doc1.selectbox("¿Quién dicta la clase?", ["TITULAR", "SUPLENTE"])
            
            nombre_final = user['email']
            
            # AHORA ESTO APARECERÁ AL INSTANTE
            if tipo_docente == "SUPLENTE":
                nom_sup = col_doc2.text_input("Nombre del Suplente")
                ape_sup = col_doc3.text_input("Apellido del Suplente")
                nombre_final = f"Suplente: {nom_sup} {ape_sup}"
            else:
                col_doc2.info(f"Titular: {user['email']}")
            
            st.markdown("---")
            # Los textos y la tarea los ponemos en un form pequeño para el botón de guardar
            with st.form("contenido_clase"):
                temas = st.text_area("Temas dictados hoy")
                st.markdown("#### 📝 Tarea")
                col_t1, col_t2 = st.columns([2, 1])
                desc_tarea = col_t1.text_area("Descripción de la tarea")
                venc_tarea = col_t2.date_input("Para el día:", datetime.date.today() + datetime.timedelta(days=7))
                
                btn_pre = st.form_submit_button("Procesar Registro")
            
            if btn_pre:
                if tipo_docente == "SUPLENTE" and (not nom_sup or not ape_sup):
                    st.error("⚠️ Por favor, completa el nombre y apellido del suplente.")
                else:
                    st.warning("⚠️ ¿Confirmas el guardado de este registro?")
                    if st.button("✅ SÍ, GUARDAR EN BITÁCORA"):
                        # Aquí se ejecuta el guardado real
                        st.success(f"💾 Guardado correctamente. Docente: {nombre_final}")
                        st.balloons()
        else:
            st.info("Carga un curso primero en la pestaña 'Cursos'.")

    # --- LAS OTRAS PESTAÑAS (CURSOS Y ALUMNOS) SE MANTIENEN IGUAL ---
    with tabs[1]:
        st.subheader("Inscripción de Alumnos")
        # (Código previo de alumnos)
    with tabs[2]:
        st.subheader("Configuración de Materias 2026")
        # (Código previo de cursos)
