import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# OptiRoute | Simulador de transporte minero
# Modelo referencial: no incorpora colas, asignación dinámica,
# tiempos de descarga independientes ni restricciones de ruta.
# ------------------------------------------------------------

st.set_page_config(
    page_title="OptiRoute | Gestión minera",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta y estilos
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    .stApp {
        background:
          radial-gradient(circle at 85% 0%, rgba(56,189,248,.10), transparent 27%),
          linear-gradient(135deg,#0b1220 0%,#101b2c 55%,#0b1422 100%);
        color:#eef4fb;
        font-family:'DM Sans',sans-serif;
    }
    h1,h2,h3 {font-family:'Space Grotesk',sans-serif !important;}
    [data-testid="stSidebar"] {background:#0e1929;border-right:1px solid rgba(148,163,184,.15);}
    [data-testid="stSidebar"] * {color:#e7eef8;}
    .block-container {padding-top:1.8rem;padding-bottom:3rem;max-width:1450px;}
    .hero {
      padding:1.8rem 2rem;border:1px solid rgba(148,163,184,.18);
      border-radius:22px;background:linear-gradient(115deg,rgba(30,48,70,.96),rgba(17,30,48,.90));
      box-shadow:0 18px 50px rgba(0,0,0,.20);margin-bottom:1.35rem;
    }
    .eyebrow {color:#f6b94e;text-transform:uppercase;letter-spacing:.16em;font-size:.72rem;font-weight:700;}
    .hero-title {font-family:'Space Grotesk',sans-serif;font-size:clamp(2rem,4vw,3.1rem);line-height:1.05;font-weight:700;color:#f8fafc;margin:.35rem 0;}
    .hero-sub {color:#b8c7d9;font-size:1rem;max-width:800px;}
    .section-label {color:#f2b34d;font-size:.73rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;margin:.25rem 0 .55rem;}
    .panel {background:rgba(17,28,46,.88);border:1px solid rgba(148,163,184,.16);border-radius:17px;padding:1rem 1.15rem;}
    .metric-label {color:#9fb0c5;font-size:.82rem;font-weight:600;}
    .metric-value {color:#f8fafc;font-family:'Space Grotesk',sans-serif;font-size:1.9rem;font-weight:700;margin-top:.2rem;}
    .metric-note {color:#9aabc0;font-size:.76rem;margin-top:.1rem;}
    div.stButton>button {
      background:linear-gradient(90deg,#f0a52e,#f7bd58);color:#172033;border:0;
      border-radius:11px;padding:.68rem 1rem;font-weight:700;min-height:2.8rem;
    }
    div.stButton>button:hover {filter:brightness(1.06);color:#172033;}
    div[data-testid="stAlert"] {border-radius:12px;}
    .small-muted {color:#9aabc0;font-size:.82rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Estado para conservar resultados al interactuar con la página
if "simulation_result" not in st.session_state:
    st.session_state.simulation_result = None

# ---------------- Sidebar ----------------
st.sidebar.markdown("## ⛏️ OptiRoute")
st.sidebar.caption("CENTRO DE CONTROL · TRANSPORTE MINERO")
st.sidebar.divider()
st.sidebar.markdown("### 1. Flota y operación")
truck_count = st.sidebar.slider("Número de camiones", 2, 30, 6)
payload_tons = st.sidebar.number_input("Capacidad por camión (toneladas)", 10.0, 400.0, 180.0, 5.0)
shift_hours = st.sidebar.slider("Duración del turno (horas)", 4, 12, 8)
availability_pct = st.sidebar.slider("Disponibilidad operacional (%)", 50, 100, 90)

st.sidebar.divider()
st.sidebar.markdown("### 2. Tiempos base")
loading_base = st.sidebar.slider("Tiempo de carguío (min)", 5.0, 30.0, 12.0, 0.5)
haul_base = st.sidebar.slider("Tiempo de transporte (min)", 5.0, 70.0, 25.0, 0.5)
delay_base = st.sidebar.slider("Demoras adicionales (min)", 0.0, 30.0, 3.0, 0.5)

st.sidebar.divider()
st.sidebar.markdown("### 3. Escenario optimizado")
improvement_pct = st.sidebar.slider("Reducción objetivo del ciclo (%)", 0, 30, 15)
sim_seed = st.sidebar.number_input("Semilla de simulación", min_value=0, max_value=999999, value=42, step=1)

# ---------------- Encabezado ----------------
st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Plataforma de análisis operacional</div>
      <div class="hero-title">OptiRoute</div>
      <div class="hero-sub">Simulación de ciclos de transporte, productividad estimada de flota
      y comparación de escenarios operacionales.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Resumen de parámetros
p1, p2, p3, p4 = st.columns(4)
p1.metric("Camiones", f"{truck_count}")
p2.metric("Carga por camión", f"{payload_tons:.0f} t")
p3.metric("Disponibilidad", f"{availability_pct}%")
p4.metric("Reducción objetivo", f"{improvement_pct}%")

st.markdown("")
run_col, info_col = st.columns([1.2, 2.2])
with run_col:
    run_simulation = st.button("▶ Ejecutar simulación", use_container_width=True)
with info_col:
    st.markdown(
        '<div class="small-muted">Ajusta los parámetros en el menú lateral y ejecuta un escenario nuevo. '
        'Los resultados anteriores se mantienen hasta la siguiente simulación.</div>',
        unsafe_allow_html=True,
    )

if run_simulation:
    rng = np.random.default_rng(int(sim_seed))
    loading = rng.normal(loading_base, max(0.8, loading_base * 0.12), truck_count)
    haul = rng.normal(haul_base, max(1.0, haul_base * 0.14), truck_count)
    delays = rng.exponential(scale=max(delay_base, 0.01), size=truck_count) if delay_base > 0 else np.zeros(truck_count)

    loading = np.clip(loading, 0.1, None)
    haul = np.clip(haul, 0.1, None)
    delays = np.clip(delays, 0, None)

    cycle_base = loading + haul + delays
    cycle_optimized = cycle_base * (1 - improvement_pct / 100)
    avg_base = float(np.mean(cycle_base))
    avg_opt = float(np.mean(cycle_optimized))
    availability = availability_pct / 100

    # Productividad teórica: ciclos independientes por camión, ajustados por disponibilidad.
    prod_base_tph = truck_count * payload_tons * (60 / avg_base) * availability
    prod_opt_tph = truck_count * payload_tons * (60 / avg_opt) * availability
    prod_base_shift = prod_base_tph * shift_hours
    prod_opt_shift = prod_opt_tph * shift_hours

    df = pd.DataFrame({
        "Camión": [f"Camión {i+1}" for i in range(truck_count)],
        "Carguío (min)": np.round(loading, 2),
        "Transporte (min)": np.round(haul, 2),
        "Demoras (min)": np.round(delays, 2),
        "Ciclo base (min)": np.round(cycle_base, 2),
        "Ciclo optimizado (min)": np.round(cycle_optimized, 2),
    })
    st.session_state.simulation_result = {
        "df": df,
        "avg_base": avg_base,
        "avg_opt": avg_opt,
        "prod_base_tph": prod_base_tph,
        "prod_opt_tph": prod_opt_tph,
        "prod_base_shift": prod_base_shift,
        "prod_opt_shift": prod_opt_shift,
        "improvement_pct": improvement_pct,
        "shift_hours": shift_hours,
        "truck_count": truck_count,
        "payload_tons": payload_tons,
        "availability_pct": availability_pct,
    }

result = st.session_state.simulation_result

if result is None:
    st.markdown("")
    st.info("Configura tu flota y presiona **Ejecutar simulación** para visualizar los indicadores y gráficos.")
    st.markdown('<div class="section-label">Módulos disponibles</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="panel"><h3>📊 Indicadores</h3><div class="small-muted">Ciclo promedio y productividad estimada de la flota.</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="panel"><h3>🚚 Flota</h3><div class="small-muted">Detalle de tiempos por camión y componentes del ciclo.</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="panel"><h3>📁 Reportes</h3><div class="small-muted">Descarga los resultados de cada simulación en CSV.</div></div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="section-label">Resultados de la simulación</div>', unsafe_allow_html=True)
    base = result["avg_base"]
    opt = result["avg_opt"]
    saved = base - opt

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ciclo promedio base", f"{base:.2f} min")
    k2.metric("Ciclo optimizado", f"{opt:.2f} min", delta=f"-{result['improvement_pct']}%")
    k3.metric("Ahorro por ciclo", f"{saved:.2f} min")
    k4.metric("Productividad optimizada", f"{result['prod_opt_tph']:,.0f} t/h")

    s1, s2 = st.columns(2)
    s1.metric("Producción estimada · turno base", f"{result['prod_base_shift']:,.0f} t")
    s2.metric("Producción estimada · turno optimizado", f"{result['prod_opt_shift']:,.0f} t",
              delta=f"+{result['prod_opt_shift'] - result['prod_base_shift']:,.0f} t")

    st.markdown("")
    chart1, chart2 = st.columns(2)
    with chart1:
        st.markdown('<div class="section-label">Comparación de ciclos</div>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(7, 4))
        fig.patch.set_facecolor("#111c2e")
        ax.set_facecolor("#111c2e")
        bars = ax.bar(["Base", "Optimizado"], [base, opt], color=["#64748b", "#38bdf8"], width=.55)
        ax.set_ylabel("Minutos por ciclo", color="#cbd5e1")
        ax.set_title("Tiempo promedio de ciclo", color="#f8fafc", pad=14, fontweight="bold")
        ax.tick_params(colors="#cbd5e1")
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#475569")
        ax.spines["left"].set_color("#475569")
        ax.grid(axis="y", alpha=.15, color="#94a3b8")
        ax.set_axisbelow(True)
        for bar, val in zip(bars, [base, opt]):
            ax.text(bar.get_x()+bar.get_width()/2, val, f"{val:.1f}", ha="center", va="bottom", color="white", fontweight="bold")
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    with chart2:
        st.markdown('<div class="section-label">Ciclo por camión</div>', unsafe_allow_html=True)
        truck_df = result["df"]
        fig, ax = plt.subplots(figsize=(7, 4))
        fig.patch.set_facecolor("#111c2e")
        ax.set_facecolor("#111c2e")
        x = np.arange(len(truck_df))
        ax.bar(x - .18, truck_df["Ciclo base (min)"], width=.36, label="Base", color="#64748b")
        ax.bar(x + .18, truck_df["Ciclo optimizado (min)"], width=.36, label="Optimizado", color="#38bdf8")
        ax.set_xticks(x)
        ax.set_xticklabels([f"C{i+1}" for i in x], color="#cbd5e1")
        ax.set_ylabel("Minutos", color="#cbd5e1")
        ax.set_title("Comparación individual", color="#f8fafc", pad=14, fontweight="bold")
        ax.tick_params(axis="y", colors="#cbd5e1")
        ax.legend(facecolor="#17243a", labelcolor="white", frameon=False)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#475569")
        ax.spines["left"].set_color("#475569")
        ax.grid(axis="y", alpha=.15, color="#94a3b8")
        ax.set_axisbelow(True)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    st.markdown('<div class="section-label">Detalle de la flota</div>', unsafe_allow_html=True)
    st.dataframe(result["df"], use_container_width=True, hide_index=True)

    csv = result["df"].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇ Descargar resultados en CSV",
        data=csv,
        file_name="optiroute_resultados.csv",
        mime="text/csv",
    )

    with st.expander("Ver supuestos y limitaciones del modelo"):
        st.write(
            "La productividad se calcula como capacidad total de la flota multiplicada por "
            "los ciclos teóricos por hora y la disponibilidad operacional. El cálculo supone "
            "que los camiones pueden operar de forma independiente. No modela colas en pala o "
            "botadero, distancias, velocidades, pendientes, tiempos de descarga, asignación "
            "dinámica ni variaciones por ruta. La reducción objetivo se aplica matemáticamente "
            "al ciclo completo; no representa una mejora medida en terreno."
        )

st.markdown(
    '<div style="text-align:center;color:#71839a;font-size:.75rem;margin-top:2.5rem">'
    'OptiRoute · Herramienta referencial de simulación operacional minera</div>',
    unsafe_allow_html=True,
)
