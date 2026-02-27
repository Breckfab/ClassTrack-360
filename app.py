import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- 1. NÚCLEO ---
st.set_page_config(page_title="ClassTrack 360 v238", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None

# --- 2. ESTILO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
    .tarea-alerta { background: rgba(255, 193, 7, 0.2); border: 2px dashed #ffc107; padding: 20px; border-radius: 10px; color: #ffc107; text-align: center; font-weight: bold; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÓGICA DE ACCESO ---
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
        components.html("""<div style="color:#4facfe;font-family:monospace;font-size:24px;text-align:center;"><div id="c">00:00:00</div></div><script>setInterval(()=>{document.getElementById('c').innerText=new Date().toLocaleTimeString('es-AR',{hour12:false})},1000);</script>""", height=50)
        if st.button("🚪 SALIR"): st.session_state.user = None; st.rerun()

    # MOTOR DE DATOS (CURSOS)
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (SENSOR DE TAREA ANTERIOR) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            c_ag = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_238")
            f_hoy = st.date_input("Fecha:", datetime.date.today())
            # Busca si en clases pasadas se dio tarea para HOY
            res_t = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_t.data:
                st.markdown(f'<div class="tarea-alerta">🔔 TAREA PARA ENTREGAR HOY:<br>{res_t.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            
            with st.form("f_ag_238"):
                temas, tarea_n = st.text_area("Temas dictados"), st.text_area("Tarea próxima")
                vto = st.date_input("Vencimiento:", f_hoy + datetime.timedelta(days=7))
                b1, b2, b3, _ = st.columns([1,1,1,5])
                if b1.form_submit_button("💾 Guardar"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": tarea_n, "fecha_tarea": str(vto)}).execute()
                    st.success("Guardado."); st.rerun()
                b2.form_submit_button("✏️ Editar")
                b3.form_submit_button("🗑️ Borrar")

    # --- TAB 1: ALUMNOS (CONSULTA / NUEVO - BLINDADO) ---
    with tabs[1]:
        sub_al = st.radio("Acción:", ["Consulta de Alumnos", "Nuevo Alumno"], horizontal=True)
        if sub_al == "Nuevo Alumno":
            with st.form("new_al"):
                n, a = st.text_input("Nombre"), st.text_input("Apellido")
                c_ins = st.selectbox("Asignar a:", list(mapa_cursos.keys()))
                if st.form_submit_button("💾 REGISTRAR"):
                    ra = supabase.table("alumnos").insert({"nombre": n, "apellido": a}).execute()
                    supabase.table("inscripciones").insert({"alumno_id": ra.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": c_ins, "anio_lectivo": 2026}).execute()
                    st.success("Satisfactorio."); st.rerun()
        else:
            c_v = st.selectbox("Seleccione Curso:", ["---"] + list(mapa_cursos.keys()), key="al_v238")
            if c_v != "---":
                res_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_v).not_.is_("alumno_id", "null").execute()
                for r in res_al.data:
                    # Extractor Blindado (Evita Error 117)
                    al = r['alumnos'][0] if isinstance(r['alumnos'], list) else r['alumnos']
                    if al:
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        ab1, ab2, ab3, _ = st.columns([1,1,1,5])
                        ab1.button("✏️ Editar", key=f"eal_{r['id']}")
                        if ab2.button("🗑️ Borrar", key=f"dal_{r['id']}"):
                            supabase.table("inscripciones").delete().eq("id", r['id']).execute(); st.rerun()
                        ab3.button("💾 Guardar", key=f"sal_{r['id']}")

    # --- TAB 4: CURSOS (DETALLADO) ---
    with tabs[4]:
        sub_cu = st.radio("Acción:", ["Listar Cursos", "Nuevo Curso"], horizontal=True)
        if sub_cu == "Nuevo Curso":
            with st.form("new_c"):
                mat = st.text_input("Materia")
                dias = st.multiselect("Días:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                hor = st.text_input("Horario")
                if st.form_submit_button("💾 INSTALAR"):
                    info = f"{mat} ({', '.join(dias)}) | {hor}"
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": info, "anio_lectivo": 2026}).execute()
                    st.success("Satisfactorio."); st.rerun()
        else:
            for c in res_c.data:
                st.markdown(f'<div class="planilla-row">📖 {c["nombre_curso_materia"]}</div>', unsafe_allow_html=True)
                cb1, cb2, cb3, _ = st.columns([1,1,1,5])
                cb1.button("✏️ Editar", key=f"ec_{c['id']}")
                if cb2.button("🗑️ Borrar", key=f"dc_{c['id']}"):
                    supabase.table("inscripciones").delete().eq("id", c['id']).execute(); st.rerun()
                cb3.button("💾 Guardar", key=f"sc_{c['id']}")
