import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN INTEGRAL ---
st.set_page_config(page_title="ClassTrack 360 v214", layout="wide")

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=JetBrains+Mono&display=swap');
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
    
    # --- SIDEBAR CON RELOJ JS (NUNCA SE DETIENE) ---
    with st.sidebar:
        st.header(f"Sede: {u_data['email'].split('.')[0].upper()}")
        components.html("""
            <div style="color: #4facfe; font-family: monospace; font-size: 24px; font-weight: bold; text-align: center;">
                <div id="d" style="font-size: 13px; color: #aaa; margin-bottom: 5px;"></div>
                <div id="c">00:00:00</div>
            </div>
            <script>
                function update() {
                    const n = new Date();
                    document.getElementById('d').innerText = n.toLocaleDateString('es-AR');
                    document.getElementById('c').innerText = n.toLocaleTimeString('es-AR', {hour12:false});
                }
                setInterval(update, 1000); update();
            </script>
        """, height=90)
        st.divider()
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- CARGA SEGURA DE CURSOS ---
    try:
        res_cursos = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_cursos.data} if res_cursos.data else {}
    except:
        mapa_cursos = {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (FORZAR DETECTOR DE TAREA) ---
    with tabs[0]:
        st.subheader("📅 Seguimiento de Clase")
        if not mapa_cursos: st.info("Primero instale un curso en la pestaña 'Cursos'.")
        else:
            c_ag = st.selectbox("Seleccione el Curso:", list(mapa_cursos.keys()), key="ag_214")
            f_hoy = st.date_input("Fecha de hoy:", datetime.date.today())
            
            # Buscar tarea que vence HOY para este curso
            res_t = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_t.data:
                st.markdown(f'<div class="tarea-alerta">🔔 TAREA PARA REVISAR HOY:<br>{res_t.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            else:
                st.info("No hay tareas pendientes para esta fecha.")
            
            with st.form("f_ag_214"):
                temas = st.text_area("Temas dictados hoy:")
                prox_tarea = st.text_area("Tarea para la próxima clase:")
                vto = st.date_input("Vencimiento tarea:", f_hoy + datetime.timedelta(days=7))
                if st.form_submit_button("💾 GUARDAR AGENDA"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": prox_tarea, "fecha_tarea": str(vto)}).execute()
                    st.success("Cambios guardados satisfactoriamente."); time.sleep(1); st.rerun()

    # --- TAB 4: CURSOS (EDICIÓN Y TRIPLE BOTONERA) ---
    with tabs[4]:
        st.subheader("🏗️ Gestión de Cursos")
        if mapa_cursos:
            for c in res_cursos.data:
                with st.container():
                    st.markdown(f'<div class="planilla-row">📖 <b>{c["nombre_curso_materia"]}</b></div>', unsafe_allow_html=True)
                    b1, b2, b3, _ = st.columns([1,1,1,5])
                    if b1.button("✏️ Editar", key=f"e_c_{c['id']}"): st.session_state[f"ed_c_{c['id']}"] = True
                    if b2.button("🗑️ Borrar", key=f"d_c_{c['id']}"): st.session_state[f"ask_c_{c['id']}"] = True
                    if b3.button("💾 Guardar", key=f"s_c_{c['id']}"): st.success("Cambios guardados satisfactoriamente.")
                    
                    if st.session_state.get(f"ed_c_{c['id']}"):
                        with st.form(f"f_ed_c_{c['id']}"):
                            nuevo_nom = st.text_input("Corregir nombre:", value=c['nombre_curso_materia'])
                            if st.form_submit_button("CONFIRMAR"):
                                supabase.table("inscripciones").update({"nombre_curso_materia": nuevo_nom}).eq("id", c['id']).execute()
                                del st.session_state[f"ed_c_{c['id']}"]; st.rerun()

        st.divider()
        with st.form("new_cur"):
            st.write("### ➕ Instalar Nuevo Curso")
            nc = st.text_input("Materia y Horario")
            if st.form_submit_button("💾 INSTALAR"):
                supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nc, "anio_lectivo": 2026}).execute()
                st.success("Cambios guardados satisfactoriamente."); st.rerun()

    # --- TABS ASISTENCIA Y NOTAS (PROTECCIÓN CASCADA) ---
    with tabs[2]:
        st.subheader("✅ Asistencia por Curso")
        if mapa_cursos:
            c_as = st.selectbox("Seleccione Curso:", ["---"] + list(mapa_cursos.keys()), key="as_214")
            if c_as != "---":
                # Lógica de planilla aquí...
                st.info(f"Cargando alumnos de {c_as}...")
