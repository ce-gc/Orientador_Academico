# Benchmark — Orientador Académico
**Fecha:** 2026-06-03 19:22:50
**Provider:** foundry
**Modelo:** DeepSeek-V4-Flash
**Casos:** 2 prompts
**Tarifa:** 0.0003 €/token

## 1. Latencia
| Métrica | Cliente (e2e) | Servidor (modelo) |
|---|---|---|
| p50 (mediana) | 3064 ms | 2802 ms |
| p95 | 3790 ms | 3508 ms |
| Mínimo | 2258 ms | 2018 ms |
| Máximo | 3871 ms | 3586 ms |

**Éxitos:** 2/2 (100%)

## 2. Coste Estimado
- **Muestras analizadas:** 2 peticiones exitosas
- **Avg prompt tokens:** 490
- **Avg completion tokens:** 102
- **Avg total tokens:** 592
- **Coste por request:** 0.1774 €
- **Coste por 1k requests:** 177.45 €

## 3. Fiabilidad
- Timeout definido: ✅ 30s (cliente OpenAI SDK)
- Reintentos: ✅ 3 automáticos (429/5xx)
- Rate limit: ✅ 0.3s entre peticiones
- Errores estructurados: ✅ 2/2 siguen contrato JSON
- Tasa de éxito: ✅ 2/2 (100%)
