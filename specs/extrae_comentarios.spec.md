# Funcionalidad: [get_comments] 
## Contexto: [función denominada get_comments que extrae los comentarios de las issues que recibe por parámetro, devolviendo un dataframe con dichos comentarios]
## Comportamiento esperado :
### [la función recibe una lista con las claves de las issues y extrae los comentarios de esas issues de jira para crear un dataframe]
### [los datos mínimos a almacenar por cada comentario son clave (CLAVE), fecha (FECHA_COMENTARIO), autor (AUTOR_COMENTARIO) y contenido del comentario (COMENTARIO)]
## Criterios de aceptación
### [La lista de issues debe la columna CLAVE_BLOQUEO del dataframe que se genera con el método get_blocks_projects]
### [Si no hubiera ningún comentario o la lista recibida como parámetro estuviera vacía, gestiono la excepción y devuelvo un dataframe vacío]
### [El resultado debe ser almacenado mediante una llamada al método actualizar_hoja en diario.py. La hoja debe llamarse COMENTARIOS_BLOQUEO]