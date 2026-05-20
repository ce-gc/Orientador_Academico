# Orientador Académico Inteligente - Práctica 12

Este repositorio contiene la arquitectura modular para el **Asistente Inteligente de atención y consulta académica** (Sesión 2 - Vertical Slice).

El asistente resuelve dudas de alumnos sobre normativa, plazos, plataformas y convalidaciones, estructurando sus respuestas en un JSON estricto. Está diseñado para responder lo conocido y derivar automáticamente los casos de fuera de dominio o personales (sensibles) al tutor o Secretaría para evitar inventar respuestas.

---

## 📂 Estructura del Proyecto

```
├── backend/
│   ├── server.py             # Servidor FastAPI (POST /predict y GET /health)
│   ├── engine_mock.py        # Motor simulado con respuestas realistas de prueba
│   └── engine_azure.py       # Motor que conecta directamente con Azure OpenAI
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
pip install fastapi uvicorn requests gradio python-dotenv
```

### 2. Configurar Variables de Entorno (Opcional para Azure)
Crea un archivo `.env` en la carpeta raíz si deseas conectar con Azure OpenAI:
```env
PROVIDER=azure
AZURE_OPENAI_API_KEY=tu-clave-api-aqui
AZURE_OPENAI_ENDPOINT=https://tu-recurso.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=nombre-de-tu-despliegue
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```
*Si no configuras las credenciales de Azure o dejas el archivo `.env` vacío, el backend iniciará automáticamente en modo **Mock**.*

### 3. Ejecutar el Servidor (Backend)
Desde una terminal en el directorio raíz de la aplicación, ejecuta:
```powershell
# Usando motor Mock (por defecto)
$env:PROVIDER="mock"; uvicorn backend.server:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Ejecutar la Interfaz (Frontend UI)
En otra terminal diferente, ejecuta:
```powershell
python ui/app.py
```
Accede a la interfaz en tu navegador: [http://127.0.0.1:7860](http://127.0.0.1:7860)

### 5. Probar con el Script de Test
Con el backend en ejecución, puedes correr las pruebas automáticas en una tercera terminal:
```powershell
python tests/client.py
```

---

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
