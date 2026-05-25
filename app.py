import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
import os
import time
from datetime import datetime
import plotly.express as px

# =========================
# CONFIG DA PÁGINA
# =========================
st.set_page_config(
    page_title="Duarte Gestão ERP",
    page_icon="🏢",
    layout="wide"
)

# =========================
# ESTILO VISUAL PREMIUM
# =========================
st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #163B73, #1F4E95);
    color: white;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: #0F274B;
}

/* BOTÕES */
.stButton > button {
    background: linear-gradient(90deg,#F59E0B,#F97316);
    color: white;
    border: none;
    border-radius: 14px;
    padding: 10px 20px;
    font-weight: bold;
    transition: 0.3s;
}

.stButton > button:hover {
    transform: scale(1.05);
    box-shadow: 0px 0px 20px rgba(255,165,0,0.5);
}

/* INPUTS */
.stTextInput input,
.stNumberInput input,
.stSelectbox div {
    border-radius: 12px !important;
}

/* CARDS */
.card {
    background: rgba(255,255,255,0.08);
    padding: 20px;
    border-radius: 18px;
    backdrop-filter: blur(10px);
    margin-bottom: 15px;
    animation: fadeUp 0.5s ease;
}

.card:hover {
    transform: translateY(-5px);
    transition: 0.3s;
}

/* ANIMAÇÃO */
@keyframes fadeUp {
    from {
        opacity:0;
        transform:translateY(20px);
    }
    to {
        opacity:1;
        transform:translateY(0px);
    }
}

/* TÍTULOS */
h1, h2, h3 {
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

# =========================
# LOGO DA DUARTE
# =========================
col1, col2 = st.columns([1,4])

with col1:
    st.image("logo.png", width=180)

with col2:
    st.markdown("""
    <h1 style='margin-top:35px;'>
        Duarte Gestão ERP
    </h1>
    """, unsafe_allow_html=True)

st.markdown("---")
# =========================================
# BANCO
# =========================================
os.makedirs("uploads", exist_ok=True)

conn = sqlite3.connect("duarte.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    usuario TEXT UNIQUE,
    senha TEXT,
    perfil TEXT
)
""")

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
    data TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    acao TEXT,
    data_hora TEXT
)
""")

conn.commit()

# =========================================
# SENHA
# =========================================
def hash_senha(senha):
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())

# =========================================
# USUÁRIOS PADRÃO
# =========================================
def criar_usuarios():

    usuarios = [
        ("Administrador", "admin", "1234", "admin"),
        ("Financeiro", "financeiro", "1234", "financeiro"),
        ("Operacional", "operacional", "1234", "operacional")
    ]

    for nome, usuario, senha, perfil in usuarios:

        senha_hash = hash_senha(senha)

        try:
            cursor.execute("""
            INSERT INTO usuarios (nome, usuario, senha, perfil)
            VALUES (?, ?, ?, ?)
            """, (nome, usuario, senha_hash, perfil))

        except:
            pass

    conn.commit()

criar_usuarios()

# =========================================
# LOGIN
# =========================================
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:

    st.title("🔐 Login")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):

        cursor.execute("""
        SELECT * FROM usuarios
        WHERE usuario=?
        """, (usuario,))

        user = cursor.fetchone()

        if user and verificar_senha(senha, user[3]):

            st.session_state["logado"] = True
            st.session_state["usuario"] = user[2]
            st.session_state["perfil"] = user[4]
            st.session_state["nome"] = user[1]

            st.success("Login realizado!")
            time.sleep(1)

            st.rerun()

        else:
            st.error("Usuário ou senha inválidos")

    st.stop()

# =========================================
# LOGS
# =========================================
def registrar_log(acao):

    cursor.execute("""
    INSERT INTO logs (usuario, acao, data_hora)
    VALUES (?, ?, ?)
    """, (
        st.session_state["usuario"],
        acao,
        datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    ))

    conn.commit()

# =========================================
# MENU
# =========================================
menu = st.sidebar.radio(
    "Menu",
    [
        "📊 Dashboard",
        "💸 Nova Despesa",
        "📋 Minhas Despesas",
        "💰 Reembolsos",
        "📜 Logs"
    ]
)

# =========================================
# DASHBOARD
# =========================================
if menu == "📊 Dashboard":

    st.title("📊 Dashboard")

    df = pd.read_sql("SELECT * FROM despesas", conn)

    total = df["valor"].sum() if not df.empty else 0
    qtd = len(df)

    col1, col2 = st.columns(2)

    col1.metric("💰 Total", f"R$ {total:,.2f}")
    col2.metric("📦 Registros", qtd)

    if not df.empty:

        fig = px.pie(
            df,
            names="categoria",
            values="valor",
            hole=0.5
        )

        st.plotly_chart(fig, use_container_width=True)

