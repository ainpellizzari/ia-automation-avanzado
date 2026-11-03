# Checkpoint 6 · Voice AI: Canal de voz de NexoFlow por Telegram

Archivo del workflow: **`canal_voz_modulo6_pellizzari_ain.json`** (workflow `M6 - Canal Voz`).
Documentación completa, con capturas, calibración y pruebas: **[`PreEntrega_Modulo6_AinPellizzari.pdf`](PreEntrega_Modulo6_AinPellizzari.pdf)**.

## Caso de uso

Un cliente le manda una **nota de voz** al bot de Telegram **NexoFlow Asistente** con una consulta comercial ("¿cuánto sale el plan más básico?"). El bot le responde con un **audio** generado a partir del manual oficial de NexoFlow (la base de conocimiento del M5), y debajo del audio escribe la **fuente** consultada. Si el audio no se entiende, le pide que lo repita.

## Arquitectura

```
[Nota de Voz Entrante: Telegram Trigger] → [Descargar Audio: Telegram Get file]
  → [Ajustar Formato Audio: .oga → .ogg] → [Transcribir Audio (Whisper): Groq, whisper-large-v3]
     ├─ error ──────────────────────────────────────────────▶ [Pedir Repetir Audio]
     └─ [¿Audio Entendible?: IF con 4 condiciones] ── no ──▶ [Pedir Repetir Audio]
           │ sí
        [Limpiar Datos (sin audio)] → [Agente de Voz: Claude + memoria por chat_id
                                        + tool buscar_manual_nexoflow (M5)]
        → [Separar Respuesta y Fuente] → [Generar Voz (ElevenLabs)] → [Responder con Voz]
```

| Pieza | Decisión |
|---|---|
| Transcripción | Whisper **large v3** servido por **Groq** (gratis, API compatible con OpenAI), idioma `es`, formato `verbose_json` |
| Contingencia | Whisper inventa texto ante el silencio ("¿Cómo te llamas?", "Gracias."). El IF exige texto de 3+ caracteres, sin "Amara.org", `no_speech_prob` < 0.15 y `avg_logprob` > -0.45, calibrados con casos reales |
| Agente | Reutiliza la herramienta RAG del M5. Reglas de voz: máximo 200 caracteres, sin links, emojis ni listas, números como se pronuncian. Salida en dos líneas: `RESPUESTA` (se escucha) y `FUENTE` (se lee) |
| Voz | ElevenLabs `eleven_multilingual_v2`, stability 0.5, similarity_boost 0.75. La respuesta se corta a 300 caracteres antes de enviarla (guardrail de costo) |
| Compliance | La voz es un dato personal: después de Whisper solo viaja texto, y el workflow está configurado para **no guardar ejecuciones** |

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

| # | Nota de voz | Resultado |
|---|---|---|
| 1 | "¿Cuánto tarda en estar lista una automatización?" | Audio con el dato y la fuente "5.1 Plazos totales por plan" ✅ |
| 2 | "¿Tienen oficina en Córdoba?" | Trabajo remoto desde CABA, fuente "1. Quiénes somos" ✅ |
| 3 | "¿Puedo pagar con criptomonedas?" (no figura en el manual) | "No sé…", sin fuente ✅ |
| 4 | Silencio | Mensaje pidiendo repetir ✅ |
| 5 | "Sí, contame más" (dos veces) | Vuelve a consultar el manual, datos nuevos y cierre variado ✅ |
| 6 | "Pasame la documentación para saber cuánto sale" | Da los precios y ofrece que un asesor envíe la documentación ✅ |

Las mejoras surgidas del uso real (cierre repetido, falsa retractación por la memoria, silencio que pasó el filtro y pedido de documentación) están en la sección 8 del PDF.
