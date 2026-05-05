import streamlit as st
import sqlite3
import os
import pandas as pd
import plotly.express as px
import bcrypt
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

st.set_page_config(page_title="Duarte Gestão", layout="wide")

# =========================
# 🎨 ESTILO
# =========================
st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #0f172a);
}

.card {
    background: #111827;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 🔥 LOGO
# =========================
st.markdown("""
<div style="text-align:center;">
<img src="https://www.duartegestao.com.br/images/logo-duartegestao.png" width="200">
</div>
""", unsafe_allow_html=True)
# =========================
# 🗄️ BANCO DE DADOS
# =========================
def connect():
    os.makedirs("uploads", exist_ok=True)
    return sqlite3.connect("banco.db", check_same_thread=False)

def criar_tabelas():
    conn = connect()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        usuario TEXT UNIQUE,
        email TEXT,
        telefone TEXT,
        cpf TEXT,
        senha TEXT,
        tipo TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        descricao TEXT,
        categoria TEXT,
        centro_custo TEXT,
        valor REAL,
        arquivos TEXT,
        status TEXT DEFAULT 'PENDENTE',
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        data_pagamento TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

# =========================
# 👤 CRIAR USUÁRIOS PADRÃO
# =========================
def criar_admins():
    conn = connect()
    c = conn.cursor()

    usuarios = [
        ("Admin","admin","admin@email.com","11999999999","00000000000","123456","admin"),
        ("Financeiro","financeiro","financeiro@email.com","11999999999","00000000000","123456","financeiro"),
        ("Operacional","operacional","operacional@email.com","11999999999","00000000000","123456","operacional")
    ]

    for nome, user, email, tel, cpf, senha, tipo in usuarios:
        hash_senha = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
        try:
            c.execute("""
            INSERT INTO usuarios (nome, usuario, email, telefone, cpf, senha, tipo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nome, user, email, tel, cpf, hash_senha, tipo))
        except:
            pass  # evita erro se já existir

    conn.commit()
    conn.close()

# 🔥 EXECUTA NA INICIALIZAÇÃO
criar_tabelas()
criar_admins()
# =========================
# 🔐 AUTENTICAÇÃO
# =========================
def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())

def login(usuario, senha):
    conn = connect()
    c = conn.cursor()

    c.execute("SELECT * FROM usuarios WHERE usuario=?", (usuario,))
    user = c.fetchone()

    conn.close()

    if user:
        senha_hash = user[6]  # posição da senha
        if senha_hash and verificar_senha(senha, senha_hash):
            return user

    return None

# =========================
# 🧠 SESSÃO
# =========================
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# =========================
# 🔑 LOGIN / CADASTRO
# =========================
if not st.session_state["logado"]:

    abas = st.tabs(["Login", "Criar Conta"])

    # ================= LOGIN =================
    with abas[0]:
        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            resultado = login(user, senha)

            if resultado:
                st.session_state["logado"] = True
                st.session_state["usuario"] = resultado[2]
                st.session_state["nome"] = resultado[1]
                st.session_state["email"] = resultado[3]
                st.session_state["tipo"] = resultado[7]

                st.success("Login realizado!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

    # ================= CADASTRO =================
    with abas[1]:
        nome = st.text_input("Nome completo", key="cad_nome")
        user = st.text_input("Usuário", key="cad_user")
        email = st.text_input("Email", key="cad_email")
        telefone = st.text_input("Telefone", key="cad_tel")
        cpf = st.text_input("CPF", key="cad_cpf")
        senha = st.text_input("Senha", type="password", key="cad_pass")

        if st.button("Criar Conta", key="btn_criar"):
            conn = connect()

            try:
                hash_senha = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

                conn.execute("""
                INSERT INTO usuarios (nome, usuario, email, telefone, cpf, senha, tipo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (nome, user, email, telefone, cpf, hash_senha, "usuario"))

                conn.commit()
                st.success("Conta criada com sucesso!")

            except sqlite3.IntegrityError:
                st.error("❌ Usuário já existe.")

            conn.close()

    st.stop()

if not st.session_state["logado"]:
    st.stop()
# =========================
# 📌 MENU LATERAL
# =========================

menu = st.sidebar.radio(
    "Menu",
    ["dashboard", "despesas", "reembolsos"],
    format_func=lambda x: {
        "dashboard": "📊 Dashboard",
        "despesas": "💸 Despesas",
        "reembolsos": "💰 Reembolsos"
    }[x]
)

# =========================
# 📊 DASHBOARD
# =========================
if menu == "dashboard":

    st.title("📊 Dashboard")

    conn = connect()
    df = pd.read_sql("SELECT * FROM despesas", conn)
    conn.close()

    if df.empty:
        st.warning("⚠️ Nenhuma despesa cadastrada ainda.")
    else:
        # =========================
        # 🔥 KPIs
        # =========================
        total = df["valor"].sum()
        qtd = len(df)
        media = df["valor"].mean()

        col1, col2, col3 = st.columns(3)

        col1.metric("💰 Total", f"R$ {total:.2f}")
        col2.metric("📦 Registros", qtd)
        col3.metric("📊 Média", f"R$ {media:.2f}")

        # =========================
        # 🧠 GARANTE COLUNAS
        # =========================
        if "categoria" in df.columns and "valor" in df.columns:

            st.subheader("📊 Despesas por Categoria")

            fig1 = px.pie(
                df,
                names="categoria",
                values="valor",
                hole=0.5
            )

            st.plotly_chart(fig1, use_container_width=True)

        else:
            st.info("Sem dados de categoria ainda.")

        # =========================
        # 🏢 CENTRO DE CUSTO
        # =========================
        if "centro_custo" in df.columns:

            st.subheader("🏢 Gastos por Centro de Custo")

            fig2 = px.bar(
                df,
                x="centro_custo",
                y="valor"
            )

            st.plotly_chart(fig2, use_container_width=True)

# =========================
# 💸 DESPESAS
# =========================
elif menu == "despesas":
    st.title("💸 Despesas")

    tab1, tab2 = st.tabs(["Nova Despesa", "Minhas Despesas"])

    categorias = [
        "Limpeza", "Remuneração Sócios", "Alimentação",
        "Telefonia e Internet", "Software e Licenças",
        "Transportes / Logística", "Material de Escritório",
        "Equipamentos de Informática", "Estacionamento",
        "Móveis e Utensílios", "Despesas de Viagens",
        "Máquinas e Equipamentos"
    ]

    centros = [
        "CREDENCIAMENTO", "REDE", "DIRETORIA",
        "DUARTE GESTÃO", "MARKETING", "FINANCEIRO"
    ]

    # =========================
    # 🆕 NOVA DESPESA
    # =========================
    with tab1:
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0, step=0.01)
        categoria = st.selectbox("Categoria", categorias)
        centro = st.selectbox("Centro de Custo", centros)

        if st.button("Enviar Despesa"):
            if not desc or valor == 0:
                st.warning("Preencha os campos corretamente")
            else:
                conn = connect()

                conn.execute("""
                    INSERT INTO despesas (usuario, descricao, categoria, centro_custo, valor)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    st.session_state["usuario"],
                    desc,
                    categoria,
                    centro,
                    valor
                ))

                conn.commit()
                conn.close()

                st.success("Despesa enviada com sucesso!")
                st.rerun()

    # =========================
    # 📋 MINHAS DESPESAS
    # =========================
    with tab2:
        conn = connect()

        df = pd.read_sql(f"""
            SELECT * FROM despesas 
            WHERE usuario='{st.session_state["usuario"]}'
            ORDER BY id DESC
        """, conn)

        if df.empty:
            st.info("Nenhuma despesa encontrada.")
        else:
            for _, row in df.iterrows():
                st.markdown(f"""
                <div class="card">
                    💸 <b>{row['descricao']}</b><br>
                    💰 R$ {row['valor']}<br>
                    📂 {row['categoria']} | {row['centro_custo']}<br>
                    📊 Status: {row['status']}
                </div>
                """, unsafe_allow_html=True)

        conn.close()

# =========================
# 💰 REEMBOLSOS
# =========================
elif menu == "reembolsos":
    st.title("💰 Reembolsos")
    st.info("Reembolsos functionality coming soon!")