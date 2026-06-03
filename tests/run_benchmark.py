# tests/run_benchmark.py
"""
Benchmark de Rendimiento, Coste y Fiabilidad del Orientador Académico.

Mide latencia (p50/p95), estima coste por 1k requests, audita fiabilidad
y documenta tradeoffs de diseño. Genera informe en consola y en archivo.

Uso:
    python tests/run_benchmark.py

Requiere que el servidor FastAPI esté corriendo en http://127.0.0.1:8000.
"""

import os
import sys
import io
import json
import time
import requests

# Forzar codificación UTF-8 en salida (Windows cp1252 no soporta caracteres especiales)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Constantes ────────────────────────────────────────────────────────────────
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
TEST_CASES_PATH = os.path.join(os.path.dirname(__file__), "test_cases.jsonl")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Tests_Results")
README_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md")

COST_PER_TOKEN = 0.0003  # €/token (supuesto del profesor)
REQUEST_DELAY = 0.3      # segundos entre peticiones (rate limit)
REQUEST_TIMEOUT = 30     # segundos de timeout por petición


# ── Helpers de formato ────────────────────────────────────────────────────────
def print_banner(text):
    """Imprime un banner centrado con bordes."""
    print("\n" + "═" * 60)
    print(f"  {text}")
    print("═" * 60)


def print_section(title):
    """Imprime un separador de sección."""
    print(f"\n── {title} " + "─" * max(0, 55 - len(title)))


# ── Fase 1: Health Check ─────────────────────────────────────────────────────
def check_server_health():
    """
    Verifica la conexión con el servidor y devuelve la info de configuración.

    Returns:
        dict con claves: provider, azure_configured, status
    Raises:
        SystemExit si no se puede conectar.
    """
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        if r.status_code != 200:
            print(f"  [✗] El servidor respondió con código {r.status_code}")
            sys.exit(1)
        return r.json()
    except requests.ConnectionError:
        print(f"  [✗] No se puede conectar con {API_URL}")
        print("      Asegúrate de que el servidor FastAPI está corriendo.")
        print("      Ejemplo: uvicorn backend.server:app --host 127.0.0.1 --port 8000")
        sys.exit(1)
    except requests.Timeout:
        print(f"  [✗] Timeout al conectar con {API_URL}")
        sys.exit(1)
    except Exception as e:
        print(f"  [✗] Error inesperado: {e}")
        sys.exit(1)


def load_test_cases():
    """
    Carga los casos de prueba desde test_cases.jsonl.
    Filtra el caso tc25 (input vacío) que no es válido para benchmarking.

    Returns:
        list de dicts con los casos de prueba válidos.
    """
    if not os.path.exists(TEST_CASES_PATH):
        print(f"  [✗] No se encontró {TEST_CASES_PATH}")
        sys.exit(1)

    cases = []
    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            case = json.loads(line)
            # Excluir tc25 (input vacío/inválido — no sirve para benchmark de latencia)
            if case.get("expected", {}).get("status_code") == 400:
                continue
            cases.append(case)

    return cases


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    print_banner("BENCHMARK — ORIENTADOR ACADÉMICO")

    # 1. Health check
    health = check_server_health()
    provider = health.get("provider", "desconocido")
    azure_ok = health.get("azure_configured", False)

    # 2. Cargar casos
    cases = load_test_cases()

    # 3. Cabecera del informe
    print(f"  Fecha:     {timestamp}")
    print(f"  Provider:  {provider}")
    print(f"  Modelo:    DeepSeek-V4-Flash")
    print(f"  Azure:     {'✅ configurado' if azure_ok else '⚠️  no configurado'}")
    print(f"  Casos:     {len(cases)} prompts cargados")
    print(f"  Timeout:   {REQUEST_TIMEOUT}s por petición")
    print(f"  Tarifa:    {COST_PER_TOKEN} €/token")

    if provider == "mock":
        print()
        print("  ⚠️  Ejecutando contra MOCK — las métricas de latencia y")
        print("     tokens no reflejan rendimiento real de Azure.")

    print("═" * 60)

    # ── Aquí se añadirán las fases 2-6 ────────────────────────────────────

    print_section("FIN DEL BENCHMARK")
    print("  Fase 1 completada. Fases 2-6 pendientes de implementar.")
    print("─" * 60)


if __name__ == "__main__":
    main()
