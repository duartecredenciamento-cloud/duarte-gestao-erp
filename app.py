import streamlit as st
import pandas as pd
import sqlite3
import os
import smtplib
import io
import urllib.parse
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import re

# --- CONFIGURAÇÃO INICIAL DA PÁGINA ---
st.set_page_config(page_title="Duarte Gestão - Financeiro", layout="wide", initial_sidebar_state="expanded")

# --- INICIALIZAÇÃO SEGURA DO SESSION STATE ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "user_info" not in st.session_state:
    st.session_state["user_info"] = None
if "app_loaded" not in st.session_state:
    st.session_state["app_loaded"] = False

def verificar_email(email):
    padrao = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(padrao, email))

DB_PATH = os.environ.get("REEMBOLSO_DB_PATH", "reembolso.db")
COMPROVANTES_DIR = os.environ.get("REEMBOLSO_UPLOAD_DIR", "comprovantes")
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
os.makedirs(COMPROVANTES_DIR, exist_ok=True)

def resolver_caminho_comprovante(caminho):
    """Resolve referências legadas relativas para o diretório configurado de anexos."""
    if not caminho:
        return ""
    nome = os.path.basename(str(caminho).replace("\\", "/"))
    if nome in ("", ".", ".."):
        return ""
    return os.path.join(COMPROVANTES_DIR, nome)

