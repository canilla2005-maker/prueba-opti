# app.py - OptiRoute | Simulador y Optimización Minera
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="OptiRoute | Minería",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Estilo visual ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
        --bg: #0b1220;
        --panel: #111c2e;
        --panel-soft: #16243a;
        --accent: #f2a93b;
        --accent-2: #38bdf8;
        --text: #eef4fb;
        --muted: #9aabc0;
    }
    .stApp {
        background:
            radial-gradient(circle at 82% 0%, rgba(56,189,248,.10), transparent 28%),
            linear-gradient(135deg, #0b1220 0%, #101b2c 55%, #0b1422 100%);
        color: var(--text);
        font-family: 'DM Sans', sans-serif;
    }
    h1, h2, h3, .hero-title { font-family: 'Space Grotesk', sans-serif !important; }
    [data-testid="stSidebar"] {
        background: #0e1929;
        border-right: 1px solid rgba(148,163,184,.15);
    }
    [data-testid="stSidebar"] * { color: #e7eef8; }
    .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px; }
    .hero {
        padding: 1.8rem 2rem;
        border: 1px solid rgba(148,163,184,.18);
        border-radius: 22px;
        background: linear-gradient(115deg, rgba(30,48,70,.96), rgba(17,30,48,.88));
        box-shadow: 0 18px 50px rgba(0,0,0,.22);
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .hero:after {
        content: "⛏";
        position: absolute; right: 2.5rem; top: -1.2rem;
        font-size: 8rem; opacity: .08;
    }
    .eyebrow {
        color: #f6b94e; text-transform: uppercase; letter-spacing: .16em;
        font-size: .72rem; font-weight: 700; margin-bottom: .55rem;
    }
    .hero-title { font-size: clamp(2rem, 4vw, 3.1rem); line-height: 1.05; font-weight: 700; margin: 0; color: #f8fafc; }
    .hero-sub { color: #b8c7d9; font-size: 1rem; margin-top: .8rem; max-width: 760px; }
    .section-label {
        color: #f2b34d; font-size: .75rem; font-weight: 700;
        letter-spacing: .13em; text-transform: uppercase; margin: .2rem 0 .55rem;
    }
    .panel {
        background: rgba(17,28,46,.88);
        border: 1px solid rgba(148,163,184,.16);
        border-radius: 18px; padding: 1.15rem 1.25rem;
        box-shadow: 0 10px 30px rgba(0,0,0,.12);
    }
    .metric-label { color: #9fb0c5; font-size: .82rem; font-weight: 600; }
    .metric-value { color: #f8fafc; font-family: 'Space Grotesk',sans-serif; font-size: 2rem; font-weight: 700; margin-top: .25rem; }
    .metric-note { color: #9fb0c5; font-size: .78rem; margin-top: .15rem; }
    div.stButton > button {
        background: linear-gradient(90deg, #f0a52e, #f7bd58);
        color: #172033; border: 0; border-radius: 12px;
        padding: .72rem 1.1rem; font-weight: 700; min-height: 3rem;
        box-shadow: 0 8px 20px rgba(242,169,59,.18);
        transition: transform .15s ease, filter .15s ease;
    }
    div.stButton > button:hover { filter: brightness(1.07); transform: translateY(-1px); color: #172033; }
    div[data-testid="stAlert"] { border-radius: 12px; }
    .footer { color: #72849b; text-align: center; font-size: .75rem; margin-top: 2.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Barra lateral ----------
st.sidebar.markdown("## ⛏️ OptiRoute")
st.sidebar.caption("CENTRO DE CONTROL · MINERÍA")
st.sidebar.divider()
st.sidebar.markdown("### Parámetros de simulación")
camiones = st.sidebar.slider("Número de camiones", 2, 12, 6)
carguio_base = st.sidebar.slider("Tiempo base de carguío", 5.0, 20.0, 12.0, step=0.5, format="%.1f min")
transporte_base = st.sidebar.slider("Tiempo base de transporte", 10.0, 50.0, 25.0, step=0.5, format="%.1f min")
st.sidebar.divider()
st.sidebar.markdown("**Configuración actual**")
st.sidebar.caption(f"🚚 {camiones} camiones en operación")
st.sidebar.caption(f"🪨 Carguío: {carguio_base:.1f} min")
st.sidebar.caption(f"🛣️ Transporte: {transporte_base:.1f} min")
st.sidebar.info("Ajusta los parámetros y ejecuta la simulación para comparar los ciclos.")

# ---------- Encabezado ----------
st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Plataforma de análisis operacional</div>
        <div class="hero-title">OptiRoute</div>
        <div class="hero-sub">
            Simulador de transporte minero para visualizar tiempos de ciclo
            y estimar el impacto de una estrategia de optimización.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.35, 1])
with left:
    st.markdown('<div class="section-label">Panel de simulación</div>', unsafe_allow_html=True)
    st.markdown("### Configura y ejecuta tu escenario")
    st.write(
        "Los tiempos de cada camión se generan a partir de los valores base "
        "definidos en el menú lateral."
    )
    ejecutar = st.button("▶  Ejecutar simulación y optimización", use_container_width=True)
with right:
    st.markdown('<div class="section-label">Objetivo del modelo</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="panel">
            <div style="font-size:1.9rem;font-weight:700;color:#f2b34d;font-family:'Space Grotesk'">−15%</div>
            <div style="font-weight:700;color:#f8fafc">Reducción estimada del ciclo</div>
            <div style="color:#9aabc0;font-size:.85rem;margin-top:.35rem">
                Escenario optimizado aplicado sobre el tiempo de ciclo base.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if ejecutar:
    np.random.seed(42)
    t_carg = np.random.normal(carguio_base, 2.0, camiones)
    t_trans = np.random.normal(transporte_base, 4.0, camiones)

    # Evita tiempos negativos en escenarios de valores base bajos.
    t_carg = np.clip(t_carg, 0, None)
    t_trans = np.clip(t_trans, 0, None)
    total_base = t_carg + t_trans
    total_opt = total_base * 0.85

    st.success("Simulación completada. Se muestran los resultados del escenario.")
    promedio_base = float(np.mean(total_base))
    promedio_opt = float(np.mean(total_opt))
    ahorro = promedio_base - promedio_opt

    st.markdown('<div class="section-label">Indicadores clave</div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            f'<div class="panel"><div class="metric-label">Ciclo promedio base</div>'
            f'<div class="metric-value">{promedio_base:.2f}<span style="font-size:1rem;color:#9aabc0"> min</span></div>'
            f'<div class="metric-note">Antes de optimizar</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="panel"><div class="metric-label">Ciclo promedio optimizado</div>'
            f'<div class="metric-value" style="color:#38bdf8">{promedio_opt:.2f}<span style="font-size:1rem;color:#9aabc0"> min</span></div>'
            f'<div class="metric-note">Con reducción del 15%</div></div>',
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f'<div class="panel"><div class="metric-label">Tiempo ahorrado por ciclo</div>'
            f'<div class="metric-value" style="color:#f2b34d">{ahorro:.2f}<span style="font-size:1rem;color:#9aabc0"> min</span></div>'
            f'<div class="metric-note">Diferencia promedio estimada</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    chart_col, detail_col = st.columns([1.5, 1])
    with chart_col:
        st.markdown('<div class="section-label">Comparación de resultados</div>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(8, 4.2))
        fig.patch.set_facecolor("#111c2e")
        ax.set_facecolor("#111c2e")
        bars = ax.bar(
            ["Escenario base", "Escenario optimizado"],
            [promedio_base, promedio_opt],
            color=["#64748b", "#38bdf8"],
            width=0.52,
        )
        ax.set_ylabel("Minutos por ciclo", color="#cbd5e1")
        ax.set_title("Tiempo promedio de ciclo", color="#f8fafc", pad=16, fontsize=14, fontweight="bold")
        ax.tick_params(axis="x", colors="#cbd5e1")
        ax.tick_params(axis="y", colors="#94a3b8")
        ax.spines["bottom"].set_color("#475569")
        ax.spines["left"].set_color("#475569")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", alpha=.16, color="#94a3b8")
        ax.set_axisbelow(True)
        for bar, value in zip(bars, [promedio_base, promedio_opt]):
            ax.text(bar.get_x() + bar.get_width()/2, value, f"{value:.2f} min",
                    ha="center", va="bottom", color="#f8fafc", fontweight="bold")
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    with detail_col:
        st.markdown('<div class="section-label">Detalle por camión</div>', unsafe_allow_html=True)
        st.dataframe(
            {
                "Camión": [f"Camión {i+1}" for i in range(camiones)],
                "Carguío (min)": np.round(t_carg, 2),
                "Transporte (min)": np.round(t_trans, 2),
                "Ciclo base (min)": np.round(total_base, 2),
                "Ciclo optimizado (min)": np.round(total_opt, 2),
            },
            use_container_width=True,
            hide_index=True,
        )

st.markdown(
    '<div class="footer">OptiRoute · Simulación referencial para análisis operacional minero</div>',
    unsafe_allow_html=True,
)
