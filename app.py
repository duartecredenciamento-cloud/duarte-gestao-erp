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
    for nome, usuario, email, telefone, cpf, senha, perfil in usuarios:
        try:
            cursor.execute(f"SELECT id, senha FROM usuarios WHERE usuario={p}", (usuario,))
            registro = cursor.fetchone()
        except Exception as e:
            if DATABASE_URL: conn.rollback()
            print(f"Erro ao buscar usuario {usuario}: {e}")
            registro = None

        if not registro:
            senha_hash = hash_senha(senha)
            try:
                cursor.execute(f"INSERT INTO usuarios (nome, usuario, email, telefone, cpf, senha, perfil) VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p})",
                               (nome, usuario, email, telefone, cpf, senha_hash, perfil))
                conn.commit()
            except Exception as e:
                if DATABASE_URL: conn.rollback()
                print(f"Erro crítico ao inserir usuario {usuario}: {e}")
        else:
            try:
                if not verificar_senha(SENHA_FORTE_PADRAO, registro[1]):
                    nova_senha_hash = hash_senha(SENHA_FORTE_PADRAO)
                    cursor.execute(f"UPDATE usuarios SET senha={p} WHERE usuario={p}", (nova_senha_hash, usuario))
                    conn.commit()
            except Exception as e:
                if DATABASE_URL: conn.rollback()
                print(f"Erro ao atualizar senha de {usuario}: {e}")
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
/* Fundo Dark Tech Premium com malha digital discreta */
.stApp {
    background: radial-gradient(circle at center, #0b2230 0%, #051017 100%) !important;
    background-image:
        radial-gradient(circle at 10% 20%, rgba(0, 242, 254, 0.08) 0%, transparent 50%),
        radial-gradient(circle at 90% 80%, rgba(79, 172, 254, 0.08) 0%, transparent 50%),
        url('https://www.transparenttextures.com/patterns/subtle-net.png') !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif;
}

footer {visibility: hidden;}

/* Container Unificado de Login (Fundo Branco Opaco Anti-Vazamento) */
.login-master-card {
    background-color: #ffffff !important;
    border-radius: 18px !important;
    padding: 0px 0px 40px 0px !important;
    box-shadow: 0px 15px 35px rgba(0, 0, 0, 0.4) !important;
    margin: 40px auto !important;
    max-width: 540px !important;
    overflow: hidden !important;
    border: 1px solid rgba(0, 0, 0, 0.05) !important;
}

/* Header Integrado com Borda Iluminada Neon */
.brand-glow-header {
    background: linear-gradient(135deg, #091e2b 0%, #05121a 100%) !important;
    padding: 35px 20px !important;
    border-bottom: 4px solid #00f2fe !important;
    box-shadow: 0px 4px 20px rgba(0, 242, 254, 0.25) !important;
    text-align: center !important;
}

/* Ajuste das fontes internas do Header */
.brand-glow-header h2 {
    color: #ffffff !important;
    font-weight: 800 !important;
    font-size: 30px !important;
    margin: 12px 0 2px 0 !important;
    letter-spacing: -0.5px !important;
}
.brand-glow-header p {
    color: #00f2fe !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    margin: 0 !important;
}

/* Envoltório do formulário para dar espaçamento interno */
.form-body-wrapper {
    padding: 0px 40px !important;
}

/* Labels das caixas de entrada em tom escuro elegante */
.form-body-wrapper label {
    color: #1e293b !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}

/* Inputs Premium: Fundo branco e texto escuro para leitura perfeita */
.stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
    background-color: #f8fafc !important;
    color: #0f172a !important;
    border-radius: 8px !important;
    border: 1px solid #cbd5e1 !important;
    padding: 10px !important;
    font-weight: 500 !important;
}
.stTextInput input:focus {
    border-color: #00f2fe !important;
    box-shadow: 0 0 8px rgba(0, 242, 254, 0.3) !important;
}

/* Customização Absoluta das Abas do Streamlit */
div[data-testid="stTabBar"] {
    background-color: #ffffff !important;
    padding: 10px 40px 0px 40px !important;
}
div[data-testid="stTabBar"] button {
    color: #64748b !important;
    font-weight: 500 !important;
}
div[data-testid="stTabBar"] button[aria-selected="true"] {
    color: #00f2fe !important;
    font-weight: 700 !important;
    border-bottom: 3px solid #00f2fe !important;
}

/* Botão Corporativo com o Brilho Certo */
.stButton > button {
    background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%) !important;
    color: #051017 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 12px 0px !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(0, 242, 254, 0.35) !important;
    width: 100%;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    box-shadow: 0 6px 22px rgba(0, 242, 254, 0.6) !important;
    transform: translateY(-1px);
}

/* Painéis de Pós-Login */
.card-despesa { background: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); color: #1e293b; }
.card-despesa span, .card-despesa div { color: #1e293b !important; }
.card-log { background: rgba(255,255,255,0.05); padding: 12px 20px; border-radius: 8px; border-left: 4px solid #00f2fe; margin-bottom: 8px; display: flex; justify-content: space-between; }
section[data-testid="stSidebar"] { background-color: #06151f !important; border-right: 1px solid rgba(0,242,254,0.1); }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label { color: #ffffff !important; }
.user-box { background: rgba(255,255,255,0.03); padding: 16px; border-radius: 10px; border: 1px solid rgba(0,242,254,0.1); margin-bottom: 25px; }
</style>
""", unsafe_allow_html=True)

if "logado" not in st.session_state: st.session_state["logado"] = False

# ==============================================================================
# INTERFACE DE LOGIN UNIFICADA
# ==============================================================================
if not st.session_state["logado"]:
    _, col_central, _ = st.columns([1, 1.8, 1])

    with col_central:
        # Abertura do Card Geral Mestre
        st.markdown('<div class="login-master-card">', unsafe_allow_html=True)

        # Bloco de Marca Injetado (Logo Expandida + Cabeçalho Neon)
        st.markdown("""
        <div class="brand-glow-header">
            <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 5px;">
                <div style="background-color: #0b2230; padding: 14px 28px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.15); box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
                    <span style="color: #ffffff; font-weight: 800; font-size: 24px; letter-spacing: -0.5px;">Duarte</span>
                    <span style="color: #eab308; font-weight: 900; font-size: 24px; margin-left: -2px;">•</span>
                </div>
            </div>
            <h2>Duarte Gestão ERP</h2>
            <p>Plataforma Corporativa de Controle Financeiro</p>
        </div>
        """, unsafe_allow_html=True)

        # Início das Abas com tratamento interno
        abas = st.tabs(["🔐 Acessar Sistema", "📝 Cadastrar Colaborador"])

        with abas[0]:
            st.markdown('<div class="form-body-wrapper"><br>', unsafe_allow_html=True)
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
            st.markdown('</div>', unsafe_allow_html=True)

        with abas[1]:
            st.markdown('<div class="form-body-wrapper"><br>', unsafe_allow_html=True)
            nome = st.text_input("Nome Completo", key="cad_nome")
            usuario_novo = st.text_input("Nome de Usuário", key="cad_usuario")
            email = st.text_input("E-mail Corporativo", key="cad_email")
            telefone = st.text_input("Telefone (Apenas números)", key="cad_telefone")
            cpf = st.text_input("CPF (Apenas numbers)", key="cad_cpf")
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

        # Fechamento do Card Mestre
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# PAINEL INTERNO PÓS-LOGIN
# ==============================================================================
st.sidebar.markdown(f"""
<div class="user-box">
    <span style="color: #00f2fe; font-size: 11px; font-weight: 600;">OPERADOR ATIVO</span>
    <div style="color: #ffffff; font-weight: 700; font-size: 15px;">{st.session_state.get('nome_completo')}</div>
    <span style="background: rgba(0,242,254,0.1); color: #00f2fe; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; display: inline-block; margin-top: 6px;">💼 {st.session_state.get('perfil').upper()}</span>
</div>""", unsafe_allow_html=True)

menu = st.sidebar.radio("Navegação", ["📊 Dashboard Geral", "💸 Lançar Despesa", "📋 Relatório de Despesas", "📜 Auditoria (Logs)"])

st.sidebar.markdown("<br><hr style='border-color: rgba(255,255,255,0.1);'><br>", unsafe_allow_html=True)
with st.sidebar.expander("📖 Guia Operacional (Assistente)"):
    st.markdown("""
    **Como operar o ERP Duarte:**
    1. **Auditar:** Vá em *Relatório de Despesas*.
    2. **Validar Anexo:** Clique em *Visualizar Comprovante*.
    3. **Baixar p/ o Drive:** Clique no botão azul *Baixar Arquivo para o Drive*.
    4. **Mudar Status:** Aprove, Rejeite ou Pague.
    5. **Fechamento:** Baixe a planilha Excel no Dashboard.
    """)

if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True):
    st.session_state["logado"] = False
    st.clear()
    st.rerun()

# 📊 DASHBOARD
if menu == "📊 Dashboard Geral":
    st.title("📊 BI - Painel de Inteligência Financeira")
    df_base = pd.read_sql("SELECT * FROM despesas", conn) if st.session_state["perfil"] in ["admin", "financeiro"] else pd.read_sql(f"SELECT * FROM despesas WHERE usuario='{st.session_state['usuario']}'", conn)

    if not df_base.empty:
        df_base['date_parsed'] = pd.to_datetime(df_base['data'], format='%d/%m/%Y', errors='coerce')
        df_base['Mes_Ano'] = df_base['date_parsed'].dt.strftime('%m/%Y').fillna("Sem Data")

        st.markdown("<h3 style='font-size:16px; font-weight:600; color:#00f2fe;'>🎯 Segmentadores de Dados</h3>", unsafe_allow_html=True)
        f1, f2, f3 = st.columns(3)
        with f1: filtro_mes = st.selectbox("Filtrar por Mês/Ano", ["Todos"] + sorted(list(df_base['Mes_Ano'].unique())))
        with f2: filtro_centro = st.selectbox("Filtrar por Centro de Custo", ["Todos"] + sorted(list(df_base['centro_custo'].unique())))
        with f3: filtro_status = st.selectbox("Filtrar por Status", ["Todos", "PENDENTE", "APROVADO", "PAGO", "REJEITADO"])

        df_filtrado = df_base.copy()
        if filtro_mes != "Todos": df_filtrado = df_filtrado[df_filtrado['Mes_Ano'] == filtro_mes]
        if filtro_centro != "Todos": df_filtrado = df_filtrado[df_filtrado['centro_custo'] == filtro_centro]
        if filtro_status != "Todos": df_filtrado = df_filtrado[df_filtrado['status'] == filtro_status]

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.markdown(f'<div style="background:#ffffff; padding:22px; border-radius:10px; border-left: 5px solid #2563eb;"><span style="color:#64748b; font-size:13px; font-weight:600;">VALOR FILTRADO</span><h2 style="margin:5px 0 0 0; font-weight:700; color:#1e293b;">R$ {df_filtrado["valor"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
        kpi2.markdown(f'<div style="background:#ffffff; padding:22px; border-radius:10px; border-left: 5px solid #16a34a;"><span style="color:#16a34a; font-size:13px; font-weight:600;">TOTAL PAGO</span><h2 style="margin:5px 0 0 0; color:#16a34a; font-weight:700;">R$ {df_filtrado[df_filtrado["status"] == "PAGO"]["valor"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
        kpi3.markdown(f'<div style="background:#ffffff; padding:22px; border-radius:10px; border-left: 5px solid #eab308;"><span style="color:#eab308; font-size:13px; font-weight:600;">TOTAL PENDENTE</span><h2 style="margin:5px 0 0 0; color:#eab308; font-weight:700;">R$ {df_filtrado[df_filtrado["status"] == "PENDENTE"]["valor"].sum():,.2f}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_filtrado.drop(columns=['date_parsed'], errors='ignore').to_excel(writer, index=False, sheet_name='Despesas')
        st.download_button(label="📊 Exportar Dados Atuais para o Excel (Planilha)", data=buffer.getvalue(), file_name="relatorio_duarte.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(px.pie(df_filtrado, names="categoria", values="valor", hole=0.4, title="Gastos por Categoria"), use_container_width=True)
        with g2:
            df_centro = df_filtrado.groupby("centro_custo")["valor"].sum().reset_index()
            st.plotly_chart(px.bar(df_centro, x="centro_custo", y="valor", title="Investimento por Centro de Custo", text_auto='.2s'), use_container_width=True)
    else: st.info("Nenhum dado encontrado.")

# 💸 LANÇAR DESPESA
elif menu == "💸 Lançar Despesa":
    st.title("💸 Nova Solicitação de Reembolso")
    col_form, _ = st.columns([2, 1])
    with col_form:
        descricao = st.text_input("Descrição Clara do Gasto")
        valor = st.number_input("Valor da Despesa (R$)", min_value=0.0, step=0.01)
        c1, c2 = st.columns(2)
        categoria = c1.selectbox("Categoria", ["Alimentação", "Transporte", "Software e Licenças", "Material Escritório", "Marketing", "Outros"])
        centro = c2.selectbox("Centro de Custo", ["FINANCEIRO", "CREDENCIAMENTO", "REDE", "MARKETING", "DIRETORIA"])
        arquivo = st.file_uploader("Anexar Comprovante Fiscal (Imagem/PDF) *OBRIGATÓRIO*", type=['png', 'jpg', 'jpeg', 'pdf'])

        if st.button("Enviar para Aprovação"):
            if not descricao or valor <= 0:
                st.error("❌ Preencha a descrição e um valor válido.")
            elif not arquivo:
                st.error("❌ Governança Duarte: É obrigatório anexar o comprovante fiscal para solicitar reembolso.")
            else:
                url_arquivo_nuvem = ""
                with st.spinner("Enviando comprovante para a nuvem segura..."):
                    try:
                        upload_result = cloudinary.uploader.upload(arquivo, folder="comprovantes_duarte")
                        url_arquivo_nuvem = upload_result.get("secure_url")
                    except Exception as e:
                        st.error(f"Erro no upload: {e}"); st.stop()

                cursor.execute(f"INSERT INTO despesas (usuario, descricao, categoria, centro_custo, valor, arquivo, status, data) VALUES ({p}, {p}, {p}, {p}, {p}, {p}, 'PENDENTE', {p})",
                               (st.session_state["usuario"], descricao, categoria, centro, valor, url_arquivo_nuvem, datetime.now().strftime("%d/%m/%Y")))
                conn.commit()
                registrar_log(st.session_state["usuario"], f"Solicitou Reembolso: {descricao} (R$ {valor:.2f})")

                st.success("✅ Solicitação enviada! Comprovante salvo e Financeiro avisado.")
                time.sleep(0.5); st.rerun()

# 📋 RELATÓRIO DE DESPESAS
elif menu == "📋 Relatório de Despesas":
    st.title("📋 Painel de Prestação de Contas")
    df = pd.read_sql("SELECT * FROM despesas ORDER BY id DESC", conn) if st.session_state["perfil"] in ["admin", "financeiro"] else pd.read_sql(f"SELECT * FROM despesas WHERE usuario='{st.session_state['usuario']}' ORDER BY id DESC", conn)

    if df.empty: st.warning("Nenhum lançamento registrado.")
    else:
        for _, row in df.iterrows():
            cor_status = "#eab308" if row['status'] == "PENDENTE" else "#16a34a" if row['status'] in ["APROVADO", "PAGO"] else "#dc2626"
            link_visualizar = f'<a href="{row["arquivo"]}" target="_blank" style="background:#f1f5f9; color:#2563eb; padding:6px 12px; border-radius:6px; font-size:13px; font-weight:600; text-decoration:none; border:1px solid #cbd5e1; margin-right: 10px;"><b>📄 Visualizar Comprovante</b></a>' if row['arquivo'] else ""

            st.markdown(f"""
            <div class="card-despesa">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:18px; font-weight:700;">{row['descricao']}</span>
                    <span style="background:{cor_status}; color:white; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600;">{row['status']}</span>
                </div>
                <div style="margin-top:10px; color:#475569; font-size:14px;">Colaborador: <b>{row['usuario']}</b> | Centro: <b>{row['centro_custo']}</b> | Data: {row['data']}</div>
                <div style="margin-top:10px; font-size:20px; font-weight:700; color:#2563eb;">R$ {row['valor']:.2f}</div>
                <div style="margin-top:15px; display: flex; align-items: center;">{link_visualizar}</div>
            </div>""", unsafe_allow_html=True)

            if st.session_state["perfil"] in ["admin", "financeiro"] and row['status'] == 'PENDENTE':
                col1, col2, col3, _ = st.columns([1, 1, 1, 3])
                if col1.button("✅ Aprovar", key=f"ap_{row['id']}"):
                    cursor.execute(f"UPDATE despesas SET status='APROVADO' WHERE id={p}", (row["id"],)); conn.commit()
                    registrar_log(st.session_state["usuario"], f"Aprovou despesa ID {row['id']}")
                    st.rerun()
                if col2.button("❌ Rejeitar", key=f"rej_{row['id']}"):
                    cursor.execute(f"UPDATE despesas SET status='REJEITADO' WHERE id={p}", (row["id"],)); conn.commit()
                    registrar_log(st.session_state["usuario"], f"Rejeitou despesa ID {row['id']}")
                    st.rerun()
                if col3.button("💰 Pagar", key=f"pg_{row['id']}"):
                    cursor.execute(f"UPDATE despesas SET status='PAGO' WHERE id={p}", (row["id"],)); conn.commit()
                    registrar_log(st.session_state["usuario"], f"Pagou despesa ID {row['id']}")
                    st.rerun()

# 📜 LOGS
elif menu == "📜 Auditoria (Logs)":
    st.title("📜 Trilha de Auditoria e Segurança")
    if st.session_state["perfil"] in ["admin", "financeiro"]:
        df_logs = pd.read_sql("SELECT * FROM logs ORDER BY id DESC LIMIT 50", conn)
        if df_logs.empty: st.info("Sem atividades.")
        else:
            for _, log in df_logs.iterrows():
                st.markdown(f'<div class="card-log"><div><span style="font-weight:600; color:#00f2fe;">{log["usuario"]}</span><span style="color:#ffffff; margin-left:8px;">{log["acao"]}</span></div><div style="color:#94a3b8; font-size:12px;">⏱️ {log["data_hora"]}</div></div>', unsafe_allow_html=True)
    else: st.error("🔒 Restrito.")