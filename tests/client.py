# tests/client.py
"""
Script de prueba para validar el contrato de la API REST del Asistente Académico.
Ejecuta varias peticiones de prueba y muestra los resultados formateados en consola.

Valida el contrato completo (P12-S2):
  GET  /health  → { status, provider, azure_configured }
  POST /predict → { ok, output: { ok, answer, category, confidence, error },
                        meta:   { provider, deployment, latency_ms,
                                  prompt_tokens, completion_tokens,
                                  total_tokens, request_id } }
"""

import sys
import io
import json
import requests

# Forzar codificación UTF-8 en salida
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

API_URL = "http://127.0.0.1:8000"

# ── Helpers ───────────────────────────────────────────────────────────────────

def _ok(msg: str):
    print(f"  [OK] {msg}")

def _fail(msg: str):
    print(f"  [FAIL] {msg}")

def _check(condition: bool, msg: str):
    if condition:
        _ok(msg)
    else:
        _fail(msg)

# ── Tests ─────────────────────────────────────────────────────────────────────

def test_health():
    print("\n" + "="*60)
    print("TEST: GET /health")
    print("="*60)
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        print(f"  Status Code: {r.status_code}")
        data = r.json()
        print(f"  Response:    {json.dumps(data, ensure_ascii=False)}")
        _check(r.status_code == 200,         "HTTP 200")
        _check("status" in data,             "Campo 'status' presente")
        _check("provider" in data,           "Campo 'provider' presente")
        _check("azure_configured" in data,   "Campo 'azure_configured' presente")
    except Exception as e:
        _fail(f"Error de conexion: {e}")


def test_predict(prompt: str, description: str, expect_ok: bool = True, expect_error_code: str = None):
    print("\n" + "="*60)
    print(f"TEST: {description}")
    print(f"  Input: {prompt!r}")
    print("="*60)
    payload = {"input": prompt}
    try:
        r = requests.post(f"{API_URL}/predict", json=payload, timeout=30)
        print(f"  Status Code: {r.status_code}")
        data = r.json()
        print(f"  Response:\n{json.dumps(data, indent=4, ensure_ascii=False)}")

        # ── Validaciones del contrato ─────────────────────────────────────
        _check("ok" in data, "Campo raiz 'ok' presente")

        if expect_error_code:
            # Respuesta de error esperada (ej. 400 INVALID_INPUT)
            _check(data.get("ok") is False,              "ok == false (error esperado)")
            err = data.get("error", {})
            _check("code" in err,                        "Campo 'error.code' presente")
            _check("message" in err,                     "Campo 'error.message' presente")
            _check(err.get("code") == expect_error_code, f"Codigo de error == {expect_error_code}")
        else:
            # Respuesta OK esperada
            _check(data.get("ok") is True,  "ok == true")
            _check("output" in data,        "Campo 'output' presente")
            _check("meta" in data,          "Campo 'meta' presente")

            output = data.get("output", {})
            _check("ok"         in output, "output.ok presente")
            _check("answer"     in output, "output.answer presente")
            _check("category"   in output, "output.category presente")
            _check("confidence" in output, "output.confidence presente")
            _check("error"      in output, "output.error presente")

            meta = data.get("meta", {})
            _check("provider"           in meta, "meta.provider presente")
            _check("deployment"         in meta, "meta.deployment presente")
            _check("latency_ms"         in meta, "meta.latency_ms presente")
            _check("prompt_tokens"      in meta, "meta.prompt_tokens presente")
            _check("completion_tokens"  in meta, "meta.completion_tokens presente")
            _check("total_tokens"       in meta, "meta.total_tokens presente")
            _check("request_id"         in meta, "meta.request_id presente")

    except Exception as e:
        _fail(f"Error de conexion: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 0. Salud del servidor
    test_health()

    # 1. Caso de exito - tramites
    test_predict(
        prompt="Como solicito una convalidacion?",
        description="Peticion valida de convalidacion (Categoria: Tramites)",
        expect_ok=True
    )

    # 2. Fuera de dominio - derivacion
    test_predict(
        prompt="Cual es la capital de Francia?",
        description="Peticion de fuera de dominio (Debe derivar)",
        expect_ok=False
    )

    # 3. Caso sensible - derivacion
    test_predict(
        prompt="Tengo un problema personal grave con un companero",
        description="Peticion de caso sensible (Debe derivar)",
        expect_ok=False
    )

    # 4. Input vacio - error de validacion
    test_predict(
        prompt="   ",
        description="Peticion invalida con espacios vacios (HTTP 400 - INVALID_INPUT)",
        expect_error_code="INVALID_INPUT"
    )

    print("\n" + "="*60)
    print("Smoke tests completados.")
    print("="*60)
