import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v217", layout="wide")

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
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.header(f"Sede: {u_data['email'].split('.')[0].upper()}")
        components.html(f"""
            <div style="color: #4facfe; font-family: monospace; font-size: 24px; font-weight: bold; text-align: center;">
                <div id="d" style="font-size: 13px; color: #aaa;">{datetime.date.today()}</div>
                <div id="c">00:00:00</div>
            </div>
            <script>
                function update() {{
                    const n = new Date();
                    document.getElementById('c').innerText = n.toLocaleTimeString('es-AR', {{hour12:false}});
                }}
                setInterval(update, 1000); update();
            </script>
        """, height=90)
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- CARGA DE DATOS ---
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (CON CALENDARIO Y TAREA) ---
    with tabs[0]:
        st.subheader("📅 Agenda y Tareas")
        if not mapa_cursos: st.warning("Cree un curso primero.")
        else:
            c_sel = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_v217")
            f_hoy = st.date_input("Fecha (Calendario):", datetime.date.today())
            
            # Buscar tarea grabada para HOY
            res_t = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_sel]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_t.data:
                st.markdown(f'<div class="tarea-alerta">🔔 TAREA PENDIENTE PARA HOY:<br>{res_t.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            
            with st.form("f_ag"):
                temas = st.text_area("Temas dictados")
                tarea = st.text_area("Tarea para la próxima")
                vto = st.date_input("Vence el:", f_hoy + datetime.timedelta(days=7))
                if st.form_submit_button("💾 GUARDAR AGENDA"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_sel], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": tarea, "fecha_tarea": str(vto)}).execute()
                    st.success("Cambios guardados satisfactoriamente."); time.sleep(1); st.rerun()

    # --- TAB 4: CURSOS (RECUPERADO) ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Cursos")
        with st.form("new_cur"):
            st.write("### ➕ Crear Nuevo Curso")
            nc = st.text_input("Nombre del Curso (ej: 1ero Psicología)")
            if st.form_submit_button("💾 INSTALAR CURSO"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.success("Cambios guardados satisfactoriamente."); st.rerun()
        
        st.divider()
        if res_c.data:
            for c in res_c.data:
                with st.container():
                    st.markdown(f'<div class="planilla-row">📖 {c["nombre_curso_materia"]}</div>', unsafe_allow_html=True)
                    b1, b2, b3, _ = st.columns([1,1,1,5])
                    b1.button("✏️ Editar", key=f"ec_{c['id']}")
                    if b2.button("🗑️ Borrar", key=f"dc_{c['id']}"):
                        supabase.table("inscripciones").delete().eq("id", c['id']).execute(); st.rerun()
                    b3.button("💾 Guardar", key=f"sc_{c['id']}")

    # --- TABS ALUMNOS, ASISTENCIA Y NOTAS ---
    with tabs[1]:
        st.subheader("👥 Alumnos")
        if mapa_cursos:
            c_ins = st.selectbox("Seleccione Curso para ver Alumnos:", ["---"] + list(mapa_cursos.keys()))
            if c_ins != "---":
                # Formulario para agregar
                with st.expander("Inscribir Nuevo Alumno"):
                    with st.form("f_al"):
                        nom, ape = st.text_input("Nombre"), st.text_input("Apellido")
                        if st.form_submit_button("💾 REGISTRAR"):
                            ra = supabase.table("alumnos").insert({"nombre": nom, "apellido": ape}).execute()
                            supabase.table("inscripciones").insert({"alumno_id": ra.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": c_ins, "anio_lectivo": 2026}).execute()
                            st.success("Alumno inscrito."); st.rerun()
