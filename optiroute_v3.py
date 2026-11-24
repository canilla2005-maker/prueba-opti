import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

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
    """Genera rutas esquemáticas escaladas según el tiempo base de transporte."""
    factor_opt = 1 - improvement_pct / 100
    routes = {
        "Ruta A · Corredor Principal": {
            "desc": "Recorrido balanceado con pendiente moderada y menor congestión.",
            "factor": 0.94,
            "distance_km": round(max(3.2, haul_minutes * 0.24), 1),
            "points": [(1, 2), (3, 4.5), (6, 4.2), (8.5, 6), (11, 6.5)],
            "labels": ["Pala 01", "Control N1", "Cruce Sur", "Rampa 2", "Botadero Principal"],
        },
        "Ruta B · Variante Este": {
            "desc": "Mayor extensión por el borde este, útil cuando hay restricciones en el tramo central.",
            "factor": 1.12,
            "distance_km": round(max(4.0, haul_minutes * 0.29), 1),
            "points": [(1, 2), (2.5, 1.2), (6.5, 1.5), (9.5, 3.8), (11, 6.5)],
            "labels": ["Pala 01", "Curva Este", "Tramo Este", "Enlace Norte", "Botadero Principal"],
        },
        "Ruta C · Acceso Directo": {
            "desc": "Trayecto más corto en distancia pero con mayor exigencia de pendiente y maniobra.",
            "factor": 1.02,
            "distance_km": round(max(2.8, haul_minutes * 0.21), 1),
            "points": [(1, 2), (4, 3.0), (7.5, 5.2), (11, 6.5)],
            "labels": ["Pala 01", "Paso Directo", "Mirador", "Botadero Principal"],
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


def render_route_map(routes_data: dict, active_route: str, optimal_route: str):
    fig = go.Figure()

    for name, info in routes_data.items():
        xs = [p[0] for p in info["points"]]
        ys = [p[1] for p in info["points"]]
        is_opt = name == optimal_route
        is_sel = name == active_route

        if is_opt:
            line_color = "#38bdf8"
            line_width = 5
            dash_style = "solid"
            opacity = 1.0
            tag = f"★ {name} (Óptima · {info['opt_time']} min)"
        elif is_sel:
            line_color = "#f6b94e"
            line_width = 4
            dash_style = "solid"
            opacity = 0.95
            tag = f"{name} (Seleccionada · {info['opt_time']} min)"
        else:
            line_color = "#64748b"
            line_width = 2.5
            dash_style = "dot"
            opacity = 0.65
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
        height=410,
        margin=dict(l=20, r=20, t=35, b=20),
        xaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,0.12)", zeroline=False, title="Eje Este-Oeste (esquema)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,0.12)", zeroline=False, title="Cota / Norte-Sur (esquema)"),
        legend=dict(bgcolor="rgba(17,28,46,0.9)", bordercolor="rgba(148,163,184,0.2)", borderwidth=1),
    )
    return fig


# ---------------- Sidebar ----------------
st.sidebar.markdown("## ⛏️ OptiRoute")
st.sidebar.caption("CENTRO DE CONTROL · TRANSPORTE MINERO")
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
st.sidebar.markdown("### 1. Flota y turno")
truck_count = st.sidebar.slider("Número de camiones", 2, 40, key="truck_count")
payload_tons = st.sidebar.number_input("Capacidad por camión (t)", 10.0, 450.0, step=5.0, key="payload_tons")
shift_hours = st.sidebar.slider("Duración del turno (h)", 4, 12, key="shift_hours")
shifts_per_day = st.sidebar.selectbox("Turnos por día", [1, 2, 3], index=2, key="shifts_per_day")
availability_pct = st.sidebar.slider("Disponibilidad operacional (%)", 50, 100, key="availability_pct")

