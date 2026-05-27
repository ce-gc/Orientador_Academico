# backend/engine_mock.py
"""
Motor Mock para el Asistente Académico (Sesión 2).
Simula respuestas realistas basadas en las 10 preguntas de prueba del proyecto.

Devuelve el mismo formato que engine_azure.py:
  { "output": {...}, "meta": { "provider": "mock", tokens: 0, ... } }
"""

import time
import re

# Respuestas predefinidas basadas en palabras clave
MOCK_DATABASE = [
    {
        "keywords": [r"convalida", r"solicito.*convalidaci", r"cómo.*convalidación"],
        "category": "trámites",
        "answer": "Para solicitar una convalidación debes presentar el formulario de solicitud en Secretaría junto con tu certificación académica oficial original de los estudios cursados.",
        "confidence": 0.95,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"empiezan.*prácticas", r"cuándo.*prácticas", r"inicio.*fct"],
        "category": "fct",
        "answer": "Las prácticas de FCT comienzan oficialmente el 1 de octubre para el primer periodo y el 1 de marzo para el segundo periodo lectivo.",
        "confidence": 0.92,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"suspendo.*fct", r"qué.*ocurre.*suspendo", r"suspender.*fct"],
        "category": "normativa",
        "answer": "Si suspendes el módulo de FCT, dispondrás de una convocatoria extraordinaria para repetirlo en el siguiente período de prácticas establecido por el centro.",
        "confidence": 0.90,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"campus.*virtual", r"accedo.*campus", r"plataforma.*virtual"],
        "category": "plataformas",
        "answer": "Puedes acceder al campus virtual utilizando las credenciales corporativas (usuario y contraseña) enviadas a tu correo electrónico al matricularte. Si tienes problemas de acceso, contacta con soporte.",
        "confidence": 0.96,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"documentaci[oó]n.*matr[ií]cula", r"qué.*necesito.*matrícula", r"documentos.*matrícula"],
        "category": "secretaría",
        "answer": "Para formalizar la matrícula necesitas entregar una copia del DNI/NIE, el resguardo de pago de tasas, una fotografía reciente y el título académico que da acceso al ciclo formativo.",
        "confidence": 0.94,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"horario.*secretar[ií]a", r"cuándo.*abre.*secretaría"],
        "category": "atención",
        "answer": "El horario de atención presencial de secretaría es de lunes a viernes de 9:00 a 14:00 horas, y los martes y jueves por la tarde de 16:00 a 18:30 horas.",
        "confidence": 0.97,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"cambiar.*grupo", r"cambio.*grupo", r"puedo.*cambiar.*grupo"],
        "category": "normativa",
        "answer": "La solicitud de cambio de grupo puede presentarse en secretaría durante los primeros 10 días lectivos de curso, justificando motivos laborales o de salud acreditados.",
        "confidence": 0.89,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"m[oó]dulos.*obligatorios", r"asignaturas.*obligatorias", r"qué.*módulos.*necesito"],
        "category": "plan_de_estudios",
        "answer": "Todos los módulos del plan de estudios son obligatorios para obtener el título, a excepción de las convalidaciones y la exención de FCT por experiencia laboral previa.",
        "confidence": 0.91,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"capital.*francia", r"geograf[ií]a", r"par[ií]s", r"fuera.*dominio"],
        "category": "derivación",
        "answer": "No dispongo de información académica sobre geografía internacional ni la capital de Francia. Este asistente está especializado en consultas académicas y normativas del centro.",
        "confidence": 0.15,
        "error": "fuera_de_dominio",
        "ok": False
    },
    {
        "keywords": [r"problema.*personal", r"compañero", r"acos[oó]", r"pelea", r"grave"],
        "category": "derivación",
        "answer": "Lamento escuchar eso. Al tratarse de un problema de convivencia personal grave, he derivado este caso con carácter prioritario al departamento de orientación y tutoría para que se pongan en contacto contigo de inmediato.",
        "confidence": 0.20,
        "error": "caso_sensible",
        "ok": False
    }
]

def predict(text: str, options: dict | None = None) -> dict:
    """
    Simula la inferencia del asistente académico.

    Devuelve el mismo contrato que engine_azure.predict():
      {
        "output": { ok, answer, category, confidence, error },
        "meta":   { provider, deployment, latency_ms,
                    prompt_tokens, completion_tokens, total_tokens, request_id }
      }
    """
    # Latencia simulada realista
    time.sleep(0.4)

    text_lower = text.lower()

    # Meta fija del mock (sin tokens reales, sin deployment real)
    _meta = {
        "provider": "mock",
        "deployment": None,
        "latency_ms": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "request_id": None,
    }

    # Intentar buscar coincidencia en la base de datos mock
    for item in MOCK_DATABASE:
        for pattern in item["keywords"]:
            if re.search(pattern, text_lower):
                return {
                    "output": {
                        "ok":         item["ok"],
                        "answer":     item["answer"],
                        "category":   item["category"],
                        "confidence": item["confidence"],
                        "error":      item["error"],
                    },
                    "meta": _meta,
                }

    # Respuesta por defecto para casos desconocidos
    return {
        "output": {
            "ok":         False,
            "answer":     "No he podido encontrar una respuesta precisa a tu consulta académica. Por favor, ponte en contacto directo con Secretaría o consulta a tu tutor.",
            "category":   "derivación",
            "confidence": 0.25,
            "error":      "fuera_de_dominio",
        },
        "meta": _meta,
    }
