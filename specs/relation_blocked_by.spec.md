# Funcionalidad: Actualizar el tipo de relación de bloqueo en Jira

## Contexto
La constante RELATION_BLOCKED_BY define el nombre de la relación Jira que identifica qué issues bloquean a otras. Su valor actual ('Es bloqueada por') no coincide con el nombre real de la relación en el servidor Jira, que es 'Depende de'. Esto provoca que get_blocks_projects() no encuentre ningún bloqueo.

## Comportamiento esperado

### La constante RELATION_BLOCKED_BY toma el valor 'Depende de'
En aid/constants.py la línea pasa de `RELATION_BLOCKED_BY = 'Es bloqueada por'` a `RELATION_BLOCKED_BY = 'Depende de'`.

### get_blocks_projects() filtra correctamente las relaciones de bloqueo
Al comparar df_relations['RELACION'] == RELATION_BLOCKED_BY se obtienen las issues que dependen de otras, que son las consideradas bloqueadas.

## Criterios de aceptación

### El valor de RELATION_BLOCKED_BY es exactamente 'Depende de'

### No se modifica ningún otro archivo fuera de aid/constants.py
El resto del código que consume RELATION_BLOCKED_BY (get_blocks_projects) no necesita cambios al importar la constante directamente.
