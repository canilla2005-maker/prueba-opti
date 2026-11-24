import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="OptiRoute | Gestión minera",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos y paleta
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    .stApp {
        background:
          radial-gradient(circle at 85% 0%, rgba(56,189,248,.11), transparent 28%),
          linear-gradient(135deg,#0b1220 0%,#101b2c 55%,#0b1422 100%);
        color:#eef4fb;
        font-family:'DM Sans',sans-serif;
    }
    h1,h2,h3 {font-family:'Space Grotesk',sans-serif !important;}
    [data-testid="stSidebar"] {background:#0e1929;border-right:1px solid rgba(148,163,184,.15);}
    [data-testid="stSidebar"] * {color:#e7eef8;}
    .block-container {padding-top:1.5rem;padding-bottom:3rem;max-width:1460px;}
    .hero {
      padding:1.65rem 2rem;border:1px solid rgba(148,163,184,.18);
      border-radius:22px;background:linear-gradient(115deg,rgba(30,48,70,.96),rgba(17,30,48,.90));
      box-shadow:0 18px 50px rgba(0,0,0,.22);margin-bottom:1.2rem;
    }
    .eyebrow {color:#f6b94e;text-transform:uppercase;letter-spacing:.16em;font-size:.72rem;font-weight:700;}
    .hero-title {font-family:'Space Grotesk',sans-serif;font-size:clamp(2rem,4vw,2.95rem);line-height:1.05;font-weight:700;color:#f8fafc;margin:.35rem 0;}
    .hero-sub {color:#b8c7d9;font-size:1rem;max-width:840px;}
    .section-label {color:#f2b34d;font-size:.73rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;margin:.3rem 0 .6rem;}
    .panel {background:rgba(17,28,46,.88);border:1px solid rgba(148,163,184,.16);border-radius:17px;padding:1.1rem 1.2rem;}
    .insight-box {
      background:linear-gradient(90deg, rgba(56,189,248,.14), rgba(246,185,78,.10));
      border-left:4px solid #38bdf8;
      border-radius:12px;
      padding:0.95rem 1.2rem;
      margin-bottom:1rem;
      color:#f1f5f9;
      font-size:0.95rem;
    }
    div.stButton>button {
      background:linear-gradient(90deg,#f0a52e,#f7bd58);color:#172033;border:0;
      border-radius:11px;padding:.65rem 1rem;font-weight:700;min-height:2.7rem;
    }
    div.stButton>button:hover {filter:brightness(1.06);color:#172033;}
    .small-muted {color:#9aabc0;font-size:.83rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Estado inicial
if "saved_scenario" not in st.session_state:
    st.session_state.saved_scenario = None
if "simulation_result" not in st.session_state:
    st.session_state.simulation_result = None

defaults = {
    "truck_count": 8,
    "payload_tons": 180.0,
    "shift_hours": 8,
    "shifts_per_day": 3,
    "availability_pct": 90,
    "loading_base": 10.0,
    "haul_base": 24.0,
    "dump_base": 4.0,
    "delay_base": 3.0,
    "improvement_pct": 15,
    "sim_seed": 42,
    "selected_route": "Ruta A · Corredor Principal",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def apply_preset(preset_name: str):
    if preset_name == "Estándar":
        st.session_state.update(defaults)
    elif preset_name == "Ruta larga":
        st.session_state.update({
            "truck_count": 12,
            "payload_tons": 220.0,
            "loading_base": 11.0,
            "haul_base": 42.0,
            "dump_base": 4.5,
            "delay_base": 4.0,
            "improvement_pct": 12,
            "selected_route": "Ruta B · Variante Este",
        })
    elif preset_name == "Alta demora":
        st.session_state.update({
            "truck_count": 8,
            "payload_tons": 180.0,
            "loading_base": 14.0,
            "haul_base": 26.0,
            "dump_base": 6.0,
            "delay_base": 9.0,
            "improvement_pct": 20,
            "selected_route": "Ruta C · Acceso Directo",
        })


def build_route_options(haul_minutes: float, improvement_pct: float):
    factor_opt = 1 - improvement_pct / 100
    routes = {
        "Ruta A · Corredor Principal": {
            "desc": "Recorrido balanceado con pendiente moderada y menor congestión.",
            "factor": 0.94,
            "distance_km": round(max(3.2, haul_minutes * 0.24), 1),
            "points": [(1, 2, 120), (3, 4.5, 165), (6, 4.2, 210), (8.5, 6, 255), (11, 6.5, 290)],
        },
        "Ruta B · Variante Este": {
            "desc": "Mayor extensión por el borde este, útil cuando hay restricciones en el tramo central.",
            "factor": 1.12,
            "distance_km": round(max(4.0, haul_minutes * 0.29), 1),
            "points": [(1, 2, 120), (2.5, 1.2, 150), (6.5, 1.5, 200), (9.5, 3.8, 250), (11, 6.5, 290)],
        },
        "Ruta C · Acceso Directo": {
            "desc": "Trayecto más corto en distancia pero con mayor exigencia de pendiente y maniobra.",
            "factor": 1.02,
            "distance_km": round(max(2.8, haul_minutes * 0.21), 1),
            "points": [(1, 2, 120), (4, 3.0, 190), (7.5, 5.2, 250), (11, 6.5, 290)],
        },
    }
    computed = {}
    for name, data in routes.items():
        base_t = haul_minutes * data["factor"]
        opt_t = base_t * factor_opt
        computed[name] = {
            **data,
            "base_time": round(base_t, 2),
            "opt_time": round(opt_t, 2),
        }
    optimal_name = min(computed.keys(), key=lambda k: computed[k]["opt_time"])
    return computed, optimal_name


def render_route_map(routes_data: dict, active_route: str, optimal_route: str, view_mode: str = "2D"):
    fig = go.Figure()

    if view_mode == "3D":
        gx = np.linspace(0.5, 11.5, 35)
        gy = np.linspace(0.5, 7.2, 28)
        GX, GY = np.meshgrid(gx, gy)
        GZ = 115 + (GX - 1.0) * 16.5 + (GY - 2.0) * 6.0 + 14.0 * np.sin(GX * 0.65) * np.cos(GY * 0.55)

        fig.add_trace(
            go.Surface(
                x=GX,
                y=GY,
                z=GZ,
                colorscale="Blues",
                opacity=0.28,
                showscale=False,
                hoverinfo="skip",
            )
        )

        for name, info in routes_data.items():
            xs = [p[0] for p in info["points"]]
            ys = [p[1] for p in info["points"]]
            zs = [p[2] for p in info["points"]]
            is_opt = name == optimal_route
            is_sel = name == active_route

            if is_opt:
                line_color, line_width, opacity = "#38bdf8", 7, 1.0
                tag = f"★ {name} (Óptima · {info['opt_time']} min)"
            elif is_sel:
                line_color, line_width, opacity = "#f6b94e", 6, 0.95
                tag = f"{name} (Seleccionada · {info['opt_time']} min)"
            else:
                line_color, line_width, opacity = "#94a3b8", 4, 0.65
                tag = f"{name} ({info['opt_time']} min)"

            fig.add_trace(
                go.Scatter3d(
                    x=xs,
                    y=ys,
                    z=zs,
                    mode="lines+markers",
                    name=tag,
                    line=dict(color=line_color, width=line_width),
                    marker=dict(size=6, color=line_color),
                    opacity=opacity,
                    hovertemplate=(
                        f"<b>{name}</b><br>"
                        f"Cota: %{{z:.0f}} msnm<br>"
                        f"Distancia aprox.: {info['distance_km']} km<br>"
                        f"Transporte optimizado: {info['opt_time']} min<extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            paper_bgcolor="#111c2e",
            font=dict(color="#cbd5e1", family="DM Sans"),
            height=460,
            margin=dict(l=10, r=10, t=25, b=10),
            scene=dict(
                xaxis=dict(title="Este-Oeste", backgroundcolor="#0d1626", gridcolor="rgba(148,163,184,0.15)"),
                yaxis=dict(title="Norte-Sur", backgroundcolor="#0d1626", gridcolor="rgba(148,163,184,0.15)"),
                zaxis=dict(title="Cota (m)", backgroundcolor="#0d1626", gridcolor="rgba(148,163,184,0.15)"),
            ),
            legend=dict(bgcolor="rgba(17,28,46,0.9)", bordercolor="rgba(148,163,184,0.2)", borderwidth=1),
        )
        return fig

    for name, info in routes_data.items():
        xs = [p[0] for p in info["points"]]
        ys = [p[1] for p in info["points"]]
        is_opt = name == optimal_route
        is_sel = name == active_route

        if is_opt:
            line_color, line_width, dash_style, opacity = "#38bdf8", 5, "solid", 1.0
            tag = f"★ {name} (Óptima · {info['opt_time']} min)"
        elif is_sel:
            line_color, line_width, dash_style, opacity = "#f6b94e", 4, "solid", 0.95
            tag = f"{name} (Seleccionada · {info['opt_time']} min)"
        else:
            line_color, line_width, dash_style, opacity = "#64748b", 2.5, "dot", 0.65
            tag = f"{name} ({info['opt_time']} min)"

        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines+markers",
                name=tag,
                line=dict(color=line_color, width=line_width, dash=dash_style),
                marker=dict(size=9, color=line_color, line=dict(color="#0b1220", width=1.5)),
                opacity=opacity,
                hovertemplate=(
                    f"<b>{name}</b><br>"
                    f"Distancia aprox.: {info['distance_km']} km<br>"
                    f"Transporte base: {info['base_time']} min<br>"
                    f"Transporte optimizado: {info['opt_time']} min<extra></extra>"
                ),
            )
        )

    fig.add_annotation(
        x=1, y=2, text="⛏️ Frente Carguío", showarrow=True,
        arrowhead=2, ax=0, ay=-32,
        font=dict(color="#f8fafc", size=12), bgcolor="#17243a", bordercolor="#f6b94e", borderwidth=1
    )
    fig.add_annotation(
        x=11, y=6.5, text="🏔️ Descarga / Botadero", showarrow=True,
        arrowhead=2, ax=-10, ay=-32,
        font=dict(color="#f8fafc", size=12), bgcolor="#17243a", bordercolor="#38bdf8", borderwidth=1
    )

    fig.update_layout(
        paper_bgcolor="#111c2e",
        plot_bgcolor="#0d1626",
        font=dict(color="#cbd5e1", family="DM Sans"),
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,0.12)", zeroline=False, title="Eje Este-Oeste (esquema)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,0.12)", zeroline=False, title="Cota / Norte-Sur (esquema)"),
        legend=dict(bgcolor="rgba(17,28,46,0.9)", bordercolor="rgba(148,163,184,0.2)", borderwidth=1),
    )
    return fig


def build_executive_html_report(res: dict, insight_text: str, optimal_route: str) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows_html = ""
    for _, r in res["df"].iterrows():
        rows_html += (
            f"<tr>"
            f"<td>{r['Camión']}</td>"
            f"<td>{r['Carguío (min)']}</td>"
            f"<td>{r['Transporte (min)']}</td>"
            f"<td>{r['Descarga (min)']}</td>"
            f"<td>{r['Demoras (min)']}</td>"
            f"<td>{r['Ciclo base (min)']}</td>"
            f"<td><b>{r['Ciclo optimizado (min)']}</b></td>"
            f"</tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Reporte Ejecutivo OptiRoute</title>
<style>
  body {{ font-family: Arial, sans-serif; color: #1e293b; margin: 36px; line-height: 1.45; }}
  .header {{ background: #0f172a; color: #f8fafc; padding: 24px 28px; border-radius: 12px; }}
  .header h1 {{ margin: 0 0 6px 0; font-size: 24px; color: #f6b94e; }}
  .header p {{ margin: 0; font-size: 13px; color: #cbd5e1; }}
  .insight {{ background: #f0f9ff; border-left: 4px solid #0284c7; padding: 14px 16px; margin: 20px 0; border-radius: 6px; }}
  .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 20px 0; }}
  .card {{ border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; background: #f8fafc; }}
  .card .lbl {{ font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: bold; }}
  .card .val {{ font-size: 20px; font-weight: bold; color: #0f172a; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 12px; }}
  th {{ background: #1e293b; color: white; text-align: left; padding: 8px; }}
  td {{ border-bottom: 1px solid #e2e8f0; padding: 7px 8px; }}
  tr:nth-child(even) {{ background: #f8fafc; }}
  .footer {{ margin-top: 28px; font-size: 11px; color: #64748b; }}
  @media print {{ body {{ margin: 16px; }} }}
</style>
</head>
<body>
  <div class="header">
    <h1>⛏️ OptiRoute · Reporte Ejecutivo Operacional</h1>
    <p>Generado el {now_str} · Fuente de datos: {res['source_label']} · Ruta recomendada: {optimal_route}</p>
  </div>

  <div class="insight">
    <strong>Diagnóstico automático:</strong> {insight_text}
  </div>

  <div class="grid">
    <div class="card"><div class="lbl">Ciclo Base</div><div class="val">{res['avg_base']:.2f} min</div></div>
    <div class="card"><div class="lbl">Ciclo Optimizado</div><div class="val">{res['avg_opt']:.2f} min</div></div>
    <div class="card"><div class="lbl">Producción / Turno Opt.</div><div class="val">{res['prod_opt_shift']:,.0f} t</div></div>
    <div class="card"><div class="lbl">Ganancia / Turno</div><div class="val">+{res['prod_opt_shift'] - res['prod_base_shift']:,.0f} t</div></div>
  </div>

  <h3>Detalle de Tiempos por Unidad</h3>
  <table>
    <thead>
      <tr>
        <th>Unidad</th><th>Carguío (min)</th><th>Transporte (min)</th>
        <th>Descarga (min)</th><th>Demoras (min)</th><th>Ciclo Base</th><th>Ciclo Opt.</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>

  <div class="footer">
    OptiRoute · Reporte imprimible (puedes guardarlo como PDF desde tu navegador con Ctrl+P / Cmd+P).
  </div>
</body>
</html>"""


# ---------------- Sidebar ----------------
st.sidebar.markdown("## ⛏️ OptiRoute")
st.sidebar.caption("CENTRO DE CONTROL · TRANSPORTE MINERO")
st.sidebar.divider()

data_mode = st.sidebar.radio(
    "Fuente de datos",
    ["Simulación paramétrica", "Subir mis datos (CSV)"],
    horizontal=False,
)

uploaded_df = None
if data_mode == "Subir mis datos (CSV)":
    st.sidebar.caption("Columnas esperadas: `Camion`, `Carguio`, `Transporte`, `Descarga`, `Demoras` (en minutos).")
    sample_csv = (
        "Camion,Carguio,Transporte,Descarga,Demoras\nC-01,9.5,23.0,3.8,2.0\nC-02,10.2,25.5,4.1,3.5\nC-03,11.0,24.0,4.0,1.5\nC-04,9.8,26.2,3.9,4.2\nC-05,10.5,22.8,4.3,2.1\n"
    )
    st.sidebar.download_button(
        "📄 Descargar plantilla CSV",
        data=sample_csv.encode("utf-8-sig"),
        file_name="plantilla_optiroute.csv",
        mime="text/csv",
        use_container_width=True,
    )
    uploaded_file = st.sidebar.file_uploader("Cargar archivo CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            raw = pd.read_csv(uploaded_file)
            norm_cols = {c.strip().lower(): c for c in raw.columns}
            req = ["carguio", "transporte"]
            if all(r in norm_cols for r in req):
                n = len(raw)
                cam_col = raw[norm_cols["camion"]].astype(str) if "camion" in norm_cols else [f"Unidad {i+1:02d}" for i in range(n)]
                uploaded_df = pd.DataFrame({
                    "Camión": cam_col,
                    "Carguío (min)": pd.to_numeric(raw[norm_cols["carguio"]], errors="coerce").fillna(10.0),
                    "Transporte (min)": pd.to_numeric(raw[norm_cols["transporte"]], errors="coerce").fillna(24.0),
                    "Descarga (min)": pd.to_numeric(raw[norm_cols["descarga"]], errors="coerce").fillna(0.0) if "descarga" in norm_cols else np.zeros(n),
                    "Demoras (min)": pd.to_numeric(raw[norm_cols["demoras"]], errors="coerce").fillna(0.0) if "demoras" in norm_cols else np.zeros(n),
                })
            else:
                st.sidebar.error("El CSV debe incluir al menos las columnas 'Carguio' y 'Transporte'.")
        except Exception as e:
            st.sidebar.error(f"Error al leer CSV: {e}")

st.sidebar.divider()
st.sidebar.markdown("### Escenarios rápidos")
c_p1, c_p2, c_p3 = st.sidebar.columns(3)
with c_p1:
    st.button("Base", on_click=apply_preset, args=("Estándar",), use_container_width=True)
with c_p2:
    st.button("Ruta larga", on_click=apply_preset, args=("Ruta larga",), use_container_width=True)
with c_p3:
    st.button("Demoras", on_click=apply_preset, args=("Alta demora",), use_container_width=True)

st.sidebar.divider()
st.sidebar.markdown("### Controles principales")
truck_count = st.sidebar.slider("Número de camiones", 2, 40, key="truck_count", disabled=(uploaded_df is not None))
payload_tons = st.sidebar.number_input("Capacidad por camión (t)", 10.0, 450.0, step=5.0, key="payload_tons")
haul_base = st.sidebar.slider("Transporte base (min)", 5.0, 90.0, 0.5, key="haul_base", disabled=(uploaded_df is not None))
improvement_pct = st.sidebar.slider("Reducción objetivo del ciclo (%)", 0, 35, key="improvement_pct")

with st.sidebar.expander("⚙️ Ajustes avanzados (tiempos y turno)"):
    loading_base = st.slider("Carguío base (min)", 3.0, 30.0, 0.5, key="loading_base", disabled=(uploaded_df is not None))
    dump_base = st.slider("Descarga / maniobra (min)", 1.0, 20.0, 0.5, key="dump_base", disabled=(uploaded_df is not None))
    delay_base = st.slider("Demoras adicionales (min)", 0.0, 30.0, 0.5, key="delay_base", disabled=(uploaded_df is not None))
    availability_pct = st.slider("Disponibilidad operacional (%)", 50, 100, key="availability_pct")
    shift_hours = st.slider("Duración del turno (h)", 4, 12, key="shift_hours")
    shifts_per_day = st.selectbox("Turnos por día", [1, 2, 3], index=2, key="shifts_per_day")
    sim_seed = st.number_input("Semilla aleatoria", min_value=0, max_value=999999, step=1, key="sim_seed")


def run_calculation():
    if uploaded_df is not None:
        df_local = uploaded_df.copy()
        active_t = len(df_local)
        eff_haul = float(df_local["Transporte (min)"].mean())
        src_label = "Archivo CSV cargado"
    else:
        rng = np.random.default_rng(int(sim_seed))
        loading = np.clip(rng.normal(loading_base, max(0.6, loading_base * 0.12), truck_count), 0.2, None)
        haul = np.clip(rng.normal(haul_base, max(1.0, haul_base * 0.14), truck_count), 0.5, None)
        dump = np.clip(rng.normal(dump_base, max(0.3, dump_base * 0.15), truck_count), 0.2, None)
        delays = (
            np.clip(rng.exponential(scale=max(delay_base, 0.01), size=truck_count), 0.0, None)
            if delay_base > 0
            else np.zeros(truck_count)
        )
        df_local = pd.DataFrame({
            "Camión": [f"Camión {i+1:02d}" for i in range(truck_count)],
            "Carguío (min)": np.round(loading, 2),
            "Transporte (min)": np.round(haul, 2),
            "Descarga (min)": np.round(dump, 2),
            "Demoras (min)": np.round(delays, 2),
        })
        active_t = truck_count
        eff_haul = haul_base
        src_label = "Simulación paramétrica"

    df_local["Ciclo base (min)"] = np.round(
        df_local["Carguío (min)"] + df_local["Transporte (min)"] + df_local["Descarga (min)"] + df_local["Demoras (min)"], 2
    )
    df_local["Ciclo optimizado (min)"] = np.round(df_local["Ciclo base (min)"] * (1 - improvement_pct / 100), 2)
    df_local["Ahorro (min)"] = np.round(df_local["Ciclo base (min)"] - df_local["Ciclo optimizado (min)"], 2)

    avg_b = float(df_local["Ciclo base (min)"].mean())
    avg_o = float(df_local["Ciclo optimizado (min)"].mean())
    av = availability_pct / 100.0

    p_base_tph = active_t * payload_tons * (60.0 / avg_b) * av
    p_opt_tph = active_t * payload_tons * (60.0 / avg_o) * av
    p_base_shift = p_base_tph * shift_hours
    p_opt_shift = p_opt_tph * shift_hours
    p_base_day = p_base_shift * shifts_per_day
    p_opt_day = p_opt_shift * shifts_per_day

    comp_mean = {
        "Carguío": float(df_local["Carguío (min)"].mean()),
        "Transporte": float(df_local["Transporte (min)"].mean()),
        "Descarga": float(df_local["Descarga (min)"].mean()),
        "Demoras": float(df_local["Demoras (min)"].mean()),
    }

    bn_name = max(comp_mean, key=comp_mean.get)
    bn_pct = (comp_mean[bn_name] / avg_b * 100) if avg_b > 0 else 0
    extra_shift = p_opt_shift - p_base_shift
    extra_day = p_opt_day - p_base_day
    ins_text = (
        f"Con {active_t} camiones ({src_label.lower()}), reducir el ciclo en {improvement_pct}% "
        f"aporta +{extra_shift:,.0f} toneladas adicionales por turno (+{extra_day:,.0f} t/día). "
        f"El principal componente del ciclo es {bn_name} ({comp_mean[bn_name]:.1f} min, "
        f"{bn_pct:.0f}% del tiempo total)."
    )

    routes_d, opt_route = build_route_options(eff_haul, improvement_pct)

    st.session_state.simulation_result = {
        "df": df_local,
        "avg_base": avg_b,
        "avg_opt": avg_o,
        "prod_base_tph": p_base_tph,
        "prod_opt_tph": p_opt_tph,
        "prod_base_shift": p_base_shift,
        "prod_opt_shift": p_opt_shift,
        "prod_base_day": p_base_day,
        "prod_opt_day": p_opt_day,
        "components_mean": comp_mean,
        "improvement_pct": improvement_pct,
        "truck_count": active_t,
        "payload_tons": payload_tons,
        "availability_pct": availability_pct,
        "source_label": src_label,
        "effective_haul": eff_haul,
        "insight_text": ins_text,
        "routes_data": routes_d,
        "optimal_route": opt_route,
    }


# ---------------- Encabezado ----------------
st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Plataforma de análisis operacional</div>
      <div class="hero-title">OptiRoute</div>
      <div class="hero-sub">Simulación de ciclos de transporte, mapa de ruta óptima 2D/3D,
      comparación de escenarios y carga de datos operacionales en CSV.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

run_col, ref_col, clear_col = st.columns([1.3, 1.4, 1.2])
with run_col:
    if st.button("▶ Ejecutar simulación", use_container_width=True):
        run_calculation()

res = st.session_state.simulation_result

with ref_col:
    if st.button("📌 Fijar como referencia", use_container_width=True, disabled=(res is None)):
        if res is not None:
            st.session_state.saved_scenario = res.copy()
            st.toast("Escenario guardado para comparación.")

with clear_col:
    if st.button("🗑️ Limpiar referencia", use_container_width=True, disabled=(st.session_state.saved_scenario is None)):
        st.session_state.saved_scenario = None
        st.rerun()

if st.session_state.saved_scenario is not None:
    ref = st.session_state.saved_scenario
    st.info(
        f"Referencia activa: **{ref['truck_count']} camiones** · Ciclo opt. **{ref['avg_opt']:.2f} min** · "
        f"**{ref['prod_opt_shift']:,.0f} t/turno**"
    )

if res is None:
    st.markdown("")
    st.info("Ajusta los parámetros en la barra lateral (o carga un CSV) y presiona **▶ Ejecutar simulación** para ver los resultados.")
else:
    df = res["df"]
    avg_base = res["avg_base"]
    avg_opt = res["avg_opt"]
    prod_base_tph = res["prod_base_tph"]
    prod_opt_tph = res["prod_opt_tph"]
    prod_base_shift = res["prod_base_shift"]
    prod_opt_shift = res["prod_opt_shift"]
    prod_base_day = res["prod_base_day"]
    prod_opt_day = res["prod_opt_day"]
    components_mean = res["components_mean"]
    extra_tons_shift = prod_opt_shift - prod_base_shift
    insight_text = res["insight_text"]
    active_trucks = res["truck_count"]
    source_label = res["source_label"]

    st.markdown(f'<div class="insight-box">💡 <b>Diagnóstico operacional:</b> {insight_text}</div>', unsafe_allow_html=True)
    routes_data, optimal_route = build_route_options(res["effective_haul"], res["improvement_pct"])

    tab_resumen, tab_comparador, tab_ruta, tab_datos = st.tabs([
        "📊 Resumen y gráficos",
        "⚖️ Comparador de escenarios",
        "🗺️ Ruta óptima",
        "📁 Datos y reportes",
    ])

    with tab_resumen:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Ciclo promedio base", f"{avg_base:.2f} min")
        k2.metric("Ciclo optimizado", f"{avg_opt:.2f} min", delta=f"-{res['improvement_pct']}%")
        k3.metric("Productividad optimizada", f"{prod_opt_tph:,.0f} t/h",
                  delta=f"+{prod_opt_tph - prod_base_tph:,.0f} t/h")
        k4.metric("Producción turno opt.", f"{prod_opt_shift:,.0f} t",
                  delta=f"+{extra_tons_shift:,.0f} t")

        st.markdown("")
        ch1, ch2, ch3 = st.columns([1, 1.35, 1])

        with ch1:
            st.markdown('<div class="section-label">Ciclo promedio (min)</div>', unsafe_allow_html=True)
            fig1 = go.Figure(
                data=[
                    go.Bar(
                        x=["Base", "Optimizado"],
                        y=[avg_base, avg_opt],
                        marker_color=["#64748b", "#38bdf8"],
                        text=[f"{avg_base:.1f}", f"{avg_opt:.1f}"],
                        textposition="outside",
                    )
                ]
            )
            fig1.update_layout(
                paper_bgcolor="#111c2e",
                plot_bgcolor="#111c2e",
                font=dict(color="#cbd5e1", family="DM Sans"),
                height=330,
                margin=dict(l=15, r=15, t=25, b=20),
                yaxis=dict(gridcolor="rgba(148,163,184,0.15)", range=[0, max(avg_base, avg_opt) * 1.22]),
            )
            st.plotly_chart(fig1, use_container_width=True)

        with ch2:
            st.markdown('<div class="section-label">Ciclo por unidad</div>', unsafe_allow_html=True)
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=df["Camión"], y=df["Ciclo base (min)"], name="Base", marker_color="#64748b"))
            fig2.add_trace(go.Bar(x=df["Camión"], y=df["Ciclo optimizado (min)"], name="Optimizado", marker_color="#38bdf8"))
            fig2.update_layout(
                barmode="group",
                paper_bgcolor="#111c2e",
                plot_bgcolor="#111c2e",
                font=dict(color="#cbd5e1", family="DM Sans"),
                height=330,
                margin=dict(l=15, r=15, t=25, b=20),
                yaxis=dict(gridcolor="rgba(148,163,184,0.15)", title="Minutos"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig2, use_container_width=True)

        with ch3:
            st.markdown('<div class="section-label">Composición ciclo base</div>', unsafe_allow_html=True)
            comp_labels = list(components_mean.keys())
            comp_vals = list(components_mean.values())
            fig3 = go.Figure(
                data=[
                    go.Bar(
                        x=comp_vals,
                        y=comp_labels,
                        orientation="h",
                        marker_color=["#f59e0b", "#38bdf8", "#34d399", "#f87171"],
                        text=[f"{v:.1f} m" for v in comp_vals],
                        textposition="outside",
                    )
                ]
            )
            fig3.update_layout(
                paper_bgcolor="#111c2e",
                plot_bgcolor="#111c2e",
                font=dict(color="#cbd5e1", family="DM Sans"),
                height=330,
                margin=dict(l=15, r=35, t=25, b=20),
                yaxis=dict(autorange="reversed"),
                xaxis=dict(gridcolor="rgba(148,163,184,0.15)", range=[0, max(comp_vals) * 1.28]),
            )
            st.plotly_chart(fig3, use_container_width=True)

    with tab_comparador:
        st.markdown('<div class="section-label">Escenario Guardado vs. Escenario Simulado</div>', unsafe_allow_html=True)
        if st.session_state.saved_scenario is None:
            st.info(
                "Aún no has fijado un escenario de referencia. Ejecuta una simulación y presiona "
                "**📌 Fijar como referencia** para compararla contra otras corridas."
            )
        else:
            ref = st.session_state.saved_scenario
            diff_cycle = avg_opt - ref["avg_opt"]
            diff_tph = prod_opt_tph - ref["prod_opt_tph"]
            diff_shift = prod_opt_shift - ref["prod_opt_shift"]
            diff_day = prod_opt_day - ref["prod_opt_day"]

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Ciclo opt. actual", f"{avg_opt:.2f} min", delta=f"{diff_cycle:+.2f} min", delta_color="inverse")
            c2.metric("Productividad actual", f"{prod_opt_tph:,.0f} t/h", delta=f"{diff_tph:+,.0f} t/h")
            c3.metric("Producción turno actual", f"{prod_opt_shift:,.0f} t", delta=f"{diff_shift:+,.0f} t")
            c4.metric("Producción día actual", f"{prod_opt_day:,.0f} t", delta=f"{diff_day:+,.0f} t")

            comp_table = pd.DataFrame({
                "Indicador": [
                    "Camiones activos",
                    "Capacidad por camión (t)",
                    "Disponibilidad (%)",
                    "Reducción objetivo (%)",
                    "Ciclo base promedio (min)",
                    "Ciclo optimizado promedio (min)",
                    "Productividad optimizada (t/h)",
                    "Producción por turno opt. (t)",
                    "Producción diaria opt. (t)",
                ],
                "Escenario Guardado": [
                    ref["truck_count"],
                    f"{ref['payload_tons']:.0f}",
                    f"{ref['availability_pct']}%",
                    f"{ref['improvement_pct']}%",
                    f"{ref['avg_base']:.2f}",
                    f"{ref['avg_opt']:.2f}",
                    f"{ref['prod_opt_tph']:,.0f}",
                    f"{ref['prod_opt_shift']:,.0f}",
                    f"{ref['prod_opt_day']:,.0f}",
                ],
                "Escenario Simulado": [
                    active_trucks,
                    f"{res['payload_tons']:.0f}",
                    f"{res['availability_pct']}%",
                    f"{res['improvement_pct']}%",
                    f"{avg_base:.2f}",
                    f"{avg_opt:.2f}",
                    f"{prod_opt_tph:,.0f}",
                    f"{prod_opt_shift:,.0f}",
                    f"{prod_opt_day:,.0f}",
                ],
            })
            st.dataframe(comp_table, use_container_width=True, hide_index=True)

    with tab_ruta:
        st.markdown('<div class="section-label">Evaluación y trazado de ruta (2D / 3D)</div>', unsafe_allow_html=True)
        col_sel, col_mode, col_opt = st.columns([1.8, 1.1, 1.5])
        with col_sel:
            selected_route = st.selectbox("Inspeccionar ruta", list(routes_data.keys()), key="selected_route")
        with col_mode:
            view_mode = st.radio("Vista del mapa", ["2D", "3D"], horizontal=True)
        with col_opt:
            st.success(f"**Ruta más óptima:** {optimal_route} ({routes_data[optimal_route]['opt_time']} min)")

        info_sel = routes_data[selected_route]
        m1, m2, m3 = st.columns(3)
        m1.metric("Distancia estimada", f"{info_sel['distance_km']} km")
        m2.metric("Transporte base", f"{info_sel['base_time']} min")
        m3.metric("Transporte optimizado", f"{info_sel['opt_time']} min", delta=f"-{res['improvement_pct']}%")

        st.caption(info_sel["desc"])
        if view_mode == "3D":
            st.caption("Arrastra para rotar, usa la rueda para zoom y pasa el cursor para ver cota y tiempo.")
        fig_map = render_route_map(routes_data, selected_route, optimal_route, view_mode=view_mode)
        st.plotly_chart(fig_map, use_container_width=True)

    with tab_datos:
        st.markdown('<div class="section-label">Detalle operacional y exportación</div>', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

        d1, d2, d3 = st.columns(3)
        with d1:
            csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "⬇ Descargar tabla en CSV",
                data=csv_bytes,
                file_name="optiroute_datos.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with d2:
            html_report = build_executive_html_report(res, insight_text, optimal_route)
            st.download_button(
                "📄 Reporte Ejecutivo (HTML / Imprimir PDF)",
                data=html_report.encode("utf-8"),
                file_name="optiroute_reporte_ejecutivo.html",
                mime="text/html",
                use_container_width=True,
            )
        with d3:
            md_report = (
                f"f"# Reporte Ejecutivo OptiRoute"f"- **Fuente:** {source_label}"f"- **Flota:** {active_trucks} camiones × {res['payload_tons']:.0f} t"f"- **Ruta recomendada:** {optimal_route}"f"- **Ciclo base:** {avg_base:.2f} min | **Ciclo optimizado:** {avg_opt:.2f} min"f"- **Producción turno optimizada:** {prod_opt_shift:,.0f} t (+{extra_tons_shift:,.0f} t)"f"## Diagnóstico{insight_text}""
            )
            st.download_button(
                "📝 Resumen Ejecutivo (Markdown)",
                data=md_report.encode("utf-8"),
                file_name="optiroute_resumen.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with st.expander("Ver supuestos y limitaciones del modelo"):
            st.write(
                "La productividad se calcula a partir de la flota activa, capacidad por camión, "
                "ciclos teóricos por hora, disponibilidad operacional y duración del turno/día. "
                "El mapa de ruta utiliza un trazado esquemático referencial derivado del tiempo de transporte "
                "y no representa coordenadas GPS reales."
            )

st.markdown(
    '<div style="text-align:center;color:#71839a;font-size:.75rem;margin-top:2.5rem">'
    'OptiRoute · Simulador referencial de transporte minero</div>',
    unsafe_allow_html=True,
)
