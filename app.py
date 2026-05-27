import streamlit as st
import sqlite3
import psycopg2  
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
import cloudinary
import cloudinary.uploader
import requests  
import io  

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Duarte | Gestão Inteligente",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_EMAIL = os.getenv("SENHA_EMAIL")
DATABASE_URL = os.getenv("DATABASE_URL")  

# CONFIGURAÇÃO DO CLOUDINARY
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

os.makedirs("uploads", exist_ok=True)

def obter_conexao():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect("duarte.db", check_same_thread=False)

conn = obter_conexao()
cursor = conn.cursor()
p = "%s" if DATABASE_URL else "?"

def init_db():
    id_auto = "SERIAL PRIMARY KEY" if DATABASE_URL else "INTEGER PRIMARY KEY AUTOINCREMENT"
    text_type = "TEXT"
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS usuarios (
        id {id_auto}, nome {text_type}, usuario {text_type} UNIQUE, email {text_type},
        telefone {text_type}, cpf {text_type}, senha {text_type}, perfil {text_type}
    )""")
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS despesas (
        id {id_auto}, usuario {text_type}, descricao {text_type}, categoria {text_type},
        centro_custo {text_type}, valor REAL, arquivo {text_type}, status {text_type} DEFAULT 'PENDENTE', data {text_type}
    )""")
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS logs (
        id {id_auto}, usuario {text_type}, acao {text_type}, data_hora {text_type}
    )""")
    conn.commit()

init_db()

def hash_senha(senha):
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())

def criar_usuarios_padrao():
    SENHA_FORTE_PADRAO = "Duarte1234#"
    usuarios = [
        ("Administrador Geral", "admin", "admin@duartegestao.com.br", "11999999999", "00000000000", SENHA_FORTE_PADRAO, "admin"),
        ("Gestor Operacional", "operacional", "operacional@duartegestao.com.br", "11999999999", "00000000000", SENHA_FORTE_PADRAO, "admin"),
        ("Financeiro", "financeiro", "financeiro@duartegestao.com.br", "11999999999", "00000000000", SENHA_FORTE_PADRAO, "financeiro")
    ]
    for nome, usuario, email, telephone, cpf, senha, perfil in usuarios:
        cursor.execute(f"SELECT id, senha FROM usuarios WHERE usuario={p}", (usuario,))
        registro = cursor.fetchone()
        if not registro:
            senha_hash = hash_senha(senha)
            try:
                cursor.execute(f"INSERT INTO usuarios (nome, usuario, email, telefone, cpf, senha, perfil) VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p})", 
                               (nome, usuario, email, telephone, cpf, senha_hash, perfil))
            except Exception:
                if DATABASE_URL: conn.rollback()
        else:
            if not verificar_senha(SENHA_FORTE_PADRAO, registro[1]):
                nova_senha_hash = hash_senha(SENHA_FORTE_PADRAO)
                cursor.execute(f"UPDATE usuarios SET senha={p} WHERE usuario={p}", (nova_senha_hash, usuario))
    conn.commit()

criar_usuarios_padrao()

def registrar_log(usuario, acao):
    cursor.execute(f"INSERT INTO logs (usuario, acao, data_hora) VALUES ({p}, {p}, {p})", 
                   (usuario, acao, datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    conn.commit()

# ==============================================================================
# 🎨 ESTILIZAÇÃO CSS: VISUAL ESCURO, CLEAN E SEM BOXES INTRUSIVOS
# ==============================================================================
st.markdown("""
<style>
/* Fundo Escuro Corporativo Padrão */
.stApp {
    background: radial-gradient(circle at center, #0b2230 0%, #051017 100%) !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif;
}

footer {visibility: hidden;}

/* Textos do Painel Interno Sempre Visíveis */
h1, h2, h3, .stMarkdown p {
    color: #ffffff !important;
}
.titulo-painel {
    color: #ffffff !important;
    font-weight: 800 !important;
    font-size: 30px !important;
    margin-bottom: 20px !important;
}

/* Área de Login Clean e Escura */
.login-container {
    max-width: 480px;
    margin: 60px auto;
    padding: 20px;
    text-align: center;
}
.login-title {
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 28px !important;
    margin-top: 15px !important;
    margin-bottom: 5px !important;
}
.login-subtitle {
    color: #00f2fe !important;
    font-size: 13px !important;
    margin-bottom: 30px !important;
}

/* Customização dos Inputs para o modo Escuro */
.stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
    background-color: rgba(255, 255, 255, 0.07) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 8px !important;
    padding: 10px !important;
}

