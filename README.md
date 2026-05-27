# Orientador Académico Inteligente - Práctica 12

Este repositorio contiene la arquitectura modular para el **Asistente Inteligente de atención y consulta académica** (Sesión 2 - Vertical Slice).

El asistente resuelve dudas de alumnos sobre normativa, plazos, plataformas y convalidaciones, estructurando sus respuestas en un JSON estricto. Está diseñado para responder lo conocido y derivar automáticamente los casos de fuera de dominio o personales (sensibles) al tutor o Secretaría para evitar inventar respuestas.

---

## 📂 Estructura del Proyecto

```
├── backend/
│   ├── server.py             # Servidor FastAPI (POST /predict y GET /health)
│   ├── engine_mock.py        # Motor simulado (Plan B — sin API key)
│   └── engine_azure.py       # Motor Azure AI Foundry con DeepSeek (Plan A)
├── ui/
│   └── app.py                # Cliente de usuario con interfaz de Gradio
├── tests/
│   ├── client.py             # Cliente de prueba para la API REST
│   └── smoke.jsonl           # Ejemplos de prueba (entradas de humo)
├── data/
│   └── normativa_academica.txt # Base de conocimientos básica para referencia
└── README.md                 # Guía general de uso y evidencias de ejecución
```

---

## ⚙️ Pasos de Instalación y Ejecución

### 1. Instalar Dependencias
Instala los paquetes de Python necesarios:
```powershell
pip install fastapi uvicorn requests gradio python-dotenv openai
```

### 2. Configurar Variables de Entorno
Crea un archivo `.env` en la carpeta raíz del proyecto (nunca lo subas al repo):
```env
# Proveedor activo:
#   foundry -> DeepSeek en Azure AI Foundry (requiere AZURE_OPENAI_API_KEY)
#   mock    -> simulacion local sin API key
PROVIDER=foundry

# Azure AI Foundry (DeepSeek-V4-Flash) — valores exactos del profesor
AZURE_OPENAI_ENDPOINT=https://cursoai-resource.services.ai.azure.com
AZURE_OPENAI_BASE_URL=https://cursoai-resource.services.ai.azure.com/openai/v1
AZURE_OPENAI_DEPLOYMENT_NAME=DeepSeek-V4-Flash
AZURE_OPENAI_API_KEY=TU_CLAVE_AQUI   # <-- secreto, NO subir al repo

# Identificador de grupo para los logs de uso (G1..G6)
GROUP_ID=G1
```
> **Nota:** Si `PROVIDER` no esta definido, el backend autodetecta:
> si existe `AZURE_OPENAI_API_KEY` usa `foundry`; si no, usa `mock`.

### 3. Ejecutar el Servidor (Backend)
Desde una terminal en el directorio raíz, ejecuta **uno** de estos comandos:

```powershell
# Plan B: Modo Mock (sin API key, para desarrollo y demos)
$env:PROVIDER="mock"; uvicorn backend.server:app --host 127.0.0.1 --port 8000 --reload

# Plan A: Modo Foundry/DeepSeek (requiere API key en .env)
# PROVIDER=foundry ya esta configurado en .env, solo lanza:
uvicorn backend.server:app --host 127.0.0.1 --port 8000 --reload
```

Verifica que el backend esta activo:
```powershell
curl http://127.0.0.1:8000/health
# Modo mock:    {"status": "ok", "provider": "mock", "azure_configured": false}
# Modo foundry: {"status": "ok", "provider": "foundry", "azure_configured": true}
```

### Smoke test rapido para Foundry (cuando tengas la API key)

