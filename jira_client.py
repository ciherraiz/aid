import os
from jira import JIRA
import streamlit as st

def get_key(key):

    if key in os.environ:
        return os.environ[key]

    if key in st.secrets:
        return st.secrets[key]
    
    raise KeyError(f"No se encuentra la variable de configuración: {key}")

class JiraClient:
    def __init__(self):
        jira_url = get_key("JIRA_URL")
        jira_user = get_key("JIRA_USER")
        jira_token = get_key("JIRA_PASS")

        if not jira_url or not jira_user:
            raise ValueError("Error en configuración de autenticación")

        self.jira = JIRA(
            server=jira_url,
            basic_auth=(jira_user, jira_token)
        )

    def get_projects_by_category(self, category_name):
        """Obtiene proyectos filtrados por categoría."""
        all_projects = self.jira.projects()
        return [p for p in all_projects if getattr(p, "projectCategory", None) and 
                p.projectCategory.name == category_name]