st.sidebar.divider()
st.sidebar.markdown("### 2. Tiempos del ciclo (min)")
loading_base = st.sidebar.slider("Carguío", 3.0, 30.0, 0.5, key="loading_base")
haul_base = st.sidebar.slider("Transporte (ida + vuelta)", 5.0, 90.0, 0.5, key="haul_base")
dump_base = st.sidebar.slider("Descarga / maniobra", 1.0, 20.0, 0.5, key="dump_base")
delay_base = st.sidebar.slider("Demoras adicionales", 0.0, 30.0, 0.5, key="delay_base")

st.sidebar.divider()
st.sidebar.markdown("### 3. Escenario optimizado")
improvement_pct = st.sidebar.slider("Reducción objetivo del ciclo (%)", 0, 35, key="improvement_pct")
sim_seed = st.sidebar.number_input("Semilla aleatoria", min_value=0, max_value=999999, value=42, step=1)

# ---------------- Encabezado ----------------
st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Plataforma de análisis operacional</div>
      <div class="hero-title">OptiRoute</div>
      <div class="hero-sub">Simulación de ciclos de transporte, visualización de rutas óptimas,
      productividad estimada de flota y comparación de escenarios mineros.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

p1, p2, p3, p4 = st.columns(4)
p1.metric("Flota activa", f"{truck_count} camiones")
p2.metric("Capacidad nominal", f"{payload_tons:.0f} t")
p3.metric("Esquema diario", f"{shifts_per_day} × {shift_hours} h")
p4.metric("Reducción objetivo", f"-{improvement_pct}%")

st.markdown("")
run_col, info_col = st.columns([1.2, 2.5])
with run_col:
    run_simulation = st.button("▶ Ejecutar simulación", use_container_width=True)
with info_col:
    st.markdown(
        '<div class="small-muted">Configura parámetros o elige un escenario rápido y presiona '
        '<b>Ejecutar simulación</b>. También puedes explorar la pestaña <b>Ruta óptima</b> en cualquier momento.</div>',
        unsafe_allow_html=True,
    )

if run_simulation:
    rng = np.random.default_rng(int(sim_seed))
    loading = np.clip(rng.normal(loading_base, max(0.6, loading_base * 0.12), truck_count), 0.2, None)
    haul = np.clip(rng.normal(haul_base, max(1.0, haul_base * 0.14), truck_count), 0.5, None)
    dump = np.clip(rng.normal(dump_base, max(0.3, dump_base * 0.15), truck_count), 0.2, None)
    delays = (
        np.clip(rng.exponential(scale=max(delay_base, 0.01), size=truck_count), 0.0, None)
        if delay_base > 0
        else np.zeros(truck_count)
    )

    cycle_base = loading + haul + dump + delays
    cycle_opt = cycle_base * (1 - improvement_pct / 100)

    avg_base = float(np.mean(cycle_base))
    avg_opt = float(np.mean(cycle_opt))
    avail = availability_pct / 100

    prod_base_tph = truck_count * payload_tons * (60.0 / avg_base) * avail
    prod_opt_tph = truck_count * payload_tons * (60.0 / avg_opt) * avail

    prod_base_shift = prod_base_tph * shift_hours
    prod_opt_shift = prod_opt_tph * shift_hours

    prod_base_day = prod_base_shift * shifts_per_day
    prod_opt_day = prod_opt_shift * shifts_per_day

    df = pd.DataFrame({
        "Camión": [f"Camión {i+1:02d}" for i in range(truck_count)],
        "Carguío (min)": np.round(loading, 2),
        "Transporte (min)": np.round(haul, 2),
        "Descarga (min)": np.round(dump, 2),
        "Demoras (min)": np.round(delays, 2),
        "Ciclo base (min)": np.round(cycle_base, 2),
        "Ciclo optimizado (min)": np.round(cycle_opt, 2),
        "Ahorro (min)": np.round(cycle_base - cycle_opt, 2),
    })

    st.session_state.simulation_result = {
        "df": df,
        "avg_base": avg_base,
        "avg_opt": avg_opt,
        "prod_base_tph": prod_base_tph,
        "prod_opt_tph": prod_opt_tph,
        "prod_base_shift": prod_base_shift,
        "prod_opt_shift": prod_opt_shift,
        "prod_base_day": prod_base_day,
        "prod_opt_day": prod_opt_day,
        "components_mean": {
            "Carguío": float(np.mean(loading)),
            "Transporte": float(np.mean(haul)),
            "Descarga": float(np.mean(dump)),
            "Demoras": float(np.mean(delays)),
        },
        "improvement_pct": improvement_pct,
        "shift_hours": shift_hours,
        "shifts_per_day": shifts_per_day,
    }

