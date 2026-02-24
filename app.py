import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ClassTrack 360", layout="wide")

# --- CONEXIÓN ---
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
    .stApp { background-color: #0b0e14; color: #e0e0e0; }
    .logo-text { font-weight: 800; background: linear-gradient(to right, #3b82f6, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br><div class='logo-text'>ClassTrack 360</div>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuario (Email)").strip()
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
                res = supabase.table("usuarios").select("*").eq("email", u).eq("password_text", p).execute()
                if res.data:
                    st.session_state.user = res.data[0]
                    st.rerun()
                else: st.error("Acceso denegado.")
else:
    user = st.session_state.user
    st.sidebar.write(f"Profe: {user['email']}")
    if st.sidebar.button("CERRAR SESIÓN"):
        st.session_state.user = None
        st.rerun()
    
    tabs = st.tabs(["📅 Agenda", "👥 Alumnos", "🏗️ Cursos", "🔍 Historial y Edición"])

    # Traer cursos actuales del profesor
    res_c = supabase.table("inscripciones").select("id, nombre_curso_materia, horario").eq("profesor_id", user['id']).execute()

    # --- TAB 2: CURSOS (CON VALIDACIÓN ANTI-DUPLICADOS) ---
    with tabs[2]:
        st.subheader("Tus Materias")
        if res_c.data:
            df_mostrar = pd.DataFrame(res_c.data)
            for _, cur in df_mostrar.iterrows():
                col_b1, col_b2 = st.columns([4,1])
                col_b1.write(f"📘 **{cur['nombre_curso_materia']}** ({cur['horario']})")
                if col_b2.button("Borrar", key=f"bc_{cur['id']}"):
                    supabase.table("inscripciones").delete().eq("id", cur['id']).execute()
                    st.rerun()
        
        st.divider()
        st.write("➕ **Añadir Nueva Materia**")
        with st.form("nc", clear_on_submit=True):
            n_m = st.text_input("Nombre de la Materia")
            h_m = st.text_input("Horario")
            if st.form_submit_button("Añadir Curso"):
                if n_m and h_m:
                    # VALIDACIÓN: ¿Ya existe?
                    duplicado = any(d['nombre_curso_materia'].lower() == n_m.lower() and d['horario'].lower() == h_m.lower() for d in res_c.data)
                    if duplicado:
                        st.error("⚠️ Este curso ya existe con ese mismo horario.")
                    else:
                        supabase.table("inscripciones").insert({"profesor_id": user['id'], "nombre_curso_materia": n_m, "horario": h_m, "anio_lectivo": 2026}).execute()
                        st.success(f"Curso {n_m} creado.")
                        st.rerun()
                else:
                    st.warning("Completá ambos campos.")

    # --- TAB 0: AGENDA (REACTIVA) ---
    with tabs[0]:
        st.subheader("Registro Diario")
        if res_c.data:
            # Quitamos duplicados visuales para el selector por seguridad
            lista_cursos = list(set([f"{row['nombre_curso_materia']} | {row['horario']}" for row in res_c.data]))
            
            c_hoy = st.selectbox("Materia", lista_cursos)
            tipo_doc = st.radio("Docente a cargo", ["TITULAR", "SUPLENTE"], horizontal=True)
            
            docente_final = user['email']
            col_s1, col_s2 = st.columns(2)
            if tipo_doc == "SUPLENTE":
                n_s = col_s1.text_input("Nombre Suplente")
                a_s = col_s2.text_input("Apellido Suplente")
                docente_final = f"Suplente: {n_s} {a_s}"
            
            with st.form("form_clase"):
                temas = st.text_area("Temas de hoy")
                tarea = st.text_area("Tarea asignada")
                venc = st.date_input("Fecha de entrega", datetime.date.today() + datetime.timedelta(days=7))
                if st.form_submit_button("Guardar Clase"):
                    # Buscar el ID correcto del curso
                    c_nombre_busq = c_hoy.split(" | ")[0]
                    c_horario_busq = c_hoy.split(" | ")[1]
                    c_id = next(item['id'] for item in res_c.data if item['nombre_curso_materia'] == c_nombre_busq and item['horario'] == c_horario_busq)
                    
                    supabase.table("bitacora").insert({
                        "curso_id": int(c_id), "profesor_id": user['id'], "fecha": str(datetime.date.today()),
                        "docente_nombre": docente_final, "temas": temas, "tarea_descripcion": tarea, "tarea_vencimiento": str(venc)
                    }).execute()
                    st.success("✅ Guardado en bitácora")
                    st.balloons()
        else: st.info("Cargá un curso primero.")

    # --- TAB 3: HISTORIAL (SEGURO) ---
    with tabs[3]:
        st.subheader("Gestión de Historial")
        try:
            clases = supabase.table("bitacora").select("*").eq("profesor_id", user['id']).order("fecha", desc=True).execute()
            if clases.data:
                for cl in clases.data:
                    with st.expander(f"📅 {cl['fecha']} - {cl['docente_nombre']}"):
                        st.write(f"**Temas:** {cl['temas']}")
                        st.write(f"**Tarea:** {cl['tarea_descripcion']}")
                        if st.button("Eliminar Registro", key=f"del_{cl['id']}"):
                            supabase.table("bitacora").delete().eq("id", cl['id']).execute()
                            st.rerun()
            else: st.info("No hay clases registradas aún.")
        except:
            st.info("La bitácora está lista para tu primer registro.")
