# Benchmark — Orientador Académico
**Fecha:** 2026-06-03 19:23:14
**Provider:** foundry
**Modelo:** DeepSeek-V4-Flash
**Casos:** 5 prompts
**Tarifa:** 0.0003 €/token

## 1. Latencia
| Métrica | Cliente (e2e) | Servidor (modelo) |
|---|---|---|
| p50 (mediana) | 2913 ms | 2652 ms |
| p95 | 5686 ms | 5440 ms |
| Mínimo | 2597 ms | 2350 ms |
| Máximo | 6266 ms | 6021 ms |

**Éxitos:** 5/5 (100%)

## 2. Coste Estimado
- **Muestras analizadas:** 5 peticiones exitosas
- **Avg prompt tokens:** 491
- **Avg completion tokens:** 99
- **Avg total tokens:** 590
- **Coste por request:** 0.1771 €
- **Coste por 1k requests:** 177.06 €

## 3. Fiabilidad
- Timeout definido: ✅ 30s (cliente OpenAI SDK)
- Reintentos: ✅ 3 automáticos (429/5xx)
- Rate limit: ✅ 0.3s entre peticiones
- Errores estructurados: ✅ 2/2 siguen contrato JSON
- Tasa de éxito: ✅ 5/5 (100%)
