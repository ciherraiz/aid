from datetime import datetime
import os
import pandas as pd
from jira import JIRA

PROJECT_CATEGORY = 'PROYECTOS AREA IMPLANTACIONES'
    
class JiraAID:

    def __init__(self, jira_url, jira_user, jira_pass):
        
        if not jira_url or not jira_user:
            raise ValueError("Error en configuración de autenticación")

        self.jira = JIRA(
            server=jira_url,
            basic_auth=(jira_user, jira_pass)
        )

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
                            'PRIORIDAD']].copy()


    def get_issues(self, jql: str):

        
        campos_deseados = ['key',
                           'summary',
                           'status',
                           'issuetype',
                           'description',
                           'created',
                           'resolved',
                           'updated',
                           'timeoriginalestimate', # Estimadas
                           'timeestimate', # Restantes
                           'customfield_16301', # Centros de implantación
                           'customfield_10601', # Fecha de inicio deseada
                           'customfield_10602', # Fecha de fin deseada
                           'customfield_12001', # Tipo de tarea
                           'customfield_12302', # Fecha inicio
                           'customfield_12303', # Fecha Fin
                           'issuelinks',  # Enlaces a otras issues
                           'customfield_16100',  # (R) Responsable
                           'customfield_16000', # Tipo de servicio
                           'priority'
                           ]

        issues = []
        start_at = 0
        max_results = 50


        while True:
            batch = self.jira.search_issues(jql, expand='names', fields=campos_deseados, startAt=start_at, maxResults=max_results)
            issues.extend(batch)

            if len(batch) < max_results:
                break

            start_at += len(batch)


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

        df.rename(columns={'Centros de implantación': 'CENTRO',
                    'Key': 'CLAVE',
                    'Summary': 'TITULO',
                    'Descripción':'DESCRIPCION',
                    'Fecha Inicio': 'INICIO',
                    'Fecha Fin': 'FIN',
                    'Fecha de Actualización': 'ACTUALIZACION',
                    'Issue Type': 'TIPO',
                    'Tipo de Tarea': 'SUBTIPO',
                    'Status': 'ESTADO',
                    'Estimadas': 'HBS_ESTIMADAS',
                    'Restantes': 'HBS_RESTANTES',
                    '(R) Responsable': 'RESPONSABLE_SERVICIO',
                    'Tipo de servicio': 'TIPO_SERVICIO',
                    'Prioridad': 'PRIORIDAD'}, inplace=True)

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
            .map({'Abierta': 'BACKLOG', 'Cerrada': 'CERRADA', 'Pdte. Información': 'BLOQUEADA'})
            .fillna("EN_CURSO")
        )
        return df

    def get_blocks_projects(self):
        cols_bloqueo = ['CLAVE_BLOQUEO','TITULO_BLOQUEO','INICIO_BLOQUEO', 'DESCRIPCION_BLOQUEO', 'ACTUALIZACION_BLOQUEO', 'RESPONSABLE_BLOQUEO', 'SERVICIO_BLOQUEO']
        df_relaciones_bloqueos = self.df_relations[self.df_relations['RELACION']=='Es bloqueada por']

        bloqueos = df_relaciones_bloqueos['CLAVE_DESTINO'].unique().tolist() #issues bloqueantes

        if bloqueos:
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


        return df_bloqueos[['SOLUCION', 'CLAVE', 'ESTADO', 'PRIORIDAD', 'CLAVE_BLOQUEO', 'TITULO_BLOQUEO', 'DESCRIPCION_BLOQUEO', 'INICIO_BLOQUEO', 'CENTRO', 'HBS_RESTANTES', 'RESPONSABLE_BLOQUEO', 'SERVICIO_BLOQUEO']]


    def calculate_hbs (self): 

        df_hbs_prorr = self.df_issues[(self.df_issues['TIPO'] == 'Tarea general') & (self.df_issues['SUBTIPO'] != 'Hito') & ((self.df_issues['INICIO'].notna()) & (self.df_issues['FIN'].notna())) & (self.df_issues['HBS_ESTIMADAS'].notna())].copy()

        df_hbs_prorr = df_hbs_prorr[['SOLUCION', 'CLAVE', 'INICIO', 'FIN', 'ESTADO_AGRUPADO', 'HBS_ESTIMADAS', 'HBS_RESTANTES']]

        df_hbs_prorr["INICIO_NORM"] = df_hbs_prorr["INICIO"].dt.normalize()
        df_hbs_prorr["FIN_NORM"] = df_hbs_prorr["FIN"].dt.normalize()

        # Ajustar inicio al máximo entre fecha original y HOY
        hoy = pd.Timestamp.now().normalize()
        df_hbs_prorr["INICIO_PRORRATEO"] = df_hbs_prorr["INICIO_NORM"].clip(lower=hoy)
        df_hbs_prorr["FIN_PRORRATEO"] = df_hbs_prorr["FIN_NORM"]

        # Calcular duración total en días (incluyendo ambos extremos)
        df_hbs_prorr["DIAS_TOTALES"] = (df_hbs_prorr["FIN_PRORRATEO"] - df_hbs_prorr["INICIO_PRORRATEO"]).dt.days + 1

        df_hbs_prorr["MES_INICIO"] = df_hbs_prorr["INICIO_PRORRATEO"].dt.to_period("M")
        df_hbs_prorr["MES_FIN"] = df_hbs_prorr["FIN_PRORRATEO"].dt.to_period("M")

        # Generar rango mensual por cada incidencia
        df_hbs_prorr["MES"] = df_hbs_prorr.apply(
            lambda x: pd.period_range(x["MES_INICIO"], x["MES_FIN"], freq="M"),
            axis=1
        )

        # Expandir dataframe (explode) para tener una fila por incidencia y mes
        df_exp = df_hbs_prorr.explode("MES")

        # Calcular inicio y fin real dentro de cada mes
        df_exp["MES_INICIO_TS"] = df_exp["MES"].dt.to_timestamp().dt.normalize()
        df_exp["MES_FIN_TS"] = (
            df_exp["MES"].dt.to_timestamp(how="end").dt.normalize()
        )

        # Convertir periodo a timestamp (inicio y fin de mes)
        df_exp["INICIO_MES_REAL"] = df_exp[["INICIO_PRORRATEO", "MES_INICIO_TS"]].max(axis=1)
        df_exp["FIN_MES_REAL"] = df_exp[["FIN_PRORRATEO", "MES_FIN_TS"]].min(axis=1)

        # Días efectivos en el mes
        df_exp["DIAS_EN_MES"] = (
            (df_exp["FIN_MES_REAL"] - df_exp["INICIO_MES_REAL"]).dt.days + 1
        )

        # Prorratear horas
        df_exp["HBS_ESTIMADAS_PRORR"] = (
            df_exp["HBS_ESTIMADAS"] *
            df_exp["DIAS_EN_MES"] /
            df_exp["DIAS_TOTALES"]
        )

        df_exp["HBS_RESTANTES_PRORR"] = (
            df_exp["HBS_RESTANTES"] *
            df_exp["DIAS_EN_MES"] /
            df_exp["DIAS_TOTALES"]
        )

        return df_exp




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
        fases_ordenadas = ['APS', 'RP', 'PRE', 'IMP', 'ARR', 'CON', 'EXT', 'PN3']
        
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
        df_disponibles = self.df_issues[(self.df_issues['ESTADO_AGRUPADO']=='BACKLOG') | (self.df_issues['ESTADO_AGRUPADO']=='EN_CURSO')][cols]
        df_bloqueadas = self.df_issues[self.df_issues['ESTADO_AGRUPADO']=='BLOQUEADA'][cols]
        df_hitos_disp = self.pivot_by_phase(df_disponibles, 'HBS_ESTIMADAS')
        df_hitos_block = self.pivot_by_phase(df_bloqueadas, 'HBS_ESTIMADAS')

        df_hitos_total = pd.merge(df_hitos_disp, df_hitos_block, on=['SOLUCION', 'CENTRO'], how='left', suffixes=('_DISP', '_BLK'))

        df_hitos_total.fillna(0, inplace=True)

        return df_hitos_total


    """
    def get_comments(self, issues):
            for issue in issues:
                comments = self.jira.comments(issue.key)

                for c in comments:
                    data.append({
                        "issue": issue.key,
                        "status": issue.fields.status.name,
                        "comment": c.body,
                        "author": c.author.displayName,
                        "created": c.created
                    })

            import pandas as pd
            df = pd.DataFrame(data)

    """