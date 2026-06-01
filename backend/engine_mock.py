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
        "keywords": [r"tarde.*examen", r"tarde.*convalidaci"],
        "category": "normativa",
        "answer": "Si llegas tarde a una prueba o examen presencial, perderás el derecho a realizarlo a menos que presentes un justificante oficial de fuerza mayor aceptado por la Jefatura de Estudios.",
        "confidence": 0.88,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"convalida", r"solicito.*convalidaci", r"cómo.*convalidación"],
        "category": "trámites",
        "answer": "Para solicitar una convalidación debes presentar el formulario de solicitud en Secretaría junto con tu certificación académica oficial original de los estudios cursados.",
        "confidence": 0.95,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"empiezan.*prácticas", r"cuándo.*prácticas", r"inicio.*fct", r"exención.*prácticas", r"exención.*fct"],
        "category": "fct",
        "answer": "Las prácticas de FCT comienzan oficialmente el 1 de octubre para el primer periodo y el 1 de marzo para el segundo periodo lectivo. Además, se puede solicitar la exención de la FCT si se acredita un año de experiencia laboral afín.",
        "confidence": 0.94,
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
        "keywords": [r"campus.*virtual", r"accedo.*campus", r"plataforma.*virtual", r"teams", r"restablezco.*contraseña", r"contraseña.*teams"],
        "category": "plataformas",
        "answer": "Puedes acceder al campus virtual o Teams utilizando las credenciales corporativas (usuario y contraseña) enviadas a tu correo electrónico al matricularte. Si tienes problemas de acceso, puedes restablecer tu contraseña en el portal de autoservicio.",
        "confidence": 0.93,
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
        "keywords": [r"anular.*matrícula", r"anulación.*matrícula", r"cómo.*anulo.*matrícula"],
        "category": "trámites",
        "answer": "Para solicitar la anulación de la matrícula debes presentar la solicitud correspondiente en Secretaría con al menos dos meses de antelación a la evaluación final del curso.",
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
        "keywords": [r"plazo.*matrícula.*año.*viene", r"matrícula.*año.*que.*viene"],
        "category": "calendario",
        "answer": "El plazo ordinario de matrícula para el próximo curso se abre del 1 al 15 de junio para alumnos de segundo año, y del 20 de junio al 10 de julio para nuevos alumnos.",
        "confidence": 0.92,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"carnet.*estudiante", r"conseguir.*carnet"],
        "category": "secretaría",
        "answer": "El carnet de estudiante se puede solicitar de forma virtual desde la secretaría online de la web del centro, o de manera presencial entregando una fotografía reciente de tamaño carnet.",
        "confidence": 0.94,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"dirección.*centro", r"dónde.*está.*el.*centro"],
        "category": "atención",
        "answer": "Nuestro centro educativo se encuentra ubicado en la Avenida de la Constitución 45, CP 28040 Madrid. Puedes ver el mapa y accesos de transporte público en nuestra página web.",
        "confidence": 0.98,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"cuántas.*convocatorias", r"convocatorias.*por.*asignatura"],
        "category": "normativa",
        "answer": "De acuerdo con la normativa vigente, dispones de un máximo de 4 convocatorias ordinarias para superar cada módulo profesional, con la opción de solicitar hasta 2 convocatorias de gracia adicionales.",
        "confidence": 0.92,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"cierra.*biblioteca", r"horario.*biblioteca"],
        "category": "calendario",
        "answer": "La biblioteca del centro abre de lunes a viernes de 8:30 a 21:00 horas ininterrumpidamente durante el periodo lectivo, y de 9:00 a 14:00 horas durante los periodos no lectivos.",
        "confidence": 0.95,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"teléfono.*director", r"contacto.*director"],
        "category": "atención",
        "answer": "El número de teléfono directo del centro es el 91-555-1234. Para contactar con la secretaría del director o concertar una tutoría, por favor solicita hablar con la extensión 102.",
        "confidence": 0.90,
        "error": None,
        "ok": True
    },
    {
        "keywords": [r"capital.*francia", r"geograf[ií]a", r"par[ií]s", r"fuera.*dominio", r"receta", r"tortilla", r"tiempo.*mañana", r"clima"],
        "category": "derivación",
        "answer": "No dispongo de información académica o administrativa sobre esa consulta de carácter general. Este asistente está especializado exclusivamente en dudas académicas y normativas de nuestro centro.",
        "confidence": 0.15,
        "error": "fuera_de_dominio",
        "ok": False
    },
    {
        "keywords": [r"problema.*personal", r"compañero", r"acos[oó]", r"pelea", r"grave", r"deprimido", r"no.*quiero.*seguir.*estudiando", r"amenazando", r"amenaza.*profesor"],
        "category": "derivación",
        "answer": "Lamento escuchar eso. Al tratarse de un problema de convivencia personal grave o sensible, he derivado este caso con carácter prioritario al departamento de orientación y tutoría para que se pongan en contacto contigo de inmediato.",
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
