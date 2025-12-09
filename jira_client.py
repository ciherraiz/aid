import os
from jira import JIRA
import streamlit as st

def get_config(key):
    # 1. Si está en streamlit secrets, lo usamos
    if key in st.secrets:
        return st.secrets[key]

    # 2. Si está en variables de entorno (Codespaces, local)
    if key in os.environ:
        return os.environ[key]

    raise KeyError(f"No se encuentra la variable de configuración: {key}")

class JiraClient:
    def __init__(self):
        jira_url = get_config("JIRA_URL")
        jira_user = get_config("JIRA_USER")
        jira_token = get_config("JIRA_TOKEN")

        if not jira_url or not jira_user or not jira_token:
            raise ValueError("Faltan variables de entorno para conectar a Jira")

        self.jira = JIRA(
            server=jira_url,
            basic_auth=(jira_user, jira_token)
        )

    def get_projects_by_category(self, category_name):
        """Obtiene proyectos filtrados por categoría."""
        all_projects = self.jira.projects()
        return [p for p in all_projects if getattr(p, "projectCategory", None) and 
                p.projectCategory.name == category_name]