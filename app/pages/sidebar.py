"""Yellowbird Telemetry — Sidebar & Data Input Panel.

Renders the sidebar controls (similarity slider, fast-mode toggle,
demo button, branding) and the main-area upload / profiling flow.
After a successful audit, pre-computed metrics are stored in
``AppState`` for consumption by tab renderers.
"""

from __future__ import annotations

import time

import streamlit as st

from app.state import AppState
from app.theme import GOLD, SLATE_LIGHT, render_header
from src.common.exceptions import IngestionError, PersistenceError, ProfilingError
from src.db import get_session
from src.services.audit_service import process_audit_upload
from src.services.demo_service import generate_demo_data
from src.services.export_service import (
    compute_total_anomaly_count,
)

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────

MAX_FILE_SIZE_MB: int = 50


def render_sidebar(state: AppState) -> None:
    """Render the sidebar controls and the main-area upload flow.

    This function owns the complete "data input" surface: the sidebar
    widgets (similarity slider, fast-mode toggle, demo button, branding)
    **and** the main-area file uploader, validation, profiling
    invocation, and post-profiling metric computation.

    After a successful audit the pre-computed ``gross_revenue`` and
    ``total_anomaly_count`` values are stored in *state* so that tab
    renderers receive them without performing any computation.

    Args:
        state: The typed session-state wrapper for the dashboard.
    """
    # ── Sidebar widgets ───────────────────────────────────────
    with st.sidebar:
        st.markdown("### Configuración")

        _fuzzy_threshold = st.slider(
            "Umbral de similitud (entidades)",
            min_value=60,
            max_value=95,
            value=82,
            step=1,
            help="Valores más altos = coincidencias más estrictas. 82 es un buen equilibrio.",
        )

        _fast_mode = st.toggle(
            "Modo rápido",
            value=False,
            help="Omite el análisis de casi-duplicados (más rápido en archivos grandes).",
        )

        st.divider()

        st.markdown(
            '<p class="trust-text">'
            "🔒 Sus datos no se almacenan. El archivo se procesa en memoria "
            "y se descarta al cerrar esta sesión. Cumplimiento RGPD."
            "</p>",
            unsafe_allow_html=True,
        )

        st.divider()

        st.markdown("##### Datos de demostración")
        demo_clicked = st.button("Generar datos de ejemplo", use_container_width=True)

        st.divider()
        st.markdown(
            f'<div style="text-align:center; color:{SLATE_LIGHT}; font-size:0.72rem;">'
            f"Yellowbird<span style='color:{GOLD};'>.</span> Telemetry<br>"
            f"© 2026 · v2.0.0</div>",
            unsafe_allow_html=True,
        )

    # ── Main-area header & upload ─────────────────────────────
    st.markdown(render_header(), unsafe_allow_html=True)

    st.markdown(
        '<div class="section-tag">Paso 1 · Suba su archivo</div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Seleccione un archivo Excel o CSV",
        type=["xlsx", "xls", "csv"],
        help="Aceptamos cualquier archivo de datos. No necesita limpiarlo previamente.",
        label_visibility="collapsed",
    )

    # ── Handle demo data generation ───────────────────────────
    if demo_clicked:
        state.set_demo_df(generate_demo_data())
        state.clear_report()
        st.rerun()

    # ── Determine what to profile ─────────────────────────────
    file_to_profile: object | None = None
    file_name: str | None = None

    if uploaded_file is not None:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            st.error(
                f"El archivo es demasiado grande ({file_size_mb:.1f} MB). "
                f"Máximo: {MAX_FILE_SIZE_MB} MB."
            )
            st.stop()
        file_to_profile = uploaded_file
        file_name = uploaded_file.name
        state.clear_demo_df()
    elif state.has_demo_df():
        file_to_profile = "demo"
        file_name = "demo_logistics_data.xlsx"

    # ── Run profiling ─────────────────────────────────────────
    if file_to_profile is not None:
        run_button = st.button("Ejecutar Auditoría", use_container_width=True, type="primary")

        if run_button or state.has_report():
            if run_button:
                _execute_profiling(state, file_to_profile, file_name or "")

            # Store pre-computed metrics for tab renderers
            report = state.get_report()
            if report is not None:
                state.set_gross_revenue(report.total_gross_revenue)
                state.set_total_anomaly_count(compute_total_anomaly_count(report))
    else:
        _render_landing()


# ──────────────────────────────────────────────────────────────
# Private helpers
# ──────────────────────────────────────────────────────────────


def _execute_profiling(
    state: AppState,
    file_to_profile: object,
    file_name: str,
) -> None:
    """Run the profiling pipeline and store results in *state*.

    Args:
        state: Typed session-state wrapper.
        file_to_profile: The uploaded file object or the literal
            string ``"demo"``.
        file_name: Display name for the file being profiled.
    """
    import tempfile
    from pathlib import Path

    from src.services.export_service import profile_excel

    with st.spinner("Analizando sus datos..."):
        start = time.time()
        progress = st.progress(0, text="Cargando archivo...")

        try:
            if file_to_profile == "demo":
                # Demo path — does NOT go through the database
                demo_df = state.get_demo_df()
                if demo_df is None:
                    st.error("No hay datos de demostración cargados.")
                    return
                with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                    demo_df.to_excel(tmp.name, index=False)
                    tmp_path = Path(tmp.name)

                progress.progress(30, text="Detectando esquema...")
                report = profile_excel(tmp_path)
                report.file_path = file_name
                elapsed = time.time() - start
                report.processing_time_seconds = round(elapsed, 2)

                try:  # noqa: SIM105
                    tmp_path.unlink()
                except OSError:
                    pass

            else:
                # Real upload path — goes through audit service + database
                file_bytes: bytes = file_to_profile.getvalue()  # type: ignore[union-attr]

                def _progress_cb(pct: int, msg: str) -> None:
                    progress.progress(pct, text=msg)

                with get_session() as session:
                    report = process_audit_upload(
                        session,
                        file_name,
                        file_bytes,
                        on_progress=_progress_cb,
                    )

            state.set_report(report)
            progress.progress(100, text="Completado.")
            time.sleep(0.3)
            progress.empty()

        except IngestionError as exc:
            st.error(
                f"Error al leer el archivo: {exc}\n\n"
                "Asegúrese de que el archivo es un Excel (.xlsx/.xls) o CSV válido."
            )
            st.stop()
        except ProfilingError as exc:
            st.error(
                f"Error en el motor de análisis: {exc}\n\n"
                "El archivo puede contener un formato no soportado."
            )
            st.stop()
        except PersistenceError as exc:
            st.error(
                f"Error al guardar los resultados: {exc}\n\n"
                "Inténtelo de nuevo. Si el problema persiste, contacte soporte."
            )
            st.stop()


def _render_landing() -> None:
    """Render the empty-state landing page."""
    st.markdown(
        """
    <div style="text-align:center; padding:3rem 1rem;">
        <p style="font-size:1.1rem; color:rgba(255,255,255,0.75); max-width:500px; margin:0 auto 1.5rem;">
            Suba un archivo Excel o CSV con sus datos operativos.
            No necesita limpiarlo. Aceptamos cualquier formato.
        </p>
        <p style="color:rgba(160,174,192,0.7); font-size:0.85rem;">
            O pulse <strong>Generar datos de ejemplo</strong> en la barra lateral para una demostración instantánea.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<p class="trust-text">'
        "🔒 Sus datos se procesan exclusivamente en memoria. No se almacena nada. "
        "Sin cookies. Sin seguimiento. Cumplimiento RGPD."
        "</p>",
        unsafe_allow_html=True,
    )
