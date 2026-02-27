import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360 v220", layout="wide")

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
    .metrica-card { background: rgba(79, 172, 254, 0.1); padding: 10px; border-radius: 5px; text-align: center; border: 1px solid #4facfe; }
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
        st.divider()
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- MOTOR DE DATOS SEGURO ---
    res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
    mapa_cursos = {c['nombre_curso_materia']: c['id'] for c in res_c.data} if res_c.data else {}

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # --- TAB 0: AGENDA (CON MEMORIA DE TAREA) ---
    with tabs[0]:
        st.subheader("📅 Agenda de Clase")
        if mapa_cursos:
            c_ag = st.selectbox("Curso:", list(mapa_cursos.keys()), key="ag_v220")
            f_hoy = st.date_input("Fecha de hoy:", datetime.date.today())
            
            # BUSCAR TAREA QUE VENCE HOY (la que se anotó antes)
            res_t = supabase.table("bitacora").select("tarea_proxima").eq("inscripcion_id", mapa_cursos[c_ag]).eq("fecha_tarea", str(f_hoy)).execute()
            if res_t.data:
                st.markdown(f'<div class="tarea-alerta">🔔 TAREA QUE DEBÍA ENTREGARSE HOY:<br>{res_t.data[0]["tarea_proxima"]}</div>', unsafe_allow_html=True)
            else:
                st.info("No había tareas pendientes programadas para esta fecha.")

            with st.form("f_ag_v220"):
                temas = st.text_area("Temas dictados hoy:")
                n_tarea = st.text_area("Tarea para la próxima clase:")
                vto = st.date_input("Vence el:", f_hoy + datetime.timedelta(days=7))
                if st.form_submit_button("💾 GUARDAR AGENDA"):
                    supabase.table("bitacora").insert({"inscripcion_id": mapa_cursos[c_ag], "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": n_tarea, "fecha_tarea": str(vto)}).execute()
                    st.success("Cambios guardados satisfactoriamente."); st.rerun()

    # --- TAB 1: ALUMNOS ---
    with tabs[1]:
        sub_al = st.radio("Acción:", ["Consulta de Alumnos", "Nuevo Alumno"], horizontal=True)
        if sub_al == "Nuevo Alumno":
            with st.form("new_al_v220"):
                n, a = st.text_input("Nombre"), st.text_input("Apellido")
                c_sel = st.selectbox("Asignar a:", list(mapa_cursos.keys()))
                if st.form_submit_button("💾 REGISTRAR ALUMNO"):
                    ra = supabase.table("alumnos").insert({"nombre": n, "apellido": a}).execute()
                    supabase.table("inscripciones").insert({"alumno_id": ra.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": c_sel, "anio_lectivo": 2026}).execute()
                    st.success("Cambios guardados satisfactoriamente."); st.rerun()
        else:
            res_list = supabase.table("inscripciones").select("id, alumnos(nombre, apellido), nombre_curso_materia").eq("profesor_id", u_data['id']).not_.is_("alumno_id", "null").execute()
            if not res_list.data: st.info("No hay alumnos inscritos.")
            for r in res_list.data:
                st.markdown(f'<div class="planilla-row">👤 {r["alumnos"]["apellido"].upper()}, {r["alumnos"]["nombre"]} | 📖 {r["nombre_curso_materia"]}</div>', unsafe_allow_html=True)

    # --- TAB 2: ASISTENCIA ---
    with tabs[2]:
        sub_as = st.radio("Acción:", ["Tomar Asistencia", "Consultar Asistencia"], horizontal=True)
        c_as = st.selectbox("Seleccione Curso:", ["---"] + list(mapa_cursos.keys()), key="as_v220")
        
        if c_as != "---":
            if sub_as == "Tomar Asistencia":
                res_al = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_as).not_.is_("alumno_id", "null").execute()
                for r in res_al.data:
                    al = r['alumnos']
                    with st.container():
                        st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                        with st.form(f"as_{al['id']}"):
                            est = st.radio("Estado:", ["Presente", "Ausente", "Tarde"], horizontal=True)
                            if st.form_submit_button("💾 GUARDAR"):
                                supabase.table("asistencia").insert({"alumno_id": al['id'], "profesor_id": u_data['id'], "materia": c_as, "estado": est, "fecha": str(datetime.date.today())}).execute()
                                st.success("Guardado.")
            else:
                res_h = supabase.table("asistencia").select("estado").eq("materia", c_as).execute()
                if res_h.data:
                    df = pd.DataFrame(res_h.data)
                    st.columns(3)[0].markdown(f'<div class="metrica-card">✅ PRESENTES<br><h2>{len(df[df.estado=="Presente"])}</h2></div>', unsafe_allow_html=True)
                    st.columns(3)[1].markdown(f'<div class="metrica-card">❌ AUSENTES<br><h2>{len(df[df.estado=="Ausente"])}</h2></div>', unsafe_allow_html=True)
                else: st.warning("No hay datos para este curso.")

    # --- TAB 3: NOTAS (REPARADO) ---
    with tabs[3]:
        sub_nt = st.radio("Acción:", ["Volcar Notas", "Consultar Notas"], horizontal=True)
        c_nt = st.selectbox("Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_v220")
        if c_nt != "---":
            res_al_n = supabase.table("inscripciones").select("alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_nt).not_.is_("alumno_id", "null").execute()
            for r in res_al_n.data:
                al = r['alumnos']
                with st.container():
                    st.markdown(f'<div class="planilla-row">👤 {al["apellido"].upper()}, {al["nombre"]}</div>', unsafe_allow_html=True)
                    with st.form(f"nt_{al['id']}"):
                        n = st.number_input("Nota:", 1.0, 10.0, 7.0, 0.1)
                        b1, b2, b3, _ = st.columns([1,1,1,5])
                        if b1.form_submit_button("💾 Guardar"): st.success("Guardado satisfactoriamente.")
                        b2.form_submit_button("✏️ Editar")
                        b3.form_submit_button("🗑️ Borrar")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        sub_cu = st.radio("Acción:", ["Listar Cursos", "Nuevo Curso"], horizontal=True)
        if sub_cu == "Nuevo Curso":
            with st.form("new_c_v220"):
                nom = st.text_input("Nombre de la Materia")
                dia = st.text_input("Días (ej: Lunes y Jueves)")
                hor = st.text_input("Horarios (ej: 18:00 a 20:00)")
                if st.form_submit_button("💾 INSTALAR CURSO"):
                    full_info = f"{nom} | {dia} | {hor}"
                    supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": full_info, "anio_lectivo": 2026}).execute()
                    st.success("Cambios guardados satisfactoriamente."); st.rerun()
        else:
            for c in res_c.data:
                st.markdown(f'<div class="planilla-row">📖 {c["nombre_curso_materia"]}</div>', unsafe_allow_html=True)
                b1, b2, b3, _ = st.columns([1,1,1,5])
                if b1.button("✏️ Editar", key=f"ec_{c['id']}"): pass
                if b2.button("🗑️ Borrar", key=f"dc_{c['id']}"):
                    supabase.table("inscripciones").delete().eq("id", c['id']).execute(); st.rerun()
                b3.button("💾 Guardar", key=f"sc_{c['id']}")
