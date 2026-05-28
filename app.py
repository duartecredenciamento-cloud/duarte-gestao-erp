import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

# Configuração
st.set_page_config(page_title="Duarte ERP Pro", layout="wide")



# Inicializa sessão
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# --- FUNÇÃO DE LOGIN ---
def tela_login():
    st.title("🔐 Login de Acesso")
    user = st.text_input("Usuário")
    pwd = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if user == "admin" and pwd == "1234": # Altere conforme sua necessidade
            st.session_state["logado"] = True
            st.rerun()
        else:
            st.error("Usuário ou Senha incorretos!")

# --- FLUXO PRINCIPAL ---
if not st.session_state["logado"]:
    tela_login()
else:
    # AQUI ENTRA TODO O SEU DASHBOARD E MENU
        st.sidebar.image("assets/logo.png", use_container_width=True) 
        st.sidebar.title("🚀 Duarte ERP v2.0")
    # ... resto do seu código de menu aqui ...
    if st.sidebar.button("Sair do Sistema"):
        st.session_state["logado"] = False
        st.rerun()