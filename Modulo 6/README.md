# Checkpoint 6 · Voice AI: Canal de voz de NexoFlow por Telegram

Archivo del workflow: **`canal_voz_modulo6_pellizzari_ain.json`** (workflow `M6 - Canal Voz`).
Documentación completa, con capturas, calibración y pruebas: **[`PreEntrega_Modulo6_AinPellizzari.pdf`](PreEntrega_Modulo6_AinPellizzari.pdf)**.

## Caso de uso

Un cliente le escribe al bot de Telegram **NexoFlow Asistente** con una consulta comercial ("¿cuánto sale el plan más básico?"). Si manda una **nota de voz**, el bot le responde con un **audio**; si **escribe**, le responde por escrito. La respuesta sale del manual oficial de NexoFlow (la base de conocimiento del M5) e incluye la **fuente** consultada. Si el audio no se entiende, le pide que lo repita; si manda otro tipo de mensaje (foto, sticker), le explica qué puede recibir; y si pide hablar con una persona, el equipo recibe un aviso en Slack.

## Arquitectura

```
[Nota de Voz Entrante] → [Switch]
  voz      → [Descargar Audio] → [Ajustar Formato Audio] → [Transcribir Audio (Whisper)]
               ├─ error → [Pedir Repetir Audio]
               └─ [¿Audio Entendible?] ── no → [Pedir Repetir Audio]
                     sí → [Limpiar Datos (sin audio)] ──┐
  texto    → [Datos del Texto] ─────────────────────────┤
  Fallback → [Tipo No Soportado]                        ▼
[Agente de Voz: Claude + memoria por chat_id + tool buscar_manual_nexoflow (M5)]
  → [Separar Respuesta y Fuente]
       ├→ [¿Responder con audio?] sí → [Generar Voz (ElevenLabs)] → [Responder con Voz]
       │                          no → [Responder con Texto]
       └→ [¿Hay que escalar?] sí → [Avisar Escalamiento] (Slack #operaciones)
```

| Pieza | Decisión |
|---|---|
| Transcripción | Whisper **large v3** servido por **Groq** (gratis, API compatible con OpenAI), idioma `es`, formato `verbose_json` |
| Contingencia | Whisper inventa texto ante el silencio ("¿Cómo te llamas?", "Gracias."). El IF exige texto de 3+ caracteres, sin "Amara.org", `no_speech_prob` < 0.15 y `avg_logprob` > -0.45, calibrados con casos reales |
| Agente | Reutiliza la herramienta RAG del M5. Reglas de voz: máximo 200 caracteres, sin links, emojis ni listas, números como se pronuncian. Salida en dos líneas: `RESPUESTA` (se escucha) y `FUENTE` (se lee) |
| Voz | ElevenLabs `eleven_multilingual_v2`, stability 0.5, similarity_boost 0.75. El prompt pide 200 caracteres en voz y 400 en texto; el código aplica un techo de seguridad de 1,5 veces (300 y 600) |
| Canales | Switch por tipo de mensaje: se responde en el mismo formato de entrada (voz → audio, texto → texto) |
| Escalamiento | Aviso automático a Slack `#operaciones` cuando el agente deriva a un asesor |
| Compliance | La voz es un dato personal: después de Whisper solo viaja texto, el workflow **no guarda ejecuciones** y Groq tiene **Zero Data Retention** activado. ElevenLabs solo recibe el texto de la respuesta |

## Requisitos y credenciales

| Servicio | Credencial en n8n | Plan |
|---|---|---|
| Telegram (bot creado con @BotFather) | Telegram API | Gratis |
| Groq | Header Auth: `Authorization: Bearer <key>` | Gratis |
| ElevenLabs | Header Auth: `xi-api-key: <key>`, con permiso solo de Text to Speech | Gratis (~10.000 caracteres por mes) |
| Anthropic | Anthropic API | Pago por uso |

El JSON no contiene tokens ni keys: solo referencias a las credenciales por nombre.

## Cómo importarlo

1. Importá y **publicá** primero el sub-workflow `M5 - Buscar en Manual` (carpeta `Modulo 5`): es la herramienta del agente.
2. En n8n: **Create workflow → ··· → Import from File** → `canal_voz_modulo6_pellizzari_ain.json`.
3. Creá las 4 credenciales y asignalas en los nodos. En `buscar_manual_nexoflow`, elegí tu sub-workflow del M5.
4. En `Generar Voz (ElevenLabs)`, reemplazá el Voice ID de la URL por una voz predeterminada de tu cuenta.
5. Probá con **Execute workflow** y una nota de voz al bot. Telegram admite un solo receptor por bot: si el workflow está publicado, despublicalo para probar desde el editor y volvé a publicarlo al terminar.

## Pruebas

| # | Caso | Resultado |
|---|---|---|
| 1 | Voz real: "¿Cuánto tarda la implementación?" | Audio con la fuente "5.1 Plazos totales por plan" ✅ |
| 2 | Silencio | Whisper inventa "¿Qué pasa?", el IF lo descarta y pide repetir ✅ |
| 3 | Audio corrupto (extensión inválida) | Groq responde 400, salida Error y pedido de repetir ✅ |
| 4 | Transcripción vacía | False en el IF y pedido de repetir ✅ |
| 5 | Mensaje escrito: "¿Cuánto sale el plan Inicial?" | Respuesta escrita con cifras y fuente ✅ |
| 6 | Sticker | Mensaje explicando que recibe voz o texto ✅ |
| 7 | "Quiero hablar con una persona" | Derivación y aviso en Slack ✅ |

Las mejoras surgidas del uso real están en la sección 8 del PDF, y las correcciones de la devolución (canal multimodal, escalamiento y batería de pruebas), en la sección 9.
