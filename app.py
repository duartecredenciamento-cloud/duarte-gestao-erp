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
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Duarte | Gestão Inteligente",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()
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
# 🎨 ESTILIZAÇÃO CSS: CLÁSSICO E ULTRA CLEAN (FONTE E INPUTS CORRIGIDOS)
# ==============================================================================
st.markdown("""
<style>
/* Fundo Claro, Neutro e Sofisticado */
.stApp {
    background-color: #f8fafc !important;
    color: #1e293b !important;
    font-family: 'Inter', sans-serif;
}

footer {visibility: hidden;}

/* Força os Textos das Etiquetas (Labels) a ficarem Escuros e Nítidos */
label, .stWidgetLabel p, [data-testid="stMetricLabel"] {
    color: #334155 !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}

/* Customização dos Inputs - Fundo Branco com Bordas Finas Elevadas */
.stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
    background-color: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    padding: 10px !important;
    font-weight: 500 !important;
}

/* Títulos do Painel Principal */
h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    color: #0f172a !important;
    font-weight: 700 !important;
}
.titulo-painel {
    color: #0f172a !important;
    font-weight: 800 !important;
    font-size: 28px !important;
    margin-bottom: 25px !important;
}

/* Área de Login Clean Centralizada */
.login-container {
    max-width: 450px;
    margin: 50px auto;
    padding: 30px;
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    border: 1px solid #e2e8f0;
    text-align: center;
}
.login-title {
    color: #0f172a !important;
    font-weight: 700 !important;
    font-size: 24px !important;
    margin-top: 15px !important;
    margin-bottom: 5px !important;
}
.login-subtitle {
    color: #64748b !important;
    font-size: 13px !important;
    margin-bottom: 25px !important;
}

/* Abas Customizadas Modernas */
div[data-testid="stTabBar"] {
    background-color: transparent !important;
    margin-bottom: 15px;
}
div[data-testid="stTabBar"] button {
    color: #64748b !important;
}
div[data-testid="stTabBar"] button[aria-selected="true"] {
    color: #1e40af !important;
    font-weight: 700 !important;
    border-bottom: 2px solid #1e40af !important;
}

/* Botões do Sistema - Azul Corporativo Limpo */
.stButton > button {
    background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%) !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 10px 0px !important;
    border: none !important;
    box-shadow: 0 4px 10px rgba(30, 64, 175, 0.15) !important;
    width: 100%;
    transition: all 0.2s ease;
}

/* Painel de Lançamentos Internos - Cards Claros Clean */
.card-despesa { 
    background: #ffffff; 
    padding: 20px; 
    border-radius: 10px; 
    border: 1px solid #e2e8f0; 
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    margin-bottom: 15px; 
}
.card-despesa span, .card-despesa div, .card-despesa b { color: #1e293b !important; }

/* Logs de Auditoria */
.card-log { 
    background: #ffffff; 
    padding: 12px 20px; 
    border-radius: 8px; 
    border-left: 4px solid #3b82f6; 
    border-top: 1px solid #e2e8f0;
    border-right: 1px solid #e2e8f0;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 8px; 
    display: flex; 
    justify-content: space-between; 
}

/* Barra Lateral (Sidebar) Clara */
section[data-testid="stSidebar"] { 
    background-color: #ffffff !important; 
    border-right: 1px solid #e2e8f0; 
}
.user-box { 
    background: #f8fafc; 
    padding: 16px; 
    border-radius: 10px; 
    border: 1px solid #e2e8f0; 
    margin-top: 15px; 
}
</style>
""", unsafe_allow_html=True)

if "logado" not in st.session_state: st.session_state["logado"] = False

# LINK DIRETO DA LOGO OFICIAL UPADO NA WEB PARA EVITAR ERRO DE CAMINHO
URL_LOGO_OFICIAL = "https://i.imgur.com/GscTBeS.jpg"

# ==============================================================================
# INTERFACE DE LOGIN CLASSIC CLEAN LIGHT
# ==============================================================================
if not st.session_state["logado"]:
    _, col_central, _ = st.columns([1, 1.3, 1])
    
    with col_central:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Carrega a logo direto do servidor de imagem estável
        st.image(URL_LOGO_OFICIAL, width=220)
            
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
# PAINEL INTERNO PÓS-LOGIN (LIGHT CLEAN)
# ==============================================================================
st.sidebar.image(URL_LOGO_OFICIAL, use_container_width=True)

