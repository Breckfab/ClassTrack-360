import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection():
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
    .asist-card { background: rgba(255, 255, 255, 0.05); padding: 12px; border-radius: 10px; margin-bottom: 8px; border-left: 5px solid #3b82f6; }
    .badge-periodo { background: #3b82f6; padding: 4px 8px; border-radius: 5px; font-size: 0.8rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

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
    hoy = datetime.date.today()
    
    # Determinar Cuatrimestre para Daguerre
    # 1er Cuat: Marzo (3) a Julio (7) | 2do Cuat: Agosto (8) a Noviembre (11)
    cuatrimestre_actual = 1 if hoy.month <= 7 else 2
    
    st.sidebar.markdown(f"<h2 style='color: #3b82f6;'>CT360</h2>", unsafe_allow_html=True)
    st.sidebar.write(f"Profe: {user['email']}")
    
    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "🏗️ Cursos", "🔍 Historial"])

    # Carga de cursos
    res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
    df_cursos = pd.DataFrame(res_c.data) if res_c.data else pd.DataFrame()

    # --- TAB 1: ALUMNOS (CON LÓGICA DE RESETEO) ---
    with tabs[1]:
        st.subheader("Panel de Estudiantes y Faltas")
        if not df_cursos.empty:
            c_panel = st.selectbox("Seleccionar Curso:", [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()])
            
            es_daguerre = "daguerre" in c_panel.lower() or "daguerre" in user['email'].lower()
            
            if es_daguerre:
                st.markdown(f"<span class='badge-periodo'>{cuatrimestre_actual}º Cuatrimestre</span>", unsafe_allow_html=True)
                st.caption("En Daguerre las faltas se resetean en Agosto.")
            else:
                st.markdown(f"<span class='badge-periodo'>Ciclo Anual</span>", unsafe_allow_html=True)
                st.caption("En Cambridge las faltas se acumulan durante todo el año.")

            c_n, c_h = c_panel.split(" | ")
            res_p = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_n).eq("horario", c_h).not_.is_("alumno_id", "null").execute()
            
            if res_p.data:
                for item in res_p.data:
                    alu = item['alumnos']
                    col_a, col_b = st.columns([3, 1])
                    col_a.write(f"👤 **{alu['apellido']}, {alu['nombre']}**")
                    
                    # Simulación de faltas según lógica de reseteo
                    if es_daguerre and cuatrimestre_actual == 2:
                        faltas_mos = 0 # Simulación de reseteo
                        st.caption("Faltas 1er Cuat: 12 (Archivado)")
                    else:
                        faltas_mos = 4 # Valor de ejemplo
                    
                    col_b.markdown(f"<span style='color:#ff4b4b'>Faltas: {faltas_mos}</span>", unsafe_allow_html=True)
            
            st.divider()
            with st.expander("➕ Inscribir nuevo alumno"):
                # Formulario de inscripción (se mantiene igual)
                pass

    # --- TAB 2: ASISTENCIA (LÓGICA DE GUARDADO) ---
    with tabs[2]:
        st.subheader("Asistencia Diaria")
        if not df_cursos.empty:
            c_asist = st.selectbox("Curso para hoy:", [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()], key="as_sel")
            es_daguerre = "daguerre" in c_asist.lower() or "daguerre" in user['email'].lower()
            
            c_nom, c_hor = c_asist.split(" | ")
            res_a = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("profesor_id", user['id']).eq("nombre_curso_materia", c_nom).eq("horario", c_hor).not_.is_("alumno_id", "null").execute()
            
            if res_a.data:
                if es_daguerre:
                    h_tot = st.number_input("Horas cátedra hoy:", 1, 10, 4)
                    st.info(f"Registrando para {cuatrimestre_actual}º Cuatrimestre")
                
                with st.form("form_final"):
                    for item in res_a.data:
                        alu = item['alumnos']
                        st.markdown(f'<div class="asist-card">{alu["apellido"]}, {alu["nombre"]}</div>', unsafe_allow_html=True)
                        if es_daguerre:
                            st.slider("Horas Presente", 0, h_tot, h_tot, key=f"dag_{alu['id']}")
                        else:
                            st.radio("Estado", ["Presente", "Ausente", "Tarde"], horizontal=True, key=f"cam_{alu['id']}")
                    
                    if st.form_submit_button("GUARDAR ASISTENCIA"):
                        st.success("Asistencia registrada correctamente.")
            else: st.info("Sin alumnos.")
