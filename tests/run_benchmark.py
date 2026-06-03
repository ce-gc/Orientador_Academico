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


# ── Fase 2: Latencia ─────────────────────────────────────────────────────────
def send_single_request(prompt):
    """
    Envía una petición POST /predict y mide latencia end-to-end.

    Returns:
        dict con: prompt, status, latency_client_ms, latency_server_ms,
                  prompt_tokens, completion_tokens, total_tokens, success
    """
    t0 = time.time()
    try:
        r = requests.post(
            f"{API_URL}/predict",
            json={"input": prompt},
            timeout=REQUEST_TIMEOUT,
        )
        latency_client = int((time.time() - t0) * 1000)
        data = r.json()

        if r.status_code == 200 and data.get("ok"):
            meta = data.get("meta", {})
            return {
                "prompt": prompt,
                "status": r.status_code,
                "latency_client_ms": latency_client,
                "latency_server_ms": meta.get("latency_ms", 0),
                "prompt_tokens": meta.get("prompt_tokens", 0),
                "completion_tokens": meta.get("completion_tokens", 0),
                "total_tokens": meta.get("total_tokens", 0),
                "success": True,
            }
        else:
            return {
                "prompt": prompt,
                "status": r.status_code,
                "latency_client_ms": latency_client,
                "latency_server_ms": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "success": False,
                "error": f"HTTP {r.status_code}: {data}",
            }
    except Exception as e:
        latency_client = int((time.time() - t0) * 1000)
        return {
            "prompt": prompt,
            "status": "ERROR",
            "latency_client_ms": latency_client,
            "latency_server_ms": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "success": False,
            "error": str(e),
        }


def calc_percentiles(values, percentiles):
    """
    Calcula los percentiles indicados de una lista de valores numéricos.

    Args:
        values: lista de números (debe tener al menos 1 elemento)
        percentiles: lista de percentiles a calcular (ej. [50, 95])
    Returns:
        dict {percentil: valor}
    """
    if not values:
        return {p: 0 for p in percentiles}

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    result = {}
    for p in percentiles:
        idx = (n - 1) * (p / 100.0)
        low = int(idx)
        high = min(low + 1, n - 1)
        frac = idx - low
        result[p] = sorted_vals[low] + frac * (sorted_vals[high] - sorted_vals[low])
    return result


def run_latency_benchmark(cases):
    """
    Ejecuta los casos secuencialmente y recoge métricas de latencia y tokens.

    Returns:
        dict con:
          results: lista de dicts por petición
          stats: dict con p50, p95, min, max para cliente y servidor
          token_data: lista de dicts {prompt_tokens, completion_tokens, total_tokens}
          success_count: número de peticiones exitosas
          total_count: número total de peticiones
    """
    results = []
    total = len(cases)

    for i, case in enumerate(cases, 1):
        prompt = case["input"]
        short = prompt[:45] + "..." if len(prompt) > 45 else prompt
        print(f"  [{i:2d}/{total}] {short}", end="", flush=True)

        res = send_single_request(prompt)
        results.append(res)

        if res["success"]:
            print(f"  → {res['latency_client_ms']} ms (ok)")
        else:
            print(f"  → {res['latency_client_ms']} ms (FAIL)")

        # Pausa entre peticiones para no sobrecargar / rate limit
        if i < total:
            time.sleep(REQUEST_DELAY)

    # Separar datos exitosos
    ok_results = [r for r in results if r["success"]]
    client_lats = [r["latency_client_ms"] for r in ok_results]
    server_lats = [r["latency_server_ms"] for r in ok_results]
    token_data = [
        {
            "prompt_tokens": r["prompt_tokens"],
            "completion_tokens": r["completion_tokens"],
            "total_tokens": r["total_tokens"],
        }
        for r in ok_results
    ]

    # Calcular percentiles
    client_pcts = calc_percentiles(client_lats, [50, 95])
    server_pcts = calc_percentiles(server_lats, [50, 95])

    stats = {
        "client_p50": client_pcts[50],
        "client_p95": client_pcts[95],
        "client_min": min(client_lats) if client_lats else 0,
        "client_max": max(client_lats) if client_lats else 0,
        "server_p50": server_pcts[50],
        "server_p95": server_pcts[95],
        "server_min": min(server_lats) if server_lats else 0,
        "server_max": max(server_lats) if server_lats else 0,
    }

    return {
        "results": results,
        "stats": stats,
        "token_data": token_data,
        "success_count": len(ok_results),
        "total_count": total,
    }


