import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v184", layout="wide")

@st.cache_resource
def init_connection():
    url = "https://tzevdylabtradqmcqldx.supabase.co"
    key = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
    return create_client(url, key)

supabase = init_connection()

if 'user' not in st.session_state: st.session_state.user = None
if 'edit_mode' not in st.session_state: st.session_state.edit_mode = None

# --- ESTILO, RELOJ Y FECHA ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .card-curso { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 12px; border: 1px solid rgba(79, 172, 254, 0.3); margin-bottom: 10px; }
    #info-superior { position: fixed; top: 10px; right: 20px; font-family: 'JetBrains Mono', monospace; text-align: right; z-index: 10000; background: rgba(0,0,0,0.8); padding: 10px; border-radius: 8px; border: 1px solid #4facfe; }
    </style>
    """, unsafe_allow_html=True)

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
    setInterval(actualizarInfo, 1000); actualizarInfo();
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
    
    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 4: CURSOS (CON TRIPLE BOTONERA FUNCIONAL) ---
    with tabs[4]:
        st.subheader("🏗️ Mis Cursos Activos")
        if res_c.data:
            for cur in res_c.data:
                # Si el curso es el que estamos editando, mostrar formulario
                if st.session_state.edit_mode == cur['id']:
                    with st.form(f"edit_form_{cur['id']}"):
                        new_name = st.text_input("Editar Nombre/Horario:", value=cur['nombre_curso_materia'])
                        col_ef1, col_ef2 = st.columns(2)
                        if col_ef1.form_submit_button("💾 GUARDAR CAMBIOS"):
                            supabase.table("inscripciones").update({"nombre_curso_materia": new_name}).eq("id", cur['id']).execute()
                            st.session_state.edit_mode = None
                            st.rerun()
                        if col_ef2.form_submit_button("❌ CANCELAR"):
                            st.session_state.edit_mode = None
                            st.rerun()
                else:
                    # Vista normal con botones funcionales
                    with st.container():
                        st.markdown(f'<div class="card-curso">📖 <b>{cur["nombre_curso_materia"]}</b></div>', unsafe_allow_html=True)
                        c_b1, c_b2, _ = st.columns([1,1,6])
                        if c_b1.button("✏️ Editar", key=f"ed_{cur['id']}"):
                            st.session_state.edit_mode = cur['id']
                            st.rerun()
                        if c_b2.button("🗑️ Borrar", key=f"del_{cur['id']}"):
                            # Borra inscripciones y el curso
                            supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                            st.warning("Curso eliminado")
                            time.sleep(0.5); st.rerun()
        else:
            st.info("No hay cursos activos.")

        st.divider()
        with st.expander("➕ CREAR NUEVO CURSO", expanded=False):
            with st.form("new_cur"):
                n_m = st.text_input("Nombre de Materia")
                d_h = st.text_input("Días y Horarios")
                if st.form_submit_button("💾 INSTALAR CURSO"):
                    supabase.table("inscripciones").insert({
                        "profesor_id": u_data['id'], 
                        "nombre_curso_materia": f"{n_m} - {d_h}", 
                        "anio_lectivo": 2026
                    }).execute()
                    st.rerun()

    # --- TAB 0: AGENDA (CON RECORDATORIO DE TAREA) ---
    with tabs[0]:
        st.subheader("📅 Seguimiento de Clases")
        mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}
        if mapa_cursos:
            sel_ag = st.selectbox("Elegir Curso:", list(mapa_cursos.keys()))
            f_hoy = datetime.date.today()
            
            # Tarea para hoy
            res_t = supabase.table("bitacora").select("*").eq("inscripcion_id", mapa_cursos[sel_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_t.data:
                for t in res_t.data:
                    st.markdown(f'<div style="background:rgba(255,193,7,0.1); border:1px solid #ffc107; padding:15px; border-radius:10px;">🔔 <b>HOY DEBEN ENTREGAR:</b> {t["tarea_proxima"]}</div>', unsafe_allow_html=True)
            
            with st.form("f_agenda"):
                temas = st.text_area("Temas dictados hoy")
                recursos = st.text_input("Recursos/Materiales")
                st.divider()
                st.write("📌 **Próxima Tarea:**")
                col_t1, col_t2 = st.columns(2)
                t_desc = col_t1.text_area("Descripción")
                t_fecha = col_t2.date_input("Fecha de entrega", f_hoy + datetime.timedelta(days=7))
                if st.form_submit_button("💾 REGISTRAR"):
                    supabase.table("bitacora").insert({
                        "inscripcion_id": mapa_cursos[sel_ag], "fecha": str(f_hoy),
                        "contenido_clase": temas, "recursos_utilizados": recursos,
                        "tarea_proxima": t_desc, "fecha_tarea": str(t_fecha)
                    }).execute()
                    st.success("Guardado."); st.rerun()
