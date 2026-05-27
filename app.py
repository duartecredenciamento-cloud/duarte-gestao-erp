import streamlit as st
import sqlite3
import psycopg2  # Nova biblioteca para o banco na nuvem
from psycopg2 import errors as pg_errors
import pandas as pd
import bcrypt
import os
import time
from datetime import datetime
import plotly.express as px
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# CONFIGURAÇÃO DA PÁGINA (Deve ser a primeira instrução)
st.set_page_config(
    page_title="Duarte | Gestão Inteligente",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_EMAIL = os.getenv("SENHA_EMAIL")
DATABASE_URL = os.getenv("DATABASE_URL")  # Pega o banco do Render

os.makedirs("uploads", exist_ok=True)

# 🔌 FUNÇÃO DE CONEXÃO INTELIGENTE (Postgres na Nuvem ou SQLite Local)
def obter_conexao():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect("duarte.db", check_same_thread=False)

conn = obter_conexao()
cursor = conn.cursor()

# Define o marcador de variáveis dinamicamente (%s para Postgres, ? para SQLite)
p = "%s" if DATABASE_URL else "?"

def init_db():
    id_auto = "SERIAL PRIMARY KEY" if DATABASE_URL else "INTEGER PRIMARY KEY AUTOINCREMENT"
    text_type = "TEXT"
    
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS usuarios (
        id {id_auto},
        nome {text_type},
        usuario {text_type} UNIQUE,
        email {text_type},
        telefone {text_type},
        cpf {text_type},
        senha {text_type},
        perfil {text_type}
    )
    """)
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS despesas (
        id {id_auto},
        usuario {text_type},
        descricao {text_type},
        categoria {text_type},
        centro_custo {text_type},
        valor REAL,
        arquivo {text_type},
        status {text_type} DEFAULT 'PENDENTE',
        data {text_type}
    )
    """)
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS logs (
        id {id_auto},
        usuario {text_type},
        acao {text_type},
        data_hora {text_type}
    )
    """)
    conn.commit()

init_db()

def hash_senha(senha):
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())

def criar_usuarios_padrao():
    usuarios = [
        ("Administrador", "admin", "admin@duartegestao.com.br", "11999999999", "00000000000", "1234", "admin"),
        ("Financeiro", "financeiro", "financeiro@duartegestao.com.br", "11999999999", "00000000000", "1234", "financeiro")
    ]
    for nome, usuario, email, telephone, cpf, senha, perfil in usuarios:
        senha_hash = hash_senha(senha)
        try:
            cursor.execute(f"""
            INSERT INTO usuarios (nome, usuario, email, telefone, cpf, senha, perfil)
            VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p})
            """, (nome, usuario, email, telephone, cpf, senha_hash, perfil))
        except (sqlite3.IntegrityError, Exception):
            if DATABASE_URL:
                conn.rollback()
    conn.commit()

criar_usuarios_padrao()

def registrar_log(usuario, acao):
    cursor.execute(f"""
    INSERT INTO logs (usuario, acao, data_hora)
    VALUES ({p}, {p}, {p})
    """, (usuario, acao, datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    conn.commit()

def enviar_email(destinatario, descricao, valor):
    if not EMAIL_REMETENTE or not SENHA_EMAIL:
        return
    try:
        corpo = f"Reembolso aprovado!\n\nDescrição: {descricao}\nValor: R$ {valor:.2f}\n\nDuarte Gestão"
        msg = MIMEText(corpo)
        msg["Subject"] = "Reembolso Pago"
        msg["From"] = EMAIL_REMETENTE
        msg["To"] = destinatario

        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(EMAIL_REMETENTE, SENHA_EMAIL)
        servidor.send_message(msg)
        servidor.quit()
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

# =========================================
# ESTILO CORPORATIVO CLEAN PREMIUM (WHITE MODE)
# =========================================
st.markdown("""
<style>
.stApp { background-color: #f8fafc; color: #1e293b; font-family: 'Inter', sans-serif; }
footer {visibility: hidden;}
h1, h2, h3, p, label { color: #0f172a !important; }
.stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
    background-color: #ffffff !important; color: #1e293b !important; border-radius: 8px !important;
    border: 1px solid #cbd5e1 !important; padding: 10px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important; color: white !important;
    border-radius: 8px !important; font-weight: 600 !important; padding: 10px 24px !important;
    border: none !important; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2) !important; transition: all 0.2s ease;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 6px 12px -2px rgba(37, 99, 235, 0.3) !important; }
