import logging
import os

import pandas as pd

from aid import JiraAID
from aid.constants import SHEET_REGISTROS, SHEET_FASES, SHEET_BLOQUEOS, SHEET_HBS
from gsheets import actualizar_hoja

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    logger.info("Inicio de ejecución diaria")

    jira_url = os.environ.get('JIRA_URL')
    jira_user = os.environ.get('JIRA_USER')
    jira_pass = os.environ.get('JIRA_PASS')

    jira = JiraAID(jira_url, jira_user, jira_pass)

    logger.info("Extrayendo issues de proyectos")
    df_issues = jira.get_issues_projects()
    logger.info("Extrayendo bloqueos")
    df_blocks = jira.get_blocks_projects()
    logger.info("Calculando HBS")
    df_issues_hbs = jira.calculate_hbs()
    df_milestones = jira.df_milestones.copy()
    df_milestones.insert(0, 'ID', df_milestones['SOLUCION'] + df_milestones['CENTRO'])

    SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')
    logger.info("Actualizando Google Sheets (id=%s)", SPREADSHEET_ID)

    actualizar_hoja(df_issues, SPREADSHEET_ID, hoja_nombre=SHEET_REGISTROS)
    actualizar_hoja(df_milestones, SPREADSHEET_ID, hoja_nombre=SHEET_FASES)
    actualizar_hoja(df_blocks, SPREADSHEET_ID, hoja_nombre=SHEET_BLOQUEOS)
    actualizar_hoja(df_issues_hbs, SPREADSHEET_ID, hoja_nombre=SHEET_HBS)

    logger.info("Ejecución completada")


if __name__ == '__main__':
    main()