/* Abas Customizadas */
div[data-testid="stTabBar"] {
    background-color: transparent !important;
    margin-bottom: 20px;
}
div[data-testid="stTabBar"] button {
    color: #94a3b8 !important;
}
div[data-testid="stTabBar"] button[aria-selected="true"] {
    color: #00f2fe !important;
    font-weight: 700 !important;
    border-bottom: 2px solid #00f2fe !important;
}

/* Botão Padrão Neon */
.stButton > button {
    background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%) !important;
    color: #051017 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 12px 0px !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(0, 242, 254, 0.2) !important;
    width: 100%;
}

/* Painel de Lançamentos Internos */
.card-despesa { background: rgba(255, 255, 255, 0.04); padding: 20px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 15px; }
.card-despesa span, .card-despesa div, .card-despesa b { color: #ffffff !important; }
.card-log { background: rgba(255,255,255,0.03); padding: 12px 20px; border-radius: 8px; border-left: 4px solid #00f2fe; margin-bottom: 8px; display: flex; justify-content: space-between; }
section[data-testid="stSidebar"] { background-color: #06151f !important; border-right: 1px solid rgba(0,242,254,0.1); }
.user-box { background: rgba(255,255,255,0.03); padding: 16px; border-radius: 10px; border: 1px solid rgba(0,242,254,0.1); margin-top: 15px; }
</style>
""", unsafe_allow_html=True)

if "logado" not in st.session_state: st.session_state["logado"] = False

# ==============================================================================
# DEFINIÇÃO DA LOGO OFICIAL (CORRIGIDO PARA O SEU ARQUIVO)
# ==============================================================================
# Procura diretamente pelo arquivo correto enviado por você
caminho_logo = "logo_2.JPG" if os.path.exists("logo_2.JPG") else ("logo.JPG" if os.path.exists("logo.JPG") else None)

# ==============================================================================
# INTERFACE DE LOGIN PURE CLEAN DARK
# ==============================================================================
if not st.session_state["logado"]:
    _, col_central, _ = st.columns([1, 1.5, 1])
    
    with col_central:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Renderização direta da Logo Oficial
        if caminho_logo:
            st.image(caminho_logo, width=180)
        else:
            st.markdown("<h1 style='margin:0; font-size: 40px;'>🏢</h1>", unsafe_allow_html=True)
            
        st.markdown('<div class="login-title">Duarte Gestão ERP</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Plataforma Corporativa de Controle Financeiro</div>', unsafe_allow_html=True)
        
        abas = st.tabs(["Acessar Sistema", "Cadastrar Colaborador"])
        
        with abas[0]:
            st.markdown("<br>", unsafe_allow_html=True)
            usuario_input = st.text_input("Usuário", key="login_usuario")
            senha_input = st.text_input("Senha", type="password", key="login_senha")
            st.markdown("<br>", unsafe_allow_html=True)
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
            telefone = st.text_input("Telefone (Apenas números)", key="cad_telefone")
            cpf = st.text_input("CPF (Apenas números)", key="cad_cpf")
            senha_nova = st.text_input("Senha de Acesso", type="password", key="cad_senha")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Finalizar Cadastro", key="btn_criar"):
                cpf_limpo = "".join(filter(str.isdigit, cpf))
                if not nome or not usuario_novo or not senha_nova or len(cpf_limpo) != 11:
                    st.error("❌ Preencha todos os campos. O CPF deve conter exatamente 11 dígitos numéricos.")
                else:
                    senha_hash = hash_senha(senha_nova)
                    try:
                        cursor.execute(f"INSERT INTO usuarios (nome, usuario, email, telefone, cpf, senha, perfil) VALUES ({p}, {p}, {p}, {p}, {p}, {p}, 'usuario')", 
                                       (nome, usuario_novo, email, telephone, cpf_limpo, senha_hash))
                        conn.commit()
                        st.success("✅ Conta criada com sucesso!")
                    except Exception:
                        if DATABASE_URL: conn.rollback()
                        st.error("❌ Este nome de usuário já existe.")
                        
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# PAINEL INTERNO PÓS-LOGIN
# ==============================================================================
if caminho_logo:
    st.sidebar.image(caminho_logo, use_container_width=True)

st.sidebar.markdown(f"""
<div class="user-box">
    <span style="color: #00f2fe; font-size: 11px; font-weight: 600;">OPERADOR ATIVO</span>
    <div style="color: #ffffff; font-weight: 700; font-size: 15px;">{st.session_state.get('nome_completo')}</div>
    <span style="background: rgba(0,242,254,0.1); color: #00f2fe; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; display: inline-block; margin-top: 6px;">💼 {st.session_state.get('perfil').upper()}</span>
</div>""", unsafe_allow_html=True)

menu = st.sidebar.radio("Navegação", ["📊 Painel Geral", "💸 Lançar Despesa", "📋 Relatório de Despesas", "📜 Auditório (Logs)"])

if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True):
    st.session_state["logado"] = False
    st.clear()
    st.rerun()

# 📊 DASHBOARD GERAL
if menu == "📊 Painel Geral":
    st.markdown('<div class="titulo-painel">BI - Painel de Inteligência Financeira</div>', unsafe_allow_html=True)
    df_base = pd.read_sql("SELECT * FROM despesas", conn) if st.session_state["perfil"] in ["admin", "financeiro"] else pd.read_sql(f"SELECT * FROM despesas WHERE usuario='{st.session_state['usuario']}'", conn)

    if not df_base.empty:
        df_base['date_parsed'] = pd.to_datetime(df_base['data'], format='%d/%m/%Y', errors='coerce')
        df_base['Mes_Ano'] = df_base['date_parsed'].dt.strftime('%m/%Y').fillna("Sem Data")

        f1, f2, f3 = st.columns(3)
        with f1: filtro_mes = st.selectbox("Filtrar por Mês/Ano", ["Todos"] + sorted(list(df_base['Mes_Ano'].unique())))
        with f2: filtro_centro = st.selectbox("Filtrar por Centro de Custo", ["Todos"] + sorted(list(df_base['centro_custo'].unique())))
        with f3: filtro_status = st.selectbox("Filtrar por Status", ["Todos", "PENDENTE", "APROVADO", "PAGO", "REJEITADO"])

        df_filtrado = df_base.copy()
        if filtro_mes != "Todos": df_filtrado = df_filtrado[df_filtrado['Mes_Ano'] == filtro_mes]
        if filtro_centro != "Todos": df_filtrado = df_filtrado[df_filtrado['centro_custo'] == filtro_centro]
        if filtro_status != "Todos": df_filtrado = df_filtrado[df_filtrado['status'] == filtro_status]

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.markdown(f'<div style="background:rgba(255,255,255,0.05); padding:22px; border-radius:10px; border-left: 5px solid #2563eb;"><span style="color:#94a3b8; font-size:13px; font-weight:600;">VALOR FILTRADO</span><h2 style="margin:5px 0 0 0; font-weight:700; color:#ffffff;">R$ {df_filtrado["valor"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
        kpi2.markdown(f'<div style="background:rgba(255,255,255,0.05); padding:22px; border-radius:10px; border-left: 5px solid #16a34a;"><span style="color:#16a34a; font-size:13px; font-weight:600;">TOTAL PAGO</span><h2 style="margin:5px 0 0 0; color:#16a34a; font-weight:700;">R$ {df_filtrado[df_filtrado["status"] == "PAGO"]["valor"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
        kpi3.markdown(f'<div style="background:rgba(255,255,255,0.05); padding:22px; border-radius:10px; border-left: 5px solid #eab308;"><span style="color:#eab308; font-size:13px; font-weight:600;">TOTAL PENDENTE</span><h2 style="margin:5px 0 0 0; color:#eab308; font-weight:700;">R$ {df_filtrado[df_filtrado["status"] == "PENDENTE"]["valor"].sum():,.2f}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(px.pie(df_filtrado, names="categoria", values="valor", hole=0.4, title="Gastos por Categoria"), use_container_width=True)
        with g2:
            df_centro = df_filtrado.groupby("centro_custo")["valor"].sum().reset_index()
            st.plotly_chart(px.bar(df_centro, x="centro_custo", y="valor", title="Investimento por Centro de Custo"), use_container_width=True)
    else: 
        st.info("Nenhum dado encontrado.")

# 💸 LANÇAR DESPESA
elif menu == "💸 Lançar Despesa":
    st.markdown('<div class="titulo-painel">💸 Nova Solicitação de Reembolso</div>', unsafe_allow_html=True)
    col_form, _ = st.columns([2, 1])
    with col_form:
        descricao = st.text_input("Descrição Clara do Gasto")
        valor = st.number_input("Valor da Despesa (R$)", min_value=0.0, step=0.01)
        c1, c2 = st.columns(2)
        categoria = c1.selectbox("Categoria", ["Alimentação", "Transporte", "Software e Licenças", "Material Escritório", "Marketing", "Outros"])
        centro = c2.selectbox("Centro de Custo", ["FINANCEIRO", "CREDENCIAMENTO", "REDE", "MARKETING", "DIRETORIA"])
        arquivo = st.file_uploader("Anexar Comprovante Fiscal (Imagem/PDF) *OBRIGATÓRIO*", type=['png', 'jpg', 'jpeg', 'pdf'])
        
        if st.button("Enviar para Aprovação"):
            if not descricao or valor <= 0 or not arquivo:
                st.error("❌ Preencha todos os campos e adicione o comprovante.")
            else:
                with st.spinner("Enviando comprovante..."):
                    upload_result = cloudinary.uploader.upload(arquivo, folder="comprovantes_duarte")
                    url_arquivo_nuvem = upload_result.get("secure_url")
                
                cursor.execute(f"INSERT INTO despesas (usuario, descricao, categoria, centro_custo, valor, arquivo, status, data) VALUES ({p}, {p}, {p}, {p}, {p}, {p}, 'PENDENTE', {p})",
                               (st.session_state["usuario"], descricao, categoria, centro, valor, url_arquivo_nuvem, datetime.now().strftime("%d/%m/%Y")))
                conn.commit()
                registrar_log(st.session_state["usuario"], f"Solicitou Reembolso: {descricao}")
                st.success("✅ Solicitação enviada!")
                time.sleep(0.5); st.rerun()

# 📋 RELATÓRIO DE DESPESAS
elif menu == "📋 Relatório de Despesas":
    st.markdown('<div class="titulo-painel">📋 Painel de Prestação de Contas</div>', unsafe_allow_html=True)
    df = pd.read_sql("SELECT * FROM despesas ORDER BY id DESC", conn) if st.session_state["perfil"] in ["admin", "financeiro"] else pd.read_sql(f"SELECT * FROM despesas WHERE usuario='{st.session_state['usuario']}' ORDER BY id DESC", conn)
        
    if df.empty: 
        st.warning("Nenhum lançamento registrado.")
    else:
        for _, row in df.iterrows():
            cor_status = "#eab308" if row['status'] == "PENDENTE" else "#16a34a" if row['status'] in ["APROVADO", "PAGO"] else "#dc2626"
            st.markdown(f"""
            <div class="card-despesa">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:18px; font-weight:700;">{row['descricao']}</span>
                    <span style="background:{cor_status}; color:white; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600;">{row['status']}</span>
                </div>
                <div style="margin-top:10px; font-size:20px; font-weight:700; color:#00f2fe;">R$ {row['valor']:.2f}</div>
            </div>""", unsafe_allow_html=True)

# 📜 AUDITORIA (LOGS)
elif menu == "📜 Auditório (Logs)":
    st.markdown('<div class="titulo-painel">📜 Trilha de Auditoria e Segurança</div>', unsafe_allow_html=True)
    if st.session_state["perfil"] in ["admin", "financeiro"]:
        df_logs = pd.read_sql("SELECT * FROM logs ORDER BY id DESC LIMIT 50", conn)
        if df_logs.empty: st.info("Sem atividades.")
        else:
            for _, log in df_logs.iterrows():
                st.markdown(f'<div class="card-log"><div><span style="font-weight:600; color:#00f2fe;">{log["usuario"]}</span><span style="color:#ffffff; margin-left:8px;">{log["acao"]}</span></div><div style="color:#94a3b8; font-size:12px;">⏱️ {log["data_hora"]}</div></div>', unsafe_allow_html=True)