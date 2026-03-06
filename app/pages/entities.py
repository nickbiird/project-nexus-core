"""Yellowbird Telemetry — Entities Tab.

Renders entity deduplication analysis: per-column cluster tables
showing canonical names, variants, similarity scores, and confidence.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.common.exceptions import ProfilingError
from src.services.export_service import ProfilingReport


def render_entities(report: ProfilingReport) -> None:
    """Render the Entities tab content.

    Args:
        report: The completed profiling report.
    """
    try:
        st.markdown(
            '<div class="section-tag">Análisis de Entidades Duplicadas</div>',
            unsafe_allow_html=True,
        )

        if report.entity_analyses:
            for ea in report.entity_analyses:
                st.markdown(f"**Columna: `{ea.column_name}`**")
                st.markdown(
                    f"{ea.raw_unique_count} valores únicos → "
                    f"**{ea.estimated_canonical_count} entidades canónicas** estimadas "
                    f"({ea.duplicate_entity_count} duplicados detectados)"
                )

                if ea.clusters:
                    cluster_data = []
                    for c in ea.clusters[:15]:
                        cluster_data.append(
                            {
                                "Nombre canónico": c.canonical,
                                "Variantes": ", ".join(c.variants[:5]),
                                "Nº variantes": len(c.variants),
                                "Similitud": f"{c.similarity_score:.0f}%",
                                "Confianza": c.confidence.title(),
                            }
                        )
                    st.dataframe(
                        pd.DataFrame(cluster_data),
                        use_container_width=True,
                        hide_index=True,
                    )
                st.divider()
        else:
            st.info("No se detectaron columnas de entidades en estos datos.")

    except ProfilingError as exc:
        st.error(
            f"Error al renderizar el análisis de entidades: {exc}\n\n"
            "Verifique que el archivo contenga columnas de tipo texto."
        )
