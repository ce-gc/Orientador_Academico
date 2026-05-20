# backend/engine_azure.py
"""
Motor Azure OpenAI para el Asistente Académico (Sesión 2).
Realiza llamadas HTTP directas al servicio de Azure OpenAI Chat Completions.
"""

import os
import json
import requests

# Carga de variables de entorno si python-dotenv está disponible
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class AzureEngineError(Exception):
    """Excepción para errores del motor de Azure OpenAI."""
    pass

SYSTEM_PROMPT = """Eres el Asistente Inteligente de atención y consulta académica de nuestro centro educativo.
Tu función es responder dudas de alumnos sobre normativa, plazos y trámites.

Debes responder obligatoriamente con un objeto JSON que tenga EXACTAMENTE esta estructura:
{
  "ok": boolean,
  "answer": "string",
  "category": "string",
  "confidence": number (entre 0.0 y 1.0),
  "error": "string" o null
}

Categorías permitidas:
- trámites
- fct
- calendario
- normativa
- plataformas
- secretaría
- atención
- plan_de_estudios
- derivación

Reglas del negocio:
1. Para preguntas de dominio académico válidas:
   - Establece "ok" en true.
   - Proporciona una respuesta clara y concisa en "answer".
   - Clasifica la pregunta en la categoría adecuada de la lista (ej. "trámites", "normativa", etc.).
   - "confidence" debe ser un número alto (0.80 a 1.00).
   - "error" debe ser null.
2. Para preguntas fuera de dominio (ej. "¿Cuál es la capital de Francia?"):
   - Establece "ok" en false.
   - En "answer" indica amablemente que no tienes esa información y sugiere contactar al centro.
   - Categoría debe ser "derivación".
   - "confidence" debe ser bajo (0.0 a 0.30).
   - "error" debe ser "fuera_de_dominio".
3. Para casos personales graves o sensibles (ej. acoso, problemas personales con compañeros):
   - Establece "ok" en false.
   - En "answer" ofrece apoyo inicial y deriva inmediatamente al tutor o departamento de orientación.
   - Categoría debe ser "derivación".
   - "confidence" debe ser bajo (0.0 a 0.30).
   - "error" debe ser "caso_sensible".

IMPORTANTE: Responde ÚNICAMENTE con el bloque JSON, sin bloques de código markdown, sin explicaciones antes o después del JSON."""

def predict(text: str, options: dict | None = None) -> dict:
    """
    Envía la consulta a Azure OpenAI y devuelve el JSON estructurado.
    """
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    if not api_key or not endpoint or not deployment:
        raise AzureEngineError(
            "Faltan variables de entorno para Azure OpenAI. "
            "Asegúrate de configurar AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT y AZURE_OPENAI_DEPLOYMENT_NAME."
        )
        
    # Limpieza de slash final en el endpoint si existe
    endpoint = endpoint.strip().rstrip("/")
    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    
    opts = options or {}
    temperature = opts.get("temperature", 0.2)
    max_tokens = opts.get("max_tokens", 256)
    
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"}  # Obliga a Azure a responder en JSON si lo soporta el modelo
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        raw_content = data["choices"][0]["message"]["content"].strip()
        
        # Intentar parsear el JSON de salida del modelo
        parsed_output = json.loads(raw_content)
        
        # Validar campos mínimos
        for field in ("ok", "answer", "category", "confidence", "error"):
            if field not in parsed_output:
                raise AzureEngineError(f"El JSON devuelto por el modelo no contiene el campo obligatorio: '{field}'")
                
        return parsed_output
        
    except requests.exceptions.RequestException as e:
        raise AzureEngineError(f"Error de red al llamar a Azure OpenAI: {e}")
    except json.JSONDecodeError as e:
        raise AzureEngineError(f"El modelo no devolvió un JSON válido. Salida: {raw_content}. Error: {e}")
    except Exception as e:
        raise AzureEngineError(f"Error inesperado en el proveedor de Azure: {e}")
