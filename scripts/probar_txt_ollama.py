"""Demonstrate grounded TXT knowledge and deterministic local fallback.

Run: python -m scripts.probar_txt_ollama --code PC-022 --mode offline
     python -m scripts.probar_txt_ollama --code PC-022 --mode live
"""

import argparse
from pathlib import Path

from plantcare.ai.txt_knowledge import (
    load_txt_knowledge,
    reference_response,
    safe_response,
)

ROOT = Path(__file__).resolve().parents[1]
TXT_PATH = ROOT / "data" / "plantcare_respuestas_referencia.txt"


def main() -> None:
    """Compare actual or simulated Llama outputs with a TXT reference."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", default="PC-022")
    parser.add_argument("--mode", choices=("offline", "incorrect", "live"),
                        default="offline")
    arguments = parser.parse_args()

    records = load_txt_knowledge(TXT_PATH)
    exact = reference_response(arguments.code, records)
    print(f"Catalogo TXT cargado: {len(records)} fichas", flush=True)
    print(f"Problema solicitado: {arguments.code}", flush=True)
    print(f"Escenario: {arguments.mode}", flush=True)

    raw_response: str | None = None
    if arguments.mode == "incorrect":
        raw_response = "Tratamiento inventado no incluido en el TXT."
    elif arguments.mode == "live":
        from plantcare.ai.ollama_client import OllamaClient, OllamaClientError

        prompt = (
            "Copia EXACTAMENTE el siguiente texto, incluyendo signos y saltos "
            "de linea. No uses Markdown ni agregues comentarios.\n\n"
            + exact
        )
        try:
            print("Consultando Ollama local...", flush=True)
            raw_response = OllamaClient().generate_explanation(prompt)
            print("\nRESPUESTA DE LLAMA (SIN VERIFICAR):\n")
            print(raw_response)
        except OllamaClientError as error:
            print(f"Ollama no disponible: {error}")

    answer, copied = safe_response(arguments.code, records, raw_response)
    print("\nCOMPARACION CON TXT:")
    print("Copia literal de Llama:", "SI" if copied else "NO")
    print("Fuente del resultado:", "TXT local (texto original)")
    print("\nRESPUESTA FINAL SEGURA:\n")
    print(answer)


if __name__ == "__main__":
    main()
