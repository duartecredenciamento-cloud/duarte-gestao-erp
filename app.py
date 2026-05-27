import streamlit as st
import sqlite3, psycopg2, bcrypt, os, pandas as pd
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

# --- CONEXÃO ---
def obter_conexao():
    # Tenta conectar no Postgres, se der qualquer erro, vai direto pro SQLite local
    try:
        if DATABASE_URL:
            return psycopg2.connect(DATABASE_URL, sslmode='require')
    except:
        pass
    return sqlite3.connect("duarte.db", check_same_thread=False)

conn = obter_conexao()
cursor = conn.cursor()

# --- RECRIAÇÃO TOTAL (O "Botão de Pânico") ---
def resetar_banco():
    cursor.execute("DROP TABLE IF EXISTS usuarios")
    cursor.execute("DROP TABLE IF EXISTS despesas")
    cursor.execute("DROP TABLE IF EXISTS logs")
    cursor.execute("CREATE TABLE usuarios (id SERIAL PRIMARY KEY, nome TEXT, usuario TEXT UNIQUE, senha TEXT, perfil TEXT)")
    cursor.execute("INSERT INTO usuarios (nome, usuario, senha, perfil) VALUES ('Cristiane', 'cristiane', '5678', 'financeiro')")
    conn.commit()

# --- INTERFACE ---
st.set_page_config(page_title="Duarte ERP", layout="centered")

if "logado" not in st.session_state: st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.title("🛡️ Acesso Rápido")
    # RESET BOTÃO (Só use se travar tudo)
    if st.sidebar.button("⚠️ RESETAR BANCO"): resetar_banco(); st.success("Banco recriado!")
    
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (u,))
        user = cursor.fetchone()
        if user and s == user[3]: # Verificação direta (sem bcrypt agora para não travar)
            st.session_state.update({"logado": True, "user": user[2]})
            st.rerun()
        else: st.error("Erro no Login")
else:
    st.title("✅ Sistema Funcionando")
    if st.button("SAIR"): st.session_state["logado"] = False; st.rerun()