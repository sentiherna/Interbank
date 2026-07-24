# LexIA Diario

Carpeta portable para ejecutar diariamente el pipeline normativo LexIA version 10.

## Objetivo

El proceso corre todos los dias a las 10 AM y procesa las normas publicadas en la fecha de ejecucion. Tambien revisa el dia anterior para detectar publicaciones extraordinarias tardias que no hayan entrado en el reporte previo. Incluye domingos si hubiera publicacion. Mantiene la misma logica del pipeline que genero las metricas consolidadas:

- Fechas evaluadas: 194
- Normas analista: 316
- Alertas IA revisadas: 531
- TP: 316
- FP: 215
- FN: 0
- Recall: 100%
- Precision: 59.5%
- F1-score: 74.6%
- Coincidencia de nivel: 287 de 316, 90.8%

La corrida diaria descarga/revisa las normas del dia, usa la historia del analista en el Excel como memoria de clasificacion y envia un mail con las normas de interes para el banco, mas CSV y Excel adjuntos. La comparativa contra el Excel del analista se calcula con el dia anterior, porque la revision del analista llega con rezago. Antes de esa comparativa, el proceso vuelve a consultar El Peruano para el dia anterior y reprocesa ese dia si detecta publicaciones extraordinarias nuevas.

## Contenido

- `rag_pipeline_s3_diario_job_10.py`: pipeline principal de descarga, extraccion y clasificacion.
- `daily_lexia.py`: orquestador diario. Calcula fecha objetivo, ejecuta el pipeline, arma reporte y envia email.
- `lexia_local.py`: storage local compatible con la logica S3 del pipeline.
- `run_daily_lexia.sh`: wrapper operativo para ejecutar el proceso.
- `install_cron_10am.sh`: instala o actualiza la tarea diaria de cron a las 10 AM.
- `requirements.txt`: dependencias Python.
- `requirements_semantic.txt`: dependencias opcionales para embeddings + cross-encoder.
- `config/Comparativo de identificación de normas VF (1).xlsx`: referencia historica del analista.
- `config/reference.env`: URL del Excel historico en Drive.
- `config/.env_email`: configuracion SMTP, misma estructura que el proceso de Obligaciones Negociables.
- `config/github.env`: token `GITHUB_TOKEN` para GitHub Models/Copilot.
- `config/groq.env`: clave alternativa para Groq, si se usa ese backend.
- `config/credentials.sh`: credenciales AWS si se corre contra S3/prod.

Los archivos reales de credenciales no deben subirse a git. Los `.example` muestran el formato esperado.

## Flujo diario

1. `run_daily_lexia.sh` carga variables de `config/`.
2. Ejecuta `daily_lexia.py`.
3. Intenta actualizar `config/Comparativo de identificación de normas VF (1).xlsx` desde `REFERENCE_DRIVE_URL`.
4. Si Drive no entrega un XLSX descargable, usa la ultima copia local sin detener el proceso.
5. Si no se indica `--date`, toma automaticamente la fecha de ejecucion.
6. Llama a `rag_pipeline_s3_diario_job_10.py` con:
   - `--download-from-source`
   - `--llm-backend copilot`
   - `--copilot-model gpt-4o`
   - `--llm-max-contexts 3`
   - `--llm-min-score 2`
   - `--human-reference-file config/Comparativo de identificación de normas VF (1).xlsx`
