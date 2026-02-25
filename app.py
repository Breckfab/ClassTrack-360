# --- TAB 0: AGENDA (CON RECUPERACIÓN DE TAREA) ---
    with tabs[0]:
        st.subheader("Registro de Clase")
        if df_cursos.empty:
            st.markdown('<div class="warning-card">⚠️ No hay materias creadas.</div>', unsafe_allow_html=True)
        else:
            c_agenda = st.selectbox("Materia:", df_cursos['nombre_curso_materia'].unique())
            
            # --- LÓGICA PARA RECUPERAR TAREA ANTERIOR ---
            try:
                res_b = supabase.table("bitacora").select("*").eq("profesor_id", user['id']).eq("materia", c_agenda).order("fecha", desc=True).limit(1).execute()
                
                if res_b.data:
                    tarea_p = res_b.data[0].get("tarea_proxima", "")
                    if tarea_p:
                        st.markdown(f'<div class="reminder-box">🔔 <b>Tarea para revisar hoy:</b><br>{tarea_p}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="reminder-box">✅ <b>No hay tarea para revisar hoy.</b></div>', unsafe_allow_html=True)
                    
                    st.info(f"📍 En la clase anterior viste: {res_b.data[0].get('temas_dictados', 'Sin registro')}")
                else:
                    st.markdown('<div class="reminder-box">📝 No hay registros previos para esta materia.</div>', unsafe_allow_html=True)
            except:
                st.error("No se pudo conectar con la bitácora.")

            # --- FORMULARIO PARA GUARDAR LA CLASE DE HOY ---
            with st.form("f_agenda_final_v7"):
                t_hoy = st.text_area("Temas dictados hoy")
                t_proxima = st.text_area("Tarea para la próxima clase")
                if st.form_submit_button("Guardar Clase"):
                    if t_hoy:
                        try:
                            supabase.table("bitacora").insert({
                                "profesor_id": user['id'],
                                "materia": c_agenda,
                                "fecha": str(datetime.datetime.now().date()),
                                "temas_dictados": t_hoy,
                                "tarea_proxima": t_proxima
                            }).execute()
                            st.success("Clase guardada exitosamente.")
                            st.rerun()
                        except:
                            st.error("Error al guardar en la base de datos.")
                    else:
                        st.warning("Por favor, completa los temas dictados.")