# --- 🎯 ARSENAL CSS: IDENTIDADE COMPLETA & ANIMAÇÕES ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root { --navy:#173b70; --navy-deep:#102e5c; --blue:#36b7e5; --orange:#ff9d16; --ink:#172b4d; --muted:#65758b; --line:#e5ebf3; --canvas:#f5f8fc; }
html, body, [class*="css"] { font-family:'Plus Jakarta Sans',sans-serif; }
[data-testid="stAppViewContainer"] { background:var(--canvas); color:var(--ink); }
[data-testid="stHeader"] { background:rgba(245,248,252,.92); }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid var(--line); }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:var(--ink); }
.block-container { padding-top:1.8rem; padding-bottom:3rem; max-width:1440px; }
.clean-title { font-size:clamp(1.7rem,3vw,2.15rem)!important; font-weight:800!important; color:var(--navy-deep)!important; letter-spacing:-.045em; margin:0 0 1.1rem; }
.premium-card { background:#fff; border:1px solid var(--line); border-radius:18px; padding:24px; box-shadow:0 8px 24px rgba(23,59,112,.045); margin-bottom:18px; }
.premium-card:hover { border-color:#cfdeef; box-shadow:0 12px 28px rgba(23,59,112,.075); }
.empty-state-box { background:#fff; border:1px dashed #c9d6e6; border-radius:18px; padding:38px 20px; text-align:center; color:var(--muted); font-size:15px; margin:14px 0; }
.kpi-title { color:var(--muted); font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.08em; }
.kpi-value { font-size:clamp(1.25rem,2vw,1.65rem); font-weight:800; margin-top:7px; letter-spacing:-.04em; }
.val-total { color:var(--navy); } .val-pago { color:#13805e; } .val-pendente { color:#c46a00; } .val-negado { color:#bd3c43; }
div.stButton > button, [data-testid="stDownloadButton"] button, div[data-testid="stFormSubmitButton"] button { min-height:2.7rem; border-radius:11px; border:1px solid var(--navy); background:var(--navy); color:#fff; font-weight:700; transition:all .18s ease; }
div.stButton > button:hover, [data-testid="stDownloadButton"] button:hover, div[data-testid="stFormSubmitButton"] button:hover { background:var(--navy-deep); border-color:var(--navy-deep); color:#fff; transform:translateY(-1px); box-shadow:0 7px 16px rgba(23,59,112,.15); }
div[data-baseweb="input"], div[data-baseweb="select"] { border-radius:10px; }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-testid="stDateInput"] input { border-radius:10px; }
[data-testid="stTabs"] button { font-weight:700; }
[data-testid="stExpander"] { border:1px solid var(--line); border-radius:14px; background:#fff; }
.logo-fallback { font-size:22px; font-weight:800; color:var(--navy); letter-spacing:-.04em; margin:4px 0 16px; }
.logo-fallback span { color:var(--blue); }
.announcement { display:flex; gap:12px; align-items:center; padding:13px 18px; margin:0 0 22px; border-radius:14px; color:#fff; background:linear-gradient(105deg,#173b70 0%,#214e86 72%,#267bb0 100%); box-shadow:0 8px 20px rgba(23,59,112,.12); }
.announcement-mark { width:9px; height:9px; flex:0 0 9px; border-radius:50%; background:var(--orange); box-shadow:0 0 0 5px rgba(255,157,22,.16); }
.announcement strong { display:block; font-size:13px; letter-spacing:.01em; }
.announcement span { display:block; color:#dce9f8; font-size:12px; margin-top:2px; }
.btn-whatsapp { background:#1ca765; color:white!important; padding:13px 20px; border-radius:11px; text-decoration:none; font-weight:700; display:flex; justify-content:center; margin-top:14px; }
.loader-container { display:flex; flex-direction:column; align-items:center; justify-content:center; height:75vh; animation:fadeOut .5s ease-in-out forwards; animation-delay:2s; }
.spinner { border:4px solid #e8eef5; border-top:4px solid var(--navy); border-right:4px solid var(--orange); border-radius:50%; width:46px; height:46px; animation:spin 1s linear infinite; margin-bottom:18px; }
@keyframes spin { to { transform:rotate(360deg); } } @keyframes fadeOut { to { opacity:0; visibility:hidden; } }
@media (max-width:640px) { .block-container { padding-left:1rem; padding-right:1rem; } .premium-card { padding:18px; border-radius:15px; } .announcement { align-items:flex-start; } }
</style>
""", unsafe_allow_html=True)

DB_TIMEOUT = 30.0

# --- TELA DE CARREGAMENTO DUARTE ---
if not st.session_state["app_loaded"]:
    st.markdown("""
        <div class="loader-container">
            <div class="spinner"></div>
            <h2 style="color: #001E57; font-weight: 800;">Duarte<span style="color: #FF9200;">Gestão</span></h2>
            <p style="color: #64748b; font-size: 14px;">Inicializando ambiente seguro...</p>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(2.5) # Tempo da animação
    st.session_state["app_loaded"] = True
    st.rerun()

# --- GERADOR DE TABELAS REUTILIZÁVEL ---
def gerar_tabela_premium(df):
    if df.empty:
        return '<div class="empty-state-box">✨ Nenhuma solicitação localizada nesta fila.</div>'

    headers = "".join([f"<th style='padding: 16px; text-align: left; color: #64748b; font-size: 12px; font-weight: 700; text-transform: uppercase; border-bottom: 2px solid #f1f5f9;'>{col}</th>" for col in df.columns if col != 'caminho_arquivo'])

    rows_html = ""
    for _, row in df.iterrows():
        cells_html = ""
        for col in df.columns:
            if col == 'caminho_arquivo':
                continue
            val = row[col]

            if col == "Status":
                if val == "PENDENTE":
                    badge = f"<span style='background: #fff7ed; color: #c2410c; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; border: 1px solid #ffedd5;'>⏳ {val}</span>"
                elif val in ["PAGO", "APROVADO"]:
                    badge = f"<span style='background: #ecfdf5; color: #047857; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; border: 1px solid #d1fae5;'>✅ {val}</span>"
                elif val in ["NEGADO", "REJEITADO"]:
                    badge = f"<span style='background: #fef2f2; color: #b91c1c; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; border: 1px solid #fee2e2;'>❌ {val}</span>"
                else:
                    badge = f"<span style='background: #f1f5f9; color: #475569; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 700;'>{val}</span>"
                cells_html += f"<td style='padding: 16px; border-bottom: 1px solid #f1f5f9;'>{badge}</td>"

            elif "Valor" in col:
                try: v_fmt = f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except: v_fmt = str(val)
                cells_html += f"<td style='padding: 16px; border-bottom: 1px solid #f1f5f9; font-weight: 700; color: #001E57;'>{v_fmt}</td>"

            elif col == "ID":
                cells_html += f"<td style='padding: 16px; border-bottom: 1px solid #f1f5f9; font-weight: 600; color: #94a3b8;'>#{val}</td>"

            else:
                cells_html += f"<td style='padding: 16px; border-bottom: 1px solid #f1f5f9; color: #334155; font-size: 14px;'>{val}</td>"

        rows_html += f"""<tr style="transition: background 0.2s;" onmouseover="this.style.backgroundColor='#fafafa'" onmouseout="this.style.backgroundColor='white'">""" + cells_html + "</tr>"

    return f"""
    <div style='background: #ffffff; border-radius: 14px; border: 1px solid #e2e8f0; overflow-x: auto;'>
        <table style='width: 100%; border-collapse: collapse; text-align: left;'>
            <thead><tr style='background: #fafafa;'>{headers}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """

def renderizar_logo(local="sidebar"):
    logo_file = os.path.join("assets", "logo.png")
    if os.path.exists(logo_file):
        if local == "sidebar":
            st.sidebar.image(logo_file, width=130)
            st.sidebar.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        else:
            st.image(logo_file, width=140)
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
    else:
        html_texto = '<div class="logo-fallback">Duarte<span>Gestão</span></div>'
        if local == "sidebar":
            st.sidebar.markdown(html_texto, unsafe_allow_html=True)
        else:
            st.markdown(html_texto, unsafe_allow_html=True)

# --- 🚀 ESTRUTURA DO BANCO DE DADOS BLINDADA (SQLITE) ---
def inicializar_banco():
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS usuarios
                   (usuario TEXT PRIMARY KEY, senha TEXT, email TEXT, nivel TEXT,
                   nome_completo TEXT, cpf TEXT, telefone TEXT)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS reembolsos
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, despesa TEXT,
                   categoria TEXT, c_custo TEXT, valor REAL, status TEXT, data DATE, caminho_arquivo TEXT)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS logs
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_acao TEXT, acao TEXT, data_hora DATETIME)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS notificacoes
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, mensagem TEXT,
                   lida INTEGER, data_hora TEXT)""")

    # 🔒 LISTA DE ADMINS (Acesso total)
    # Credencial inicial configurada pelo administrador no ambiente; nunca sobrescreve usuários existentes.
    senha_admin_inicial = os.environ.get("ADMIN_BOOTSTRAP_PASSWORD", "")
    lista_admins = []
    if senha_admin_inicial:
        lista_admins = [
            ('admin', senha_admin_inicial, os.environ.get("ADMIN_BOOTSTRAP_EMAIL", ""), 'admin', 'ADMINISTRADOR PRINCIPAL', '', ''),
            ('operacional', senha_admin_inicial, os.environ.get("ADMIN_BOOTSTRAP_EMAIL", ""), 'admin', 'OPERACIONAL ADMINISTRATIVO', '', ''),
            ('financeiro', senha_admin_inicial, os.environ.get("ADMIN_BOOTSTRAP_EMAIL", ""), 'admin', 'FINANCEIRO DIRETORIA', '', '')
        ]

    # Contas legadas preservadas para permitir redefinição da senha pelo fluxo de suporte.
    # A senha vazia só é usada na criação inicial; usuários existentes nunca são alterados.
    lista_usuarios_comuns = [
        ('15413186843', '', 'diretoria@duartegestao.com.br', 'usuario', 'Cristiane A Duarte', '15413186843', '11959353330'),
        ('26218440818', '', 'bethania.duarte@duartegestao.com.br', 'usuario', 'Bethania Duarte', '26218440818', '11949957937'),
        ('11286836875', '', 'abraaossantos@gmail.com', 'usuario', 'Abraao S. Santos', '11286836875', '11972061000')
    ]

    for u in lista_admins + lista_usuarios_comuns:
        cursor.execute("INSERT OR IGNORE INTO usuarios VALUES (?,?,?,?,?,?,?)", u)
        
    conn.commit()
    conn.close()

def registrar_log(user, acao):
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (usuario_acao, acao, data_hora) VALUES (?,?,?)", (user, acao, datetime.now()))
    conn.commit()
    conn.close()

inicializar_banco()

st.markdown("""
<div class="announcement">
  <div class="announcement-mark"></div>
  <div><strong>Atualização 2.0 do sistema de reembolsos</strong>
  <span>Mais clareza para acompanhar solicitações e reforço nas rotinas de segurança.</span></div>
</div>
""", unsafe_allow_html=True)

# =================================================================
# FASE 1: LOGIN / CADASTRO
# =================================================================
if not st.session_state["logado"]:
    renderizar_logo(local="main")
    tab1, tab2, tab3 = st.tabs(["🔐 Acessar Conta", "📝 Novo Cadastro", "🛠️ Suporte & Senha"])

    with tab1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        login_cpf = st.text_input("CPF ou Login")
        login_senha = st.text_input("Senha", type="password")
        if st.button("Entrar no Sistema"):
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            user = conn.cursor().execute("SELECT * FROM usuarios WHERE (cpf=? OR usuario=?) AND senha=?", (login_cpf, login_cpf, login_senha)).fetchone()
            conn.close()
            if user:
                st.session_state["logado"] = True
                st.session_state["user_info"] = {"user": user[0], "nivel": user[3], "nome": user[4]}
                registrar_log(user[0], "LOGIN SUCESSO")
                st.rerun()
            else:
                st.error("CPF ou senha inválidos.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        with st.form("cad_form", clear_on_submit=True):
            nc_cpf = st.text_input("CPF (Apenas números)")
            nc_nome = st.text_input("Nome Completo")
            nc_tel = st.text_input("Telefone (Ex: 11999999999)")
            nc_email = st.text_input("E-mail")
            nc_senha = st.text_input("Senha", type="password")

            if st.form_submit_button("Cadastrar Profissional"):
                if not nc_cpf.strip() or not nc_email or "@" not in nc_email or nc_nome.strip() == "" or nc_senha.strip() == "":
                    st.error("Por favor, preencha todos os campos corretamente.")
                else:
                    try:
                        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                        conn.cursor().execute("INSERT INTO usuarios VALUES (?,?,?,?,?,?,?)", (nc_cpf, nc_senha, nc_email, 'usuario', nc_nome, nc_cpf, nc_tel))
                        conn.commit()
                        conn.close()
                        st.success("Cadastro efetuado! Prossiga para a aba de Acesso.")
                    except:
                        st.error("Este CPF já possui cadastro.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 🔑 Alterar Senha (Autoverificação)")
        rec_cpf = st.text_input("Informe seu CPF", key="rec_cpf")
        rec_email = st.text_input("Informe seu E-mail", key="rec_email")
        rec_tel = st.text_input("Informe seu Telefone", key="rec_tel")
        nova_senha = st.text_input("Digite a Nova Senha", type="password", key="nova_senha")

        if st.button("Validar dados e Alterar Senha"):
            if rec_cpf and rec_email and rec_tel and nova_senha:
                conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                cursor = conn.cursor()
                user = cursor.execute("SELECT * FROM usuarios WHERE (cpf=? OR usuario=?) AND email=? AND telefone=?", (rec_cpf, rec_cpf, rec_email, rec_tel)).fetchone()
                if user:
                    cursor.execute("UPDATE usuarios SET senha=? WHERE (cpf=? OR usuario=?)", (nova_senha, rec_cpf, rec_cpf))
                    conn.commit()
                    st.success("🔒 Senha redefinida com sucesso!")
                else:
                    st.error("❌ Os dados informados não conferem.")
                conn.close()
        st.markdown("<br><hr>", unsafe_allow_html=True)
        link_suporte_whatsapp = "https://wa.me/5511918551349?text=Olá,%20não%20consigo%20redefinir%20minha%20senha."
        st.markdown(f'<a href="{link_suporte_whatsapp}" target="_blank" class="btn-whatsapp">💬 Chamar Suporte Duarte Gestão</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# =================================================================
# FASE 2: AMBIENTE LOGADO
# =================================================================
else:
    renderizar_logo(local="sidebar")
    nome_usuario = st.session_state["user_info"].get("nome", "Usuário")
    usuario_id = st.session_state["user_info"].get("user")

    st.sidebar.markdown(f'<div style="padding: 12px 0; border-top: 1px solid #f1f5f9; margin-top: 15px;"><p style="margin:0; font-size:14px; font-weight:700; color:#001E57;">{nome_usuario}</p><span style="color:#FF9200; font-size:11px; font-weight:600; text-transform:uppercase;">Painel Ativo</span></div>', unsafe_allow_html=True)

    # --- ENGINE DE NOTIFICAÇÕES (SININHO) ---
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
    n_pendentes = conn.cursor().execute("SELECT COUNT(*) FROM notificacoes WHERE usuario=? AND lida=0", (usuario_id,)).fetchone()[0]
    conn.close()
    txt_sininho = f"🔔 Notificações ({n_pendentes})" if n_pendentes > 0 else "🔔 Notificações"

    with st.sidebar.popover(txt_sininho, use_container_width=True):
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        lista_notif = conn.cursor().execute("SELECT id, mensagem, data_hora, lida FROM notificacoes WHERE usuario=? ORDER BY id DESC LIMIT 5", (usuario_id,)).fetchall()
        if not lista_notif:
            st.markdown('<div style="color:#64748b; font-size:12px; text-align:center;">Nenhum aviso recente.</div>', unsafe_allow_html=True)
        else:
            for notif_id, msg_texto, dt_notif, status_lida in lista_notif:
                borda_estilo = "2px solid #FF9200" if status_lida == 0 else "1px solid #e2e8f0"
                st.markdown(f'<div style="background:#fff7ed; padding:10px; border-radius:8px; border:{borda_estilo}; margin-bottom:8px;"><p style="margin:0; font-size:12px; color:#001E57;">{msg_texto}</p></div>', unsafe_allow_html=True)
            if st.button("🧹 Limpar Notificações"):
                conn.cursor().execute("UPDATE notificacoes SET lida=1 WHERE usuario=?", (usuario_id,))
                conn.commit()
                st.rerun()
        conn.close()

    opcoes_menu = ["🏠 Início", "💸 Solicitar Reembolso", "📋 Meus Pedidos"]
    if st.session_state['user_info']['nivel'] == 'admin':
        opcoes_menu += ["📊 Painel do Admin", "📈 Painel Executivo"]
        if DB_PATH == "reembolso.db":
            st.sidebar.warning("Armazenamento padrão ativo. Para preservar os dados entre implantações, configure um volume persistente e REEMBOLSO_DB_PATH.")

    menu = st.sidebar.radio("Navegação", opcoes_menu)

    st.sidebar.write("---")
    if st.sidebar.button("🔒 Desconectar e Sair"):
        st.session_state["logado"] = False
        st.session_state["user_info"] = None
        st.rerun()

    # --- LISTAS DE CATEGORIAS E CENTROS DE CUSTO ---
    LISTA_CATEGORIAS = ["LIMPEZA", "REMUNERAÇÃO SÓCIOS", "ALIMENTAÇÃO", "TELEFONIA E INTERNET", "SOFTWARE E LICENÇAS - INFORMÁTICA", "TRANSPORTES / LOGÍSTICA", "COMBUSTÍVEL", "MATERIAL DE ESCRITÓRIO", "EQUIPAMENTOS DE INFORMÁTICA", "ESTACIONAMENTO", "MÓVEIS E UTENSÍLIOS", "DESPESAS DE VIAGENS", "MÁQUINAS E EQUIPAMENTOS", "HOSPEDAGEM", "OUTROS"]
    LISTA_CENTROS_CUSTO = ["CREDENCIAMENTO", "REDE", "DIRETORIA", "DUARTE GESTÃO", "MARKETING", "FINANCEIRO", "TECNOLOGIA DA INFORMAÇÃO", "RECURSOS HUMANOS - RH", "ADMINISTRATIVO", "OUTROS"]

    # --- 🏠 ABA: INÍCIO ---
    if menu == "🏠 Início":
        st.markdown('<h1 class="clean-title">Manual de Utilização do Sistema</h1>', unsafe_allow_html=True)
        st.markdown("""
        <div class="premium-card">
            <h3 style="color: #001E57; margin-top: 0; font-weight: 700;">👋 Boas-vindas ao Portal de Reembolsos Duarte Gestão</h3>
            <p style="color: #334155; font-size: 15px; line-height: 1.6;">
                Este espaço foi projetado para simplificar, organizar e auditar a prestação de contas de despesas corporativas. 
                Siga as diretrizes abaixo para garantir que o seu reembolso seja processado sem pendências.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="premium-card" style="height: 100%;">
                <h4 style="color: #FF9200; margin-top: 0; font-weight: 700;">1. Organize o Comprovante</h4>
                <ul style="color: #475569; font-size: 13px; padding-left: 20px;">
                    <li>Formatos aceitos: <b>PDF, JPG ou PNG</b>.</li>
                    <li>O documento deve estar <b>totalmente legível</b>, exibindo claramente Data, Valor e CNPJ.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="premium-card" style="height: 100%;">
                <h4 style="color: #10b981; margin-top: 0; font-weight: 700;">2. Monitore o Status</h4>
                <ul style="color: #475569; font-size: 13px; padding-left: 20px;">
                    <li>⏳ <b>PENDENTE:</b> Aguardando verificação fiscal.</li>
                    <li>❌ <b>NEGADO:</b> Nota com inconsistência. Você será notificado do motivo.</li>
                    <li>✅ <b>APROVADO / PAGO:</b> Nota auditada e liquidação concluída.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    # --- 💸 ABA: SOLICITAR REEMBOLSO ---
    elif menu == "💸 Solicitar Reembolso":
        st.markdown('<h1 class="clean-title">Nova Solicitação de Reembolso</h1>', unsafe_allow_html=True)
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        
        with st.form("reembolso_form", clear_on_submit=True):
            desc = st.text_input("Descrição Clara da Despesa")
            
            c_cat1, c_cat2 = st.columns(2)
            with c_cat1:
                cat_sel = st.selectbox("Categoria", LISTA_CATEGORIAS)
                cat_outros = st.text_input("Se escolheu 'OUTROS' na Categoria, digite aqui qual é:")
            with c_cat2:
                cc_sel = st.selectbox("Centro de Custo", LISTA_CENTROS_CUSTO)
                cc_outros = st.text_input("Se escolheu 'OUTROS' no Centro de Custo, digite aqui qual é:")

            val = st.number_input("Valor da Operação (R$)", min_value=0.01, step=0.01)
            arq = st.file_uploader("Upload do Comprovante (PDF, PNG, JPG)", type=['jpg', 'png', 'pdf'])

            if st.form_submit_button("Enviar Solicitação"):
                cat_final = cat_outros.strip().upper() if (cat_sel == "OUTROS" and cat_outros.strip() != "") else cat_sel
                cc_final = cc_outros.strip().upper() if (cc_sel == "OUTROS" and cc_outros.strip() != "") else cc_sel

                if desc and val > 0:
                    nome_seguro = os.path.basename(arq.name) if arq else ""
                    nome_arquivo = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{nome_seguro}" if arq else ""
                    path = f"comprovantes/{nome_arquivo}" if arq else ""
                    if arq:
                        with open(os.path.join(COMPROVANTES_DIR, nome_arquivo), "wb") as f: f.write(arq.getbuffer())
                    
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    conn.cursor().execute("INSERT INTO reembolsos (usuario, despesa, categoria, c_custo, valor, status, data, caminho_arquivo) VALUES (?,?,?,?,?,?,?,?)",
                                          (st.session_state['user_info']['user'], desc, cat_final, cc_final, val, 'PENDENTE', datetime.now().date(), path))
                    conn.commit(); conn.close()
                    st.success("Solicitação salva com sucesso!")
                else:
                    st.error("Por favor, preencha a descrição e o valor corretamente.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 📋 ABA: MEUS PEDIDOS ---
    elif menu == "📋 Meus Pedidos":
        st.markdown('<h1 class="clean-title">Acompanhamento de Solicitações</h1>', unsafe_allow_html=True)
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df_completo = pd.read_sql_query("SELECT id as 'ID', despesa as 'Descrição', categoria as 'Categoria', c_custo as 'Centro de Custo', valor as 'Valor (R$)', status as 'Status', data as 'Data', caminho_arquivo FROM reembolsos WHERE usuario=? ORDER BY id DESC", conn, params=(st.session_state['user_info']['user'],))
        conn.close()

        if df_completo.empty:
            st.markdown('<div class="empty-state-box">✨ Nenhuma solicitação registrada.</div>', unsafe_allow_html=True)
        else:
            df_exibir = df_completo.drop(columns=['caminho_arquivo'])
            st.markdown(gerar_tabela_premium(df_exibir), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            df_editaveis = df_completo[df_completo['Status'].isin(['PENDENTE', 'NEGADO'])]

            if not df_editaveis.empty:
                st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                st.markdown('<p style="font-weight:700; color:#001E57; margin-bottom:15px; font-size:18px;">✏️ Corrigir ou Alterar Solicitação</p>', unsafe_allow_html=True)
                st.write("Você pode consertar dados de solicitações que estão **Pendentes** ou que foram **Negadas**.")
                
                df_editaveis['selector_edit'] = df_editaveis.apply(lambda r: f"#{r['ID']} - {r['Descrição']} (R$ {r['Valor (R$)']:.2f}) [{r['Status']}]", axis=1)
                item_edit = st.selectbox("Escolha qual lançamento deseja corrigir:", df_editaveis['selector_edit'].tolist())
                
                row_edit = df_editaveis[df_editaveis['selector_edit'] == item_edit].iloc[0]
                id_edit = int(row_edit['ID'])
                
                with st.form(f"form_editar_{id_edit}", clear_on_submit=False):
                    nova_desc = st.text_input("Corrigir Descrição", value=row_edit['Descrição'])
                    
                    c_edit1, c_edit2 = st.columns(2)
                    with c_edit1:
                        idx_cat = LISTA_CATEGORIAS.index(row_edit['Categoria']) if row_edit['Categoria'] in LISTA_CATEGORIAS else LISTA_CATEGORIAS.index("OUTROS")
                        nova_cat = st.selectbox("Alterar Categoria", LISTA_CATEGORIAS, index=idx_cat)
                        valor_padrao_cat = row_edit['Categoria'] if idx_cat == LISTA_CATEGORIAS.index("OUTROS") else ""
                        nova_cat_outros = st.text_input("Se 'OUTROS', corrija a categoria aqui:", value=valor_padrao_cat)
                        
                    with c_edit2:
                        idx_cc = LISTA_CENTROS_CUSTO.index(row_edit['Centro de Custo']) if row_edit['Centro de Custo'] in LISTA_CENTROS_CUSTO else LISTA_CENTROS_CUSTO.index("OUTROS")
                        novo_cc = st.selectbox("Alterar Centro de Custo", LISTA_CENTROS_CUSTO, index=idx_cc)
                        valor_padrao_cc = row_edit['Centro de Custo'] if idx_cc == LISTA_CENTROS_CUSTO.index("OUTROS") else ""
                        novo_cc_outros = st.text_input("Se 'OUTROS', corrija o centro de custo aqui:", value=valor_padrao_cc)

                    novo_val = st.number_input("Corrigir Valor (R$)", min_value=0.01, step=0.01, value=float(row_edit['Valor (R$)']))
                    
                    st.write("Anexar novo comprovante (deixe em branco para manter o comprovante atual):")
                    novo_arq = st.file_uploader("Substituir Comprovante", type=['jpg', 'png', 'pdf'], key=f"file_edit_{id_edit}")
                    
                    if st.form_submit_button("💾 Salvar Alterações e Reenviar"):
                        cat_final_edit = nova_cat_outros.strip().upper() if (nova_cat == "OUTROS" and nova_cat_outros.strip() != "") else nova_cat
                        cc_final_edit = novo_cc_outros.strip().upper() if (novo_cc == "OUTROS" and novo_cc_outros.strip() != "") else novo_cc

                        if nova_desc and novo_val > 0:
                            caminho_atual = row_edit['caminho_arquivo']
                            
                            if novo_arq:
                                if caminho_atual and os.path.exists(resolver_caminho_comprovante(caminho_atual)):
                                    try: os.remove(resolver_caminho_comprovante(caminho_atual))
                                    except: pass
                                nome_seguro = os.path.basename(novo_arq.name)
                                nome_arquivo = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{nome_seguro}"
                                caminho_atual = f"comprovantes/{nome_arquivo}"
                                with open(os.path.join(COMPROVANTES_DIR, nome_arquivo), "wb") as f: f.write(novo_arq.getbuffer())
                            
                            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE reembolsos 
                                SET despesa=?, categoria=?, c_custo=?, valor=?, status='PENDENTE', caminho_arquivo=? 
                                WHERE id=?
                            """, (nova_desc, cat_final_edit, cc_final_edit, novo_val, caminho_atual, id_edit))
                            conn.commit(); conn.close()
                            
                            registrar_log(st.session_state['user_info']['user'], f"EDITOU E REENVIOU REEMBOLSO ID {id_edit}")
                            st.success(f"Solicitação #{id_edit} atualizada com sucesso! Ela voltou para a fila de análise do Admin.")
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # --- 📊 ABA: PAINEL DO ADMIN ---
    elif menu == "📊 Painel do Admin":
        st.markdown('<h1 class="clean-title">Central de Despache Express</h1>', unsafe_allow_html=True)

        def processar_acao_clean(id_target, novo_status, log_msg, motivo_rejeicao=""):
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            cursor = conn.cursor()
            pedido = cursor.execute("SELECT r.despesa, u.usuario FROM reembolsos r JOIN usuarios u ON r.usuario = u.usuario WHERE r.id = ?", (id_target,)).fetchone()

            if pedido:
                despesa, usuario_dono = pedido
                cursor.execute("UPDATE reembolsos SET status=? WHERE id=?", (novo_status, id_target))
                msg_notif = f"Sua solicitação #{id_target} ({despesa}) foi alterada para {novo_status}."
                if novo_status == "NEGADO" and motivo_rejeicao: msg_notif += f" Motivo: {motivo_rejeicao}"
                
                cursor.execute("INSERT INTO notificacoes (usuario, mensagem, lida, data_hora) VALUES (?, ?, 0, ?)",
                               (usuario_dono, msg_notif, datetime.now().strftime('%d/%m/%Y %H:%M:%S')))
                conn.commit()
                registrar_log(st.session_state['user_info']['user'], f"{log_msg} ID {id_target}")
                conn.close()
                st.success(f"Status atualizado para {novo_status}!")
                st.rerun()
            else:
                conn.close()

        # 🔥 AQUI ESTÁ O LEFT JOIN PARA APARECER O NOME DO FUNCIONÁRIO
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        query_admin = """
        SELECT 
            r.id as 'ID', 
            u.nome_completo as 'Funcionário', 
            r.despesa as 'Descrição', 
            r.categoria as 'Categoria', 
            r.c_custo as 'Centro de Custo', 
            r.valor as 'Valor (R$)', 
            r.status as 'Status', 
            r.data as 'Data Lançamento', 
            r.caminho_arquivo 
        FROM reembolsos r
        LEFT JOIN usuarios u ON r.usuario = u.usuario
        ORDER BY r.id DESC
        """
        df_todos = pd.read_sql(query_admin, conn)
        conn.close()

        tab_pendente, tab_aprovado, tab_historico = st.tabs(["⏳ Aguardando Análise", "💸 Pronto para Pagamento", "🗂️ Histórico Geral"])

        with tab_pendente: st.markdown(gerar_tabela_premium(df_todos[df_todos['Status'] == 'PENDENTE']), unsafe_allow_html=True)
        with tab_aprovado: st.markdown(gerar_tabela_premium(df_todos[df_todos['Status'] == 'APROVADO']), unsafe_allow_html=True)
        with tab_historico: st.markdown(gerar_tabela_premium(df_todos[df_todos['Status'].isin(['PAGO', 'NEGADO'])]), unsafe_allow_html=True)

        # PAINEL DE AÇÕES RÁPIDAS
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<p style="font-weight:700; color:#001E57; margin-bottom:20px; font-size:18px;">🕹️ Painel de Ações Rápidas</p>', unsafe_allow_html=True)

        if df_todos.empty:
            st.info("Nenhum lançamento no sistema.")
        else:
            df_todos['selector_text'] = df_todos.apply(lambda r: f"#{r['ID']} - {r['Funcionário']} | {r['Descrição']} (R$ {r['Valor (R$)']:.2f}) [{r['Status']}]", axis=1)
            col_ctrl, col_preview = st.columns([1.3, 1])

            with col_ctrl:
                item_selecionado = st.selectbox("Selecione o lançamento para despachar:", df_todos['selector_text'].tolist())
                row_sel = df_todos[df_todos['selector_text'] == item_selecionado].iloc[0]

                id_target = int(row_sel['ID'])
                status_atual = row_sel['Status']
                caminho_comprovante = row_sel['caminho_arquivo']
                usuario_dono_nome = row_sel['Funcionário']

                # Precisamos buscar o usuário (código) real e telefone para o WhatsApp
                conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                dados_func = conn.cursor().execute("SELECT telefone FROM usuarios WHERE nome_completo=?", (usuario_dono_nome,)).fetchone()
                conn.close()

                telefone_func = dados_func[0] if dados_func else ""

                if status_atual == "PENDENTE":
                    if st.button("✅ Aprovar Documento"): processar_acao_clean(id_target, "APROVADO", "APROVOU REEMBOLSO")
                elif status_atual == "APROVADO":
                    if st.button("💸 Marcar como PAGO (Liquidar)"): processar_acao_clean(id_target, "PAGO", "PAGOU REEMBOLSO")

                if status_atual == "PAGO" and telefone_func:
                    tel_limpo = "".join(filter(str.isdigit, telefone_func))
                    if not tel_limpo.startswith("55") and len(tel_limpo) >= 10: tel_limpo = "55" + tel_limpo
                    msg_wa = f"Olá, *{usuario_dono_nome}*!\n\nSua solicitação de reembolso *#{id_target}* (*{row_sel['Descrição']}*) de *R$ {row_sel['Valor (R$)']:.2f}* foi paga com sucesso!"
                    st.markdown(f'<a href="https://wa.me/{tel_limpo}?text={urllib.parse.quote(msg_wa)}" target="_blank" class="btn-whatsapp">💬 Enviar Notificação via WhatsApp</a>', unsafe_allow_html=True)

                if status_atual in ["PENDENTE", "APROVADO"]:
                    motivo = st.text_input("Motivo da Recusa:", key=f"motivo_{id_target}")
                    if st.button("❌ Negar Reembolso"):
                        if motivo.strip(): processar_acao_clean(id_target, "NEGADO", "REJEITOU REEMBOLSO", motivo)
                        else: st.error("Insira o motivo.")

                st.write("---")
                st.markdown("<p style='color:#ef4444; font-weight:700; font-size:14px; margin-bottom:5px;'>⚠️ Zona de Perigo</p>", unsafe_allow_html=True)
                confirmar_exclusao = st.checkbox("Estou ciente de que esta ação apagará permanentemente o registro do banco de dados.", key=f"del_chk_{id_target}")
                
                if st.button("🗑️ Excluir Lançamento Permanente", key=f"del_btn_{id_target}"):
                    if confirmar_exclusao:
                        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                        cursor = conn.cursor()
                        if caminho_comprovante and os.path.exists(resolver_caminho_comprovante(caminho_comprovante)):
                            try: os.remove(resolver_caminho_comprovante(caminho_comprovante))
                            except: pass
                        cursor.execute("DELETE FROM reembolsos WHERE id=?", (id_target,))
                        conn.commit(); conn.close()
                        st.success(f"Lançamento #{id_target} apagado!")
                        st.rerun()
                    else:
                        st.error("Marque a caixa de confirmação primeiro.")

            # 📥 DOWNLOAD DO COMPROVANTE CORRIGIDO
            with col_preview:
                if caminho_comprovante and os.path.exists(resolver_caminho_comprovante(caminho_comprovante)):
                    st.markdown("**📄 Arquivo em anexo:**")
                    
                    if caminho_comprovante.lower().endswith('.pdf'):
                        st.caption("Documento PDF. Clique no botão abaixo para baixar e revisar:")
                    else:
                        st.image(resolver_caminho_comprovante(caminho_comprovante), use_container_width=True)
                        st.caption("Imagem do comprovante. Clique no botão abaixo para salvar uma cópia:")
                    
                    with open(resolver_caminho_comprovante(caminho_comprovante), "rb") as f:
                        st.download_button(
                            label="📥 Baixar Comprovante", 
                            data=f, 
                            file_name=os.path.basename(caminho_comprovante),
                            use_container_width=True
                        )
                else: 
                    st.info("Sem arquivo em anexo.")
                    
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("👥 [PRODUÇÃO] Lista de Usuários Cadastrados no Sistema"):
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            df_users = pd.read_sql("SELECT usuario as 'Login', nome_completo as 'Nome Completo', nivel as 'Perfil', email as 'E-mail', telefone as 'Telefone' FROM usuarios", conn)
            conn.close()
            st.dataframe(df_users, use_container_width=True)

    # --- 📈 ABA: PAINEL EXECUTIVO ---
    elif menu == "📈 Painel Executivo":
        st.markdown('<h1 class="clean-title">Painel Executivo de Controladoria</h1>', unsafe_allow_html=True)
        st.markdown('<div class="premium-card">📊 Métricas de desempenho financeiro consolidado da Duarte Gestão.</div>', unsafe_allow_html=True)
        
        # --- ENGINE DO DASHBOARD ---
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df_dash = pd.read_sql("SELECT * FROM reembolsos", conn)
        conn.close()

        if df_dash.empty:
            st.info("Ainda não há lançamentos suficientes para gerar os indicadores.")
        else:
            df_pago = df_dash[df_dash['status'] == 'PAGO']
            df_pend = df_dash[df_dash['status'] == 'PENDENTE']
            df_neg  = df_dash[df_dash['status'] == 'NEGADO']

            tot_geral = df_dash['valor'].sum()
            tot_pago = df_pago['valor'].sum()
            tot_pend = df_pend['valor'].sum()
            tot_neg = df_neg['valor'].sum()

            def formata_brl(valor):
                return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            st.markdown("### 🎯 Visão Geral de Lançamentos")
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.markdown(f'<div class="premium-card"><div class="kpi-title">Volume Solicitado</div><div class="kpi-value val-total">{formata_brl(tot_geral)}</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="premium-card"><div class="kpi-title">Total Liquidado (Pago)</div><div class="kpi-value val-pago">{formata_brl(tot_pago)}</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="premium-card"><div class="kpi-title">Fila Pendente</div><div class="kpi-value val-pendente">{formata_brl(tot_pend)}</div></div>', unsafe_allow_html=True)
            with c4:
                st.markdown(f'<div class="premium-card"><div class="kpi-title">Total Negado</div><div class="kpi-value val-negado">{formata_brl(tot_neg)}</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📊 Distribuição de Custos (Liquidados)")
            g1, g2 = st.columns(2)

            with g1:
                st.markdown("**Por Centro de Custo**")
                if not df_pago.empty:
                    df_cc = df_pago.groupby('c_custo')['valor'].sum().sort_values(ascending=False)
                    st.bar_chart(df_cc, color="#001E57") 
                else:
                    st.write("Aguardando pagamentos para gerar o gráfico.")

            with g2:
                st.markdown("**Por Categoria da Despesa**")
                if not df_pago.empty:
                    df_cat = df_pago.groupby('categoria')['valor'].sum().sort_values(ascending=False)
                    st.bar_chart(df_cat, color="#FF9200") 
                else:
                    st.write("Aguardando pagamentos para gerar o gráfico.")

        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.markdown("### 📥 Backup de Segurança Total (Botão de Pânico)")
        st.write("Baixe a cópia de segurança completa de todos os dados salvos no sistema para salvaguarda externa:")
        
        if not df_dash.empty:
            csv_backup = df_dash.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 BAIXAR HISTÓRICO COMPLETO (CSV)",
                data=csv_backup,
                file_name=f"BACKUP_GERAL_DUARTE_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
        else:
            st.info("Nenhum dado financeiro para exportar no momento.")

        st.markdown("### 🛡️ Importar backup de solicitações (CSV)")
        st.caption("A importação só é liberada quando ainda não há solicitações no banco. Ela não substitui usuários, anexos ou outros dados; primeiro gera uma cópia local do banco atual.")
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        qtd_atual = conn.execute("SELECT COUNT(*) FROM reembolsos").fetchone()[0]
        conn.close()
        if qtd_atual:
            st.warning(f"Importação bloqueada: o banco já possui {qtd_atual} solicitação(ões). Isso evita duplicações e sobrescritas acidentais.")
        else:
            st.info("O banco de solicitações está vazio. Envie um backup CSV para conferir a prévia antes de confirmar.")

        arquivo_backup = st.file_uploader("Selecionar backup CSV", type=["csv"], key="importar_backup_csv")
        if arquivo_backup is not None:
            try:
                dados_bytes = arquivo_backup.getvalue()
                try:
                    df_import = pd.read_csv(io.BytesIO(dados_bytes), dtype=str, keep_default_na=False, encoding="utf-8-sig")
                except UnicodeDecodeError:
                    df_import = pd.read_csv(io.BytesIO(dados_bytes), dtype=str, keep_default_na=False, encoding="latin-1")

                obrigatorias = ["id", "usuario", "despesa", "categoria", "c_custo", "valor", "status", "data"]
                faltantes = [c for c in obrigatorias if c not in df_import.columns]
                if faltantes:
                    st.error("CSV não reconhecido. Colunas obrigatórias ausentes: " + ", ".join(faltantes))
                elif df_import.empty:
                    st.error("O CSV não contém solicitações para importar.")
                else:
                    erros_import = []
                    linhas_import = []
                    ids_vistos = set()
                    for numero_linha, linha in df_import.iterrows():
                        linha_num = numero_linha + 2
                        try:
                            id_registro = int(str(linha["id"]).strip())
                            if id_registro <= 0 or id_registro in ids_vistos:
                                raise ValueError("ID inválido ou repetido no próprio CSV")
                            ids_vistos.add(id_registro)
                            usuario_csv = str(linha["usuario"]).strip()
                            despesa_csv = str(linha["despesa"]).strip()
                            categoria_csv = str(linha["categoria"]).strip()
                            centro_csv = str(linha["c_custo"]).strip()
                            status_csv = str(linha["status"]).strip().upper()
                            if not usuario_csv or not despesa_csv or not categoria_csv or not centro_csv:
                                raise ValueError("há campo obrigatório vazio")
                            if status_csv not in {"PENDENTE", "APROVADO", "PAGO", "NEGADO"}:
                                raise ValueError("status não reconhecido")
                            valor_txt = str(linha["valor"]).strip().replace("R$", "").replace(" ", "")
                            if "," in valor_txt and "." not in valor_txt:
                                valor_txt = valor_txt.replace(",", ".")
                            valor_csv = float(valor_txt)
                            if valor_csv < 0 or not pd.notna(valor_csv):
                                raise ValueError("valor inválido")
                            data_txt = str(linha["data"]).strip()
                            data_csv = None
                            for fmt_data in ("%Y-%m-%d", "%d/%m/%Y"):
                                try:
                                    data_csv = datetime.strptime(data_txt, fmt_data).date().isoformat()
                                    break
                                except ValueError:
                                    pass
                            if data_csv is None:
                                raise ValueError("data inválida (use AAAA-MM-DD ou DD/MM/AAAA)")
                            anexo_csv = str(linha.get("caminho_arquivo", "")).strip()
                            if anexo_csv:
                                anexo_norm = anexo_csv.replace("\\", "/")
                                if anexo_norm.startswith("/") or ":" in anexo_norm or ".." in anexo_norm.split("/") or not anexo_norm.startswith("comprovantes/"):
                                    raise ValueError("caminho de comprovante inseguro ou fora da pasta comprovantes")
                                anexo_csv = "comprovantes/" + os.path.basename(anexo_norm)
                            linhas_import.append((id_registro, usuario_csv, despesa_csv, categoria_csv, centro_csv, valor_csv, status_csv, data_csv, anexo_csv))
                        except Exception as erro_linha:
                            erros_import.append(f"Linha {linha_num}: {erro_linha}")

                    st.markdown(f"**Prévia:** {len(df_import)} linha(s) no arquivo · **{len(linhas_import)} válida(s)** · {sum(1 for x in linhas_import if x[8])} com referência a comprovante.")
                    st.caption("Os arquivos de comprovante não estão dentro do CSV; referências só voltarão a abrir se os arquivos também existirem na pasta persistente de anexos.")
                    if erros_import:
                        with st.expander(f"Ver problemas encontrados ({len(erros_import)})"):
                            for erro in erros_import[:30]:
                                st.write("• " + erro)
                            if len(erros_import) > 30:
                                st.caption(f"Mais {len(erros_import) - 30} problema(s) não exibido(s).")
                    if len(linhas_import) == len(df_import) and not erros_import:
                        st.warning("Confirme apenas se este é o backup correto. A operação adiciona todas as linhas em uma única transação; se falhar, nenhuma linha é importada.")
                        confirma_import = st.text_input("Digite IMPORTAR para habilitar a restauração", key="confirmar_importacao_csv")
                        if st.button("Restaurar solicitações deste CSV", type="primary", key="botao_importar_csv"):
                            if confirma_import.strip() != "IMPORTAR":
                                st.error("Digite IMPORTAR exatamente para confirmar.")
                            else:
                                copia_path = ""
                                try:
                                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                                    conn.execute("BEGIN IMMEDIATE")
                                    if conn.execute("SELECT COUNT(*) FROM reembolsos").fetchone()[0] != 0:
                                        raise RuntimeError("O banco deixou de estar vazio; importação cancelada sem alterações.")
                                    os.makedirs("backups", exist_ok=True)
                                    copia_path = os.path.join("backups", f"reembolso_pre_importacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite3")
                                    destino = sqlite3.connect(copia_path)
                                    conn.backup(destino)
                                    destino.close()
                                    conn.executemany("INSERT INTO reembolsos (id, usuario, despesa, categoria, c_custo, valor, status, data, caminho_arquivo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", linhas_import)
                                    conn.commit()
                                    conn.close()
                                    registrar_log(st.session_state['user_info']['user'], f"IMPORTOU BACKUP CSV ({len(linhas_import)} solicitações)")
                                    st.success(f"Importação concluída: {len(linhas_import)} solicitações restauradas. Uma cópia local do banco anterior foi criada antes da operação.")
                                    st.rerun()
                                except Exception as erro_import:
                                    try:
                                        conn.rollback()
                                        conn.close()
                                    except Exception:
                                        pass
                                    st.error(f"Importação cancelada; o banco não foi alterado: {erro_import}")
            except Exception as erro_csv:
                st.error(f"Não foi possível ler este CSV: {erro_csv}")
