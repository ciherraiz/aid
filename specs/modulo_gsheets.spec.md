# Funcionalidad: [Refactorizar todo las funciones relacionadas con Google Sheets] 
## Contexto: [el módulo diario.py tiene varias funciones relacionadas con la lectura y grabación de datos en Google Sheets. Deberían encapsularse todos esos métodos en un nuevo módulo denominado gsheets.py]
## Comportamiento esperado :
### [Pasar las funciones que actuan con Google Sheets a un nuevo módulo llamado gsheets.py]
### [El módulo diario.py debe realizar las llamadas al nuevo módulo sheets.py para mantener el comportamiento actual]
## Criterios de aceptación
### [todas las funciones que operan google gsheets ya no están definidas en diario.py]
### [en diario.py sólo debe quedar el método main()]
### [el nuevo módulo sheets.py debe residir en la carpeta aid junto al fichero jira_aid.py]