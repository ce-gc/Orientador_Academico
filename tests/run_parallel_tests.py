# tests/run_parallel_tests.py
"""
Script de utilidad para medir latencia bajo concurrencia.
Lanza peticiones en paralelo a la API de predicción y reporta los tiempos individuales y tokens.
"""

import concurrent.futures
import requests
import time
import sys

API_URL = "http://127.0.0.1:8000/predict"
prompts = [
    "¿Cómo solicito una convalidación?",
    "¿Cuándo empiezan las prácticas de FCT?",
    "¿Cómo puedo acceder al campus virtual?",
    "¿Qué documentación necesito presentar para la matrícula?",
    "¿Cuál es el horario de atención de secretaría?",
    "¿Puedo solicitar un cambio de grupo?"
]

def send_request(prompt):
    t0 = time.time()
    try:
        r = requests.post(API_URL, json={"input": prompt}, timeout=60)
        latency = int((time.time() - t0) * 1000)
        return {"prompt": prompt, "status": r.status_code, "json": r.json(), "latency": latency}
    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        return {"prompt": prompt, "status": "ERROR", "error": str(e), "latency": latency}

def main():
    print(" Lanza Peticiones Concurrentes al Orientador Académico ".center(60, "="))
    print(f"[+] Enviando {len(prompts)} peticiones simultáneas en paralelo...\n")
    
    t_start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(prompts)) as executor:
        results = list(executor.map(send_request, prompts))
    total_elapsed = time.time() - t_start
    
    successful_latencies = []
    
    for i, res in enumerate(results, 1):
        print(f"[{i}] Prompt: {res['prompt']!r}")
        print(f"    Estado HTTP: {res['status']}")
        if res['status'] == 200:
            meta = res['json'].get('meta', {})
            server_latency = meta.get('latency_ms')
            client_latency = res['latency']
            successful_latencies.append(server_latency)
            print(f"    Latencia Cliente: {client_latency} ms | Latencia Servidor (Azure): {server_latency} ms")
            print(f"    Tokens: {meta.get('total_tokens')} (Prompt: {meta.get('prompt_tokens')}, Completion: {meta.get('completion_tokens')})")
        else:
            print(f"    Error: {res.get('error') or res.get('json')}")
        print("-" * 60)
        
    print(f"[+] Ejecución completada en {total_elapsed:.2f} segundos.")
    if successful_latencies:
        successful_latencies.sort()
        n = len(successful_latencies)
        # p50 (mediana)
        if n % 2 == 1:
            p50 = successful_latencies[n // 2]
        else:
            p50 = (successful_latencies[n // 2 - 1] + successful_latencies[n // 2]) / 2
        # p95 (interpolación lineal simple)
        idx = (n - 1) * 0.95
        low = int(idx)
        high = min(low + 1, n - 1)
        p95 = successful_latencies[low] + (idx - low) * (successful_latencies[high] - successful_latencies[low])
        
        print(f"[+] Métricas de esta muestra:")
        print(f"    - Total completadas con éxito: {n}")
        print(f"    - p50 (Mediana): {p50:.1f} ms")
        print(f"    - p95 (Percentil 95): {p95:.1f} ms")
    print("="*60)

if __name__ == "__main__":
    main()
