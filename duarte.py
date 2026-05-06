import streamlit as st
import sqlite3
import os
import pandas as pd
import plotly.express as px
import bcrypt
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import smtplib
from email.mime.text import MIMEText

EMAIL_REMETENTE = "financeiro.duartegestao@gmail.com"
SENHA_EMAIL = "mzia irrz yimu jhnu"

st.set_page_config(page_title="Duarte Gestão", layout="wide")
def enviar_email(destinatario, nome, descricao, valor, categoria, centro_custo, data_pagamento):
    try:
        corpo = f"""
Olá {nome},

Seu reembolso foi aprovado e pago com sucesso! 🎉

📄 Descrição: {descricao}
📂 Categoria: {categoria}
🏢 Centro de Custo: {centro_custo}
💰 Valor: R$ {valor}
📅 Data do Pagamento: {data_pagamento}

⚠️ NÃO RESPONDER ESTE EMAIL

Duarte Gestão
"""

        msg = MIMEText(corpo)
        msg["Subject"] = "💰 Reembolso Pago"
        msg["From"] = EMAIL_REMETENTE
        msg["To"] = destinatario

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        print("Conectando no email...")
        server.login(EMAIL_REMETENTE, SENHA_EMAIL)

        print("Enviando email...")
        server.send_message(msg)

        server.quit()

        st.success("📧 Email enviado com sucesso!")

    except Exception as e:
        st.error(f"❌ Erro ao enviar email: {e}")
        print("ERRO REAL:", e)

