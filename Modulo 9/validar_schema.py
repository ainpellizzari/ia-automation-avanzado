"""Valida el JSON Schema del log y lo prueba contra logs reales de la planilla M8 - Registro QA."""
import csv, json, sys
from jsonschema import Draft7Validator

SCHEMA = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://nexoflow.example/schemas/log-v2.json",
  "title": "LogNexoFlow v2",
  "type": "object",
  "required": ["traceId", "timestamp", "environment", "nodeName", "toolOutput", "systemPromptSnapshot", "confidenceScore"],
  "properties": {
    "traceId": {"type": "string", "pattern": "^tr-\\d{8}-\\d{6}-\\d+$"},
    "executionId": {"type": "string", "pattern": "^\\d+$"},
    "timestamp": {"type": "string", "format": "date-time"},
    "environment": {"type": "string", "enum": ["dev", "prod"]},
    "nodeName": {"type": "string", "minLength": 1},
    "toolOutput": {"type": "string", "maxLength": 500},
    "systemPromptSnapshot": {"type": "string", "minLength": 1},
    "confidenceScore": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
    "veredicto": {"type": "string", "enum": ["ACEPTADO", "CORREGIR", "RECHAZADO", "SIN_JUEZ"]},
    "intento": {"type": "integer", "minimum": 1, "maximum": 3},
    "arquitectura": {"type": "string"}
  },
  "additionalProperties": False
}

Draft7Validator.check_schema(SCHEMA)          # el esquema en sí es draft-07 válido
v = Draft7Validator(SCHEMA)

rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
logs = [(r["traceId"], json.loads(r["Log_JSON"])) for r in rows if r.get("Log_JSON", "").strip()]

# Log de soporte: hoy el Worker Soporte no escribe en la planilla; se arma con los datos reales de la ejecución 473
soporte = {"traceId": "tr-20261114-235840-472", "executionId": "473", "timestamp": "2026-11-14T20:58:59.000-03:00",
           "environment": "dev", "nodeName": "Clasificar Ticket",
           "toolOutput": "FALLA_TECNICA · ALTA · Bot dejó de funcionar; consulta costo de mejorar plan para atención 24 horas.",
           "systemPromptSnapshot": "soporte-v2", "confidenceScore": None}
logs.append(("tr-20261114-235840-472", soporte))

ok = 0
for tid, log in logs:
    errs = list(v.iter_errors(log))
    print(("OK   " if not errs else "FALLA"), tid, log.get("veredicto", "-"), [e.message for e in errs])
    ok += not errs
print(f"{ok}/{len(logs)} logs válidos")

# negativo: un log mal formado tiene que fallar
malo = dict(logs[0][1]); malo["traceId"] = "trace-434"; malo["confidenceScore"] = 5
print("Log mal formado detectado:", [e.message for e in v.iter_errors(malo)])
json.dump(SCHEMA, open("log_schema_v2.json", "w"), ensure_ascii=False, indent=2)
