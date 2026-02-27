import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v195", layout="wide")

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
    .tarea-alerta { background: rgba(255, 193, 7, 0.1); border: 1px solid #ffc107; padding: 10px; border-radius: 8px; margin-bottom: 15px; color: #ffc107; }
    #info-superior { position: fixed; top: 10px; right: 20px; font-family: 'JetBrains Mono', monospace; text-align: right; z-index: 10000; background: rgba(0,0,0,0.8); padding: 10px; border-radius: 8px; border: 1px solid #4facfe; }
    </style>
    """, unsafe_allow_html=True)

# --- RELOJ Y FECHA ---
components.html("""
    <div id="info-superior">
        <div id="fecha-actual" style="font-size: 0.9rem; color: #e0e0e0;">--/--/----</div>
        <div id="reloj-fijo" style="font-size: 1.2rem; color: #4facfe; font-weight: bold;">00:00:00</div>
    </div>
    <script>
    function actualizarInfo() {
        const ahora = new Date();
        const d = String(ahora.getDate()).padStart(2, '0');
        const m = String(ahora.getMonth() + 1).padStart(2, '0');
        const a = ahora.getFullYear();
        const h = String(ahora.getHours()).padStart(2, '0');
        const min = String(ahora.getMinutes()).padStart(2, '0');
        const s = String(ahora.getSeconds()).padStart(2, '0');
        window.parent.document.getElementById('fecha-actual').innerText = d + '/' + m + '/' + a;
        window.parent.document.getElementById('reloj-fijo').innerText = h + ':' + min + ':' + s;
    }
    setInterval(actualizarInfo, 1000); actualizarInfo();
    </script>
    """, height=60)

if st.session_state.user is None:
    st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Sede").strip().lower()
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("ENTRAR AL SISTEMA"):
            res = supabase.table("usuarios").select("*").eq("email", f"{u}.fabianbelledi@gmail.com").eq("password_text", p).execute()
            if res.data: st.session_state.user = res.data[0]; st.rerun()
            else: st.error("Acceso denegado.")
else:
    u_data = st.session_state.user
    # Carga de Cursos
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA FUNCIONAL ---
    with tabs[0]:
        st.subheader("📅 Control de Bitácora")
        if not mapa_cursos: st.warning("Cree un curso primero.")
        else:
            c_sel = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_c")
            f_hoy = st.date_input("Fecha de hoy:", datetime.date.today())
            
            # 1. Ver qué tarea había para hoy (programada antes)
            res_prev = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_sel]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_prev.data:
                st.markdown(f'<div class="tarea-alerta">🔔 <b>TAREA PARA HOY:</b> {res_prev.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            
            # 2. Anotar lo de hoy
            res_hoy = supabase.table("bitacora").select("*").eq("inscripcion_id", mapa_cursos[c_sel]).eq("fecha", str(f_hoy)).execute()
            with st.form("f_ag_v195"):
                t_hoy = st.text_area("Temas de hoy:", value=res_hoy.data[0]['contenido_clase'] if res_hoy.data else "")
                t_fut = st.text_area("Tarea para la próxima clase:", value=res_hoy.data[0]['tarea_proxima'] if res_hoy.data else "")
                f_vto = st.date_input("Para entregar el día:", datetime.date.today() + datetime.timedelta(days=7))
                if st.form_submit_button("💾 GUARDAR AGENDA"):
                    payload = {"inscripcion_id": mapa_cursos[c_sel], "fecha": str(f_hoy), "contenido_clase": t_hoy, "tarea_proxima": t_fut, "fecha_tarea": str(f_vto)}
                    if res_hoy.data: supabase.table("bitacora").update(payload).eq("id", res_hoy.data[0]['id']).execute()
                    else: supabase.table("bitacora").insert(payload).execute()
                    st.success("Guardado."); st.rerun()

    # --- TAB 1: ALUMNOS (SIN CÓDIGOS, CON ACCIONES DIRECTAS) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        # Formulario de carga
        with st.expander("➕ Inscribir Alumno Nuevo"):
            with st.form("new_al"):
                col1, col2 = st.columns(2)
                nom = col1.text_input("Nombre")
                ape = col1.text_input("Apellido")
                dn = col2.text_input("DNI")
                c_ins = st.selectbox("Curso:", list(mapa_cursos.keys()))
                if st.form_submit_button("💾 GUARDAR"):
                    res_a = supabase.table("alumnos").insert({"nombre": nom, "apellido": ape, "dni": dn}).execute()
                    if res_a.data:
                        supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": c_ins, "anio_lectivo": 2026}).execute()
                        st.success("Inscripto."); st.rerun()

        # Listado con botones
        st.write("### Listado de Alumnos")
        res_al = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido, dni)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        if res_al.data:
            for r in res_al.data:
                al = r['alumnos']
                with st.container():
                    st.markdown(f'<div class="planilla-row"><b>{al["apellido"].upper()}, {al["nombre"]}</b> | {r["nombre_curso_materia"]} (DNI: {al["dni"]})</div>', unsafe_allow_html=True)
                    c1, c2, c3, _ = st.columns([1,1,1,5])
                    if c2.button("🗑️ Borrar", key=f"del_al_{r['id']}"):
                        supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                        st.rerun()
                    c1.button("✏️ Editar", key=f"ed_al_{r['id']}")
                    c3.button("💾 Guardar", key=f"sv_al_{r['id']}")

    # --- TAB 2: ASISTENCIA POR CURSO ---
    with tabs[2]:
        st.subheader("✅ Tomar Asistencia")
        if mapa_cursos:
            c_asist = st.selectbox("Elegir Curso:", ["---"] + list(mapa_cursos.keys()))
            if c_asist != "---":
                res_lista = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_asist).not_.is_("alumno_id", "null").execute()
                for item in res_lista.data:
                    al = item['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"as_{al['id']}_{c_asist}"):
                            est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                            if st.form_submit_button("💾 REGISTRAR"):
                                supabase.table("asistencia").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": c_asist, "estado": est, "fecha": str(datetime.date.today())}).execute()
                                st.success("Ok")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("🏗️ Cursos")
        with st.form("c_new"):
            n_c = st.text_input("Nombre Materia/Horario")
            if st.form_submit_button("💾 CREAR CURSO"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": n_c, "anio_lectivo": 2026}).execute()
                st.rerun()
