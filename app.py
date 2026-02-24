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
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""<div style="text-align: center;"><svg viewBox="0 0 120 80" width="150"><defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style="stop-color:#3b82f6;"/><stop offset="100%" style="stop-color:#a855f7;"/></linearGradient></defs><path d="M10 40 Q 60 0 110 40 Q 60 80 10 40" fill="none" stroke="url(#g)" stroke-width="3" /><circle cx="60" cy="40" r="18" fill="rgba(59, 130, 246, 0.1)" stroke="url(#g)" stroke-width="2" /><text x="60" y="44" font-family="Arial" font-weight="800" font-size="10" fill="white" text-anchor="middle">360</text></svg></div>""", unsafe_allow_html=True)
        st.markdown("<div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
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
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()

    st.title("📑 Mi Gestión Académica")
    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "🏗️ Cursos"])

    # --- PESTAÑA AGENDA (BITÁCORA REAL) ---
    with tabs[0]:
        st.subheader("Registro de Clase Diaria")
        
        # Traer cursos creados para el selector
        res_cursos = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).execute()
        
        if res_cursos.data:
            df_cursos = pd.DataFrame(res_cursos.data).drop_duplicates(subset=['nombre_curso_materia', 'horario'])
            lista_cursos = [f"{row['nombre_curso_materia']} | {row['horario']}" for _, row in df_cursos.iterrows()]
            
            with st.form("form_bitacora"):
                col_c1, col_c2 = st.columns(2)
                seleccion_curso = col_c1.selectbox("Seleccionar Materia", lista_cursos)
                fecha_clase = col_c2.date_input("Fecha de hoy", datetime.date.today())
                
                st.markdown("---")
                col_d1, col_d2, col_d3 = st.columns([1.5, 2, 2])
                es_suplente = col_d1.selectbox("¿Quién dicta la clase?", ["TITULAR", "SUPLENTE"])
                
                nombre_doc = user['email']
                if es_suplente == "SUPLENTE":
                    nom_sup = col_d2.text_input("Nombre Suplente")
                    ape_sup = col_d3.text_input("Apellido Suplente")
                    nombre_doc = f"Suplente: {nom_sup} {ape_sup}"
                else:
                    col_d2.info(f"Titular: {user['email']}")
                
                st.markdown("---")
                temas_dictados = st.text_area("Temas de hoy (Bitácora)", placeholder="Escriba los contenidos vistos...")
                
                st.markdown("#### 📝 Tarea Asignada")
                col_t1, col_t2 = st.columns([2, 1])
                descripcion_tarea = col_t1.text_area("¿Qué tarea queda?", placeholder="Detalle la tarea...")
                fecha_vencimiento = col_t2.date_input("Para el día:", datetime.date.today() + datetime.timedelta(days=7))
                
                submit_prep = st.form_submit_button("Preparar Guardado")

            if submit_prep:
                st.warning("⚠️ ¿Confirmas el guardado de este registro en la bitácora?")
                if st.button("✅ SÍ, GUARDAR EN LA NUBE"):
                    # Buscamos el ID del curso seleccionado
                    c_nombre = seleccion_curso.split(" | ")[0]
                    c_horario = seleccion_curso.split(" | ")[1]
                    curso_id = df_cursos[(df_cursos['nombre_curso_materia'] == c_nombre) & (df_cursos['horario'] == c_horario)]['id'].values[0]
                    
                    datos_clase = {
                        "curso_id": int(curso_id),
                        "profesor_id": user['id'],
                        "fecha": str(fecha_clase),
                        "docente_nombre": nombre_doc,
                        "temas": temas_dictados,
                        "tarea_descripcion": descripcion_tarea,
                        "tarea_vencimiento": str(fecha_vencimiento)
                    }
                    
                    try:
                        supabase.table("bitacora").insert(datos_clase).execute()
                        st.success("✅ Registro guardado con éxito en la base de datos.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

        else:
            st.info("Primero debés crear un curso en la pestaña 'Cursos'.")

    # (Las pestañas de Alumnos y Cursos se mantienen con el código que ya validamos)
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        # ... (código previo de alumnos)
    with tabs[2]:
        st.subheader("Gestión de Cursos")
        # ... (código previo de cursos)
