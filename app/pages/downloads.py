"""Yellowbird Telemetry — Downloads Tab.

Renders JSON and HTML report download buttons.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st

from src.common.exceptions import ExportError
from src.services.export_service import ProfilingReport, generate_html_report


def render_downloads(report: ProfilingReport) -> None:
    """Render the Downloads tab content.

    Args:
        report: The completed profiling report.
    """
    try:
        st.markdown(
            '<div class="section-tag">Descargar Informe</div>',
            unsafe_allow_html=True,
        )

        dl1, dl2 = st.columns(2)

        with dl1:
            st.markdown("**Informe JSON** (datos completos)")
            st.download_button(
                label="Descargar JSON",
                data=report.to_json(),
                file_name=(
                    f"yellowbird_audit_{Path(report.file_path).stem}"
                    f"_{datetime.now().strftime('%Y%m%d')}.json"
                ),
                mime="application/json",
                use_container_width=True,
            )

        with dl2:
            st.markdown("**Informe HTML** (para compartir con el cliente)")
            html_report = generate_html_report(report)
            st.download_button(
                label="Descargar HTML",
                data=html_report,
                file_name=(
                    f"yellowbird_audit_{Path(report.file_path).stem}"
                    f"_{datetime.now().strftime('%Y%m%d')}.html"
                ),
                mime="text/html",
                use_container_width=True,
            )

    except ExportError as exc:
        st.error(
            f"Error al generar el informe para descarga: {exc}\n\n"
            "Intente de nuevo o descargue en el otro formato."
        )
