import sys
import subprocess

# Tenta importar o que é essencial, se falhar, tenta instalar automaticamente
def check_requirements():
    required = ['streamlit', 'pandas', 'plotly', 'psycopg2-binary']
    for lib in required:
        try:
            __import__(lib)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

check_requirements()

# AGORA sim, faz os imports normais
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os
import psycopg2
# ... resto do seu código

# --- CONEXÃO ---
def get_db():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    return sqlite3.connect("duarte.db", check_same_thread=False) if not DATABASE_URL else psycopg2.connect(DATABASE_URL, sslmode='require')

conn = get_db()
cursor = conn.cursor()

# --- GARANTIR CRIAÇÃO DAS TABELAS ---
def criar_tabelas():
    cur = conn.cursor()
    # Cria tabela de usuários se não existir
    cur.execute("CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, nome TEXT, usuario TEXT UNIQUE, senha TEXT)")
    # Cria tabela de despesas se não existir
    cur.execute("CREATE TABLE IF NOT EXISTS despesas (id SERIAL PRIMARY KEY, categoria TEXT, valor REAL)")
    conn.commit()

criar_tabelas() # Chama a função aqui para rodar uma vez só

# --- INTERFACE ---
st.set_page_config(page_title="Duarte ERP", layout="wide")

if "logado" not in st.session_state: st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.title("🛡️ Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        cursor.execute("SELECT * FROM usuarios WHERE usuario = %s AND senha = %s", (u, p))
        user = cursor.fetchone()
        if user:
            st.session_state.update({"logado": True, "user": user[2]})
            st.rerun()
        else: st.error("Credenciais inválidas.")
else:
    # AQUI ESTÃO AS SUAS ABAS DE VOLTA
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "💸 Lançar Despesa", "📋 Relatórios"])
    if st.sidebar.button("SAIR"): st.session_state["logado"] = False; st.rerun()

    if menu == "📊 Dashboard":
        st.title("📊 Painel de Controle")
        # Exemplo de leitura de dados
        try:
            df = pd.read_sql("SELECT * FROM despesas", conn)
            if not df.empty:
                st.metric("Total Gasto", f"R$ {df['valor'].sum():,.2f}")
                st.plotly_chart(px.pie(df, names="categoria", values="valor"))
            else: st.info("Nenhuma despesa lançada ainda.")
        except: st.warning("Banco de dados vazio ou tabela inexistente.")

    elif menu == "💸 Lançar Despesa":
        st.title("💸 Nova Despesa")
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor")
        if st.button("Salvar"):
            cursor.execute("INSERT INTO despesas (descricao, valor) VALUES (%s, %s)", (desc, valor))
            conn.commit()
            st.success("Despesa salva!")

    elif menu == "📋 Relatórios":
        st.title("📋 Relatórios")
        df = pd.read_sql("SELECT * FROM despesas", conn)
        st.dataframe(df)