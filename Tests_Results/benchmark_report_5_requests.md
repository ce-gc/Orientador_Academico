# Benchmark — Orientador Académico
**Fecha:** 2026-06-03 18:57:11
**Provider:** foundry
**Modelo:** DeepSeek-V4-Flash
**Casos:** 5 prompts
**Tarifa:** 0.0003 €/token

## 1. Latencia
| Métrica | Cliente (e2e) | Servidor (modelo) |
|---|---|---|
| p50 (mediana) | 5449 ms | 5138 ms |
| p95 | 17611 ms | 17209 ms |
| Mínimo | 2454 ms | 2218 ms |
| Máximo | 20342 ms | 19910 ms |

**Éxitos:** 5/5 (100%)

## 2. Coste Estimado
- **Muestras analizadas:** 5 peticiones exitosas
- **Avg prompt tokens:** 491
- **Avg completion tokens:** 100
- **Avg total tokens:** 591
- **Coste por request:** 0.1774 €
- **Coste por 1k requests:** 177.36 €

## 3. Fiabilidad
- Timeout definido: ✅ 30s (cliente OpenAI SDK)
- Reintentos: ✅ 3 automáticos (429/5xx)
- Rate limit: ✅ 0.3s entre peticiones
- Errores estructurados: ✅ 2/2 siguen contrato JSON
- Tasa de éxito: ✅ 5/5 (100%)
