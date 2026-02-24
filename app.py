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

# --- ESTILO CSS PARA ALERTAS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.5rem; text-align: center; margin-bottom: 20px; }
    
    /* Estilos del Semáforo */
    .riesgo-bajo { color: #4ade80; font-weight: bold; }
    .riesgo-medio { color: #fbbf24; font-weight: bold; }
    .riesgo-alto { color: #ef4444; font-weight: bold; text-transform: uppercase; }
    
    .alumno-card { 
        background: rgba(255, 255, 255, 0.05); 
        padding: 15px; 
        border-radius: 12px; 
        margin-bottom: 10px; 
        border: 1px solid rgba(255,255,255,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (Simplificado para el ejemplo) ---
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
                else: st.error("Error de acceso.")

else:
    user = st.session_state.user
    hoy = datetime.date.today()
    cuatrimestre_actual = 1 if hoy.month <= 7 else 2
    
    st.sidebar.title("CT360")
    st.sidebar.write(f"Profe: {user['email']}")
    
    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "🏗️ Cursos", "🔍 Historial"])

    # Carga de cursos
    res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
    df_cursos = pd.DataFrame(res_c.data) if res_c.data else pd.DataFrame()

    # --- TAB 1: ALUMNOS (CON SEMÁFORO DE ALERTAS) ---
    with tabs[1]:
        st.subheader("Estado Académico de Alumnos")
        if not df_cursos.empty:
            c_panel = st.selectbox("Curso:", [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()])
            es_daguerre = "daguerre" in c_panel.lower() or "daguerre" in user['email'].lower()
            
            c_n, c_h = c_panel.split(" | ")
            res_p = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_n).eq("horario", c_h).not_.is_("alumno_id", "null").execute()
            
            if res_p.data:
                st.write("---")
                for item in res_p.data:
                    alu = item['alumnos']
                    
                    # LÓGICA DE ALERTAS (Simulada con valores de ejemplo para probar el visual)
                    # En una fase final, esto vendría de un COUNT(*) en la base de datos
                    faltas_acumuladas = 16 if "Pérez" in alu['apellido'] else 5 
                    
                    # Definición de color
                    clase_css = "riesgo-bajo"
                    if faltas_acumuladas >= 15: clase_css = "riesgo-alto"
                    elif faltas_acumuladas >= 10: clase_css = "riesgo-medio"
                    
                    # Mostrar Card del Alumno
                    with st.container():
                        col_info, col_faltas = st.columns([3, 1])
                        col_info.markdown(f"""
                            <div class='alumno-card'>
                                👤 <b>{alu['apellido']}, {alu['nombre']}</b>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        label_unidad = "hs" if es_daguerre else "días"
                        col_faltas.markdown(f"<div style='padding-top:20px;'><span class='{clase_css}'>{faltas_acumuladas} {label_unidad}</span></div>", unsafe_allow_html=True)
                        
                        if faltas_acumuladas >= 15:
                            st.error(f"⚠️ ATENCIÓN: El alumno {alu['nombre']} ha superado el límite permitido.")
            
            st.divider()
            # Botón para descargar reporte rápido
            st.button(f"Generar Reporte de Alertas ({c_n})")

    # --- TAB 2: ASISTENCIA (SE MANTIENE IGUAL) ---
    with tabs[2]:
        st.subheader("Toma de Asistencia")
        # ... (código de asistencia anterior)

    # --- TAB 0: AGENDA (SE MANTIENE IGUAL) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        # ... (código de agenda anterior)
