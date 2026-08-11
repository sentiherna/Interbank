# Contratos de datos e interfaces - Feature 002

**Feature**: `002-plaft-investigation-graph`  
**Date**: 2026-08-10

Este directorio define contratos minimos para:

1. Fuentes prioritarias iniciales del MVP.
2. Entidades investigativas creadas dentro de la plataforma.

## Fuentes prioritarias iniciales

- [clientes.md](clientes.md)
- [cuentas.md](cuentas.md)
- [titularidades.md](titularidades.md)
- [transferencias.md](transferencias.md)
- [alertas_plaft.md](alertas_plaft.md)
- [casos_historicos.md](casos_historicos.md)

## Contratos investigativos internos

- [caso_investigado.md](caso_investigado.md)
- [hallazgo_analitico.md](hallazgo_analitico.md)
- [evidencia.md](evidencia.md)

## Reglas transversales

- Validar esquema, tipos, obligatorios y dominios.
- Aplicar `fecha_corte` en todas las fuentes con temporalidad.
- Detener ejecucion en errores criticos de calidad.
- Conservar trazabilidad al registro fuente.
- No almacenar datos reales sensibles en el repositorio.
