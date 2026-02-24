import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")

# --- ESTILO SOFISTICADO ---
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

    # --- TAB 0: AGENDA (NUEVA LÓGICA) ---
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
                col_d1, col_d2, col_d3 = st.columns([1.5, 2, 2])
                es_sup = col_d1.selectbox("Docente", ["TITULAR", "SUPLENTE"])
                
                nom_final = user['email']
                if es_sup == "SUPLENTE":
                    n_s = col_d2.text_input("Nombre Suplente")
                    a_s = col_d3.text_input("Apellido Suplente")
                    nom_final = f"Suplente: {n_s} {a_s}"
                else: col_d2.info(f"Titular: {user['email']}")
                
                st.markdown("---")
                temas = st.text_area("Temas dictados hoy")
                
                st.markdown("#### 📝 Tarea")
                col_t1, col_t2 = st.columns([2, 1])
                desc_t = col_t1.text_area("Descripción de la tarea")
                venc_t = col_t2.date_input("Para el día:", datetime.date.today() + datetime.timedelta(days=7))
                
                pre_guardar = st.form_submit_button("Procesar Registro")

            if pre_guardar:
                st.warning("⚠️ ¿Confirmas el guardado de este registro?")
                if st.button("✅ SÍ, GUARDAR EN BITÁCORA"):
                    c_info = df_c[df_c['nombre_curso_materia'] == curso_sel.split(" | ")[0]].iloc[0]
                    data_clase = {
                        "curso_id": int(c_info['id']),
                        "profesor_id": user['id'],
                        "fecha": str(fecha_c),
                        "docente_nombre": nom_final,
                        "temas": temas,
                        "tarea_description": desc_t,
                        "tarea_vencimiento": str(venc_t)
                    }
                    supabase.table("bitacora").insert(data_clase).execute()
                    st.success("✅ Clase guardada correctamente.")
                    st.balloons()
        else: st.info("Cargá un curso primero.")

    # --- TABS ALUMNOS Y CURSOS (YA FUNCIONALES) ---
    with tabs[1]:
        st.subheader("Inscripción")
        # Aquí se mantiene tu código de Alumnos que ya probamos
    with tabs[2]:
        st.subheader("Configuración de Materias 2026")
        with st.form("form_curso_final", clear_on_submit=True):
            n_m = st.text_input("Nombre de la Materia")
            h_m = st.text_input("Horario")
            if st.form_submit_button("Guardar Materia"):
                supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": n_m, "horario": h_m, "anio_lectivo": 2026}).execute()
                st.success(f"¡Curso '{n_m}' creado!")
                st.rerun()