res = st.session_state.simulation_result

tab_resumen, tab_ruta, tab_flota, tab_supuestos = st.tabs([
    "📊 Resumen y gráficos",
    "🗺️ Ruta óptima",
    "🚚 Flota y CSV",
    "⚙️ Supuestos",
])

with tab_resumen:
    if res is None:
        st.info("Presiona **Ejecutar simulación** para generar los indicadores y gráficos de la flota.")
    else:
        base = res["avg_base"]
        opt = res["avg_opt"]
        saved = base - opt

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Ciclo promedio base", f"{base:.2f} min")
        k2.metric("Ciclo optimizado", f"{opt:.2f} min", delta=f"-{res['improvement_pct']}%")
        k3.metric("Ahorro por ciclo", f"{saved:.2f} min")
        k4.metric("Productividad optimizada", f"{res['prod_opt_tph']:,.0f} t/h",
                  delta=f"+{res['prod_opt_tph'] - res['prod_base_tph']:,.0f} t/h")

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Turno base", f"{res['prod_base_shift']:,.0f} t")
        s2.metric("Turno optimizado", f"{res['prod_opt_shift']:,.0f} t",
                  delta=f"+{res['prod_opt_shift'] - res['prod_base_shift']:,.0f} t")
        s3.metric("Día base", f"{res['prod_base_day']:,.0f} t")
        s4.metric("Día optimizado", f"{res['prod_opt_day']:,.0f} t",
                  delta=f"+{res['prod_opt_day'] - res['prod_base_day']:,.0f} t")

        st.markdown("")
        ch1, ch2, ch3 = st.columns([1, 1.3, 1])

        with ch1:
            st.markdown('<div class="section-label">Ciclo promedio</div>', unsafe_allow_html=True)
            fig, ax = plt.subplots(figsize=(5.5, 4))
            fig.patch.set_facecolor("#111c2e")
            ax.set_facecolor("#111c2e")
            bars = ax.bar(["Base", "Optimizado"], [base, opt], color=["#64748b", "#38bdf8"], width=.5)
            ax.set_ylabel("Minutos", color="#cbd5e1")
            ax.tick_params(colors="#cbd5e1")
            for sp in ["top", "right"]:
                ax.spines[sp].set_visible(False)
            ax.spines["bottom"].set_color("#475569")
            ax.spines["left"].set_color("#475569")
            ax.grid(axis="y", alpha=.15, color="#94a3b8")
            ax.set_axisbelow(True)
            for bar, val in zip(bars, [base, opt]):
                ax.text(bar.get_x() + bar.get_width() / 2, val, f"{val:.1f}",
                        ha="center", va="bottom", color="white", fontweight="bold")
            fig.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

        with ch2:
            st.markdown('<div class="section-label">Ciclo por camión</div>', unsafe_allow_html=True)
            tdf = res["df"]
            fig, ax = plt.subplots(figsize=(7, 4))
            fig.patch.set_facecolor("#111c2e")
            ax.set_facecolor("#111c2e")
            x = np.arange(len(tdf))
            ax.bar(x - .18, tdf["Ciclo base (min)"], width=.36, label="Base", color="#64748b")
            ax.bar(x + .18, tdf["Ciclo optimizado (min)"], width=.36, label="Optimizado", color="#38bdf8")
            ax.set_xticks(x)
            ax.set_xticklabels([f"C{i+1}" for i in x], color="#cbd5e1", fontsize=8)
            ax.set_ylabel("Minutos", color="#cbd5e1")
            ax.tick_params(axis="y", colors="#cbd5e1")
            ax.legend(facecolor="#17243a", labelcolor="white", frameon=False)
            for sp in ["top", "right"]:
                ax.spines[sp].set_visible(False)
            ax.spines["bottom"].set_color("#475569")
            ax.spines["left"].set_color("#475569")
            ax.grid(axis="y", alpha=.15, color="#94a3b8")
            ax.set_axisbelow(True)
            fig.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

        with ch3:
            st.markdown('<div class="section-label">Composición base</div>', unsafe_allow_html=True)
            comp = res["components_mean"]
            fig, ax = plt.subplots(figsize=(5.5, 4))
            fig.patch.set_facecolor("#111c2e")
            ax.set_facecolor("#111c2e")
            labels = list(comp.keys())
            vals = list(comp.values())
            colors = ["#f59e0b", "#38bdf8", "#34d399", "#f87171"]
            bars = ax.barh(labels, vals, color=colors, height=.55)
            ax.invert_yaxis()
            ax.set_xlabel("Minutos promedio", color="#cbd5e1")
            ax.tick_params(colors="#cbd5e1")
            for sp in ["top", "right"]:
                ax.spines[sp].set_visible(False)
            ax.spines["bottom"].set_color("#475569")
            ax.spines["left"].set_color("#475569")
            ax.grid(axis="x", alpha=.15, color="#94a3b8")
            ax.set_axisbelow(True)
            for bar, val in zip(bars, vals):
                ax.text(val, bar.get_y() + bar.get_height() / 2, f" {val:.1f}",
                        va="center", ha="left", color="white", fontsize=9, fontweight="bold")
            fig.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

