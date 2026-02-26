import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import math
import pandas as pd
import numpy as np
from aid import JiraAID

def conectar_google_sheets():
    """Establece conexión con Google Sheets usando credenciales"""
    # Las credenciales estarán en una variable de entorno
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    creds_dict = json.loads(creds_json)
    
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict, scope
    )
    
    client = gspread.authorize(credentials)
    return client

def convertir_para_sheets(df):
    """
    Convierte un DataFrame a formatos 100% compatibles con Google Sheets
    Elimina NaN, inf, -inf, NaT y otros valores problemáticos
    """
    df_copy = df.copy()
    
    for col in df_copy.columns:
        dtype = df_copy[col].dtype
        
        # 1. Convertir datetime/Timestamp a string
        if pd.api.types.is_datetime64_any_dtype(dtype):
            df_copy[col] = df_copy[col].apply(
                lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else ''
            )
        
        # 2. Convertir timedelta
        elif pd.api.types.is_timedelta64_dtype(dtype):
            df_copy[col] = df_copy[col].apply(
                lambda x: str(x) if pd.notna(x) else ''
            )
        
        # 3. Convertir booleanos
        elif pd.api.types.is_bool_dtype(dtype):
            df_copy[col] = df_copy[col].apply(
                lambda x: 'TRUE' if x is True else ('FALSE' if x is False else '')
            )
        
        # 4. Convertir numéricos (aquí está el problema principal)
        elif pd.api.types.is_numeric_dtype(dtype):
            def limpiar_numero(x):
                # Verificar si es NaN, None, inf o -inf
                if pd.isna(x) or x is None:
                    return ''
                if isinstance(x, float) and (math.isinf(x) or math.isnan(x)):
                    return ''
                return x
            
            df_copy[col] = df_copy[col].apply(limpiar_numero)
        
        # 5. Convertir objetos/strings
        else:
            df_copy[col] = df_copy[col].apply(
                lambda x: str(x) if pd.notna(x) and x is not None and x != '' else ''
            )
    
    # Reemplazo final de cualquier NaN que haya quedado
    df_copy = df_copy.replace([np.nan, np.inf, -np.inf], '')
    
    # Convertir None a string vacío
    df_copy = df_copy.fillna('')
    
    return df_copy

def actualizar_hoja(df, spreadsheet_id, hoja_nombre):
    """
    Actualiza una hoja de Google Sheets con el DataFrame
    
    Args:
        df: DataFrame de pandas
        spreadsheet_id: ID de tu Google Sheet (está en la URL)
        hoja_nombre: Nombre de la pestaña
    """
    client = conectar_google_sheets()
    
    # Abrir la hoja de cálculo
    sheet = client.open_by_key(spreadsheet_id)
    
    # Seleccionar o crear la pestaña
    try:
        worksheet = sheet.worksheet(hoja_nombre)
    except:
        worksheet = sheet.add_worksheet(
            title=hoja_nombre, 
            rows=100, 
            cols=20
        )
    
    
    df_adaptado = convertir_para_sheets(df)

    # Sobrescribir todo
    worksheet.clear()
    worksheet.update([df_adaptado.columns.values.tolist()] + df_adaptado.values.tolist())
    
    print(f"✓ Datos actualizados en Google Sheets: {hoja_nombre} ({len(df_adaptado)} registros)")

def main():   

    jira_url = os.environ.get('JIRA_URL')
    jira_user = os.environ.get('JIRA_USER')
    jira_pass = os.environ.get('JIRA_PASS')

    jira = JiraAID(jira_url, jira_user, jira_pass)


    df_issues = jira.get_issues_projects()
    df_blocks = jira.get_blocks_projects()
    df_issues_hbs = jira.calculate_hbs()
    
    SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')
    
    actualizar_hoja(df_issues, SPREADSHEET_ID, hoja_nombre='REGISTROS')
    actualizar_hoja(jira.df_milestones, SPREADSHEET_ID, hoja_nombre='FASES')
    actualizar_hoja(df_blocks, SPREADSHEET_ID, hoja_nombre='BLOQUEOS')
    actualizar_hoja(df_issues_hbs, SPREADSHEET_ID, hoja_nombre='HBS')
    

if __name__ == '__main__':
    main()