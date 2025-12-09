import streamlit as st
import pandas as pd
from jira_client import JiraClient

st.set_page_config(page_title="AID Dashboard", layout="wide")

st.title("📊 Dashboard Jira con Streamlit")

# Cargar cliente Jira (solo una vez)
@st.cache_resource
def load_jira_client():
    return JiraClient()

jira = load_jira_client()

# Sidebar
st.sidebar.header("Opciones")