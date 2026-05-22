import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
import os
import time
from datetime import datetime
import plotly.express as px

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Duarte Gestão ERP",
    page_icon="🏢",
    layout="wide"
)

# =========================
# CSS PREMIUM
# =========================
st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #0f172a);
}

.stButton>button {
    background: linear-gradient(90deg,#2563eb,#1d4ed8);
    color: white;
    border-radius: 10px;
    border: none;
    font-weight: bold;
}

.card {
    background: #111827;
    padding: 15px;
    border-radius: 15px;
    margin-bottom: 10px;
    color: white;
}

</style>
""", unsafe_allow_html=True)

# =========================
# PASTA UPLOADS
# =========================
os.makedirs("uploads", exist_ok=True)

# =========================
# BANCO
# =========================
conn = sqlite3.connect(
    "duarte.db",
    check_same_thread=False
)

cursor = conn.cursor()

# =========================
# TABELA USUARIOS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    usuario TEXT UNIQUE,
    email TEXT,
    senha TEXT,
    tipo TEXT
)
""")

# =========================
# TABELA DESPESAS
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS despesas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    descricao TEXT,
    categoria TEXT,
    centro_custo TEXT,
    valor REAL,
    arquivo TEXT,
    status TEXT DEFAULT 'PENDENTE',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_pagamento TIMESTAMP
)
""")

conn.commit()

# =========================
# CRIAR ADMINS
# =========================
def criar_admins():

    usuarios = [
        (
            "Admin",
            "admin",
            "admin@email.com",
            "123456",
            "admin"
        ),
        (
            "Financeiro",
            "financeiro",
            "financeiro@email.com",
            "123456",
            "financeiro"
        ),
        (
            "Operacional",
            "operacional",
            "operacional@email.com",
            "123456",
            "operacional"
        )
    ]

    for nome, usuario, email, senha, tipo in usuarios:

        hash_senha = bcrypt.hashpw(
            senha.encode(),
            bcrypt.gensalt()
        ).decode()

        try:

            cursor.execute("""
            INSERT INTO usuarios
            (
                nome,
                usuario,
                email,
                senha,
                tipo
            )
            VALUES (?, ?, ?, ?, ?)
            """, (
                nome,
                usuario,
                email,
                hash_senha,
                tipo
            ))

        except:
            pass

    conn.commit()

criar_admins()

# =========================
# LOGIN
# =========================
def verificar_login(usuario, senha):

    cursor.execute(
        "SELECT * FROM usuarios WHERE usuario=?",
        (usuario,)
    )

    user = cursor.fetchone()

    if user:

        senha_hash = user[4]

        if bcrypt.checkpw(
            senha.encode(),
            senha_hash.encode()
        ):
            return user

    return None

# =========================
# SESSION
# =========================
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# =========================
# LOGIN TELA
# =========================
if not st.session_state["logado"]:

    st.markdown("""
    <div style='text-align:center'>
        <img src='https://www.duartegestao.com.br/images/logo-duartegestao.png' width='250'>
    </div>
    """, unsafe_allow_html=True)

    st.title("🔐 Login")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):

        resultado = verificar_login(
            usuario,
            senha
        )

        if resultado:

            st.session_state["logado"] = True
            st.session_state["usuario"] = resultado[2]
            st.session_state["nome"] = resultado[1]
            st.session_state["tipo"] = resultado[5]

            st.success("✅ Login realizado")

            time.sleep(1)

            st.rerun()

        else:
            st.error("❌ Usuário ou senha inválidos")

    st.stop()

# =========================
# LOGO
# =========================
st.markdown("""
<div style="text-align:center; margin-bottom:20px;">

<a href="https://duartegestao.com.br/" target="_blank">

<img 
src="https://duartegestao.com.br/wp-content/uploads/2026/02/logoduarte.webp" 
width="260"
style="cursor:pointer;"
>

</a>

