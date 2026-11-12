# Checkpoint 8 · QA automatizado con AI-as-a-Judge

Documentación completa (rúbrica, rutas probadas, experimento A/B y proyección): **[`Checkpoint_Modulo8_Pellizzari_Ain.pdf`](Checkpoint_Modulo8_Pellizzari_Ain.pdf)**.

## Qué hace

El agente comercial "Nexo" (Worker Ventas, con memoria en Airtable y RAG sobre el manual) ya no responde directo al cliente. Cada respuesta pasa por un **Juez** independiente (Gemini 3.5 Flash, temperatura 0) que la califica con una rúbrica y devuelve un JSON con esquema forzado. Un Switch decide la ruta:

| Veredicto | Qué pasa |
|---|---|
| ACEPTADO (exactitud ≥ 4, o 5 si la consulta habla de dinero) | La respuesta sale al cliente |
| CORREGIR | El agente reintenta con la crítica del Juez; máximo 2 reintentos y después escala |
| RECHAZADO, o Juez no disponible | Pausa y Slack con botones Aprobar / Editar |

Cada veredicto queda en Google Sheets (`registro_qa_modulo8.csv`) para auditoría. Un nodo Code valida el veredicto: umbral por criticidad, rechazo ante problemas de seguridad y rechazo si el Juez no recibió datos.

## Archivos

| Archivo | Workflow |
|---|---|
| `manager_modulo8_pellizzari_ain.json` | `M8 - Manager`: chat, memoria en Airtable, Router de intención |
| `worker_ventas_modulo8_pellizzari_ain.json` | `M8 - Worker Ventas`: agente, evaluación, Switch de 3 rutas y aprobación humana |
| `supervisor_juez_modulo8_pellizzari_ain.json` | `M8 - Supervisor Juez`: Juez con Structured Output y validación por código |
| `registro_qa_modulo8.csv` | Registro de veredictos, incluidas las 10 corridas del A/B |

## Resultado del experimento A/B (5 casos por arquitectura)

| | A · Sonnet 5.5 | B · Haiku 5.5 |
|---|---|---|
| Precisión (auditoría humana) | 100% | 80% |
| Intervención humana | 0% | 20% |
| Costo cada 1.000 consultas (agente + Juez) | USD 23,94 | USD 4,48 |
| Latencia promedio | 10,8 s | 9,4 s |

Recomendación: Sonnet. El ciclo de mejora corrigió la búsqueda que hacía fallar a Haiku en la pregunta de precio.

## Cómo importarlo

1. Importá los tres JSON. Publicá primero `M8 - Supervisor Juez` y el sub-workflow `M5 - Buscar en Manual`.
2. Credenciales: Anthropic, Google Gemini (PaLM) API, Google Sheets, Airtable y Slack.
3. En `M8 - Manager`, apuntá `Delegar a Ventas` al Worker; en el Worker, apuntá `Llamar al Juez` al Supervisor.
4. Creá la planilla `M8 - Registro QA` con los encabezados del CSV y elegila en `Registrar Veredicto`.
5. Probá desde **Open chat** del Manager. El plan gratuito de Gemini admite 20 evaluaciones por día.

Los JSON no contienen keys ni tokens: solo referencias a credenciales.