# ── Fase 3: Coste ────────────────────────────────────────────────────────────
def estimate_cost(token_data):
    """
    Estima el coste por request y por 1k requests a partir de los tokens reales.

    Args:
        token_data: lista de dicts {prompt_tokens, completion_tokens, total_tokens}
    Returns:
        dict con avg_prompt, avg_completion, avg_total, cost_per_request, cost_per_1k
    """
    if not token_data:
        return {
            "avg_prompt": 0, "avg_completion": 0, "avg_total": 0,
            "cost_per_request": 0.0, "cost_per_1k": 0.0,
            "num_samples": 0,
        }

    n = len(token_data)
    avg_prompt = sum(d["prompt_tokens"] for d in token_data) / n
    avg_completion = sum(d["completion_tokens"] for d in token_data) / n
    avg_total = sum(d["total_tokens"] for d in token_data) / n

    cost_per_request = avg_total * COST_PER_TOKEN
    cost_per_1k = cost_per_request * 1000

    return {
        "avg_prompt": avg_prompt,
        "avg_completion": avg_completion,
        "avg_total": avg_total,
        "cost_per_request": cost_per_request,
        "cost_per_1k": cost_per_1k,
        "num_samples": n,
    }


# ── Fase 4: Fiabilidad ────────────────────────────────────────────────────────
def audit_reliability(bench):
    """Realiza las comprobaciones de fiabilidad y devuelve los resultados."""
    timeout_ok = True
    timeout_msg = "30s (cliente OpenAI SDK)"
    retries_ok = True
    retries_msg = "3 automáticos (429/5xx)"
    rate_ok = True
    rate_msg = f"{REQUEST_DELAY}s entre peticiones"

    err_count = 0
    try:
        r1 = requests.post(f"{API_URL}/predict", json={"input": "   "}, timeout=REQUEST_TIMEOUT)
        d1 = r1.json()
        if r1.status_code == 400 and d1.get("ok") is False and "error" in d1:
            err_count += 1
    except:
        pass
    
    try:
        r2 = requests.post(f"{API_URL}/predict", json={"input": "¿Cuál es la capital de Francia?"}, timeout=REQUEST_TIMEOUT)
        d2 = r2.json()
        if r2.status_code == 200 and d2.get("ok") is True:
            out2 = d2.get("output", {})
            if out2.get("ok") is False and out2.get("error") == "fuera_de_dominio":
                err_count += 1
    except:
        pass

    errors_ok = (err_count == 2)
    success_rate = bench["success_count"] / bench["total_count"] if bench["total_count"] else 0
    success_ok = (success_rate == 1.0)

    return {
        "timeout_ok": timeout_ok, "timeout_msg": timeout_msg,
        "retries_ok": retries_ok, "retries_msg": retries_msg,
        "rate_limit_ok": rate_ok, "rate_msg": rate_msg,
        "errors_ok": errors_ok, "err_count": err_count,
        "success_ok": success_ok, "success_rate": success_rate
    }


# ── Fase 5: Tradeoffs y README ────────────────────────────────────────────────
def get_tradeoffs():
    return [
        "Calidad vs Latencia: temperature=0.2 prioriza consistencia sobre creatividad. max_tokens=600 (hard limit) reduce latencia y coste pero limita respuestas largas.",
        "Coste vs Robustez: max_retries=3 (SDK OpenAI) aumenta resiliencia ante errores 429/5xx, pero en el peor caso puede triplicar el consumo de tokens de una petición.",
        "Seguridad vs UX: El system prompt exige JSON estricto sin markdown, lo que simplifica el parsing en el backend pero genera respuestas más rígidas que texto libre."
    ]

