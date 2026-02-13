import pandas as pd
from datetime import datetime

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