# tests/test_api.py
"""
Suite de pruebas con Pytest para el contrato y comportamiento de la API REST del Orientador Académico.
Carga dinámicamente los casos de prueba desde tests/test_cases.jsonl.
"""

import os
import json
import pytest
import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
TEST_CASES_PATH = os.path.join(os.path.dirname(__file__), "test_cases.jsonl")

def load_test_cases():
    cases = []
    if not os.path.exists(TEST_CASES_PATH):
        return []
    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases

# Cargar los casos para parametrizar
TEST_CASES = load_test_cases()

def test_health_endpoint():
    """Valida el contrato del endpoint GET /health."""
    r = requests.get(f"{API_URL}/health", timeout=5)
    assert r.status_code == 200, f"Error HTTP {r.status_code}"
    data = r.json()
    assert "status" in data, "Falta el campo 'status' en la respuesta de salud"
    assert data["status"] == "ok", f"El estado de la API no es 'ok': {data['status']}"
    assert "provider" in data, "Falta el campo 'provider' en la respuesta de salud"
    assert "azure_configured" in data, "Falta el campo 'azure_configured' en la respuesta de salud"


@pytest.mark.parametrize("case", TEST_CASES, ids=lambda c: c["id"])
def test_predict_endpoint(case):
    """Valida los casos de prueba cargados contra el endpoint POST /predict."""
    payload = {"input": case["input"]}
    expected = case["expected"]
    
    # Manejar caso esperado de error HTTP 400 (como tc25)
    if "status_code" in expected and expected["status_code"] == 400:
        r = requests.post(f"{API_URL}/predict", json=payload, timeout=30)
        assert r.status_code == 400, f"Se esperaba HTTP 400 pero se obtuvo {r.status_code}"
        data = r.json()
        assert data.get("ok") is False, "El campo 'ok' raíz debería ser False en respuesta de error"
        assert "error" in data, "Falta el campo 'error' en respuesta de error"
        assert data["error"].get("code") == expected["error_code"], f"Código de error incorrecto. Esperado: {expected['error_code']}, Obtenido: {data['error'].get('code')}"
        assert "message" in data["error"], "Falta el mensaje explicativo del error"
        return

    # Casos estándar de éxito HTTP 200
    r = requests.post(f"{API_URL}/predict", json=payload, timeout=30)
    assert r.status_code == 200, f"Error HTTP {r.status_code} al enviar input: {case['input']!r}. Detalle: {r.text}"
    
    data = r.json()
    
    # 1. Validación de esquema raíz
    assert "ok" in data, "El campo raíz 'ok' es obligatorio"
    assert data["ok"] is True, "El campo raíz 'ok' debe ser True para respuestas exitosas"
    assert "output" in data, "El campo raíz 'output' es obligatorio"
    assert "meta" in data, "El campo raíz 'meta' es obligatorio"
    
    # 2. Validación de esquema de output
    output = data["output"]
    assert "ok" in output, "Falta 'output.ok'"
    assert "answer" in output, "Falta 'output.answer'"
    assert "category" in output, "Falta 'output.category'"
    assert "confidence" in output, "Falta 'output.confidence'"
    assert "error" in output, "Falta 'output.error'"
    
    assert isinstance(output["ok"], bool), "'output.ok' debe ser booleano"
    assert isinstance(output["answer"], str), "'output.answer' debe ser string"
    assert isinstance(output["category"], str), "'output.category' debe ser string"
    assert isinstance(output["confidence"], (int, float)), "'output.confidence' debe ser un número"
    assert output["error"] is None or isinstance(output["error"], str), "'output.error' debe ser string o null"
    
    # 3. Validación de esquema de meta
    meta = data["meta"]
    for field in ("provider", "deployment", "latency_ms", "prompt_tokens", "completion_tokens", "total_tokens", "request_id"):
        assert field in meta, f"Falta 'meta.{field}'"
    
    assert isinstance(meta["provider"], str), "'meta.provider' debe ser string"
    assert meta["deployment"] is None or isinstance(meta["deployment"], str), "'meta.deployment' debe ser string o null"
    assert isinstance(meta["latency_ms"], int), "'meta.latency_ms' debe ser entero"
    assert isinstance(meta["prompt_tokens"], int), "'meta.prompt_tokens' debe ser entero"
    assert isinstance(meta["completion_tokens"], int), "'meta.completion_tokens' debe ser entero"
    assert isinstance(meta["total_tokens"], int), "'meta.total_tokens' debe ser entero"
    assert meta["request_id"] is None or isinstance(meta["request_id"], str), "'meta.request_id' debe ser string o null"

    # 4. Validación de lógica de negocio según el caso
    assert output["ok"] == expected["ok"], f"El estado 'output.ok' no coincide. Esperado: {expected['ok']}, Obtenido: {output['ok']}"
    assert output["error"] == expected["error"], f"El error no coincide. Esperado: {expected['error']}, Obtenido: {output['error']}"
    
    # Comprobar categoría (limpiando mayúsculas/minúsculas y tildes si es necesario, o coincidencia exacta)
    expected_category = expected["category"].lower().replace("á", "a").replace("ó", "o").replace("í", "i")
    actual_category = output["category"].lower().replace("á", "a").replace("ó", "o").replace("í", "i")
    assert actual_category == expected_category, f"La categoría no coincide. Esperada: {expected['category']}, Obtenida: {output['category']}"
    
    # Si se esperaba ok=False (derivación), el score debe ser bajo
    if not expected["ok"]:
        assert output["confidence"] <= 0.3, f"Para derivaciones, la confianza debe ser <= 0.3. Obtenida: {output['confidence']}"
    else:
        assert output["confidence"] >= 0.7, f"Para consultas válidas, la confianza debe ser >= 0.7. Obtenida: {output['confidence']}"
        assert len(output["answer"].strip()) >= 15, "La respuesta es demasiado corta o vacía"
