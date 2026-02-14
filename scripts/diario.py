import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
from aid import JiraClient

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

def actualizar_hoja(df, spreadsheet_id, hoja_nombre='Datos'):
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
    
    # Opción 1: Sobrescribir todo
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    
    print(f"✓ Datos actualizados en Google Sheets: {hoja_nombre}")

def main():    
    analizador = JiraClient(parametro1="valor_ejemplo")
    
    
    df = analizador.generar_reporte()
    print(f"✓ DataFrame generado con {len(df)} filas")
    
    SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', 'TU_ID_AQUI')
    
    
    actualizar_hoja(df, SPREADSHEET_ID, hoja_nombre='Reporte Diario')
    
    print("✓ Proceso completado exitosamente")

if __name__ == '__main__':
    main()