# =========================================
# NOVA DESPESA
# =========================================
elif menu == "💸 Nova Despesa":

    st.title("💸 Nova Despesa")

    categorias = [
        "Alimentação",
        "Transporte",
        "Software e Licenças",
        "Material Escritório",
        "Marketing",
        "Outros"
    ]

    centros = [
        "FINANCEIRO",
        "CREDENCIAMENTO",
        "REDE",
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

    arquivo = st.file_uploader("Anexar comprovante")

    if st.button("Salvar Despesa"):

        caminho_arquivo = ""

        if arquivo:

            nome_arquivo = f"{datetime.now().timestamp()}_{arquivo.name}"

            caminho_arquivo = os.path.join(
                "uploads",
                nome_arquivo
            )

            with open(caminho_arquivo, "wb") as f:
                f.write(arquivo.read())

        cursor.execute("""
        INSERT INTO despesas
        (
            usuario,
            descricao,
            categoria,
            centro_custo,
            valor,
            arquivo,
            data
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            st.session_state["usuario"],
            descricao,
            categoria,
            centro,
            valor,
            caminho_arquivo,
            datetime.now().strftime("%d/%m/%Y")
        ))

        conn.commit()

        registrar_log("Nova despesa cadastrada")

        st.success("✅ Despesa cadastrada!")
        st.balloons()

# =========================================
# MINHAS DESPESAS
# =========================================
elif menu == "📋 Minhas Despesas":

    st.title("📋 Minhas Despesas")

    df = pd.read_sql("""
    SELECT * FROM despesas
    WHERE usuario=?
    ORDER BY id DESC
    """, conn, params=(st.session_state["usuario"],))

    if df.empty:

        st.warning("Nenhuma despesa encontrada.")

    else:

        for _, row in df.iterrows():

            st.markdown(f"""
            <div class="card">
                <h3>{row['descricao']}</h3>

                💰 R$ {row['valor']}<br>
                📂 {row['categoria']}<br>
                🏢 {row['centro_custo']}<br>
                📅 {row['data']}<br>
                📊 Status: <b>{row['status']}</b>
            </div>
            """, unsafe_allow_html=True)

            if row["arquivo"] and os.path.exists(row["arquivo"]):

                with open(row["arquivo"], "rb") as file:

                    st.download_button(
                        "📥 Baixar Comprovante",
                        file,
                        file_name=os.path.basename(row["arquivo"]),
                        key=row["id"]
                    )

# =========================================
# REEMBOLSOS
# =========================================
elif menu == "💰 Reembolsos":

    st.title("💰 Gestão de Reembolsos")

    if st.session_state["perfil"] not in [
        "admin",
        "financeiro",
        "operacional"
    ]:

        st.warning("Sem permissão.")
        st.stop()

    df = pd.read_sql("""
    SELECT * FROM despesas
    ORDER BY id DESC
    """, conn)

    if df.empty:

        st.warning("Sem despesas.")

    else:

        for _, row in df.iterrows():

            st.markdown(f"""
            <div class="card">

            👤 <b>{row['usuario']}</b><br>
            💸 {row['descricao']}<br>
            💰 R$ {row['valor']}<br>
            📂 {row['categoria']}<br>
            📊 STATUS: <b>{row['status']}</b>

            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)

            if col1.button("✅ Aprovar", key=f"ap_{row['id']}"):

                cursor.execute("""
                UPDATE despesas
                SET status='APROVADO'
                WHERE id=?
                """, (row["id"],))

                conn.commit()

                registrar_log(f"Aprovou ID {row['id']}")

                st.success("Aprovado!")
                st.rerun()

            if col2.button("❌ Rejeitar", key=f"rej_{row['id']}"):

                cursor.execute("""
                UPDATE despesas
                SET status='REJEITADO'
                WHERE id=?
                """, (row["id"],))

                conn.commit()

                registrar_log(f"Rejeitou ID {row['id']}")

                st.warning("Rejeitado!")
                st.rerun()

            if col3.button("💰 Pago", key=f"pg_{row['id']}"):

                cursor.execute("""
                UPDATE despesas
                SET status='PAGO'
                WHERE id=?
                """, (row["id"],))

                conn.commit()

                registrar_log(f"Pagou ID {row['id']}")

                st.success("Pagamento realizado!")
                st.balloons()

                st.rerun()

# =========================================
# LOGS
# =========================================
elif menu == "📜 Logs":

    st.title("📜 Logs")

    logs = pd.read_sql("""
    SELECT * FROM logs
    ORDER BY id DESC
    """, conn)

    st.dataframe(logs, use_container_width=True)