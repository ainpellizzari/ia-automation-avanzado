# Nexo — Agente Calificador de Leads (n8n + Claude)

Proyecto integrador del curso **AI Automation Avanzado**. Es un agente de IA construido en n8n que conversa con potenciales clientes de **NexoFlow** (agencia ficticia de automatizaciones e IA para pymes), los califica como CALIENTE, TIBIO o FRÍO, los registra en Google Sheets y reporta cada ejecución en Slack para supervisión humana.

El proyecto evoluciona módulo a módulo: cada checkpoint parte del `.json` anterior y le suma nodos nuevos.

---

## Caso de uso

Una pyme que vende servicios recibe consultas de posibles clientes. En lugar de que una persona responda y filtre cada una, el agente:

1. Conversa con el lead y recolecta 7 datos en unos 3 mensajes: nombre, empresa y rubro, cantidad de empleados, necesidad, presupuesto, urgencia y email.
2. Clasifica al lead según criterios definidos:
   - **CALIENTE:** necesidad clara, presupuesto definido y urgencia menor a 1 mes.
   - **TIBIO:** necesidad clara, pero sin presupuesto definido o sin urgencia.
   - **FRÍO:** está explorando, sin necesidad concreta.
3. Decide por sí mismo cuándo registrar al lead en una planilla (sin duplicarlo: si el email ya existe, actualiza la fila).
4. Deja un log en Slack con lo que pidió el lead, qué herramientas usó el agente y qué respondió.

El agente **no** inventa precios, no promete reuniones, no pide datos sensibles y escala a un humano ante reclamos, pedidos de hablar con una persona o proyectos fuera de alcance.

---

## Arquitectura

```
[When chat message received] → [AI Agent] → [Respond to Chat] → [Log Observabilidad Slack]
                                   ├─ Anthropic Chat Model   (cerebro)
                                   ├─ Simple Memory          (contexto de la sesión)
                                   └─ Registrar Lead         (tool: Google Sheets)
```

- **Línea principal (determinista):** se ejecuta siempre, en el mismo orden. Recibe el mensaje, responde al usuario y genera el log.
- **Conexiones laterales (probabilísticas):** el agente decide en cada vuelta del ciclo ReAct (razonar → actuar → observar) si usa la herramienta. La herramienta nunca está en la línea principal.

### Nodos utilizados

| Nodo | Tipo | Función |
|---|---|---|
| When chat message received | Chat Trigger | Puerta de entrada. `Response Mode = Using Response Nodes` para que la respuesta al usuario la dé un nodo específico. |
| AI Agent | Tools Agent | Motor de razonamiento. System Message modular, **Max Iterations = 7** y **Return Intermediate Steps = ON**. |
| Anthropic Chat Model | Language Model | Modelo Claude (Sonnet). |
| Simple Memory | Memory | Recuerda la conversación dentro de la sesión, para juntar datos aportados en distintos mensajes. |
| Registrar Lead | Google Sheets Tool | Operación `Append or Update Row`, columna de coincidencia `Email` (upsert). Campos completados con `$fromAI()`; la fecha la pone n8n con `$now`. |
| Respond to Chat | Chat | Devuelve al usuario la respuesta del agente (`{{ $json.output }}`). |
| Log Observabilidad Slack | Slack | Envía al canal `#agente-leads` fecha, sesión, mensaje del lead, herramientas usadas (`intermediateSteps`) y respuesta del agente. |

### Guardrails

- **Max Iterations = 7:** techo de vueltas del ciclo ReAct para evitar bucles y blindar el costo.
- **Mínimo privilegio:** la herramienta solo puede crear o actualizar filas, nunca borrar.
- **System Message** estructurado en Rol → Ámbito → Objetivo → Uso de herramientas → Reglas → Escalamiento, con prohibiciones explícitas para reducir alucinaciones.
- **Descripción semántica de la tool** que indica cuándo usarla, cuándo no, qué datos enviar y cómo interpretar el resultado.

---

## Requisitos y credenciales

| Servicio | Para qué | Credencial en n8n |
|---|---|---|
| Anthropic | Modelo de lenguaje | **Anthropic API** (API key de console.anthropic.com, con crédito cargado) |
| Google Sheets | Registro de leads | **Google Sheets OAuth2** (en n8n Cloud: "Sign in with Google") |
| Slack | Log de observabilidad | **Slack OAuth2** (conectar el workspace) |

