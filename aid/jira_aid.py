from datetime import datetime
import os
import pandas as pd
from jira import JIRA

class JiraClient:
    """Clase ejemplo que genera un DataFrame con datos"""
    
    def __init__(self, parametro1=None):
        self.parametro1 = parametro1
        
    def generar_reporte(self):
        """
        Método que devuelve un DataFrame con datos
        Este es tu método que quieres ejecutar diariamente
        """
        # Ejemplo: generar datos ficticios
        datos = {
            'fecha': [datetime.now().strftime('%Y-%m-%d')],
            'metrica_1': [42],
            'metrica_2': [85],
            'observaciones': ['Datos del día']
        }
        
        df = pd.DataFrame(datos)
        return df
    
    def procesar_datos(self, df):
        """Método adicional para procesamiento"""
        # Aquí tu lógica personalizada
        return df
    
class JiraAID:

    def __init__(self):
        jira_url = os.environ.get('JIRA_URL')
        jira_user = os.environ.get('JIRA_USER')
        jira_pass = os.environ.get('JIRA_PASS')

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

        #if issue.key == 'IGUINE-11':
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


    def get_issues_projects(self, jql: str):
        self.issues = self.get_issues(jql)
        df = self.issues_to_df(self.issues)
        self.df_issues = self.clean_issues(df)
        self.extract_relations()

        return self.df_issues[['SOLUCION',
                            'CLAVE',
                            'TITULO',
                            'DESCRIPCION',
                            'INICIO', 'FIN',
                            'ACTUALIZACION',
                            'CENTRO',
                            'ESTADO',
                            'CLAVE_MCMI',
                            'TIPO',
                            'SUBTIPO',
                            'HBS_ESTIMADAS',
                            'HBS_RESTANTES',
                            'ESTADO_AGRUPADO',
                            'RESPONSABLE_SERVICIO',
                            'TIPO_SERVICIO']].copy()


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
                           'customfield_16000' # Tipo de servicio
                           ]

        issues = []
        start_at = 0
        max_results = 50

        #pbar = tqdm(desc="Downloading issues...")

        while True:
            batch = self.jira.search_issues(jql, expand='names', fields=campos_deseados, startAt=start_at, maxResults=max_results)
            issues.extend(batch)

            if len(batch) < max_results:
                break

            start_at += len(batch)
            #pbar.update(len(batch))

        #pbar.close()

        print(f'{len(issues)} issues loaded')
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
                    'Tipo de servicio': 'TIPO_SERVICIO'}, inplace=True)

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

        df['HBS_ESTIMADAS'] = df['HBS_ESTIMADAS'].astype(float) / 3600
        df['HBS_RESTANTES'] = df['HBS_RESTANTES'].astype(float) / 3600

        df['ESTADO_AGRUPADO'] = (
            df['ESTADO']
            .map({'Abierta': 'BACKLOG', 'Cerrada': 'CERRADA', 'Pdte Información': 'BLOQUEADA'})
            .fillna("EN_CURSO")
        )
        return df


    def get_blocks_projects(self):
        cols_bloqueo = ['CLAVE_BLOQUEO','TITULO_BLOQUEO','INICIO_BLOQUEO', 'DESCRIPCION_BLOQUEO', 'ACTUALIZACION_BLOQUEO']
        df_relaciones = pd.DataFrame(self.relations)
        df_relaciones_bloqueos = df_relaciones[df_relaciones['RELACION']=='Es bloqueada por']
        #print(df_relaciones_bloqueos)
        bloqueos = df_relaciones_bloqueos['CLAVE_DESTINO'].unique().tolist() #issues bloqueantes

        claves_issues = self.df_issues['CLAVE'].unique().tolist()
        bloqueos_externos = [x for x in bloqueos if x not in claves_issues]

        bloqueos_internos = list(set(bloqueos) - set(bloqueos_externos))

        print('Bloqueos fuera de proyectos AID', bloqueos_externos)
        print('Bloqueos en proyectos AID', bloqueos_internos)

        df_bloqueos_internos = self.df_issues[self.df_issues['CLAVE'].isin(bloqueos_internos)].copy()
        df_bloqueos_internos.rename(columns={'CLAVE': 'CLAVE_BLOQUEO', 'TITULO': 'TITULO_BLOQUEO', 'INICIO': 'INICIO_BLOQUEO', 'ACTUALIZACION': 'ACTUALIZACION_BLOQUEO', 'DESCRIPCION': 'DESCRIPCION_BLOQUEO'}, inplace=True)
        df_bloqueos_internos = df_bloqueos_internos[cols_bloqueo]

        if len(bloqueos_externos) > 0:
            jql = f'key in ({",".join(bloqueos_externos)})'
            issues_bloqueos_externos = self.get_issues(jql)
            df_bloqueos_externos = self.issues_to_df(issues_bloqueos_externos)
            df_bloqueos_externos.rename(columns={'CLAVE': 'CLAVE_BLOQUEO', 'TITULO': 'TITULO_BLOQUEO', 'Fecha de Creación': 'INICIO_BLOQUEO', 'ACTUALIZACION': 'ACTUALIZACION_BLOQUEO', 'DESCRIPCION': 'DESCRIPCION_BLOQUEO'}, inplace=True)
            df_bloqueos_externos = df_bloqueos_externos[cols_bloqueo]
        else:
            df_bloqueos_externos = pd.DataFrame(columns=cols_bloqueo)

        df_bloqueos = pd.concat([df_bloqueos_internos[cols_bloqueo], df_bloqueos_externos[cols_bloqueo]])

        df_bloqueos = df_bloqueos.merge(df_relaciones_bloqueos, left_on='CLAVE_BLOQUEO', right_on = 'CLAVE_DESTINO', how='left') # completa datos issue origen

        df_bloqueos = df_bloqueos.merge(self.df_issues[['SOLUCION', 'CLAVE', 'CENTRO', 'HBS_RESTANTES']], left_on='CLAVE_ORIGEN', right_on='CLAVE', how='left')


        return df_bloqueos[['SOLUCION', 'CLAVE', 'CLAVE_BLOQUEO', 'TITULO_BLOQUEO', 'DESCRIPCION_BLOQUEO', 'INICIO_BLOQUEO', 'CENTRO', 'HBS_RESTANTES']]

        return df

    def extract_relations(self):
        relations = []
        for issue in self.issues:
            for link in issue.fields.issuelinks:
                #sólo tenecesito la relación desde mis issues a cualquier otra (inward)
                if hasattr(link, "inwardIssue"):
                    relations.append({'CLAVE_ORIGEN': issue.key,  'RELACION':link.type.inward, 'CLAVE_DESTINO': link.inwardIssue.key})

        self.relations = relations
        print(f'{len(self.relations)} relations loaded')

    data = []
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