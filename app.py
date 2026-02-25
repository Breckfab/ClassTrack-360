# --- TAB 0: AGENDA (CON MEMORIA INTELIGENTE) ---
with tabs[0]:
    st.subheader("Registro de Clase y Continuidad")
    if df_cursos.empty:
        st.markdown('<div class="warning-card">⚠️ No hay materias. Crea una en la pestaña <b>Cursos</b>.</div>', unsafe_allow_html=True)
    else:
        c_agenda = st.selectbox("Materia de hoy:", df_cursos['nombre_curso_materia'].unique())
        
        # --- LÓGICA DE RECUPERACIÓN DE CLASE ANTERIOR ---
        ultima_clase = None
        try:
            # Buscamos el último registro de bitácora para esta materia y este profesor
            res_b = supabase.table("bitacora").select("*")\
                .eq("profesor_id", user['id'])\
                .eq("materia", c_agenda)\
                .order("created_at", desc=True)\
                .limit(1).execute()
            if res_b.data:
                ultima_clase = res_b.data[0]
        except:
            pass

        # Mostrar recordatorio de la clase anterior
        if ultima_clase:
            tarea_pendiente = ultima_clase.get('tarea_proxima', '').strip()
            temas_anteriores = ultima_clase.get('temas_dictados', '').strip()
            
            # Cuadro de Tarea
            if tarea_pendiente:
                st.markdown(f'<div class="reminder-box">🔔 <b>Tarea para revisar hoy:</b><br>{tarea_pendiente}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="reminder-box">✅ <b>No hay tarea pendiente para revisar hoy.</b></div>', unsafe_allow_html=True)
            
            # Cuadro de Continuidad
            st.info(f"📍 **La clase anterior ({ultima_clase['fecha']}) viste:**\n\n{temas_anteriores}")
        else:
            st.markdown('<div class="reminder-box">🆕 <b>Primera clase:</b> No hay registros previos para esta materia.</div>', unsafe_allow_html=True)

        st.write("---")
        # Formulario para la clase de hoy
        with st.form("form_agenda_hoy", clear_on_submit=True):
            st.write(f"📝 **Registro para hoy: {hoy.strftime('%d/%m/%Y')}**")
            temas_hoy = st.text_area("¿Qué temas vas a dictar hoy?", placeholder="Ej: Introducción a la unidad 2...")
            tarea_hoy = st.text_area("Tarea para la próxima clase:", placeholder="Ej: Leer páginas 45 a 50...")
            f_venc = st.date_input("Fecha de entrega estimada:", hoy + datetime.timedelta(days=7))
            
            if st.form_submit_button("Guardar y Finalizar Clase"):
                if temas_hoy:
                    try:
                        data_insert = {
                            "profesor_id": user['id'],
                            "materia": c_agenda,
                            "fecha": hoy.strftime('%Y-%m-%d'),
                            "temas_dictados": temas_hoy,
                            "tarea_proxima": tarea_hoy,
                            "vencimiento_tarea": f_venc.strftime('%Y-%m-%d')
                        }
                        supabase.table("bitacora").insert(data_insert).execute()
                        st.success("¡Clase guardada! La próxima vez que entres, verás estos datos como referencia.")
                        st.rerun()
                    except:
                        st.error("Error al guardar en la base de datos.")
                else:
                    st.warning("Debes completar los temas dictados para guardar la clase.")
