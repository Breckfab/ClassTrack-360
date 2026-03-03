import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import calendar
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN DE NÚCLEO ---
st.set_page_config(page_title="ClassTrack 360 v265", layout="wide")

SUPABASE_URL = "https://tzevdylabtradqmcqldx.supabase.co"
SUPABASE_KEY = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if 'user' not in st.session_state: st.session_state.user = None
if 'sede_admin' not in st.session_state: st.session_state.sede_admin = None
if 'editando_bitacora' not in st.session_state: st.session_state.editando_bitacora = None
if 'editando_alumno' not in st.session_state: st.session_state.editando_alumno = None
if 'editando_curso' not in st.session_state: st.session_state.editando_curso = None
if 'confirmar_reset' not in st.session_state: st.session_state.confirmar_reset = None
if 'cal_mes' not in st.session_state: st.session_state.cal_mes = datetime.date.today().month
if 'cal_anio' not in st.session_state: st.session_state.cal_anio = datetime.date.today().year

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

    .alumno-block { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px 18px; margin-bottom: 12px; }
    .alumno-block .nombre { font-weight: 600; color: #e8eaf0; font-size: 0.95rem; margin-bottom: 10px; }
    .nota-linea { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.85rem; color: #99a; }
    .nota-linea:last-of-type { border-bottom: none; }
    .nota-badge { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 0.85rem; padding: 2px 8px; border-radius: 5px; }
    .nota-badge.baja { color: #ff4d6d; background: rgba(255,77,109,0.1); border: 1px solid rgba(255,77,109,0.3); }
    .nota-badge.media { color: #ffc107; background: rgba(255,193,7,0.1); border: 1px solid rgba(255,193,7,0.3); }
    .nota-badge.alta { color: #4facfe; background: rgba(79,172,254,0.1); border: 1px solid rgba(79,172,254,0.3); }
    .promedio-linea { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(79,172,254,0.2); font-size: 0.85rem; color: #4facfe; font-weight: 600; }
    .aprobado { color: #4facfe; background: rgba(79,172,254,0.1); border: 1px solid rgba(79,172,254,0.3); padding: 2px 10px; border-radius: 5px; font-size: 0.8rem; font-weight: 700; }
    .desaprobado { color: #ff4d6d; background: rgba(255,77,109,0.1); border: 1px solid rgba(255,77,109,0.3); padding: 2px 10px; border-radius: 5px; font-size: 0.8rem; font-weight: 700; }
    .biblio-box { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 10px 14px; margin-top: 6px; font-size: 0.8rem; color: #778; }

    .cal-box { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.07); border-radius: 10px; padding: 10px; margin-top: 8px; }
    .cal-titulo { text-align: center; font-family: 'Syne', sans-serif; font-weight: 700; font-size: 0.85rem; color: #4facfe; margin-bottom: 8px; }
    .cal-tabla { width: 100%; border-collapse: collapse; font-size: 0.72rem; }
    .cal-tabla th { color: #4facfe; text-align: center; padding: 2px; font-weight: 600; }
    .cal-tabla td { text-align: center; padding: 3px 2px; color: #99a; }
    .cal-tabla td.hoy { background: #4facfe; color: #080b10; border-radius: 50%; font-weight: 800; }
    .cal-tabla td.vacio { color: transparent; }

    .admin-badge { background: rgba(255,77,109,0.15); border: 1px solid rgba(255,77,109,0.4); border-radius: 8px; padding: 8px 14px; color: #ff4d6d; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; display: inline-block; margin-bottom: 16px; }
    .reset-box { background: rgba(255,77,109,0.05); border: 2px solid rgba(255,77,109,0.3); border-radius: 12px; padding: 20px; margin-top: 20px; }
    .reset-titulo { color: #ff4d6d; font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1rem; margin-bottom: 8px; }
    .advertencia-box { background: rgba(255,193,7,0.1); border: 2px solid #ffc107; border-radius: 10px; padding: 16px; margin: 16px 0; color: #ffc107; font-size: 0.9rem; }

    .login-box { background: rgba(255,255,255,0.03); border: 1px solid rgba(79,172,254,0.2); border-radius: 16px; padding: 40px; margin-top: 60px; }
    .login-logo { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.4rem; letter-spacing: 0.05em; color: #e8eaf0; margin-bottom: 6px; }
    .login-logo span { color: #4facfe; }
    .login-eyebrow { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.15em; color: #4facfe; margin-bottom: 16px; }
    .login-title { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1.6rem; margin-bottom: 28px; color: #e8eaf0; }
    .login-footer { font-size: 0.72rem; color: #3a4358; text-align: center; margin-top: 24px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 16px; }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIONES ---
def color_nota(n):
    if n <= 3: return "baja"
    elif n <= 5: return "media"
    else: return "alta"

def estado_aprobacion(promedio, nota_aprobacion):
    if promedio is None or nota_aprobacion is None:
        return ""
    if promedio >= nota_aprobacion:
        return '<span class="aprobado">✅ APROBADO</span>'
    else:
        return '<span class="desaprobado">❌ DESAPROBADO</span>'

def render_calendario(mes, anio):
    MESES_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    hoy = datetime.date.today()
    cal = calendar.monthcalendar(anio, mes)
    filas = ""
    for semana in cal:
        fila = ""
        for dia in semana:
            if dia == 0:
                fila += '<td class="vacio">·</td>'
            elif dia == hoy.day and mes == hoy.month and anio == hoy.year:
                fila += f'<td class="hoy">{dia}</td>'
            else:
                fila += f'<td>{dia}</td>'
        filas += f"<tr>{fila}</tr>"
    return f"""
    <div class="cal-box">
        <div class="cal-titulo">{MESES_ES[mes-1]} {anio}</div>
        <table class="cal-tabla">
            <tr><th>Lu</th><th>Ma</th><th>Mi</th><th>Ju</th><th>Vi</th><th>Sa</th><th>Do</th></tr>
            {filas}
        </table>
    </div>
    """

def reset_completo_sede(sede_nombre):
    try:
        res_u = supabase.table("usuarios").select("id").eq("sede", sede_nombre).execute()
        if not res_u.data: return False, "No se encontró la sede."
        profesor_id = res_u.data[0]['id']
        res_insc = supabase.table("inscripciones").select("id, alumno_id").eq("profesor_id", profesor_id).execute()
        ids_insc = [i['id'] for i in res_insc.data] if res_insc.data else []
        ids_alumnos = list(set([i['alumno_id'] for i in res_insc.data if i.get('alumno_id')] if res_insc.data else []))
        for iid in ids_insc:
            supabase.table("notas").delete().eq("inscripcion_id", iid).execute()
            supabase.table("bitacora").delete().eq("inscripcion_id", iid).execute()
        supabase.table("inscripciones").delete().eq("profesor_id", profesor_id).execute()
        for aid in ids_alumnos:
            supabase.table("alumnos").delete().eq("id", aid).execute()
        return True, f"Sede {sede_nombre.upper()} reseteada correctamente."
    except Exception as e:
        return False, str(e)

# =========================================================
# --- LOGIN ---
# =========================================================
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
        with st.form("login", clear_on_submit=False):
            sede_input = st.text_input("Sede", key="sede_input")
            clave_input = st.text_input("Clave de acceso", type="password", key="clave_input")
            submitted = st.form_submit_button("ENTRAR AL SISTEMA", use_container_width=True)
            if submitted:
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
        st.markdown('<div class="login-footer">© 2026 ClassTrack 360 · v265</div>', unsafe_allow_html=True)

# =========================================================
# --- PANEL ADMIN ---
# =========================================================
elif st.session_state.user.get('sede', '').lower() == 'admin':
    u_data = st.session_state.user

    with st.sidebar:
        st.markdown('<div class="admin-badge">⚡ Modo Administrador</div>', unsafe_allow_html=True)
        st.write(f"📅 {datetime.date.today().strftime('%d/%m/%Y')}")
        st.markdown("---")
        try:
            res_sedes = supabase.table("usuarios").select("sede, nombre").neq("sede", "admin").execute()
            sedes_disponibles = [s['sede'] for s in res_sedes.data] if res_sedes.data else []
        except:
            sedes_disponibles = []
        if sedes_disponibles:
            sede_sel = st.selectbox("Ver sede:", sedes_disponibles, key="admin_sede_sel")
            st.session_state.sede_admin = sede_sel
        else:
            st.warning("No hay sedes registradas.")
        st.markdown("---")
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.session_state.sede_admin = None
            st.rerun()

    st.markdown('<div class="admin-badge">⚡ Panel de Administración</div>', unsafe_allow_html=True)
    st.title("ClassTrack 360 · Admin")

    if st.session_state.sede_admin:
        sede_activa = st.session_state.sede_admin
        admin_tabs = st.tabs(["📊 Resumen", "👥 Alumnos", "📝 Notas", "🗑️ Reset de Datos"])

        with admin_tabs[0]:
            st.subheader(f"Resumen — Sede {sede_activa.upper()}")
            try:
                res_u = supabase.table("usuarios").select("id, nombre").eq("sede", sede_activa).execute()
                if res_u.data:
                    prof_id = res_u.data[0]['id']
                    res_cursos = supabase.table("inscripciones").select("nombre_curso_materia").eq("profesor_id", prof_id).is_("alumno_id", "null").execute()
                    res_alumnos = supabase.table("inscripciones").select("id").eq("profesor_id", prof_id).not_.is_("alumno_id", "null").execute()
                    col1, col2 = st.columns(2)
                    col1.metric("Cursos", len(res_cursos.data) if res_cursos.data else 0)
                    col2.metric("Alumnos", len(res_alumnos.data) if res_alumnos.data else 0)
                    if res_cursos.data:
                        st.markdown("**Cursos activos:**")
                        for c in res_cursos.data:
                            st.markdown(f'<div class="planilla-row">📖 {c["nombre_curso_materia"]}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")

        with admin_tabs[1]:
            st.subheader(f"Alumnos — Sede {sede_activa.upper()}")
            try:
                res_u = supabase.table("usuarios").select("id").eq("sede", sede_activa).execute()
                if res_u.data:
                    prof_id = res_u.data[0]['id']
                    res_cursos = supabase.table("inscripciones").select("nombre_curso_materia").eq("profesor_id", prof_id).is_("alumno_id", "null").execute()
                    if res_cursos.data:
                        for curso in res_cursos.data:
                            nombre_curso = curso['nombre_curso_materia']
                            res_al = supabase.table("inscripciones").select("id, alumnos(nombre, apellido)").eq("nombre_curso_materia", nombre_curso).not_.is_("alumno_id", "null").execute()
                            if res_al.data:
                                st.markdown(f"**📖 {nombre_curso}** ({len(res_al.data)} alumnos)")
                                for r in res_al.data:
                                    al_raw = r.get('alumnos')
                                    al = al_raw[0] if isinstance(al_raw, list) and len(al_raw) > 0 else al_raw
                                    if al:
                                        st.markdown(f'<div class="planilla-row">👤 {al.get("apellido","").upper()}, {al.get("nombre","")}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")

        with admin_tabs[2]:
            st.subheader(f"Notas — Sede {sede_activa.upper()}")
            try:
                res_u = supabase.table("usuarios").select("id").eq("sede", sede_activa).execute()
                if res_u.data:
                    prof_id = res_u.data[0]['id']
                    res_cursos = supabase.table("inscripciones").select("nombre_curso_materia").eq("profesor_id", prof_id).is_("alumno_id", "null").execute()
                    if res_cursos.data:
                        curso_sel = st.selectbox("Curso:", ["---"] + [c['nombre_curso_materia'] for c in res_cursos.data])
                        if curso_sel != "---":
                            res_al = supabase.table("inscripciones").select("id, alumnos(nombre, apellido)").eq("nombre_curso_materia", curso_sel).not_.is_("alumno_id", "null").execute()
                            for r in res_al.data:
                                al_raw = r.get('alumnos')
                                al = al_raw[0] if isinstance(al_raw, list) and len(al_raw) > 0 else al_raw
                                if al:
                                    res_notas = supabase.table("notas").select("calificacion, created_at").eq("inscripcion_id", r['id']).order("created_at", desc=False).execute()
                                    notas = res_notas.data if res_notas.data else []
                                    filas_html = ""
                                    valores = []
                                    for i, nt in enumerate(notas):
                                        val = float(nt['calificacion'])
                                        valores.append(val)
                                        fecha_fmt = datetime.datetime.fromisoformat(nt['created_at'][:10]).strftime('%d/%m/%Y')
                                        clase = color_nota(val)
                                        filas_html += f'<div class="nota-linea"><span>Nota {i+1} · {fecha_fmt}</span><span class="nota-badge {clase}">{val}</span></div>'
                                    if not filas_html:
                                        filas_html = '<div class="nota-linea"><span style="color:#555">Sin notas</span></div>'
                                        promedio_html = ""
                                        estado_html = ""
                                    else:
                                        promedio = round(sum(valores) / len(valores), 2)
                                        clase_prom = color_nota(promedio)
                                        promedio_html = f'<div class="promedio-linea"><span>Promedio</span><span class="nota-badge {clase_prom}">{promedio}</span></div>'
                                        estado_html = ""
                                    st.markdown(f'''
                                        <div class="alumno-block">
                                            <div class="nombre">👤 {al.get("apellido","").upper()}, {al.get("nombre","")}</div>
                                            {filas_html}
                                            {promedio_html}
                                        </div>
                                    ''', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")

        with admin_tabs[3]:
            st.subheader("🗑️ Reset de Datos")
            st.markdown(f"""
                <div class="reset-box">
                    <div class="reset-titulo">⚠️ Zona de Peligro</div>
                    Esta acción borrará TODOS los datos de la sede seleccionada: cursos, alumnos, clases y notas. El usuario de la sede NO será eliminado.
                </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
            sede_reset = st.selectbox("Sede a resetear:", sedes_disponibles, key="reset_sede_sel")
            if st.session_state.confirmar_reset != sede_reset:
                if st.button(f"🔴 BORRAR TODOS LOS DATOS DE {sede_reset.upper()}", type="primary"):
                    st.session_state.confirmar_reset = sede_reset
                    st.rerun()
            else:
                st.markdown(f"""
                    <div class="advertencia-box">
                        ⚠️ <b>ADVERTENCIA FINAL</b><br><br>
                        Estás a punto de borrar TODOS los datos de la sede <b>{sede_reset.upper()}</b>.<br>
                        Esta acción es <b>irreversible</b> y no se podrán recuperar los datos.
                    </div>
                """, unsafe_allow_html=True)
                col_si, col_no = st.columns(2)
                if col_si.button("✅ SÍ, BORRAR TODO", type="primary", use_container_width=True):
                    ok, msg = reset_completo_sede(sede_reset)
                    if ok:
                        st.success(f"✅ {msg}")
                        st.session_state.confirmar_reset = None
                        st.rerun()
                    else:
                        st.error(f"Error: {msg}")
                if col_no.button("❌ NO, CANCELAR", use_container_width=True):
                    st.session_state.confirmar_reset = None
                    st.rerun()

# =========================================================
# --- APP NORMAL ---
# =========================================================
else:
    u_data = st.session_state.user
    f_hoy = datetime.date.today()

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
        col_prev, col_next = st.columns([1, 1])
        if col_prev.button("◀", key="cal_prev"):
            if st.session_state.cal_mes == 1:
                st.session_state.cal_mes = 12
                st.session_state.cal_anio -= 1
            else:
                st.session_state.cal_mes -= 1
            st.rerun()
        if col_next.button("▶", key="cal_next"):
            if st.session_state.cal_mes == 12:
                st.session_state.cal_mes = 1
                st.session_state.cal_anio += 1
            else:
                st.session_state.cal_mes += 1
            st.rerun()
        st.markdown(render_calendario(st.session_state.cal_mes, st.session_state.cal_anio), unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    mapa_cursos = {}
    mapa_cursos_data = {}
    try:
        res_c = supabase.table("inscripciones").select("*").eq("profesor_id", u_data['id']).is_("alumno_id", "null").execute()
        if res_c.data:
            for c in res_c.data:
                if 'nombre_curso_materia' in c:
                    mapa_cursos[c['nombre_curso_materia']] = c['id']
                    mapa_cursos_data[c['nombre_curso_materia']] = c
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
                busqueda = st.text_input("🔍 Buscar alumno por nombre o apellido:", key="busq_alumno")
                c_v = st.selectbox("Filtrar por curso:", ["---"] + list(mapa_cursos.keys()))
                if c_v != "---":
                    try:
                        res_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_v).not_.is_("alumno_id", "null").execute()
                        alumnos_filtrados = []
                        for r in res_al.data:
                            al_raw = r.get('alumnos')
                            al = al_raw[0] if isinstance(al_raw, list) and len(al_raw) > 0 else al_raw
                            if al:
                                if busqueda.strip() == "" or busqueda.lower() in al.get('nombre','').lower() or busqueda.lower() in al.get('apellido','').lower():
                                    alumnos_filtrados.append((r, al))
                        st.info(f"Cantidad de alumnos: {len(alumnos_filtrados)}")
                        for r, al in alumnos_filtrados:
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
            sub_nt = st.radio("Acción:", ["📋 Ver Notas por Curso", "✏️ Cargar Nota"], horizontal=True)

            if sub_nt == "📋 Ver Notas por Curso":
                col_f1, col_f2 = st.columns([2, 1])
                c_ver = col_f1.selectbox("Seleccione Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_ver")
                filtro_estado = col_f2.selectbox("Estado:", ["Todos", "Aprobados", "Desaprobados"], key="filtro_estado")
                busq_nota = st.text_input("🔍 Buscar alumno:", key="busq_nota")

                if c_ver != "---":
                    curso_data = mapa_cursos_data.get(c_ver, {})
                    nota_aprobacion = curso_data.get('nota_aprobacion')
                    try:
                        res_al_v = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_ver).not_.is_("alumno_id", "null").execute()
                        if not res_al_v.data:
                            st.info("No hay alumnos inscriptos en este curso.")
                        else:
                            mostrados = 0
                            for r in res_al_v.data:
                                al_raw = r.get('alumnos')
                                al = al_raw[0] if isinstance(al_raw, list) and len(al_raw) > 0 else al_raw
                                if al:
                                    if busq_nota.strip() and busq_nota.lower() not in al.get('nombre','').lower() and busq_nota.lower() not in al.get('apellido','').lower():
                                        continue
                                    try:
                                        res_notas = supabase.table("notas").select("calificacion, created_at").eq("inscripcion_id", r['id']).order("created_at", desc=False).execute()
                                        notas = res_notas.data if res_notas.data else []
                                    except:
                                        notas = []
                                    filas_html = ""
                                    valores = []
                                    for i, nt in enumerate(notas):
                                        val = float(nt['calificacion'])
                                        valores.append(val)
                                        fecha_fmt = datetime.datetime.fromisoformat(nt['created_at'][:10]).strftime('%d/%m/%Y')
                                        clase = color_nota(val)
                                        filas_html += f'<div class="nota-linea"><span>Nota {i+1} · {fecha_fmt}</span><span class="nota-badge {clase}">{val}</span></div>'

                                    if not valores:
                                        if filtro_estado != "Todos": continue
                                        filas_html = '<div class="nota-linea"><span style="color:#555">Sin notas cargadas</span></div>'
                                        promedio_html = ""
                                        estado_html = ""
                                    else:
                                        promedio = round(sum(valores) / len(valores), 2)
                                        clase_prom = color_nota(promedio)
                                        es_aprobado = nota_aprobacion and promedio >= nota_aprobacion
                                        if filtro_estado == "Aprobados" and not es_aprobado: continue
                                        if filtro_estado == "Desaprobados" and es_aprobado: continue
                                        promedio_html = f'<div class="promedio-linea"><span>Promedio</span><span class="nota-badge {clase_prom}">{promedio}</span></div>'
                                        estado_html = estado_aprobacion(promedio, nota_aprobacion)

                                    mostrados += 1
                                    st.markdown(f'''
                                        <div class="alumno-block">
                                            <div class="nombre">👤 {al.get("apellido","").upper()}, {al.get("nombre","")} {estado_html if valores else ""}</div>
                                            {filas_html}
                                            {promedio_html if valores else ""}
                                        </div>
                                    ''', unsafe_allow_html=True)
                            st.caption(f"Mostrando {mostrados} alumno/s")
                    except Exception as e:
                        st.error(f"Error al cargar alumnos: {e}")

            else:
                c_nt = st.selectbox("Seleccione Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_carga")
                busq_carga = st.text_input("🔍 Buscar alumno:", key="busq_carga")
                if c_nt != "---":
                    try:
                        res_al_n = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido)").eq("nombre_curso_materia", c_nt).not_.is_("alumno_id", "null").execute()
                        if not res_al_n.data:
                            st.info("No hay alumnos inscriptos en este curso.")
                        else:
                            for r in res_al_n.data:
                                al_raw = r.get('alumnos')
                                al = al_raw[0] if isinstance(al_raw, list) and len(al_raw) > 0 else al_raw
                                if al:
                                    if busq_carga.strip() and busq_carga.lower() not in al.get('nombre','').lower() and busq_carga.lower() not in al.get('apellido','').lower():
                                        continue
                                    try:
                                        res_notas = supabase.table("notas").select("calificacion, created_at").eq("inscripcion_id", r['id']).order("created_at", desc=False).execute()
                                        notas_existentes = res_notas.data if res_notas.data else []
                                    except:
                                        notas_existentes = []
                                    st.markdown(f'<div class="planilla-row">👤 {al.get("apellido","").upper()}, {al.get("nombre","")}</div>', unsafe_allow_html=True)
                                    if notas_existentes:
                                        for i, nt in enumerate(notas_existentes):
                                            fecha_fmt = datetime.datetime.fromisoformat(nt['created_at'][:10]).strftime('%d/%m/%Y')
                                            st.markdown(f'<p class="nota-existente">Nota {i+1}: <b>{nt["calificacion"]}</b> · {fecha_fmt}</p>', unsafe_allow_html=True)
                                    with st.form(f"nt_{r['id']}"):
                                        nueva_nota = st.number_input("Nueva calificación:", 0.0, 10.0, value=0.0, step=0.1, key=f"ni_{r['id']}")
                                        if st.form_submit_button("💾 Agregar Nota"):
                                            try:
                                                supabase.table("notas").insert({"inscripcion_id": r['id'], "alumno_id": al['id'], "calificacion": nueva_nota}).execute()
                                                st.success(f"Nota {nueva_nota} agregada para {al.get('apellido','').upper()}, {al.get('nombre','')}.")
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
                mat = st.text_input("Nombre del Curso *")
                hor = st.text_input("Horario (ej: 08:00 - 10:00)")
                dias = st.multiselect("Días:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                nota_ap = st.number_input("Nota de Aprobación * (obligatorio)", min_value=1.0, max_value=10.0, value=4.0, step=0.5)
                biblio = st.text_area("Bibliografía / Fotocopias (opcional)")
                if st.form_submit_button("💾 CREAR CURSO"):
                    if not mat.strip():
                        st.error("El nombre del curso es obligatorio.")
                    elif not dias:
                        st.error("Seleccioná al menos un día.")
                    elif not nota_ap:
                        st.error("La nota de aprobación es obligatoria.")
                    else:
                        info = f"{mat.strip()} ({', '.join(dias)}) | {hor}"
                        try:
                            supabase.table("inscripciones").insert({
                                "profesor_id": u_data['id'],
                                "nombre_curso_materia": info,
                                "anio_lectivo": 2026,
                                "nota_aprobacion": nota_ap,
                                "bibliografia": biblio.strip() if biblio.strip() else None
                            }).execute()
                            st.success(f"Curso '{info}' creado con nota de aprobación {nota_ap}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al crear curso: {e}")
        else:
            if not mapa_cursos:
                st.info("No tenés cursos creados todavía.")
            else:
                busq_curso = st.text_input("🔍 Buscar curso:", key="busq_curso")
                for n_c, i_c in mapa_cursos.items():
                    if busq_curso.strip() and busq_curso.lower() not in n_c.lower():
                        continue
                    curso_data = mapa_cursos_data.get(n_c, {})
                    nota_ap_cur = curso_data.get('nota_aprobacion', '-')
                    biblio_cur = curso_data.get('bibliografia', '')

                    if st.session_state.editando_curso == i_c:
                        partes = n_c.split(" (")
                        mat_actual = partes[0] if partes else n_c
                        with st.form(f"edit_c_{i_c}"):
                            mat_e = st.text_input("Nombre del Curso:", value=mat_actual)
                            hor_e = st.text_input("Horario:")
                            dias_e = st.multiselect("Días:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                            nota_ap_e = st.number_input("Nota de Aprobación *", min_value=1.0, max_value=10.0, value=float(nota_ap_cur) if nota_ap_cur != '-' else 4.0, step=0.5)
                            biblio_e = st.text_area("Bibliografía / Fotocopias (opcional):", value=biblio_cur or "")
                            col_c1, col_c2 = st.columns(2)
                            if col_c1.form_submit_button("💾 Guardar"):
                                nuevo_nombre = f"{mat_e.strip()} ({', '.join(dias_e)}) | {hor_e}" if dias_e else mat_e.strip()
                                try:
                                    supabase.table("inscripciones").update({
                                        "nombre_curso_materia": nuevo_nombre,
                                        "nota_aprobacion": nota_ap_e,
                                        "bibliografia": biblio_e.strip() if biblio_e.strip() else None
                                    }).eq("id", i_c).execute()
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
                        biblio_html = f'<div class="biblio-box">📚 {biblio_cur}</div>' if biblio_cur else ""
                        st.markdown(f'''
                            <div class="planilla-row">
                                📖 {n_c}<br>
                                <small style="color:#4facfe;">Alumnos: {cant} · Nota de aprobación: {nota_ap_cur}</small>
                                {biblio_html}
                            </div>
                        ''', unsafe_allow_html=True)
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
