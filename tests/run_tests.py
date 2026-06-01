# tests/run_tests.py
"""
Script ejecutable independiente para el Orientador Académico.
1. Valida la conexión con el servidor.
2. Ejecuta secuencialmente los 25 casos de tests/test_cases.jsonl.
3. Evalúa la métrica Tasa de Respuesta Correcta (Accuracy General) por caso y global.
4. Muestra una tabla premium de resultados en la consola.
5. Guarda las evidencias en Tests_Results/V13_eval_evidence.json y Tests_Results/calidad_eval_results.csv.
"""

import os
import sys
import json
import csv
import time
import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
TEST_CASES_PATH = os.path.join(os.path.dirname(__file__), "test_cases.jsonl")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Tests_Results")

def print_banner(text):
    print("\n" + "="*80)
    print(f" {text} ".center(80, "="))
    print("="*80)

def main():
    print_banner("INICIO DE PRUEBAS DE CALIDAD - ORIENTADOR ACADÉMICO")
    
    # 0. Verificar salud del servidor
    try:
        r_health = requests.get(f"{API_URL}/health", timeout=5)
        if r_health.status_code != 200:
            print(f"[-] ERROR: El endpoint de salud respondió con código {r_health.status_code}")
            sys.exit(1)
        health_data = r_health.json()
        print(f"[+] Conexión establecida con el servidor API.")
        print(f"[+] Proveedor activo: {health_data.get('provider', 'desconocido')}")
        print(f"[+] Azure configurado: {health_data.get('azure_configured', False)}")
    except Exception as e:
        print(f"[-] ERROR DE CONEXIÓN: No se puede conectar con {API_URL}")
        print("    Asegúrate de que el servidor FastAPI está corriendo (ej. uvicorn backend.server:app).")
        print(f"    Detalle: {e}")
        sys.exit(1)

    # 1. Cargar casos de prueba
    if not os.path.exists(TEST_CASES_PATH):
        print(f"[-] ERROR: No se encontró el archivo de casos en {TEST_CASES_PATH}")
        sys.exit(1)
        
    cases = []
    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
                
    print(f"[+] Se cargaron {len(cases)} casos de prueba desde tests/test_cases.jsonl\n")

    # Crear directorio de resultados si no existe
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # 2. Ejecutar cada caso de prueba y evaluar métrica
    results = []
    passed_cases = 0
    
    print(f"{'ID':<6} | {'Categoría':<16} | {'Estado':<10} | {'Latencia':<8} | {'Confianza':<9} | {'Accuracy General':<15}")
    print("-" * 80)
    
    for case in cases:
        cid = case["id"]
        inp = case["input"]
        expected = case["expected"]
        notes = case["notes"]
        
        t0 = time.time()
        
        status_ok = False
        error_details = []
        response_data = None
        status_code = None
        
        try:
            # Petición a /predict
            r = requests.post(f"{API_URL}/predict", json={"input": inp}, timeout=30)
            status_code = r.status_code
            response_data = r.json()
        except Exception as e:
            error_details.append(f"Error de petición: {e}")
            
        latency_ms = int((time.time() - t0) * 1000)
        
        # Evaluar métrica AQCIQ
        c_contract = False
        c_intent = False
        c_quality = False
        
        category_shown = "N/A"
        confidence_shown = "N/A"
        
        if response_data:
            if "status_code" in expected and expected["status_code"] == 400:
                # Caso esperado de error HTTP 400
                c_contract = (status_code == 400) and (response_data.get("ok") is False) and ("error" in response_data)
                c_intent = response_data.get("error", {}).get("code") == expected["error_code"] if c_contract else False
                c_quality = "message" in response_data.get("error", {}) if c_contract else False
                
                category_shown = "error (400)"
                confidence_shown = "N/A"
            else:
                # Caso estándar
                if status_code == 200 and response_data.get("ok") is True:
                    output = response_data.get("output", {})
                    meta = response_data.get("meta", {})
                    
                    # 1. Contrato
                    req_out_keys = {"ok", "answer", "category", "confidence", "error"}
                    req_meta_keys = {"provider", "deployment", "latency_ms", "prompt_tokens", "completion_tokens", "total_tokens", "request_id"}
                    
                    has_out_keys = all(k in output for k in req_out_keys)
                    has_meta_keys = all(k in meta for k in req_meta_keys)
                    
                    c_contract = has_out_keys and has_meta_keys
                    if not c_contract:
                        error_details.append("Faltan claves requeridas en JSON (output o meta)")
                    
                    # 2. Intención / Negocio
                    if c_contract:
                        category_shown = output.get("category", "")
                        confidence_val = output.get("confidence", 0.0)
                        confidence_shown = f"{confidence_val * 100:.1f}%"
                        
                        expected_cat = expected["category"].lower().replace("á", "a").replace("ó", "o").replace("í", "i")
                        actual_cat = category_shown.lower().replace("á", "a").replace("ó", "o").replace("í", "i")
                        
                        cat_ok = (actual_cat == expected_cat)
                        ok_field_ok = (output.get("ok") == expected["ok"])
                        error_field_ok = (output.get("error") == expected["error"])
                        
                        if not expected["ok"]:
                            confidence_ok = (confidence_val <= 0.3)
                        else:
                            confidence_ok = (confidence_val >= 0.7)
                            
                        c_intent = cat_ok and ok_field_ok and error_field_ok and confidence_ok
                        if not c_intent:
                            if not cat_ok: error_details.append(f"Categoría incorrecta (esperaba: {expected['category']}, obtuvo: {category_shown})")
                            if not ok_field_ok: error_details.append(f"ok incorrecto (esperaba: {expected['ok']}, obtuvo: {output.get('ok')})")
                            if not error_field_ok: error_details.append(f"error incorrecto (esperaba: {expected['error']}, obtuvo: {output.get('error')})")
                            if not confidence_ok: error_details.append(f"Confianza fuera de rango para el caso (obtuvo: {confidence_val})")
                    
                    # 3. Calidad de respuesta
                    if c_contract:
                        ans = output.get("answer", "").strip()
                        c_quality = len(ans) >= 15
                        if not c_quality:
                            error_details.append(f"Respuesta demasiado corta ({len(ans)} caracteres)")
                else:
                    error_details.append(f"Respuesta HTTP {status_code} no exitosa o sin campo ok=True")
        
        # El caso es exitoso en la métrica si cumple los 3 criterios
        case_passed = c_contract and c_intent and c_quality
        if case_passed:
            passed_cases += 1
            metric_str = "PASS (1.0)"
            status_text = "PASS"
        else:
            metric_str = "FAIL (0.0)"
            status_text = "FAIL"
            
        print(f"{cid:<6} | {category_shown[:16]:<16} | {status_text:<10} | {latency_ms:<5} ms | {confidence_shown:<9} | {metric_str:<15}")
        
        # Guardar para reporte de evidencias
        results.append({
            "id": cid,
            "input": inp,
            "expected": expected,
            "response": response_data,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "metric_score": 1.0 if case_passed else 0.0,
            "checks": {
                "contract": c_contract,
                "intent": c_intent,
                "quality": c_quality
            },
            "errors": error_details,
            "notes": notes
        })
        
        # Pequeña pausa para no sobrecargar si se usa Azure
        time.sleep(0.1)

    print("-" * 80)
    
    # 3. Calcular métrica global
    total_cases = len(cases)
    global_score = (passed_cases / total_cases) * 100 if total_cases > 0 else 0.0
    
    print(f"\n[+] Resultados Globales:")
    print(f"    - Casos totales:  {total_cases}")
    print(f"    - Casos exitosos: {passed_cases}")
    print(f"    - Accuracy General: {global_score:.2f}%")
    print("="*80)

    # 4. Guardar archivo de evidencias (JSON - V13_eval_evidence.json)
    evidence_json_path = os.path.join(RESULTS_DIR, "V13_eval_evidence.json")
    with open(evidence_json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[+] Evidencia JSON guardada en: Tests_Results/V13_eval_evidence.json")

    # 5. Guardar reporte CSV (calidad_eval_results.csv)
    evidence_csv_path = os.path.join(RESULTS_DIR, "calidad_eval_results.csv")
    with open(evidence_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "input", "expected_category", "actual_category", "status_code", "latency_ms", "score", "passed", "errors"])
        for res in results:
            act_cat = "N/A"
            if res["response"] and "output" in res["response"]:
                act_cat = res["response"]["output"].get("category", "N/A")
            elif res["status_code"] == 400:
                act_cat = "INVALID_INPUT"
                
            writer.writerow([
                res["id"],
                res["input"],
                res["expected"].get("category", "INVALID_INPUT"),
                act_cat,
                res["status_code"],
                res["latency_ms"],
                res["metric_score"],
                "OK" if res["metric_score"] == 1.0 else "FAIL",
                "; ".join(res["errors"])
            ])
    print(f"[+] Evidencia CSV guardada en: Tests_Results/calidad_eval_results.csv")

if __name__ == "__main__":
    main()
