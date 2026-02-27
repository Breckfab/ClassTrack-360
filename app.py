import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v193", layout="wide")

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
    .stApp { background: linear-gradient(135deg, #0b0e14 0%, #1e293b 100%); color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 5px; }
    .kpi-card { background: rgba(79, 172, 254, 0.1); border: 1px solid #4facfe; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; }
    #info-superior { position: fixed; top: 10px; right: 20px; font-family: 'JetBrains Mono', monospace; text-align: right; z-index: 10000; background: rgba(0,0,0,0.8); padding: 10px; border-radius: 8px; border: 1px solid #4facfe; }
    </style>
    """, unsafe_allow_html=True)

# --- RELOJ Y FECHA ---
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
        if st.form_submit_button("ENTRAR AL SISTEMA"):
            res = supabase.table("usuarios").select("*").eq("email", f"{u}.fabianbelledi@gmail.com").eq("password_text", p).execute()
            if res.data: st.session_state.user = res.data[0]; st.rerun()
            else: st.error("Acceso denegado.")
else:
    u_data = st.session_state.user
    
    # --- CARGA DE CURSOS ---
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB ALUMNOS: AUDITORÍA DE DUPLICADOS ---
    with tabs[1]:
        st.subheader("👥 Auditoría y Gestión de Alumnos")
        
        # 1. LISTADO PARA DETECTAR DUPLICADOS
        st.write("### 🔍 Lista General de Inscriptos")
        res_lista = supabase.table("inscripciones").select("id, nombre_curso_materia, alumnos(id, nombre, apellido, dni)").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
        
        if res_lista.data:
            df_audit = []
            for r in res_lista.data:
                al = r['alumnos']
                df_audit.append({
                    "ID Registro": r['id'],
                    "Apellido": al['apellido'].upper(),
                    "Nombre": al['nombre'],
                    "DNI": al['dni'],
                    "Curso": r['nombre_curso_materia']
                })
            st.table(df_audit) # Mostramos tabla fija para que Fabián vea los IDs
            
            st.write("### 🗑️ Eliminar Duplicados")
            col_id, col_btn = st.columns([2, 1])
            id_a_borrar = col_id.text_input("Pegue aquí el 'ID Registro' que desea borrar:")
            if col_btn.button("Borrar Registro Seleccionado"):
                if id_a_borrar:
                    supabase.table("inscripciones").delete().eq("id", id_a_borrar).execute()
                    st.success(f"Registro {id_a_borrar} eliminado satisfactoriamente."); time.sleep(1); st.rerun()
        else:
            st.info("No hay alumnos inscriptos aún.")

    # --- TAB AGENDA: ANTIBLOQUEO ---
    with tabs[0]:
        st.subheader("📅 Agenda")
        if not mapa_cursos:
            st.warning("Debe crear un curso para ver la agenda.")
        else:
            sel_cur_ag = st.selectbox("Curso:", list(mapa_cursos.keys()))
            f_hoy = datetime.date.today()
            
            # Buscador por fecha
            f_busq = st.date_input("Consultar fecha:", f_hoy)
            
            try:
                res_ag = supabase.table("bitacora").select("*").eq("inscripcion_id", mapa_cursos[sel_cur_ag]).eq("fecha", str(f_busq)).execute()
                
                with st.form("f_agenda_v193"):
                    tema_h = res_ag.data[0]['contenido_clase'] if res_ag.data else ""
                    tarea_h = res_ag.data[0]['tarea_proxima'] if res_ag.data else ""
                    
                    st.text_area("Temas dictados:", value=tema_h, key="tema_ag")
                    st.text_area("Tarea próxima:", value=tarea_h, key="tarea_ag")
                    
                    c1, c2, c3, _ = st.columns([1,1,1,4])
                    if c1.form_submit_button("💾 GUARDAR"):
                        data_ag = {"inscripcion_id": mapa_cursos[sel_cur_ag], "fecha": str(f_busq), "contenido_clase": st.session_state.tema_ag, "tarea_proxima": st.session_state.tarea_ag}
                        if res_ag.data:
                            supabase.table("bitacora").update(data_ag).eq("id", res_ag.data[0]['id']).execute()
                        else:
                            supabase.table("bitacora").insert(data_ag).execute()
                        st.success("Satisactorio."); st.rerun()
                    c2.form_submit_button("✏️ EDITAR")
                    c3.form_submit_button("❌ CANCELAR")
            except Exception as e:
                st.error(f"Error en Agenda: {e}")

    # --- TAB CURSOS ---
    with tabs[4]:
        st.subheader("🏗️ Cursos")
        if res_c.data:
            for c in res_c.data:
                with st.container():
                    st.markdown(f'<div class="planilla-row">📖 {c["nombre_curso_materia"]}</div>', unsafe_allow_html=True)
                    bc1, bc2, _ = st.columns([1,1,6])
                    if bc2.button("🗑️ Borrar Curso", key=f"dc_{c['id']}"):
                        supabase.table("inscripciones").delete().eq("id", c['id']).execute()
                        st.rerun()