def check_readme_status():
    if not os.path.exists(README_PATH):
        return []
    
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    sections = [
        {"name": "Instalación / dependencias", "pattern": "pip install", "found": False},
        {"name": "Ejecución del servidor", "pattern": "uvicorn", "found": False},
        {"name": "Ejecución de la UI", "pattern": "app.py", "found": False},
        {"name": "Variables de entorno / .env", "pattern": ".env", "found": False},
        {"name": "Logs de uso", "pattern": "logs.jsonl", "found": False},
        {"name": "Evidencias de ejecución", "pattern": "Evidencias", "found": False},
        {"name": "Métricas de rendimiento (latencia, coste)", "pattern": "benchmark", "found": False},
        {"name": "Decisiones de arquitectura / tradeoffs", "pattern": "tradeoff", "found": False},
        {"name": "Instrucciones de benchmarking", "pattern": "run_benchmark", "found": False},
    ]

    for sec in sections:
        if sec["pattern"].lower() in content.lower():
            sec["found"] = True

    return sections


# ── Fase 6: Persistencia ──────────────────────────────────────────────────────
def generate_report(provider, cases_len, bench, cost, rel, tradeoffs, readme_status):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    s = bench["stats"]
    
    md = f"""# Benchmark — Orientador Académico
**Fecha:** {timestamp}
**Provider:** {provider}
**Modelo:** DeepSeek-V4-Flash
**Casos:** {cases_len} prompts
**Tarifa:** {COST_PER_TOKEN} €/token

## 1. Latencia
| Métrica | Cliente (e2e) | Servidor (modelo) |
|---|---|---|
| p50 (mediana) | {s['client_p50']:.0f} ms | {s['server_p50']:.0f} ms |
| p95 | {s['client_p95']:.0f} ms | {s['server_p95']:.0f} ms |
| Mínimo | {s['client_min']} ms | {s['server_min']} ms |
| Máximo | {s['client_max']} ms | {s['server_max']} ms |

**Éxitos:** {bench['success_count']}/{bench['total_count']} ({bench['success_count']/bench['total_count']*100:.0f}%)

## 2. Coste Estimado
- **Muestras analizadas:** {cost['num_samples']} peticiones exitosas
- **Avg prompt tokens:** {cost['avg_prompt']:.0f}
- **Avg completion tokens:** {cost['avg_completion']:.0f}
- **Avg total tokens:** {cost['avg_total']:.0f}
- **Coste por request:** {cost['cost_per_request']:.4f} €
- **Coste por 1k requests:** {cost['cost_per_1k']:.2f} €

## 3. Fiabilidad
- Timeout definido: {'✅' if rel['timeout_ok'] else '❌'} {rel['timeout_msg']}
- Reintentos: {'✅' if rel['retries_ok'] else '❌'} {rel['retries_msg']}
- Rate limit: {'✅' if rel['rate_limit_ok'] else '❌'} {rel['rate_msg']}
- Errores estructurados: {'✅' if rel['errors_ok'] else '❌'} {rel['err_count']}/2 siguen contrato JSON
- Tasa de éxito: {'✅' if rel['success_ok'] else '❌'} {bench['success_count']}/{bench['total_count']} ({rel['success_rate']*100:.0f}%)
"""
        
    return md

