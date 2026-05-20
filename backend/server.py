# backend/server.py
"""
API REST para el Asistente Académico (Sesión 2).
Implementa GET /health y POST /predict con el contrato de la Práctica 12.
"""

import os
import sys
import time
from typing import Any, Dict, Optional

# Agregar el directorio de este script a sys.path para resolver importaciones locales
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

# Configuración del proveedor
_PROVIDER_NAME = os.getenv("PROVIDER", "").strip().lower()

# Autodetectar proveedor si no está definido
if not _PROVIDER_NAME:
    if os.getenv("AZURE_OPENAI_API_KEY"):
        _PROVIDER_NAME = "azure"
    else:
        _PROVIDER_NAME = "mock"

if _PROVIDER_NAME == "azure":
    from engine_azure import predict as _engine_predict, AzureEngineError
    _PROVIDER_DISPLAY = "azure-openai"
else:
    from engine_mock import predict as _engine_predict
    # Definimos la excepción vacía por consistencia
    class AzureEngineError(Exception): pass
    _PROVIDER_DISPLAY = "mock"

# Inicializar FastAPI
app = FastAPI(
    title="Asistente Académico API",
    version="2.0",
    description="Backend del Asistente Académico con contrato estable (Sesión 2)."
)

# ── Modelos Pydantic ──────────────────────────────────────────────────────────

class PredictOptions(BaseModel):
    temperature: Optional[float] = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=256, ge=1, le=2048)

class PredictIn(BaseModel):
    input: str
    options: Optional[PredictOptions] = Field(default_factory=PredictOptions)

    @field_validator("input")
    @classmethod
    def input_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El campo 'input' no puede estar vacío o contener solo espacios.")
        return v.strip()

# ── Manejador de Errores de Validación ────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    field = "input"
    message = "La entrada no cumple con el formato requerido."
    
    if errors:
        first_error = errors[0]
        loc = first_error.get("loc", [])
        field = loc[-1] if loc else "input"
        message = first_error.get("msg", message)
        
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "ok": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": f"Error en el campo '{field}': {message}",
                "details": {
                    "field": str(field)
                }
            }
        }
    )

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", summary="Comprueba la salud de la API.")
def health():
    return {
        "status": "ok",
        "provider": _PROVIDER_DISPLAY,
        "azure_configured": bool(os.getenv("AZURE_OPENAI_API_KEY"))
    }

@app.post("/predict", summary="Predicción del Asistente Académico.")
def predict(body: PredictIn):
    t0 = time.time()
    
    try:
        # Ejecutar inferencia en el motor correspondiente
        output_data = _engine_predict(
            text=body.input,
            options=body.options.model_dump() if body.options else None
        )
        
        latency = int((time.time() - t0) * 1000)
        
        return {
            "ok": True,
            "output": output_data,
            "meta": {
                "model": _PROVIDER_DISPLAY,
                "latency_ms": latency
            }
        }
        
    except AzureEngineError as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "ok": False,
                "error": {
                    "code": "MODEL_ERROR",
                    "message": f"El motor de Azure OpenAI reportó un error: {exc}",
                    "details": {
                        "provider": "azure"
                    }
                }
            }
        )
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "ok": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Error inesperado en el backend: {exc}",
                    "details": None
                }
            }
        )

if __name__ == "__main__":
    import uvicorn
    # Determinar puerto (por defecto 8000)
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
