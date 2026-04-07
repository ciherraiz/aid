# Funcionalidad: Prorrateo histórico de HBS para issues cerradas

## Contexto
Actualmente `calculate_hbs()` aplica dos recortes que hacen invisibles las issues cerradas:
1. `INICIO_PRORR = INICIO.clip(lower=hoy)` — elimina la historia pasada de cada issue.
2. Filtro `FIN_PRORR >= hoy` — descarta todas las issues cuyo FIN ya pasó, que son precisamente las cerradas.

El resultado es que la columna CERRADA en la hoja HBS siempre vale 0.

Se quiere incorporar un **camino histórico** para issues con `ESTADO_AGRUPADO == 'CERRADA'`:
usar sus fechas INICIO/FIN originales sin recorte, prorratear `HBS_ESTIMADAS` entre todos
los meses que abarca su período planificado (incluyendo meses pasados), y unir el resultado
con el cálculo prospectivo existente (issues abiertas/en curso/bloqueadas).

## Comportamiento esperado

### [Las issues con ESTADO_AGRUPADO == 'CERRADA' se procesan por un camino separado dentro de `calculate_hbs()`]

### [Para issues CERRADAS: INICIO_PRORR = INICIO original (sin clip a hoy) y FIN_PRORR = FIN original; no se aplica el filtro `FIN_PRORR >= hoy`]

### [Para issues NO CERRADAS: se mantiene el comportamiento actual (clip a hoy + filtro FIN >= hoy)]

### [Ambos subconjuntos (CERRADAS e históricas vs. abiertas y prospectivas) se concatenan con `pd.concat` antes del groupby, de forma que el resto del pipeline (explosión por mes, prorrateo, groupby, pivot) se ejecuta una única vez sobre el DataFrame combinado]

### [La métrica relevante para CERRADAS es HBS_ESTIMADAS (HBS_RESTANTES es 0 en Jira al cerrar una issue); el pipeline no necesita cambio adicional porque ya calcula ambas columnas: la columna CERRADA aparecerá con valores en el pivot de estimadas y con 0 en el pivot de restantes, lo cual es correcto]

### [Los meses resultantes para issues CERRADAS pueden ser anteriores a hoy; la hoja HBS mostrará filas con MES en el pasado para el estado CERRADA]

## Criterios de aceptación

### [La columna CERRADA en el pivot de HBS_ESTIMADAS (_EST) contiene valores > 0 para los meses en que hubo issues cerradas planificadas]

### [La columna CERRADA en el pivot de HBS_RESTANTES sigue siendo 0 (comportamiento correcto: no quedan horas restantes en issues cerradas)]

### [Las columnas de estados abiertos (BACKLOG, EN_CURSO, BLOQUEADA) conservan exactamente los mismos valores que antes de este cambio]

### [La suma de HBS_ESTIMADAS de issues CERRADAS en la hoja HBS coincide con la suma de HBS_ESTIMADAS de esas mismas issues en la hoja REGISTROS]
