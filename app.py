import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v182", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: 
    st.session_state.user = None

# --- ESTILO, RELOJ Y FECHA ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .card-tarea-hoy { background: rgba(255, 193, 7, 0.1); border: 1px solid #ffc107; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; }
    #info-superior { position: fixed; top: 10px; right: 20px; font-family: 'JetBrains Mono', monospace; text-align: right; z-index: 10000; background: rgba(0,0,0,0.7); padding: 10px; border-radius: 8px; border: 1px solid #4facfe; line-height: 1.2; }
    </style>
    """, unsafe_allow_html=True)

# --- RELOJ Y FECHA DINÁMICA ---
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
    setInterval(actualizarInfo, 1000);
    actualizarInfo();
    </script>
    """, height=0)

if st.session_state.user is None:
    # Login (Fabian Cambridge por defecto)
    st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Sede").strip().lower()
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("ENTRAR"):
            res = supabase.table("usuarios").select("*").eq("email", f"{u}.fabianbelledi@gmail.com").eq("password_text", p).execute()
            if res.data: st.session_state.user = res.data[0]; st.rerun()
else:
    u_data = st.session_state.user
    
    # Cargar cursos del profesor una sola vez para todas las pestañas
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA INTELIGENTE ---
    with tabs[0]:
        st.subheader("📅 Gestión de Clase y Tareas")
        if not mapa_cursos:
            st.warning("Cree un curso para empezar.")
        else:
            sel_ag = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_sel")
            col_f1, col_f2 = st.columns([2,1])
            f_clase = col_f1.date_input("Día de la clase:", datetime.date.today())
            
            # MOSTRAR TAREA PARA HOY (Automático)
            res_t_hoy = supabase.table("bitacora").select("*").eq("inscripcion_id", mapa_cursos[sel_ag]).eq("fecha_tarea", str(f_clase)).execute()
            if res_t_hoy.data:
                for t in res_t_hoy.data:
                    st.markdown(f'<div class="card-tarea-hoy">📌 <b>TAREA PARA HOY:</b> {t["tarea_proxima"]}</div>', unsafe_allow_html=True)
            else:
                st.info("No hay tareas programadas para entregar hoy.")

            with st.form("f_agenda"):
                temas = st.text_area("¿Qué temas diste hoy?")
                recursos = st.text_input("Recursos utilizados")
                st.divider()
                st.write("📝 **Asignar Nueva Tarea:**")
                c_t1, c_t2 = st.columns(2)
                d_tarea = c_t1.text_area("Descripción de la tarea")
                f_tarea = c_t2.date_input("Para entregar el día:", datetime.date.today() + datetime.timedelta(days=7))
                if st.form_submit_button("💾 GUARDAR TODO"):
                    supabase.table("bitacora").insert({
                        "inscripcion_id": mapa_cursos[sel_ag], "fecha": str(f_clase),
                        "contenido_clase": temas, "recursos_utilizados": recursos,
                        "tarea_proxima": d_tarea, "fecha_tarea": str(f_tarea)
                    }).execute()
                    st.success("Día registrado."); st.rerun()

    # --- TAB 1: ALUMNOS (RECONECTADO) ---
    with tabs[1]:
        st.subheader("👥 Registro de Alumnos")
        if mapa_cursos:
            with st.form("ins_al"):
                c1, c2 = st.columns(2)
                n_nom, n_ape = c1.text_input("Nombre"), c1.text_input("Apellido")
                n_dni, n_tel = c2.text_input("DNI"), c2.text_input("Teléfono")
                n_cur = st.selectbox("Asignar a:", list(mapa_cursos.keys()))
                if st.form_submit_button("💾 REGISTRAR"):
                    res_a = supabase.table("alumnos").insert({"nombre": n_nom, "apellido": n_ape, "dni": n_dni, "telefono_contacto": n_tel}).execute()
                    if res_a.data:
                        supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": n_cur, "anio_lectivo": 2026}).execute()
                        st.success("Alumno guardado.")

    # --- TAB 2: ASISTENCIA (RECONECTADO) ---
    with tabs[2]:
        st.subheader("✅ Asistencia")
        if mapa_cursos:
            sel_as = st.selectbox("Curso:", list(mapa_cursos.keys()), key="as_sel")
            f_as = st.date_input("Fecha:", datetime.date.today(), key="as_f")
            res_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_as).not_.is_("alumno_id", "null").execute()
            for it in res_al.data:
                al = it['alumnos']
                with st.form(f"as_{al['id']}"):
                    st.markdown(f'<div class="planilla-row">{al["apellido"]}, {al["nombre"]}</div>', unsafe_allow_html=True)
                    est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                    if st.form_submit_button("💾 OK"):
                        supabase.table("asistencia").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": sel_as, "estado": est, "fecha": str(f_as)}).execute()
                        st.success("Listo")

    # --- TAB 3: NOTAS (RECONECTADO) ---
    with tabs[3]:
        st.subheader("📝 Calificaciones")
        if mapa_cursos:
            sel_nt = st.selectbox("Curso:", list(mapa_cursos.keys()), key="nt_sel")
            res_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_nt).not_.is_("alumno_id", "null").execute()
            for it in res_al.data:
                al = it['alumnos']
                res_n = supabase.table("notas").select("calificacion").eq("alumno_id", al['id']).eq("materia", sel_nt).execute()
                prom = sum([float(n['calificacion']) for n in res_n.data]) / len(res_n.data) if res_n.data else 0
                with st.form(f"nt_{al['id']}"):
                    st.markdown(f'<div class="planilla-row">{al["apellido"]} (Promedio: {prom:.2f})</div>', unsafe_allow_html=True)
                    n_v = st.number_input("Nota:", 1.0, 10.0, value=None)
                    if st.form_submit_button("💾 SUBIR"):
                        if n_v:
                            supabase.table("notas").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": sel_nt, "calificacion": float(n_v)}).execute()
                            st.rerun()

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("🏗️ Cursos")
        with st.form("c_cur"):
            n = st.text_input("Nombre")
            d = st.text_input("Días/Horas")
            if st.form_submit_button("CREAR"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": f"{n} - {d}", "anio_lectivo": 2026}).execute()
                st.rerun()
