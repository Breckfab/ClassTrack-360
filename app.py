import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v183", layout="wide")

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
    .card-curso { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 12px; border: 1px solid rgba(79, 172, 254, 0.3); margin-bottom: 10px; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; }
    #info-superior { position: fixed; top: 10px; right: 20px; font-family: 'JetBrains Mono', monospace; text-align: right; z-index: 10000; background: rgba(0,0,0,0.8); padding: 10px; border-radius: 8px; border: 1px solid #4facfe; }
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
    st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Sede").strip().lower()
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("ENTRAR"):
            res = supabase.table("usuarios").select("*").eq("email", f"{u}.fabianbelledi@gmail.com").eq("password_text", p).execute()
            if res.data: st.session_state.user = res.data[0]; st.rerun()
else:
    u_data = st.session_state.user
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 4: CURSOS (ORDENADO: LISTADO ARRIBA, CREAR ABAJO) ---
    with tabs[4]:
        st.subheader("🏗️ Mis Cursos Activos")
        if res_c.data:
            for cur in res_c.data:
                with st.container():
                    st.markdown(f'<div class="card-curso">📖 <b>{cur["nombre_curso_materia"]}</b> | Año: {cur["anio_lectivo"]}</div>', unsafe_allow_html=True)
                    c_b1, c_b2, c_b3, _ = st.columns([1,1,1,5])
                    if c_b1.button("✏️ Editar", key=f"ed_{cur['id']}"): st.toast("Modo edición activado")
                    if c_b2.button("🗑️ Borrar", key=f"del_{cur['id']}"):
                        supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                        st.warning("Curso eliminado"); time.sleep(0.5); st.rerun()
                    if c_b3.button("💾 Guardar", key=f"sv_{cur['id']}"): st.success("Cambios guardados")
        else:
            st.info("Aún no tienes cursos creados.")

        st.divider()
        with st.expander("➕ CREAR NUEVO CURSO", expanded=False):
            with st.form("new_cur"):
                n_m = st.text_input("Nombre de Materia")
                d_h = st.text_input("Días y Horarios (ej: Mar/Jue 18hs)")
                if st.form_submit_button("💾 INSTALAR NUEVA MATERIA"):
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": f"{n_m} - {d_h}", "anio_lectivo": 2026}).execute()
                    st.rerun()

    # --- TAB 0: AGENDA INTELIGENTE ---
    with tabs[0]:
        st.subheader("📅 Seguimiento de Clases")
        if mapa_cursos:
            sel_ag = st.selectbox("Curso:", list(mapa_cursos.keys()))
            f_hoy = datetime.date.today()
            
            # REVISIÓN DE TAREA PROGRAMADA PARA HOY
            res_tarea = supabase.table("bitacora").select("*").eq("inscripcion_id", mapa_cursos[sel_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_tarea.data:
                for t in res_tarea.data:
                    st.markdown(f'<div class="card-tarea-hoy">🔔 <b>HOY DEBEN ENTREGAR:</b> {t["tarea_proxima"]}</div>', unsafe_allow_html=True)
            
            with st.form("f_agenda"):
                st.write(f"### Clase del {f_hoy.strftime('%d/%m/%Y')}")
                t_dictados = st.text_area("Temas tratados en clase")
                mat_usado = st.text_input("Material/Recursos")
                st.divider()
                st.write("📌 **Asignar Tareas:**")
                col_t1, col_t2 = st.columns(2)
                t_desc = col_t1.text_area("Descripción de la tarea")
                t_fecha = col_t2.date_input("Fecha de entrega", f_hoy + datetime.timedelta(days=7))
                if st.form_submit_button("💾 REGISTRAR ACTIVIDAD"):
                    supabase.table("bitacora").insert({
                        "inscripcion_id": mapa_cursos[sel_ag], "fecha": str(f_hoy),
                        "contenido_clase": t_dictados, "recursos_utilizados": mat_usado,
                        "tarea_proxima": t_desc, "fecha_tarea": str(t_fecha)
                    }).execute()
                    st.success("Actividad guardada."); st.rerun()
