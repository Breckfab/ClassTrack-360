import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; text-align: center; margin-bottom: 20px; }
    .print-table { background-color: white; color: black; border-radius: 5px; padding: 10px; }
    @media print {
        .no-print { display: none !important; }
        .stApp { background-color: white !important; color: black !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN DISCRETO ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        with st.form("login_form"):
            u_input = st.text_input("Sede").strip().lower()
            p = st.text_input("Clave", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                email_real = ""
                if u_input == "cambridge": email_real = "cambridge.fabianbelledi@gmail.com"
                elif u_input == "daguerre": email_real = "daguerre.fabianbelledi@gmail.com"
                if email_real:
                    try:
                        res = supabase.table("usuarios").select("*").eq("email", email_real).eq("password_text", p).execute()
                        if res.data:
                            st.session_state.user = res.data[0]
                            st.rerun()
                        else: st.error("Clave incorrecta.")
                    except: st.error("Error de conexión.")
                else: st.error("Sede no válida.")
else:
    user = st.session_state.user
    st.sidebar.write(f"Sede activa")
    if st.sidebar.button("SALIR"):
        st.session_state.user = None
        st.rerun()

    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "✅ Asistencia", "📝 Notas", "🏗️ Cursos"])

    # Carga de materias segura
    df_cursos = pd.DataFrame()
    try:
        res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario, anio_lectivo").eq("profesor_id", user['id']).is_("alumno_id", "null").execute()
        if res_c.data: df_cursos = pd.DataFrame(res_c.data)
    except: pass

    # --- TAB 1: ALUMNOS (FILTROS E IMPRESIÓN) ---
    with tabs[1]:
        st.subheader("Búsqueda y Gestión de Alumnos")
        
        if not df_cursos.empty:
            # Filtros superiores
            col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
            busqueda = col_f1.text_input("🔍 Buscar por Nombre o Apellido", placeholder="Ej: Perez")
            anio_sel = col_f2.selectbox("Año Lectivo", sorted(df_cursos['anio_lectivo'].unique(), reverse=True))
            curso_filtro = col_f3.selectbox("Filtrar por Curso", ["Todos"] + list(df_cursos['nombre_curso_materia'].unique()))

            # Consulta de alumnos con filtros aplicados
            try:
                query = supabase.table("inscripciones").select("alumnos(id, nombre, apellido), nombre_curso_materia, anio_lectivo").eq("profesor_id", user['id']).not_.is_("alumno_id", "null")
                if anio_sel: query = query.eq("anio_lectivo", anio_sel)
                if curso_filtro != "Todos": query = query.eq("nombre_curso_materia", curso_filtro)
                
                res_p = query.execute()
                
                if res_p.data:
                    # Formatear datos para tabla
                    lista_alu = []
                    for r in res_p.data:
                        if r['alumnos']:
                            alu_full = f"{r['alumnos']['apellido']}, {r['alumnos']['nombre']}"
                            if busqueda.lower() in alu_full.lower():
                                lista_alu.append({
                                    "Alumno": alu_full,
                                    "Curso": r['nombre_curso_materia'],
                                    "Año": r['anio_lectivo']
                                })
                    
                    df_final = pd.DataFrame(lista_alu)
                    
                    if not df_final.empty:
                        st.dataframe(df_final, use_container_width=True)
                        
                        # Botón de Impresión
                        if st.button("🖨️ Generar Versión para Imprimir"):
                            st.write("### Planilla de Alumnos - " + ("Cambridge" if "cambridge" in user['email'] else "Daguerre"))
                            st.table(df_final)
                            st.info("💡 Consejo: Usa Ctrl+P (Windows) o Cmd+P (Mac) para imprimir o guardar como PDF.")
                    else:
                        st.info("No se encontraron alumnos con ese nombre.")
                else:
                    st.info("No hay alumnos registrados con esos filtros.")
            except:
                st.error("Error al cargar la lista de alumnos.")

            st.divider()
            with st.expander("➕ Inscribir Nuevo Alumno"):
                with st.form("ins_alu_form", clear_on_submit=True):
                    c_ins = st.selectbox("Materia:", [f"{c['nombre_curso_materia']} | {c['horario']}" for _, c in df_cursos.iterrows()])
                    n_a = st.text_input("Nombre")
                    a_a = st.text_input("Apellido")
                    if st.form_submit_button("Confirmar Inscripción"):
                        if n_a and a_a:
                            nuevo = supabase.table("alumnos").insert({"nombre": n_a, "apellido": a_a}).execute()
                            c_nom, c_hor = c_ins.split(" | ")
                            supabase.table("inscripciones").insert({
                                "alumno_id": nuevo.data[0]['id'], "profesor_id": user['id'], 
                                "nombre_curso_materia": c_nom, "horario": c_hor, "anio_lectivo": 2026
                            }).execute()
                            st.success("Registrado.")
                            st.rerun()
        else:
            st.info("Primero cargá un curso en la pestaña 'Cursos'.")

    # --- TAB 4: CURSOS ---
    with tabs[4]:
        st.subheader("Tus Materias")
        if not df_cursos.empty:
            for _, cur in df_cursos.iterrows():
                col_n, col_b = st.columns([4, 1])
                col_n.write(f"📘 **{cur['nombre_curso_materia']}** | {cur['horario']} (Año: {cur['anio_lectivo']})")
                if col_b.button("Borrar", key=f"del_{cur['id']}"):
                    supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                    st.rerun()
        
        with st.form("nuevo_curso"):
            st.write("➕ Añadir Materia")
            nc = st.text_input("Nombre")
            hc = st.text_input("Horario")
            if st.form_submit_button("Crear"):
                if nc and hc:
                    supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": nc, "horario": hc, "anio_lectivo": 2026}).execute()
                    st.rerun()

    # Mensajes para pestañas en desarrollo
    for i, label in [(0, "Agenda"), (2, "Asistencia"), (3, "Notas")]:
        with tabs[i]:
            st.subheader(label)
            st.info("Pestaña lista para recibir datos de alumnos.")
