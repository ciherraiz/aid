from datetime import datetime
import logging
import os
import time
import pandas as pd
from jira import JIRA
from jira.exceptions import JIRAError
from aid.constants import (
    PROJECT_CATEGORY, JIRA_FIELDS, COLUMN_RENAME, PHASES,
    STATUS_MAP, STATUS_DEFAULT, ISSUE_TYPE_TASK, ISSUE_TYPE_MILESTONE,
    RELATION_BLOCKED_BY,
)

logger = logging.getLogger(__name__)
    
class JiraAID:

    def __init__(self, jira_url, jira_user, jira_pass):
        
        if not jira_url or not jira_user:
            raise ValueError("Error en configuración de autenticación")

        try:
            self.jira = JIRA(
                server=jira_url,
                basic_auth=(jira_user, jira_pass)
            )
        except JIRAError as e:
            status = e.status_code if hasattr(e, "status_code") else "?"
            if status == 401:
                raise ConnectionError(f"Credenciales de Jira inválidas (HTTP 401): {jira_url}") from e
            if status == 403:
                raise ConnectionError(f"Sin permisos para acceder a Jira (HTTP 403): {jira_url}") from e
            raise ConnectionError(f"Error al conectar con Jira (HTTP {status}): {e.text}") from e
        except Exception as e:
            raise ConnectionError(f"No se pudo conectar con Jira en '{jira_url}': {e}") from e
        logger.info("Conectado a Jira: %s", jira_url)

    def get_projects_by_category(self, category_name):
        all_projects = self.jira.projects()
        return [
        {   "id": p.id,
            "key": p.key,
            "name": p.name
        }
        for p in all_projects if getattr(p, "projectCategory", None) and
                p.projectCategory.name == category_name]


    def normalize_jira_value(self, val):

        if val is None:
            return None

        if hasattr(val, "name"):
            return val.name

        if isinstance(val, list):
            return ", ".join(self.normalize_jira_value(v) for v in val)

        if isinstance(val, dict):
            if "name" in val:
                return val["name"]
            if "value" in val:
                return val["value"]
            if "id" in val:
                return val["id"]
            return str(val)

        # Resto de tipos
        return val

    def issue_to_dict(self, issue, field_names):
        d = {}
        d["Key"] = issue.key
        d["Summary"] = issue.fields.summary
        d["Status"] = issue.fields.status.name
        d["Issue Type"] = issue.fields.issuetype.name


        #    print(issue.raw["fields"].items())

        for fid, val in issue.raw["fields"].items():
            if fid in field_names:
                name = field_names[fid]
                d[name] = self.normalize_jira_value(val)
                """
                if hasattr(val, "name"):
                    d[name] = val.name
                elif isinstance(val, list):
                    d[name] = ", ".join(getattr(v, "name", str(v)) for v in val)
                else:
                    d[name] = val
                """
        return d


    def get_issues_projects(self):

        projects = self.get_projects_by_category(PROJECT_CATEGORY)
        logger.info("Proyectos encontrados en '%s': %d", PROJECT_CATEGORY, len(projects))
        jql =f"project in ({','.join([d['key'] for d in projects])}) ORDER BY Clasificación ASC"

        self.issues = self.get_issues(jql)
        df = self.issues_to_df(self.issues)
        self.df_issues = self.clean_issues(df)
        self.extract_relations()

        self.df_milestones = self.get_milestone_data()


        return self.df_issues[['SOLUCION',
                            'CENTRO',
                            'CLAVE',
                            'FASE',
                            'TITULO',
                            'DESCRIPCION',
                            'INICIO', 'FIN',
                            'ACTUALIZACION',
                            'ESTADO',
                            'CLAVE_MCMI',
                            'TIPO',
                            'SUBTIPO',
                            'HBS_ESTIMADAS',
                            'HBS_RESTANTES',
                            'ESTADO_AGRUPADO',
                            'RESPONSABLE_SERVICIO',
                            'TIPO_SERVICIO',
                            'DIAS',
                            'PRIORIDAD',
                            'AGRUPADOR']].copy()


    def get_issues(self, jql: str):

        
        campos_deseados = JIRA_FIELDS

        issues = []
        start_at = 0
        max_results = 100


        MAX_INTENTOS = 4
        while True:
            for intento in range(1, MAX_INTENTOS + 1):
                try:
                    batch = self.jira.search_issues(
                        jql, expand='names', fields=campos_deseados,
                        startAt=start_at, maxResults=max_results
                    )
                    break  # éxito: salir del bucle de reintentos
                except JIRAError as e:
                    status = getattr(e, "status_code", None)
                    if status in (400, 401, 403):
                        raise  # error permanente: no reintentar
                    if intento == MAX_INTENTOS:
                        raise RuntimeError(
                            f"get_issues falló tras {MAX_INTENTOS} intentos "
                            f"(startAt={start_at}): {e}"
                        ) from e
                    logger.warning("Reintento %d/%d (startAt=%d, HTTP %s): %s", intento, MAX_INTENTOS, start_at, status, e)
                except Exception as e:
                    if intento == MAX_INTENTOS:
                        raise RuntimeError(
                            f"get_issues falló tras {MAX_INTENTOS} intentos "
                            f"(startAt={start_at}): {e}"
                        ) from e
                    logger.warning("Reintento %d/%d (startAt=%d): %s", intento, MAX_INTENTOS, start_at, e)
                time.sleep(2 ** intento)  # backoff: 2s, 4s, 8s, 16s

            issues.extend(batch)
            if len(batch) < max_results:
                break
            start_at += len(batch)


        logger.info("get_issues: %d issues obtenidas", len(issues))
        return issues

    def issues_to_df(self, issues):
        #issues = self.jira.search_issues(jql, expand='names', fields=campos_deseados)
        field_names = {field["id"]: field["name"] for field in self.jira.fields()}

        #print(field_names)

        df = pd.DataFrame(self.issue_to_dict(issue, field_names) for issue in issues)

        df = df.replace("", pd.NA)
        df = df.map(lambda x: pd.NA if x == [] else x)
        df = df.where(pd.notnull(df), pd.NA)
        df = df.dropna(axis=1, how='all')

        df.rename(columns=COLUMN_RENAME, inplace=True)

        return df

    def clean_issues(self, df):
        df['CLAVE_MCMI'] = df['DESCRIPCION'].str.extract(r'^([A-Za-z0-9]+-[A-Za-z0-9]+-[A-Za-z0-9]+-\d+(?:\.\d+)?)#')[0].str.upper()
        df['SOLUCION'] = df['CLAVE'].str.split('-').str[0]
        df['FASE'] = df['DESCRIPCION'].str.split('-').str[1]
        df['ICLAVE'] = df['CENTRO'] + '_' + df['CLAVE_MCMI']

        df[['INICIO', 'FIN']] = (
        df[['INICIO', 'FIN']]
        .apply(pd.to_datetime, errors="coerce", utc=True)
        .apply(lambda x: x.dt.tz_localize(None))
        )

        df['DIAS'] = (df['FIN'] - df['INICIO']).dt.days

        df['HBS_ESTIMADAS'] = df['HBS_ESTIMADAS'].astype(float) / 3600
        df['HBS_RESTANTES'] = df['HBS_RESTANTES'].astype(float) / 3600

        df['ESTADO_AGRUPADO'] = (
            df['ESTADO']
            .map(STATUS_MAP)
            .fillna(STATUS_DEFAULT)
        )
        return df

    def get_blocks_projects(self):
        cols_bloqueo = ['CLAVE_BLOQUEO','TITULO_BLOQUEO','INICIO_BLOQUEO', 'DESCRIPCION_BLOQUEO', 'ACTUALIZACION_BLOQUEO', 'RESPONSABLE_BLOQUEO', 'SERVICIO_BLOQUEO']
        df_relaciones_bloqueos = self.df_relations[self.df_relations['RELACION']==RELATION_BLOCKED_BY]

        bloqueos = df_relaciones_bloqueos['CLAVE_DESTINO'].unique().tolist() #issues bloqueantes

        if bloqueos:
            logger.info("Issues bloqueantes encontradas: %d", len(bloqueos))
            jql = f'key in ({",".join(bloqueos)})'
            issues_bloqueos = self.get_issues(jql)

            df_bloqueos = self.issues_to_df(issues_bloqueos)
            df_bloqueos.rename(columns={'CLAVE': 'CLAVE_BLOQUEO', 'TITULO': 'TITULO_BLOQUEO', 'Fecha de Creación': 'INICIO_BLOQUEO', 'ACTUALIZACION': 'ACTUALIZACION_BLOQUEO', 'DESCRIPCION': 'DESCRIPCION_BLOQUEO', 'RESPONSABLE_SERVICIO': 'RESPONSABLE_BLOQUEO', 'TIPO_SERVICIO': 'SERVICIO_BLOQUEO'}, inplace=True)
            df_bloqueos = df_bloqueos[cols_bloqueo]
        else:
            df_bloqueos = pd.DataFrame(columns=cols_bloqueo)

        df_bloqueos = df_bloqueos.merge(df_relaciones_bloqueos, left_on='CLAVE_BLOQUEO', right_on = 'CLAVE_DESTINO', how='left') # completa datos issue origen

        df_total_bloqueadas = self.df_issues[self.df_issues['ESTADO_AGRUPADO']=='BLOQUEADA'][['SOLUCION', 'CLAVE', 'CENTRO', 'HBS_RESTANTES', 'ESTADO', 'PRIORIDAD']]
        
        df_bloqueos = df_total_bloqueadas.merge(df_bloqueos, left_on='CLAVE', right_on='CLAVE_ORIGEN', how='left')
        df_bloqueos['INICIO_BLOQUEO'] = pd.to_datetime(df_bloqueos["INICIO_BLOQUEO"], errors="coerce").dt.normalize()
        df_bloqueos['DIAS'] = (pd.to_datetime('today', utc=True).normalize() - df_bloqueos['INICIO_BLOQUEO']).dt.days


        return df_bloqueos[['SOLUCION', 'CLAVE', 'ESTADO', 'PRIORIDAD', 'CLAVE_BLOQUEO', 'TITULO_BLOQUEO', 'DESCRIPCION_BLOQUEO', 'INICIO_BLOQUEO', 'CENTRO', 'HBS_RESTANTES', 'RESPONSABLE_BLOQUEO', 'SERVICIO_BLOQUEO', 'DIAS']]


    def calculate_hbs (self): 

        df_hbs_prorr = self.df_issues[
                        (self.df_issues['TIPO'] == ISSUE_TYPE_TASK) &
                        (self.df_issues['SUBTIPO'] != ISSUE_TYPE_MILESTONE) &
                        self.df_issues['INICIO'].notna() &
                        self.df_issues['FIN'].notna() &
                        self.df_issues['HBS_ESTIMADAS'].notna()
                    ].copy()[['SOLUCION', 'CLAVE', 'INICIO', 'FIN', 'ESTADO_AGRUPADO', 'HBS_ESTIMADAS', 'HBS_RESTANTES']]

        hoy = pd.Timestamp.now().normalize()

        # Normalizar fechas y aplicar clip: el prorrateo empieza desde hoy como mínimo
        df_hbs_prorr["INICIO_PRORR"] = df_hbs_prorr["INICIO"].dt.normalize().clip(lower=hoy)
        df_hbs_prorr["FIN_PRORR"]    = df_hbs_prorr["FIN"].dt.normalize()

        # Descartar incidencias que ya terminaron (FIN < hoy → no hay nada que prorratear)
        df_hbs_prorr = df_hbs_prorr[df_hbs_prorr["FIN_PRORR"] >= hoy]

        # Duración total del período de prorrateo
        df_hbs_prorr["DIAS_TOTALES"] = (df_hbs_prorr["FIN_PRORR"] - df_hbs_prorr["INICIO_PRORR"]).dt.days + 1
        df_hbs_prorr = df_hbs_prorr[df_hbs_prorr["DIAS_TOTALES"] > 0]  # descarta datos con INICIO > FIN

        # Expandir por mes
        df_hbs_prorr["MES"] = df_hbs_prorr.apply(
            lambda x: pd.period_range(x["INICIO_PRORR"], x["FIN_PRORR"], freq="M"),
            axis=1
        )
        df_exp = df_hbs_prorr.explode("MES")

        # Inicio y fin del mes como timestamps
        df_exp["MES_INICIO_TS"] = df_exp["MES"].dt.to_timestamp().dt.normalize()
        df_exp["MES_FIN_TS"]    = df_exp["MES"].dt.to_timestamp(how="end").dt.normalize()

        # Recorte real dentro del mes
        df_exp["INICIO_MES_REAL"] = df_exp[["INICIO_PRORR", "MES_INICIO_TS"]].max(axis=1)
        df_exp["FIN_MES_REAL"]    = df_exp[["FIN_PRORR",    "MES_FIN_TS"  ]].min(axis=1)

        # Días efectivos — con el filtro previo esto nunca debería ser ≤ 0,
        # pero lo dejamos como salvaguarda
        df_exp["DIAS_EN_MES"] = (df_exp["FIN_MES_REAL"] - df_exp["INICIO_MES_REAL"]).dt.days + 1
        df_exp = df_exp[df_exp["DIAS_EN_MES"] > 0]  # salvaguarda explícita

        # Prorrateo proporcional
        df_exp["HBS_ESTIMADAS_PRORR"] = df_exp["HBS_ESTIMADAS"] * df_exp["DIAS_EN_MES"] / df_exp["DIAS_TOTALES"]
        df_exp["HBS_RESTANTES_PRORR"] = df_exp["HBS_RESTANTES"] * df_exp["DIAS_EN_MES"] / df_exp["DIAS_TOTALES"]

        #return df_exp[['SOLUCION', 'CLAVE', 'MES', 'INICIO', 'FIN', 'DIAS_EN_MES', 'DIAS_TOTALES', 'HBS_ESTIMADAS_PRORR', 'HBS_RESTANTES_PRORR']]
    
        # Agrupar
        df_hbs_mes_prorr = (
            df_exp
            .groupby(["SOLUCION", "MES", "ESTADO_AGRUPADO"], as_index=False)
            [["HBS_ESTIMADAS_PRORR", "HBS_RESTANTES_PRORR"]]
            .sum()
        )

        df_hbs_mes_prorr_pivot = (
                df_hbs_mes_prorr
                .pivot_table(
                    index=['SOLUCION', 'MES'],
                    columns="ESTADO_AGRUPADO",
                    values="HBS_RESTANTES_PRORR",
                    aggfunc="sum",
                    fill_value=0
                )
                .rename_axis(None, axis=1)
                .reset_index()
        )

        df_hbs_mes_prorr_est_pivot = (
                df_hbs_mes_prorr
                .pivot_table(
                    index=['SOLUCION', 'MES'],
                    columns="ESTADO_AGRUPADO",
                    values="HBS_ESTIMADAS_PRORR",
                    aggfunc="sum",
                    fill_value=0
                )
                .rename_axis(None, axis=1)
                .reset_index()
        )

        cols_pivot = df_hbs_mes_prorr_pivot.columns.difference(['SOLUCION', 'MES'])

        df_hbs_mes_prorr_pivot['TOTAL_HBS_RESTANTES'] = df_hbs_mes_prorr_pivot[cols_pivot].sum(axis=1)
        df_hbs_mes_prorr_pivot = df_hbs_mes_prorr_pivot.merge(df_hbs_mes_prorr_est_pivot, on=['SOLUCION', 'MES'], suffixes=('', '_EST'))

        #df_hbs_mes_prorr_pivot = df_hbs_mes_prorr_pivot.merge(df_soluciones[['SOLUCION', 'CODIGO_CANAL']], on='SOLUCION', how='left')
        #df_hbs_mes_prorr_pivot = df_hbs_mes_prorr_pivot.merge(df_cap_total.reset_index()[['CODIGO_CANAL', 'MES', 'HBS_CAPACIDAD']], on=['CODIGO_CANAL', 'MES'], how="left")

        #df_hbs_mes_prorr_pivot['HBS_RESTANTES_PCT']=df_hbs_mes_prorr_pivot['TOTAL_HBS_RESTANTES']/df_hbs_mes_prorr_pivot['HBS_CAPACIDAD'] * 100

        #return df_hbs_mes_prorr_pivot[['SOLUCION', 'MES', 'TOTAL_HBS_RESTANTES', 'HBS_ESTIMADAS_PRORR_EST']]
        return df_hbs_mes_prorr_pivot

    def extract_relations(self):
        relations = []
        for issue in self.issues:
            for link in issue.fields.issuelinks:
                #sólo tenecesito la relación desde mis issues a cualquier otra (inward)
                if hasattr(link, "inwardIssue"):
                    relations.append({'CLAVE_ORIGEN': issue.key,  'RELACION':link.type.inward, 'CLAVE_DESTINO': link.inwardIssue.key})

        self.df_relations = pd.DataFrame(relations)

    data = []

    def pivot_by_phase(self, df, columna_agregacion):
        """
        Pivota un dataframe agrupando por SOLUCION y CENTRO, creando columnas para cada FASE.
        
        Parámetros:
        -----------
        df : pd.DataFrame
            DataFrame con las columnas SOLUCION, CENTRO, FASE y la columna a agregar
        columna_agregacion : str
            Nombre de la columna cuyos valores se sumarán (por defecto 'HBS_ESTIMADAS')
        
        Retorna:
        --------
        pd.DataFrame
            DataFrame pivotado con SOLUCION, CENTRO y una columna por cada fase
        """
        # Lista de fases en el orden deseado
        fases_ordenadas = PHASES
        
        # Crear una copia del dataframe y asegurar que la columna de agregación sea numérica
        df_limpio = df.copy()
        df_limpio[columna_agregacion] = pd.to_numeric(df_limpio[columna_agregacion], errors='coerce').fillna(0)
        
        # Crear la tabla pivotada
        df_pivotado = df_limpio.pivot_table(
            index=['SOLUCION', 'CENTRO'],
            columns='FASE',
            values=columna_agregacion,
            aggfunc='sum',
            fill_value=0
        )
        
        # Reindexar las columnas para asegurar el orden y que existan todas las fases
        df_pivotado = df_pivotado.reindex(columns=fases_ordenadas, fill_value=0)
        
        # Resetear el índice para que SOLUCION y CENTRO sean columnas
        df_pivotado = df_pivotado.reset_index()
        
        # Aplanar el nombre de las columnas (eliminar el nivel jerárquico)
        df_pivotado.columns.name = None
        
        # Convertir todas las columnas de fases a tipo numérico y rellenar NaN con 0
        for fase in fases_ordenadas:
            df_pivotado[fase] = pd.to_numeric(df_pivotado[fase], errors='coerce').fillna(0).astype(int)
        
        return df_pivotado
    
    def get_milestone_data(self):
        cols = ['SOLUCION', 'CENTRO', 'CLAVE', 'FASE', 'HBS_ESTIMADAS', 'DIAS']
        df_disponibles = self.df_issues[((self.df_issues['ESTADO_AGRUPADO']=='BACKLOG') | (self.df_issues['ESTADO_AGRUPADO']==STATUS_DEFAULT)) & (self.df_issues['TIPO']==ISSUE_TYPE_TASK)][cols]
        df_bloqueadas = self.df_issues[(self.df_issues['ESTADO_AGRUPADO']=='BLOQUEADA') & (self.df_issues['TIPO']==ISSUE_TYPE_TASK)][cols]
        df_cerradas = self.df_issues[(self.df_issues['ESTADO_AGRUPADO']=='CERRADA') & (self.df_issues['TIPO']==ISSUE_TYPE_TASK)][cols]

        df_fases_disp = self.pivot_by_phase(df_disponibles, 'HBS_ESTIMADAS')
        df_fases_block = self.pivot_by_phase(df_bloqueadas, 'HBS_ESTIMADAS')
        df_fases_cerr = self.pivot_by_phase(df_cerradas, 'HBS_ESTIMADAS')
        df_fases_cerr = df_fases_cerr.rename(
                                            columns={
                                                col: f"{col}_CERR" 
                                                for col in df_fases_cerr.columns 
                                                if col not in ['SOLUCION', 'CENTRO']
                                            }
                                        )

        df_fases_total = pd.merge(df_fases_disp, df_fases_block, on=['SOLUCION', 'CENTRO'], how='left', suffixes=('_DISP', '_BLK'))
        df_fases_total = pd.merge(df_fases_total, df_fases_cerr, on=['SOLUCION', 'CENTRO'], how='left', suffixes=('', '_CERR'))

        df_fases_total.fillna(0, inplace=True)

        return df_fases_total


    def get_comments(self, issue_keys: list) -> pd.DataFrame:
        empty = pd.DataFrame(columns=['CLAVE', 'FECHA_COMENTARIO', 'AUTOR_COMENTARIO', 'COMENTARIO'])
        if not issue_keys:
            return empty

        rows = []
        for key in issue_keys:
            try:
                for c in self.jira.comments(key):
                    rows.append({
                        'CLAVE': key,
                        'FECHA_COMENTARIO': pd.to_datetime(c.created, utc=True).tz_localize(None),
                        'AUTOR_COMENTARIO': c.author.displayName,
                        'COMENTARIO': c.body,
                    })
            except Exception as e:
                logger.warning("get_comments: error en issue %s: %s", key, e)

        if not rows:
            return empty

        return pd.DataFrame(rows)