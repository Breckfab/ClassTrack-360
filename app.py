import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v196", layout="wide")

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
    .logo-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(to right, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
    .promedio-badge { background: #4facfe; color: #0b0e14; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: 'JetBrains Mono'; }
    .tarea-alerta { background: rgba(255, 193, 7, 0.1); border: 1px solid #ffc107; padding: 15px; border-radius: 8px; margin-bottom: 15px; color: #ffc107; text-align: center; }
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
    """, height=60)

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
    
    # --- CARGA GLOBAL DE CURSOS ---
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA CON MEMORIA DE TAREAS ---
    with tabs[0]:
        st.subheader("📅 Seguimiento de Clase")
        if not mapa_cursos: st.warning("Cree un curso primero.")
        else:
            c_sel_ag = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_c_sel")
            f_hoy = st.date_input("Fecha de hoy:", datetime.date.today())
            
            # Buscar si había tarea programada para HOY
            res_tarea_hoy = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_sel_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_tarea_hoy.data:
                st.markdown(f'<div class="tarea-alerta">🔔 <b>TAREA PARA HOY:</b> {res_tarea_hoy.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="tarea-alerta">✅ No hay tareas pendientes para hoy.</div>', unsafe_allow_html=True)
            
            # Formulario de Bitácora
            res_ag_hoy = supabase.table("bitacora").select("*").eq("inscripcion_id", mapa_cursos[c_sel_ag]).eq("fecha", str(f_hoy)).execute()
            with st.form("f_agenda_v196"):
                tema = st.text_area("Temas dictados hoy:", value=res_ag_hoy.data[0]['contenido_clase'] if res_ag_hoy.data else "")
                tarea_nueva = st.text_area("Tarea para la próxima clase:", value=res_ag_hoy.data[0]['tarea_proxima'] if res_ag_hoy.data else "")
                f_vto = st.date_input("Fecha de entrega de esta tarea:", datetime.date.today() + datetime.timedelta(days=7))
                if st.form_submit_button("💾 CERRAR AGENDA"):
                    payload = {"inscripcion_id": mapa_cursos[c_sel_ag], "fecha": str(f_hoy), "contenido_clase": tema, "tarea_proxima": tarea_nueva, "fecha_tarea": str(f_vto)}
                    if res_ag_hoy.data: supabase.table("bitacora").update(payload).eq("id", res_ag_hoy.data[0]['id']).execute()
                    else: supabase.table("bitacora").insert(payload).execute()
                    st.success("Guardado."); st.rerun()

    # --- TAB 3: NOTAS CON PROMEDIO AUTOMÁTICO ---
    with tabs[3]:
        st.subheader("📝 Planilla de Calificaciones")
        if not mapa_cursos: st.warning("Cree un curso primero.")
        else:
            c_sel_nt = st.selectbox("Elegir Curso:", list(mapa_cursos.keys()), key="nt_c_sel")
            res_al_nt = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_sel_nt).not_.is_("alumno_id", "null").execute()
            
            for item in res_al_nt.data:
                al = item['alumnos']
                # Buscar notas existentes para promedio
                res_notas_hist = supabase.table("notas").select("calificacion").eq("alumno_id", al['id']).eq("materia", c_sel_nt).execute()
                lista_notas = [float(n['calificacion']) for n in res_notas_hist.data]
                promedio = sum(lista_notas) / len(lista_notas) if lista_notas else 0
                
                with st.container():
                    st.markdown(f"""
                        <div class="planilla-row">
                            👤 <b>{al['apellido'].upper()}, {al['nombre']}</b> 
                            <span style="float:right;">Promedio: <span class="promedio-badge">{promedio:.2f}</span></span>
                        </div>
                    """, unsafe_allow_html=True)
                    with st.form(f"f_nota_{al['id']}"):
                        n_nueva = st.number_input("Nueva Nota:", 1.0, 10.0, step=0.5)
                        if st.form_submit_button("💾 GRABAR NOTA"):
                            supabase.table("notas").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": c_sel_nt, "calificacion": n_nueva, "fecha": str(datetime.date.today())}).execute()
                            st.rerun()

    # --- TAB 4: CURSOS (RECUPERADO) ---
    with tabs[4]:
        st.subheader("🏗️ Mis Cursos")
        # Listado de cursos arriba
        if res_c.data:
            for c in res_c.data:
                with st.container():
                    st.markdown(f'<div class="planilla-row">📖 <b>{c["nombre_curso_materia"]}</b></div>', unsafe_allow_html=True)
                    col1, col2, col3, _ = st.columns([1,1,1,5])
                    col1.button("✏️ Editar", key=f"ed_cur_{c['id']}")
                    if col2.button("🗑️ Borrar", key=f"del_cur_{c['id']}"):
                        supabase.table("inscripciones").delete().eq("id", c['id']).execute()
                        st.rerun()
                    col3.button("💾 Guardar", key=f"sav_cur_{c['id']}")
        
        st.divider()
        with st.form("f_new_cur"):
            st.write("### ➕ Crear Nuevo Curso")
            nuevo_nombre = st.text_input("Nombre de Materia y Horario")
            if st.form_submit_button("💾 INSTALAR CURSO"):
                if nuevo_nombre:
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": nuevo_nombre, "anio_lectivo": 2026}).execute()
                    st.success("Curso creado."); time.sleep(0.5); st.rerun()
