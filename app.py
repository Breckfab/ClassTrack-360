import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v224", layout="wide")

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
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
    
    with st.sidebar:
        st.header(f"Sede: {u_data['email'].split('.')[0].upper()}")
        components.html(f"""<div style="color:#4facfe;font-family:monospace;font-size:24px;text-align:center;"><div id="c">00:00:00</div></div><script>setInterval(()=>{{document.getElementById('c').innerText=new Date().toLocaleTimeString('es-AR',{{hour12:false}})}},1000);</script>""", height=50)
        if st.button("🚪 SALIR"): st.session_state.user = None; st.rerun()

    # MOTOR DE DATOS
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (SENSOR RETROACTIVO) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            c_ag = st.selectbox("Seleccione Curso:", list(mapa_cursos.keys()), key="ag_sel_v224")
            f_hoy = st.date_input("Fecha de hoy:", datetime.date.today())
            
            # BUSCAR TAREA QUE VENCE HOY (Programada en clase anterior)
            res_t = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            
            if res_t.data:
                st.markdown(f'<div class="tarea-alerta">🔔 TAREA QUE DEBÍA ENTREGARSE HOY:<br>{res_t.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            else:
                st.info("No había tareas programadas para esta fecha.")

            with st.form("f_ag_v224"):
                temas = st.text_area("Temas dictados hoy:")
                n_tarea = st.text_area("Nueva tarea para la próxima:")
                vto = st.date_input("Fecha de entrega de la nueva tarea:", f_hoy + datetime.timedelta(days=7))
                col_b1, col_b2, col_b3, _ = st.columns([1,1,1,5])
                if col_b1.form_submit_button("💾 Guardar"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": n_tarea, "fecha_tarea": str(vto)}).execute()
                    st.success("Cambios guardados satisfactoriamente."); time.sleep(1); st.rerun()
                col_b2.form_submit_button("✏️ Editar")
                col_b3.form_submit_button("🗑️ Borrar")

    # --- TAB 2: ASISTENCIA (SUB-ITEMS) ---
    with tabs[2]:
        sub_as = st.radio("Acción:", ["Tomar Asistencia", "Consultar Asistencia"], horizontal=True)
        c_as = st.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="as_sel_v224")
        if c_as != "---":
            if sub_as == "Tomar Asistencia":
                res_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_as).not_.is_("alumno_id", "null").execute()
                for r in res_al.data:
                    al = r['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"asist_{al['id']}"):
                            est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                            if st.form_submit_button("💾 GUARDAR"):
                                supabase.table("asistencia").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": c_as, "estado": est, "fecha": str(datetime.date.today())}).execute()
                                st.success("Guardado satisfactoriamente.")
            else:
                st.info("Historial de asistencia en desarrollo...")

    # --- TAB 4: CURSOS (NUEVO CURSO DETALLADO) ---
    with tabs[4]:
        sub_cu = st.radio("Acción:", ["Listar Cursos", "Nuevo Curso"], horizontal=True)
        if sub_cu == "Nuevo Curso":
            with st.form("new_c_v224"):
                nom_m = st.text_input("Materia")
                dias = st.multiselect("Días:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                hor = st.text_input("Horario (ej: 18:00 a 20:00)")
                if st.form_submit_button("💾 INSTALAR CURSO"):
                    info = f"{nom_m} ({', '.join(dias)}) | {hor}"
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": info, "anio_lectivo": 2026}).execute()
                    st.success("Cambios guardados satisfactoriamente."); st.rerun()
        else:
            for c in res_c.data:
                with st.container():
                    st.markdown(f'<div class="planilla-row">📖 {c["nombre_curso_materia"]}</div>', unsafe_allow_html=True)
                    cb1, cb2, cb3, _ = st.columns([1,1,1,5])
                    cb1.button("✏️ Editar", key=f"ec_{c['id']}")
                    if cb2.button("🗑️ Borrar", key=f"dc_{c['id']}"):
                        supabase.table("inscripciones").delete().eq("id", c['id']).execute(); st.rerun()
                    cb3.button("💾 Guardar", key=f"sc_{c['id']}")
