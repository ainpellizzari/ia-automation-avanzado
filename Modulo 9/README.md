# Módulo 9 · Gobernanza, trazabilidad y FinOps de IA

Pre-entrega del Módulo 9 de **AI Automation Avanzado** (Coderhouse), dentro del proyecto integrador **NexoFlow**.

El sistema multi-agente de los módulos anteriores suma una capa de gobernanza:

- **Trazabilidad:** cada consulta recibe un `traceId` en el Manager, y ese mismo valor viaja a todos los sub-workflows: Worker Ventas, herramienta del manual, Juez y Worker Soporte.
- **Control de costos:** keys de Anthropic separadas para desarrollo y producción, cada una con su límite de gasto mensual.
- **Compliance:** se revisó qué hace cada proveedor de IA con los datos.

## Archivos

| Archivo | Qué es |
|---|---|
| `PreEntrega_Modulo9_AinPellizzari.pdf` | Plan de Gobernanza, Gestión y Monitoreo Financiero de IA, con 3 dimensiones: Finanzas, Trazabilidad, y Ética y compliance |
| `manager_modulo9_pellizzari_ain.json` | Manager: genera el `traceId` (nodo *Generar traceId*) y lo registra en el log de Slack |
| `worker_ventas_modulo9_pellizzari_ain.json` | Worker Ventas: guarda el `traceId`, el `executionId` y el `Log_JSON` en la planilla. La aprobación humana bloquea las respuestas vacías |
| `worker_soporte_modulo9_pellizzari_ain.json` | Worker Soporte: ticket con `traceId`. Si el mensaje también pide información comercial, manda un aviso aparte a `#operaciones` |
| `supervisor_juez_modulo9_pellizzari_ain.json` | Juez de calidad: devuelve `traceId` en su veredicto (mismo nombre en todo el sistema). Gemini como modelo principal, Claude Haiku de respaldo y timeout de 60 s |
| `log_schema_v2.json` | JSON Schema (draft-07) del log, versión 2 |
| `validar_schema.py` | Valida el esquema contra los logs reales de la planilla (16 de 16 válidos: ventas, soporte, error, fallback y aprobación humana) |
| `buscar_manual_modulo9_pellizzari_ain.json` | Herramienta RAG del M5: recibe el `traceId` como valor fijo, no lo completa el modelo |

## Log JSON (columna `Log_JSON`)

Campos que exige la consigna: `traceId`, `timestamp`, `nodeName`, `toolOutput`, `systemPromptSnapshot` y `confidenceScore`.
Campos de contexto: `executionId` (ejecución del Worker), `environment`, `veredicto`, `intento` y `arquitectura`.

Antes de guardar el `toolOutput`, se recorta a 500 caracteres y los emails se reemplazan por `[EMAIL]`.

## Versión 2 (después de la devolución)

- Números del ROI y TCO con una sola convención (redondeo a 2 decimales y conciliación de las sumas).
- KPIs con fórmula explícita: numerador ÷ total.
- Un solo nombre para el identificador: `traceId`.
- Esquema JSON v2, validado con logs reales.
- Riesgo de sesgo, prueba de equidad con 6 perfiles (6 de 6 con los mismos datos) y revisión mensual de KPIs, riesgos, retención de logs y presupuesto por entorno.

## Seguridad

- Las API keys están solo en las credenciales de n8n. Los JSON exportados no contienen keys.
- Todos los datos de prueba son ficticios.
- Pendiente antes de producción: pasar Gemini al plan pago, hacer el opt-out de entrenamiento en ElevenLabs y cambiar las credenciales a `Anthropic PROD`.
