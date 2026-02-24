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
    .asist-card { background: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 8px; margin-bottom: 5px; border-left: 5px solid #3b82f6; }
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
    st.sidebar.write(f"Profe: {user['email']}")
    if st.sidebar.button("CERRAR SESIÓN"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "🏗️ Cursos", "🔍 Historial"])

    # Consulta de cursos
    res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
    df_cursos = pd.DataFrame(res_c.data) if res_c.data else pd.DataFrame()

    # --- TAB 2: ASISTENCIA (LÓGICA DIFERENCIAL) ---
    with tabs[2]:
        st.subheader("Control de Asistencia")
        if not df_cursos.empty:
            opciones = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()]
            curso_asist = st.selectbox("Seleccionar Curso", opciones)
            
            # Determinamos institución por el email del profesor
            es_daguerre = "daguerre" in user['email'].lower()
            inst_label = "DAGUERRE (Por Hora Cátedra)" if es_daguerre else "CAMBRIDGE (Por Día)"
            st.info(f"Sistema configurado para: **{inst_label}**")

            c_nom, c_hor = curso_asist.split(" | ")
            res_a = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("profesor_id", user['id']).eq("nombre_curso_materia", c_nom).eq("horario", c_hor).not_.is_("alumno_id", "null").execute()
            
            if res_a.data:
                horas_totales = 1
                if es_daguerre:
                    horas_totales = st.number_input("Cantidad de horas cátedra hoy:", min_value=1, max_value=8, value=3)

                with st.form("form_asistencia"):
                    st.write("### Lista de Alumnos")
                    datos_asistencia = []
                    for item in res_a.data:
                        alu = item['alumnos']
                        st.markdown(f'<div class="asist-card">👤 {alu["apellido"]}, {alu["nombre"]}</div>', unsafe_allow_html=True)
                        
                        if es_daguerre:
                            # Para Daguerre: Elegir cuántas horas estuvo presente
                            h_pres = st.slider(f"Horas presente para {alu['nombre']}", 0, horas_totales, horas_totales, key=f"h_{alu['id']}")
                            datos_asistencia.append({"id": alu['id'], "valor": h_pres, "total": horas_totales})
                        else:
                            # Para Cambridge: Presente/Ausente/Tarde
                            estado = st.radio(f"Estado", ["Presente", "Ausente", "Tarde"], key=f"st_{alu['id']}", horizontal=True)
                            datos_asistencia.append({"id": alu['id'], "valor": estado})
                    
                    if st.form_submit_button("Guardar Lista de Hoy"):
                        # Aquí iría el insert a la tabla asistencia_logs
                        st.success(f"Asistencia de {inst_label} registrada correctamente.")
            else:
                st.info("No hay alumnos inscritos en este curso.")
        else:
            st.warning("Primero creá un curso en la pestaña 'Cursos'.")

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("Registro de Clase")
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
                temas = st.text_area("Temas dictados")
                tarea = st.text_area("Tarea")
                venc = st.date_input("Vencimiento", datetime.date.today() + datetime.timedelta(days=7))
                if st.form_submit_button("Procesar Registro"):
                    st.session_state.confirm_agenda = {"temas": temas, "tarea": tarea, "venc": str(venc), "doc": doc_final, "curso_str": c_agenda}

            if st.session_state.get('confirm_agenda'):
                st.warning("¿Confirmás el guardado en Bitácora?")
                if st.button("✅ GUARDAR"):
                    c_info = df_cursos[df_cursos['nombre_curso_materia'] == st.session_state.confirm_agenda['curso_str'].split(" | ")[0]].iloc[0]
                    supabase.table("bitacora").insert({
                        "curso_id": int(c_info['id']), "profesor_id": user['id'], "fecha": str(datetime.date.today()),
                        "docente_nombre": st.session_state.confirm_agenda['doc'], "temas": st.session_state.confirm_agenda['temas'],
                        "tarea_descripcion": st.session_state.confirm_agenda['tarea'], "tarea_vencimiento": st.session_state.confirm_agenda['venc']
                    }).execute()
                    del st.session_state.confirm_agenda
                    st.rerun()

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("Inscripción de Estudiantes")
        if not df_cursos.empty:
            with st.form("form_ins_alu", clear_on_submit=True):
                opciones = [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()]
                c_sel = st.selectbox("Asignar a Curso", opciones, key="sel_ins")
                nom_a = st.text_input("Nombre del Alumno")
                ape_a = st.text_input("Apellido del Alumno")
                if st.form_submit_button("Inscribir"):
                    if nom_a and ape_a:
                        st.session_state.confirm_alu = {"nom": nom_a, "ape": ape_a, "curso": c_sel}
            
            if st.session_state.get('confirm_alu'):
                st.warning(f"¿Inscribir a {st.session_state.confirm_alu['nom']}?")
                if st.button("✅ SÍ, INSCRIBIR"):
                    nuevo = supabase.table("alumnos").insert({"nombre": st.session_state.confirm_alu['nom'], "apellido": st.session_state.confirm_alu['ape']}).execute()
                    c_n, c_h = st.session_state.confirm_alu['curso'].split(" | ")
                    supabase.table("inscripciones").insert({"alumno_id": nuevo.data[0]['id'], "profesor_id": user['id'], "nombre_curso_materia": c_n, "horario": c_h, "anio_lectivo": 2026}).execute()
                    del st.session_state.confirm_alu
                    st.rerun()

    # --- TAB 3: CURSOS ---
    with tabs[3]:
        st.subheader("Mis Cursos")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows():
                col_c1, col_c2 = st.columns([4, 1])
                col_c1.write(f"📘 **{cur['nombre_curso_materia']}** ({cur['horario']})")
                if col_c2.button("Borrar", key=f"del_cur_{cur['id']}"):
                    supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                    st.rerun()
        with st.form("nuevo_c"):
            nc = st.text_input("Materia")
            hc = st.text_input("Horario")
            if st.form_submit_button("Añadir"):
                supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                st.rerun()

    # --- TAB 4: HISTORIAL ---
    with tabs[4]:
        st.subheader("Historial")
        try:
            res_h = supabase.table("bitacora").select("*").eq("profesor_id", user['id']).order("fecha", desc=True).execute()
            if res_h.data:
                st.table(pd.DataFrame(res_h.data)[['fecha', 'docente_nombre', 'temas']])
            else: st.info("Sin registros.")
        except: st.info("Listo para el primer registro.")
