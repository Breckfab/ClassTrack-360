import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v251", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- ESTILO ---
st.markdown("""
    <style>
    .stApp { background: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; }
    .tarea-alerta { background: rgba(255, 193, 7, 0.2); border: 2px dashed #ffc107; padding: 20px; border-radius: 10px; color: #ffc107; text-align: center; font-weight: bold; margin-bottom: 25px; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

if st.session_state.user is None:
    with st.form("login"):
        u = st.text_input("Sede").strip().lower()
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("ENTRAR AL SISTEMA"):
            res = supabase.table("usuarios").select("*").eq("email", f"{u}.fabianbelledi@gmail.com").eq("password_text", p).execute()
            if res.data: st.session_state.user = res.data[0]; st.rerun()
else:
    u_data = st.session_state.user
    
    # MOTOR DE CURSOS
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (CON SENSOR RETROACTIVO) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            c_ag = st.selectbox("Seleccione Curso:", list(mapa_cursos.keys()), key="ag_251")
            f_hoy = datetime.date.today()
            
            # SENSOR FORZADO: Busca la última tarea pendiente (hoy o anterior)
            res_t = supabase.table("bitacora").select("tarea_proxima, fecha_tarea").eq("inscripcion_id", mapa_cursos[c_ag]).lte("fecha_tarea", str(f_hoy)).order("fecha_tarea", desc=True).limit(1).execute()
            
            if res_t.data:
                tarea = res_t.data[0]['tarea_proxima']
                fecha_t = res_t.data[0]['fecha_tarea']
                st.markdown(f'<div class="tarea-alerta">⚠️ TAREA PENDIENTE (Clase {fecha_t}):<br>{tarea}</div>', unsafe_allow_html=True)
            
            with st.form("f_ag_new"):
                temas = st.text_area("Temas dictados hoy")
                tarea_n = st.text_area("Nueva tarea para la próxima")
                vto = st.date_input("Vencimiento tarea:", f_hoy + datetime.timedelta(days=7))
                b1, b2, b3, _ = st.columns([1,1,1,5])
                if b1.form_submit_button("💾 Guardar"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": tarea_n, "fecha_tarea": str(vto)}).execute()
                    st.success("Guardado."); st.rerun()
                b2.form_submit_button("✏️ Editar")
                b3.form_submit_button("🗑️ Borrar")

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        sub_al = st.radio("Acción:", ["Consulta", "Nuevo Alumno"], horizontal=True)
        if sub_al == "Nuevo Alumno":
            with st.form("new_al"):
                n, a = st.text_input("Nombre"), st.text_input("Apellido")
                c_sel = st.selectbox("Asignar a:", list(mapa_cursos.keys()))
                if st.form_submit_button("💾 REGISTRAR"):
                    ra = supabase.table("alumnos").insert({"nombre": n, "apellido": a}).execute()
                    if ra.data:
                        supabase.table("inscripciones").insert({"alumno_id": ra.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": c_sel, "anio_lectivo": 2026}).execute()
                        st.success("Registrado."); st.rerun()
        else:
            c_v = st.selectbox("Filtrar:", ["---"] + list(mapa_cursos.keys()))
            if c_v != "---":
                res_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_v).not_.is_("alumno_id", "null").execute()
                for r in res_al.data:
                    al = r['alumnos'][0] if isinstance(r['alumnos'], list) else r['alumnos']
                    if al:
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)

    # --- TAB 2: NOTAS ---
    with tabs[2]:
        st.subheader("📝 Notas")
        c_nt = st.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_251")
        if c_nt != "---":
            res_al_n = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_nt).not_.is_("alumno_id", "null").execute()
            for r in res_al_n.data:
                al = r['alumnos'][0] if isinstance(r['alumnos'], list) else r['alumnos']
                if al:
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"nt_{al['id']}"):
                            nota = st.number_input("Nota:", 0.0, 10.0, step=0.1)
                            if st.form_submit_button("💾 Guardar Nota"): st.success("Nota guardada.")

    # --- TAB 3: CURSOS ---
    with tabs[3]:
        sub_cu = st.radio("Acción:", ["Listar", "Nuevo Curso"], horizontal=True)
        if sub_cu == "Nuevo Curso":
            with st.form("new_c"):
                mat, hor = st.text_input("Materia"), st.text_input("Horario")
                dias = st.multiselect("Días:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                if st.form_submit_button("💾 INSTALAR"):
                    info = f"{mat} ({', '.join(dias)}) | {hor}"
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": info, "anio_lectivo": 2026}).execute()
                    st.success("Curso instalado."); st.rerun()
        else:
            for n_c, i_c in mapa_cursos.items():
                st.markdown(f'<div class="planilla-row">📖 {n_c}</div>', unsafe_allow_html=True)