7. El pipeline descarga todas las normas del dia, extrae texto y clasifica.
8. Prioriza candidatas al LLM con heuristicas y, si esta instalado el modulo semantico, con embeddings + cross-encoder contra el historico del analista.
9. Solo envia al LLM las candidatas de mayor interes; el resto se resuelve localmente con heuristicas.
10. Si el Excel del analista tiene una decision para esa fecha y norma, se usa como referencia.
11. Aplica reglas locales de negocio para casos recurrentes del analista. Por ejemplo, un Estado de Emergencia se considera `SI / INFORMATIVA` solo cuando corresponde a la norma publicada de PCM/Presidencia del Consejo de Ministros y la causa es desastres naturales o criminalidad/orden interno.
12. Para el reporte operativo del dia, se conservan solo filas donde `FECHA` y `FECHA_PUBLICACION` coinciden con el dia procesado. `FECHA_EMISION` se informa como dato, pero no excluye publicaciones. Si la identidad `TIPO_NORMA`/`NUMERO` parece venir de una cita interna, se marca en `IDENTIDAD_CONFIABLE` y `OBS_IDENTIDAD`, pero no se oculta la fila.
13. Antes de armar el reporte del dia, revisa `run_date - 1 dia` contra El Peruano. Si hay publicaciones nuevas/no incluidas en el reporte anterior, reprocesa ese dia con `--force` para incorporar extraordinarias tardias.
14. Para la comparativa contra el analista, se usa `run_date - 1 dia` y el CSV IA actualizado de ese dia si existe.
15. Se genera:
   - `output_batch/normas_YYYY-MM-DD.csv`
   - `reportes_diarios/lexia_diario_YYYYMMDD.html`
   - `reportes_diarios/lexia_diario_YYYYMMDD.xlsx`
   - `reportes_diarios/normas_reporte_YYYYMMDD.csv`
16. Se envia mail a `REPORT_EMAIL_TO`.

Controles incorporados:

- El listado oficial de El Peruano acompaña cada PDF descargado como respaldo de numero, tipo, emisor y descripcion. Si el OCR toma una cita interna, se conserva la identidad oficial para clasificar.
- Una alerta se emite solo por obligacion, adecuacion, sancion, aplicacion directa o seguimiento historico explicito. Referencias indirectas a sectores financiados, MYPE, antidumping, grupos de trabajo o actos internos no bastan por si solas.
- Si el Excel no tiene filas del analista para el dia comparado, la comparativa queda `pendiente`: no se generan falsos positivos ni metricas artificiales.
- El wrapper usa un bloqueo para evitar dos corridas simultaneas y trabaja con `LEXIA_TIMEZONE=America/Argentina/Buenos_Aires` por defecto.
- Si una corrida falla antes del reporte normal, el wrapper envia un correo de error con el log adjunto. El flag `--no-email` tambien desactiva este aviso.

## Configuracion inicial

