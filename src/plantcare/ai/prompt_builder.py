
"""Build grounded prompts for PlantCare AI."""

from collections.abc import Mapping, Sequence
from typing import Any

from plantcare.tree.node import DiagnosisNode


def build_diagnostic_prompt(
    diagnosis: DiagnosisNode,
    catalogue: Mapping[str, Mapping[str, Any]],
    *,
    case_observations: Sequence[str] = (),
    decision_paths: Sequence[str] = (),
) -> str:
    """Build a prompt from diagnosed problems and catalogue records."""

    if not diagnosis.problem_codes:
        raise ValueError("Diagnosis must contain at least one problem.")

    records: list[str] = []

    for code in diagnosis.problem_codes:
        problem = catalogue.get(code)

        if problem is None:
            raise ValueError(
                f"Problem not found in catalogue: {code}"
            )

        records.append(
            f"CODIGO: {code}\n"
            f"NOMBRE EXACTO: {problem['name']}\n"
            f"SINTOMAS: {problem['indicative_symptoms']}\n"
            "MANEJO NO QUIMICO: "
            f"{problem['organic_or_nonchemical_management']}"
        )

    knowledge = "\n\n".join(records)
    observations = "\n".join(f"- {item}" for item in case_observations)
    paths = "\n".join(f"- {path}" for path in decision_paths)

    return f"""
Eres el asistente explicativo de PlantCare Tree.

El arbol binario ya determino los posibles problemas.
Tu responsabilidad NO es diagnosticar nuevamente.

REGLAS OBLIGATORIAS:
1. Conserva exactamente los codigos y nombres recibidos.
2. No agregues ni elimines problemas.
3. No intercambies datos entre problemas.
4. No inventes causas, tratamientos, productos ni dosis.
5. Explica solamente lo documentado en las fichas.
6. Conserva expresiones de incertidumbre como "a veces".
7. Responde en espanol claro y comprensible.
8. Organiza cada problema en una seccion independiente.
9. No atribuyas otros sintomas al usuario ni propongas nuevas soluciones.
10. La ruta del arbol describe decisiones internas, no hechos clinicos nuevos.

OBSERVACIONES REPORTADAS POR EL USUARIO:
{observations if observations else "No se proporcionaron observaciones adicionales."}

RECORRIDO BINARIO DE LA OBSERVACION (TRAZABILIDAD):
{paths if paths else "No se proporciono una ruta."}

FICHAS DEL CATALOGO:
{knowledge}

FORMATO:
Para cada problema presenta:
- Codigo y nombre exacto.
- Sintomas de referencia.
- Recomendaciones de manejo no quimico.

Termina con esta advertencia exacta:
"Este resultado es orientativo y no sustituye una evaluacion
especializada de la planta."
""".strip()
