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
    .asist-card { 
        background: rgba(255, 255, 255, 0.05); 
        padding: 15px; 
        border-radius: 10px; 
        margin-bottom: 10px; 
        border-left: 5px solid #a855f7;
    }
    .stButton>button { border-radius: 8px; }
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
    st.sidebar.markdown(f"<h2 style='color: #3b82f6;'>CT360</h2>", unsafe_allow_html=True)
    st.sidebar.write(f"Profe: {user['email']}")
    if st.sidebar.button("CERRAR SESIÓN"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "🏗️ Cursos", "🔍 Historial"])

    # Consulta de cursos (Carga base para todas las pestañas)
    res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
    df_cursos = pd.DataFrame(res_c.data) if res_c.data else pd.DataFrame()

    # --- TAB 2: ASISTENCIA (LÓGICA DAGUERRE VS CAMBRIDGE) ---
    with tabs[2]:
        st.subheader("Control de Asistencia")
        if not df_cursos.empty:
            opciones = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()]
            curso_asist = st.selectbox("Seleccionar Curso para pasar lista", opciones)
            
            # Determinamos institución por palabras clave en el curso o perfil
            # Si el curso contiene "Daguerre" o el mail es de allí
            es_daguerre = "daguerre" in curso_asist.lower() or "daguerre" in user['email'].lower()
            
            st.markdown(f"**Sistema de cómputo:** {'📚 Daguerre (Por Horas Cátedra)' if es_daguerre else '🎓 Cambridge (Por Día)'}")

            c_nom, c_hor = curso_asist.split(" | ")
            res_a = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("profesor_id", user['id']).eq("nombre_curso_materia", c_nom).eq("horario", c_hor).not_.is_("alumno_id", "null").execute()
            
            if res_a.data:
                if es_daguerre:
                    h_totales = st.number_input("Horas Cátedra totales de hoy:", min_value=1, max_value=12, value=4)
                
                with st.form("form_asistencia_final"):
                    st.write("### Lista de Alumnos")
                    for item in res_a.data:
                        alu = item['alumnos']
                        st.markdown(f'<div class="asist-card"><b>{alu["apellido"]}, {alu["nombre"]}</b></div>', unsafe_allow_html=True)
                        
                        if es_daguerre:
                            st.slider(f"Horas Presente (de {h_totales}hs totales)", 0, h_totales, h_totales, key=f"asist_{alu['id']}")
                        else:
                            st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True, key=f"asist_{alu['id']}")
                    
                    if st.form_submit_button("Guardar Asistencia de Hoy"):
                        st.success("Asistencia registrada. (Mañana conectaremos esto a la base de datos de reportes)")
            else:
                st.info("No hay alumnos inscritos en este curso.")
        else:
            st.warning("Cargá un curso primero.")

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("Registro de Clase Diaria")
        if not df_cursos.empty:
            opciones_c = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()]
            c_agenda = st.selectbox("Materia", opciones_c, key="sel_agenda")
            tipo_doc = st.radio("Docente", ["TITULAR", "SUPLENTE"], horizontal=True)
            doc_final = user['email']
            if tipo_doc == "SUPLENTE":
                col_s1, col_s2 = st.columns(2)
                n_sup = col_s1.text_input("Nombre Suplente")
                a_sup = col_s2.text_input("Apellido Suplente")
                doc_final = f"Suplente: {n_sup} {a_sup}"
            
            with st.form("form_agenda"):
                temas = st.text_area("Contenidos dictados")
                tarea = st.text_area("Tarea para el hogar")
                venc = st.date_input("Fecha de entrega", datetime.date.today() + datetime.timedelta(days=7))
                if st.form_submit_button("Guardar en Bitácora"):
                    st.session_state.confirm_agenda = {"temas": temas, "tarea": tarea, "venc": str(venc), "doc": doc_final, "curso_str": c_agenda}

            if st.session_state.get('confirm_agenda'):
                st.warning("¿Confirmás el guardado?")
                if st.button("✅ SÍ, GUARDAR"):
                    c_info = df_cursos[df_cursos['nombre_curso_materia'] == st.session_state.confirm_agenda['curso_str'].split(" | ")[0]].iloc[0]
                    supabase.table("bitacora").insert({
                        "curso_id": int(c_info['id']), "profesor_id": user['id'], "fecha": str(datetime.date.today()),
                        "docente_nombre": st.session_state.confirm_agenda['doc'], "temas": st.session_state.confirm_agenda['temas'],
                        "tarea_descripcion": st.session_state.confirm_agenda['tarea'], "tarea_vencimiento": st.session_state.confirm_agenda['venc']
                    }).execute()
                    del st.session_state.confirm_agenda
                    st.success("Guardado correctamente.")
                    st.rerun()

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if not df_cursos.empty:
            with st.form("form_ins_alu", clear_on_submit=True):
                opciones = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()]
                c_sel = st.selectbox("Asignar a Curso", opciones, key="sel_ins_alu")
                nom_a = st.text_input("Nombre")
                ape_a = st.text_input("Apellido")
                if st.form_submit_button("Inscribir Alumno"):
                    if nom_a and ape_a:
                        st.session_state.confirm_alu = {"nom": nom_a, "ape": ape_a, "curso": c_sel}
            
            if st.session_state.get('confirm_alu'):
                st.warning(f"¿Inscribir a {st.session_state.confirm_alu['nom']} {st.session_state.confirm_alu['ape']}?")
                if st.button("✅ CONFIRMAR INSCRIPCIÓN"):
                    nuevo = supabase.table("alumnos").insert({"nombre": st.session_state.confirm_alu['nom'], "apellido": st.session_state.confirm_alu['ape']}).execute()
                    c_n, c_
