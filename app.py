import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360 v136", layout="wide")

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: 
    st.session_state.user = None

# --- ESTILO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .st-active { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 8px; border-radius: 4px; background: rgba(0,255,0,0.1); }
    .st-inactive { color: #ff4b4b; font-weight: bold; border: 1px solid #ff4b4b; padding: 2px 8px; border-radius: 4px; background: rgba(255,75,75,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- RELOJ ---
components.html("""
    <div id="rtc" style="position:fixed; top:10px; right:25px; font-family:'JetBrains Mono',monospace; font-size:1rem; color:white; font-weight:400; z-index:9999;">--:--:--</div>
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

# --- LOGIN ---
if st.session_state.user is None:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="logo-text">ClassTrack 360</div>', unsafe_allow_html=True)
        with st.form("login_v136"):
            u_in = st.text_input("Sede").strip().lower()
            p_in = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
                email = f"{u_in}.fabianbelledi@gmail.com" if u_in in ["cambridge", "daguerre"] else ""
                if email:
                    try:
                        res = supabase.table("usuarios").select("*").eq("email", email).eq("password_text", p_in).execute()
                        if res and res.data:
                            st.session_state.user = res.data[0]
                            st.rerun()
                        else: st.error("Clave incorrecta.")
                    except: st.error("Error de conexión.")
                else: st.error("Sede no reconocida.")
else:
    u_data = st.session_state.user
    with st.sidebar:
        st.markdown('<div class="logo-text" style="font-size:1.5rem; text-align:left;">CT360</div>', unsafe_allow_html=True)
        st.write(f"📍 Sede: {'Daguerre' if 'daguerre' in u_data['email'].lower() else 'Cambridge'}")
        st.divider()
        if st.button("🚪 SALIR DEL SISTEMA", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    # --- CARGA MAESTRA ---
    mapa_cursos = {}
    try:
        r_c = supabase.table("inscripciones").select("id, nombre_curso_materia, estado").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if r_c and r_c.data: 
            mapa_cursos = {row['nombre_curso_materia']: {"id": row['id'], "estado": row.get('estado', 'ACTIVO')} for row in r_c.data}
    except: pass

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 4: CURSOS (REFORZADO) ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Materias")
        
        # Formulario de creación con manejo de errores explícito
        with st.form("crear_materia_v136"):
            st.write("### ➕ Registrar Nueva Materia")
            nueva_m = st.text_input("Nombre de la Materia / Curso")
            if st.form_submit_button("💾 GRABAR MATERIA"):
                if nueva_m:
                    try:
                        # Intentamos la grabación con los campos mínimos requeridos
                        datos_insert = {
                            "profesor_id": u_data['id'],
                            "nombre_curso_materia": nueva_m,
                            "estado": "ACTIVO",
                            "anio_lectivo": 2026
                        }
                        res = supabase.table("inscripciones").insert(datos_insert).execute()
                        
                        if res.data:
                            st.success(f"✅ ¡MATERIA REGISTRADA! '{nueva_m}' ya aparece en tu lista.")
                            st.rerun()
                        else:
                            st.error("⚠️ La base de datos no devolvió confirmación. Revisa los permisos.")
                    except Exception as e:
                        st.error(f"❌ Error crítico al grabar: {str(e)}")
                else:
                    st.warning("Escribe el nombre de la materia antes de grabar.")

        st.divider()
        st.write("### Materias Registradas")
        if mapa_cursos:
            for n, info in mapa_cursos.items():
                est_css = "st-active" if info["estado"] == "ACTIVO" else "st-inactive"
                with st.expander(f"📘 {n}"):
                    st.markdown(f'<span class="{est_css}">{info["estado"]}</span>', unsafe_allow_html=True)
                    # Botonera Triple
                    with st.form(f"ops_curso_{info['id']}"):
                        new_nom = st.text_input("Editar Nombre", value=n)
                        new_est = st.selectbox("Estado", ["ACTIVO", "INACTIVO"], index=0 if info["estado"] == "ACTIVO" else 1)
                        c1, c2, c3 = st.columns(3)
                        if c1.form_submit_button("💾 GUARDAR"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": new_nom, "estado": new_est}).eq("id", info['id']).execute()
                            st.rerun()
                        if c2.form_submit_button("🔄 CANCELAR"): st.rerun()
                        if c3.form_submit_button("🗑️ BORRAR DEFINITIVO"):
                            supabase.table("inscripciones").delete().eq("id", info['id']).execute()
                            st.rerun()
        else:
            st.info("No hay materias registradas. Usa el formulario de arriba para empezar.")

    # --- TAB 0: AGENDA (CON PROTECCIÓN) ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if not mapa_cursos:
            st.warning("⚠️ Debes registrar una materia en la pestaña 'Cursos' antes de usar la Agenda.")
        else:
            sel_ag = st.selectbox("Elegir Materia:", ["---"] + list(mapa_cursos.keys()), key="ag_v136")
            if sel_ag != "---":
                with st.form("f_ag_v136"):
                    st.write(f"Fecha: {datetime.date.today().strftime('%d/%m/%Y')}")
                    temas = st.text_area("Dictado de hoy")
                    f_tar = st.date_input("Fecha de Tarea", value=datetime.date.today() + datetime.timedelta(days=7))
                    desc_tar = st.text_area("Detalle de Tarea")
                    if st.form_submit_button("💾 GUARDAR AGENDA"):
                        supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[sel_ag]["id"], "fecha": str(datetime.date.today()), "contenido_clase": temas, "tarea_proxima": desc_tar, "fecha_tarea": str(f_tar)}).execute()
                        st.success("Agenda guardada.")

    # --- TAB 1: ALUMNOS (CARGA DINÁMICA) ---
    with tabs[1]:
        st.subheader("👥 Alumnos")
        if not mapa_cursos:
            st.warning("⚠️ Registra una materia primero para poder inscribir alumnos.")
        else:
            with st.expander("➕ INSCRIBIR ALUMNO"):
                with st.form("ins_al_v136"):
                    nom, ape = st.text_input("Nombre"), st.text_input("Apellido")
                    cur = st.selectbox("Materia:", list(mapa_cursos.keys()))
                    if st.form_submit_button("💾 REGISTRAR"):
                        r_a = supabase.table("alumnos").insert({"nombre": nom, "apellido": ape}).execute()
                        if r_a.data:
                            supabase.table("inscripciones").insert({"alumno_id": r_a.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": cur}).execute()
                            st.rerun()
