import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN INTEGRAL ---
st.set_page_config(page_title="ClassTrack 360 v222", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- ESTILO CLASSTRACK ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
    .tarea-alerta { background: rgba(255, 193, 7, 0.2); border: 2px dashed #ffc107; padding: 20px; border-radius: 10px; color: #ffc107; text-align: center; font-weight: bold; margin-bottom: 25px; }
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
    
    # --- SIDEBAR CON RELOJ ---
    with st.sidebar:
        st.header(f"Sede: {u_data['email'].split('.')[0].upper()}")
        components.html(f"""
            <div style="color: #4facfe; font-family: monospace; font-size: 24px; font-weight: bold; text-align: center;">
                <div id="c">00:00:00</div>
            </div>
            <script>
                function update() {{
                    const n = new Date();
                    document.getElementById('c').innerText = n.toLocaleTimeString('es-AR', {{hour12:false}});
                }}
                setInterval(update, 1000); update();
            </script>
        """, height=50)
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- MOTOR DE DATOS SEGURO ---
    try:
        res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}
    except:
        mapa_cursos = {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (DETECTOR DE TAREAS) ---
    with tabs[0]:
        st.subheader("📅 Agenda y Seguimiento")
        if mapa_cursos:
            c_ag = st.selectbox("Seleccione Curso:", list(mapa_cursos.keys()), key="ag_222")
            f_hoy = st.date_input("Fecha de hoy:", datetime.date.today())
            
            # Buscar si hay una tarea que vence HOY para este curso
            res_t = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_t.data:
                st.markdown(f'<div class="tarea-alerta">🔔 TAREA PENDIENTE PARA HOY:<br>{res_t.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            
            with st.form("f_agenda_222"):
                temas = st.text_area("Temas dictados hoy:")
                prox_tarea = st.text_area("Tarea para la próxima clase:")
                vto = st.date_input("Vencimiento tarea:", f_hoy + datetime.timedelta(days=7))
                if st.form_submit_button("💾 GUARDAR AGENDA"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": prox_tarea, "fecha_tarea": str(vto)}).execute()
                    st.success("Cambios guardados satisfactoriamente."); st.rerun()

    # --- TAB 2: ASISTENCIA (PLANILLA COLECTIVA) ---
    with tabs[2]:
        st.subheader("✅ Tomar Asistencia")
        if mapa_cursos:
            c_as = st.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="as_222")
            if c_as != "---":
                res_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_as).not_.is_("alumno_id", "null").execute()
                if not res_al.data: st.info("No hay alumnos en este curso.")
                for r in res_al.data:
                    al = r['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 <b>{al["apellido"].upper()}, {al["nombre"]}</b></div>', unsafe_allow_html=True)
                        with st.form(f"asist_{al['id']}"):
                            est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                            b1, b2, b3, _ = st.columns([1,1,1,5])
                            if b1.form_submit_button("💾 Guardar"):
                                supabase.table("asistencia").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": c_as, "estado": est, "fecha": str(datetime.date.today())}).execute()
                                st.success("Guardado satisfactoriamente.")
                            b2.form_submit_button("✏️ Editar")
                            b3.form_submit_button("🗑️ Borrar")

    # --- TAB 4: CURSOS (NUEVO CURSO CON DÍAS) ---
    with tabs[4]:
        sub_c = st.radio("Acción:", ["Listar Cursos", "Nuevo Curso"], horizontal=True)
        if sub_c == "Nuevo Curso":
            with st.form("new_curso_222"):
                nom_m = st.text_input("Nombre Materia")
                dias_sel = st.multiselect("Días de cursada:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                hora_c = st.text_input("Horario")
                if st.form_submit_button("💾 INSTALAR"):
                    info = f"{nom_m} ({', '.join(dias_sel)}) | {hora_c}"
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": info, "anio_lectivo": 2026}).execute()
                    st.success("Cambios guardados satisfactoriamente."); st.rerun()
