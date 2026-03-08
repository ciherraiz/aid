# CLAUDE.md — Proyecto aid

## Descripción
Script de extracción diaria de datos de Jira hacia Google Sheets para seguimiento de proyectos del área de implantaciones.

## Estructura

```
aid/
├── aid/                  # Paquete principal
│   ├── __init__.py       # Exporta JiraAID, versión 0.1.0
│   ├── jira_aid.py       # Clase JiraAID (lógica principal)
│   └── constants.py      # Constantes: campos Jira, columnas, estados, fases
├── scripts/
│   └── diario.py         # Entry point de ejecución diaria
├── requirements.txt
└── setup.py
```

## Flujo de datos

```
Jira API → JiraAID → DataFrames → Google Sheets (4 hojas)
```

## Variables de entorno requeridas

| Variable             | Descripción                                |
|----------------------|--------------------------------------------|
| `JIRA_URL`           | URL del servidor Jira                      |
| `JIRA_USER`          | Usuario Jira                               |
| `JIRA_PASS`          | Contraseña/token Jira                      |
| `GOOGLE_CREDENTIALS` | JSON de credenciales de service account    |
| `SPREADSHEET_ID`     | ID del Google Sheet destino                |

## Hojas de Google Sheets generadas

| Hoja        | Contenido                                       |
|-------------|--------------------------------------------------|
| `REGISTROS` | Issues de proyectos (DataFrame principal)        |
| `FASES`     | Pivot de horas por fase (APS, RP, PRE, IMP, ...) |
| `BLOQUEOS`  | Issues bloqueadas y sus bloqueantes              |
| `HBS`       | Prorrateo de horas estimadas/restantes por mes   |

## Clase JiraAID (aid/jira_aid.py)

- `get_issues_projects()` — extrae issues de proyectos en la categoría `PROYECTOS AREA IMPLANTACIONES`
- `get_issues(jql)` — paginación con reintentos (backoff exponencial), batch de 100
- `issues_to_df(issues)` — convierte issues a DataFrame y renombra columnas según `COLUMN_RENAME`
- `clean_issues(df)` — normaliza fechas, calcula DIAS, convierte HBS de segundos a horas, mapea ESTADO_AGRUPADO
- `get_blocks_projects()` — obtiene issues bloqueantes y las cruza con las bloqueadas
- `calculate_hbs()` — prorrateo de horas por mes expandiendo por períodos
- `get_milestone_data()` — pivot de fases por SOLUCION/CENTRO
- `extract_relations()` — extrae relaciones inward entre issues

## Constantes (aid/constants.py)

Todos los literales importantes están centralizados aquí: campos Jira, mapeo de columnas, fases, estados, nombres de hojas, scopes de Google.

## Entorno de desarrollo

### Requisitos
- Python 3.12 (instalado vía `winget install Python.Python.3.12 --source winget`)
- Entorno virtual en `.venv/` (Python 3.12, no subir a git)

### Configuración inicial (primera vez)
```bash
py -3.12 -m venv .venv
.venv/Scripts/pip install -e .
```

### Activar el entorno (cada sesión)
```bash
# PowerShell / CMD
.venv\Scripts\activate

# bash / Git Bash
source .venv/Scripts/activate
```

### Ejecutar el script diario
```bash
# Con variables de entorno definidas:
.venv/Scripts/python scripts/diario.py
```

### Verificar instalación
```bash
.venv/Scripts/python -c "from aid import JiraAID; print('OK')"
```

## Convenciones

- Columnas del DataFrame en MAYÚSCULAS (`CLAVE`, `TITULO`, `ESTADO`, etc.)
- Commits en español con prefijo convencional (`feat:`, `fix:`, `perf:`, etc.)
- PRs con merge directo a `main`
- Python >= 3.12
