import streamlit as st
import pandas as pd
from jira_client import JiraClient

st.set_page_config(page_title="AID Dashboard", layout="wide")

st.title("📊 L3 Dashboard")

# Cargar cliente Jira (solo una vez)
@st.cache_resource
def load_jira_client():
    return JiraClient()

jira = load_jira_client()

# Sidebar
st.sidebar.header("Opciones")

data = jira.get_projects_by_category('PROYECTOS AREA IMPLANTACIONES')
df = pd.DataFrame(data)

#st.write(df.columns)

st.dataframe(df[['key', 'name']])