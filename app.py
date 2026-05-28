import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime

# Configuração
st.set_page_config(page_title="Duarte ERP Pro", layout="wide")

# Conexão Banco
conn = sqlite3.connect("duarte.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS transacoes 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   tipo TEXT, categoria TEXT, valor REAL, data DATE)""")
# Tabela de usuários expandida
cursor.execute("""CREATE TABLE IF NOT EXISTS usuarios 
                  (usuario TEXT PRIMARY KEY, senha TEXT, nome_completo TEXT, 
                   cpf TEXT, telefone TEXT, email TEXT)""")
conn.commit()

# --- ESTADO DA SESSÃO ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# --- FUNÇÃO DE LOGIN E CADASTRO ---
def tela_login():
    st.title("🔐 Acesso ao Sistema")
    tab1, tab2 = st.tabs(["Entrar", "Novo Cadastro"])
    
    with tab1:
        u = st.text_input("Usuário", key="login_u")
        p = st.text_input("Senha", type="password", key="login_p")
        if st.button("ENTRAR"):
            cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, p))
            if cursor.fetchone():
                st.session_state["logado"] = True
                st.rerun()
            else:
                st.error("Usuário ou Senha incorretos!")
                
    with tab2:
        with st.form("form_cadastro"):
            nome = st.text_input("Nome Completo")
            user = st.text_input("Nome de Usuário")
            cpf = st.text_input("CPF")
            tel = st.text_input("Telefone")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            
            if st.form_submit_button("CADASTRAR"):
                try:
                    cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?, ?, ?)", 
                                   (user, senha, nome, cpf, tel, email))
                    conn.commit()
                    st.success("Cadastro realizado! Faça o login agora.")
                except:
                    st.error("Erro: Usuário já existente.")

# --- FLUXO PRINCIPAL ---
if not st.session_state["logado"]:
    tela_login()
else:
    # Sidebar
    st.sidebar.title("🚀 Duarte ERP v2.0")
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard & Saldo", "💸 Lançar Transação", "📋 Relatório & Export"])
    if st.sidebar.button("Sair do Sistema"):
        st.session_state["logado"] = False
        st.rerun()

    # --- DASHBOARD & TRANSAÇÕES (Mesma lógica anterior) ---
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

    elif menu == "📋 Relatório & Export":
        st.title("📋 Relatório Detalhado")
        df = pd.read_sql("SELECT * FROM transacoes", conn)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Relatório (CSV)", data=csv, file_name="relatorio.csv", mime="text/csv")