import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360 v154", layout="wide")

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: 
    st.session_state.user = None

# --- ESTILO CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .filter-box { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #4facfe; }
    .promedio-badge { background: #4facfe; color: #0b0e14; padding: 2px 8px; border-radius: 5px; font-weight: bold; font-family: 'JetBrains Mono'; }
    </style>
    """, unsafe_allow_html=True)

# --- RELOJ ---
components.html("""
    <div id="rtc" style="position:fixed; top:10px; right:25px; font-family:'JetBrains Mono',monospace; font-size:1rem; color:white; z-index:9999;">--:--:--</div>
    <script>
    function t(){
        const n=new Date();
        const h=String(n.getHours()).padStart(2,'0');
        const m=String(n.getMinutes()).padStart(2,'0');
        const s=String(n.getSeconds()).padStart(2,'0');
        document.getElementById('rtc').innerText=h+":"+m+":"+s;
    }
    setInterval(t,1000); t();
    </script>
    """, height=40)

# --- LOGIN OPTIMIZADO ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v154", clear_on_submit=False):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            submit = st.form_submit_button("ENTRAR AL SISTEMA", use_container_width=True)
            
            if submit:
                email = f"{u_in}.fabianbelledi@gmail.com" if u_in in ["cambridge", "daguerre"] else ""
                if email:
                    success_login = False
                    for _ in range(2):  # Reintento automático para evitar el error de conexión
                        try:
                            res = supabase.table("usuarios").select("*").eq("email", email).eq("password_text", p_in).execute()
                            if res and res.data:
                                st.session_state.user = res.data[0]
                                success_login = True
                                break
                        except:
                            time.sleep(0.5)
                    
                    if success_login:
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas o problema de red.")
                else:
                    st.error("Sede no reconocida.")
else:
    u_data = st.session_state.user
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"📍 Sede: {u_data['email'].split('.')[0].capitalize()}")
        st.divider()
        if st.button("🚪 SALIR", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c.data: mapa_cursos = {row['nombre_curso_materia']: row['id'] for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        st.subheader("👥 Gestión de Alumnos")
        with st.expander("➕ INSCRIBIR NUEVO ALUMNO"):
            with st.form("ins_al_v154"):
                nn, na = st.text_input("Nombre"), st.text_input("Apellido")
                nc = st.selectbox("Curso / Materia:", list(mapa_cursos.keys()) if mapa_cursos else ["Sin cursos"])
                if st.form_submit_button("💾 REGISTRAR E INSCRIBIR"):
                    if nn and na and mapa_cursos:
                        res_a = supabase.table("alumnos").insert({"nombre": nn, "apellido": na}).execute()
                        if res_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": res_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                            st.success(f"Alumno {na} inscripto.")
                            st.rerun()

    # --- TAB 2: ASISTENCIA (PLANILLA COLECTIVA) ---
    with tabs[2]:
        st.subheader("✅ Planilla de Asistencia")
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        sel_as_c = st.selectbox("📍 Llamar Curso:", ["---"] + list(mapa_cursos.keys()), key="as_v154")
        st.markdown('</div>', unsafe_allow_html=True)
        if sel_as_c != "---":
            r_as = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_as_c).not_.is_("alumno_id", "null").execute()
            if r_as.data:
                for it in r_as.data:
                    al = it['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"as_{al['id']}_{sel_as_c}"):
                            est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                            c1, c2, c3 = st.columns(3)
                            if c1.form_submit_button("💾 GUARDAR"):
                                supabase.table("asistencia").insert({"alumno_id": al['id'], "materia": sel_as_c, "estado": est, "fecha": str(datetime.date.today())}).execute()
                                st.success("Ok")
                            if c2.form_submit_button("🔄 CANCELAR"): st.rerun()
                            if c3.form_submit_button("🗑️ BORRAR"): st.rerun()

    # --- TAB 3: NOTAS (PLANILLA + PROMEDIO) ---
    with tabs[3]:
        st.subheader("📝 Planilla de Calificaciones")
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        sel_nt_c = st.selectbox("📍 Seleccionar Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_v154")
        st.markdown('</div>', unsafe_allow_html=True)
        if sel_nt_c != "---":
            r_nt = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", sel_nt_c).not_.is_("alumno_id", "null").execute()
            if r_nt.data:
                for it in r_nt.data:
                    al = it['alumnos']
                    res_notas = supabase.table("notas").select("calificacion").eq("alumno_id", al['id']).eq("materia", sel_nt_c).execute()
                    promedio = sum([n['calificacion'] for n in res_notas.data]) / len(res_notas.data) if res_notas.data else 0
                    with st.container():
                        st.markdown(f'<div class="planilla-row">📝 {al["apellido"].upper()}, {al["nombre"]} <span style="float:right;">Promedio: <span class="promedio-badge">{promedio:.2f}</span></span></div>', unsafe_allow_html=True)
                        with st.form(f"nt_{al['id']}_{sel_nt_c}"):
                            n_val = st.number_input("Nota", 1, 10, 7)
                            n_ins = st.text_input("Instancia (Ej: TP1)")
                            if st.form_submit_button("💾 GRABAR NOTA"):
                                supabase.table("notas").insert({"alumno_id": al['id'], "materia": sel_nt_c, "calificacion": n_val, "tipo_nota": n_ins, "fecha": str(datetime.date.today())}).execute()
                                st.success("Grabado")
                                st.rerun()

    # --- TAB 0 Y 4: AGENDA Y CURSOS ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if mapa_cursos:
            sel_ag = st.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()))
            if sel_ag != "---":
                with st.form("f_ag_v154"):
                    f_h = datetime.date.today()
                    st.info(f"Fecha: {f_h.strftime('%d/%m/%Y')}")
                    temas = st.text_area("Temas hoy")
                    f_ent = st.date_input("Próxima tarea", value=f_h + datetime.timedelta(days=7))
                    desc_t = st.text_area("Detalle tarea")
                    if st.form_submit_button("💾 GUARDAR AGENDA"):
                        supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[sel_ag], "fecha": str(f_h), "contenido_clase": temas, "tarea_proxima": desc_t, "fecha_tarea": str(f_ent)}).execute()
                        st.success("Guardado")

    with tabs[4]:
        st.subheader("🏗️ Cursos")
        with st.form("new_c_v154"):
            nom_c = st.text_input("Nombre Materia")
            if st.form_submit_button("💾 CREAR MATERIA"):
                if nom_c:
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nom_c, "anio_lectivo": 2026}).execute()
                    st.rerun()
