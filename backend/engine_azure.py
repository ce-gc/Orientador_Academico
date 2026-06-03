# backend/engine_azure.py
"""
Motor Azure AI Foundry (DeepSeek) para el Asistente Académico.

Usa el SDK oficial de OpenAI apuntando al endpoint OpenAI-compatible
de Azure AI Foundry. Incluye el wrapper call_and_log para trazar
cada llamada al modelo en logs.jsonl (requisito de la práctica).

Variables de entorno requeridas:
  AZURE_OPENAI_BASE_URL          https://cursoai-resource.services.ai.azure.com/openai/v1
  AZURE_OPENAI_DEPLOYMENT_NAME   DeepSeek-V4-Flash
  AZURE_OPENAI_API_KEY           (secreto — no subir al repo)
  GROUP_ID                       G1..G6
"""

import os
import json
import time
import uuid
import re

# Carga de variables de entorno desde .env si python-dotenv está disponible
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI, APIError, APIConnectionError, APITimeoutError
except ImportError as e:
    raise ImportError(
        "El paquete 'openai' no está instalado. Ejecuta: pip install openai"
    ) from e


# ── Configuración del ejercicio ───────────────────────────────────────────────
EXERCISE_ID = "P12-S2"
MAX_TOKENS_HARD_LIMIT = 600   # Límite obligatorio fijado por el profesor
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs.jsonl")


# ── Excepción propia ──────────────────────────────────────────────────────────
class AzureEngineError(Exception):
    """Excepción para errores del motor de Azure AI Foundry."""
    pass


# ── System prompt del negocio ─────────────────────────────────────────────────
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
   - Clasifica la pregunta en la categoría adecuada de la lista.
   - "confidence" debe ser un número alto (0.80 a 1.00).
   - "error" debe ser null.
2. Para preguntas fuera de dominio (ej. "¿Cuál es la capital de Francia?"):
   - Establece "ok" en false.
   - En "answer" indica amablemente que no tienes esa información y sugiere contactar al centro.
   - Categoría debe ser "derivación".
   - "confidence" debe ser bajo (0.0 a 0.30).
   - "error" debe ser "fuera_de_dominio".
3. Para casos personales graves o sensibles (ej. acoso, problemas personales):
   - Establece "ok" en false.
   - En "answer" ofrece apoyo inicial y deriva al tutor o departamento de orientación.
   - Categoría debe ser "derivación".
   - "confidence" debe ser bajo (0.0 a 0.30).
   - "error" debe ser "caso_sensible".

