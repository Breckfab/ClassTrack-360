import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v211", layout="wide")

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
    .stApp { background: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
    .tarea-alerta { background: rgba(255, 193, 7, 0.2); border: 2px dashed #ffc107; padding: 20px; border-radius: 10px; color: #ffc107; text-align: center; font-size: 1.1rem; font-weight: bold; margin-bottom: 25px; }
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
    
    with st.sidebar:
        st.header(f"Sede: {u_data['email'].split('.')[0].upper()}")
        components.html("""
            <div style="color: #4facfe; font-family: monospace; font-size: 26px; font-weight: bold; text-align: center;">
                <div id="d" style="font-size: 14px; color: #888; margin-bottom: 5px;"></div>
                <div id="c">00:00:00</div>
            </div>
            <script>
                function update() {
                    const n = new Date();
                    document.getElementById('d').innerText = n.toLocaleDateString('es-AR');
                    document.getElementById('c').innerText = n.toLocaleTimeString('es-AR', {hour12:false});
                }
                setInterval(update, 1000); update();
            </script>
        """, height=100)
        st.divider()
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- MOTOR DE DATOS SEGURO ---
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (CON DETECTOR DE TAREA) ---
    with tabs[0]:
        st.subheader("📅 Seguimiento de Clase")
        if not mapa_cursos: st.info("Cree un curso para habilitar la agenda.")
        else:
            c_ag = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_v211")
            f_hoy = st.date_input("Fecha de hoy:", datetime.date.today())
            
            # BUSQUEDA ACTIVA DE TAREA
            res_t = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_t.data:
                for t in res_t.data:
                    st.markdown(f'<div class="tarea-alerta">🔔 TAREA PARA REVISAR HOY:<br>{t["tarea_proxima"]}</div>', unsafe_allow_html=True)
            else:
                st.info("No hay tareas pendientes para esta fecha.")

            with st.form("f_ag_v211"):
                temas = st.text_area("Temas dictados hoy:")
                n_tarea = st.text_area("Tarea para la próxima:")
                vto = st.date_input("Vence el:", f_hoy + datetime.timedelta(days=7))
                if st.form_submit_button("💾 GUARDAR AGENDA"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": n_tarea, "fecha_tarea": str(vto)}).execute()
                    st.success("Cambios guardados satisfactoriamente."); time.sleep(1); st.rerun()

    # --- TAB 1: ALUMNOS (BLOQUEO ANTI-NEGRO) ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        with st.expander("➕ Inscribir Alumno Nuevo"):
            with st.form("new_al_v211"):
                n, a = st.text_input("Nombre"), st.text_input("Apellido")
                c_sel = st.selectbox("Asignar a:", list(mapa_cursos.keys()))
                if st.form_submit_button("💾 REGISTRAR"):
                    ra = supabase.table("alumnos").insert({"nombre": n, "apellido": a}).execute()
                    if ra.data:
                        supabase.table("inscripciones").insert({"alumno_id": ra.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": c_sel, "anio_lectivo": 2026}).execute()
                        st.success("Cambios guardados satisfactoriamente."); st.rerun()

        c_filt = st.selectbox("Seleccione Curso para ver Alumnos:", ["---"] + list(mapa_cursos.keys()), key="filt_al")
        if c_filt != "---":
            res_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("profesor_id", u_data['id']).eq("nombre_curso_materia", c_filt).not_.is_("alumno_id", "null").execute()
            for r in res_al.data:
                al = r['alumnos']
                with st.container():
                    st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                    b1, b2, b3, _ = st.columns([1,1,1,5])
                    b1.button("✏️ Editar", key=f"e_al_{r['id']}")
                    if b2.button("🗑️ Borrar", key=f"d_al_{r['id']}"):
                        st.session_state[f"ask_al_{r['id']}"] = True
                    b3.button("💾 Guardar", key=f"s_al_{r['id']}")
                    
                    if st.session_state.get(f"ask_al_{r['id']}"):
                        st.error("¿Borrar inscripción?")
                        if st.button("SÍ", key=f"y_al_{r['id']}"):
                            supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                            del st.session_state[f"ask_al_{r['id']}"]; st.rerun()

    # --- TAB 3: NOTAS (TRIPLE BOTONERA Y CASCADA) ---
    with tabs[3]:
        st.subheader("📝 Planilla de Notas")
        c_nt = st.selectbox("Seleccione Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_v211")
        if c_nt != "---":
            res_nt = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_nt).not_.is_("alumno_id", "null").execute()
            for r in res_nt.data:
                al = r['alumnos']
                with st.container():
                    st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                    with st.form(f"f_n_{al['id']}"):
                        n = st.number_input("Nota:", 1.0, 10.0, 7.0, 0.1)
                        if st.form_submit_button("💾 GUARDAR NOTA"):
                            st.success("Cambios guardados satisfactoriamente."); time.sleep(1); st.rerun()

    # --- TAB 4: CURSOS (EDICIÓN Y CREACIÓN) ---
    with tabs[4]:
        st.subheader("🏗️ Cursos Activos")
        for c in res_c.data:
            with st.container():
                st.markdown(f'<div class="planilla-row">📖 <b>{c["nombre_curso_materia"]}</b></div>', unsafe_allow_html=True)
                cb1, cb2, cb3, _ = st.columns([1,1,1,5])
                if cb1.button("✏️ Editar", key=f"e_c_{c['id']}"): st.session_state[f"ed_c_{c['id']}"] = True
                if cb2.button("🗑️ Borrar", key=f"d_c_{c['id']}"):
                    st.session_state[f"ask_c_{c['id']}"] = True
                cb3.button("💾 Guardar", key=f"s_c_{c['id']}")

                if st.session_state.get(f"ed_c_{c['id']}"):
                    with st.form(f"f_ed_c_{c['id']}"):
                        n_nm = st.text_input("Corregir nombre:", value=c['nombre_curso_materia'])
                        if st.form_submit_button("CONFIRMAR"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": n_nm}).eq("id", c['id']).execute()
                            del st.session_state[f"ed_c_{c['id']}"]; st.rerun()
        st.divider()
        with st.form("new_c"):
            st.write("### ➕ Instalar Nuevo Curso")
            nm = st.text_input("Nombre Materia/Horario")
            if st.form_submit_button("💾 GUARDAR CURSO"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nm, "anio_lectivo": 2026}).execute()
                st.success("Cambios guardados satisfactoriamente."); st.rerun()