```bash
cd /media/santi/Work/Interbank/LexIA_Diario
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Para activar la priorizacion semantica con embeddings + cross-encoder:

```bash
.venv/bin/pip install -r requirements_semantic.txt
```

Nota: esta dependencia instala PyTorch y puede ser pesada. En entornos productivos conviene definir una instalacion CPU/GPU controlada antes de habilitarla.

Revisar estos archivos:

```bash
cp config/.env_email.example config/.env_email
cp config/reference.env.example config/reference.env
cp config/github.env.example config/github.env
cp config/groq.env.example config/groq.env
cp config/credentials.sh.example config/credentials.sh
```

Completar los valores reales. Para modo local, `credentials.sh` puede quedar sin claves AWS.

## Ejecucion manual

Ejecutar la fecha de hoy y enviar email:

```bash
cd /media/santi/Work/Interbank/LexIA_Diario
bash run_daily_lexia.sh
```

Ejecutar una fecha puntual sin enviar email:

```bash
bash run_daily_lexia.sh --date 2026-05-27 --no-email --force
```

Ejecutar sin descargar PDFs, usando lo ya guardado localmente:

```bash
bash run_daily_lexia.sh --date 2026-05-27 --no-download --no-email --force
```

Cambiar cantidad maxima de normas enviadas al LLM:

```bash
bash run_daily_lexia.sh --date 2026-05-27 --llm-max-contexts 5 --force
```

Desactivar semantic search + cross-encoder para una corrida puntual:

```bash
bash run_daily_lexia.sh --date 2026-05-27 --disable-semantic-prioritization --force
```

Desactivar la revision de extraordinarias del dia anterior:

```bash
bash run_daily_lexia.sh --date 2026-07-02 --no-backfill-previous --force
```

## Extraordinarias tardias

En cada corrida diaria, antes de armar el mail, `daily_lexia.py` revisa nuevamente El Peruano para el dia anterior.

El proceso compara:

- la hoja `publicadas_fuente` guardada en el reporte del dia anterior;
- el manifiesto actual de publicaciones de El Peruano para esa misma fecha.

Si detecta publicaciones nuevas o no incluidas, reprocesa automaticamente el dia anterior con `--force`. Esto permite capturar publicaciones extraordinarias que El Peruano carga despues de la corrida original.

Cuando se detectan extraordinarias tardias, la lista queda guardada en `reportes_diarios/extraordinarias_prev_YYYYMMDD.csv`, donde `YYYYMMDD` corresponde al reporte del dia actual. Esto evita perder la trazabilidad si luego se regenera el reporte: aunque ya no sean "nuevas" en una corrida posterior, el mail puede seguir mostrando cuales fueron incorporadas.

El reporte del dia actual incluye:

- una seccion HTML llamada `Revision de extraordinarias del dia anterior`;
- una hoja Excel llamada `extraordinarias_prev`;
- metricas `backfill_previous_date`, `backfill_missing_count`, `backfill_display_count` y `backfill_rerun` en la salida de log.

Ejemplo validado:

```text
Corrida: 2026-07-02
Dia revisado: 2026-07-01
Publicadas actuales: 57
Publicadas en reporte previo: 46
Nuevas/no incluidas: 11
Reprocesado: SI
```

## Priorizacion semantica

El pipeline puede aplicar el flujo:

```text
Normas historicas del analista
        -> embeddings
        -> base vectorial en memoria
        -> semantic search contra normas nuevas
        -> cross-encoder para reranking
        -> top K normas candidatas
        -> LLM
