# Funcionalidad: Restringir la extracción del último comentario a issues BLOQUEADAS

## Contexto
Tras incorporar get_last_comments() al flujo principal, el tiempo de ejecución del script aumentó significativamente porque se llama a la API de Jira una vez por cada issue del proyecto. Solo es relevante conocer el último comentario de las issues cuyo ESTADO_AGRUPADO es 'BLOQUEADA', ya que son las que requieren seguimiento activo.

## Comportamiento esperado

### get_last_comments() solo se invoca para las issues con ESTADO_AGRUPADO == 'BLOQUEADA'
En get_issues_projects(), el filtro se aplica antes de llamar al método, reduciendo el número de llamadas a la API de Jira al subconjunto de issues bloqueadas.

### Las issues no bloqueadas tienen NA en las tres columnas de comentario
Al hacer el merge left por CLAVE, las issues que no estaban en el subconjunto filtrado quedan con NA en FECHA_ULTIMO_COMENTARIO, AUTOR_ULTIMO_COMENTARIO y ULTIMO_COMENTARIO.

### El resto del comportamiento de get_last_comments() no cambia
El método en sí no se modifica; el filtro se aplica en el punto de llamada dentro de get_issues_projects().

## Criterios de aceptación

### Solo se realizan llamadas a la API de Jira para issues con ESTADO_AGRUPADO == 'BLOQUEADA'

### Issues con cualquier otro ESTADO_AGRUPADO tienen NA en las tres columnas de comentario en REGISTROS

### El número de llamadas a la API se reduce al número de issues bloqueadas, mejorando el tiempo de ejecución
