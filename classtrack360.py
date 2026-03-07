# ============================================================
# INICIO PARTE 1 DE 2 — ClassTrack 360 v288
# ============================================================

import streamlit as st
from supabase import create_client
import datetime
import calendar
import streamlit.components.v1 as components
import io
import random
import string
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    EXCEL_OK = True
except ImportError:
    EXCEL_OK = False

st.set_page_config(page_title="ClassTrack 360 v288", layout="wide")

SUPABASE_URL = "https://tzevdylabtradqmcqldx.supabase.co"
SUPABASE_KEY = "sb_publishable_SVgeWB2OpcuC3rd6L6b8sg_EcYfgUir"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ANIO_ACTUAL = datetime.date.today().year

def init_state():
    defaults = {
        'user': None, 'sede_admin': None,
        'editando_bitacora': None, 'editando_alumno': None, 'editando_curso': None,
        'confirmar_reset': None,
        'cal_mes': datetime.date.today().month, 'cal_anio': datetime.date.today().year,
        'es_suplente': False,
        'prev_curso_alumnos': None, 'prev_curso_notas_ver': None,
        'prev_curso_notas_carga': None, 'prev_curso_busq_hist': None,
        'busq_alumno_val': '', 'busq_nota_val': '', 'filtro_estado_val': 'Todos',
        'busq_carga_val': '', 'busq_contenido_hist_val': '', 'tipo_prof_val': 'Todos',
        'pantalla_login': 'login',
        'editando_tarea': None,
        'editando_tarea_legacy': None,
        'hist_curso': 'Todos',
        'hist_contenido': '',
        'hist_tipo_prof': 'Todos',
        'hist_anio': datetime.date.today().year,
        'hist_desde': datetime.date(datetime.date.today().year, 1, 1),
        'hist_hasta': datetime.date.today(),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def footer():
    st.markdown('<div class="footer-cr">&#174; Sistema diseñado y realizado por Fabián Belledi &nbsp;·&nbsp; 2026</div>', unsafe_allow_html=True)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@300;400&display=swap');
    .stApp { background: #080b10; color: #e8eaf0; font-family: 'DM Mono', monospace; }
    .stApp::before {
        content: ''; position: fixed; inset: 0; z-index: 0; pointer-events: none;
        background-image: linear-gradient(rgba(79,172,254,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(79,172,254,0.04) 1px, transparent 1px);
        background-size: 48px 48px;
    }
    .planilla-row { background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4facfe; border: 1px solid rgba(255,255,255,0.1); }
    .tarea-alerta { background: rgba(255,193,7,0.25); border: 2px solid #ffc107; padding: 20px; border-radius: 12px; color: #ffc107; text-align: center; font-weight: 800; margin-bottom: 10px; font-size: 1.2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    .tarea-card { background: rgba(255,193,7,0.08); border: 1px solid rgba(255,193,7,0.25); border-radius: 10px; padding: 14px 18px; margin-bottom: 8px; }
    .tarea-card .tarea-titulo { color: #ffc107; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px; }
    .tarea-card .tarea-texto { color: #e8eaf0; font-size: 0.9rem; margin-bottom: 4px; }
    .tarea-card .tarea-fecha { color: #778; font-size: 0.75rem; }
    .tarea-card-done { background: rgba(79,172,254,0.05); border: 1px solid rgba(79,172,254,0.15); border-radius: 10px; padding: 10px 18px; margin-bottom: 8px; opacity: 0.5; }
    .tarea-card-done .tarea-titulo { color: #4facfe; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px; }
    .tarea-card-done .tarea-texto { color: #778; font-size: 0.9rem; text-decoration: line-through; margin-bottom: 4px; }
    .tarea-card-done .tarea-fecha { color: #556; font-size: 0.75rem; }
    .tarea-card-vencida { background: rgba(255,77,109,0.10); border: 2px solid rgba(255,77,109,0.5); border-radius: 10px; padding: 14px 18px; margin-bottom: 8px; }
    .tarea-card-vencida .tarea-titulo { color: #ff4d6d; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px; }
    .tarea-card-vencida .tarea-texto { color: #e8eaf0; font-size: 0.9rem; margin-bottom: 4px; }
    .tarea-card-vencida .tarea-fecha { color: #ff4d6d; font-size: 0.75rem; font-weight: 700; }
    .vencidas-header { color: #ff4d6d; font-weight: 700; font-size: 0.9rem; margin-bottom: 10px; margin-top: 4px; background: rgba(255,77,109,0.07); border: 1px solid rgba(255,77,109,0.25); border-radius: 8px; padding: 8px 14px; }
    .badge-vencidas { background: #ff4d6d; color: #fff; font-family: 'Syne', sans-serif; font-weight: 800; font-size: 0.8rem; border-radius: 20px; padding: 4px 14px; display: inline-block; margin-bottom: 8px; letter-spacing: 0.05em; }
    .badge-clases { background: rgba(79,172,254,0.15); border: 1px solid rgba(79,172,254,0.4); color: #4facfe; font-family: 'Syne', sans-serif; font-weight: 800; font-size: 0.8rem; border-radius: 20px; padding: 4px 14px; display: inline-block; margin-bottom: 8px; letter-spacing: 0.05em; }
    .proxima-clase-card { background: rgba(79,172,254,0.07); border: 1px solid rgba(79,172,254,0.25); border-radius: 10px; padding: 12px 18px; margin-bottom: 12px; }
    .proxima-clase-card .pc-titulo { color: #4facfe; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px; }
    .proxima-clase-card .pc-fecha { color: #e8eaf0; font-size: 1rem; font-weight: 700; margin-bottom: 2px; }
    .proxima-clase-card .pc-detalle { color: #778; font-size: 0.78rem; }
    .contador-card { background: rgba(79,172,254,0.05); border: 1px solid rgba(79,172,254,0.2); border-radius: 12px; padding: 18px 22px; margin-bottom: 12px; }
    .contador-card .cc-nombre { color: #e8eaf0; font-size: 0.95rem; font-weight: 700; margin-bottom: 8px; }
    .contador-card .cc-info { color: #4facfe; font-size: 0.78rem; margin-bottom: 4px; }
    .contador-card .cc-clases { color: #a0c4ff; font-size: 0.82rem; margin-top: 6px; }
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
    .suplente-badge { background: rgba(255,193,7,0.12); border: 1px solid rgba(255,193,7,0.35); border-radius: 6px; padding: 3px 10px; color: #ffc107; font-size: 0.78rem; font-weight: 700; display: inline-block; margin-top: 4px; }
    .titular-badge { background: rgba(79,172,254,0.1); border: 1px solid rgba(79,172,254,0.3); border-radius: 6px; padding: 3px 10px; color: #4facfe; font-size: 0.78rem; font-weight: 700; display: inline-block; margin-top: 4px; }
    .filtros-box { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.07); border-radius: 10px; padding: 14px 18px; margin-bottom: 16px; }
    .no-encontrado { background: rgba(255,77,109,0.07); border: 1px solid rgba(255,77,109,0.2); border-radius: 8px; padding: 12px 18px; color: #ff4d6d; font-size: 0.88rem; margin-top: 8px; }
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
    .codigo-box { background: rgba(79,172,254,0.08); border: 1px solid rgba(79,172,254,0.3); border-radius: 8px; padding: 12px 18px; font-family: 'DM Mono', monospace; font-size: 1.1rem; color: #4facfe; font-weight: 700; letter-spacing: 0.15em; text-align: center; margin: 8px 0; }
    .habilitado-tag { color: #4facfe; background: rgba(79,172,254,0.1); border: 1px solid rgba(79,172,254,0.3); padding: 2px 10px; border-radius: 5px; font-size: 0.75rem; font-weight: 700; }
    .deshabilitado-tag { color: #ff4d6d; background: rgba(255,77,109,0.1); border: 1px solid rgba(255,77,109,0.3); padding: 2px 10px; border-radius: 5px; font-size: 0.75rem; font-weight: 700; }
    .footer-cr { position: fixed; bottom: 0; left: 0; right: 0; text-align: center; padding: 6px; font-size: 0.72rem; color: #c8d8f0; font-family: 'DM Mono', monospace; background: #080b10; border-top: 1px solid rgba(255,255,255,0.08); z-index: 999; letter-spacing: 0.05em; }
    .tareas-pendientes-header { color: #ffc107; font-weight: 700; font-size: 0.9rem; margin-bottom: 10px; margin-top: 4px; }
    .registro-link { text-align: center; margin-top: 16px; font-size: 0.78rem; color: #4a5568; }
    .email-tag { color: #4facfe; font-size: 0.78rem; margin-top: 2px; }
    .calendario-box { background: rgba(79,172,254,0.06); border: 1px solid rgba(79,172,254,0.2); border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; }
    .calendario-box .cal-header { color: #4facfe; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 10px; }
    .calendario-box .cal-fechas { color: #e8eaf0; font-size: 0.9rem; }
    .calendario-box .cal-dias { color: #778; font-size: 0.78rem; margin-top: 4px; }
    .cronograma-box { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.07); border-radius: 10px; padding: 14px 18px; margin-bottom: 12px; }
    .cronograma-titulo { color: #4facfe; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIONES ---
def no_encontrado(msg):
    st.markdown(f'<div class="no-encontrado">🔍 {msg}</div>', unsafe_allow_html=True)

def color_nota(n):
    if n <= 3: return "baja"
    elif n <= 5: return "media"
    else: return "alta"

def estado_aprobacion(promedio, nota_aprobacion):
    if promedio is None or nota_aprobacion is None: return ""
    if promedio >= float(nota_aprobacion): return '<span class="aprobado">✅ APROBADO</span>'
    else: return '<span class="desaprobado">❌ DESAPROBADO</span>'

def estado_texto(promedio, nota_aprobacion):
    if promedio is None or nota_aprobacion is None: return "-"
    return "APROBADO" if promedio >= float(nota_aprobacion) else "DESAPROBADO"

def validar_hora(h):
    try:
        datetime.datetime.strptime(h.strip(), "%H:%M")
        return True
    except: return False

def format_horario(inicio, fin):
    if inicio and fin: return f"{str(inicio)[:5]} → {str(fin)[:5]}"
    elif inicio: return str(inicio)[:5]
    return "-"

def generar_codigo():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def marcar_tarea(bit_id, num_tarea, completada):
    try:
        supabase.table("bitacora").update({f"tarea{num_tarea}_completada": completada}).eq("id", bit_id).execute()
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

def marcar_tarea_proxima(bit_id, completada):
    try:
        supabase.table("bitacora").update({"tarea_proxima_completada": completada}).eq("id", bit_id).execute()
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

def guardar_edicion_tarea(bit_id, num_tarea, nuevo_texto, nueva_fecha):
    try:
        supabase.table("bitacora").update({
            f"tarea{num_tarea}": nuevo_texto.strip() or None,
            f"tarea{num_tarea}_fecha": str(nueva_fecha) if nuevo_texto.strip() else None,
        }).eq("id", bit_id).execute()
        st.session_state.editando_tarea = None
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

def guardar_edicion_tarea_legacy(bit_id, nuevo_texto):
    try:
        supabase.table("bitacora").update({
            "tarea_proxima": nuevo_texto.strip() or None,
        }).eq("id", bit_id).execute()
        st.session_state.editando_tarea_legacy = None
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

def get_tareas_vencidas_count(profesor_id):
    hoy = datetime.date.today()
    try:
        res_insc = supabase.table("inscripciones").select("id").eq("profesor_id", profesor_id).is_("alumno_id", "null").execute()
        if not res_insc.data: return 0
        ids = [r['id'] for r in res_insc.data]
        total_vencidas = 0
        for iid in ids:
            res = supabase.table("bitacora").select(
                "tarea1, tarea1_fecha, tarea1_completada, tarea2, tarea2_fecha, tarea2_completada, tarea3, tarea3_fecha, tarea3_completada"
            ).eq("inscripcion_id", iid).execute()
            for reg in (res.data or []):
                for i in range(1, 4):
                    txt = reg.get(f'tarea{i}')
                    fecha_t = reg.get(f'tarea{i}_fecha')
                    completada = reg.get(f'tarea{i}_completada', False)
                    if txt and not completada and fecha_t:
                        if datetime.date.fromisoformat(fecha_t) < hoy:
                            total_vencidas += 1
        return total_vencidas
    except: return 0

def get_stats_curso(inscripcion_id):
    try:
        res = supabase.table("bitacora").select("fecha").eq("inscripcion_id", inscripcion_id).order("fecha", desc=True).execute()
        cant = len(res.data) if res.data else 0
        ultima = datetime.date.fromisoformat(res.data[0]['fecha']).strftime('%d/%m/%Y') if res.data else None
        return cant, ultima
    except:
        return 0, None

def get_total_clases_sidebar(profesor_id):
    """v288: total de clases dictadas en todos los cursos para el sidebar."""
    try:
        res_insc = supabase.table("inscripciones").select("id").eq("profesor_id", profesor_id).is_("alumno_id", "null").execute()
        if not res_insc.data: return 0
        total = 0
        for r in res_insc.data:
            cant, _ = get_stats_curso(r['id'])
            total += cant
        return total
    except: return 0

DIAS_SEMANA_MAP = {
    'lunes': 0, 'martes': 1, 'miércoles': 2, 'miercoles': 2,
    'jueves': 3, 'viernes': 4, 'sábado': 5, 'sabado': 5, 'domingo': 6
}
DIAS_SEMANA_ES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
MESES_ES_LARGO = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']

def extraer_dias_curso(nombre_curso):
    dias = []
    try:
        if '(' in nombre_curso and ')' in nombre_curso:
            parte = nombre_curso.split('(')[1].split(')')[0]
            for token in parte.split(','):
                t = token.strip().lower()
                if t in DIAS_SEMANA_MAP:
                    dias.append(DIAS_SEMANA_MAP[t])
    except: pass
    return sorted(set(dias))

def get_proxima_clase(nombre_curso, hora_inicio, hora_fin):
    dias = extraer_dias_curso(nombre_curso)
    if not dias: return None
    hoy = datetime.date.today()
    for offset in range(1, 8):
        candidato = hoy + datetime.timedelta(days=offset)
        if candidato.weekday() in dias:
            dias_faltan = offset
            nombre_dia = DIAS_SEMANA_ES[candidato.weekday()]
            fecha_fmt = f"{nombre_dia} {candidato.day} de {MESES_ES_LARGO[candidato.month - 1]}"
            horario = format_horario(str(hora_inicio or '')[:5], str(hora_fin or '')[:5])
            return {
                'fecha_fmt': fecha_fmt,
                'dias_faltan': dias_faltan,
                'horario': horario,
                'fecha': candidato,
            }
    return None

def render_calendario(mes, anio):
    MESES_ES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    hoy = datetime.date.today()
    cal = calendar.monthcalendar(anio, mes)
    filas = ""
    for semana in cal:
        fila = ""
        for dia in semana:
            if dia == 0: fila += '<td class="vacio">·</td>'
            elif dia == hoy.day and mes == hoy.month and anio == hoy.year: fila += f'<td class="hoy">{dia}</td>'
            else: fila += f'<td>{dia}</td>'
        filas += f"<tr>{fila}</tr>"
    return f"""<div class="cal-box"><div class="cal-titulo">{MESES_ES[mes-1]} {anio}</div>
    <table class="cal-tabla"><tr><th>Lu</th><th>Ma</th><th>Mi</th><th>Ju</th><th>Vi</th><th>Sa</th><th>Do</th></tr>{filas}</table></div>"""

def get_calendario_sede(sede):
    try:
        res = supabase.table("calendario_sede").select("*").eq("sede", sede).execute()
        return res.data[0] if res.data else None
    except: return None

def upsert_calendario_sede(sede, fecha_inicio, fecha_fin):
    try:
        existing = get_calendario_sede(sede)
        if existing:
            supabase.table("calendario_sede").update({
                "fecha_inicio": str(fecha_inicio) if fecha_inicio else None,
                "fecha_fin": str(fecha_fin) if fecha_fin else None,
                "updated_at": datetime.datetime.now().isoformat()
            }).eq("sede", sede).execute()
        else:
            supabase.table("calendario_sede").insert({
                "sede": sede,
                "fecha_inicio": str(fecha_inicio) if fecha_inicio else None,
                "fecha_fin": str(fecha_fin) if fecha_fin else None,
            }).execute()
        return True
    except Exception as e:
        st.error(f"Error guardando calendario: {e}")
        return False

def subir_cronograma(sede, cuatrimestre, archivo):
    try:
        ext = archivo.name.split('.')[-1].lower()
        path = f"{sede}/cronograma_{cuatrimestre}c.{ext}"
        data = archivo.read()
        try:
            supabase.storage.from_("cronogramas").remove([path])
        except: pass
        supabase.storage.from_("cronogramas").upload(path, data, {"content-type": archivo.type, "upsert": "true"})
        url = supabase.storage.from_("cronogramas").get_public_url(path)
        existing = get_calendario_sede(sede)
        campo_url = f"cronograma_{cuatrimestre}c_url"
        campo_nombre = f"cronograma_{cuatrimestre}c_nombre"
        if existing:
            supabase.table("calendario_sede").update({
                campo_url: url,
                campo_nombre: archivo.name,
                "updated_at": datetime.datetime.now().isoformat()
            }).eq("sede", sede).execute()
        else:
            supabase.table("calendario_sede").insert({
                "sede": sede,
                campo_url: url,
                campo_nombre: archivo.name,
            }).execute()
        return url
    except Exception as e:
        st.error(f"Error subiendo cronograma: {e}")
        return None

def render_cronograma_visor(url, nombre, titulo):
    if not url: return
    ext = nombre.split('.')[-1].lower() if nombre else ''
    st.markdown(f'<div class="cronograma-box"><div class="cronograma-titulo">📅 {titulo}</div>', unsafe_allow_html=True)
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        st.image(url, use_container_width=True)
    elif ext == 'pdf':
        components.html(f'<iframe src="{url}" width="100%" height="600px" style="border:none;border-radius:8px;"></iframe>', height=620)
    else:
        st.markdown(f'⚠️ Este formato ({ext.upper()}) no se puede previsualizar. <a href="{url}" target="_blank" style="color:#4facfe;">Descargar archivo</a>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def reset_completo_sede(sede_nombre):
    try:
        res_u = supabase.table("usuarios").select("id").eq("sede", sede_nombre).execute()
        if not res_u.data: return False, "No se encontró la sede."
        profesor_id = res_u.data[0]['id']
        res_insc = supabase.table("inscripciones").select("id, alumno_id").eq("profesor_id", profesor_id).execute()
        ids_alumnos = list(set([i['alumno_id'] for i in res_insc.data if i.get('alumno_id')] if res_insc.data else []))
        for iid in [i['id'] for i in res_insc.data] if res_insc.data else []:
            supabase.table("notas").delete().eq("inscripcion_id", iid).execute()
            supabase.table("bitacora").delete().eq("inscripcion_id", iid).execute()
        supabase.table("inscripciones").delete().eq("profesor_id", profesor_id).execute()
        for aid in ids_alumnos:
            supabase.table("alumnos").delete().eq("id", aid).execute()
        return True, f"Sede {sede_nombre.upper()} reseteada correctamente."
    except Exception as e:
        return False, str(e)

def generar_excel(sede, curso_nombre, curso_data, datos):
    """v288: genera Excel con alumnos y notas."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Alumnos y Notas"

    azul = "1A5276"
    azul_claro = "D6EAF8"
    gris = "F2F2F2"

    header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill("solid", fgColor=azul)
    header_align = Alignment(horizontal="center", vertical="center")
    subheader_fill = PatternFill("solid", fgColor=azul_claro)
    subheader_font = Font(name="Calibri", bold=True, size=10)
    normal_font = Font(name="Calibri", size=10)
    center_align = Alignment(horizontal="center", vertical="center")
    thin = Side(style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # Título
    ws.merge_cells("A1:J1")
    ws["A1"] = f"ClassTrack 360 — Sede: {sede.upper()}"
    ws["A1"].font = Font(name="Calibri", bold=True, size=14, color="FFFFFF")
    ws["A1"].fill = header_fill
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    ws.merge_cells("A2:J2")
    ws["A2"] = f"Curso: {curso_nombre}"
    ws["A2"].font = subheader_font
    ws["A2"].fill = subheader_fill
    ws["A2"].alignment = Alignment(horizontal="center")
    ws.row_dimensions[2].height = 20

    hi = str(curso_data.get('hora_inicio','') or '')[:5]
    hf = str(curso_data.get('hora_fin','') or '')[:5]
    nota_ap = curso_data.get('nota_aprobacion')
    biblio = curso_data.get('bibliografia','') or ''
    info_txt = f"Horario: {format_horario(hi, hf)}   |   Aprobación: {nota_ap if nota_ap else 'Sin definir'}   |   Generado: {datetime.date.today().strftime('%d/%m/%Y')}"
    ws.merge_cells("A3:J3")
    ws["A3"] = info_txt
    ws["A3"].font = Font(name="Calibri", size=9, color="555555")
    ws["A3"].alignment = Alignment(horizontal="center")
    ws.row_dimensions[3].height = 16

    if biblio:
        ws.merge_cells("A4:J4")
        ws["A4"] = f"Bibliografía: {biblio}"
        ws["A4"].font = Font(name="Calibri", size=9, italic=True, color="777777")
        ws["A4"].alignment = Alignment(horizontal="center")
        ws.row_dimensions[4].height = 14
        fila_headers = 6
    else:
        fila_headers = 5

    # Headers tabla
    headers = ["#", "Apellido", "Nombre", "Email", "Nota 1", "Nota 2", "Nota 3", "Nota 4", "Nota 5", "Promedio", "Estado"]
    col_widths = [5, 20, 18, 28, 9, 9, 9, 9, 9, 11, 14]
    for col_idx, (h, w) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=fila_headers, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = border
        ws.column_dimensions[cell.column_letter].width = w
    ws.row_dimensions[fila_headers].height = 22

    alumnos_data = datos.get('alumnos', [])
    notas_data = datos.get('notas', {})

    for idx, al in enumerate(sorted(alumnos_data, key=lambda x: x['apellido']), 1):
        fila = fila_headers + idx
        ns = notas_data.get(al['insc_id'], [])
        promedio = round(sum(ns)/len(ns), 2) if ns else None
        estado = estado_texto(promedio, nota_ap) if promedio is not None else "Sin notas"

        row_fill = PatternFill("solid", fgColor="FFFFFF") if idx % 2 != 0 else PatternFill("solid", fgColor=gris)

        datos_fila = [
            idx,
            al['apellido'].upper(),
            al['nombre'],
            al.get('email','') or '',
            ns[0] if len(ns) > 0 else '',
            ns[1] if len(ns) > 1 else '',
            ns[2] if len(ns) > 2 else '',
            ns[3] if len(ns) > 3 else '',
            ns[4] if len(ns) > 4 else '',
            promedio if promedio is not None else '',
            estado,
        ]
        for col_idx, val in enumerate(datos_fila, 1):
            cell = ws.cell(row=fila, column=col_idx, value=val)
            cell.font = normal_font
            cell.fill = row_fill
            cell.border = border
            if col_idx in [1, 5, 6, 7, 8, 9, 10]:
                cell.alignment = center_align
            if col_idx == 11 and val == "APROBADO":
                cell.font = Font(name="Calibri", size=10, bold=True, color="1A5276")
            elif col_idx == 11 and val == "DESAPROBADO":
                cell.font = Font(name="Calibri", size=10, bold=True, color="C0392B")

        ws.row_dimensions[fila].height = 18

    # Freeze headers
    ws.freeze_panes = ws.cell(row=fila_headers + 1, column=1)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()

def generar_pdf(sede, curso_nombre, curso_data, incluir_alumnos, incluir_notas, incluir_historial, incluir_resumen, datos):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    azul = colors.HexColor('#1a5276')
    gris = colors.HexColor('#555555')
    gris_claro = colors.HexColor('#f2f2f2')
    estilo_titulo = ParagraphStyle('titulo', parent=styles['Normal'], fontSize=18, fontName='Helvetica-Bold', textColor=azul, spaceAfter=4, alignment=TA_CENTER)
    estilo_subtitulo = ParagraphStyle('subtitulo', parent=styles['Normal'], fontSize=11, fontName='Helvetica', textColor=gris, spaceAfter=12, alignment=TA_CENTER)
    estilo_seccion = ParagraphStyle('seccion', parent=styles['Normal'], fontSize=13, fontName='Helvetica-Bold', textColor=azul, spaceBefore=16, spaceAfter=8)
    estilo_normal = ParagraphStyle('normal', parent=styles['Normal'], fontSize=9, fontName='Helvetica', spaceAfter=4)
    estilo_small = ParagraphStyle('small', parent=styles['Normal'], fontSize=8, fontName='Helvetica', textColor=gris, spaceAfter=2)
    story = []
    story.append(Paragraph("ClassTrack 360", estilo_titulo))
    story.append(Paragraph(f"Sede: {sede.upper()}  ·  {curso_nombre}", estilo_subtitulo))
    story.append(Paragraph(f"Generado el {datetime.date.today().strftime('%d/%m/%Y')}", estilo_small))
    story.append(HRFlowable(width="100%", thickness=2, color=azul, spaceAfter=16))
    hi = str(curso_data.get('hora_inicio','') or '')[:5]
    hf = str(curso_data.get('hora_fin','') or '')[:5]
    nota_ap = curso_data.get('nota_aprobacion')
    biblio = curso_data.get('bibliografia','')
    info_curso = []
    if hi and hf: info_curso.append(f"Horario: {hi} -> {hf}")
    if nota_ap: info_curso.append(f"Nota de aprobacion: {nota_ap}")
    if biblio: info_curso.append(f"Bibliografia: {biblio}")
    if info_curso:
        story.append(Paragraph(" · ".join(info_curso), estilo_small))
        story.append(Spacer(1, 8))
    alumnos_data = datos.get('alumnos', [])
    notas_data = datos.get('notas', {})
    historial_data = datos.get('historial', [])
    if incluir_resumen and alumnos_data:
        story.append(Paragraph("Resumen del Curso", estilo_seccion))
        total = len(alumnos_data); aprobados = 0; promedios = []
        for al in alumnos_data:
            ns = notas_data.get(al['insc_id'], [])
            if ns:
                prom = round(sum(ns)/len(ns), 2); promedios.append(prom)
                if nota_ap and prom >= float(nota_ap): aprobados += 1
        prom_gral = round(sum(promedios)/len(promedios), 2) if promedios else "-"
        porc = f"{round(aprobados/total*100)}%" if total > 0 else "-"
        t = Table([["Total alumnos","Con notas","Aprobados","% Aprobados","Promedio general"],
                   [str(total),str(len(promedios)),str(aprobados),porc,str(prom_gral)]], colWidths=[3.2*cm]*5)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),azul),('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,gris_claro])]))
        story.append(t); story.append(Spacer(1,12))
    if incluir_alumnos and alumnos_data:
        story.append(Paragraph("Listado de Alumnos", estilo_seccion))
        rows = [["#","Apellido","Nombre","Email"]]
        for idx, al in enumerate(sorted(alumnos_data, key=lambda x: x['apellido']), 1):
            rows.append([str(idx), al['apellido'].upper(), al['nombre'], al.get('email','') or '-'])
        t = Table(rows, colWidths=[1*cm,5*cm,5*cm,5*cm])
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),azul),('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),
            ('ALIGN',(0,0),(0,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,gris_claro])]))
        story.append(t); story.append(Spacer(1,12))
    if incluir_notas and alumnos_data:
        story.append(Paragraph("Notas y Promedios", estilo_seccion))
        rows = [["Alumno","Nota 1","Nota 2","Nota 3","Nota 4","Nota 5","Promedio","Estado"]]
        for al in sorted(alumnos_data, key=lambda x: x['apellido']):
            ns = notas_data.get(al['insc_id'], [])
            fila = [f"{al['apellido'].upper()}, {al['nombre']}"]
            for i in range(5): fila.append(str(ns[i]) if i < len(ns) else "-")
            if ns:
                prom = round(sum(ns)/len(ns), 2)
                fila += [str(prom), estado_texto(prom, nota_ap)]
            else:
                fila += ["-", "Sin notas"]
            rows.append(fila)
        t = Table(rows, colWidths=[5*cm]+[1.5*cm]*5+[2*cm,2.5*cm])
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),azul),('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),
            ('ALIGN',(1,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,gris_claro])]))
        story.append(t); story.append(Spacer(1,12))
    if incluir_historial and historial_data:
        story.append(Paragraph("Historial de Clases", estilo_seccion))
        for reg in sorted(historial_data, key=lambda x: x['fecha']):
            fecha_fmt = datetime.date.fromisoformat(reg['fecha']).strftime('%d/%m/%Y')
            suplente = reg.get('profesor_suplente')
            prof = f"Suplente: {suplente}" if suplente else "Titular"
            story.append(Paragraph(f"<b>{fecha_fmt}</b> · {prof}", estilo_normal))
            contenido = reg.get('contenido_clase','') or ''
            if contenido: story.append(Paragraph(f"Contenido: {contenido}", estilo_small))
            for i in range(1,4):
                txt = reg.get(f'tarea{i}'); ft = reg.get(f'tarea{i}_fecha')
                completada = reg.get(f'tarea{i}_completada', False)
                if txt:
                    ft_fmt = datetime.date.fromisoformat(ft).strftime('%d/%m/%Y') if ft else "-"
                    estado = " [COMPLETADA]" if completada else ""
                    story.append(Paragraph(f"  Tarea {i}: {txt} (entrega: {ft_fmt}){estado}", estilo_small))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc'), spaceAfter=6))
    story.append(Spacer(1,20))
    estilo_footer_pdf = ParagraphStyle('footer', parent=styles['Normal'], fontSize=7, fontName='Helvetica', textColor=colors.HexColor('#aaaaaa'), alignment=TA_CENTER)
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc'), spaceAfter=6))
    story.append(Paragraph("® Sistema diseñado y realizado por Fabián Belledi · 2026", estilo_footer_pdf))
    doc.build(story)
    buffer.seek(0)
    return buffer.read()

def generar_html_impresion(sede, curso_nombre, curso_data, incluir_alumnos, incluir_notas, incluir_historial, incluir_resumen, datos):
    hi = str(curso_data.get('hora_inicio','') or '')[:5]
    hf = str(curso_data.get('hora_fin','') or '')[:5]
    nota_ap = curso_data.get('nota_aprobacion')
    biblio = curso_data.get('bibliografia','')
    alumnos_data = datos.get('alumnos', [])
    notas_data = datos.get('notas', {})
    historial_data = datos.get('historial', [])
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>ClassTrack 360</title>
    <style>body{{font-family:Arial,sans-serif;font-size:11px;color:#111;margin:20px}}
    h1{{color:#1a5276;font-size:20px;margin-bottom:2px}}h2{{color:#1a5276;font-size:14px;border-bottom:2px solid #1a5276;padding-bottom:4px;margin-top:20px}}
    .meta{{color:#666;font-size:10px;margin-bottom:16px}}table{{width:100%;border-collapse:collapse;margin-bottom:16px}}
    th{{background:#1a5276;color:white;padding:6px 8px;text-align:left;font-size:10px}}td{{padding:5px 8px;border-bottom:1px solid #ddd;font-size:10px}}
    tr:nth-child(even){{background:#f5f5f5}}.aprobado{{color:#1a5276;font-weight:bold}}.desaprobado{{color:#c0392b;font-weight:bold}}
    .clase-row{{border-bottom:1px solid #eee;padding:6px 0;margin-bottom:4px}}.clase-fecha{{font-weight:bold;color:#1a5276}}
    .clase-tarea{{color:#555;margin-left:12px}}.tarea-done{{color:#aaa;text-decoration:line-through}}
    .footer-doc{{text-align:center;font-size:9px;color:#aaa;margin-top:30px;padding-top:10px;border-top:1px solid #ddd}}
    @media print{{body{{margin:10px}}}}</style></head><body>
    <h1>ClassTrack 360</h1><div class="meta">Sede: <b>{sede.upper()}</b> · Curso: <b>{curso_nombre}</b>"""
    if hi and hf: html += f" · Horario: <b>{hi} → {hf}</b>"
    if nota_ap: html += f" · Aprobación: <b>{nota_ap}</b>"
    html += f"<br>Generado el {datetime.date.today().strftime('%d/%m/%Y')}</div>"
    if biblio: html += f"<p><b>Bibliografía:</b> {biblio}</p>"
    if incluir_resumen and alumnos_data:
        total = len(alumnos_data); aprobados = 0; promedios = []
        for al in alumnos_data:
            ns = notas_data.get(al['insc_id'], [])
            if ns:
                prom = round(sum(ns)/len(ns), 2); promedios.append(prom)
                if nota_ap and prom >= float(nota_ap): aprobados += 1
        prom_gral = round(sum(promedios)/len(promedios), 2) if promedios else "-"
        porc = f"{round(aprobados/total*100)}%" if total > 0 else "-"
        html += f"""<h2>Resumen del Curso</h2><table><tr><th>Total alumnos</th><th>Con notas</th><th>Aprobados</th><th>% Aprobados</th><th>Promedio general</th></tr>
        <tr><td>{total}</td><td>{len(promedios)}</td><td>{aprobados}</td><td>{porc}</td><td>{prom_gral}</td></tr></table>"""
    if incluir_alumnos and alumnos_data:
        html += "<h2>Listado de Alumnos</h2><table><tr><th>#</th><th>Apellido</th><th>Nombre</th><th>Email</th></tr>"
        for idx, al in enumerate(sorted(alumnos_data, key=lambda x: x['apellido']), 1):
            html += f"<tr><td>{idx}</td><td>{al['apellido'].upper()}</td><td>{al['nombre']}</td><td>{al.get('email','') or '-'}</td></tr>"
        html += "</table>"
    if incluir_notas and alumnos_data:
        html += "<h2>Notas y Promedios</h2><table><tr><th>Alumno</th><th>Nota 1</th><th>Nota 2</th><th>Nota 3</th><th>Nota 4</th><th>Nota 5</th><th>Promedio</th><th>Estado</th></tr>"
        for al in sorted(alumnos_data, key=lambda x: x['apellido']):
            ns = notas_data.get(al['insc_id'], [])
            celdas = "".join([f"<td>{ns[i] if i < len(ns) else '-'}</td>" for i in range(5)])
            if ns:
                prom = round(sum(ns)/len(ns), 2); est = estado_texto(prom, nota_ap)
                clase = "aprobado" if est == "APROBADO" else "desaprobado"
                html += f"<tr><td>{al['apellido'].upper()}, {al['nombre']}</td>{celdas}<td>{prom}</td><td class='{clase}'>{est}</td></tr>"
            else:
                html += f"<tr><td>{al['apellido'].upper()}, {al['nombre']}</td>{celdas}<td>-</td><td>Sin notas</td></tr>"
        html += "</table>"
    if incluir_historial and historial_data:
        html += "<h2>Historial de Clases</h2>"
        for reg in sorted(historial_data, key=lambda x: x['fecha']):
            fecha_fmt = datetime.date.fromisoformat(reg['fecha']).strftime('%d/%m/%Y')
            suplente = reg.get('profesor_suplente')
            prof = f"Suplente: {suplente}" if suplente else "Titular"
            html += f"<div class='clase-row'><span class='clase-fecha'>{fecha_fmt}</span> · {prof}"
            contenido = reg.get('contenido_clase','') or ''
            if contenido: html += f"<br><span style='color:#333'>{contenido}</span>"
            for i in range(1,4):
                txt = reg.get(f'tarea{i}'); ft = reg.get(f'tarea{i}_fecha')
                completada = reg.get(f'tarea{i}_completada', False)
                if txt:
                    ft_fmt = datetime.date.fromisoformat(ft).strftime('%d/%m/%Y') if ft else "-"
                    clase_done = " tarea-done" if completada else ""
                    html += f"<div class='clase-tarea{clase_done}'>Tarea {i}: {txt} (entrega: {ft_fmt})</div>"
            html += "</div>"
    html += "<div class='footer-doc'>® Sistema diseñado y realizado por Fabián Belledi · 2026</div>"
    html += "<script>window.onload=function(){window.print();}</script></body></html>"
    return html

def cargar_datos_por_nombre_curso(nombre_curso, inscripcion_id):
    alumnos = []; notas_dict = {}; historial = []
    try:
        res_al = supabase.table("inscripciones").select("id, alumnos(nombre, apellido, email)").eq("nombre_curso_materia", nombre_curso).not_.is_("alumno_id", "null").execute()
        for r in (res_al.data or []):
            al_raw = r.get('alumnos')
            al = al_raw[0] if isinstance(al_raw, list) and al_raw else al_raw
            if al:
                alumnos.append({'insc_id': r['id'], 'nombre': al.get('nombre',''), 'apellido': al.get('apellido',''), 'email': al.get('email','') or ''})
                res_n = supabase.table("notas").select("calificacion").eq("inscripcion_id", r['id']).order("created_at").execute()
                notas_dict[r['id']] = [float(n['calificacion']) for n in (res_n.data or [])]
    except: pass
    try:
        res_h = supabase.table("bitacora").select("*").eq("inscripcion_id", inscripcion_id).order("fecha").execute()
        historial = res_h.data or []
    except: pass
    return {'alumnos': alumnos, 'notas': notas_dict, 'historial': historial}

def render_seccion_calendario(sede, es_admin=False):
    cal = get_calendario_sede(sede)
    fecha_inicio = datetime.date.fromisoformat(cal['fecha_inicio']) if cal and cal.get('fecha_inicio') else None
    fecha_fin = datetime.date.fromisoformat(cal['fecha_fin']) if cal and cal.get('fecha_fin') else None
    if fecha_inicio and fecha_fin:
        hoy = datetime.date.today()
        total_dias = (fecha_fin - fecha_inicio).days
        dias_transcurridos = max(0, (hoy - fecha_inicio).days)
        dias_restantes = max(0, (fecha_fin - hoy).days)
        st.markdown(f'''<div class="calendario-box">
            <div class="cal-header">📆 Año Lectivo {fecha_inicio.year}</div>
            <div class="cal-fechas">🟢 Inicio: <b>{fecha_inicio.strftime("%d/%m/%Y")}</b> &nbsp;·&nbsp; 🔴 Fin: <b>{fecha_fin.strftime("%d/%m/%Y")}</b></div>
            <div class="cal-dias">Total: {total_dias} días · Transcurridos: {dias_transcurridos} · Restantes: {dias_restantes}</div>
        </div>''', unsafe_allow_html=True)
    else:
        st.markdown('<div class="calendario-box"><div class="cal-header">📆 Año Lectivo</div><div class="cal-fechas" style="color:#556">Sin fechas configuradas aún.</div></div>', unsafe_allow_html=True)
    if cal:
        url_1c = cal.get('cronograma_1c_url')
        nombre_1c = cal.get('cronograma_1c_nombre')
        url_2c = cal.get('cronograma_2c_url')
        nombre_2c = cal.get('cronograma_2c_nombre')
        if url_1c: render_cronograma_visor(url_1c, nombre_1c, "Cronograma 1° Cuatrimestre")
        if url_2c: render_cronograma_visor(url_2c, nombre_2c, "Cronograma 2° Cuatrimestre")
    with st.expander("✏️ Editar calendario y cronogramas", expanded=not fecha_inicio):
        with st.form(f"cal_form_{sede}"):
            col1, col2 = st.columns(2)
            fi = col1.date_input("Fecha de inicio del año lectivo:",
                value=fecha_inicio if fecha_inicio else datetime.date(datetime.date.today().year, 3, 1))
            ff = col2.date_input("Fecha de fin del año lectivo:",
                value=fecha_fin if fecha_fin else datetime.date(datetime.date.today().year, 11, 30))
            st.markdown("**📁 Subir cronograma 1° Cuatrimestre** (PDF, JPG, PNG, Excel, Word)")
            arch_1c = st.file_uploader("Cronograma 1C:", type=['pdf','jpg','jpeg','png','gif','webp','xlsx','xls','docx','doc'], key=f"arch1c_{sede}")
            st.markdown("**📁 Subir cronograma 2° Cuatrimestre** (PDF, JPG, PNG, Excel, Word)")
            arch_2c = st.file_uploader("Cronograma 2C:", type=['pdf','jpg','jpeg','png','gif','webp','xlsx','xls','docx','doc'], key=f"arch2c_{sede}")
            if st.form_submit_button("💾 Guardar", use_container_width=True):
                if fi >= ff:
                    st.error("La fecha de inicio debe ser anterior a la fecha de fin.")
                else:
                    ok = upsert_calendario_sede(sede, fi, ff)
                    if ok:
                        if arch_1c: subir_cronograma(sede, 1, arch_1c)
                        if arch_2c: subir_cronograma(sede, 2, arch_2c)
                        st.success("✅ Calendario actualizado correctamente.")
                        st.rerun()

# ============================================================
# FIN PARTE 1 DE 2 — Continuá pegando desde aquí en Parte 2
# ============================================================
# ============================================================
# INICIO PARTE 2 DE 2 — Pegá esto a continuación de Parte 1
# ============================================================

# =========================================================
# --- LOGIN Y REGISTRO ---
# =========================================================
if st.session_state.user is None:
    _, col, _ = st.columns([1.5, 1, 1.5])
    with col:
        if st.session_state.pantalla_login == 'registro':
            st.markdown("""<div class="login-box">
                <div class="login-logo">Class<span>Track</span> 360</div>
                <div class="login-eyebrow">// Crear cuenta nueva</div>
                <div class="login-title">Registro</div></div>""", unsafe_allow_html=True)
            with st.form("registro", clear_on_submit=False):
                codigo_input = st.text_input("Código de invitación *", placeholder="Ej: AB12CD34")
                sede_input_r = st.text_input("Nombre de sede *", placeholder="Ej: quilmes")
                nombre_input = st.text_input("Tu nombre completo *", placeholder="Ej: García, María")
                clave1 = st.text_input("Contraseña *", type="password")
                clave2 = st.text_input("Repetir contraseña *", type="password")
                submitted_r = st.form_submit_button("✅ CREAR CUENTA", use_container_width=True)
                if submitted_r:
                    errores = []
                    if not codigo_input.strip(): errores.append("El código de invitación es obligatorio.")
                    if not sede_input_r.strip(): errores.append("El nombre de sede es obligatorio.")
                    if not nombre_input.strip(): errores.append("Tu nombre es obligatorio.")
                    if not clave1.strip(): errores.append("La contraseña es obligatoria.")
                    elif clave1 != clave2: errores.append("Las contraseñas no coinciden.")
                    elif len(clave1) < 6: errores.append("La contraseña debe tener al menos 6 caracteres.")
                    if errores:
                        for e in errores: st.error(e)
                    else:
                        try:
                            res_cod = supabase.table("codigos_invitacion").select("*").eq("codigo", codigo_input.strip().upper()).eq("usado", False).execute()
                            if not res_cod.data:
                                st.error("Código inválido o ya utilizado.")
                            else:
                                cod = res_cod.data[0]
                                sede_norm = sede_input_r.strip().lower()
                                res_sede = supabase.table("usuarios").select("id").eq("sede", sede_norm).execute()
                                if res_sede.data:
                                    st.error(f"La sede '{sede_norm}' ya está registrada. Elegí otro nombre.")
                                else:
                                    supabase.table("usuarios").insert({
                                        "sede": sede_norm, "nombre": nombre_input.strip(),
                                        "password_text": clave1, "habilitado": True,
                                        "tipo_cuenta": cod.get('tipo_cuenta', 'permanente')
                                    }).execute()
                                    supabase.table("codigos_invitacion").update({
                                        "usado": True, "usado_por": sede_norm
                                    }).eq("id", cod['id']).execute()
                                    st.success(f"✅ Cuenta creada. Ya podés iniciar sesión con la sede '{sede_norm}'.")
                                    st.session_state.pantalla_login = 'login'
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            if st.button("← Volver al inicio de sesión", use_container_width=True):
                st.session_state.pantalla_login = 'login'
                st.rerun()
            st.markdown('<div class="login-footer">© 2026 ClassTrack 360 · v288</div>', unsafe_allow_html=True)
        else:
            st.markdown("""<div class="login-box">
                <div class="login-logo">Class<span>Track</span> 360</div>
                <div class="login-eyebrow">// Acceso al sistema</div>
                <div class="login-title">Iniciar sesión</div></div>""", unsafe_allow_html=True)
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
                            u = res.data[0]
                            if u.get('habilitado') == False:
                                st.error("Tu cuenta está deshabilitada. Contactá al administrador.")
                            else:
                                st.session_state.user = u
                                st.rerun()
                        else:
                            st.error("Sede o clave incorrectos.")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")
            st.markdown('<div class="registro-link">¿Primera vez? Si tenés un código de invitación podés crear tu cuenta.</div>', unsafe_allow_html=True)
            if st.button("➕ Crear cuenta nueva", use_container_width=True):
                st.session_state.pantalla_login = 'registro'
                st.rerun()
            st.markdown('<div class="login-footer">© 2026 ClassTrack 360 · v288</div>', unsafe_allow_html=True)
    footer()

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
            opciones_sede = ["— Todas las sedes —"] + sedes_disponibles
            sede_sel = st.selectbox("Ver sede:", opciones_sede, key="admin_sede_sel")
            st.session_state.sede_admin = None if sede_sel == "— Todas las sedes —" else sede_sel
        else:
            st.warning("No hay sedes registradas.")
            sedes_disponibles = []
        st.markdown("---")
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.session_state.sede_admin = None
            st.rerun()

    st.markdown('<div class="admin-badge">⚡ Panel de Administración</div>', unsafe_allow_html=True)
    st.title("ClassTrack 360 · Admin")
    footer()

    admin_tabs = st.tabs(["👥 Profesores", "🔑 Códigos de Invitación", "📊 Resumen", "📝 Notas", "📆 Calendarios", "🗑️ Reset de Datos"])

    with admin_tabs[0]:
        st.subheader("👥 Gestión de Profesores")
        try:
            res_profs = supabase.table("usuarios").select("*").neq("sede", "admin").execute()
            profs = res_profs.data or []
            if not profs:
                no_encontrado("No hay profesores registrados.")
            else:
                for prof in profs:
                    habilitado = prof.get('habilitado', True)
                    tipo = prof.get('tipo_cuenta', 'permanente')
                    tag_hab = '<span class="habilitado-tag">✅ HABILITADO</span>' if habilitado else '<span class="deshabilitado-tag">🚫 DESHABILITADO</span>'
                    tag_tipo = f'<span style="color:#aaa;font-size:0.75rem">{tipo.upper()}</span>'
                    st.markdown(f'<div class="planilla-row"><b>{prof.get("sede","").upper()}</b> · {prof.get("nombre","Sin nombre")} &nbsp; {tag_hab} &nbsp; {tag_tipo}</div>', unsafe_allow_html=True)
                    col_h, col_t, col_d = st.columns(3)
                    if habilitado:
                        if col_h.button("🚫 Deshabilitar", key=f"desh_{prof['id']}"):
                            supabase.table("usuarios").update({"habilitado": False}).eq("id", prof['id']).execute()
                            st.success(f"Profesor {prof.get('sede','').upper()} deshabilitado."); st.rerun()
                    else:
                        if col_h.button("✅ Habilitar", key=f"hab_{prof['id']}"):
                            supabase.table("usuarios").update({"habilitado": True}).eq("id", prof['id']).execute()
                            st.success(f"Profesor {prof.get('sede','').upper()} habilitado."); st.rerun()
                    if tipo == 'provisorio':
                        if col_t.button("⬆️ Hacer Permanente", key=f"perm_{prof['id']}"):
                            supabase.table("usuarios").update({"tipo_cuenta": "permanente"}).eq("id", prof['id']).execute()
                            st.success(f"Cuenta de {prof.get('sede','').upper()} cambiada a Permanente."); st.rerun()
                    else:
                        col_t.caption("Cuenta permanente")
                    if col_d.button("🗑️ Eliminar cuenta", key=f"del_prof_{prof['id']}"):
                        st.session_state[f'confirm_del_{prof["id"]}'] = True; st.rerun()
                    if st.session_state.get(f'confirm_del_{prof["id"]}'):
                        st.warning(f"⚠️ ¿Confirmar eliminación de la cuenta {prof.get('sede','').upper()}?")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Confirmar", key=f"conf_del_{prof['id']}"):
                            supabase.table("usuarios").delete().eq("id", prof['id']).execute()
                            st.session_state[f'confirm_del_{prof["id"]}'] = False
                            st.success("Cuenta eliminada."); st.rerun()
                        if c2.button("❌ Cancelar", key=f"canc_del_{prof['id']}"):
                            st.session_state[f'confirm_del_{prof["id"]}'] = False; st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    with admin_tabs[1]:
        st.subheader("🔑 Códigos de Invitación")
        col_g1, col_g2 = st.columns([2, 1])
        tipo_nuevo = col_g1.selectbox("Tipo de cuenta:", ["permanente", "provisorio"], key="tipo_cod")
        if col_g2.button("➕ Generar Código", use_container_width=True):
            nuevo_codigo = generar_codigo()
            try:
                supabase.table("codigos_invitacion").insert({"codigo": nuevo_codigo, "tipo_cuenta": tipo_nuevo}).execute()
                st.markdown(f'<div class="codigo-box">🔑 {nuevo_codigo}</div>', unsafe_allow_html=True)
                st.success(f"Código generado. Tipo: {tipo_nuevo.upper()}"); st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        st.markdown("---")
        try:
            res_cod = supabase.table("codigos_invitacion").select("*").order("created_at", desc=True).execute()
            codigos = res_cod.data or []
            if not codigos:
                no_encontrado("No hay códigos generados aún.")
            else:
                disponibles = [c for c in codigos if not c.get('usado')]
                usados = [c for c in codigos if c.get('usado')]
                st.caption(f"Disponibles: {len(disponibles)} · Usados: {len(usados)}")
                for cod in codigos:
                    usado = cod.get('usado', False)
                    tipo = cod.get('tipo_cuenta', 'permanente')
                    usado_por = cod.get('usado_por', '')
                    estado_color = "#555" if usado else "#4facfe"
                    estado_txt = f"✅ Usado por: {usado_por}" if usado else "🟢 Disponible"
                    col_a, col_b, col_c = st.columns([2, 2, 1])
                    col_a.markdown(f'<span style="font-family:monospace;font-size:1rem;color:{estado_color};font-weight:700">{cod["codigo"]}</span>', unsafe_allow_html=True)
                    col_b.markdown(f'<span style="font-size:0.8rem;color:#aaa">{tipo.upper()} · {estado_txt}</span>', unsafe_allow_html=True)
                    if not usado:
                        if col_c.button("🗑️", key=f"del_cod_{cod['id']}"):
                            supabase.table("codigos_invitacion").delete().eq("id", cod['id']).execute(); st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    with admin_tabs[2]:
        sedes_a_mostrar = sedes_disponibles if not st.session_state.sede_admin else [st.session_state.sede_admin]
        st.subheader("📊 Resumen General" if not st.session_state.sede_admin else f"📊 Resumen — {st.session_state.sede_admin.upper()}")
        for sede_activa in sedes_a_mostrar:
            try:
                res_u = supabase.table("usuarios").select("id, nombre").eq("sede", sede_activa).execute()
                if res_u.data:
                    prof_id = res_u.data[0]['id']
                    res_cursos = supabase.table("inscripciones").select("nombre_curso_materia, hora_inicio, hora_fin").eq("profesor_id", prof_id).is_("alumno_id", "null").execute()
                    res_alumnos = supabase.table("inscripciones").select("id").eq("profesor_id", prof_id).not_.is_("alumno_id", "null").execute()
                    cant_cursos = len(res_cursos.data) if res_cursos.data else 0
                    cant_alumnos = len(res_alumnos.data) if res_alumnos.data else 0
                    with st.expander(f"🏫 {sede_activa.upper()} · {cant_cursos} cursos · {cant_alumnos} alumnos", expanded=len(sedes_a_mostrar) == 1):
                        col1, col2 = st.columns(2)
                        col1.metric("Cursos", cant_cursos)
                        col2.metric("Alumnos", cant_alumnos)
                        if res_cursos.data:
                            for c in res_cursos.data:
                                st.markdown(f'<div class="planilla-row">📖 {c["nombre_curso_materia"]}<br><small style="color:#4facfe;">🕐 {format_horario(c.get("hora_inicio",""), c.get("hora_fin",""))}</small></div>', unsafe_allow_html=True)
                        else:
                            no_encontrado("No hay cursos registrados.")
            except Exception as e:
                st.error(f"Error en sede {sede_activa}: {e}")

    with admin_tabs[3]:
        st.subheader("📝 Notas")
        sedes_a_mostrar_n = sedes_disponibles if not st.session_state.sede_admin else [st.session_state.sede_admin]
        sede_sel_notas = st.selectbox("Sede:", sedes_a_mostrar_n, key="admin_notas_sede") if len(sedes_a_mostrar_n) > 1 else (sedes_a_mostrar_n[0] if sedes_a_mostrar_n else None)
        if sede_sel_notas:
            try:
                res_u = supabase.table("usuarios").select("id").eq("sede", sede_sel_notas).execute()
                if res_u.data:
                    prof_id = res_u.data[0]['id']
                    res_cursos = supabase.table("inscripciones").select("nombre_curso_materia").eq("profesor_id", prof_id).is_("alumno_id", "null").execute()
                    if res_cursos.data:
                        curso_sel = st.selectbox("Curso:", ["---"] + [c['nombre_curso_materia'] for c in res_cursos.data])
                        if curso_sel != "---":
                            res_cur_data = supabase.table("inscripciones").select("nota_aprobacion").eq("nombre_curso_materia", curso_sel).is_("alumno_id", "null").limit(1).execute()
                            nota_ap_admin = res_cur_data.data[0].get('nota_aprobacion') if res_cur_data.data else None
                            res_al = supabase.table("inscripciones").select("id, alumnos(nombre, apellido, email)").eq("nombre_curso_materia", curso_sel).not_.is_("alumno_id", "null").execute()
                            if res_al.data:
                                for r in res_al.data:
                                    al_raw = r.get('alumnos')
                                    al = al_raw[0] if isinstance(al_raw, list) and al_raw else al_raw
                                    if al:
                                        res_notas = supabase.table("notas").select("id, calificacion, created_at").eq("inscripcion_id", r['id']).order("created_at", desc=False).execute()
                                        notas = res_notas.data if res_notas.data else []
                                        filas_html = ""; valores = []
                                        for i, nt in enumerate(notas):
                                            val = float(nt['calificacion']); valores.append(val)
                                            fecha_fmt = datetime.datetime.fromisoformat(nt['created_at'][:10]).strftime('%d/%m/%Y')
                                            filas_html += f'<div class="nota-linea"><span>Nota {i+1} · {fecha_fmt}</span><span class="nota-badge {color_nota(val)}">{val}</span></div>'
                                        if not filas_html:
                                            filas_html = '<div class="nota-linea"><span style="color:#555">Sin notas</span></div>'
                                            promedio_html = estado_html = ""
                                        else:
                                            promedio = round(sum(valores)/len(valores), 2)
                                            promedio_html = f'<div class="promedio-linea"><span>Promedio</span><span class="nota-badge {color_nota(promedio)}">{promedio}</span></div>'
                                            estado_html = estado_aprobacion(promedio, nota_ap_admin)
                                        email_html = f'<div class="email-tag">✉️ {al.get("email","")}</div>' if al.get("email") else ""
                                        st.markdown(f'<div class="alumno-block"><div class="nombre">👤 {al.get("apellido","").upper()}, {al.get("nombre","")} {estado_html if valores else ""}</div>{email_html}{filas_html}{promedio_html if valores else ""}</div>', unsafe_allow_html=True)
                            else:
                                no_encontrado("No hay alumnos inscriptos en este curso.")
                    else:
                        no_encontrado("No hay cursos registrados.")
            except Exception as e:
                st.error(f"Error: {e}")

    with admin_tabs[4]:
        st.subheader("📆 Calendarios por Sede")
        sedes_cal = sedes_disponibles if not st.session_state.sede_admin else [st.session_state.sede_admin]
        if not sedes_cal:
            no_encontrado("No hay sedes registradas.")
        elif st.session_state.sede_admin:
            render_seccion_calendario(st.session_state.sede_admin, es_admin=True)
        else:
            sede_cal_sel = st.selectbox("Seleccionar sede:", sedes_cal, key="admin_cal_sede")
            render_seccion_calendario(sede_cal_sel, es_admin=True)

    with admin_tabs[5]:
        st.subheader("🗑️ Reset de Datos")
        st.markdown('<div class="reset-box"><div class="reset-titulo">⚠️ Zona de Peligro</div>Esta acción borrará TODOS los datos de la sede seleccionada. El usuario NO será eliminado.</div>', unsafe_allow_html=True)
        st.markdown("---")
        if sedes_disponibles:
            sede_reset = st.selectbox("Sede a resetear:", sedes_disponibles, key="reset_sede_sel")
            if st.session_state.confirmar_reset != sede_reset:
                if st.button(f"🔴 BORRAR TODOS LOS DATOS DE {sede_reset.upper()}", type="primary"):
                    st.session_state.confirmar_reset = sede_reset; st.rerun()
            else:
                st.markdown(f'<div class="advertencia-box">⚠️ <b>ADVERTENCIA FINAL</b><br><br>Estás a punto de borrar TODOS los datos de <b>{sede_reset.upper()}</b>. Esta acción es <b>irreversible</b>.</div>', unsafe_allow_html=True)
                col_si, col_no = st.columns(2)
                if col_si.button("✅ SÍ, BORRAR TODO", type="primary", use_container_width=True):
                    ok, msg = reset_completo_sede(sede_reset)
                    if ok:
                        st.success(f"✅ {msg}"); st.session_state.confirmar_reset = None; st.rerun()
                    else:
                        st.error(f"Error: {msg}")
                if col_no.button("❌ NO, CANCELAR", use_container_width=True):
                    st.session_state.confirmar_reset = None; st.rerun()

# =========================================================
# --- APP NORMAL ---
# =========================================================
else:
    u_data = st.session_state.user
    f_hoy = datetime.date.today()

    total_vencidas_sidebar = get_tareas_vencidas_count(u_data['id'])
    total_clases_sidebar = get_total_clases_sidebar(u_data['id'])  # v288

    with st.sidebar:
        st.header(f"Sede: {u_data['sede'].upper()}")
        st.write(f"📅 {f_hoy.strftime('%d/%m/%Y')}")
        components.html("""<div style="color:#4facfe;font-family:monospace;font-size:24px;text-align:center;"><div id="c">00:00:00</div></div><script>setInterval(()=>{document.getElementById('c').innerText=new Date().toLocaleTimeString('es-AR',{hour12:false})},1000);</script>""", height=50)
        try:
            res_total = supabase.table("inscripciones").select("id").eq("profesor_id", u_data['id']).eq("anio_lectivo", 2026).not_.is_("alumno_id", "null").execute()
            st.markdown(f'<div class="stat-card">Total Alumnos 2026: <b>{len(res_total.data)}</b></div>', unsafe_allow_html=True)
        except:
            st.markdown('<div class="stat-card">Total Alumnos 2026: <b>-</b></div>', unsafe_allow_html=True)
        # v288: contador de clases en sidebar
        if total_clases_sidebar > 0:
            st.markdown(f'<div class="badge-clases">🔢 {total_clases_sidebar} clase{"s" if total_clases_sidebar != 1 else ""} dictada{"s" if total_clases_sidebar != 1 else ""}</div>', unsafe_allow_html=True)
        if total_vencidas_sidebar > 0:
            st.markdown(f'<div class="badge-vencidas">⚠️ {total_vencidas_sidebar} tarea{"s" if total_vencidas_sidebar > 1 else ""} vencida{"s" if total_vencidas_sidebar > 1 else ""}</div>', unsafe_allow_html=True)
        cal_sede = get_calendario_sede(u_data['sede'])
        if cal_sede and cal_sede.get('fecha_inicio') and cal_sede.get('fecha_fin'):
            fi_s = datetime.date.fromisoformat(cal_sede['fecha_inicio'])
            ff_s = datetime.date.fromisoformat(cal_sede['fecha_fin'])
            dias_r = max(0, (ff_s - f_hoy).days)
            st.markdown(f'<div class="stat-card" style="font-size:0.72rem;">📆 Año lectivo<br><b>{fi_s.strftime("%d/%m")}</b> → <b>{ff_s.strftime("%d/%m")}</b><br>{dias_r} días restantes</div>', unsafe_allow_html=True)
        st.markdown("---")
        col_prev, col_next = st.columns(2)
        if col_prev.button("◀", key="cal_prev"):
            if st.session_state.cal_mes == 1: st.session_state.cal_mes = 12; st.session_state.cal_anio -= 1
            else: st.session_state.cal_mes -= 1
            st.rerun()
        if col_next.button("▶", key="cal_next"):
            if st.session_state.cal_mes == 12: st.session_state.cal_mes = 1; st.session_state.cal_anio += 1
            else: st.session_state.cal_mes += 1
            st.rerun()
        st.markdown(render_calendario(st.session_state.cal_mes, st.session_state.cal_anio), unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🚪 SALIR"):
            st.session_state.user = None
            st.rerun()

    footer()

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

    # v288: tab Calendario con año dinámico
    tabs = st.tabs([
        "📅 Agenda",
        "📋 Historial de Clases",
        "👥 Alumnos",
        "📝 Notas",
        "🔢 Contador de Clases",
        "🏗️ Cursos",
        f"📆 Calendario Académico {ANIO_ACTUAL}",
        "🖨️ Impresión"
    ])

    # =========================================================
    # TAB 0 — AGENDA
    # =========================================================
    with tabs[0]:
        if not mapa_cursos:
            no_encontrado("No tenés cursos creados. Andá a la pestaña 🏗️ Cursos para crear uno.")
        else:
            c_ag = st.selectbox("Seleccione Curso:", list(mapa_cursos.keys()), key="ag_sel")
            inscripcion_id = mapa_cursos[c_ag]
            curso_sel_data = mapa_cursos_data.get(c_ag, {})
            hi = str(curso_sel_data.get('hora_inicio', '') or '')[:5]
            hf = str(curso_sel_data.get('hora_fin', '') or '')[:5]
            if hi and hf: st.caption(f"🕐 Horario: {format_horario(hi, hf)}")

            proxima = get_proxima_clase(c_ag, hi, hf)
            if proxima:
                dias_txt = "mañana" if proxima['dias_faltan'] == 1 else f"en {proxima['dias_faltan']} días"
                st.markdown(f'''<div class="proxima-clase-card">
                    <div class="pc-titulo">📅 PRÓXIMA CLASE</div>
                    <div class="pc-fecha">{proxima["fecha_fmt"]}</div>
                    <div class="pc-detalle">🕐 {proxima["horario"]} &nbsp;·&nbsp; {dias_txt}</div>
                </div>''', unsafe_allow_html=True)

            try:
                res_tareas_pend = supabase.table("bitacora").select(
                    "id, fecha, tarea1, tarea1_fecha, tarea1_completada, tarea2, tarea2_fecha, tarea2_completada, tarea3, tarea3_fecha, tarea3_completada"
                ).eq("inscripcion_id", inscripcion_id).execute()
                tareas_vencidas = []
                tareas_pendientes = []
                for reg in (res_tareas_pend.data or []):
                    for i in range(1, 4):
                        txt = reg.get(f'tarea{i}')
                        fecha_t = reg.get(f'tarea{i}_fecha')
                        completada = reg.get(f'tarea{i}_completada', False)
                        if txt and not completada:
                            item = {'bit_id': reg['id'], 'num': i, 'texto': txt, 'fecha': fecha_t, 'clase_fecha': reg['fecha']}
                            if fecha_t and datetime.date.fromisoformat(fecha_t) < f_hoy:
                                tareas_vencidas.append(item)
                            else:
                                tareas_pendientes.append(item)

                if tareas_vencidas:
                    st.markdown(f'<div class="vencidas-header">⚠️ {len(tareas_vencidas)} TAREA{"S" if len(tareas_vencidas) > 1 else ""} VENCIDA{"S" if len(tareas_vencidas) > 1 else ""} — FECHA DE ENTREGA PASADA</div>', unsafe_allow_html=True)
                    for tp in tareas_vencidas:
                        fecha_fmt = datetime.date.fromisoformat(tp['fecha']).strftime('%d/%m/%Y') if tp['fecha'] else "-"
                        clase_fmt = datetime.date.fromisoformat(tp['clase_fecha']).strftime('%d/%m/%Y') if tp['clase_fecha'] else "-"
                        key_edit = f"{tp['bit_id']}_{tp['num']}"
                        if st.session_state.editando_tarea == key_edit:
                            with st.form(f"edit_tarea_v_{key_edit}"):
                                st.markdown(f"**✏️ Editando Tarea {tp['num']} · Clase del {clase_fmt}**")
                                nuevo_texto = st.text_area("Descripción:", value=tp['texto'], key=f"etv_txt_{key_edit}")
                                nueva_fecha = st.date_input("Nueva fecha de entrega:", value=f_hoy, key=f"etv_fch_{key_edit}")
                                col_g, col_c = st.columns(2)
                                if col_g.form_submit_button("💾 Guardar"):
                                    guardar_edicion_tarea(tp['bit_id'], tp['num'], nuevo_texto, nueva_fecha)
                                if col_c.form_submit_button("❌ Cancelar"):
                                    st.session_state.editando_tarea = None; st.rerun()
                        else:
                            col_t, col_b1, col_b2 = st.columns([5, 1, 1])
                            with col_t:
                                st.markdown(f'''<div class="tarea-card-vencida">
                                    <div class="tarea-titulo">⚠️ VENCIDA · Tarea {tp["num"]} · Clase del {clase_fmt}</div>
                                    <div class="tarea-texto">{tp["texto"]}</div>
                                    <div class="tarea-fecha">📅 Vencida el: {fecha_fmt}</div>
                                </div>''', unsafe_allow_html=True)
                            with col_b1:
                                st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                                if st.button("✅ Hecha", key=f"comp_v_{tp['bit_id']}_{tp['num']}"):
                                    marcar_tarea(tp['bit_id'], tp['num'], True)
                            with col_b2:
                                st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                                if st.button("✏️ Editar", key=f"edit_v_{tp['bit_id']}_{tp['num']}"):
                                    st.session_state.editando_tarea = key_edit; st.rerun()

                if tareas_pendientes:
                    st.markdown('<div class="tareas-pendientes-header">📌 TAREAS PENDIENTES DE ESTE CURSO:</div>', unsafe_allow_html=True)
                    for tp in tareas_pendientes:
                        fecha_fmt = datetime.date.fromisoformat(tp['fecha']).strftime('%d/%m/%Y') if tp['fecha'] else "-"
                        clase_fmt = datetime.date.fromisoformat(tp['clase_fecha']).strftime('%d/%m/%Y') if tp['clase_fecha'] else "-"
                        key_edit = f"{tp['bit_id']}_{tp['num']}"
                        if st.session_state.editando_tarea == key_edit:
                            with st.form(f"edit_tarea_{key_edit}"):
                                st.markdown(f"**✏️ Editando Tarea {tp['num']} · Clase del {clase_fmt}**")
                                nuevo_texto = st.text_area("Descripción:", value=tp['texto'], key=f"et_txt_{key_edit}")
                                nueva_fecha = st.date_input("Fecha de entrega:", value=datetime.date.fromisoformat(tp['fecha']) if tp['fecha'] else f_hoy, key=f"et_fch_{key_edit}")
                                col_g, col_c = st.columns(2)
                                if col_g.form_submit_button("💾 Guardar"):
                                    guardar_edicion_tarea(tp['bit_id'], tp['num'], nuevo_texto, nueva_fecha)
                                if col_c.form_submit_button("❌ Cancelar"):
                                    st.session_state.editando_tarea = None; st.rerun()
                        else:
                            col_t, col_b1, col_b2 = st.columns([5, 1, 1])
                            with col_t:
                                st.markdown(f'''<div class="tarea-card">
                                    <div class="tarea-titulo">Tarea {tp["num"]} · Clase del {clase_fmt}</div>
                                    <div class="tarea-texto">{tp["texto"]}</div>
                                    <div class="tarea-fecha">📅 Entrega: {fecha_fmt}</div>
                                </div>''', unsafe_allow_html=True)
                            with col_b1:
                                st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                                if st.button("✅ Hecha", key=f"comp_{tp['bit_id']}_{tp['num']}"):
                                    marcar_tarea(tp['bit_id'], tp['num'], True)
                            with col_b2:
                                st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                                if st.button("✏️ Editar", key=f"edit_tp_{tp['bit_id']}_{tp['num']}"):
                                    st.session_state.editando_tarea = key_edit; st.rerun()

            except Exception as e:
                st.error(f"Error al cargar tareas: {e}")

            try:
                res_t = supabase.table("bitacora").select(
                    "id, tarea_proxima, fecha, tarea_proxima_completada"
                ).eq("inscripcion_id", inscripcion_id).not_.is_("tarea_proxima", "null").order("fecha", desc=True).limit(1).execute()
                if res_t.data:
                    reg_legacy = res_t.data[0]
                    tarea_txt = reg_legacy.get('tarea_proxima', '')
                    tarea_fecha = reg_legacy.get('fecha', '')
                    completada_legacy = reg_legacy.get('tarea_proxima_completada', False)
                    if tarea_txt and not completada_legacy:
                        if st.session_state.editando_tarea_legacy == reg_legacy['id']:
                            with st.form(f"edit_legacy_{reg_legacy['id']}"):
                                st.markdown(f"**✏️ Editando tarea de la clase del {tarea_fecha}**")
                                nuevo_txt_legacy = st.text_area("Descripción:", value=tarea_txt, key=f"etl_txt_{reg_legacy['id']}")
                                col_gl, col_cl = st.columns(2)
                                if col_gl.form_submit_button("💾 Guardar"):
                                    guardar_edicion_tarea_legacy(reg_legacy['id'], nuevo_txt_legacy)
                                if col_cl.form_submit_button("❌ Cancelar"):
                                    st.session_state.editando_tarea_legacy = None; st.rerun()
                        else:
                            st.markdown(f'''<div class="tarea-alerta">
                                🔔 TAREA PENDIENTE DE LA CLASE ANTERIOR ({tarea_fecha})<br>
                                <div style="margin-top:10px;border-top:1px solid #ffc107;padding-top:10px;color:#fff;font-weight:400;font-size:1rem;">{tarea_txt}</div>
                            </div>''', unsafe_allow_html=True)
                            col_l1, col_l2 = st.columns(2)
                            if col_l1.button("✅ Marcar como hecha", key=f"legacy_done_{reg_legacy['id']}"):
                                marcar_tarea_proxima(reg_legacy['id'], True)
                            if col_l2.button("✏️ Editar tarea", key=f"legacy_edit_{reg_legacy['id']}"):
                                st.session_state.editando_tarea_legacy = reg_legacy['id']; st.rerun()
            except Exception as e:
                st.error(f"Error al cargar tarea legacy: {e}")

            st.markdown("---")
            st.subheader("📝 Registrar Clase de Hoy")
            try:
                res_hoy = supabase.table("bitacora").select("id").eq("inscripcion_id", inscripcion_id).eq("fecha", str(f_hoy)).execute()
                ya_guardado_hoy = len(res_hoy.data) > 0
            except:
                ya_guardado_hoy = False
            if ya_guardado_hoy:
                st.warning("⚠️ Ya existe un registro para HOY en este curso. Podés editarlo desde la pestaña 📋 Historial de Clases.")
            else:
                col_tit, col_sup = st.columns([3, 1])
                with col_tit:
                    if st.session_state.es_suplente:
                        st.markdown('<span class="suplente-badge">⚠️ Registrando clase como SUPLENTE</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="titular-badge">👤 Clase dictada por TITULAR</span>', unsafe_allow_html=True)
                with col_sup:
                    if not st.session_state.es_suplente:
                        if st.button("👥 Dictada por suplente", key="btn_suplente"):
                            st.session_state.es_suplente = True; st.rerun()
                    else:
                        if st.button("👤 Volver a titular", key="btn_titular"):
                            st.session_state.es_suplente = False; st.rerun()
                suplente_nombre = ""
                if st.session_state.es_suplente:
                    suplente_nombre = st.text_input("Apellido y Nombre del profesor suplente:", placeholder="Ej: García, María")
                with st.form("f_agenda"):
                    temas = st.text_area("Contenido dictado hoy")
                    st.markdown("---")
                    st.markdown("**📌 Tareas** (podés completar hasta 3, ninguna es obligatoria)")
                    col_t1, col_t2, col_t3 = st.columns(3)
                    with col_t1:
                        st.markdown("**Tarea 1**")
                        tarea1 = st.text_area("Descripción:", key="t1_desc", height=100)
                        fecha1 = st.date_input("Fecha:", key="t1_fecha", value=f_hoy + datetime.timedelta(days=7))
                    with col_t2:
                        st.markdown("**Tarea 2**")
                        tarea2 = st.text_area("Descripción:", key="t2_desc", height=100)
                        fecha2 = st.date_input("Fecha:", key="t2_fecha", value=f_hoy + datetime.timedelta(days=7))
                    with col_t3:
                        st.markdown("**Tarea 3**")
                        tarea3 = st.text_area("Descripción:", key="t3_desc", height=100)
                        fecha3 = st.date_input("Fecha:", key="t3_fecha", value=f_hoy + datetime.timedelta(days=7))
                    if st.form_submit_button("💾 Guardar Clase"):
                        if not temas.strip():
                            st.error("El contenido de la clase no puede estar vacío.")
                        elif st.session_state.es_suplente and not suplente_nombre.strip():
                            st.error("Ingresá el apellido y nombre del profesor suplente.")
                        else:
                            try:
                                supabase.table("bitacora").insert({
                                    "inscripcion_id": inscripcion_id, "fecha": str(f_hoy),
                                    "contenido_clase": temas,
                                    "profesor_suplente": suplente_nombre.strip() if st.session_state.es_suplente else None,
                                    "tarea_proxima": tarea1 or tarea2 or tarea3 or None,
                                    "fecha_tarea": str(fecha1) if tarea1 else (str(fecha2) if tarea2 else (str(fecha3) if tarea3 else None)),
                                    "tarea1": tarea1 or None, "tarea1_fecha": str(fecha1) if tarea1 else None,
                                    "tarea2": tarea2 or None, "tarea2_fecha": str(fecha2) if tarea2 else None,
                                    "tarea3": tarea3 or None, "tarea3_fecha": str(fecha3) if tarea3 else None,
                                    "tarea1_completada": False, "tarea2_completada": False, "tarea3_completada": False,
                                    "tarea_proxima_completada": False,
                                }).execute()
                                st.session_state.es_suplente = False
                                st.success("Clase guardada satisfactoriamente."); st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

    # =========================================================
    # TAB 1 — HISTORIAL DE CLASES
    # =========================================================
    with tabs[1]:
        st.subheader("📋 Historial de Clases")
        if not mapa_cursos:
            no_encontrado("No tenés cursos creados.")
        else:
            st.markdown('<div class="filtros-box">', unsafe_allow_html=True)
            col_f1, col_f2, col_f3 = st.columns(3)
            hist_curso = col_f1.selectbox("Curso:", ["Todos"] + list(mapa_cursos.keys()), key="hist_curso_sel")
            hist_tipo_prof = col_f2.selectbox("Profesor:", ["Todos", "👤 Titular", "👥 Suplente"], key="hist_tipo_prof_sel")
            hist_contenido = col_f3.text_input("🔍 Buscar en contenido:", key="hist_contenido_sel")
            col_f4, col_f5, col_f6 = st.columns(3)
            anio_actual = f_hoy.year
            hist_anio = col_f4.selectbox("Año lectivo:", list(range(anio_actual, anio_actual - 5, -1)), key="hist_anio_sel")
            hist_desde = col_f5.date_input("Desde:", value=datetime.date(hist_anio, 1, 1), key="hist_desde_sel")
            hist_hasta = col_f6.date_input("Hasta:", value=datetime.date(hist_anio, 12, 31), key="hist_hasta_sel")
            st.markdown('</div>', unsafe_allow_html=True)
            try:
                ids_insc = list(mapa_cursos.values()) if hist_curso == "Todos" else [mapa_cursos[hist_curso]]
                todos_registros = []
                for iid in ids_insc:
                    nombre_curso_hist = [k for k, v in mapa_cursos.items() if v == iid][0]
                    res_b = supabase.table("bitacora").select("*").eq("inscripcion_id", iid).gte("fecha", str(hist_desde)).lte("fecha", str(hist_hasta)).order("fecha", desc=True).execute()
                    for reg in (res_b.data or []):
                        reg['_curso'] = nombre_curso_hist
                        todos_registros.append(reg)
                filtrados = []
                for reg in todos_registros:
                    suplente = reg.get('profesor_suplente')
                    if hist_tipo_prof == "👤 Titular" and suplente: continue
                    if hist_tipo_prof == "👥 Suplente" and not suplente: continue
                    if hist_contenido.strip() and hist_contenido.lower() not in (reg.get('contenido_clase', '') or '').lower(): continue
                    filtrados.append(reg)
                filtrados.sort(key=lambda x: x['fecha'], reverse=True)
                if not filtrados:
                    no_encontrado("No se encontraron clases con los filtros seleccionados.")
                else:
                    st.caption(f"📊 {len(filtrados)} clase/s encontrada/s")
                    for reg in filtrados:
                        suplente_h = reg.get('profesor_suplente')
                        prof_label = f"👥 Suplente: {suplente_h}" if suplente_h else "👤 Titular"
                        fecha_fmt = datetime.date.fromisoformat(reg['fecha']).strftime('%d/%m/%Y')
                        with st.expander(f"📅 {fecha_fmt} · {reg['_curso']} · {prof_label}"):
                            if suplente_h:
                                st.markdown(f'<span class="suplente-badge">👤 Clase dictada por suplente: {suplente_h}</span>', unsafe_allow_html=True)
                            else:
                                st.markdown('<span class="titular-badge">👤 Clase dictada por titular</span>', unsafe_allow_html=True)
                            if st.session_state.editando_bitacora == reg['id']:
                                with st.form(f"edit_bit_h_{reg['id']}"):
                                    t_edit = st.text_area("Contenido dictado:", value=reg.get('contenido_clase', ''))
                                    es_sup_edit = st.checkbox("¿Clase dictada por suplente?", value=bool(suplente_h), key=f"sup_chk_h_{reg['id']}")
                                    sup_nombre_edit = ""
                                    if es_sup_edit:
                                        sup_nombre_edit = st.text_input("Apellido y Nombre del suplente:", value=suplente_h or "", key=f"sup_nom_h_{reg['id']}")
                                    st.markdown("**Tareas:**")
                                    col_t1, col_t2, col_t3 = st.columns(3)
                                    with col_t1:
                                        st.markdown("**Tarea 1**")
                                        t1_e = st.text_area("Descripción:", value=reg.get('tarea1','') or '', key=f"et1_h_{reg['id']}")
                                        f1_e = st.date_input("Fecha:", value=datetime.date.fromisoformat(reg['tarea1_fecha']) if reg.get('tarea1_fecha') else f_hoy, key=f"ef1_h_{reg['id']}")
                                    with col_t2:
                                        st.markdown("**Tarea 2**")
                                        t2_e = st.text_area("Descripción:", value=reg.get('tarea2','') or '', key=f"et2_h_{reg['id']}")
                                        f2_e = st.date_input("Fecha:", value=datetime.date.fromisoformat(reg['tarea2_fecha']) if reg.get('tarea2_fecha') else f_hoy, key=f"ef2_h_{reg['id']}")
                                    with col_t3:
                                        st.markdown("**Tarea 3**")
                                        t3_e = st.text_area("Descripción:", value=reg.get('tarea3','') or '', key=f"et3_h_{reg['id']}")
                                        f3_e = st.date_input("Fecha:", value=datetime.date.fromisoformat(reg['tarea3_fecha']) if reg.get('tarea3_fecha') else f_hoy, key=f"ef3_h_{reg['id']}")
                                    col_e1, col_e2 = st.columns(2)
                                    if col_e1.form_submit_button("💾 Guardar Cambios"):
                                        try:
                                            supabase.table("bitacora").update({
                                                "contenido_clase": t_edit,
                                                "profesor_suplente": sup_nombre_edit.strip() if es_sup_edit and sup_nombre_edit.strip() else None,
                                                "tarea1": t1_e or None, "tarea1_fecha": str(f1_e) if t1_e else None,
                                                "tarea2": t2_e or None, "tarea2_fecha": str(f2_e) if t2_e else None,
                                                "tarea3": t3_e or None, "tarea3_fecha": str(f3_e) if t3_e else None,
                                            }).eq("id", reg['id']).execute()
                                            st.session_state.editando_bitacora = None
                                            st.success("Registro actualizado."); st.rerun()
                                        except Exception as e:
                                            st.error(f"Error: {e}")
                                    if col_e2.form_submit_button("❌ Cancelar"):
                                        st.session_state.editando_bitacora = None; st.rerun()
                            else:
                                st.write(f"**Contenido:** {reg.get('contenido_clase', '-')}")
                                for i in range(1, 4):
                                    txt = reg.get(f'tarea{i}')
                                    fecha_t = reg.get(f'tarea{i}_fecha')
                                    completada = reg.get(f'tarea{i}_completada', False)
                                    if txt:
                                        vencida = fecha_t and datetime.date.fromisoformat(fecha_t) < f_hoy and not completada
                                        if completada:
                                            st.markdown(f'''<div class="tarea-card-done">
                                                <div class="tarea-titulo">✅ Tarea {i} — COMPLETADA</div>
                                                <div class="tarea-texto">{txt}</div>
                                                <div class="tarea-fecha">📅 {datetime.date.fromisoformat(fecha_t).strftime("%d/%m/%Y") if fecha_t else "-"}</div>
                                            </div>''', unsafe_allow_html=True)
                                            if st.button("↩️ Desmarcar", key=f"descomp_h_{reg['id']}_{i}"):
                                                marcar_tarea(reg['id'], i, False)
                                        elif vencida:
                                            st.markdown(f'''<div class="tarea-card-vencida">
                                                <div class="tarea-titulo">⚠️ VENCIDA · Tarea {i}</div>
                                                <div class="tarea-texto">{txt}</div>
                                                <div class="tarea-fecha">📅 Venció el: {datetime.date.fromisoformat(fecha_t).strftime("%d/%m/%Y")}</div>
                                            </div>''', unsafe_allow_html=True)
                                            if st.button(f"✅ Marcar hecha", key=f"comp_vh_{reg['id']}_{i}"):
                                                marcar_tarea(reg['id'], i, True)
                                        else:
                                            st.markdown(f'''<div class="tarea-card">
                                                <div class="tarea-titulo">Tarea {i}</div>
                                                <div class="tarea-texto">{txt}</div>
                                                <div class="tarea-fecha">📅 {datetime.date.fromisoformat(fecha_t).strftime("%d/%m/%Y") if fecha_t else "-"}</div>
                                            </div>''', unsafe_allow_html=True)
                                col_b1, col_b2 = st.columns([1, 5])
                                if col_b1.button("✏️ Editar", key=f"edit_b_h_{reg['id']}"):
                                    st.session_state.editando_bitacora = reg['id']; st.rerun()
                                if col_b2.button("🗑️ Borrar", key=f"del_b_h_{reg['id']}"):
                                    try:
                                        supabase.table("bitacora").delete().eq("id", reg['id']).execute()
                                        st.success("Registro eliminado."); st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
            except Exception as e:
                st.error(f"Error en historial: {e}")

    # =========================================================
    # TAB 2 — ALUMNOS
    # =========================================================
    with tabs[2]:
        sub_al = st.radio("Acción:", ["Ver Lista", "Registrar Alumno Nuevo"], horizontal=True)
        if sub_al == "Registrar Alumno Nuevo":
            if not mapa_cursos:
                no_encontrado("Primero creá un curso en la pestaña 🏗️ Cursos.")
            else:
                with st.form("new_al"):
                    n = st.text_input("Nombre *")
                    a = st.text_input("Apellido *")
                    e = st.text_input("Email (opcional)", placeholder="alumno@mail.com")
                    c_sel = st.selectbox("Asignar a curso:", list(mapa_cursos.keys()))
                    if st.form_submit_button("💾 REGISTRAR"):
                        if not n.strip() or not a.strip():
                            st.error("Nombre y Apellido son obligatorios.")
                        else:
                            try:
                                datos_alumno = {"nombre": n.strip(), "apellido": a.strip()}
                                if e.strip(): datos_alumno["email"] = e.strip()
                                ra = supabase.table("alumnos").insert(datos_alumno).execute()
                                if ra.data:
                                    supabase.table("inscripciones").insert({"alumno_id": ra.data[0]['id'], "profesor_id": u_data['id'], "nombre_curso_materia": c_sel, "anio_lectivo": 2026}).execute()
                                    st.success(f"Alumno {a.upper()}, {n} registrado en {c_sel}."); st.rerun()
                            except Exception as e_err:
                                st.error(f"Error: {e_err}")
        else:
            if not mapa_cursos:
                no_encontrado("No hay cursos creados.")
            else:
                c_v = st.selectbox("Filtrar por curso:", ["---"] + list(mapa_cursos.keys()), key="curso_alumnos_sel",
                    on_change=lambda: st.session_state.update({'busq_alumno_val': ''}))
                busqueda = st.text_input("🔍 Buscar alumno por nombre o apellido:", value=st.session_state.busq_alumno_val, key="busq_alumno_input")
                st.session_state.busq_alumno_val = busqueda
                if c_v != "---":
                    try:
                        res_al = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido, email)").eq("nombre_curso_materia", c_v).not_.is_("alumno_id", "null").execute()
                        alumnos_filtrados = []
                        for r in res_al.data:
                            al_raw = r.get('alumnos')
                            al = al_raw[0] if isinstance(al_raw, list) and al_raw else al_raw
                            if al:
                                if busqueda.strip() == "" or busqueda.lower() in al.get('nombre','').lower() or busqueda.lower() in al.get('apellido','').lower():
                                    alumnos_filtrados.append((r, al))
                        if not res_al.data: no_encontrado("No hay alumnos inscriptos en este curso.")
                        elif not alumnos_filtrados: no_encontrado(f"No se encontró ningún alumno con '{busqueda}'.")
                        else:
                            st.info(f"Cantidad de alumnos: {len(alumnos_filtrados)}")
                            for r, al in alumnos_filtrados:
                                if st.session_state.editando_alumno == r['id']:
                                    with st.form(f"edit_al_{r['id']}"):
                                        n_edit = st.text_input("Nombre:", value=al.get('nombre', ''))
                                        a_edit = st.text_input("Apellido:", value=al.get('apellido', ''))
                                        e_edit = st.text_input("Email (opcional):", value=al.get('email', '') or '')
                                        col_a1, col_a2 = st.columns(2)
                                        if col_a1.form_submit_button("💾 Guardar"):
                                            try:
                                                supabase.table("alumnos").update({"nombre": n_edit.strip(), "apellido": a_edit.strip(), "email": e_edit.strip() if e_edit.strip() else None}).eq("id", al['id']).execute()
                                                st.session_state.editando_alumno = None
                                                st.success("Alumno actualizado."); st.rerun()
                                            except Exception as e_err:
                                                st.error(f"Error: {e_err}")
                                        if col_a2.form_submit_button("❌ Cancelar"):
                                            st.session_state.editando_alumno = None; st.rerun()
                                else:
                                    email_display = f'<br><span class="email-tag">✉️ {al.get("email","")}</span>' if al.get('email') else ''
                                    st.markdown(f'<div class="planilla-row">👤 {al.get("apellido","").upper()}, {al.get("nombre","")}{email_display}</div>', unsafe_allow_html=True)
                                    ab1, ab2 = st.columns(2)
                                    if ab1.button("✏️ Editar", key=f"eal_{r['id']}"):
                                        st.session_state.editando_alumno = r['id']; st.rerun()
                                    if ab2.button("🗑️ Borrar", key=f"dal_{r['id']}"):
                                        try:
                                            supabase.table("inscripciones").delete().eq("id", r['id']).execute()
                                            st.success("Alumno eliminado del curso."); st.rerun()
                                        except Exception as e_err:
                                            st.error(f"Error: {e_err}")
                    except Exception as e:
                        st.error(f"Error al cargar alumnos: {e}")

    # =========================================================
    # TAB 3 — NOTAS
    # =========================================================
    with tabs[3]:
        st.subheader("📝 Notas y Calificaciones")
        if not mapa_cursos:
            no_encontrado("No hay cursos creados.")
        else:
            sub_nt = st.radio("Acción:", ["📋 Ver Notas por Curso", "✏️ Cargar Nota"], horizontal=True)
            if sub_nt == "📋 Ver Notas por Curso":
                col_f1, col_f2 = st.columns([2, 1])
                c_ver = col_f1.selectbox("Seleccione Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_ver_sel",
                    on_change=lambda: st.session_state.update({'busq_nota_val': '', 'filtro_estado_val': 'Todos'}))
                filtro_estado = col_f2.selectbox("Filtrar por estado:", ["Todos", "✅ Aprobados", "❌ Desaprobados"],
                    index=["Todos", "✅ Aprobados", "❌ Desaprobados"].index(st.session_state.filtro_estado_val), key="filtro_estado_sel",
                    on_change=lambda: st.session_state.update({'busq_nota_val': ''}))
                st.session_state.filtro_estado_val = filtro_estado
                busq_nota = st.text_input("🔍 Buscar alumno:", value=st.session_state.busq_nota_val, key="busq_nota_input")
                st.session_state.busq_nota_val = busq_nota
                if c_ver != "---":
                    curso_data = mapa_cursos_data.get(c_ver, {})
                    nota_aprobacion = curso_data.get('nota_aprobacion')
                    if nota_aprobacion: st.caption(f"Nota de aprobación del curso: {nota_aprobacion}")
                    try:
                        res_al_v = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido, email)").eq("nombre_curso_materia", c_ver).not_.is_("alumno_id", "null").execute()
                        if not res_al_v.data:
                            no_encontrado("No hay alumnos inscriptos en este curso.")
                        else:
                            mostrados = 0
                            for r in res_al_v.data:
                                al_raw = r.get('alumnos')
                                al = al_raw[0] if isinstance(al_raw, list) and al_raw else al_raw
                                if al:
                                    if busq_nota.strip() and busq_nota.lower() not in al.get('nombre','').lower() and busq_nota.lower() not in al.get('apellido','').lower(): continue
                                    try:
                                        res_notas = supabase.table("notas").select("id, calificacion, created_at").eq("inscripcion_id", r['id']).order("created_at", desc=False).execute()
                                        notas = res_notas.data if res_notas.data else []
                                    except: notas = []
                                    filas_html = ""; valores = []
                                    for i, nt in enumerate(notas):
                                        val = float(nt['calificacion']); valores.append(val)
                                        fecha_fmt = datetime.datetime.fromisoformat(nt['created_at'][:10]).strftime('%d/%m/%Y')
                                        filas_html += f'<div class="nota-linea"><span>Nota {i+1} · {fecha_fmt}</span><span class="nota-badge {color_nota(val)}">{val}</span></div>'
                                    if not valores:
                                        if filtro_estado != "Todos": continue
                                        filas_html = '<div class="nota-linea"><span style="color:#555">Sin notas cargadas</span></div>'
                                        promedio_html = estado_html = ""
                                    else:
                                        promedio = round(sum(valores)/len(valores), 2)
                                        es_aprobado = nota_aprobacion is not None and promedio >= float(nota_aprobacion)
                                        if filtro_estado == "✅ Aprobados" and not es_aprobado: continue
                                        if filtro_estado == "❌ Desaprobados" and es_aprobado: continue
                                        promedio_html = f'<div class="promedio-linea"><span>Promedio</span><span class="nota-badge {color_nota(promedio)}">{promedio}</span></div>'
                                        estado_html = estado_aprobacion(promedio, nota_aprobacion)
                                    email_html = f'<div class="email-tag">✉️ {al.get("email","")}</div>' if al.get("email") else ""
                                    mostrados += 1
                                    st.markdown(f'<div class="alumno-block"><div class="nombre">👤 {al.get("apellido","").upper()}, {al.get("nombre","")} &nbsp; {estado_html if valores else ""}</div>{email_html}{filas_html}{promedio_html if valores else ""}</div>', unsafe_allow_html=True)
                                    if notas:
                                        for i, nt in enumerate(notas):
                                            col_n, col_d = st.columns([6, 1])
                                            col_n.caption(f"Nota {i+1}: {nt['calificacion']}")
                                            if col_d.button("🗑️", key=f"del_nota_{nt['id']}"):
                                                st.session_state[f'confirm_nota_{nt["id"]}'] = True; st.rerun()
                                            if st.session_state.get(f'confirm_nota_{nt["id"]}'):
                                                st.warning(f"⚠️ ¿Borrar Nota {i+1}: {nt['calificacion']}?")
                                                c1, c2 = st.columns(2)
                                                if c1.button("✅ Sí, borrar", key=f"conf_nota_{nt['id']}"):
                                                    try:
                                                        supabase.table("notas").delete().eq("id", nt['id']).execute()
                                                        st.session_state[f'confirm_nota_{nt["id"]}'] = False
                                                        st.success("Nota eliminada."); st.rerun()
                                                    except Exception as e_err:
                                                        st.error(f"Error: {e_err}")
                                                if c2.button("❌ Cancelar", key=f"canc_nota_{nt['id']}"):
                                                    st.session_state[f'confirm_nota_{nt["id"]}'] = False; st.rerun()
                            if mostrados == 0:
                                no_encontrado(f"No se encontró ningún alumno con '{busq_nota}'." if busq_nota.strip() else "No hay alumnos que coincidan con el filtro.")
                            else:
                                st.caption(f"Mostrando {mostrados} alumno/s")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                c_nt = st.selectbox("Seleccione Curso:", ["---"] + list(mapa_cursos.keys()), key="nt_carga_sel",
                    on_change=lambda: st.session_state.update({'busq_carga_val': ''}))
                busq_carga = st.text_input("🔍 Buscar alumno:", value=st.session_state.busq_carga_val, key="busq_carga_input")
                st.session_state.busq_carga_val = busq_carga
                if c_nt != "---":
                    try:
                        res_al_n = supabase.table("inscripciones").select("id, alumnos(id, nombre, apellido, email)").eq("nombre_curso_materia", c_nt).not_.is_("alumno_id", "null").execute()
                        if not res_al_n.data:
                            no_encontrado("No hay alumnos inscriptos en este curso.")
                        else:
                            mostrados_carga = 0
                            for r in res_al_n.data:
                                al_raw = r.get('alumnos')
                                al = al_raw[0] if isinstance(al_raw, list) and al_raw else al_raw
                                if al:
                                    if busq_carga.strip() and busq_carga.lower() not in al.get('nombre','').lower() and busq_carga.lower() not in al.get('apellido','').lower(): continue
                                    mostrados_carga += 1
                                    try:
                                        res_notas = supabase.table("notas").select("id, calificacion, created_at").eq("inscripcion_id", r['id']).order("created_at", desc=False).execute()
                                        notas_existentes = res_notas.data if res_notas.data else []
                                    except: notas_existentes = []
                                    email_display = f'<br><span class="email-tag">✉️ {al.get("email","")}</span>' if al.get('email') else ''
                                    st.markdown(f'<div class="planilla-row">👤 {al.get("apellido","").upper()}, {al.get("nombre","")}{email_display}</div>', unsafe_allow_html=True)
                                    if notas_existentes:
                                        for i, nt in enumerate(notas_existentes):
                                            fecha_fmt = datetime.datetime.fromisoformat(nt['created_at'][:10]).strftime('%d/%m/%Y')
                                            col_n, col_d = st.columns([6, 1])
                                            col_n.markdown(f'<p class="nota-existente">Nota {i+1}: <b>{nt["calificacion"]}</b> · {fecha_fmt}</p>', unsafe_allow_html=True)
                                            if col_d.button("🗑️", key=f"del_nota_c_{nt['id']}"):
                                                st.session_state[f'confirm_nota_c_{nt["id"]}'] = True; st.rerun()
                                            if st.session_state.get(f'confirm_nota_c_{nt["id"]}'):
                                                st.warning(f"⚠️ ¿Borrar Nota {i+1}: {nt['calificacion']}?")
                                                c1, c2 = st.columns(2)
                                                if c1.button("✅ Sí, borrar", key=f"conf_nota_c_{nt['id']}"):
                                                    try:
                                                        supabase.table("notas").delete().eq("id", nt['id']).execute()
                                                        st.session_state[f'confirm_nota_c_{nt["id"]}'] = False
                                                        st.success("Nota eliminada."); st.rerun()
                                                    except Exception as e_err:
                                                        st.error(f"Error: {e_err}")
                                                if c2.button("❌ Cancelar", key=f"canc_nota_c_{nt['id']}"):
                                                    st.session_state[f'confirm_nota_c_{nt["id"]}'] = False; st.rerun()
                                    with st.form(f"nt_{r['id']}"):
                                        nueva_nota = st.number_input("Nueva calificación:", 0.0, 10.0, value=0.0, step=0.1, key=f"ni_{r['id']}")
                                        if st.form_submit_button("💾 Agregar Nota"):
                                            try:
                                                supabase.table("notas").insert({"inscripcion_id": r['id'], "alumno_id": al['id'], "calificacion": nueva_nota}).execute()
                                                st.success(f"Nota {nueva_nota} agregada."); st.rerun()
                                            except Exception as e_err:
                                                st.error(f"Error: {e_err}")
                            if mostrados_carga == 0:
                                no_encontrado(f"No se encontró ningún alumno con '{busq_carga}'." if busq_carga.strip() else "No hay alumnos inscriptos.")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # =========================================================
    # TAB 4 — CONTADOR DE CLASES
    # =========================================================
    with tabs[4]:
        st.subheader("🔢 Contador de Clases")
        if not mapa_cursos:
            no_encontrado("No tenés cursos creados.")
        else:
            st.caption("Seleccioná un curso para ver el detalle de clases dictadas.")
            curso_cont = st.selectbox("Seleccione Curso:", ["---"] + list(mapa_cursos.keys()), key="cont_curso_sel")
            if curso_cont != "---":
                i_c = mapa_cursos[curso_cont]
                cd = mapa_cursos_data.get(curso_cont, {})
                hi_c = str(cd.get('hora_inicio', '') or '')[:5]
                hf_c = str(cd.get('hora_fin', '') or '')[:5]
                nota_ap_c = cd.get('nota_aprobacion')
                try:
                    res_count = supabase.table("inscripciones").select("id", count="exact").eq("nombre_curso_materia", curso_cont).not_.is_("alumno_id", "null").execute()
                    cant_alumnos = res_count.count if res_count.count else 0
                except: cant_alumnos = 0
                cant_clases, ultima_clase = get_stats_curso(i_c)
                ultima_html = f"Última clase: <b>{ultima_clase}</b>" if ultima_clase else "Sin clases registradas aún"
                st.markdown(f'''<div class="contador-card">
                    <div class="cc-nombre">📖 {curso_cont}</div>
                    <div class="cc-info">🕐 {format_horario(hi_c, hf_c)} &nbsp;·&nbsp; Alumnos: {cant_alumnos} &nbsp;·&nbsp; Aprobación: {nota_ap_c if nota_ap_c else "Sin definir"}</div>
                    <div class="cc-clases">📅 Clases dictadas: <b style="font-size:1.1rem;color:#4facfe">{cant_clases}</b> &nbsp;·&nbsp; {ultima_html}</div>
                </div>''', unsafe_allow_html=True)
            else:
                st.markdown("---")
                st.caption("📊 Resumen de todos los cursos:")
                for n_c, i_c in mapa_cursos.items():
                    cd = mapa_cursos_data.get(n_c, {})
                    hi_c = str(cd.get('hora_inicio', '') or '')[:5]
                    hf_c = str(cd.get('hora_fin', '') or '')[:5]
                    nota_ap_c = cd.get('nota_aprobacion')
                    try:
                        res_count = supabase.table("inscripciones").select("id", count="exact").eq("nombre_curso_materia", n_c).not_.is_("alumno_id", "null").execute()
                        cant_alumnos = res_count.count if res_count.count else 0
                    except: cant_alumnos = 0
                    cant_clases, ultima_clase = get_stats_curso(i_c)
                    ultima_html = f"Última: <b>{ultima_clase}</b>" if ultima_clase else "Sin clases aún"
                    st.markdown(f'''<div class="contador-card">
                        <div class="cc-nombre">📖 {n_c}</div>
                        <div class="cc-info">🕐 {format_horario(hi_c, hf_c)} &nbsp;·&nbsp; Alumnos: {cant_alumnos} &nbsp;·&nbsp; Aprobación: {nota_ap_c if nota_ap_c else "Sin definir"}</div>
                        <div class="cc-clases">📅 Clases dictadas: <b style="font-size:1.1rem;color:#4facfe">{cant_clases}</b> &nbsp;·&nbsp; {ultima_html}</div>
                    </div>''', unsafe_allow_html=True)

    # =========================================================
    # TAB 5 — CURSOS
    # =========================================================
    with tabs[5]:
        sub_cu = st.radio("Acción:", ["Mis Cursos", "Crear Nuevo Curso"], horizontal=True)
        if sub_cu == "Crear Nuevo Curso":
            with st.form("new_c"):
                mat = st.text_input("Nombre del Curso *")
                dias = st.multiselect("Días:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                col_h1, col_h2 = st.columns(2)
                hora_ini = col_h1.text_input("Hora de inicio *", placeholder="hh:mm")
                hora_fin = col_h2.text_input("Hora de finalización *", placeholder="hh:mm")
                nota_ap = st.number_input("Nota de aprobación *", min_value=1.0, max_value=10.0, value=None, step=0.5, placeholder="Nota de aprobación")
                biblio = st.text_area("Bibliografía / Fotocopias (opcional)")
                if st.form_submit_button("💾 CREAR CURSO"):
                    errores = []
                    if not mat.strip(): errores.append("El nombre del curso es obligatorio.")
                    if not dias: errores.append("Seleccioná al menos un día.")
                    if not hora_ini.strip(): errores.append("La hora de inicio es obligatoria.")
                    elif not validar_hora(hora_ini): errores.append("Hora de inicio inválida. Usá hh:mm (ej: 15:00).")
                    if not hora_fin.strip(): errores.append("La hora de finalización es obligatoria.")
                    elif not validar_hora(hora_fin): errores.append("Hora de finalización inválida. Usá hh:mm (ej: 17:00).")
                    if nota_ap is None: errores.append("La nota de aprobación es obligatoria.")
                    if errores:
                        for e in errores: st.error(e)
                    else:
                        info = f"{mat.strip()} ({', '.join(dias)}) | {hora_ini.strip()} → {hora_fin.strip()}"
                        try:
                            supabase.table("inscripciones").insert({
                                "profesor_id": u_data['id'], "nombre_curso_materia": info,
                                "anio_lectivo": 2026, "nota_aprobacion": nota_ap,
                                "bibliografia": biblio.strip() if biblio.strip() else None,
                                "hora_inicio": hora_ini.strip(), "hora_fin": hora_fin.strip()
                            }).execute()
                            st.success(f"Curso '{info}' creado correctamente."); st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        else:
            if not mapa_cursos:
                no_encontrado("No tenés cursos creados todavía.")
            else:
                busq_curso = st.text_input("🔍 Buscar curso:", key="busq_curso")
                cursos_filtrados = {n: i for n, i in mapa_cursos.items() if not busq_curso.strip() or busq_curso.lower() in n.lower()}
                if busq_curso.strip() and not cursos_filtrados:
                    no_encontrado(f"No se encontró ningún curso con '{busq_curso}'.")
                else:
                    for n_c, i_c in cursos_filtrados.items():
                        curso_data = mapa_cursos_data.get(n_c, {})
                        nota_ap_cur = curso_data.get('nota_aprobacion')
                        biblio_cur = curso_data.get('bibliografia', '')
                        hi_cur = str(curso_data.get('hora_inicio', '') or '')[:5]
                        hf_cur = str(curso_data.get('hora_fin', '') or '')[:5]
                        if st.session_state.editando_curso == i_c:
                            partes = n_c.split(" (")
                            mat_actual = partes[0] if partes else n_c
                            try: val_nota_edit = float(nota_ap_cur) if nota_ap_cur is not None else None
                            except: val_nota_edit = None
                            with st.form(f"edit_c_{i_c}"):
                                mat_e = st.text_input("Nombre del Curso:", value=mat_actual)
                                dias_e = st.multiselect("Días:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
                                col_h1e, col_h2e = st.columns(2)
                                hora_ini_e = col_h1e.text_input("Hora de inicio:", value=hi_cur, placeholder="hh:mm")
                                hora_fin_e = col_h2e.text_input("Hora de finalización:", value=hf_cur, placeholder="hh:mm")
                                nota_ap_e = st.number_input("Nota de aprobación *", min_value=1.0, max_value=10.0, value=val_nota_edit, step=0.5, placeholder="Nota de aprobación")
                                biblio_e = st.text_area("Bibliografía / Fotocopias (opcional):", value=biblio_cur or "")
                                col_c1, col_c2 = st.columns(2)
                                if col_c1.form_submit_button("💾 Guardar"):
                                    errores = []
                                    if hora_ini_e.strip() and not validar_hora(hora_ini_e): errores.append("Hora de inicio inválida.")
                                    if hora_fin_e.strip() and not validar_hora(hora_fin_e): errores.append("Hora de finalización inválida.")
                                    if nota_ap_e is None: errores.append("La nota de aprobación es obligatoria.")
                                    if errores:
                                        for e in errores: st.error(e)
                                    else:
                                        nuevo_nombre = f"{mat_e.strip()} ({', '.join(dias_e)}) | {hora_ini_e.strip()} → {hora_fin_e.strip()}" if dias_e else mat_e.strip()
                                        try:
                                            supabase.table("inscripciones").update({
                                                "nombre_curso_materia": nuevo_nombre, "nota_aprobacion": nota_ap_e,
                                                "bibliografia": biblio_e.strip() if biblio_e.strip() else None,
                                                "hora_inicio": hora_ini_e.strip() if hora_ini_e.strip() else None,
                                                "hora_fin": hora_fin_e.strip() if hora_fin_e.strip() else None,
                                            }).eq("id", i_c).execute()
                                            st.session_state.editando_curso = None
                                            st.success("Curso actualizado."); st.rerun()
                                        except Exception as e:
                                            st.error(f"Error: {e}")
                                if col_c2.form_submit_button("❌ Cancelar"):
                                    st.session_state.editando_curso = None; st.rerun()
                        else:
                            try:
                                res_count = supabase.table("inscripciones").select("id", count="exact").eq("nombre_curso_materia", n_c).not_.is_("alumno_id", "null").execute()
                                cant = res_count.count if res_count.count else 0
                            except: cant = 0
                            nota_display = nota_ap_cur if nota_ap_cur is not None else "Sin definir"
                            biblio_html = f'<div class="biblio-box">📚 {biblio_cur}</div>' if biblio_cur else ""
                            st.markdown(
                                f'<div class="planilla-row">'
                                f'📖 {n_c}<br>'
                                f'<small style="color:#4facfe;">🕐 {format_horario(hi_cur, hf_cur)} &nbsp;·&nbsp; Alumnos: {cant} &nbsp;·&nbsp; Aprobación: {nota_display}</small>'
                                f'{biblio_html}'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                            cb1, cb2 = st.columns(2)
                            if cb1.button("✏️ Editar", key=f"ec_{i_c}"):
                                st.session_state.editando_curso = i_c; st.rerun()
                            if cb2.button("🗑️ Borrar", key=f"dc_{i_c}"):
                                try:
                                    supabase.table("inscripciones").delete().eq("id", i_c).execute()
                                    st.success("Curso eliminado."); st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

    # =========================================================
    # TAB 6 — CALENDARIO ACADÉMICO (v288: año dinámico)
    # =========================================================
    with tabs[6]:
        st.subheader(f"📆 Calendario Académico {ANIO_ACTUAL}")
        render_seccion_calendario(u_data['sede'])

    # =========================================================
    # TAB 7 — IMPRESIÓN (v288: + exportar Excel)
    # =========================================================
    with tabs[7]:
        st.subheader("🖨️ Impresión y Exportación")
        if not mapa_cursos:
            no_encontrado("No tenés cursos creados.")
        else:
            col_i1, col_i2 = st.columns([2, 1])
            curso_imp = col_i1.selectbox("Seleccione Curso:", list(mapa_cursos.keys()), key="imp_curso")
            accion_imp = col_i2.selectbox("Acción:", ["📄 Exportar PDF", "📊 Exportar Excel", "🖨️ Imprimir"], key="imp_accion")

            if accion_imp == "📊 Exportar Excel":
                st.info("📊 El Excel incluirá el listado completo de alumnos con todas sus notas y promedios.")
                if st.button("⚙️ Generar Excel", type="primary", use_container_width=True):
                    if not EXCEL_OK:
                        st.error("La librería openpyxl no está instalada. Agregá 'openpyxl' a requirements.txt y redesplegá.")
                    else:
                        with st.spinner("Generando Excel..."):
                            inscripcion_id_imp = mapa_cursos[curso_imp]
                            curso_data_imp = mapa_cursos_data.get(curso_imp, {})
                            datos_imp = cargar_datos_por_nombre_curso(curso_imp, inscripcion_id_imp)
                            xlsx_bytes = generar_excel(u_data['sede'], curso_imp, curso_data_imp, datos_imp)
                            nombre_xlsx = f"ClassTrack_{u_data['sede']}_{curso_imp[:20].replace(' ','_')}_{datetime.date.today().strftime('%Y%m%d')}.xlsx"
                            st.download_button(
                                label="⬇️ Descargar Excel",
                                data=xlsx_bytes,
                                file_name=nombre_xlsx,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                            st.success("Excel generado. Hacé clic arriba para descargarlo.")
            else:
                st.markdown("**¿Qué incluir?**")
                col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                inc_resumen = col_c1.checkbox("📊 Resumen del curso", value=True, key="inc_resumen")
                inc_alumnos = col_c2.checkbox("👥 Listado de alumnos", value=True, key="inc_alumnos")
                inc_notas = col_c3.checkbox("📝 Notas y promedios", value=True, key="inc_notas")
                inc_historial = col_c4.checkbox("📅 Historial de clases", value=False, key="inc_historial")
                if not any([inc_resumen, inc_alumnos, inc_notas, inc_historial]):
                    st.warning("Seleccioná al menos una sección para incluir.")
                else:
                    if st.button("⚙️ Generar documento", type="primary", use_container_width=True):
                        with st.spinner("Generando..."):
                            inscripcion_id_imp = mapa_cursos[curso_imp]
                            curso_data_imp = mapa_cursos_data.get(curso_imp, {})
                            datos_imp = cargar_datos_por_nombre_curso(curso_imp, inscripcion_id_imp)
                            if accion_imp == "📄 Exportar PDF":
                                pdf_bytes = generar_pdf(u_data['sede'], curso_imp, curso_data_imp, inc_alumnos, inc_notas, inc_historial, inc_resumen, datos_imp)
                                nombre_archivo = f"ClassTrack_{u_data['sede']}_{curso_imp[:20].replace(' ','_')}_{datetime.date.today().strftime('%Y%m%d')}.pdf"
                                st.download_button(label="⬇️ Descargar PDF", data=pdf_bytes, file_name=nombre_archivo, mime="application/pdf", use_container_width=True)
                                st.success("PDF generado. Hacé clic arriba para descargarlo.")
                            else:
                                html_imp = generar_html_impresion(u_data['sede'], curso_imp, curso_data_imp, inc_alumnos, inc_notas, inc_historial, inc_resumen, datos_imp)
                                html_encoded = html_imp.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")
                                js_code = f"<script>var w=window.open('','_blank');w.document.write('{html_encoded}');w.document.close();</script>"
                                components.html(js_code, height=0)
                                st.success("✅ Se abrió la ventana de impresión en una nueva pestaña.")
            st.markdown("---")
            st.caption("💡 PDF ideal para enviar por mail · Excel para trabajar los datos · Imprimir abre el diálogo del navegador.")

# ============================================================
# FIN PARTE 2 DE 2 — v288 completa ✅
# ============================================================
