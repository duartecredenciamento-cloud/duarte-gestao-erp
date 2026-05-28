import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

# Configuração da página
st.set_page_config(page_title="Duarte ERP Pro", layout="wide")

# Conexão Banco
conn = sqlite3.connect("duarte.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS despesas (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, valor REAL)")
conn.commit()

# Inicializa sessão
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# --- FUNÇÃO DE LOGIN ---
def tela_login():
    st.title("🔐 Login de Acesso")
    user = st.text_input("Usuário")
    pwd = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if user == "admin" and pwd == "1234":
            st.session_state["logado"] = True
            st.rerun()
        else:
            st.error("Usuário ou Senha incorretos!")

# --- FLUXO PRINCIPAL ---
if not st.session_state["logado"]:
    tela_login()
else:
    # Sidebar
    st.sidebar.image("assets/logo.png", use_container_width=True)
    st.sidebar.title("🚀 Duarte ERP v2.0")
    
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard Executivo", "💸 Lançar Despesa", "📋 Relatório Geral"])
    
    if st.sidebar.button("Sair do Sistema"):
        st.session_state["logado"] = False
        st.rerun()

    # --- DASHBOARD ---
    if menu == "📊 Dashboard Executivo":
        st.title("📊 Painel de Controle Pro")
        df = pd.read_sql("SELECT * FROM despesas", conn)
        
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total de Gastos", f"R$ {df['valor'].sum():,.2f}")
            c2.metric("Qtd. de Lançamentos", len(df))
            c3.metric("Média por Despesa", f"R$ {df['valor'].mean():,.2f}")
            
            st.plotly_chart(px.pie(df, names="categoria", values="valor", hole=0.4), use_container_width=True)
        else:
            st.info("Nenhum dado registrado para análise.")

    elif menu == "💸 Lançar Despesa":
        st.title("💸 Lançamento de Custos")
        with st.form("form_despesa"):
            cat = st.selectbox("Categoria", ["Operacional", "RH", "Marketing", "Infraestrutura", "Outros"])
            val = st.number_input("Valor da Despesa", min_value=0.0)
            submit = st.form_submit_button("Registrar no Sistema")
            
            if submit:
                cursor.execute("INSERT INTO despesas (categoria, valor) VALUES (?, ?)", (cat, val))
                conn.commit()
                st.success(f"Sucesso! {cat} lançado.")

    elif menu == "📋 Relatório Geral":
        st.title("📋 Relatório Detalhado")
        st.dataframe(pd.read_sql("SELECT * FROM despesas", conn), use_container_width=True)