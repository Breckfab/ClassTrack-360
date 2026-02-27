import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v202", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- ESTILO CONTROLADO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.2rem; font-weight: 800; color: #4facfe; text-align: center; margin-bottom: 20px; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
    .tarea-hoy { background: rgba(255, 193, 7, 0.15); border: 1px solid #ffc107; padding: 15px; border-radius: 8px; color: #ffc107; text-align: center; margin-bottom: 20px; }
    #info-superior { position: fixed; top: 10px; right: 20px; font-family: 'JetBrains Mono', monospace; text-align: right; z-index: 10000; background: rgba(0,0,0,0.8); padding: 10px; border-radius: 8px; border: 1px solid #4facfe; }
    </style>
    """, unsafe_allow_html=True)

# RELOJ Y FECHA DINÁMICOS
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
    with st.form("login_v202"):
        u = st.text_input("Sede").strip().lower()
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("ENTRAR AL SISTEMA"):
            res = supabase.table("usuarios").select("*").eq("email", f"{u}.fabianbelledi@gmail.com").eq("password_text", p).execute()
            if res.data: st.session_state.user = res.data[0]; st.rerun()
            else: st.error("Acceso denegado.")
else:
    u_data = st.session_state.user
    
    # CARGA DE CURSOS PARA MAPEO
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (CON RECORDATORIO DE TAREA) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if not mapa_cursos: st.info("Cree un curso primero.")
        else:
            c_ag = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_c")
            f_hoy = st.date_input("Fecha de hoy:", datetime.date.today())
            
            # Buscar tarea que vencía hoy
            res_tarea_hoy = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_tarea_hoy.data:
                st.markdown(f'<div class="tarea-hoy">🔔 <b>TAREA PENDIENTE PARA HOY:</b><br>{res_tarea_hoy.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="tarea-hoy">✅ No hay tareas pendientes para hoy.</div>', unsafe_allow_html=True)
            
            with st.form("f_agenda"):
                temas = st.text_area("¿Qué temas se trataron?")
                nueva_tarea = st.text_area("Tarea para la próxima clase:")
                fecha_vto = st.date_input("Fecha de entrega:", f_hoy + datetime.timedelta(days=7))
                if st.form_submit_button("💾 GUARDAR AGENDA"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": nueva_tarea, "fecha_tarea": str(fecha_vto)}).execute()
                    st.success("Guardado satisfactoriamente."); st.rerun()

    # --- TAB 2: ASISTENCIA (LISTADO POR CURSO) ---
    with tabs[2]:
        st.subheader("✅ Toma de Asistencia")
        if mapa_cursos:
            c_asist = st.selectbox("Elegir Curso:", ["---"] + list(mapa_cursos.keys()), key="as_sel")
            if c_asist != "---":
                res_al_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_asist).not_.is_("alumno_id", "null").execute()
                for item in res_al_as.data:
                    al = item['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"as_{al['id']}"):
                            est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                            if st.form_submit_button("💾 REGISTRAR"):
                                supabase.table("asistencia").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": c_asist, "estado": est, "fecha": str(datetime.date.today())}).execute()
                                st.success("Registrado.")

    # --- TAB 3: NOTAS (CON PUNTO Y PROMEDIO) ---
    with tabs[3]:
        st.subheader("📝 Planilla de Notas")
        if mapa_cursos:
            c_nota = st.selectbox("Elegir Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_sel")
            if c_nota != "---":
                res_al_nt = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_nota).not_.is_("alumno_id", "null").execute()
                for item in res_al_nt.data:
                    al = item['alumnos']
                    # Promedio
                    res_h = supabase.table("notas").select("calificacion").eq("alumno_id", al['id']).eq("materia", c_nota).execute()
                    vals = [float(n['calificacion']) for n in res_h.data]
                    prom = sum(vals)/len(vals) if vals else 0.0
                    
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 <b>{al["apellido"].upper()}</b> <span style="float:right;">Promedio: {prom:.2f}</span></div>', unsafe_allow_html=True)
                        with st.form(f"nt_{al['id']}"):
                            val_nota = st.number_input("Nota (7.00):", min_value=1.0, max_value=10.0, value=7.0, step=0.1, format="%.2f")
                            if st.form_submit_button("💾 VOLCAR"):
                                supabase.table("notas").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": c_nota, "calificacion": val_nota, "fecha": str(datetime.date.today())}).execute()
                                st.rerun()

    # --- TAB 1: ALUMNOS (REDISEÑADO) ---
    with tabs[1]:
        st.subheader("👥 Alumnos")
        # El listado aquí se carga con try/except para evitar el "negro"
        try:
            res_al_list = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido, dni)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if res_al_list.data:
                for r in res_al_list.data:
                    al = r['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 <b>{al["apellido"].upper()}, {al["nombre"]}</b> | {r["nombre_curso_materia"]}</div>', unsafe_allow_html=True)
                        col_b1, col_b2, _ = st.columns([1,1,6])
                        if col_b2.button("🗑️ Borrar", key=f"d_al_{r['id']}"):
                            supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                            st.rerun()
            else: st.info("No hay alumnos inscriptos.")
        except: st.error("Error al cargar lista de alumnos.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("🏗️ Cursos")
        # Listado siempre visible
        if res_c.data:
            for c in res_c.data:
                st.markdown(f'<div class="planilla-row">📖 {c["nombre_curso_materia"]}</div>', unsafe_allow_html=True)
                if st.button("🗑️ Borrar Curso", key=f"dc_{c['id']}"):
                    supabase.table("inscripciones").delete().eq("id", c['id']).execute()
                    st.rerun()
        st.divider()
        with st.form("new_cur"):
            st.write("### ➕ Crear Nuevo")
            nc = st.text_input("Nombre Materia/Horario")
            if st.form_submit_button("💾 INSTALAR"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.rerun()
