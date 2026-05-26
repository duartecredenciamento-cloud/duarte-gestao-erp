import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
import os
import time
from datetime import datetime
import plotly.express as px
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# CONFIGURAÇÃO DA PÁGINA (Deve ser a PRIMEIRA instrução Streamlit do script)
st.set_page_config(
    page_title="Duarte | Gestão Inteligente",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carrega variáveis de ambiente
load_dotenv()
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_EMAIL = os.getenv("SENHA_EMAIL")

# Cria diretório de uploads se não existir
os.makedirs("uploads", exist_ok=True)

# Inicialização estável do banco de dados
conn = sqlite3.connect("duarte.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        usuario TEXT UNIQUE,
        email TEXT,
        telefone TEXT,
        cpf TEXT,
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

init_db()

# Criptografia de senhas
def hash_senha(senha):
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

def verificar_senha(senha, senha_hash):
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())

def criar_usuarios_padrao():
    usuarios = [
        ("Administrador", "admin", "admin@duartegestao.com.br", "11999999999", "00000000000", "1234", "admin"),
        ("Financeiro", "financeiro", "financeiro@duartegestao.com.br", "11999999999", "00000000000", "1234", "financeiro")
    ]
    for nome, usuario, email, telefone, cpf, senha, perfil in usuarios:
        senha_hash = hash_senha(senha)
        try:
            cursor.execute("""
            INSERT INTO usuarios (nome, usuario, email, telefone, cpf, senha, perfil)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nome, usuario, email, telefone, cpf, senha_hash, perfil))
        except sqlite3.IntegrityError:
            pass
    conn.commit()

criar_usuarios_padrao()

def registrar_log(usuario, acao):
    cursor.execute("""
    INSERT INTO logs (usuario, acao, data_hora)
    VALUES (?, ?, ?)
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

# INTERFACE VISUAL (Header)
col1, col2 = st.columns([1, 5])
with col1:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=120)
    else:
        st.markdown("<h1 style='margin:0;'>🏢</h1>", unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="padding-top:10px;">
        <h1 style="margin:0; color:#e5e7eb;">Duarte Gestão ERP</h1>
        <p style="margin:0; color:#94a3b8;">Sistema inteligente para gestão empresarial</p>
    </div>
    """, unsafe_allow_html=True)

# Estilo SaaS Premium CSS
st.markdown("""
<style>
.stApp { background: radial-gradient(circle at top, #0f172a, #0b1220); color: #e5e7eb; font-family: 'Inter', sans-serif; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
h1, h2, h3, p, label { color: #e5e7eb !important; }
.stTextInput input { background: #111827 !important; color: white !important; border-radius: 12px !important; border: 1px solid #334155 !important; padding: 12px !important; }
.stButton > button { background: linear-gradient(135deg, #6366f1, #4f46e5); color: white; border-radius: 12px; font-weight: 700; padding: 12px; border: none; }
.stButton > button:hover { transform: scale(1.02); }
.card { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 10px; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0b1220, #111827); }
</style>
""", unsafe_allow_html=True)

# SISTEMA DE AUTENTICAÇÃO
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    abas = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
    
    with abas[0]:
        st.subheader("🔐 Entrar")
        usuario_input = st.text_input("Usuário", key="login_usuario")
        senha_input = st.text_input("Senha", type="password", key="login_senha")
        
        if st.button("Entrar", key="btn_login"):
            cursor.execute("SELECT * FROM usuarios WHERE usuario=?", (usuario_input,))
            user = cursor.fetchone()
            
            if user and verificar_senha(senha_input, user[6]):
                st.session_state["logado"] = True
                st.session_state["usuario"] = user[2]  # Guarda o 'usuario' (username) para os filtros de banco
                st.session_state["nome_completo"] = user[1]
                st.session_state["perfil"] = user[7]
                st.success("✅ Login realizado!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos")
                
    with abas[1]:
        st.subheader("📝 Criar Conta")
        nome = st.text_input("Nome Completo", key="cad_nome")
        usuario_novo = st.text_input("Usuário", key="cad_usuario")
        email = st.text_input("E-mail", key="cad_email")
        telefone = st.text_input("Telefone", key="cad_telefone")
        cpf = st.text_input("CPF", key="cad_cpf")
        senha_nova = st.text_input("Senha", type="password", key="cad_senha")
        
        if st.button("Criar Conta", key="btn_criar"):
            if nome and usuario_novo and senha_nova:
                senha_hash = hash_senha(senha_nova)
                try:
                    cursor.execute("""
                    INSERT INTO usuarios (nome, usuario, email, telefone, cpf, senha, perfil)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (nome, usuario_novo, email, telefone, cpf, senha_hash, "usuario"))
                    conn.commit()
                    st.success("✅ Conta criada com sucesso! Mude para a aba de login.")
                except sqlite3.IntegrityError:
                    st.error("❌ Usuário já existe.")
            else:
                st.warning("⚠️ Preencha os campos obrigatórios (Nome, Usuário e Senha).")
    st.stop()

# =========================================
# INTERFACE LOGADA
# =========================================
st.sidebar.markdown(f"Olá, **{st.session_state.get('nome_completo')}** 💼")
menu = st.sidebar.radio(
    "Menu",
    ["📊 Dashboard", "💸 Nova Despesa", "📋 Minhas Despesas", "📜 Logs"]
)

if st.sidebar.button("🚪 Sair"):
    st.session_state["logado"] = False
    st.clear()
    st.rerun()

# 📊 DASHBOARD
if menu == "📊 Dashboard":
    st.title("📊 Dashboard Executivo")
    
    # Se for admin/financeiro vê tudo, senão vê só o dele
    if st.session_state["perfil"] in ["admin", "financeiro"]:
        df = pd.read_sql("SELECT * FROM despesas", conn)
    else:
        df = pd.read_sql("SELECT * FROM despesas WHERE usuario=?", conn, params=(st.session_state["usuario"],))
        
    total = df["valor"].sum() if not df.empty else 0
    qtd = len(df)
    
    col1, col2 = st.columns(2)
    col1.metric("💰 Total em Despesas", f"R$ {total:,.2f}")
    col2.metric("📦 Quantidade de Registros", qtd)
    
    if not df.empty:
        fig = px.pie(df, names="categoria", values="valor", hole=0.4, title="Despesas por Categoria")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado lançado para exibir no gráfico.")

# 💸 NOVA DESPESA
elif menu == "💸 Nova Despesa":
    st.title("💸 Solicitar Reembolso / Nova Despesa")
    
    categorias = ["Alimentação", "Transporte", "Software e Licenças", "Material Escritório", "Marketing", "Outros"]
    centros = ["FINANCEIRO", "CREDENCIAMENTO", "REDE", "MARKETING", "DIRETORIA"]
    
    descricao = st.text_input("Descrição do Gasto")
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
    categoria = st.selectbox("Categoria", categorias)
    centro = st.selectbox("Centro de Custo", centros)
    arquivo = st.file_uploader("Anexar comprovante (Imagem/PDF)")
    
    if st.button("Salvar Despesa"):
        if not descricao or valor <= 0:
            st.error("Por favor, informe uma descrição e um valor válido.")
        else:
            caminho_arquivo = ""
            if arquivo:
                nome_arquivo = f"{datetime.now().timestamp()}_{arquivo.name}"
                caminho_arquivo = os.path.join("uploads", nome_arquivo)
                with open(caminho_arquivo, "wb") as f:
                    f.write(arquivo.read())
            
            cursor.execute("""
            INSERT INTO despesas (usuario, descricao, categoria, centro_custo, valor, arquivo, status, data)
            VALUES (?, ?, ?, ?, ?, ?, 'PENDENTE', ?)
            """, (st.session_state["usuario"], descricao, categoria, centro, valor, caminho_arquivo, datetime.now().strftime("%d/%m/%Y")))
            conn.commit()
            
            registrar_log(st.session_state["usuario"], f"Cadastrou despesa: {descricao} (R$ {valor})")
            st.success("✅ Despesa cadastrada com sucesso!")
            st.balloons()

# 📋 MINHAS DESPESAS & GESTÃO
elif menu == "📋 Minhas Despesas":
    st.title("📋 Painel de Despesas e Aprovações")
    
    # Controle de visualização de acordo com nível de acesso
    if st.session_state["perfil"] in ["admin", "financeiro"]:
        st.markdown("💡 *Modo Gestor: Exibindo todas as despesas abertas no sistema.*")
        df = pd.read_sql("SELECT * FROM despesas ORDER BY id DESC", conn)
    else:
        df = pd.read_sql("SELECT * FROM despesas WHERE usuario=? ORDER BY id DESC", conn, params=(st.session_state["usuario"],))
        
    if df.empty:
        st.warning("Nenhuma despesa encontrada.")
    else:
        for _, row in df.iterrows():
            st.markdown(f"""
            <div class="card">
                <b>Funcionário:</b> {row['usuario']} | <b>Descrição:</b> {row['descricao']}<br>
                💰 <b>R$ {row['valor']:.2f}</b> | 📂 Categoria: {row['categoria']} | 🏢 Centro: {row['centro_custo']}<br>
                📅 Data: {row['data']} | 📊 Status: <b>{row['status']}</b>
            </div>
            """, unsafe_allow_html=True)
            
            # Só exibe os botões de ação se o usuário atual for Admin ou Financeiro e o registro estiver pendente
            if st.session_state["perfil"] in ["admin", "financeiro"] and row['status'] == 'PENDENTE':
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("✅ Aprovar", key=f"ap_{row['id']}"):
                        cursor.execute("UPDATE despesas SET status='APROVADO' WHERE id=?", (row["id"],))
                        conn.commit()
                        registrar_log(st.session_state["usuario"], f"Aprovou despesa ID {row['id']}")
                        st.success("Aprovado!")
                        st.rerun()
                        
                with col2:
                    if st.button("❌ Rejeitar", key=f"rej_{row['id']}"):
                        cursor.execute("UPDATE despesas SET status='REJEITADO' WHERE id=?", (row["id"],))
                        conn.commit()
                        registrar_log(st.session_state["usuario"], f"Rejeitou despesa ID {row['id']}")
                        st.warning("Rejeitado!")
                        st.rerun()
                        
                with col3:
                    if st.button("💰 Confirmar Pagamento", key=f"pg_{row['id']}"):
                        cursor.execute("UPDATE despesas SET status='PAGO' WHERE id=?", (row["id"],))
                        conn.commit()
                        registrar_log(st.session_state["usuario"], f"Marcou como PAGO despesa ID {row['id']}")
                        
                        # Tenta buscar e-mail do dono da despesa para notificar
                        cursor.execute("SELECT email FROM usuarios WHERE usuario=?", (row['usuario'],))
                        user_email = cursor.fetchone()
                        if user_email and user_email[0]:
                            enviar_email(user_email[0], row['descricao'], row['valor'])
                            
                        st.success("Pago e Notificado!")
                        st.rerun()
            st.markdown("---")

# 📜 LOGS
elif menu == "📜 Logs":
    st.title("📜 Auditoria de Logs do Sistema")
    if st.session_state["perfil"] in ["admin", "financeiro"]:
        df_logs = pd.read_sql("SELECT * FROM logs ORDER BY id DESC LIMIT 100", conn)
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.error("Apenas administradores podem auditar os logs do sistema.")