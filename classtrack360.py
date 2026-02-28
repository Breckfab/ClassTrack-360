import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN DE NÚCLEO ---
st.set_page_config(page_title="ClassTrack 360 v260", layout="wide")

SUPABASE_URL = "https://tzevdylabtradqmcqldx.supabase.co"
SUPABASE_KEY = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if 'user' not in st.session_state: st.session_state.user = None
if 'editando_bitacora' not in st.session_state: st.session_state.editando_bitacora = None
if 'editando_alumno' not in st.session_state: st.session_state.editando_alumno = None
if 'editando_curso' not in st.session_state: st.session_state.editando_curso = None

# --- 2. ESTILO VISUAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@300;400&display=swap');

    .stApp { background: #080b10; color: #e8eaf0; font-family: 'DM Mono', monospace; }

    .stApp::before {
        content: '';
        position: fixed; inset: 0; z-index: 0; pointer-events: none;
        background-image:
            linear-gradient(rgba(79,172,254,0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(79,172,254,0.04) 1px, transparent 1px);
        background-size: 48px 48px;
    }

    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
    .tarea-alerta { background: rgba(255,193,7,0.25); border: 2px solid #ffc107; padding: 20px; border-radius: 12px; color: #ffc107; text-align: center; font-weight: 800; margin-bottom: 25px; font-size: 1.2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    .stat-card { background: rgba(79,172,254,0.1); border: 1px solid #4facfe; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px; }
    .nota-existente { color: #4facfe; font-size: 0.85rem; margin-top: 4px; }

    .login-box {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(79,172,254,0.2);
        border-radius: 16px;
        padding: 40px;
        margin-top: 60px;
    }
    .login-logo {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 1.4rem;
        letter-spacing: 0.05em;
        color: #e8eaf0;
        margin-bottom: 6px;
    }
    .login-logo span { color: #4facfe; }
    .login-eyebrow {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: #4facfe;
        margin-bottom: 16px;
    }
    .login-title {
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 1.6rem;
        margin-bottom: 28px;
        color: #e8eaf0;
    }
    .login-footer {
        font-size: 0.72rem;
        color: #3a4358;
        text-align: center;
        margin-top: 24px;
        border-top: 1px solid rgba(255,255,255,0.05);
        padding-top: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE ACCESO ---
if st.session_state.user is None:
    _, col, _ = st.columns([1.5, 1, 1.5])
    with col:
        st.markdown("""
            <div class="login-box">
                <div class="login-logo">Class<span>Track</span> 360</div>
                <div class="login-eyebrow">// Acceso al sistema</div>
                <div class="login-title">Iniciar sesión</div>
            </div>
        """, unsafe_allow_html=True)
        sede_input = st.text_input("Sede", placeholder="cambridge", key="sede_input")
        clave_input = st.text_input("Clave de acceso", type="password", key="clave_input")
        if st.button("ENTRAR AL SISTEMA", use_container_width=True):
            sede = sede_input.strip().lower()
            clave = clave_input.strip()
            try:
                res = supabase.table("usuarios").select("*").eq("sede", sede).eq("password_text", clave).execute()
                if res.data:
                    st.session_state.user = res.data[0]
                    st.rerun()
                else:
                    st.error("Sede o clave incorrectos.")
            except Exception as e:
                st.error(f"Error de conexión: {e}")
        st.markdown('<div class="login-footer">© 2026 ClassTrack 360 · v260</div>', unsafe_allow_html=True)

else:
    u_data = st.session_state.user
    f_hoy = datetime.date.today()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header(f"Sede: {u_data['sede'].upper()}")
        st.write(f"📅 {f_hoy.strftime('%d/%m/%Y')}")
        components.html("""<div style="color:#4facfe;font-family:monospace;font-size:24px;text-align:center;"><div id="c">00:00:00</div></div><script>setInterval(()=>{document.getElementById('c').innerText=new Date().toLocaleTimeString('es-AR',{hour12:false})},1000);</script>""", height=50)
        try:
            res_total = supabase.table("inscripciones").select("id").eq("profesor_id", u_data['id']).eq("anio_lectivo", 2026).not_.is_("alumno_id", "null").execute()
            st.markdown(f'<div class="stat-card">Total Alumnos 2026: <b>{len(res_total.data)}</b></div>', unsafe_allow_html=True)
        except:
            st.markdown('<div class="stat-card">Total Alumnos 2026: <b>-</b></div>', unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    # --- MOTOR DE DATOS ---
    mapa_cursos = {}
    try:
        res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if res_c.data:
            for c in res_c.data:
                if 'nombre_curso_materia' in c:
                    mapa_cursos[c['nombre_curso_materia']] = c['id']
    except Exception as e:
        st.error(f"Error al cargar cursos: {e}")

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "📝 Notas", "🏗️ Cursos"])

    # =========================================================
    # --- TAB 0: AGENDA ---
    # =========================================================
    with tabs[0]:
        if not mapa_cursos:
            st.warning("No tenés cursos creados. Andá a la pestaña 🏗️ Cursos para crear uno.")
        else:
            c_ag = st.selectbox("Seleccione Curso para iniciar clase:", list(mapa_cursos.keys()), key="ag_sel")
            inscripcion_id = mapa_cursos[c_ag]
            try:
                res_t = supabase.table("bitacora").select("tarea_proxima, fecha").eq("inscripcion_id", inscripcion_id).lt("fecha", str(f_hoy)).order("fecha", desc=True).limit(1).execute()
                if res_t.data and res_t.data[0].get('tarea_proxima'):
                    st.markdown(f'''<div class="tarea-alerta">🔔 TAREA PENDIENTE DE LA CLASE ANTERIOR ({res_t.data[0]['fecha']})<br><div style="margin-top:10px;border-top:1px solid #ffc107;padding-top:10px;color:#fff;font-weight:400;font-size:1.1rem;">{res_t.data[0]["tarea_proxima"]}</div></div>''', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error al buscar tarea pendiente: {e}")

            st.subheader("📋 Historial de Clases")
            try:
                res_hist = supabase.table("bitacora").select("*").eq("inscripcion_id", inscripcion_id).order("fecha", desc=True).limit(10).execute()
            except:
                res_hist = type('obj', (object,), {'data': []})()

            if res_hist.data:
                for reg in res_hist.data:
                    with st.expander(f"📅 Clase del {reg['fecha']}"):
                        if st.session_state.editando_bitacora == reg['id']:
                            with st.form(f"edit_bit_{reg['id']}"):
                                t_edit = st.text_area("Contenido dictado:", value=reg.get('contenido_clase', ''))
                                ta_edit = st.text_area("Tarea para próxima clase:", value=reg.get('tarea_proxima', ''))
                                vto_val = datetime.date.fromisoformat(reg['fecha_tarea']) if reg.get('fecha_tarea') else f_hoy
                                vto_edit = st.date_input("Vencimiento:", vto_val)
                                col_e1, col_e2 = st.columns(2)
                                if col_e1.form_submit_button("💾 Guardar Cambios"):
                                    try:
                                        supabase.table("bitacora").update({"contenido_clase": t_edit, "tarea_proxima": ta_edit, "fecha_tarea": str(vto_edit)}).eq("id", reg['id']).execute()
                                        st.session_state.editando_bitacora = None
                                        st.success("Registro actualizado.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error al actualizar: {e}")
                                if col_e2.form_submit_button("❌ Cancelar"):
                                    st.session_state.editando_bitacora = None
                                    st.rerun()
                        else:
                            st.write(f"**Contenido:** {reg.get('contenido_clase', '-')}")
                            st.write(f"**Tarea:** {reg.get('tarea_proxima', '-')}")
                            st.write(f"**Vencimiento:** {reg.get('fecha_tarea', '-')}")
                            col_b1, col_b2 = st.columns([1, 5])
                            if col_b1.button("✏️ Editar", key=f"edit_b_{reg['id']}"):
                                st.session_state.editando_bitacora = reg['id']
                                st.rerun()
                            if col_b2.button("🗑️ Borrar", key=f"del_b_{reg['id']}"):
                                try:
                                    supabase.table("bitacora").delete().eq("id", reg['id']).execute()
                                    st.success("Registro eliminado.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al borrar: {e}")
            else:
                st.info("No hay clases registradas para este curso aún.")

            st.subheader("📝 Registrar Clase de Hoy")
            try:
                res_hoy = supabase.table("bitacora").select("id").eq("inscripcion_id", inscripcion_id).eq("fecha", str(f_hoy)).execute()
                ya_guardado_hoy = len(res_hoy.data) > 0
            except:
                ya_guardado_hoy = False

            if ya_guardado_hoy:
                st.warning("⚠️ Ya existe un registro para HOY en este curso. Podés editarlo desde el historial de arriba.")
            else:
                with st.form("f_agenda"):
                    temas = st.text_area("Contenido dictado hoy")
                    n_tarea = st.text_area("Tarea para la próxima clase")
                    vto = st.date_input("Vencimiento de esta tarea:", f_hoy + datetime.timedelta(days=7))
                    if st.form_submit_button("💾 Guardar Clase"):
                        if not temas.strip():
                            st.error("El contenido de la clase no puede estar vacío.")
                        else:
                            try:
                                supabase.table("bitacora").insert({"inscripcion_id": inscripcion_id, "fecha": str(f_hoy), "contenido_clase": temas, "tarea_proxima": n_tarea, "fecha_tarea": str(vto)}).execute()
                                st.success("Clase guardada satisfactoriamente.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al guardar: {e}")

    # =========================================================
    # --- TAB 1: ALUMNOS ---
    # =========================================================
    with tabs[1]:
        sub_al = st.radio("Acción:", ["Ver Lista", "Registrar Alumno Nuevo"], horizontal=True)
        if sub_al == "Registrar Alumno Nuevo":
            if not mapa_cursos:
                st.warning("Primero creá un curso en la pestaña 🏗️ Cursos.")
            else:
                with st.form("new_al"):
                    n = st.text_input("Nombre")
                    a = st.text_input("Apellido")
                    c_sel = st.selectbox("Asignar a:", list(mapa_cursos.keys()))
                    if st.form_submit_button("💾 REGISTRAR"):
                        if not n.strip() or not a.strip():
                            st.error("Nombre y Apellido son obligatorios.")
                        else:
                            try:
                                ra = supabase.table("alumnos").insert({"nombre": n.strip(), "apellido": a.strip()}).execute()
                                if ra.data:
                                    supabase.table("inscripciones").insert({"alumno_id": ra.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": c_sel, "anio_lectivo": 2026}).execute()
                                    st.success(f"Alumno {a.upper()}, {n} registrado en {c_sel}.")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error al registrar alumno: {e}")
        else:
            if not mapa_cursos:
                st.warning("No hay cursos creados.")
            else:
                c_v = st.selectbox("Filtrar por curso:", ["---"] + list(mapa_cursos.keys()))
                if c_v != "---":
                    try:
                        res_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_v).not_.is_("alumno_id", "null").execute()
                        st.info(f"Cantidad de alumnos: {len(res_al.data)}")
                        for r in res_al.data:
                            al_raw = r.get('alumnos')
                            al = al_raw[0] if isinstance(al_raw, list) and len(al_raw) > 0 else al_raw
                            if al:
                                if st.session_state.editando_alumno == r['id']:
                                    with st.form(f"edit_al_{r['id']}"):
                                        n_edit = st.text_input("Nombre:", value=al.get('nombre', ''))
                                        a_edit = st.text_input("Apellido:", value=al.get('apellido', ''))
                                        col_a1, col_a2 = st.columns(2)
                                        if col_a1.form_submit_button("💾 Guardar"):
                                            try:
                                                supabase.table("alumnos").update({"nombre": n_edit.strip(), "apellido": a_edit.strip()}).eq("id", al['id']).execute()
                                                st.session_state.editando_alumno = None
                                                st.success("Alumno actualizado.")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error: {e}")
                                        if col_a2.form_submit_button("❌ Cancelar"):
                                            st.session_state.editando_alumno = None
                                            st.rerun()
                                else:
                                    st.markdown(f'<div class="planilla-row">👤 {al.get("apellido", "").upper()}, {al.get("nombre", "")}</div>', unsafe_allow_html=True)
                                    ab1, ab2 = st.columns([1, 1])
                                    if ab1.button("✏️ Editar", key=f"eal_{r['id']}"):
                                        st.session_state.editando_alumno = r['id']
                                        st.rerun()
                                    if ab2.button("🗑️ Borrar", key=f"dal_{r['id']}"):
                                        try:
                                            supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                                            st.success("Alumno eliminado del curso.")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error al borrar: {e}")
                    except Exception as e:
                        st.error(f"Error al cargar alumnos: {e}")

    # =========================================================
    # --- TAB 2: NOTAS ---
    # =========================================================
    with tabs[2]:
        st.subheader("📝 Notas y Calificaciones")
        if not mapa_cursos:
            st.warning("No hay cursos creados.")
        else:
            c_nt = st.selectbox("Seleccione Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_sel")
            if c_nt != "---":
                try:
                    res_al_n = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_nt).not_.is_("alumno_id", "null").execute()
                    if not res_al_n.data:
                        st.info("No hay alumnos inscriptos en este curso.")
                    else:
                        st.info(f"Alumnos en el curso: {len(res_al_n.data)}")
                        for r in res_al_n.data:
                            al_raw = r.get('alumnos')
                            al = al_raw[0] if isinstance(al_raw, list) and len(al_raw) > 0 else al_raw
                            if al:
                                nota_existente = None
                                try:
                                    res_nota = supabase.table("notas").select("id, calificacion").eq("inscripcion_id", r['id']).order("created_at", desc=True).limit(1).execute()
                                    if res_nota.data:
                                        nota_existente = res_nota.data[0]
                                except:
                                    pass
                                st.markdown(f'<div class="planilla-row">👤 {al.get("apellido", "").upper()}, {al.get("nombre", "")}</div>', unsafe_allow_html=True)
                                if nota_existente:
                                    st.markdown(f'<p class="nota-existente">📌 Nota actual: <b>{nota_existente["calificacion"]}</b></p>', unsafe_allow_html=True)
                                with st.form(f"nt_{r['id']}"):
                                    val_default = float(nota_existente['calificacion']) if nota_existente else 0.0
                                    nueva_nota = st.number_input("Calificación:", 0.0, 10.0, value=val_default, step=0.1, key=f"ni_{r['id']}")
                                    if st.form_submit_button("💾 Guardar Nota"):
                                        try:
                                            if nota_existente:
                                                supabase.table("notas").update({"calificacion": nueva_nota}).eq("id", nota_existente['id']).execute()
                                            else:
                                                supabase.table("notas").insert({"inscripcion_id": r['id'], "alumno_id": al['id'], "calificacion": nueva_nota}).execute()
                                            st.success(f"Nota {nueva_nota} guardada para {al.get('apellido', '').upper()}, {al.get('nombre', '')}.")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error al guardar nota: {e}")
                except Exception as e:
                    st.error(f"Error al cargar alumnos: {e}")

    # =========================================================
    # --- TAB 3: CURSOS ---
    # =========================================================
    with tabs[3]:
        sub_cu = st.radio("Acción:", ["Mis Cursos", "Crear Nuevo Curso"], horizontal=True)
        if sub_cu == "Crear Nuevo Curso":
            with st.form("new_c"):
                mat = st.text_input("Materia")
                hor = st.text_input("Horario (ej: 08:00 - 10:00)")
                dias = st.multiselect("Días:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                if st.form_submit_button("💾 CREAR CURSO"):
                    if not mat.strip():
                        st.error("El nombre de la materia es obligatorio.")
                    elif not dias:
                        st.error("Seleccioná al menos un día.")
                    else:
                        info = f"{mat.strip()} ({', '.join(dias)}) | {hor}"
                        try:
                            supabase.table("inscripciones").insert({"profesor_id": u_data['id'], "nombre_curso_materia": info, "anio_lectivo": 2026}).execute()
                            st.success(f"Curso '{info}' creado correctamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al crear curso: {e}")
        else:
            if not mapa_cursos:
                st.info("No tenés cursos creados todavía.")
            else:
                for n_c, i_c in mapa_cursos.items():
                    if st.session_state.editando_curso == i_c:
                        partes = n_c.split(" (")
                        mat_actual = partes[0] if partes else n_c
                        with st.form(f"edit_c_{i_c}"):
                            mat_e = st.text_input("Materia:", value=mat_actual)
                            hor_e = st.text_input("Horario:")
                            dias_e = st.multiselect("Días:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                            col_c1, col_c2 = st.columns(2)
                            if col_c1.form_submit_button("💾 Guardar"):
                                nuevo_nombre = f"{mat_e.strip()} ({', '.join(dias_e)}) | {hor_e}" if dias_e else mat_e.strip()
                                try:
                                    supabase.table("inscripciones").update({"nombre_curso_materia": nuevo_nombre}).eq("id", i_c).execute()
                                    supabase.table("inscripciones").update({"nombre_curso_materia": nuevo_nombre}).eq("nombre_curso_materia", n_c).execute()
                                    st.session_state.editando_curso = None
                                    st.success("Curso actualizado.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                            if col_c2.form_submit_button("❌ Cancelar"):
                                st.session_state.editando_curso = None
                                st.rerun()
                    else:
                        try:
                            res_count = supabase.table("inscripciones").select("id", count="exact").eq("nombre_curso_materia", n_c).not_.is_("alumno_id", "null").execute()
                            cant = res_count.count if res_count.count else 0
                        except:
                            cant = 0
                        st.markdown(f'<div class="planilla-row">📖 {n_c}<br><small style="color:#4facfe;">Alumnos: {cant}</small></div>', unsafe_allow_html=True)
                        cb1, cb2 = st.columns([1, 1])
                        if cb1.button("✏️ Editar", key=f"ec_{i_c}"):
                            st.session_state.editando_curso = i_c
                            st.rerun()
                        if cb2.button("🗑️ Borrar", key=f"dc_{i_c}"):
                            try:
                                supabase.table("inscripciones").delete().eq("id", i_c).execute()
                                st.success("Curso eliminado.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al borrar: {e}")
