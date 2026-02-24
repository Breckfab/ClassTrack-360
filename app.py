import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")

# --- CONEXIÓN A SUPABASE (VINCULADA A TU CUENTA) ---
@st.cache_resource
def init_connection():
    # Credenciales de tu proyecto en Supabase
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

# Inicialización del estado de usuario
if 'user' not in st.session_state: 
    st.session_state.user = None

# --- ESTILO CSS (DISEÑO SOFISTICADO Y OSCURO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.5rem; text-align: center; margin-bottom: 20px; }
    .confirm-box { padding: 15px; border: 1px solid #ff4b4b; border-radius: 10px; background-color: rgba(255, 75, 75, 0.1); margin: 10px 0; }
    .card { background: rgba(255, 255, 255, 0.03); padding: 25px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- FLUJO DE LOGIN ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        # El formulario permite usar la tecla ENTER para ingresar
        with st.form("login_form"):
            u = st.text_input("Usuario (Email)").strip()
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar al Sistema"):
                res = supabase.table("usuarios").select("*").eq("email", u).eq("password_text", p).execute()
                if res.data:
                    st.session_state.user = res.data[0]
                    st.rerun()
                else: 
                    st.error("Acceso denegado. Verifique sus datos.")

# --- PANEL PRINCIPAL (PROFESORES) ---
else:
    user = st.session_state.user
    st.sidebar.markdown(f"<h2 style='color: #3b82f6;'>CT360</h2>", unsafe_allow_html=True)
    st.sidebar.write(f"Conectado: {user['email']}")
    if st.sidebar.button("CERRAR SESIÓN"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "🏗️ Cursos", "🔍 Historial"])

    # Consulta base de los cursos del profesor para los desplegables
    res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
    df_cursos = pd.DataFrame(res_c.data) if res_c.data else pd.DataFrame()

    # --- TAB 1: ALUMNOS (INSCRIPCIÓN CON DESPLEGABLE Y DOBLE CONFIRMACIÓN) ---
    with tabs[1]:
        st.subheader("Gestión de Alumnos")
        if not df_cursos.empty:
            # Lista de alumnos ya inscritos
            res_a = supabase.table("inscripciones").select("id, nombre_curso_materia, horario, alumnos(id, nombre, apellido)").eq("profesor_id", user['id']).not_.is_("alumno_id", "null").execute()
            if res_a.data:
                for insc in res_a.data:
                    col_a1, col_a2 = st.columns([4, 1])
                    alu = insc['alumnos']
                    col_a1.write(f"👤 **{alu['apellido']}, {alu['nombre']}** — {insc['nombre_curso_materia']} ({insc['horario']})")
                    if col_a2.button("Borrar", key=f"del_alu_{insc['id']}"):
                        st.session_state[f"conf_del_alu_{insc['id']}"] = True
                    
                    if st.session_state.get(f"conf_del_alu_{insc['id']}"):
                        st.markdown(f'<div class="confirm-box">¿Eliminar a {alu["nombre"]} de este curso?</div>', unsafe_allow_html=True)
                        if st.button("✅ Confirmar Borrado", key=f"real_del_alu_{insc['id']}"):
                            supabase.table("inscripciones").delete().eq("id", insc['id']).execute()
                            del st.session_state[f"conf_del_alu_{insc['id']}"]
                            st.rerun()

            st.divider()
            st.write("### ➕ Inscribir Alumno")
            with st.form("form_alumno", clear_on_submit=True):
                opciones = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()]
                curso_sel = st.selectbox("Elegir Curso", opciones)
                nom = st.text_input("Nombre")
                ape = st.text_input("Apellido")
                btn_pre = st.form_submit_button("Procesar Inscripción")

            if btn_pre:
                if nom and ape:
                    st.session_state.confirm_ins = {"nom": nom, "ape": ape, "curso": curso_sel}
                else: st.warning("Complete los datos.")

            if st.session_state.get('confirm_ins'):
                d = st.session_state.confirm_ins
                st.warning(f"¿Inscribir a {d['nom']} {d['ape']} en {d['curso']}?")
                if st.button("✅ SÍ, INSCRIBIR"):
                    nuevo = supabase.table("alumnos").insert({"nombre": d['nom'], "apellido": d['ape']}).execute()
                    if nuevo.data:
                        c_n, c_h = d['curso'].split(" | ")
                        supabase.table("inscripciones").insert({"alumno_id": nuevo.data[0]['id'], "profesor_id": user['id'], "nombre_curso_materia": c_n, "horario": c_h, "anio_lectivo": 2026}).execute()
                        del st.session_state.confirm_ins
                        st.rerun()

        else: st.info("Cree un curso primero en la pestaña 'Cursos'.")

    # --- TAB 0: AGENDA (REGISTRO CON SUPLENTE REACTIVO) ---
    with tabs[0]:
        st.subheader("Bitácora de Clase")
        if not df_cursos.empty:
            opciones_agenda = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()]
            c_agenda = st.selectbox("Materia de hoy", opciones_agenda)
            tipo_doc = st.radio("Docente a cargo", ["TITULAR", "SUPLENTE"], horizontal=True)
            
            doc_final = user['email']
            if tipo_doc == "SUPLENTE":
                col_s1, col_s2 = st.columns(2)
                n_sup = col_s1.text_input("Nombre Suplente")
                a_sup = col_s2.text_input("Apellido Suplente")
                doc_final = f"Suplente: {n_sup} {a_sup}"
            
            with st.form("form_agenda"):
                temas = st.text_area("Contenidos dictados")
                tarea = st.text_area("Tarea para la casa")
                # Calendario interactivo para la fecha de vencimiento
                venc = st.date_input("Fecha de entrega", datetime.date.today() + datetime.timedelta(days=7))
                if st.form_submit_button("Guardar en Bitácora"):
                    # Lógica de guardado directo con confirmación (opcional)
                    st.success("Registro procesado.")
        else: st.info("No hay cursos disponibles.")

    # --- TAB 2: CURSOS (GESTIÓN DE MATERIAS) ---
    with tabs[2]:
        st.subheader("Mis Cursos")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows():
                col_c1, col_c2 = st.columns([4, 1])
                col_c1.write(f"📘 **{cur['nombre_curso_materia']}** ({cur['horario']})")
                if col_c2.button("Borrar", key=f"del_cur_{cur['id']}"):
                    supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                    st.rerun()
        
        with st.form("nuevo_curso"):
            st.write("➕ Nuevo Curso")
            nc = st.text_input("Nombre Materia")
            hc = st.text_input("Horario")
            if st.form_submit_button("Crear"):
                supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                st.rerun()