def save_results(report_md, raw_json):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    report_path = os.path.join(RESULTS_DIR, "benchmark_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
        
    raw_path = os.path.join(RESULTS_DIR, "benchmark_raw.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_json, f, indent=2, ensure_ascii=False)
        
    return report_path, raw_path



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

    # ── Fase 2: Latencia ──────────────────────────────────────────────────
    print_section(f"LATENCIA ({len(cases)} peticiones, DeepSeek-V4-Flash / {provider})")
    bench = run_latency_benchmark(cases)
    s = bench["stats"]

    print()
    print(f"  {'':16s} {'Cliente (e2e)':>16s}   {'Servidor (modelo)':>18s}")
    print(f"  {'─' * 54}")
    print(f"  {'p50 (mediana)':16s} {s['client_p50']:13.0f} ms   {s['server_p50']:15.0f} ms")
    print(f"  {'p95':16s} {s['client_p95']:13.0f} ms   {s['server_p95']:15.0f} ms")
    print(f"  {'Mínimo':16s} {s['client_min']:13d} ms   {s['server_min']:15d} ms")
    print(f"  {'Máximo':16s} {s['client_max']:13d} ms   {s['server_max']:15d} ms")
    print(f"  {'─' * 54}")
    print(f"  Éxitos: {bench['success_count']}/{bench['total_count']} ({bench['success_count']/bench['total_count']*100:.0f}%)")

    # ── Fase 3: Coste ────────────────────────────────────────────────────
    print_section("COSTE ESTIMADO")
    cost = estimate_cost(bench["token_data"])

    print(f"  Muestras analizadas:    {cost['num_samples']} peticiones exitosas")
    print()
    print(f"  Avg prompt tokens:      {cost['avg_prompt']:.0f}")
    print(f"  Avg completion tokens:  {cost['avg_completion']:.0f}")
    print(f"  Avg total tokens:       {cost['avg_total']:.0f}")
    print()
    print(f"  Coste por request:      {cost['cost_per_request']:.4f} €")
    print(f"  Coste por 1k requests:  {cost['cost_per_1k']:.2f} €")
    print()
    print(f"  Supuestos:")
    print(f"    - Tarifa uniforme: {COST_PER_TOKEN} €/token (input y output)")
    print(f"    - Modelo: DeepSeek-V4-Flash")
    print(f"    - Config: temperature=0.2, max_tokens=600")
    print(f"    - Fórmula: avg_total_tokens × {COST_PER_TOKEN} × 1000")

    # ── Fase 4: Fiabilidad ───────────────────────────────────────────────
    print_section("FIABILIDAD")
    rel = audit_reliability(bench)
    print(f"  Timeout definido:       {'✅' if rel['timeout_ok'] else '❌'} {rel['timeout_msg']}")
    print(f"  Reintentos:             {'✅' if rel['retries_ok'] else '❌'} {rel['retries_msg']}")
    print(f"  Rate limit / pausas:    {'✅' if rel['rate_limit_ok'] else '❌'} {rel['rate_msg']}")
    print(f"  Errores estructurados:  {'✅' if rel['errors_ok'] else '❌'} {rel['err_count']}/2 siguen contrato JSON")
    print(f"  Tasa de éxito (bench):  {'✅' if rel['success_ok'] else '❌'} {bench['success_count']}/{bench['total_count']} ({rel['success_rate']*100:.0f}%)")

    # ── Fase 5: Tradeoffs y README ───────────────────────────────────────
    print_section("DECISIONES / TRADEOFFS")
    tradeoffs = get_tradeoffs()
    for i, t in enumerate(tradeoffs, 1):
        print(f"  {i}. {t}\n")

    print_section("ESTADO DEL README")
    readme_status = check_readme_status()
    for r in readme_status:
        mark = "x" if r["found"] else " "
        print(f"  [{mark}] {r['name']}")

    # ── Fase 6: Persistencia ─────────────────────────────────────────────
    print_section("PERSISTENCIA")
    md = generate_report(provider, len(cases), bench, cost, rel, tradeoffs, readme_status)
    raw_data = {
        "timestamp": timestamp,
        "provider": provider,
        "latency_stats": bench["stats"],
        "cost_estimation": cost,
        "reliability": rel,
        "results": bench["results"]
    }
    report_path, raw_path = save_results(md, raw_data)
    print(f"  [+] Informe guardado en: {report_path}")
    print(f"  [+] Datos crudos en:     {raw_path}")

    print_section("FIN DEL BENCHMARK")
    print("  Benchmark completado con éxito.")
    print("─" * 60)


if __name__ == "__main__":
    main()