st.sidebar.markdown(f"""
<div class="user-box">
    <span style="color: #1e40af; font-size: 11px; font-weight: 600;">OPERADOR ATIVO</span>
    <div style="color: #0f172a; font-weight: 700; font-size: 15px;">{st.session_state.get('nome_completo')}</div>
    <span style="background: rgba(30,64,175,0.1); color: #1e40af; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; display: inline-block; margin-top: 6px;">💼 {st.session_state.get('perfil').upper()}</span>
</div>""", unsafe_allow_html=True)

st.sidebar.markdown("<br>", unsafe_allow_html=True)
menu = st.sidebar.radio("Navegação", ["📊 Painel Geral", "💸 Lançar Despesa", "📋 Relatório de Despesas", "📜 Auditório (Logs)"])

st.sidebar.markdown("<br><hr style='border-color:#e2e8f0;'><br>", unsafe_allow_html=True)
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
        kpi1.markdown(f'<div style="background:#ffffff; padding:22px; border-radius:10px; border-left: 5px solid #2563eb; box-shadow: 0 2px 4px rgba(0,0,0,0.02);"><span style="color:#64748b; font-size:13px; font-weight:600;">VALOR FILTRADO</span><h2 style="margin:5px 0 0 0; font-weight:700; color:#0f172a;">R$ {df_filtrado["valor"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
        kpi2.markdown(f'<div style="background:#ffffff; padding:22px; border-radius:10px; border-left: 5px solid #16a34a; box-shadow: 0 2px 4px rgba(0,0,0,0.02);"><span style="color:#16a34a; font-size:13px; font-weight:600;">TOTAL PAGO</span><h2 style="margin:5px 0 0 0; color:#16a34a; font-weight:700;">R$ {df_filtrado[df_filtrado["status"] == "PAGO"]["valor"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
        kpi3.markdown(f'<div style="background:#ffffff; padding:22px; border-radius:10px; border-left: 5px solid #eab308; box-shadow: 0 2px 4px rgba(0,0,0,0.02);"><span style="color:#eab308; font-size:13px; font-weight:600;">TOTAL PENDENTE</span><h2 style="margin:5px 0 0 0; color:#eab308; font-weight:700;">R$ {df_filtrado[df_filtrado["status"] == "PENDENTE"]["valor"].sum():,.2f}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            fig_p = px.pie(df_filtrado, names="categoria", values="valor", hole=0.4, title="Gastos por Categoria")
            fig_p.update_layout(template="plotly_white")
            st.plotly_chart(fig_p, use_container_width=True)
        with g2:
            df_centro = df_filtrado.groupby("centro_custo")["valor"].sum().reset_index()
            fig_b = px.bar(df_centro, x="centro_custo", y="valor", title="Investimento por Centro de Custo")
            fig_b.update_layout(template="plotly_white")
            st.plotly_chart(fig_b, use_container_width=True)
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
                    <span style="font-size:16px; font-weight:700; color:#0f172a;">{row['descricao']}</span>
                    <span style="background:{cor_status}; color:white; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600;">{row['status']}</span>
                </div>
                <div style="margin-top:10px; font-size:18px; font-weight:700; color:#1e40af;">R$ {row['valor']:.2f}</div>
            </div>""", unsafe_allow_html=True)

# 📜 AUDITORIA (LOGS)
elif menu == "📜 Auditório (Logs)":
    st.markdown('<div class="titulo-painel">📜 Trilha de Auditoria e Segurança</div>', unsafe_allow_html=True)
    if st.session_state["perfil"] in ["admin", "financeiro"]:
        df_logs = pd.read_sql("SELECT * FROM logs ORDER BY id DESC LIMIT 50", conn)
        if df_logs.empty: st.info("Sem atividades.")
        else:
            for _, log in df_logs.iterrows():
                st.markdown(f'<div class="card-log"><div><span style="font-weight:600; color:#1e40af;">{log["usuario"]}</span><span style="color:#334155; margin-left:8px;">{log["acao"]}</span></div><div style="color:#64748b; font-size:12px;">⏱️ {log["data_hora"]}</div></div>', unsafe_allow_html=True)