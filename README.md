# Nexo · Sistema de agentes de IA para NexoFlow (n8n)

Proyecto integrador del curso **AI Automation Avanzado** (Coderhouse). Es un sistema de agentes de IA construido en n8n para **NexoFlow**, una agencia ficticia de automatizaciones e IA para pymes. El sistema atiende consultas comerciales y de soporte por chat, correo y Telegram (voz o texto), califica leads, mantiene ordenado el CRM, responde solo con información verificada del manual de la empresa y somete sus respuestas a un supervisor de calidad antes de enviarlas.

El proyecto evolucionó módulo a módulo: cada checkpoint parte del anterior y le suma una capacidad nueva. Cada carpeta tiene su propio README, los `.json` de los workflows y la documentación entregada.

---

## Qué resuelve

Una pyme de servicios recibe consultas de posibles clientes y de clientes actuales por varios canales. Responderlas a mano lleva horas por semana, las consultas fuera de horario esperan al día siguiente y el CRM se llena de duplicados. Nexo:

1. **Responde al instante, a cualquier hora**, por chat, correo o Telegram, en el mismo formato en que le hablan (audio o texto).
2. **Califica cada lead** (CALIENTE, TIBIO o FRÍO) y lo registra sin duplicarlo.
3. **Responde solo con el manual oficial**, cita la fuente y dice "No sé" cuando el dato no figura.
4. **Recuerda a cada usuario** entre conversaciones.
5. **Deja los correos como borrador** para que una persona los revise antes de enviar.
6. **Pasa cada respuesta por un Juez de calidad** y escala a una persona en Slack cuando hay riesgo.

---

## Arquitectura actual

```
                ┌─ Chat web ──────────┐
Señales ────────┼─ Correo (Gmail) ────┼──▶ Validación determinista (anti auto-reply, limpieza, IF)
                └─ Telegram voz/texto ┘
                              │
                              ▼
                 [Manager: memoria Airtable + Router de intención]
                     ├─ Worker Ventas ──▶ RAG (Pinecone) · Registrar Lead · HubSpot
                     ├─ Worker Soporte
                     └─ Escalamiento humano
                              │
                              ▼
                 [Supervisor Juez: Gemini + JSON Schema + validación por código]
                     ├─ ACEPTADO  ──▶ respuesta al cliente
                     ├─ CORREGIR  ──▶ el agente reintenta con la crítica (máx. 2)
                     └─ RECHAZADO ──▶ Slack con Aprobar / Editar
                              │
                              ▼
                 Registro de cada decisión (Google Sheets / Slack)
```

---

## Historial de checkpoints

| Módulo | Carpeta | Qué se agregó |
|---|---|---|
| M1 · Agente base | [`Modulo 1/`](Modulo%201/) | Chat Trigger, AI Agent (Tools Agent, máx. 7 iteraciones), System Prompt modular, Google Sheets como herramienta con upsert por email, Simple Memory y log de observabilidad en Slack. |
| M2 · Multi-agente | [`Modulo 2/`](Modulo%202/) | Patrón Manager-Worker: un Router de intención deriva a sub-workflows especializados (Ventas y Soporte) con un contrato de datos fijo, y escala a un humano ante errores o pedidos fuera de alcance. |
| M3 · Memoria | [`Modulo 3/`](Modulo%203/) | Memoria persistente en Airtable por sesión: nombre, estado del caso y resumen consolidado cada 5 mensajes, inyectados entre delimitadores para evitar prompt injection. |
| M4 · Integraciones | [`Modulo 4/`](Modulo%204/) | Canal de correo: Gmail → filtro anti auto-reply → limpieza del payload → agente que clasifica y redacta → validación de la respuesta → HubSpot (Look up antes de crear) → borrador en Gmail para revisión humana → aviso en Slack. |
| M5 · RAG | [`Modulo 5/`](Modulo%205/) | Base de conocimiento: manual oficial parseado con LlamaParse, fragmentado por sección e indexado en Pinecone con embeddings de Gemini. Top-K 4 y Minimum Score 0,70 calibrado en tres rondas; cita obligatoria y "No sé" si el dato no figura. Validación ciega: 5/5. |
| M6 · Voz | [`Modulo 6/`](Modulo%206/) | Canal de Telegram multimodal: nota de voz → Whisper (Groq) → IF de contingencia calibrado con no_speech_prob y avg_logprob → agente con el RAG → respuesta hablada con ElevenLabs, o escrita si el usuario escribe. Aviso de escalamiento a Slack. Compliance: el audio no se almacena. 7/7 pruebas. |
| M7 · Diseño vertical | [`Modulo 7/`](Modulo%207/) | Informe de consultoría de 4 páginas: especialización del sistema para Sales Ops y Customer Success, con baseline, priorización ponderada, red de 6 agentes con contratos JSON, mapa de permisos, KPIs, semáforo de riesgo con HITL, especificación de prueba y scorecards. |
| M8 · QA | [`Modulo 8/`](Modulo%208/) | Supervisor AI-as-a-Judge: Juez Gemini con JSON Schema, validación por código y Switch de 3 rutas (aceptar, corregir con hasta 2 reintentos o escalar a Slack). Prueba A/B Sonnet 5.5 vs Haiku 5.5 (100% vs 80% de precisión; USD 23,94 vs 4,48 cada 1.000 consultas) y ciclo de mejora sobre la búsqueda RAG. |

---

## Guardrails del sistema

| Riesgo | Control |
|---|---|
| Bucles y costo descontrolado | Máximo de iteraciones por agente, máximo 2 reintentos de corrección, techo de caracteres antes de la síntesis de voz |
| Datos inventados | RAG con Minimum Score calibrado, cita obligatoria, "No sé" literal y un Juez que compara la respuesta con los fragmentos recuperados |
| Prompt injection | Delimitadores en memoria y mensajes, Router que escala pedidos sospechosos y regla de seguridad en el Juez |
| Correos en bucle | Filtro anti auto-reply antes del agente |
| Duplicados en el CRM | Upsert por email y Look up antes de crear |
| Acciones irreversibles | Mínimo privilegio: ningún workflow borra registros ni envía correos solo; los correos quedan como borrador |
| Supervisor que falla | Si el Juez no responde o no recibe datos, la respuesta va a revisión humana |
| Datos personales | La voz no se guarda: ejecuciones sin guardar y Zero Data Retention en el proveedor de transcripción |

---

## Stack

n8n Cloud · Claude (Anthropic) · Gemini (embeddings y Juez) · Pinecone · LlamaParse · Airtable · Google Sheets · Gmail · HubSpot · Slack · Telegram · Whisper (Groq) · ElevenLabs.

Todos los servicios, salvo Anthropic, se usan en planes gratuitos.

---

## Cómo usar este repositorio

1. Entrá a la carpeta del módulo que te interese y leé su README.
2. En n8n, **Create workflow → ··· → Import from File** con cada `.json` de la carpeta.
3. Creá tus propias credenciales: los `.json` **no contienen** API keys ni tokens, solo referencias por nombre.
4. Publicá primero los sub-workflows (Workers, búsqueda en el manual y Juez), porque n8n no permite llamar sub-workflows sin publicar.

---

**Autor:** Ain Pellizzari · Curso AI Automation Avanzado
