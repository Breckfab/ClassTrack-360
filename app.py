import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v221", layout="wide")

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

    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 3: NOTAS (SIN NOTAS POR DEFECTO) ---
    with tabs[3]:
        sub_nt = st.radio("Acción:", ["Volcar Notas", "Consultar Notas"], horizontal=True)
        c_nt = st.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_v221")
        if c_nt != "---":
            res_al_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_nt).not_.is_("alumno_id", "null").execute()
            for r in res_al_n.data:
                al = r['alumnos']
                with st.container():
                    st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                    with st.form(f"nt_{al['id']}"):
                        # Nota vacía/neutra por defecto
                        n = st.number_input("Calificación:", min_value=0.0, max_value=10.0, value=0.0, step=0.1)
                        b1, b2, b3, _ = st.columns([1,1,1,5])
                        if b1.form_submit_button("💾 Guardar"):
                            supabase.table("notas").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": c_nt, "calificacion": n, "fecha": str(datetime.date.today())}).execute()
                            st.success("Cambios guardados satisfactoriamente.")
                        b2.form_submit_button("✏️ Editar")
                        b3.form_submit_button("🗑️ Borrar")

    # --- TAB 4: CURSOS (CON SELECTOR DE DÍAS) ---
    with tabs[4]:
        sub_cu = st.radio("Acción:", ["Listar Cursos", "Nuevo Curso"], horizontal=True)
        if sub_cu == "Nuevo Curso":
            with st.form("new_c_v221"):
                nom_m = st.text_input("Nombre de la Materia")
                st.write("Seleccione días de cursada:")
                dias = st.multiselect("Días:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                horario = st.text_input("Hora (ej: 18:00 a 20:00)")
                if st.form_submit_button("💾 INSTALAR CURSO"):
                    info_completa = f"{nom_m} ({', '.join(dias)}) - {horario}"
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": info_completa, "anio_lectivo": 2026}).execute()
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
