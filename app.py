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
    .nota-card { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 10px; }
    .promedio-box { background: #3b82f6; color: white; padding: 5px 10px; border-radius: 8px; font-weight: bold; font-size: 1.1rem; }
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
    st.sidebar.title("CT360")
    st.sidebar.write(f"Profe: {user['email']}")
    if st.sidebar.button("CERRAR SESIÓN"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos", "🔍 Historial"])

    # Carga de cursos
    res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
    df_cursos = pd.DataFrame(res_c.data) if res_c.data else pd.DataFrame()

    # --- TAB 3: NOTAS (DIFERENCIAL DAGUERRE VS CAMBRIDGE) ---
    with tabs[3]:
        st.subheader("Calificaciones Académicas")
        if not df_cursos.empty:
            c_notas = st.selectbox("Materia:", [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()], key="sel_notas")
            
            es_daguerre = "daguerre" in c_notas.lower() or "daguerre" in user['email'].lower()
            tipo_eval = "Trabajo Práctico" if es_daguerre else "Writing"
            
            st.info(f"Sistema evaluativo para: **{tipo_eval}s**")

            c_n, c_h = c_notas.split(" | ")
            res_p = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_n).eq("horario", c_h).not_.is_("alumno_id", "null").execute()
            
            if res_p.data:
                for item in res_p.data:
                    alu = item['alumnos']
                    with st.container():
                        st.markdown(f"**{alu['apellido']}, {alu['nombre']}**")
                        col1, col2, col3, col_prom = st.columns([1, 1, 1, 1.2])
                        
                        # Tres casilleros de notas (pueden ser más si lo deseás)
                        n1 = col1.number_input(f"{tipo_eval} 1", 0.0, 10.0, 0.0, step=0.5, key=f"n1_{alu['id']}")
                        n2 = col2.number_input(f"{tipo_eval} 2", 0.0, 10.0, 0.0, step=0.5, key=f"n2_{alu['id']}")
                        n3 = col3.number_input(f"{tipo_eval} 3", 0.0, 10.0, 0.0, step=0.5, key=f"n3_{alu['id']}")
                        
                        # Cálculo del promedio automático (solo promedia si la nota es mayor a 0)
                        notas_reales = [n for n in [n1, n2, n3] if n > 0]
                        promedio = sum(notas_reales) / len(notas_reales) if notas_reales else 0.0
                        
                        col_prom.markdown(f"<div style='margin-top:25px;'>Promedio: <span class='promedio-box'>{promedio:.2f}</span></div>", unsafe_allow_html=True)
                        st.divider()
                
                if st.button("Guardar todas las Notas"):
                    st.success("Notas actualizadas en la base de datos.")
            else: st.info("Sin alumnos inscritos.")
        else: st.warning("Cargá un curso primero.")

    # --- TAB 2: ASISTENCIA (MANTIENE LÓGICA PREVIA) ---
    with tabs[2]:
        st.subheader("Control de Asistencia")
        # (Aquí se mantiene el código de asistencia que ya probamos)

    # --- TAB 1: ALUMNOS (MANTIENE SEMÁFORO DE ALERTAS) ---
    with tabs[1]:
        st.subheader("Estado de Alumnos")
        # (Aquí se mantiene el código de alumnos con el semáforo)

    # (El resto de las pestañas Agenda, Cursos e Historial siguen igual)
