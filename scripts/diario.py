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
    
    # Opción 2: Añadir al final (comentar opción 1 y descomentar esto)
    # existing_data = worksheet.get_all_values()
    # if len(existing_data) == 0:
    #     # Primera vez: añadir encabezados
    #     worksheet.append_row(df.columns.values.tolist())
    # worksheet.append_rows(df.values.tolist())
    
    print(f"✓ Datos actualizados en Google Sheets: {hoja_nombre}")

def main():
    """Función principal que ejecuta todo el proceso"""
    # 1. Crear instancia de tu clase
    analizador = JiraClient(parametro1="valor_ejemplo")
    
    # 2. Generar el DataFrame
    df = analizador.generar_reporte()
    print(f"✓ DataFrame generado con {len(df)} filas")
    
    # 3. ID de tu Google Sheet (sacado de la URL)
    # URL ejemplo: https://docs.google.com/spreadsheets/d/ABC123XYZ/edit
    # El ID es: ABC123XYZ
    SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID', 'TU_ID_AQUI')
    
    # 4. Actualizar Google Sheets
    actualizar_hoja(df, SPREADSHEET_ID, hoja_nombre='Reporte Diario')
    
    print("✓ Proceso completado exitosamente")

if __name__ == '__main__':
    main()