</div>
""", unsafe_allow_html=True)
    
    st.title(f"💼 ERP Duarte Gestão - {st.session_state.perfil.upper()}")

# =========================
# MENU
# =========================
menu = st.sidebar.radio(
    "Menu",
    [
        "Dashboard",
        "Despesas",
        "Reembolsos"
    ]
)

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":

    st.title("📊 Dashboard")

    # ADMIN VE TUDO
    if st.session_state["tipo"] in [
        "admin",
        "financeiro",
        "operacional"
    ]:

        df = pd.read_sql(
            "SELECT * FROM despesas",
            conn
        )

    # USUARIO VE APENAS O DELE
    else:

        df = pd.read_sql(
            """
            SELECT * FROM despesas
            WHERE usuario=?
            """,
            conn,
            params=(st.session_state["usuario"],)
        )

    if df.empty:

        st.warning("Nenhuma despesa encontrada")

    else:

        total = df["valor"].sum()
        qtd = len(df)
        media = df["valor"].mean()

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "💰 Total",
            f"R$ {total:.2f}"
        )

        col2.metric(
            "📦 Registros",
            qtd
        )

        col3.metric(
            "📊 Média",
            f"R$ {media:.2f}"
        )

        fig1 = px.pie(
            df,
            names="categoria",
            values="valor",
            hole=0.5
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

# =========================
# DESPESAS
# =========================
elif menu == "Despesas":

    st.title("💸 Despesas")

    categorias = [
        "Alimentação",
        "Transporte",
        "Internet",
        "Software",
        "Equipamentos",
        "Outros"
    ]

    centros = [
        "CREDENCIAMENTO",
        "REDE",
        "FINANCEIRO",
        "MARKETING",
        "DIRETORIA"
    ]

    descricao = st.text_input("Descrição")

    valor = st.number_input(
        "Valor",
        min_value=0.0,
        step=0.01
    )

    categoria = st.selectbox(
        "Categoria",
        categorias
    )

    centro = st.selectbox(
        "Centro de Custo",
        centros
    )

    arquivo = st.file_uploader(
        "Anexar comprovante"
    )

    if st.button("Enviar Despesa"):

        caminho = ""

        if arquivo:

            nome_arquivo = f"""
            {datetime.now().timestamp()}_
            {arquivo.name}
            """

            nome_arquivo = nome_arquivo.replace(
                " ",
                "_"
            )

            caminho = os.path.join(
                "uploads",
                nome_arquivo
            )

            with open(caminho, "wb") as f:
                f.write(arquivo.read())

        cursor.execute("""
        INSERT INTO despesas
        (
            usuario,
            descricao,
            categoria,
            centro_custo,
            valor,
            arquivo
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            st.session_state["usuario"],
            descricao,
            categoria,
            centro,
            valor,
            caminho
        ))

        conn.commit()

        st.success("✅ Despesa enviada")

        st.balloons()

        time.sleep(1)

        st.rerun()

    st.divider()

    st.subheader("📋 Minhas Despesas")

    minhas = pd.read_sql("""
    SELECT *
    FROM despesas
    WHERE usuario=?
    ORDER BY id DESC
    """, conn, params=(
        st.session_state["usuario"],
    ))

    if minhas.empty:

        st.info("Nenhuma despesa")

    else:

        for _, row in minhas.iterrows():

            st.markdown(f"""
            <div class='card'>

            💸 <b>{row['descricao']}</b><br>
            💰 R$ {row['valor']}<br>
            📂 {row['categoria']}<br>
            📊 {row['status']}

            </div>
            """, unsafe_allow_html=True)

            if row["arquivo"]:

                if os.path.exists(row["arquivo"]):

                    with open(
                        row["arquivo"],
                        "rb"
                    ) as f:

                        st.download_button(
                            "📎 Baixar Arquivo",
                            f,
                            file_name=os.path.basename(
                                row["arquivo"]
                            ),
                            key=row["id"]
                        )

# =========================
# REEMBOLSOS
# =========================
elif menu == "Reembolsos":

    if st.session_state["tipo"] not in [
        "admin",
        "financeiro",
        "operacional"
    ]:

        st.warning("🚫 Sem permissão")
        st.stop()

    st.title("💰 Gestão de Reembolsos")

    df = pd.read_sql("""
    SELECT *
    FROM despesas
    ORDER BY id DESC
    """, conn)

    if df.empty:

        st.info("Nenhuma despesa")

    else:

        for _, row in df.iterrows():

            st.markdown(f"""
            <div class='card'>

            👤 <b>{row['usuario']}</b><br>
            💸 {row['descricao']}<br>
            💰 R$ {row['valor']}<br>
            📊 {row['status']}

            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)

            if col1.button(
                "✅ Aprovar",
                key=f"ap_{row['id']}"
            ):

                cursor.execute("""
                UPDATE despesas
                SET status='APROVADO'
                WHERE id=?
                """, (row["id"],))

                conn.commit()

                st.success("Aprovado")

                st.rerun()

            if col2.button(
                "❌ Rejeitar",
                key=f"rej_{row['id']}"
            ):

                cursor.execute("""
                UPDATE despesas
                SET status='REJEITADO'
                WHERE id=?
                """, (row["id"],))

                conn.commit()

                st.warning("Rejeitado")

                st.rerun()

            if col3.button(
                "💰 Pagar",
                key=f"pg_{row['id']}"
            ):

                cursor.execute("""
                UPDATE despesas
                SET status='PAGO',
                data_pagamento=?
                WHERE id=?
                """, (
                    datetime.now(),
                    row["id"]
                ))

                conn.commit()

                st.success("Pagamento realizado")

                st.balloons()

                st.rerun()