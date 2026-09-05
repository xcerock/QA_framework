# Banco de pruebas: calidad en respuestas de IA

Herramienta para las dos demostraciones en vivo de la ponencia **"Calidad en respuestas de IA: del wow al rigor"**.

Backend en FastAPI, frontend sin framework ni build. La llave de API vive en el servidor y nunca llega al navegador.

## Las dos demos

**1 · El wow que engaña.** La misma pregunta con dos instrucciones de sistema: una sin salvaguardas y otra que exige fuentes, niveles de confianza y permiso explícito para no saber. Un botón revela la nota de verificación con el dato real.

**2 · Consistencia.** Lanza la misma pregunta N veces en paralelo y muestra las respuestas en cuadrícula, con dos métricas separadas y las palabras volátiles resaltadas.

## Arrancar

El entorno se gestiona con **conda** (`environment.yml`, Python 3.12).

### Windows (PowerShell)

```powershell
copy .env.example .env    # pon tu ANTHROPIC_API_KEY
.\run.ps1
```

El script crea el entorno conda si no existe, instala dependencias y levanta el
servidor en `http://127.0.0.1:8000`.

| Parámetro | Para qué |
|---|---|
| `-NoReload` | Arranque rápido, sin recarga automática. **Úsalo el día del evento.** |
| `-Port 9000` | Cambiar el puerto |
| `-Recreate` | Borrar y volver a crear el entorno desde cero |

Si PowerShell bloquea el script por la política de ejecución:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

Si `conda` no está en el PATH, abre una *Anaconda Prompt*, o carga el hook antes:

```powershell
& "$env:USERPROFILE\AppData\Local\miniconda3\shell\condabin\conda-hook.ps1"
```

> **Ojo con `--reload` en Windows.** El proceso hijo del recargador tarda unos
> **40 segundos** en levantar la primera vez, porque Windows crea el subproceso
> con `spawn` y vuelve a importar todo. No está colgado, está arrancando. Con
> `-NoReload` levanta en segundos.

### macOS y Linux

```bash
cp .env.example .env      # pon tu ANTHROPIC_API_KEY
./run.sh
```

### A mano, en cualquier sistema

```bash
conda env create -f environment.yml
conda activate qa-framework
uvicorn app.main:app --reload
```

## Las dos métricas, y por qué son dos

Esta separación es el corazón de la demo 2.

**Divergencia léxica.** Similitud de Jaccard sobre el vocabulario, promediada entre todos los pares de respuestas. Mide cuánto cambia la redacción.

**Divergencia en los datos.** Lo mismo, pero solo sobre números, años, cifras y porcentajes extraídos de cada respuesta.

La diferencia entre ambas es el momento pedagógico de la charla:

| Situación | Léxica | Datos | Lectura |
|---|---|---|---|
| Mismo hecho, redacción distinta | 89% | 0% | El modelo es consistente. Reformula, pero no se contradice. |
| Hechos distintos | 75% | 50% | El modelo se está contradiciendo. Esto sí es un problema. |
| Respuestas idénticas | 0% | 0% | Determinista, o pregunta demasiado cerrada. |

Una divergencia léxica alta no prueba nada por sí sola. Si presentas solo ese número exageras el problema, y alguien del público con criterio te lo va a señalar. Muestra los dos.

La extracción de datos es deliberadamente simple: una expresión regular sobre números. No sabe que "1968" y "mil novecientos sesenta y ocho" son lo mismo. Para producción querrías similitud semántica o extracción de afirmaciones. Para mostrar fragilidad en un escenario, esto basta y se explica en una frase.

## Sobre el muestreo

Los modelos de la generación Sonnet 5 y Opus 5 gestionan el muestreo por su cuenta y **rechazan `temperature` con un error 400**. El control equivalente es `output_config.effort`, que va en el nivel superior de la petición.

El cliente hace tres cosas para que esto no reviente una demo en vivo:

1. No envía `temperature` a los modelos que se sabe que la rechazan.
2. Si aun así llega un 400 quejándose del parámetro, reintenta una vez sin él.
3. La interfaz oculta el campo de temperatura cuando no aplica, para que nadie toque una perilla desconectada en pleno escenario.

Esto mejora la demo. Ya no puedes fijar la temperatura en cero para esconder la variación: el modelo decide su propio muestreo y la variación sigue ahí. Si quieres mostrar el contraste con un modelo que sí acepta temperatura, cambia a `claude-haiku-4-5-20251001` en Ajustes y el campo reaparece.

## Modo repetición

La red de una sala de conferencias es el riesgo más real de una demo en vivo.

Cada corrida se guarda automáticamente en `data/`. Si el día del evento algo falla, activa el interruptor **Modo repetición** en la barra superior: la interfaz se comporta igual, sirviendo las respuestas guardadas, sin llamar a la API.

También puedes forzarlo desde el arranque con `REPLAY_MODE=true` en el `.env`.

Practica el cambio antes. Debe tomarte menos de diez segundos.

## Atajos para el escenario

| Tecla | Acción |
|---|---|
| `1` | Ir a la demo 1 |
| `2` | Ir a la demo 2 |
| `Enter` | Ejecutar la demo activa |
| `v` | Revelar la verificación (demo 1) |

Funcionan solo cuando el foco no está en un campo de texto. Haz clic en un área vacía antes de usarlos.

## API

| Método | Ruta | Qué hace |
|---|---|---|
| `GET` | `/api/config` | Modelos disponibles, valores por defecto, corridas guardadas |
| `GET` | `/api/health` | Estado del servidor y si hay llave configurada |
| `POST` | `/api/ask` | Una pregunta, una respuesta |
| `POST` | `/api/consistency` | N ejecuciones en paralelo con métricas |

Documentación interactiva en `/docs` mientras el servidor corre.

## Estructura

```
app/
  main.py           rutas de FastAPI
  config.py         ajustes desde .env
  schemas.py        contratos de entrada y salida
  claude_client.py  llamadas a la API, manejo del muestreo
  metrics.py        divergencia léxica y de datos
  replay.py         respuestas guardadas para el modo repetición
static/
  index.html        interfaz
  styles.css        panel de instrumentos, pensado para proyección
  app.js            lógica del cliente
data/               corridas guardadas (ignorado por git)
environment.yml     entorno conda
run.ps1             arranque en Windows
run.sh              arranque en macOS y Linux
```

## Antes de subir al escenario

- Corre la pregunta de la demo 1 varias veces durante la semana previa. Los modelos cambian de versión sin aviso y el fallo que buscas puede desaparecer.
- Escribe la nota de verificación con el dato real y su fuente, desde el botón "Editar esta nota". No improvises eso frente a la sala.
- Corre la demo 2 al menos una vez para dejar respuestas guardadas.
- Sube el zoom del navegador a 125% o 150% y comprueba la legibilidad desde el fondo.
- Si vas a compartir el escritorio completo, revisa que ninguna terminal muestre el `.env`.

## Las cuatro dimensiones del framework

| Dimensión | Pregunta | ¿Está en la herramienta? |
|---|---|---|
| Precisión | ¿El dato es correcto? | Parcial, vía la nota de verificación |
| Contexto | ¿Entendió lo que realmente pedí? | No |
| Consistencia | ¿Responde igual ante la misma pregunta? | Sí, demo 2 |
| Confianza calibrada | ¿Sabe cuándo no sabe? | Sí, comparando los dos prompts de la demo 1 |

Las dos casillas vacías son buenas candidatas si alguien quiere contribuir.