.card-despesa { background: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.card-log { background: #ffffff; padding: 12px 20px; border-radius: 8px; border-left: 4px solid #3b82f6; border-top: 1px solid #f1f5f9; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px rgba(0,0,0,0.02); }
section[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0; }
section[data-testid="stSidebar"] .stRadio label p { color: #334155 !important; font-size: 15px !important; font-weight: 500 !important; }
.user-box { background: #f8fafc; padding: 16px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 25px; }
</style>
""", unsafe_allow_html=True)

# HEADER DA PÁGINA
col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=90)
    else:
        st.markdown("<h1 style='margin:0; font-size: 50px;'>🏢</h1>", unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="padding-top:5px;">
        <h2 style="margin:0; color:#0f172a; font-weight:700;">Duarte Gestão ERP</h2>
        <p style="margin:0; color:#64748b; font-size:14px;">Plataforma Corporativa de Controle Financeiro</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    col_login, _ = st.columns([1, 1])
    with col_login:
        abas = st.tabs(["🔐 Acessar Sistema", "📝 Cadastrar Colaborador"])
        with abas[0]:
            st.markdown("<br>", unsafe_allow_html=True)
            usuario_input = st.text_input("Usuário", key="login_usuario")
            senha_input = st.text_input("Senha", type="password", key="login_senha")
            if st.button("Entrar no ERP", key="btn_login"):
                cursor.execute(f"SELECT * FROM usuarios WHERE usuario={p}", (usuario_input,))
                user = cursor.fetchone()
                if user and verificar_senha(senha_input, user[6]):
                    st.session_state["logado"] = True
                    st.session_state["usuario"] = user[2]
                    st.session_state["nome_completo"] = user[1]
                    st.session_state["perfil"] = user[7]
                    st.success("✅ Autenticado com sucesso!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Credenciais incorretas.")
        with abas[1]:
            st.markdown("<br>", unsafe_allow_html=True)
            nome = st.text_input("Nome Completo", key="cad_nome")
            usuario_novo = st.text_input("Nome de Usuário", key="cad_usuario")
            email = st.text_input("E-mail Corporativo", key="cad_email")
            telefone = st.text_input("Telefone", key="cad_telefone")
            cpf = st.text_input("CPF", key="cad_cpf")
            senha_nova = st.text_input("Senha de Acesso", type="password", key="cad_senha")
            if st.button("Finalizar Cadastro", key="btn_criar"):
                if nome and usuario_novo and senha_nova:
                    senha_hash = hash_senha(senha_nova)
                    try:
                        cursor.execute(f"""
                        INSERT INTO usuarios (nome, usuario, email, telefone, cpf, senha, perfil)
                        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, 'usuario')
                        """, (nome, usuario_novo, email, telefone, cpf, senha_hash))
                        conn.commit()
                        st.success("✅ Conta criada! Prossiga para a aba de Login.")
                    except (sqlite3.IntegrityError, Exception):
                        if DATABASE_URL: conn.rollback()
                        st.error("❌ Este nome de usuário já está em uso.")
                else:
                    st.warning("⚠️ Preencha Nome, Usuário e Senha.")
    st.stop()

# INTERFACE LOGADA
st.sidebar.markdown(f"""
<div class="user-box">
    <span style="color: #64748b; font-size: 11px; font-weight: 600; letter-spacing: 0.5px;">OPERADOR ATIVO</span>
    <div style="color: #0f172a; font-weight: 700; font-size: 15px; margin-top: 2px;">{st.session_state.get('nome_completo')}</div>
    <span style="background: #eff6ff; color: #2563eb; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; display: inline-block; margin-top: 6px;">
        💼 {st.session_state.get('perfil').upper()}
    </span>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<p style='color: #64748b; font-size: 11px; font-weight: 600; margin-bottom: 5px;'>MENU DE NAVEGAÇÃO</p>", unsafe_allow_html=True)

menu = st.sidebar.radio(
    "Navegação",
    ["📊 Dashboard Geral", "💸 Lançar Despesa", "📋 Relatório de Despesas", "📜 Auditoria (Logs)"],
    label_visibility="collapsed"
)

st.sidebar.markdown("<br><hr style='margin: 10px 0; border-color: #f1f5f9;'><br>", unsafe_allow_html=True)
if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True):
    st.session_state["logado"] = False
    st.clear()
    st.rerun()

# 📊 DASHBOARD
if menu == "📊 Dashboard Geral":
    st.title("📊 Painel Executivo")
    if st.session_state["perfil"] in ["admin", "financeiro"]:
        df = pd.read_sql("SELECT * FROM despesas", conn)
    else:
        # Ajustado para aceitar a sintaxe correta em ambos os bancos
        if DATABASE_URL:
            df = pd.read_sql("SELECT * FROM despesas WHERE usuario=%s", conn, params=(st.session_state["usuario"],))
        else:
            df = pd.read_sql("SELECT * FROM despesas WHERE usuario=?", conn, params=(st.session_state["usuario"],))
        
    total = df["valor"].sum() if not df.empty else 0
    qtd = len(df)
    
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(f"""<div style="background:#ffffff; padding:20px; border-radius:8px; border:1px solid #e2e8f0;"><span style="color:#64748b; font-size:14px; font-weight:600;">VALOR TOTAL LANÇADO</span><h2 style="margin:5px 0 0 0; color:#1e293b; font-weight:700;">R$ {total:,.2f}</h2></div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div style="background:#ffffff; padding:20px; border-radius:8px; border:1px solid #e2e8f0;"><span style="color:#64748b; font-size:14px; font-weight:600;">SOLICITAÇÕES REGISTRADAS</span><h2 style="margin:5px 0 0 0; color:#1e293b; font-weight:700;">{qtd} registros</h2></div>""", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    if not df.empty:
        titulo_grafico = "Distribuição de Custos da Empresa por Categoria" if st.session_state["perfil"] in ["admin", "financeiro"] else "Meus Gastos por Categoria"
        fig = px.pie(df, names="categoria", values="valor", hole=0.4, title=titulo_grafico)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#1e293b")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma transferência financeira encontrada para gerar gráficos.")

# 💸 LANÇAR DESPESA
elif menu == "💸 Lançar Despesa":
    st.title("💸 Nova Solicitação de Reembolso")
    col_form, _ = st.columns([2, 1])
    with col_form:
        descricao = st.text_input("Descrição Clara do Gasto")
        valor = st.number_input("Valor da Despesa (R$)", min_value=0.0, step=0.01)
        c1, c2 = st.columns(2)
        with c1: categoria = st.selectbox("Categoria do Gasto", ["Alimentação", "Transporte", "Software e Licenças", "Material Escritório", "Marketing", "Outros"])
        with c2: centro = st.selectbox("Centro de Custo", ["FINANCEIRO", "CREDENCIAMENTO", "REDE", "MARKETING", "DIRETORIA"])
        arquivo = st.file_uploader("Anexar Comprovante Fiscal (Imagem/PDF)")
        
        if st.button("Enviar para Aprovação"):
            if not descricao or valor <= 0:
                st.error("Preencha a descrição e defina um valor válido.")
            else:
                caminho_arquivo = ""
                if arquivo:
                    nome_arquivo = f"{datetime.now().timestamp()}_{arquivo.name}"
                    caminho_arquivo = os.path.join("uploads", nome_arquivo)
                    with open(caminho_arquivo, "wb") as f: f.write(arquivo.read())
                
                cursor.execute(f"""
                INSERT INTO despesas (usuario, descricao, categoria, centro_custo, valor, arquivo, status, data)
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, 'PENDENTE', {p})
                """, (st.session_state["usuario"], descricao, categoria, centro, valor, caminho_arquivo, datetime.now().strftime("%d/%m/%Y")))
                conn.commit()
                registrar_log(st.session_state["usuario"], f"Solicitou Reembolso: {descricao} (R$ {valor:.2f})")
                st.success("✅ Solicitação enviada!")
                time.sleep(0.5)
                st.rerun()

# 📋 RELATÓRIO DE DESPESAS
elif menu == "📋 Relatório de Despesas":
    st.title("📋 Painel de Prestação de Contas")
    if st.session_state["perfil"] in ["admin", "financeiro"]:
        df = pd.read_sql("SELECT * FROM despesas ORDER BY id DESC", conn)
    else:
        if DATABASE_URL:
            df = pd.read_sql("SELECT * FROM despesas WHERE usuario=%s ORDER BY id DESC", conn, params=(st.session_state["usuario"],))
        else:
            df = pd.read_sql("SELECT * FROM despesas WHERE usuario=? ORDER BY id DESC", conn, params=(st.session_state["usuario"],))
        
    if df.empty:
        st.warning("Nenhum lançamento pendente ou registrado.")
    else:
        for _, row in df.iterrows():
            cor_status = "#eab308" if row['status'] == "PENDENTE" else "#16a34a" if row['status'] in ["APROVADO", "PAGO"] else "#dc2626"
            st.markdown(f"""
            <div class="card-despesa">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:18px; font-weight:700; color:#0f172a;">{row['descricao']}</span>
                    <span style="background:{cor_status}; color:white; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600;">{row['status']}</span>
                </div>
                <div style="margin-top:10px; color:#475569; font-size:14px;">Colaborador: <b>{row['usuario']}</b> | Categoria: <b>{row['categoria']}</b> | Centro: <b>{row['centro_custo']}</b> | Data: {row['data']}</div>
                <div style="margin-top:10px; font-size:20px; font-weight:700; color:#2563eb;">R$ {row['valor']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.session_state["perfil"] in ["admin", "financeiro"] and row['status'] == 'PENDENTE':
                col1, col2, col3, _ = st.columns([1, 1, 1, 3])
                with col1:
                    if st.button("✅ Aprovar", key=f"ap_{row['id']}"):
                        cursor.execute(f"UPDATE despesas SET status='APROVADO' WHERE id={p}", (row["id"],))
                        conn.commit()
                        registrar_log(st.session_state["usuario"], f"Aprovou a despesa ID {row['id']}")
                        st.rerun()
                with col2:
                    if st.button("❌ Rejeitar", key=f"rej_{row['id']}"):
                        cursor.execute(f"UPDATE despesas SET status='REJEITADO' WHERE id={p}", (row["id"],))
                        conn.commit()
                        registrar_log(st.session_state["usuario"], f"Rejeitou a despesa ID {row['id']}")
                        st.rerun()
                with col3:
                    if st.button("💰 Pagar", key=f"pg_{row['id']}"):
                        cursor.execute(f"UPDATE despesas SET status='PAGO' WHERE id={p}", (row["id"],))
                        conn.commit()
                        registrar_log(st.session_state["usuario"], f"Efetuou pagamento da despesa ID {row['id']}")
                        
                        # Ajustado busca de email para a sintaxe atual
                        cursor.execute(f"SELECT email FROM usuarios WHERE usuario={p}", (row['usuario'],))
                        user_email = cursor.fetchone()
                        if user_email and user_email[0]: 
                            enviar_email(user_email[0], row['descricao'], row['valor'])
                        st.rerun()

# 📜 TIMELINE DE AUDITORIA (LOGS)
elif menu == "📜 Auditoria (Logs)":
    st.title("📜 Trilha de Auditoria e Segurança")
    if st.session_state["perfil"] in ["admin", "financeiro"]:
        df_logs = pd.read_sql("SELECT * FROM logs ORDER BY id DESC LIMIT 50", conn)
        if df_logs.empty: st.info("Nenhuma atividade registrada.")
        else:
            for _, log in df_logs.iterrows():
                st.markdown(f"""<div class="card-log"><div><span style="font-weight:600; color:#1e293b;">{log['usuario']}</span><span style="color:#475569; margin-left:8px;">{log['acao']}</span></div><div style="color:#94a3b8; font-size:12px;">⏱️ {log['data_hora']}</div></div>""", unsafe_allow_html=True)
    else:
        st.error("🔒 Acesso restrito.")