```

La memoria historica se arma desde el Excel del analista usando las normas con `C. NORMATIVO = SI`. Para cada norma nueva del dia, el pipeline busca ejemplos historicos semanticamente parecidos. Luego el cross-encoder compara pares `norma nueva vs norma historica` y sube al LLM las candidatas con mayor similitud.

Parametros principales:

```bash
--semantic-embed-model sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
--semantic-cross-model cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
--semantic-top-k 12
--semantic-min-score 0.45
```

Si `sentence-transformers` no esta instalado o el modelo no se puede cargar, el proceso no falla: deja un aviso en el log y vuelve a la seleccion heuristica anterior.

Para confirmar que quedo disponible antes de pasar a produccion:

```bash
.venv/bin/python -c "from sentence_transformers import CrossEncoder, SentenceTransformer; print('Semantic OK')"
```

## Reglas locales principales

### Estado de Emergencia

Se clasifica como `INTERES_AL_BANCO = SI` y `NIVEL_IMPACTO = INFORMATIVA` solo si se cumplen todas estas condiciones:

- La norma publicada es un Decreto Supremo de PCM o Presidencia del Consejo de Ministros.
- El numero aparece como encabezado de la norma publicada, no solo como cita interna dentro de otro PDF.
- El texto indica que el Estado de Emergencia responde a desastres naturales o a criminalidad/orden interno.

Ejemplos de causas aceptadas:

- Desastres naturales: precipitaciones pluviales, peligro inminente, impacto de danos, inundaciones, sismos, sequia, deficit hidrico, colapso de alcantarillado.
- Criminalidad u orden interno: criminalidad, seguridad ciudadana, violencia, mineria ilegal, delitos conexos, grupos hostiles, control migratorio o fronterizo, PNP, orden y seguridad.

Ejemplo validado:

```text
096-2026-PCM -> SI / INFORMATIVA
Justificacion: Estado de Emergencia por criminalidad u orden interno; relevante para seguimiento del banco.
```

Si un Estado de Emergencia aparece solo como referencia dentro de otra norma, no se marca automaticamente como interes para el banco.

## Programar a las 10 AM

```bash
cd /media/santi/Work/Interbank/LexIA_Diario
bash install_cron_10am.sh
```

```bash
cd /media/santi/Work/Interbank/LexIA_Diario
bash install_cron_8am.sh
```

La linea instalada es equivalente a:

```cron
0 10 * * * cd /media/santi/Work/Interbank/LexIA_Diario && bash run_daily_lexia.sh >> /media/santi/Work/Interbank/LexIA_Diario/logs/cron_lexia_diario.log 2>&1
```

Ver cron instalado:

```bash
crontab -l
```

Ver logs:

```bash
tail -f /media/santi/Work/Interbank/LexIA_Diario/logs/cron_lexia_diario.log
```

## Email

El envio usa la misma estructura SMTP del proceso de Obligaciones Negociables:

```bash
REPORT_EMAIL_TO=mail1@dominio.com,mail2@dominio.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=usuario@gmail.com
SMTP_PASSWORD=app_password
SMTP_FROM=usuario@gmail.com
```

En la configuracion actual local, `REPORT_EMAIL_TO` apunta a `shernandez2@intercorp.com.pe`.

El mail incluye:

- resumen HTML en el cuerpo;
- Excel diario adjunto;
- CSV filtrado del reporte diario adjunto.

El CSV original completo queda en `output_batch/`. El CSV adjunto al mail queda en `reportes_diarios/` y aplica los filtros operativos del reporte.

## LLM

Backend default:

- `--llm-backend copilot`
- modelo: `gpt-4o`
- token: `GITHUB_TOKEN`
- endpoint usado por el pipeline: GitHub Models/Copilot compatible con chat completions.

Backend alternativo:

- `--llm-backend groq`
- requiere `GROQ_API_KEY`

## Excel del analista en Drive

El archivo historico vive en Drive y se configura en `config/reference.env`:

```bash
REFERENCE_DRIVE_URL=https://docs.google.com/spreadsheets/d/1vO3fQfZqCtDX8HuHjmEuf7Z4guSfIbSv/edit?gid=1405822604#gid=1405822604
```

En cada corrida, `daily_lexia.py` intenta descargarlo y reemplazar la copia local:

`config/Comparativo de identificación de normas VF (1).xlsx`

Importante: para una corrida automatica por cron, el archivo debe ser descargable por el proceso. Si el Drive esta privado y no hay autenticacion Google configurada, Google responde 401/HTML y el proceso usa la ultima copia local disponible. En ese caso la corrida no falla, pero no toma la actualizacion mas reciente del Drive.

Columnas principales:

- `FECHA DE PUBLICACIÓN`
- `N° NORMA`
- `C. NORMATIVO`
- `INTERÉS AL BANCO`
- `COMENTARIO / DESCRIPCIÓN DE LA NORMA`

Si se actualiza el Excel con nueva historia o nuevas validaciones del analista y el archivo es descargable por el proceso, la siguiente corrida lo toma automaticamente. Para reprocesar una fecha ya generada, usar `--force`.

Para omitir la sincronizacion y usar solo la copia local:

```bash
bash run_daily_lexia.sh --no-sync-reference
```

## Migracion a otra laptop o prod

1. Copiar completa la carpeta `LexIA_Diario`.
2. Crear `.venv` e instalar `requirements.txt`.
3. Completar `config/.env_email`, `config/github.env` y, si aplica, `config/credentials.sh`.
4. Validar una fecha puntual:

```bash
bash run_daily_lexia.sh --date 2026-05-27 --no-email --force
```

5. Validar envio:

```bash
bash run_daily_lexia.sh --date 2026-05-27 --force
```

6. Instalar cron:

```bash
bash install_cron_8am.sh
```

En prod se puede reemplazar cron por systemd, Airflow, Control-M u otro scheduler. El contrato operativo es ejecutar `bash run_daily_lexia.sh`.
