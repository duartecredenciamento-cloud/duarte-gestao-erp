import streamlit as st
import sqlite3
import psycopg2
import bcrypt
import os
import time
import pandas as pd
import plotly.express as px
from datetime import datetime
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import io

# --- CONFIGURAÇÃO E INIT ---
load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def obter_conexao():
    return psycopg2.connect(DATABASE_URL, sslmode='require') if DATABASE_URL else sqlite3.connect("duarte.db", check_same_thread=False)

conn = obter_conexao()
cursor = conn.cursor()
p = "%s" if DATABASE_URL else "?"

def init_db():
    cursor.execute(f"CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, nome TEXT, usuario TEXT UNIQUE, email TEXT, telefone TEXT, cpf TEXT, senha TEXT, perfil TEXT)")
    cursor.execute(f"CREATE TABLE IF NOT EXISTS despesas (id SERIAL PRIMARY KEY, usuario TEXT, descricao TEXT, categoria TEXT, centro_custo TEXT, valor REAL, arquivo TEXT, status TEXT, data TEXT)")
    cursor.execute(f"CREATE TABLE IF NOT EXISTS logs (id SERIAL PRIMARY KEY, usuario TEXT, acao TEXT, data_hora TEXT)")
    conn.commit()

init_db()

def registrar_log(usuario, acao):
    cursor.execute(f"INSERT INTO logs (usuario, acao, data_hora) VALUES ({p}, {p}, {p})", (usuario, acao, datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    conn.commit()

def verificar_senha(senha, senha_hash):
    try:
        if bcrypt.checkpw(senha.encode(), senha_hash.encode()): return True
    except: pass
    return senha == senha_hash

# --- INTERFACE ---
st.set_page_config(page_title="Duarte Gestão", layout="wide")

if "logado" not in st.session_state: st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.title("🛡️ Duarte Gestão ERP")
    aba1, aba2 = st.tabs(["🔐 Acessar", "📝 Cadastro"])
    
    with aba1:
        u_in = st.text_input("Usuário")
        s_in = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            cursor.execute(f"SELECT * FROM usuarios WHERE LOWER(usuario) = LOWER({p})", (u_in,))
            user = cursor.fetchone()
            if user and verificar_senha(s_in, user[6]):
                st.session_state.update({"logado": True, "usuario": user[2], "nome": user[1], "perfil": user[7]})
                st.rerun()
            else: st.error("Credenciais inválidas.")

    with aba2:
        nome = st.text_input("Nome"); user_n = st.text_input("Usuário"); email = st.text_input("Email")
        tel = st.text_input("Telefone"); cpf = st.text_input("CPF"); senha_n = st.text_input("Senha", type="password")
        if st.button("Cadastrar"):
            try:
                cursor.execute(f"INSERT INTO usuarios (nome, usuario, email, telefone, cpf, senha, perfil) VALUES ({p}, {p}, {p}, {p}, {p}, {p}, 'usuario')",
                               (nome, user_n, email, tel, cpf, bcrypt.hashpw(senha_n.encode(), bcrypt.gensalt()).decode()))
                conn.commit()
                st.success("Usuário criado!")
            except Exception as e: st.error(f"Erro: {e}")
else:
    # --- SISTEMA LOGADO ---
    st.sidebar.title(f"Olá, {st.session_state['nome']}")
    menu = st.sidebar.radio("Navegação", ["Dashboard", "Lançar Despesa", "Relatórios", "Auditoria"])
    if st.sidebar.button("Sair"): st.session_state["logado"] = False; st.rerun()

    if menu == "Dashboard":
        st.title("📊 Dashboard")
        df = pd.read_sql("SELECT * FROM despesas", conn)
        if not df.empty:
            st.metric("Total", f"R$ {df['valor'].sum():,.2f}")
            st.plotly_chart(px.pie(df, names="categoria", values="valor"), use_container_width=True)

    elif menu == "Lançar Despesa":
        st.title("💸 Lançar Despesa")
        desc = st.text_input("Descrição"); val = st.number_input("Valor", min_value=0.0)
        arq = st.file_uploader("Comprovante")
        if st.button("Enviar"):
            url = cloudinary.uploader.upload(arq)["secure_url"] if arq else ""
            cursor.execute(f"INSERT INTO despesas (usuario, descricao, valor, status, data, arquivo) VALUES ({p}, {p}, {p}, 'PENDENTE', {p}, {p})",
                           (st.session_state["usuario"], desc, val, datetime.now().strftime("%d/%m/%Y"), url))
            conn.commit()
            registrar_log(st.session_state["usuario"], f"Lançou despesa: {desc}")
            st.success("Enviado!")

    elif menu == "Relatórios":
        st.title("📋 Relatórios")
        st.dataframe(pd.read_sql("SELECT * FROM despesas", conn))

    elif menu == "Auditoria":
        st.title("📜 Logs de Auditoria")
        st.dataframe(pd.read_sql("SELECT * FROM logs ORDER BY id DESC", conn))