# Benchmark — Orientador Académico
**Fecha:** 2026-06-03 19:16:26
**Provider:** foundry
**Modelo:** DeepSeek-V4-Flash
**Casos:** 24 prompts
**Tarifa:** 0.0003 €/token

## 1. Latencia
| Métrica | Cliente (e2e) | Servidor (modelo) |
|---|---|---|
| p50 (mediana) | 2912 ms | 2671 ms |
| p95 | 18446 ms | 18173 ms |
| Mínimo | 1799 ms | 1550 ms |
| Máximo | 21711 ms | 21315 ms |

**Éxitos:** 21/24 (88%)

## 2. Coste Estimado
- **Muestras analizadas:** 21 peticiones exitosas
- **Avg prompt tokens:** 491
- **Avg completion tokens:** 93
- **Avg total tokens:** 585
- **Coste por request:** 0.1754 €
- **Coste por 1k requests:** 175.37 €

## 3. Fiabilidad
- Timeout definido: ✅ 30s (cliente OpenAI SDK)
- Reintentos: ✅ 3 automáticos (429/5xx)
- Rate limit: ✅ 0.3s entre peticiones
- Errores estructurados: ✅ 2/2 siguen contrato JSON
- Tasa de éxito: ❌ 21/24 (88%)