Además se necesita:

- Una planilla de Google Sheets con estos encabezados en la fila 1 (A a J):
  `Fecha | Nombre | Email | Empresa | Rubro | Empleados | Necesidad | Presupuesto | Urgencia | Clasificacion`
- Un canal de Slack (por ejemplo `#agente-leads`).

> El `.json` exportado **no contiene** API keys ni tokens: solo referencias a las credenciales. Hay que crearlas en tu propia instancia.

| Airtable | Memoria de largo plazo del agente (M3) | **Airtable OAuth2** o Personal Access Token con permisos `data.records:read`, `data.records:write` y `schema.bases:read` |
### Base de memoria (desde M3)

Base `NexoFlow Memoria`, tabla `Memoria`, con estas columnas:

| Columna | Tipo |
|---|---|
| Session_ID | Single line text (campo principal) |
| Nombre | Single line text |
| Fecha de actualización | Date con hora |
| Resumen consolidado | Long text |
| Estado del caso | Single select: Nuevo, En calificación, Lead registrado, Ticket abierto, Escalado |
| Datos clave | Long text |
| Mensajes | Number (entero) |
---

## Cómo importar y poner en marcha

1. En n8n, creá un workflow nuevo, abrí el menú `···` y elegí **Import from File**. Seleccioná el `.json` del checkpoint.
2. Creá las tres credenciales (Anthropic, Google Sheets, Slack) y asignalas en cada nodo.
3. En **Registrar Lead**, elegí tu planilla y hoja, y verificá que la columna de coincidencia sea `Email`.
4. En **Log Observabilidad Slack**, elegí tu canal. Si da `not_in_channel`, invitá la app de n8n al canal con `/invite`.
5. En **Anthropic Chat Model**, elegí el modelo disponible en tu cuenta.
6. Probá desde **Open chat** con un mensaje como:
   > Hola, soy Martina López de Casa Sur, una inmobiliaria de Rosario con 8 empleados. Queremos automatizar las consultas que nos llegan por WhatsApp, tenemos unos 1500 USD y lo necesitamos este mes. Mi mail es martina@casasur.com
7. Verificá: todo el lienzo en verde, la fila en la planilla con clasificación CALIENTE y el log en Slack.

---

## Historial de checkpoints

## Historial de checkpoints

| Módulo | Archivos | Qué se agregó |
|---|---|---|
| M1 · Agente base | `checkpoint1_ain_pellizzari.json` | Chat Trigger, AI Agent (Tools Agent, máx. 7 iteraciones), System Prompt modular, Google Sheets como tool con upsert, Simple Memory, log en Slack. |
| M2 · Multi-agente | [`Modulo 2/`](Modulo%202/) | Manager con router (Text Classifier, taxonomía VENTAS / SOPORTE / Other) que delega por Execute Workflow a dos Workers: Ventas (agente Nexo del M1) y Soporte (clasificación con IA, ticket y alerta urgente). Contratos JSON de entrada y salida, rutas de error, timeouts y log de trazabilidad en Slack. |
| M3 · Memoria | [`Modulo 3/`](Modulo%203/) | Memoria de largo plazo en Airtable por Session_ID: búsqueda al inicio, alta de usuarios nuevos, inyección del contexto en el System Prompt entre delimitadores anti-inyección y actualización idempotente al final de cada turno. Desde el sexto mensaje, Claude Haiku resume la conversación en JSON (asunto_principal, puntos_clave, accion_requerida). Reutiliza el Worker Soporte del M2. |
| M4 · Integraciones | [`Modulo 4/`](Modulo%204/) | Canal de email: Gmail Trigger con filtro anti auto-reply, limpieza y validación del payload, Agente de Correo (clasificación y borrador), Look up en HubSpot antes de crear o actualizar (con validación cruzada), borrador Human-in-the-loop y aviso a Slack con payload mínimo. Integraciones por OAuth2 con mínimo privilegio. |
| M5 · RAG | — | Pendiente |
| M6 · Voz | — | Pendiente |

---

**Autor:** Ain Pellizzari · Curso AI Automation Avanzado
