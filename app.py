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
DATABASE_URL = os.getenv("DATABASE_URL")  

# CONFIGURAÇÃO DO CLOUDINARY
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

os.makedirs("uploads", exist_ok=True)

# 🔌 FUNÇÃO DE CONEXÃO INTELIGENTE
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
                        """, (nome, usuario_novo, email, telephone, cpf, senha_hash))
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

# 📊 DASHBOARD (ETAPA 2: ESTILO POWER BI)
if menu == "📊 Dashboard Geral":
    st.title("📊 BI - Painel de Inteligência Financeira")
    
    # 1. CARGA DE DADOS COM TRAVA DE ACESSO CRÍTICO
    if st.session_state["perfil"] in ["admin", "financeiro"]:
        df_base = pd.read_sql("SELECT * FROM despesas", conn)
    else:
        if DATABASE_URL:
            df_base = pd.read_sql("SELECT * FROM despesas WHERE usuario=%s", conn, params=(st.session_state["usuario"],))
        else:
            df_base = pd.read_sql("SELECT * FROM despesas WHERE usuario=?", conn, params=(st.session_state["usuario"],))

    if not df_base.empty:
        # Tratamento das datas para extrair o Mês/Ano para os filtros
        df_base['date_parsed'] = pd.to_datetime(df_base['data'], format='%d/%m/%Y', errors='coerce')
        df_base['Mes_Ano'] = df_base['date_parsed'].dt.strftime('%m/%Y')
        df_base['Mes_Ano'] = df_base['Mes_Ano'].fillna("Sem Data")

        # 2. SEÇÃO DE FILTROS (ESTILO SEGMENTAÇÃO DE DADOS POWER BI)
        st.markdown("<h3 style='font-size:16px; font-weight:600; color:#475569;'>🎯 Segmentadores de Dados</h3>", unsafe_allow_html=True)
        f1, f2, f3 = st.columns(3)
        
        with f1:
            lista_meses = ["Todos"] + sorted(list(df_base['Mes_Ano'].unique()))
            filtro_mes = st.selectbox("Filtrar por Mês/Ano", lista_meses)
        with f2:
            lista_centros = ["Todos"] + sorted(list(df_base['centro_custo'].unique()))
            filtro_centro = st.selectbox("Filtrar por Centro de Custo", lista_centros)
        with f3:
            lista_status = ["Todos", "PENDENTE", "APROVADO", "PAGO", "REJEITADO"]
            filtro_status = st.selectbox("Filtrar por Status", lista_status)

        # Aplicando as escolhas dos filtros na tabela
        df_filtrado = df_base.copy()
        if filtro_mes != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Mes_Ano'] == filtro_mes]
        if filtro_centro != "Todos":
            df_filtrado = df_filtrado[df_filtrado['centro_custo'] == filtro_centro]
        if filtro_status != "Todos":
            df_filtrado = df_filtrado[df_filtrado['status'] == filtro_status]

        # 3. VALORES TOTAIS (CARDS DE KPI PREMIUM)
        total_lancado = df_filtrado["valor"].sum()
        total_pago = df_filtrado[df_filtrado["status"] == "PAGO"]["valor"].sum()
        total_pendente = df_filtrado[df_filtrado["status"] == "PENDENTE"]["valor"].sum()

        st.markdown("<br>", unsafe_allow_html=True)
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.markdown(f"""<div style="background:#ffffff; padding:22px; border-radius:10px; border:1px solid #e2e8f0; border-left: 5px solid #2563eb;"><span style="color:#64748b; font-size:13px; font-weight:600;">VALOR TOTAL FILTRADO</span><h2 style="margin:5px 0 0 0; color:#1e293b; font-weight:700;">R$ {total_lancado:,.2f}</h2></div>""", unsafe_allow_html=True)
        with kpi2:
            st.markdown(f"""<div style="background:#ffffff; padding:22px; border-radius:10px; border:1px solid #e2e8f0; border-left: 5px solid #16a34a;"><span style="color:#16a34a; font-size:13px; font-weight:600;">TOTAL EFETIVADO (PAGO)</span><h2 style="margin:5px 0 0 0; color:#16a34a; font-weight:700;">R$ {total_pago:,.2f}</h2></div>""", unsafe_allow_html=True)
        with kpi3:
            st.markdown(f"""<div style="background:#ffffff; padding:22px; border-radius:10px; border:1px solid #e2e8f0; border-left: 5px solid #eab308;"><span style="color:#eab308; font-size:13px; font-weight:600;">TOTAL EM ABERTO (PENDENTE)</span><h2 style="margin:5px 0 0 0; color:#eab308; font-weight:700;">R$ {total_pendente:,.2f}</h2></div>""", unsafe_allow_html=True)

        # 4. GRÁFICOS AVANÇADOS COMBINADOS
        st.markdown("<br><br>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        
        with g1:
            st.markdown("<h4 style='font-size:16px; font-weight:700; text-align:center;'>Gastos por Categoria</h4>", unsafe_allow_html=True)
            fig_pizza = px.pie(df_filtrado, names="categoria", values="valor", hole=0.4)
            fig_pizza.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#1e293b", margin=dict(t=20, b=20, l=10, r=10))
            st.plotly_chart(fig_pizza, use_container_width=True)
            
        with g2:
            st.markdown("<h4 style='font-size:16px; font-weight:700; text-align:center;'>Investimento por Centro de Custo</h4>", unsafe_allow_html=True)
            # Agrupa os valores para criar o gráfico de colunas corporativo
            df_centro = df_filtrado.groupby("centro_custo")["valor"].sum().reset_index()
            fig_barra = px.bar(df_centro, x="centro_custo", y="valor", labels={"valor": "Valor (R$)", "centro_custo": "Centro de Custo"}, text_auto='.2s')
            fig_barra.update_traces(marker_color='#2563eb', textposition='outside')
            fig_barra.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#1e293b", margin=dict(t=20, b=20, l=10, r=10))
            st.plotly_chart(fig_barra, use_container_width=True)
    else:
        st.info("Nenhuma transferência financeira encontrada para gerar os painéis do BI.")

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
                url_arquivo_nuvem = ""
                if arquivo:
                    with st.spinner("Enviando comprovante para a nuvem segura..."):
                        try:
                            upload_result = cloudinary.uploader.upload(arquivo, folder="comprovantes_duarte")
                            url_arquivo_nuvem = upload_result.get("secure_url")
                        except Exception as e:
                            st.error(f"Erro ao salvar arquivo na nuvem: {e}")
                            st.stop()
                
                cursor.execute(f"""
                INSERT INTO despesas (usuario, descricao, categoria, centro_custo, valor, arquivo, status, data)
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, 'PENDENTE', {p})
                """, (st.session_state["usuario"], descricao, categoria, centro, valor, url_arquivo_nuvem, datetime.now().strftime("%d/%m/%Y")))
                conn.commit()
                registrar_log(st.session_state["usuario"], f"Solicitou Reembolso: {descricao} (R$ {valor:.2f})")
                st.success("✅ Solicitação enviada com comprovante em nuvem!")
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
            
            link_visualizar = ""
            if row['arquivo']:
                link_visualizar = f'<a href="{row["arquivo"]}" target="_blank" style="background:#f1f5f9; color:#2563eb; padding:6px 12px; border-radius:6px; font-size:13px; font-weight:600; text-decoration:none; border:1px solid #cbd5e1; margin-right: 10px;"><b>📄 Visualizar Comprovante</b></a>'

            st.markdown(f"""
            <div class="card-despesa">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:18px; font-weight:700; color:#0f172a;">{row['descricao']}</span>
                    <span style="background:{cor_status}; color:white; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600;">{row['status']}</span>
                </div>
                <div style="margin-top:10px; color:#475569; font-size:14px;">Colaborador: <b>{row['usuario']}</b> | Categoria: <b>{row['categoria']}</b> | Centro: <b>{row['centro_custo']}</b> | Data: {row['data']}</div>
                <div style="margin-top:10px; font-size:20px; font-weight:700; color:#2563eb;">R$ {row['valor']:.2f}</div>
                <div style="margin-top:15px; display: flex; align-items: center;">
                    {link_visualizar}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if row['arquivo']:
                try:
                    extensao = ".pdf" if ".pdf" in row['arquivo'].lower() else ".png"
                    nome_baixar = f"comprovante_{row['id']}{extensao}"
                    response_file = requests.get(row['arquivo'])
                    st.download_button(
                        label="⬇️ Baixar Arquivo para o Drive",
                        data=response_file.content,
                        file_name=nome_baixar,
                        mime="application/pdf" if extensao == ".pdf" else "image/png",
                        key=f"dl_{row['id']}"
                    )
                except:
                    pass

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