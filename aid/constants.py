PROJECT_CATEGORY = 'PROYECTOS AREA IMPLANTACIONES'

JIRA_FIELDS = [
    'key', 'summary', 'status', 'issuetype', 'description',
    'created', 'resolved', 'updated',
    'timeoriginalestimate',   # Estimadas
    'timeestimate',           # Restantes
    'customfield_16301',      # Centros de implantación
    'customfield_10601',      # Fecha de inicio deseada
    'customfield_10602',      # Fecha de fin deseada
    'customfield_12001',      # Tipo de tarea
    'customfield_12302',      # Fecha inicio
    'customfield_12303',      # Fecha Fin
    'issuelinks',             # Enlaces a otras issues
    'customfield_16100',      # (R) Responsable
    'customfield_16000',      # Tipo de servicio
    'customfield_16002',      # Agrupadores
    'priority',
]

COLUMN_RENAME = {
    'Centros de implantación': 'CENTRO',
    'Key':                     'CLAVE',
    'Summary':                 'TITULO',
    'Descripción':             'DESCRIPCION',
    'Fecha Inicio':            'INICIO',
    'Fecha Fin':               'FIN',
    'Fecha de Actualización':  'ACTUALIZACION',
    'Issue Type':              'TIPO',
    'Tipo de Tarea':           'SUBTIPO',
    'Status':                  'ESTADO',
    'Estimadas':               'HBS_ESTIMADAS',
    'Restantes':               'HBS_RESTANTES',
    '(R) Responsable':         'RESPONSABLE_SERVICIO',
    'Tipo de servicio':        'TIPO_SERVICIO',
    'Agrupadores':             'AGRUPADOR',
    'Prioridad':               'PRIORIDAD',
}

PHASES = ['APS', 'RP', 'PRE', 'IMP', 'ARR', 'CON', 'EXT', 'PN3']

STATUS_MAP = {
    'Abierta':           'BACKLOG',
    'Cerrada':           'CERRADA',
    'Pdte. Información': 'BLOQUEADA',
}
STATUS_DEFAULT = 'EN_CURSO'

ISSUE_TYPE_TASK      = 'Tarea general'
ISSUE_TYPE_MILESTONE = 'Hito'
RELATION_BLOCKED_BY  = 'Es bloqueada por'

SHEET_REGISTROS           = 'REGISTROS'
SHEET_FASES               = 'FASES'
SHEET_BLOQUEOS            = 'BLOQUEOS'
SHEET_HBS                 = 'HBS'
SHEET_COMENTARIOS_BLOQUEO = 'COMENTARIOS_BLOQUEO'

GOOGLE_SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
]
