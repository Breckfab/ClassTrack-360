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
    .confirm-box { padding: 15px; border: 1px solid #ff4b4b; border-radius: 10px; background-color: rgba(255, 75, 75, 0.1); margin: 10px 0; }
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
                else: 
                    st.error("Acceso denegado.")

else:
    user = st.session_state.user
    st.sidebar.markdown(f"<h2 style='color: #3b82f6;'>CT360</h2>", unsafe_allow_html=True)
    st.sidebar.write(f"Profe: {user['email']}")
    if st.sidebar.button("CERRAR SESIÓN"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "🏗️ Cursos", "🔍 Historial"])

    # Consulta de cursos para toda la aplicación
    res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
    df_cursos = pd.DataFrame(res_c.data) if res_c.data else pd.DataFrame()

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if not df_cursos.empty:
            opciones_c = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()]
            c_agenda = st.selectbox("Materia", opciones_c)
            tipo_doc = st.radio("Docente", ["TITULAR", "SUPLENTE"], horizontal=True)
            
            doc_final = user['email']
            if tipo_doc == "SUPLENTE":
                col_s1, col_s2 = st.columns(2)
                n_sup = col_s1.text_input("Nombre Suplente")
                a_sup = col_s2.text_input("Apellido Suplente")
                doc_final = f"Suplente: {n_sup} {a_sup}"
            
            with st.form("form_agenda"):
                temas = st.text_area("Contenidos dictados")
                tarea = st.text_area("Tarea")
                venc = st.date_input("Vencimiento", datetime.date.today() + datetime.timedelta(days=7))
                if st.form_submit_button("Procesar Registro"):
                    st.session_state.confirm_agenda = {"temas": temas, "tarea": tarea, "venc": str(venc), "doc": doc_final, "curso_str": c_agenda}

            if st.session_state.get('confirm_agenda'):
                st.warning("¿Confirmás el guardado en Bitácora?")
                c1, c2 = st.columns(2)
                if c1.button("✅ GUARDAR"):
                    # Buscar ID del curso
                    c_info = df_cursos[df_cursos['nombre_curso_materia'] == st.session_state.confirm_agenda['curso_str'].split(" | ")[0]].iloc[0]
                    supabase.table("bitacora").insert({
                        "curso_id": int(c_info['id']), "profesor_id": user['id'], "fecha": str(datetime.date.today()),
                        "docente_nombre": st.session_state.confirm_agenda['doc'], "temas": st.session_state.confirm_agenda['temas'],
                        "tarea_descripcion": st.session_state.confirm_agenda['tarea'], "tarea_vencimiento": st.session_state.confirm_agenda['venc']
                    }).execute()
                    del st.session_state.confirm_agenda
                    st.success("Guardado.")
                    st.balloons()
                if c2.button("❌ CANCELAR"):
                    del st.session_state.confirm_agenda
                    st.rerun()
        else: st.info("Cargá un curso primero.")

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Inscripción con Desplegable")
        if not df_cursos.empty:
            with st.form("form_ins_alu", clear_on_submit=True):
                opciones = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()]
                c_sel = st.selectbox("Elegir Curso", opciones)
                nom_a = st.text_input("Nombre")
                ape_a = st.text_input("Apellido")
                if st.form_submit_button("Inscribir"):
                    if nom_a and ape_a:
                        st.session_state.confirm_alu = {"nom": nom_a, "ape": ape_a, "curso": c_sel}
            
            if st.session_state.get('confirm_alu'):
                d = st.session_state.confirm_alu
                st.warning(f"¿Inscribir a {d['nom']} {d['ape']}?")
                if st.button("✅ SÍ, INSCRIBIR"):
                    nuevo = supabase.table("alumnos").insert({"nombre": d['nom'], "apellido": d['ape']}).execute()
                    c_n, c_h = d['curso'].split(" | ")
                    supabase.table("inscripciones").insert({"alumno_id": nuevo.data[0]['id'], "profesor_id": user['id'], "nombre_curso_materia": c_n, "horario": c_h, "anio_lectivo": 2026}).execute()
                    del st.session_state.confirm_alu
                    st.rerun()

    # --- TAB 2: CURSOS ---
    with tabs[2]:
        st.subheader("Mis Cursos")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows():
                col_c1, col_c2 = st.columns([4, 1])
                col_c1.write(f"📘 **{cur['nombre_curso_materia']}** ({cur['horario']})")
                if col_c2.button("Borrar", key=f"del_cur_{cur['id']}"):
                    st.session_state[f"conf_del_c_{cur['id']}"] = True
                if st.session_state.get(f"conf_del_c_{cur['id']}"):
                    if st.button("🔥 Confirmar Borrado", key=f"real_del_c_{cur['id']}"):
                        supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                        st.rerun()

        with st.form("nuevo_c"):
            nc = st.text_input("Materia")
            hc = st.text_input("Horario")
            if st.form_submit_button("Añadir"):
                supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                st.rerun()

    # --- TAB 3: HISTORIAL ---
    with tabs[3]:
        st.subheader("Consultar Bitácora")
        res_h = supabase.table("bitacora").select("*").eq("profesor_id", user['id']).order("fecha", desc=True).execute()
        if res_h.data:
            df_h = pd.DataFrame(res_h.data)
            busqueda = st.text_input("🔍 Buscar tema o docente...")
            if busqueda:
                df_h = df_h[df_h['temas'].str.contains(busqueda, case=False) | df_h['docente_nombre'].str.contains(busqueda, case=False)]
            st.table(df_h[['fecha', 'docente_nombre', 'temas', 'tarea_descripcion']])
        else: st.info("Sin registros históricos.")
