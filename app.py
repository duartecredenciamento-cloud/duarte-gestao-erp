import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os

# Configuração Pika Max
st.set_page_config(page_title="Duarte ERP Pro", layout="wide")

# Estilo customizado (CSS para deixar o sistema mais bonito)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 2px 2px 10px #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

# Conexão
conn = sqlite3.connect("duarte.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS despesas (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, valor REAL, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.commit()

# Sidebar Estilizada
st.sidebar.image("c:\Users\User\Desktop\CODIGOS\duarte-app\assets\logo.png", use_container_width=True)
st.sidebar.title("🚀 Duarte ERP v2.0")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard Executivo", "💸 Lançar Despesa", "📋 Relatório Geral"])

if menu == "📊 Dashboard Executivo":
    st.title("📊 Painel de Controle Pro")
    df = pd.read_sql("SELECT * FROM despesas", conn)
    
    if not df.empty:
        # Métricas de destaque
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Gastos", f"R$ {df['valor'].sum():,.2f}")
        c2.metric("Qtd. de Lançamentos", len(df))
        c3.metric("Média por Despesa", f"R$ {df['valor'].mean():,.2f}")
        
        st.markdown("---")
        
        # Gráficos Pro
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            fig = px.pie(df, names="categoria", values="valor", title="Distribuição de Custos", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with col_graf2:
            fig2 = px.bar(df, x="categoria", y="valor", title="Gastos por Categoria", color="categoria")
            st.plotly_chart(fig2, use_container_width=True)
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
    df = pd.read_sql("SELECT * FROM despesas", conn)
    st.dataframe(df, use_container_width=True)