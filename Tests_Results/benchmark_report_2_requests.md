# Benchmark — Orientador Académico
**Fecha:** 2026-06-03 19:00:35
**Provider:** foundry
**Modelo:** DeepSeek-V4-Flash
**Casos:** 2 prompts
**Tarifa:** 0.0003 €/token

## 1. Latencia
| Métrica | Cliente (e2e) | Servidor (modelo) |
|---|---|---|
| p50 (mediana) | 3983 ms | 3728 ms |
| p95 | 4263 ms | 4020 ms |
| Mínimo | 3672 ms | 3404 ms |
| Máximo | 4294 ms | 4052 ms |

**Éxitos:** 2/2 (100%)

## 2. Coste Estimado
- **Muestras analizadas:** 2 peticiones exitosas
- **Avg prompt tokens:** 490
- **Avg completion tokens:** 106
- **Avg total tokens:** 596
- **Coste por request:** 0.1788 €
- **Coste por 1k requests:** 178.80 €

## 3. Fiabilidad
- Timeout definido: ✅ 30s (cliente OpenAI SDK)
- Reintentos: ✅ 3 automáticos (429/5xx)
- Rate limit: ✅ 0.3s entre peticiones
- Errores estructurados: ✅ 2/2 siguen contrato JSON
- Tasa de éxito: ✅ 2/2 (100%)