Este comando verifica la conexion directa con DeepSeek sin necesitar la UI:
```powershell
python -c "
import os; from dotenv import load_dotenv; load_dotenv()
from openai import OpenAI
client = OpenAI(
    base_url=os.environ['AZURE_OPENAI_BASE_URL'],
    api_key=os.environ['AZURE_OPENAI_API_KEY'],
    default_headers={'api-key': os.environ['AZURE_OPENAI_API_KEY']},
)
resp = client.chat.completions.create(
    model=os.environ['AZURE_OPENAI_DEPLOYMENT_NAME'],
    messages=[{'role': 'user', 'content': 'Di hola en una frase.'}],
    max_tokens=50, temperature=0.2,
)
print('RESPUESTA:', resp.choices[0].message.content)
print('USAGE:', resp.usage)
"

### 4. Ejecutar la Interfaz (Frontend UI)
En otra terminal diferente, ejecuta:
```powershell
python ui/app.py
```
Accede a la interfaz en tu navegador: [http://127.0.0.1:7860](http://127.0.0.1:7860)

### 5. Probar con el Script de Test
Con el backend en ejecución, ejecuta las pruebas automáticas:
```powershell
python tests/client.py
```

---

## 📊 Logs de Uso (Tracking obligatorio P12-S2)

Cada llamada real al modelo DeepSeek genera automáticamente una línea en **`logs.jsonl`** (en la raíz del proyecto).

### Campos por entrada de log

| Campo | Descripción |
| :--- | :--- |
| `ts` | Fecha y hora ISO de la llamada |
| `group_id` | Identificador de grupo (G1..G6) |
| `exercise_id` | Identificador del ejercicio (`P12-S2`) |
| `request_id` | UUID único por llamada |
| `deployment` | Nombre del modelo (`DeepSeek-V4-Flash`) |
| `prompt_tokens` | Tokens del prompt enviado |
| `completion_tokens` | Tokens de la respuesta generada |
| `total_tokens` | Total de tokens consumidos |
| `latency_ms` | Tiempo total de la llamada en milisegundos |

### Ejemplo de línea en `logs.jsonl`

```json
{"ts": "2026-05-27T17:30:00+0200", "group_id": "G1", "exercise_id": "P12-S2", "request_id": "a1b2c3d4-...", "deployment": "DeepSeek-V4-Flash", "prompt_tokens": 312, "completion_tokens": 87, "total_tokens": 399, "latency_ms": 1240}
```

> **Nota:** El archivo `logs.jsonl` está en `.gitignore` — no se sube al repositorio.
> En modo Mock no se generan logs (tokens = 0).

## 📊 Evidencias de Ejecución (Smoke Tests)

A continuación se muestra una tabla de los 10 casos de prueba del negocio ejecutados contra el backend (`POST /predict`) usando el motor Mock (Plan B de la sesión):

| # | Entrada (Pregunta del Alumno) | Categoría Esperada | Output Esperado (Estructura JSON) | Output Obtenido | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | "¿Cómo solicito una convalidación?" | `trámites` | `{"ok": true, "answer": "...", "category": "trámites", "confidence": 0.95, "error": null}` | `{"ok": true, "answer": "Para solicitar una convalidación debes presentar...", "category": "trámites", "confidence": 0.95, "error": null}` | ✅ Pasado |
| 2 | "¿Cuándo empiezan las prácticas?" | `fct` | `{"ok": true, "answer": "...", "category": "fct", "confidence": 0.92, "error": null}` | `{"ok": true, "answer": "Las prácticas de FCT comienzan oficialmente...", "category": "fct", "confidence": 0.92, "error": null}` | ✅ Pasado |
| 3 | "¿Qué ocurre si suspendo FCT?" | `normativa` | `{"ok": true, "answer": "...", "category": "normativa", "confidence": 0.90, "error": null}` | `{"ok": true, "answer": "Si suspendes el módulo de FCT, dispondrás...", "category": "normativa", "confidence": 0.90, "error": null}` | ✅ Pasado |
| 4 | "¿Cómo accedo al campus virtual?" | `plataformas` | `{"ok": true, "answer": "...", "category": "plataformas", "confidence": 0.96, "error": null}` | `{"ok": true, "answer": "Puedes acceder al campus virtual utilizando...", "category": "plataformas", "confidence": 0.96, "error": null}` | ✅ Pasado |
| 5 | "¿Qué documentación necesito para la matrícula?" | `secretaría` | `{"ok": true, "answer": "...", "category": "secretaría", "confidence": 0.94, "error": null}` | `{"ok": true, "answer": "Para formalizar la matrícula necesitas entregar...", "category": "secretaría", "confidence": 0.94, "error": null}` | ✅ Pasado |
| 6 | "¿Cuál es el horario de secretaría?" | `atención` | `{"ok": true, "answer": "...", "category": "atención", "confidence": 0.97, "error": null}` | `{"ok": true, "answer": "El horario de atención presencial de secretaría...", "category": "atención", "confidence": 0.97, "error": null}` | ✅ Pasado |
| 7 | "¿Puedo cambiar de grupo?" | `normativa` | `{"ok": true, "answer": "...", "category": "normativa", "confidence": 0.89, "error": null}` | `{"ok": true, "answer": "La solicitud de cambio de grupo puede presentarse...", "category": "normativa", "confidence": 0.89, "error": null}` | ✅ Pasado |
| 8 | "¿Qué módulos son obligatorios?" | `plan_de_estudios` | `{"ok": true, "answer": "...", "category": "plan_de_estudios", "confidence": 0.91, "error": null}` | `{"ok": true, "answer": "Todos los módulos del plan de estudios son obligatorios...", "category": "plan_de_estudios", "confidence": 0.91, "error": null}` | ✅ Pasado |
| 9 | "¿Cuál es la capital de Francia?" | `derivación` | `{"ok": false, "answer": "...", "category": "derivación", "confidence": 0.15, "error": "fuera_de_dominio"}` | `{"ok": false, "answer": "No dispongo de información académica sobre...", "category": "derivación", "confidence": 0.15, "error": "fuera_de_dominio"}` | ✅ Pasado |
| 10 | "Tengo un problema personal grave con un compañero" | `derivación` | `{"ok": false, "answer": "...", "category": "derivación", "confidence": 0.20, "error": "caso_sensible"}` | `{"ok": false, "answer": "Lamento escuchar eso. Al tratarse de un problema...", "category": "derivación", "confidence": 0.20, "error": "caso_sensible"}` | ✅ Pasado |
| 11 | "   " (Espacio en blanco) | (Error de validación) | `{"ok": false, "error": {"code": "INVALID_INPUT", ...}}` | `{"ok": false, "error": {"code": "INVALID_INPUT", "message": "Error en el campo 'input': ...", "details": {"field": "input"}}}` | ✅ Pasado |
