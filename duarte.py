import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Duarte Gestão", layout="wide")

# =========================
# DB
# =========================
def connect():
    return sqlite3.connect("banco.db", check_same_thread=False)

def criar_tabelas():
    conn = connect()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT,
        valor REAL,
        status TEXT DEFAULT 'PENDENTE',
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

criar_tabelas()

# =========================
# MENU
# =========================
menu = st.sidebar.radio("Menu", ["Dashboard", "Nova Despesa"])

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":

    st.title("📊 Dashboard")

    conn = connect()
    df = pd.read_sql("SELECT * FROM despesas", conn)

    if not df.empty:
        st.dataframe(df)
    else:
        st.info("Sem dados ainda")

    conn.close()

# =========================
# NOVA DESPESA
# =========================
elif menu == "Nova Despesa":

    st.title("💸 Nova Despesa")

    desc = st.text_input("Descrição")
    valor = st.number_input("Valor")

    if st.button("Salvar"):

        conn = connect()
        conn.execute("""
            INSERT INTO despesas (descricao, valor)
            VALUES (?, ?)
        """, (desc, valor))

        conn.commit()
        conn.close()

        st.success("Salvo com sucesso!")
        st.rerun()