IMPORTANTE: Responde ÚNICAMENTE con el bloque JSON, sin bloques de código markdown, sin explicaciones."""


# ── Función de logging ────────────────────────────────────────────────────────
def _write_log(event: dict) -> None:
    """Escribe una entrada de log en logs.jsonl (una línea JSON por llamada)."""
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass  # El logging nunca debe romper el flujo principal


# ── Wrapper call_and_log ──────────────────────────────────────────────────────
def call_and_log(
    client: "OpenAI",
    deployment: str,
    messages: list,
    group_id: str,
    temperature: float = 0.2,
    max_tokens: int = MAX_TOKENS_HARD_LIMIT,
    exercise_id: str = EXERCISE_ID,
) -> tuple:
    """
    Llama al modelo y registra la llamada en logs.jsonl.

    Respeta el hard limit de max_tokens=600 del profesor:
    si el llamador pide más, se recorta silenciosamente.

    Returns:
        (resp, request_id, latency_ms)
    """
    # Forzar límite máximo de tokens
    safe_max_tokens = min(max_tokens, MAX_TOKENS_HARD_LIMIT)

    request_id = str(uuid.uuid4())
    t0 = time.time()

    resp = client.chat.completions.create(
        model=deployment,
        messages=messages,
        max_tokens=safe_max_tokens,
        temperature=temperature,
    )

    latency_ms = int((time.time() - t0) * 1000)
    u = resp.usage

    event = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "group_id": group_id,
        "exercise_id": exercise_id,
        "request_id": request_id,
        "deployment": deployment,
        "prompt_tokens": u.prompt_tokens if u else 0,
        "completion_tokens": u.completion_tokens if u else 0,
        "total_tokens": u.total_tokens if u else 0,
        "latency_ms": latency_ms,
    }
    _write_log(event)

    return resp, request_id, latency_ms


# ── Función pública ───────────────────────────────────────────────────────────
def predict(text: str, options: dict | None = None) -> dict:
    """
    Envía la consulta a Azure AI Foundry (DeepSeek) y devuelve
    un dict con 'output' (respuesta estructurada del modelo) y 'meta'.

    Formato de retorno:
    {
        "output": { "ok": bool, "answer": str, "category": str,
                    "confidence": float, "error": str|null },
        "meta":   { "provider": "foundry", "deployment": str,
                    "latency_ms": int, "prompt_tokens": int,
                    "completion_tokens": int, "total_tokens": int,
                    "request_id": str }
    }
    """
    # ── Leer configuración ────────────────────────────────────────────────
    api_key    = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    base_url   = os.getenv("AZURE_OPENAI_BASE_URL", "").strip().rstrip("/")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "").strip()
    group_id   = os.getenv("GROUP_ID", "G?").strip()

    # Si no hay BASE_URL, construirla desde ENDPOINT
    if not base_url:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip().rstrip("/")
        if endpoint:
            base_url = f"{endpoint}/openai/v1"

    # ── Validar configuración ─────────────────────────────────────────────
    missing = []
    if not api_key:
        missing.append("AZURE_OPENAI_API_KEY")
    if not base_url:
        missing.append("AZURE_OPENAI_BASE_URL (o AZURE_OPENAI_ENDPOINT)")
    if not deployment:
        missing.append("AZURE_OPENAI_DEPLOYMENT_NAME")
    if missing:
        raise AzureEngineError(
            f"Faltan variables de entorno: {', '.join(missing)}. "
            "Revisa tu archivo .env en la raíz del proyecto."
        )

    # ── Opciones de inferencia ────────────────────────────────────────────
    opts        = options or {}
    temperature = opts.get("temperature", 0.2)
    max_tokens  = opts.get("max_tokens", MAX_TOKENS_HARD_LIMIT)

    # ── Crear cliente OpenAI apuntando a Foundry ──────────────────────────
    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
        default_headers={"api-key": api_key},   # Foundry requiere ambos
        timeout=30.0,                           # Timeout definido (30s)
        max_retries=3,                          # Reintentos (hasta 3 veces) en errores 429/5xx o conexión
    )


    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": text},
    ]

    # ── Llamada con logging ───────────────────────────────────────────────
    raw_content = ""
    try:
        resp, request_id, latency_ms = call_and_log(
            client=client,
            deployment=deployment,
            messages=messages,
            group_id=group_id,
            temperature=temperature,
            max_tokens=max_tokens,
            exercise_id=EXERCISE_ID,
        )

        raw_content = resp.choices[0].message.content.strip()

        # Limpiar posibles bloques markdown que el modelo añada
        if raw_content.startswith("```"):
            raw_content = re.sub(r"^```[a-z]*\n?", "", raw_content)
            raw_content = re.sub(r"\n?```$", "", raw_content).strip()

        parsed_output = json.loads(raw_content)

        # Validar campos mínimos del contrato
        for field in ("ok", "answer", "category", "confidence", "error"):
            if field not in parsed_output:
                raise AzureEngineError(
                    f"El JSON del modelo no contiene el campo obligatorio: '{field}'"
                )

        u = resp.usage
        return {
            "output": parsed_output,
            "meta": {
                "provider": "foundry",
                "deployment": deployment,
                "latency_ms": latency_ms,
                "prompt_tokens": u.prompt_tokens if u else 0,
                "completion_tokens": u.completion_tokens if u else 0,
                "total_tokens": u.total_tokens if u else 0,
                "request_id": request_id,
            },
        }

    except (APIConnectionError, APITimeoutError) as e:
        raise AzureEngineError(
            f"No se pudo conectar con Azure AI Foundry en '{base_url}'. "
            "Comprueba el endpoint y tu conexión a internet."
        ) from e
    except APIError as e:
        raise AzureEngineError(
            f"Error HTTP {e.status_code} desde Azure AI Foundry: {e.message}"
        ) from e
    except json.JSONDecodeError as e:
        raise AzureEngineError(
            f"El modelo no devolvió JSON válido. Salida: {raw_content!r}. Error: {e}"
        )
    except AzureEngineError:
        raise
    except Exception as e:
        raise AzureEngineError(
            f"Error inesperado en el motor de Azure AI Foundry: {e}"
        ) from e