st.markdown("""
<style>

/* =========================
🎯 BASE GLOBAL
========================= */
html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}

/* =========================
🔥 SIDEBAR PREMIUM
========================= */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #0f172a);
    border-right: 1px solid rgba(255,255,255,0.05);
}

/* =========================
📦 CARDS MODERNOS
========================= */
.card {
    background: linear-gradient(145deg, #111827, #1f2937);
    padding: 18px;
    border-radius: 16px;
    margin-bottom: 15px;
    color: #e5e7eb;
    border: 1px solid rgba(255,255,255,0.05);
    
    transition: all 0.3s ease;
    animation: fadeInUp 0.5s ease;
}

.card:hover {
    transform: translateY(-6px) scale(1.02);
    box-shadow: 0 15px 35px rgba(0,0,0,0.5);
}

/* =========================
✨ ANIMAÇÃO DE ENTRADA
========================= */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* =========================
🔥 BOTÕES ESTILO PRO
========================= */
.stButton>button {
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white;
    border-radius: 12px;
    padding: 10px 16px;
    border: none;
    font-weight: 600;

    transition: all 0.25s ease;
}

.stButton>button:hover {
    transform: scale(1.05);
    box-shadow: 0 8px 20px rgba(37,99,235,0.5);
}

/* =========================
✅ SUCCESS ANIMADO
========================= */
.success-check {
    background: linear-gradient(90deg,#22c55e,#16a34a);
    padding: 14px;
    border-radius: 12px;
    color: white;
    text-align: center;
    font-weight: bold;

    animation: popIn 0.4s ease;
}

@keyframes popIn {
    from {
        transform: scale(0.8);
        opacity: 0;
    }
    to {
        transform: scale(1);
        opacity: 1;
    }
}

/* =========================
📊 SCROLLBAR CUSTOM
========================= */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #020617;
}

::-webkit-scrollbar-thumb {
    background: #1d4ed8;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #2563eb;
}

/* =========================
📌 INPUTS MAIS BONITOS
========================= */
input, textarea, select {
    border-radius: 10px !important;
}

/* =========================
📱 TRANSIÇÃO GLOBAL SUAVE
========================= */
* {
    transition: all 0.2s ease;
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
        ("Financeiro","financeiro","financeiro.duartegestao@gmail.com","11999999999","00000000000","123456","financeiro"),
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

    # 📎 ANEXO AQUI
    arquivos = st.file_uploader(
        "📎 Anexar arquivos (PDF, imagem, etc)",
        accept_multiple_files=True
    )

    if st.button("Enviar Despesa"):

        if not desc or valor == 0:
            st.warning("Preencha os campos corretamente")
        else:
            lista_arquivos = []

            # 💾 SALVAR ARQUIVOS
            if arquivos:
                for i, arq in enumerate(arquivos):
                    nome = f"{datetime.now().timestamp()}_{i}_{arq.name}"
                    caminho = os.path.join("uploads", nome)

                    with open(caminho, "wb") as f:
                        f.write(arq.read())

                    lista_arquivos.append(caminho)

            conn = connect()

            conn.execute("""
                INSERT INTO despesas 
                (usuario, descricao, categoria, centro_custo, valor, arquivos)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                st.session_state["usuario"],
                desc,
                categoria,
                centro,
                valor,
                ",".join(lista_arquivos)
            ))

            conn.commit()
            conn.close()

            st.success("💸 Despesa enviada com sucesso!")
            st.balloons()
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

    st.title("💰 Gestão de Reembolsos")

    # 🔒 Permissão
    if st.session_state["tipo"] not in ["admin", "financeiro", "operacional"]:
        st.warning("🚫 Você não tem permissão para acessar essa área.")
        st.stop()

    conn = connect()
    df = pd.read_sql("SELECT * FROM despesas ORDER BY id DESC", conn)

    if df.empty:
        st.info("Nenhuma despesa cadastrada.")
    else:
        for _, row in df.iterrows():

            # =========================
            # 🎴 CARD
            # =========================
            st.markdown(f"""
            <div class="card">
                👤 <b>{row['usuario']}</b><br>
                💸 {row['descricao']}<br>
                💰 R$ {row['valor']}<br>
                📂 {row['categoria']} | {row['centro_custo']}<br>
                📊 Status: <b>{row['status']}</b>
            </div>
            """, unsafe_allow_html=True)

            # =========================
            # 📎 ANEXOS (DENTRO DO FOR ✅)
            # =========================
            if row["arquivos"] and row["arquivos"] != "":
                arquivos = row["arquivos"].split(",")

                for i, arq in enumerate(arquivos):
                    if os.path.exists(arq):

                        if arq.lower().endswith((".png", ".jpg", ".jpeg")):
                            st.image(arq, width=200)

                        else:
                            with open(arq, "rb") as f:
                                st.download_button(
                                    "📎 Baixar arquivo",
                                    f,
                                    file_name=os.path.basename(arq),
                                    key=f"file_{row['id']}_{i}"
                                )

            # =========================
            # 🔥 BOTÕES COM IMPACTO
            # =========================
            col1, col2, col3, col4 = st.columns(4)

            # ✅ APROVAR
            if col1.button("✅ Aprovar", key=f"ap_{row['id']}"):
                conn.execute("UPDATE despesas SET status='APROVADO' WHERE id=?", (row["id"],))
                conn.commit()

                st.markdown("""
                <div style="background:linear-gradient(90deg,#22c55e,#16a34a);
                padding:10px;border-radius:10px;color:white;text-align:center;
                animation: pop 0.3s ease;">
                ✅ Aprovado com sucesso
                </div>
                """, unsafe_allow_html=True)

                st.balloons()
                st.rerun()

            # ❌ REJEITAR
            if col2.button("❌ Rejeitar", key=f"rej_{row['id']}"):
                conn.execute("UPDATE despesas SET status='REJEITADO' WHERE id=?", (row["id"],))
                conn.commit()

                st.markdown("""
                <div style="background:linear-gradient(90deg,#ef4444,#b91c1c);
                padding:10px;border-radius:10px;color:white;text-align:center;
                animation: pop 0.3s ease;">
                ❌ Rejeitado
                </div>
                """, unsafe_allow_html=True)

                st.rerun()

            # 💰 PAGAR
            if col3.button("💰 Pagar", key=f"pg_{row['id']}"):

                if row["status"] == "PAGO":
                    st.warning("⚠️ Já está pago.")
                else:
                    c = conn.cursor()

                    c.execute("SELECT nome, email FROM usuarios WHERE usuario=?", (row["usuario"],))
                    user_data = c.fetchone()

                    if user_data:
                        nome, email = user_data

                        data_pagamento = datetime.now().strftime("%d/%m/%Y %H:%M")

                        enviado = enviar_email(
                            email,
                            nome,
                            row["descricao"],
                            row["valor"],
                            row["categoria"],
                            row["centro_custo"],
                            data_pagamento
                        )
                    if enviado:
                        st.success("📧 Email enviado!")
                    else:
                        st.warning("⚠️ Pagamento feito, mas email falhou.")
                    
                    conn.execute("""
                        UPDATE despesas 
                        SET status='PAGO', data_pagamento=? 
                        WHERE id=?
                    """, (datetime.now(), row["id"]))

                    conn.commit()

                    st.markdown("""
                    <div style="background:linear-gradient(90deg,#16a34a,#22c55e);
                    padding:12px;border-radius:10px;color:white;text-align:center;
                    font-weight:bold;animation: pop 0.3s ease;">
                    💰 PAGAMENTO REALIZADO
                    </div>
                    """, unsafe_allow_html=True)

                    st.balloons()
                    st.rerun()

            # 🗑️ EXCLUIR
            if col4.button("🗑️ Excluir", key=f"del_{row['id']}"):
                conn.execute("DELETE FROM despesas WHERE id=?", (row["id"],))
                conn.commit()

                st.markdown("""
                <div style="background:#111827;padding:10px;border-radius:10px;
                color:white;text-align:center;">
                🗑️ Excluído
                </div>
                """, unsafe_allow_html=True)

                st.rerun()

    conn.close()