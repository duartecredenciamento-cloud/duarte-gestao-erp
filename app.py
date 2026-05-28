import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Duarte ERP Elite", layout="wide")

# Conexão Banco
conn = sqlite3.connect("duarte.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS transacoes 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   usuario TEXT, tipo TEXT, categoria TEXT, valor REAL, data DATE)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS usuarios 
                  (usuario TEXT PRIMARY KEY, senha TEXT, nome TEXT, 
                   cpf TEXT, tel TEXT, email TEXT, nivel TEXT)""")

# --- CRIAÇÃO AUTOMÁTICA DOS ADMS ---
def criar_adms():
    adms = [
        ('admin', '1234', 'Admin Principal', '000', '000', 'financeiro.duartegestao@gmail.com', 'admin'),
        ('operacional', '1234', 'Gestor Operacional', '000', '000', 'financeiro.duartegestao@gmail.com', 'admin'),
        ('financeiro', '1234', 'Gestor Financeiro', '000', '000', 'financeiro.duartegestao@gmail.com', 'admin')
    ]
    for u in adms:
        try:
            cursor.execute("INSERT INTO usuarios VALUES (?,?,?,?,?,?,?)", u)
            conn.commit()
        except:
            pass # Usuário já existe
criar_adms()

# --- SESSÃO ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
    st.session_state["user_data"] = None

def tela_login():
    st.title("🔐 Acesso Restrito")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, p))
        user = cursor.fetchone()
        if user:
            st.session_state["logado"] = True
            st.session_state["user_data"] = {"user": user[0], "nivel": user[6]}
            st.rerun()
        else:
            st.error("Credenciais inválidas.")

if not st.session_state["logado"]:
    tela_login()
else:
    st.sidebar.title(f"👤 {st.session_state['user_data']['user']}")
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "💸 Transações", "📋 Gestão de Usuários"])
    if st.sidebar.button("Sair"):
        st.session_state["logado"] = False
        st.rerun()

    if menu == "📊 Dashboard":
        st.title("📊 Dashboard Executivo")
        df = pd.read_sql("SELECT * FROM transacoes", conn)
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Receitas", f"R$ {df[df['tipo']=='Receita']['valor'].sum():,.2f}")
            c2.metric("Despesas", f"R$ {df[df['tipo']=='Despesa']['valor'].sum():,.2f}")
            c3.metric("Saldo", f"R$ {(df[df['tipo']=='Receita']['valor'].sum() - df[df['tipo']=='Despesa']['valor'].sum()):,.2f}")
            st.plotly_chart(px.pie(df, names="tipo", values="valor"), use_container_width=True)

    elif menu == "💸 Transações":
        st.title("💸 Lançar Transação")
        with st.form("add_trans"):
            tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
            cat = st.text_input("Categoria")
            val = st.number_input("Valor", min_value=0.0)
            if st.form_submit_button("Lançar"):
                cursor.execute("INSERT INTO transacoes (usuario, tipo, categoria, valor, data) VALUES (?, ?, ?, ?, ?)", 
                               (st.session_state['user_data']['user'], tipo, cat, val, datetime.now()))
                conn.commit()
                st.success("Registrado!")

    elif menu == "📋 Gestão de Usuários":
        st.title("📋 Área Administrativa")
        st.write("Aqui você pode ver todos os usuários cadastrados.")
        st.dataframe(pd.read_sql("SELECT usuario, nome, nivel FROM usuarios", conn))