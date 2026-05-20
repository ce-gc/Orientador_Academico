# tests/client.py
"""
Script de prueba para validar el contrato de la API REST del Asistente Académico.
Ejecuta varias peticiones de prueba y muestra los resultados formateados en consola.
"""

import sys
import io
import requests

# Forzar codificación UTF-8 en salida
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

API_URL = "http://127.0.0.1:8000"

def test_health():
    print("\n--- TEST: GET /health ---")
    try:
        r = requests.get(f"{API_URL}/health")
        print("Status Code:", r.status_code)
        print("Response JSON:", r.json())
    except Exception as e:
        print("Error de conexión:", e)

def test_predict(prompt: str, description: str):
    print(f"\n--- TEST: {description} ---")
    print("Input:", prompt)
    payload = {"input": prompt}
    try:
        r = requests.post(f"{API_URL}/predict", json=payload)
        print("Status Code:", r.status_code)
        print("Response JSON:")
        import json
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print("Error de conexión:", e)

if __name__ == "__main__":
    # Comprobar salud
    test_health()
    
    # 1. Caso de éxito (normativa/trámites)
    test_predict(
        prompt="¿Cómo solicito una convalidación?",
        description="Petición válida de convalidación (Categoría: Trámites)"
    )
    
    # 2. Caso de fuera de dominio (derivación)
    test_predict(
        prompt="¿Cuál es la capital de Francia?",
        description="Petición de fuera de dominio (Debe derivar)"
    )
    
    # 3. Caso sensible (derivación)
    test_predict(
        prompt="Tengo un problema personal grave con un compañero",
        description="Petición de caso sensible (Debe derivar)"
    )
    
    # 4. Caso de error de validación (input vacío)
    test_predict(
        prompt="   ",
        description="Petición inválida con espacios vacíos (Debe dar HTTP 400 - INVALID_INPUT)"
    )