with tab_ruta:
    st.markdown('<div class="section-label">Evaluación y trazado de ruta</div>', unsafe_allow_html=True)
    routes_data, optimal_route = build_route_options(haul_base, improvement_pct)

    col_sel, col_opt = st.columns([2, 1.5])
    with col_sel:
        selected_route = st.selectbox("Inspeccionar ruta", list(routes_data.keys()), key="selected_route")
    with col_opt:
        st.success(f"**Ruta más óptima:** {optimal_route} ({routes_data[optimal_route]['opt_time']} min)")

    info_sel = routes_data[selected_route]
    m1, m2, m3 = st.columns(3)
    m1.metric("Distancia estimada", f"{info_sel['distance_km']} km")
    m2.metric("Transporte base", f"{info_sel['base_time']} min")
    m3.metric("Transporte optimizado", f"{info_sel['opt_time']} min", delta=f"-{improvement_pct}%")

    st.caption(info_sel["desc"])
    fig_map = render_route_map(routes_data, selected_route, optimal_route)
    st.plotly_chart(fig_map, use_container_width=True)

with tab_flota:
    if res is None:
        st.info("Ejecuta una simulación para ver el detalle por camión y descargar el CSV.")
    else:
        st.dataframe(res["df"], use_container_width=True, hide_index=True)
        csv = res["df"].to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇ Descargar detalle en CSV",
            data=csv,
            file_name="optiroute_detalle_flota.csv",
            mime="text/csv",
        )

with tab_supuestos:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.write(
        "El mapa de ruta utiliza un trazado esquemático referencial derivado del tiempo de transporte "
        "configurado y la reducción objetivo; no representa coordenadas GPS reales ni topografía "
        "certificada de una operación específica. La productividad tampoco incorpora colas discretas "
        "ni asignación dinámica de camiones."
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div style="text-align:center;color:#71839a;font-size:.75rem;margin-top:2.5rem">'
    'OptiRoute · Simulador referencial de transporte minero</div>',
    unsafe_allow_html=True,
)
