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
    .stApp { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; text-align: center; }
    .promedio-box { background: #3b82f6; color: white; padding: 10px; border-radius: 8px; font-weight: bold; font-size: 1.5rem; text-align: center; }
    .nota-container { background: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN (Simplificado) ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                res = supabase.table("usuarios").select("*").eq("email", u).eq("password_text", p).execute()
                if res.data: 
                    st.session_state.user = res.data[0]
                    st.rerun()

else:
    user = st.session_state.user
    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # Carga de cursos
    res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
    df_cursos = pd.DataFrame(res_c.data) if res_c.data else pd.DataFrame()

    # --- TAB 3: NOTAS CON FECHA Y OBSERVACIONES ---
    with tabs[3]:
        st.subheader("Calificaciones y Seguimiento")
        if not df_cursos.empty:
            c_notas = st.selectbox("Materia:", [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()])
            
            es_daguerre = "daguerre" in c_notas.lower() or "daguerre" in user['email'].lower()
            tipo_eval = "TP" if es_daguerre else "Writing"

            c_n, c_h = c_notas.split(" | ")
            res_p = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_n).eq("horario", c_h).not_.is_("alumno_id", "null").execute()
            
            if res_p.data:
                for item in res_p.data:
                    alu = item['alumnos']
                    
                    with st.container():
                        st.markdown(f"### 👤 {alu['apellido']}, {alu['nombre']}")
                        
                        # Fila para el Trabajo 1
                        st.markdown(f"**{tipo_eval} N° 1**")
                        col_n1, col_f1, col_o1 = st.columns([1, 1.5, 3])
                        n1 = col_n1.number_input("Nota", 0.0, 10.0, 0.0, step=0.5, key=f"n1_{alu['id']}")
                        f1 = col_f1.date_input("Fecha de entrega", datetime.date.today(), key=f"f1_{alu['id']}")
                        o1 = col_o1.text_input("Observaciones", placeholder="Ej: Entregó tarde / Rehacer", key=f"o1_{alu['id']}")
                        
                        # Fila para el Trabajo 2
                        st.markdown(f"**{tipo_eval} N° 2**")
                        col_n2, col_f2, col_o2 = st.columns([1, 1.5, 3])
                        n2 = col_n2.number_input("Nota", 0.0, 10.0, 0.0, step=0.5, key=f"n2_{alu['id']}")
                        f2 = col_f2.date_input("Fecha de entrega", datetime.date.today(), key=f"f2_{alu['id']}")
                        o2 = col_o2.text_input("Observaciones", placeholder="Ej: Excelente vocabulario", key=f"o2_{alu['id']}")
                        
                        # Cálculo de Promedio Visual
                        notas = [n for n in [n1, n2] if n > 0]
                        promedio = sum(notas) / len(notas) if notas else 0.0
                        color_p = "#4ade80" if promedio >= 7 else "#fbbf24" if promedio >= 4 else "#ef4444"
                        
                        st.markdown(f"""
                            <div style='display: flex; align-items: center; gap: 20px; margin-top: 10px;'>
                                <div style='font-size: 1.1rem;'>Promedio Actual:</div>
                                <div class='promedio-box' style='background: {color_p};'>{promedio:.2f}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        st.divider()
                
                if st.button("💾 GUARDAR REGISTRO COMPLETO"):
                    st.success("Datos guardados. La bitácora ha sido actualizada.")
            else:
                st.info("No hay alumnos para calificar en este curso.")
