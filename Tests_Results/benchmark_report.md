# Benchmark — Orientador Académico
**Fecha:** 2026-06-03 18:38:06
**Provider:** foundry
**Modelo:** DeepSeek-V4-Flash
**Casos:** 24 prompts
**Tarifa:** 0.0003 €/token

## 1. Latencia
| Métrica | Cliente (e2e) | Servidor (modelo) |
|---|---|---|
| p50 (mediana) | 5836 ms | 5590 ms |
| p95 | 23689 ms | 23422 ms |
| Mínimo | 1824 ms | 1582 ms |
| Máximo | 25433 ms | 25175 ms |

**Éxitos:** 22/24 (92%)

## 2. Coste Estimado
- **Muestras analizadas:** 22 peticiones exitosas
- **Avg prompt tokens:** 492
- **Avg completion tokens:** 97
- **Avg total tokens:** 589
- **Coste por request:** 0.1767 €
- **Coste por 1k requests:** 176.70 €

## 3. Fiabilidad
- Timeout definido: ✅ 30s (cliente OpenAI SDK)
- Reintentos: ✅ 3 automáticos (429/5xx)
- Rate limit: ✅ 0.3s entre peticiones
- Errores estructurados: ✅ 2/2 siguen contrato JSON
- Tasa de éxito: ❌ 22/24 (92%)
