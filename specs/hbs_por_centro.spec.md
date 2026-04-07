# Funcionalidad: Desagregar HBS por CENTRO dentro de cada SOLUCION

## Contexto
Actualmente la hoja HBS agrega el prorrateo de horas estimadas/restantes únicamente a nivel de SOLUCION y MES. Se requiere mayor granularidad desagregando también por CENTRO (campo 'Centros de implantación' de Jira), de forma que cada fila represente una combinación única de SOLUCION + CENTRO + MES. Las primeras columnas del resultado deben ser ID, SOLUCION, CENTRO (en ese orden), tal como ya se hace en la hoja FASES.

## Comportamiento esperado

### [La columna CENTRO debe incluirse en la selección inicial de columnas dentro de `calculate_hbs()`]
### [El groupby debe incluir CENTRO: `["SOLUCION", "CENTRO", "MES", "ESTADO_AGRUPADO"]`]
### [Los pivot_table deben usar `index=['SOLUCION', 'CENTRO', 'MES']` en lugar de `['SOLUCION', 'MES']`]
### [El DataFrame resultante debe incluir una columna ID al inicio, calculada como SOLUCION + CENTRO, igual al patrón ya usado en diario.py para df_milestones]
### [La columna ID debe insertarse en `diario.py` antes de escribir la hoja HBS, siguiendo el mismo patrón que FASES]

## Criterios de aceptación

### [Las primeras columnas de la hoja HBS son: ID, SOLUCION, CENTRO, MES, …]
### [Cada fila representa una combinación única de SOLUCION + CENTRO + MES]
### [Issues sin CENTRO asignado se agrupan bajo un valor vacío o NaN (sin eliminar el registro)]
### [Los totales de HBS a nivel de SOLUCION+MES, sumando todos sus CENTROs, coinciden con los valores previos a este cambio]
