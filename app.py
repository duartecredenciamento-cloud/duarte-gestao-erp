import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Duarte ERP Pro", layout="wide")

# Conexão Banco
conn = sqlite3.connect("duarte.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS transacoes 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   tipo TEXT, categoria TEXT, valor REAL, data DATE)""")
conn.commit()

# --- ESTADO DA SESSÃO ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# --- FUNÇÃO DE LOGIN ---
def tela_login():
    st.title("🔐 Login de Acesso")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if u == "aline" and p == "1234": # Ajuste aqui o usuário e senha da Aline
            st.session_state["logado"] = True
            st.rerun()
        else:
            st.error("Credenciais inválidas.")

# --- FLUXO DE PROTEÇÃO ---
if not st.session_state["logado"]:
    tela_login()
else:
    # --- SIDEBAR (LOGO E MENU) ---
    # Certifique-se de que a pasta 'assets' está na raiz do seu projeto
    try:
        st.sidebar.image("assets/logo.png", use_container_width=True)
    except:
        st.sidebar.warning("Logo não encontrada na pasta assets.")
        
    st.sidebar.title("🚀 Duarte ERP v2.0")
    
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard & Saldo", "💸 Lançar Transação", "📋 Relatório & Export"])
    
    if st.sidebar.button("Sair do Sistema"):
        st.session_state["logado"] = False
        st.rerun()

    # --- DASHBOARD ---
    if menu == "📊 Dashboard & Saldo":
        st.title("📊 Painel Executivo")
        df = pd.read_sql("SELECT * FROM transacoes", conn)
        if not df.empty:
            df['data'] = pd.to_datetime(df['data'])
            receitas = df[df['tipo'] == 'Receita']['valor'].sum()
            despesas = df[df['tipo'] == 'Despesa']['valor'].sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 Receitas", f"R$ {receitas:,.2f}")
            c2.metric("💸 Despesas", f"R$ {despesas:,.2f}")
            c3.metric("📈 Saldo Atual", f"R$ {receitas - despesas:,.2f}")
            
            st.plotly_chart(px.pie(df, names="tipo", values="valor", title="Distribuição Financeira"), use_container_width=True)
        else:
            st.info("Nenhuma transação registrada.")

    # --- LANÇAR TRANSAÇÃO ---
    elif menu == "💸 Lançar Transação":
        st.title("💸 Lançar Entrada/Saída")
        with st.form("form_transacao"):
            tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
            cat = st.text_input("Categoria")
            val = st.number_input("Valor", min_value=0.0)
            data = st.date_input("Data", datetime.now())
            if st.form_submit_button("Confirmar Lançamento"):
                cursor.execute("INSERT INTO transacoes (tipo, categoria, valor, data) VALUES (?, ?, ?, ?)", (tipo, cat, val, data))
                conn.commit()
                st.success("Transação registrada!")

    # --- RELATÓRIO & EXPORT ---
    elif menu == "📋 Relatório & Export":
        st.title("📋 Relatório Detalhado")
        df = pd.read_sql("SELECT * FROM transacoes", conn)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Relatório (CSV)", data=csv, file_name="relatorio.csv", mime="text/csv")