# ui/app.py
"""
Interfaz de usuario de Gradio para el Asistente Académico (Sesión 2).
Conecta con el backend en http://127.0.0.1:8000/predict.
"""

import os
import requests
import gradio as gr

# Configuración
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/predict")
TIMEOUT = 45  # segundos

def ask_assistant(question: str, temperature: float, max_tokens: float) -> tuple[str, str, str, str, str]:
    """
    Envía la pregunta al backend de la API y retorna la respuesta para la interfaz.
    Retorna: (answer, category, confidence, error_msg, meta_info)
    """
    if not question or not question.strip():
        return "", "", "", "[ADVERTENCIA] Por favor, introduce una pregunta.", ""

    payload = {
        "input": question,
        "options": {
            "temperature": float(temperature),
            "max_tokens": int(max_tokens)
        }
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=TIMEOUT)
        
        # ── Procesar respuesta del servidor ─────────────────────────────────
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                output = data.get("output", {})
                
                # Campos de la respuesta estructurada del modelo
                answer = output.get("answer", "")
                category = output.get("category", "").upper()
                confidence_val = output.get("confidence", 0.0)
                confidence = f"{confidence_val * 100:.1f}%"
                
                # Si el modelo derivó, mostrar aviso
                if not output.get("ok"):
                    deriv_msg = f"[Derivación: {output.get('error')}]"
                    category = f"{category} {deriv_msg}"

                # Extraer meta: tokens y proveedor
                meta = data.get("meta", {})
                provider   = meta.get("provider", "?")
                deployment = meta.get("deployment") or "mock"
                p_tok = meta.get("prompt_tokens", 0)
                c_tok = meta.get("completion_tokens", 0)
                t_tok = meta.get("total_tokens", 0)
                lat   = meta.get("latency_ms", 0)
                rid   = meta.get("request_id") or "(mock)"
                meta_info = (
                    f"Proveedor: {provider} | Modelo: {deployment}\n"
                    f"Tokens → prompt: {p_tok} | completion: {c_tok} | total: {t_tok}\n"
                    f"Latencia: {lat} ms | request_id: {rid}"
                )

                return answer, category, confidence, "", meta_info
            else:
                # Estructura de error de la API
                err_info = data.get("error", {})
                err_code = err_info.get("code", "UNKNOWN_ERROR")
                err_msg  = err_info.get("message", "Error sin mensaje.")
                return "", "", "", f"[{err_code}] {err_msg}", ""
                
        elif response.status_code in (400, 422):
            data = response.json()
            err_info = data.get("error", {})
            err_code = err_info.get("code", "INVALID_INPUT")
            err_msg  = err_info.get("message", "Entrada inválida.")
            return "", "", "", f"[{err_code}] {err_msg}", ""
            
        elif response.status_code == 503:
            data = response.json()
            err_info = data.get("error", {})
            err_msg  = err_info.get("message", "El motor LLM no está disponible temporalmente.")
            return "", "", "", f"[SERVICE_UNAVAILABLE] {err_msg}", ""
            
        else:
            return "", "", "", f"[ERROR HTTP {response.status_code}] {response.text[:200]}", ""

    except requests.exceptions.ConnectionError:
        return (
            "", "", "",
            "[ERROR DE CONEXION] No se pudo conectar con el backend de la API en 127.0.0.1:8000.\n"
            "Asegurate de iniciar primero el servidor ejecutando:\n"
            "uvicorn backend.server:app --host 127.0.0.1 --port 8000 --reload",
            ""
        )
    except requests.exceptions.Timeout:
        return "", "", "", f"[TIMEOUT] El servidor tardó más de {TIMEOUT} segundos en responder.", ""
    except Exception as exc:
        return "", "", "", f"[ERROR INESPERADO] {exc}", ""

# ── Diseño de la UI con Gradio ────────────────────────────────────────────────

# Estilo CSS premium personalizado
custom_css = """
.gradio-container {
    font-family: 'Outfit', 'Inter', system-ui, sans-serif;
    max-width: 900px !important;
    margin: auto;
}
.title-box {
    text-align: center;
    margin-bottom: 2rem;
    padding: 1.5rem;
    border-radius: 12px;
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    color: white;
}
.title-box h1 {
    margin: 0;
    font-size: 2.2rem;
    font-weight: 700;
}
.title-box p {
    margin: 0.5rem 0 0 0;
    opacity: 0.9;
    font-size: 1.1rem;
}
"""

with gr.Blocks(title="Asistente Académico Inteligente", css=custom_css) as demo:
    
    # Cabecera con diseño elegante
    gr.HTML("""
        <div class="title-box">
            <h1>Asistente Académico Inteligente</h1>
            <p>Resuelve dudas frecuentes sobre normativa, secretaría, plazos y prácticas (FCT)</p>
        </div>
    """)
    
    with gr.Row():
        # Columna de Entrada
        with gr.Column(scale=1):
            gr.Markdown("### 📝 Realiza tu consulta")
            txt_in = gr.Textbox(
                label="Pregunta",
                placeholder="Ej: ¿Cómo solicito una convalidación? o ¿Cuándo empiezan las prácticas?",
                lines=4,
                autofocus=True
            )
            
            btn_send = gr.Button("Enviar Consulta", variant="primary", size="lg")
            
            with gr.Accordion("Opciones avanzadas de inferencia", open=False):
                slide_temp = gr.Slider(
                    label="Temperatura (Creatividad)",
                    minimum=0.0,
                    maximum=1.0,
                    value=0.2,
                    step=0.05
                )
                slide_tokens = gr.Slider(
                    label="Maximo de tokens a generar (hard limit: 600)",
                    minimum=64,
                    maximum=600,
                    value=256,
                    step=32
                )
                
            gr.Markdown(
                "💡 *Este asistente estructurará su respuesta y, en caso de preguntas personales o de fuera de dominio, derivará el caso automáticamente.*"
            )

        # Columna de Salida
        with gr.Column(scale=1):
            gr.Markdown("### 🤖 Respuesta del Asistente")
            
            txt_out = gr.Textbox(
                label="Respuesta oficial",
                lines=5,
                interactive=False
            )
            
            with gr.Row():
                txt_category = gr.Textbox(
                    label="Categoría detectada",
                    interactive=False
                )
                txt_confidence = gr.Textbox(
                    label="Confianza (Score)",
                    interactive=False
                )
            
            # Area de error visible solo cuando ocurre un error
            txt_error = gr.Textbox(
                label="Estado / Alertas del sistema",
                interactive=False,
                visible=True,
                placeholder="Sin errores detectados."
            )

            # Panel de meta: tokens y proveedor (novedad P12-S2)
            txt_meta = gr.Textbox(
                label="Uso / Meta (proveedor, tokens, latencia)",
                interactive=False,
                lines=3,
                placeholder="Aqui apareceran los tokens consumidos y el proveedor activo."
            )

    # Interacciones
    _inputs  = [txt_in, slide_temp, slide_tokens]
    _outputs = [txt_out, txt_category, txt_confidence, txt_error, txt_meta]

    btn_send.click(fn=ask_assistant, inputs=_inputs, outputs=_outputs)
    txt_in.submit(fn=ask_assistant,  inputs=_inputs, outputs=_outputs)

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
