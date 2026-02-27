import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v223", layout="wide")

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
        components.html(f"""<div style="color:#4facfe;font-family:monospace;font-size:24px;text-align:center;"><div id="c">00:00:00</div></div><script>setInterval(()=>{{document.getElementById('c').innerText=new Date().toLocaleTimeString('es-AR',{{hour12:false}})}},1000);</script>""", height=50)
        if st.button("🚪 SALIR"): st.session_state.user = None; st.rerun()

    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            c_ag = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_sel")
            f_hoy = st.date_input("Fecha:", datetime.date.today())
            res_t = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_t.data: st.markdown(f'<div class="tarea-alerta">🔔 TAREA PENDIENTE PARA HOY:<br>{res_t.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            with st.form("f_ag"):
                t_hoy = st.text_area("Temas dictados")
                t_pro = st.text_area("Tarea para la próxima")
                vto = st.date_input("Vencimiento:", f_hoy + datetime.timedelta(days=7))
                b1, b2, b3, _ = st.columns([1,1,1,5])
                if b1.form_submit_button("💾 Guardar"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": t_hoy, "tarea_proxima": t_pro, "fecha_tarea": str(vto)}).execute()
                    st.success("Guardado."); st.rerun()
                b2.form_submit_button("✏️ Editar")
                b3.form_submit_button("🗑️ Borrar")

    # --- TAB 2: ASISTENCIA ---
    with tabs[2]:
        sub = st.radio("Acción:", ["Tomar Asistencia", "Consultar Asistencia"], horizontal=True)
        c_as = st.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="as_sel")
        if c_as != "---":
            if sub == "Tomar Asistencia":
                res_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_as).not_.is_("alumno_id", "null").execute()
                for r in res_al.data:
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {r["alumnos"]["apellido"].upper()}, {r["alumnos"]["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"as_{r['alumnos']['id']}"):
                            est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                            if st.form_submit_button("💾 Guardar"):
                                supabase.table("asistencia").insert({"alumno_id": r['alumnos']['id'], "profesor_id": u_data['id'], "materia": c_as, "estado": est, "fecha": str(datetime.date.today())}).execute()
                                st.success("Guardado.")
            else:
                res_h = supabase.table("asistencia").select("estado").eq("materia", c_as).execute()
                if res_h.data:
                    df = pd.DataFrame(res_h.data)
                    st.write(f"✅ Presentes: {len(df[df.estado=='Presente'])} | ❌ Ausentes: {len(df[df.estado=='Ausente'])}")
                else: st.info("No hay datos.")

    # --- TAB 3: NOTAS ---
    with tabs[3]:
        sub_n = st.radio("Acción:", ["Volcar Notas", "Consultar Notas"], horizontal=True)
        c_nt = st.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_sel")
        if c_nt != "---":
            if sub_n == "Volcar Notas":
                res_al_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_nt).not_.is_("alumno_id", "null").execute()
                for r in res_al_n.data:
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {r["alumnos"]["apellido"].upper()}, {r["alumnos"]["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"nt_{r['alumnos']['id']}"):
                            n = st.number_input("Nota:", 0.0, 10.0, value=0.0)
                            b1, b2, b3, _ = st.columns([1,1,1,5])
                            if b1.form_submit_button("💾 Guardar"): st.success("Guardado.")
                            b2.form_submit_button("✏️ Editar")
                            b3.form_submit_button("🗑️ Borrar")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        sub_c = st.radio("Acción:", ["Listar Cursos", "Nuevo Curso"], horizontal=True)
        if sub_c == "Nuevo Curso":
            with st.form("new_c"):
                nom = st.text_input("Nombre Materia")
                dias = st.multiselect("Días:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                hor = st.text_input("Horario (ej: 18:00 a 20:00)")
                if st.form_submit_button("💾 INSTALAR"):
                    info = f"{nom} ({', '.join(dias)}) | {hor}"
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": info, "anio_lectivo": 2026}).execute()
                    st.success("Cambios guardados satisfactoriamente."); st.rerun()
        else:
            for c in res_c.data:
                with st.container():
                    st.markdown(f'<div class="planilla-row">📖 {c["nombre_curso_materia"]}</div>', unsafe_allow_html=True)
                    b1, b2, b3, _ = st.columns([1,1,1,5])
                    b1.button("✏️ Editar", key=f"e_c_{c['id']}")
                    if b2.button("🗑️ Borrar", key=f"d_c_{c['id']}"):
                        supabase.table("inscripciones").delete().eq("id", c['id']).execute(); st.rerun()
                    b3.button("💾 Guardar", key=f"s_c_{c['id']}")
