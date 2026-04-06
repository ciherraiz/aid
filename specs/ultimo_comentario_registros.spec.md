# Funcionalidad: Añadir último comentario de cada issue en la hoja REGISTROS

## Contexto
Para cada issue que aparece en la hoja REGISTROS se quiere mostrar el comentario más reciente publicado en Jira, junto con su fecha y autor, sin necesidad de acceder a Jira directamente.

## Comportamiento esperado

### Se añade la columna FECHA_ULTIMO_COMENTARIO
Contiene la fecha de creación del comentario más reciente de la issue. Si la issue no tiene comentarios, el valor es vacío (NA).

### Se añade la columna AUTOR_ULTIMO_COMENTARIO
Contiene el nombre del autor (`displayName`) del comentario más reciente. Si la issue no tiene comentarios, el valor es vacío (NA).

### Se añade la columna ULTIMO_COMENTARIO
Contiene el texto (`body`) del comentario más reciente. Si la issue no tiene comentarios, el valor es vacío (NA).

### Los tres campos se incluyen al final de la hoja REGISTROS
No se crean hojas adicionales.

### Los errores por issue individual no detienen la ejecución
Si falla la llamada de comentarios para una issue concreta, se registra un warning y la issue tendrá NA en las tres columnas.

## Criterios de aceptación

### La hoja REGISTROS incluye las columnas FECHA_ULTIMO_COMENTARIO, AUTOR_ULTIMO_COMENTARIO y ULTIMO_COMENTARIO

### El valor es el comentario con la fecha de creación más alta (el más reciente)

### Issues sin comentarios tienen NA en las tres columnas

### Issues con error al obtener comentarios tienen NA en las tres columnas y se registra un warning en el log
