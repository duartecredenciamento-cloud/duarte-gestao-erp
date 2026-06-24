import streamlit as st
import pandas as pd
import sqlite3
import os
import smtplib
import io
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import re

# --- CONFIGURAÇÃO INICIAL DA PÁGINA (Deve ser o primeiro comando Streamlit) ---
st.set_page_config(page_title="Duarte Gestão - Financeiro", layout="wide", initial_sidebar_state="expanded")

# --- INICIALIZAÇÃO SEGURA DO SESSION STATE ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "user_info" not in st.session_state:
    st.session_state["user_info"] = None

def verificar_email(email):
    padrao = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(padrao, email))

if not os.path.exists("comprovantes"): 
    os.makedirs("comprovantes")

# --- 🎯 ARSENAL CSS: IDENTIDADE COMPLETA & ANIMAÇÕES INCRÍVEIS 🎯 ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=300;400;500;600;700;800&display=swap');
        
        * { font-family: 'Plus Jakarta Sans', sans-serif; }
        [data-testid="stAppViewContainer"] {
            background-color: #f8fafc !important;
            color: #001E57 !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0 !important;
        }
        
        .clean-title {
            font-size: 28px !important;
            font-weight: 800 !important;
            color: #001E57 !important;
            letter-spacing: -0.5px;
            margin-bottom: 25px;
            animation: softSlideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        }
        /* Cards Premium com Animação de Hover Flutuante */
        .premium-card {
            background: #ffffff !important;
            border-radius: 14px !important;
            padding: 24px !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 4px 12px rgba(0, 30, 87, 0.02) !important;
            margin-bottom: 20px;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
            animation: softSlideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .premium-card:hover {
            transform: translateY(-4px) !important;
            box-shadow: 0 12px 24px rgba(0, 30, 87, 0.06) !important;
            border-color: #001E57 !important;
        }
        .empty-state-box {
            background: #ffffff !important;
            border: 2px dashed #e2e8f0 !important;
            border-radius: 14px !important;
            padding: 40px 20px !important;
            text-align: center !important;
            color: #64748b !important;
            font-size: 15px !important;
            font-weight: 500 !important;
            margin-bottom: 20px;
            animation: softSlideUp 0.5s ease-out;
        }
        .kpi-title { color: #64748b !important; font-size: 12px !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.5px; }
        .kpi-value { font-size: 24px !important; font-weight: 800 !important; margin-top: 4px; }
        .val-total { color: #001E57 !important; }
        .val-pago { color: #10b981 !important; }
        .val-pendente { color: #FF9200 !important; }
        .val-negado { color: #ef4444 !important; }
        /* Botões Estilizados e Animados */
        div.stButton > button {
            width: 100% !important;
            background-color: #001E57 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }
        div.stButton > button:hover {
            background-color: #FF9200 !important;
            color: #ffffff !important;
            transform: scale(1.02) !important;
            box-shadow: 0 6px 20px rgba(255, 146, 0, 0.25) !important;
        }
        div.stButton > button:active {
            transform: scale(0.98) !important;
        }
        /* Botão do WhatsApp de Suporte e Disparos */
        .btn-whatsapp {
            background-color: #25D366;
            color: white !important;
            padding: 14px 28px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin-top: 15px;
            width: 100%;
            box-sizing: border-box;
            box-shadow: 0 4px 12px rgba(37, 211, 102, 0.2);
            transition: all 0.25s ease !important;
        }
        .btn-whatsapp:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 24px rgba(37, 211, 102, 0.35) !important;
        }
        div[data-baseweb="input"], div[data-baseweb="select"] {
            border-radius: 8px !important;
        }
        .logo-fallback {
            font-size: 20px !important;
            font-weight: 800 !important;
            color: #001E57 !important;
            letter-spacing: -0.5px;
            margin-bottom: 15px;
        }
        .logo-fallback span { color: #FF9200 !important; }
        /* Keyframes para Entrada Suave (Slide e Opacidade) */
        @keyframes softSlideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        tr {
            transition: background-color 0.2s ease !important;
        }
    </style>
""", unsafe_allow_html=True)

DB_PATH = "reembolso.db"
DB_TIMEOUT = 30.0
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_REMETENTE = "financeiro.duartegestao@gmail.com"
EMAIL_SENHA = "zbvwzhnsjlqperfr"

# --- GERADOR DE TABELAS ULTRA PROFISSIONAIS ---
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

# --- FUNÇÃO DE RENDERIZAÇÃO DE LOGO COMPACTA PADRÃO CORPORATIVO ---
def renderizar_logo(local="sidebar"):
    logo_file = "LOGO DUARTE FUNDO MARINHO - AJUSTADO.JPG"
    
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

# --- NOTIFICAÇÕES VIA E-MAIL ---
def enviar_notificacao_email(destinatario, assunto, titulo_card, status_pedido, detalhes_html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = f"Duarte Gestão Financeira <{EMAIL_REMETENTE}>"
    msg["To"] = destinatario
    cor_status = "#001E57"
    if "PENDENTE" in status_pedido: cor_status = "#FF9200"
    elif "APROVADO" in status_pedido or "PAGO" in status_pedido: cor_status = "#10b981"
    elif "NEGADO" in status_pedido or "REJEITADO" in status_pedido: cor_status = "#ef4444"
    html = f"""
<html>
<body style="font-family: 'Segoe UI', sans-serif; background-color: #f8fafc; padding: 30px; margin: 0;">
    <div style="max-width: 600px; background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; margin: 0 auto; overflow: hidden; box-shadow: 0 4px 12px rgba(0,30,87,0.03);">
        <div style="background-color: #001E57; padding: 30px; text-align: center;">
            <h2 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: 700;">DUARTE GESTÃO</h2>
            <p style="color: #FF9200; margin: 5px 0 0 0; font-size: 12px; font-weight: 600; text-transform: uppercase;">Controladoria & Finanças</p>
        </div>
        <div style="padding: 30px; color: #334155;">
            <h3 style="color: #001E57; margin-top: 0; font-size: 18px; font-weight: 700;">{titulo_card}</h3>
            <div style="display: inline-block; background-color: {cor_status}; color: #ffffff; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; margin-bottom: 25px; text-transform: uppercase;">
                Status: {status_pedido}
            </div>
            <div style="background-color: #f1f5f9; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">{detalhes_html}</table>
            </div>
        </div>
    </div>
</body>
</html>
"""
    msg.attach(MIMEText(html, "html"))
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_REMETENTE, EMAIL_SENHA)
        server.sendmail(EMAIL_REMETENTE, destinatario, msg.as_string())
        server.quit()
        return True
    except:
        return False

# --- ESTRUTURA DO BANCO DE DADOS (SQLITE) ---
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
    
    adms = [
        ('admin', 'Duarte1234#', 'financeiro.duartegestao@gmail.com', 'admin', 'ADMINISTRADOR PRINCIPAL', '000.000.000-00', '(00) 00000-0000'),
        ('operacional', 'Duarte1234#', 'financeiro.duartegestao@gmail.com', 'admin', 'OPERACIONAL ADMINISTRATIVO', '000.000.000-00', '(00) 00000-0000'),
        ('financeiro', 'Duarte1234#', 'financeiro.duartegestao@gmail.com', 'admin', 'FINANCEIRO DIRETORIA', '000.000.000-00', '(00) 00000-0000')
    ]
    for u in adms: cursor.execute("INSERT OR REPLACE INTO usuarios VALUES (?,?,?,?,?,?,?)", u)
    conn.commit(); conn.close()

def registrar_log(user, acao):
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (usuario_acao, acao, data_hora) VALUES (?,?,?)", (user, acao, datetime.now()))
    conn.commit(); conn.close()

inicializar_banco()

# =================================================================
# FASE 1: USUÁRIO DESLOGADO -> EXIBE LOGIN / CADASTRO
# =================================================================
if not st.session_state["logado"]:
    renderizar_logo(local="main")
    
    tab1, tab2, tab3 = st.tabs(["🔐 Acessar Conta", "📝 Novo Cadastro", "🛠️ Suporte & Senha"])
    
    with tab1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        login_cpf = st.text_input("CPF")
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
            nc_cpf = st.text_input("CPF (Apenas números ou formatado)")
            nc_nome = st.text_input("Nome Completo")
            nc_tel = st.text_input("Telefone (Ex: 11999999999)")
            nc_email = st.text_input("E-mail")
            nc_senha = st.text_input("Senha", type="password")
            
            if st.form_submit_button("Cadastrar Profissional"):
                if not nc_cpf.strip():
                    st.error("O campo CPF é obrigatório.")
                elif not nc_email or "@" not in nc_email:    
                    st.error("Por favor, informe um e-mail válido.")
                elif nc_nome.strip() == "" or nc_senha.strip() == "":
                    st.error("Nome completo e Senha são obrigatórios.")
                else:
                    try:
                        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                        conn.cursor().execute("INSERT INTO usuarios VALUES (?,?,?,?,?,?,?)", (nc_cpf, nc_senha, nc_email, 'usuario', nc_nome, nc_cpf, nc_tel))
                        conn.commit()
                        conn.close()
                        st.success("Cadastro efetuado com sucesso! Prossiga para a aba de Acesso.")
                    except Exception as e: 
                        st.error("Este CPF já possui cadastro no sistema.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 🔑 Alterar Senha (Autoverificação)")
        st.write("Insira seus dados cadastrados exatamente como no registro para definir uma nova senha:")
        
        rec_cpf = st.text_input("Informe seu CPF", key="rec_cpf")
        rec_email = st.text_input("Informe seu E-mail cadastrado", key="rec_email")
        rec_tel = st.text_input("Informe seu Telefone cadastrado", key="rec_tel")
        nova_senha = st.text_input("Digite a Nova Senha", type="password", key="nova_senha")
        
        if st.button("Validar dados e Alterar Senha"):
            if rec_cpf and rec_email and rec_tel and nova_senha:
                conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                cursor = conn.cursor()
                user = cursor.execute("SELECT * FROM usuarios WHERE (cpf=? OR usuario=?) AND email=? AND telefone=?", (rec_cpf, rec_cpf, rec_email, rec_tel)).fetchone()
                
                if user:
                    cursor.execute("UPDATE usuarios SET senha=? WHERE (cpf=? OR usuario=?)", (nova_senha, rec_cpf, rec_cpf))
                    conn.commit()
                    registrar_log(user[0], "ALTERACAO SENHA AUTO")
                    st.success("🔒 Senha redefinida com sucesso! Você já pode acessar a aba 'Acessar Conta'.")
                else:
                    st.error("❌ Os dados informados não conferem com nenhum registro ativo.")
                conn.close()
            else:
                st.warning("Preencha todos os campos para executar a redefinição de segurança.")
        
        st.markdown("<br><hr style='border-color:#e2e8f0;'><p style='font-size:13px; color:#64748b;'>Caso não lembre de seus dados cadastrados, solicite ajuda manual:</p>", unsafe_allow_html=True)
        link_suporte_whatsapp = "https://wa.me/5511918551349?text=Olá,%20não%20consigo%20redefinir%20minha%20senha%20de%20acesso%20ao%20Painel%20de%20Reembolsos%20da%20Duarte%20Gestão.%20Poderia%20me%20auxiliar?"
        st.markdown(f'<a href="{link_suporte_whatsapp}" target="_blank" class="btn-whatsapp">💬 Chamar Suporte Duarte Gestão</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# =================================================================
# FASE 2: AMBIENTE INTERNO LOGADO
# =================================================================
else:
    renderizar_logo(local="sidebar")
    
    if st.session_state.get("user_info") is not None:
        nome_usuario = st.session_state["user_info"].get("nome", "Usuário")
        usuario_id = st.session_state["user_info"].get("user")
        
        st.sidebar.markdown(
            f'<div style="padding: 12px 0; border-top: 1px solid #f1f5f9; margin-top: 15px;">'
            f'<p style="margin:0; font-size:14px; font-weight:700; color:#001E57;">{nome_usuario}</p>'
            f'<span style="color:#FF9200; font-size:11px; font-weight:600; text-transform:uppercase;">Painel Ativo</span>'
            f'</div>', 
            unsafe_allow_html=True
        )
        
        # --- 🔔 ENGINE DO SININHO DE NOTIFICAÇÕES ---
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        n_pendentes = conn.cursor().execute("SELECT COUNT(*) FROM notificacoes WHERE usuario=? AND lida=0", (usuario_id,)).fetchone()[0]
        conn.close()
        
        txt_sininho = f"🔔 Notificações ({n_pendentes})" if n_pendentes > 0 else "🔔 Notificações"
        
        with st.sidebar.popover(txt_sininho, use_container_width=True):
            st.markdown('<p style="font-weight:700; color:#001E57; margin-bottom:10px; font-size:14px;">Centro de Notificações</p>', unsafe_allow_html=True)
            
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            lista_notif = conn.cursor().execute("SELECT id, mensagem, data_hora, lida FROM notificacoes WHERE usuario=? ORDER BY id DESC LIMIT 5", (usuario_id,)).fetchall()
            
            if not lista_notif:
                st.markdown('<div style="color:#64748b; font-size:12px; text-align:center; padding:10px;">Nenhum aviso recente por aqui.</div>', unsafe_allow_html=True)
            else:
                for notif_id, msg_texto, dt_notif, status_lida in lista_notif:
                    borda_estilo = "2px solid #FF9200" if status_lida == 0 else "1px solid #e2e8f0"
                    fundo_estilo = "#fff7ed" if status_lida == 0 else "#ffffff"
                    st.markdown(f"""
                        <div style="background: {fundo_estilo}; padding: 10px; border-radius: 8px; border: {borda_estilo}; margin-bottom: 8px;">
                            <p style="margin: 0; font-size: 12px; color: #001E57; font-weight: 500;">{msg_texto}</p>
                            <span style="font-size: 10px; color: #94a3b8;">{dt_notif[:16]}</span>
                        </div>
                    """, unsafe_allow_html=True)
                
                if st.button("🧹 Marcar todas como lidas"):
                    conn.cursor().execute("UPDATE notificacoes SET lida=1 WHERE usuario=?", (usuario_id,))
                    conn.commit()
                    conn.close()
                    st.rerun()
            conn.close()
    
    opcoes_menu = ["🏠 Início", "💸 Solicitar Reembolso", "📋 Meus Pedidos"]
    if st.session_state['user_info']['nivel'] == 'admin':
        opcoes_menu += ["📊 Painel do Admin", "📈 Painel Executivo"]
        
    menu = st.sidebar.radio("Navegação", opcoes_menu)
    
    st.sidebar.write("---")
    if st.sidebar.button("🔒 Desconectar e Sair"):
        st.session_state["logado"] = False
        st.session_state["user_info"] = None
        st.rerun()

    # --- ABA: INÍCIO ---
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
                    <li>O documento deve estar **totalmente legível**, exibindo claramente Data, Valor e CNPJ.</li>
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
            
    # --- ABA: SOLICITAR REEMBOLSO ---
    elif menu == "💸 Solicitar Reembolso":
        st.markdown('<h1 class="clean-title">Nova Solicitação de Reembolso</h1>', unsafe_allow_html=True)
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        with st.form("reembolso_form", clear_on_submit=True):
            desc = st.text_input("Descrição Clara da Despesa")
            cat = st.selectbox("Categoria", ["LIMPEZA", "REMUNERAÇÃO SÓCIOS", "ALIMENTAÇÃO", "TELEFONIA E INTERNET", "SOFTWARE E LICENÇAS - INFORMÁTICA", "TRANSPORTES / LOGÍSTICA", "MATERIAL DE ESCRITRIOM", "EQUIPAMENTOS DE INFORMÁTICA", "ESTACIONAMENTO", "MÓVEIS E UTENSÍLIOS", "DESPESAS DE VIAGENS", "MÁQUINAS E EQUIPAMENTOS"])
            cc = st.selectbox("Centro de Custo", ["CREDENCIAMENTO", "REDE", "DIRETORIA", "DUARTE GESTÃO", "MARKETING", "FINANCEIRO"])
            val = st.number_input("Valor da Operação (R$)", min_value=0.01, step=0.01)
            arq = st.file_uploader("Upload do Comprovante", type=['jpg', 'png', 'pdf'])
            
            if st.form_submit_button("Enviar Solicitação"):
                if desc and val > 0:
                    path = f"comprovantes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{arq.name}" if arq else ""
                    if arq:
                        with open(path, "wb") as f: f.write(arq.getbuffer())
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    conn.cursor().execute("INSERT INTO reembolsos (usuario, despesa, categoria, c_custo, valor, status, data, caminho_arquivo) VALUES (?,?,?,?,?,?,?,?)", 
                                       (st.session_state['user_info']['user'], desc, cat, cc, val, 'PENDENTE', datetime.now().date(), path))
                    conn.commit(); conn.close()
                    st.success("Solicitação salva e enviada para a fila de aprovação!")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ABA: MEUS PEDIDOS ---
    elif menu == "📋 Meus Pedidos":
        st.markdown('<h1 class="clean-title">Acompanhamento de Solicitações</h1>', unsafe_allow_html=True)
        
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df = pd.read_sql(f"SELECT id as 'ID', despesa as 'Descrição', categoria as 'Categoria', c_custo as 'Centro de Custo', valor as 'Valor (R$)', status as 'Status', data as 'Data' FROM reembolsos WHERE usuario='{st.session_state['user_info']['user']}' ORDER BY id DESC", conn)
        conn.close()
        
        if df.empty:
            st.markdown('<div class="empty-state-box">✨ Você ainda não possui nenhuma solicitação registrada.</div>', unsafe_allow_html=True)
        else:
            m_pend = df[df['Status'] == 'PENDENTE']['Valor (R$)'].sum()
            m_aprov = df[df['Status'] == 'APROVADO']['Valor (R$)'].sum()
            m_pago = df[df['Status'] == 'PAGO']['Valor (R$)'].sum()
            m_neg = df[df['Status'] == 'NEGADO']['Valor (R$)'].sum()
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f'<div class="premium-card"><div class="kpi-title">⏳ Em Análise</div><div class="kpi-value val-pendente">R$ {m_pend:,.2f}</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="premium-card"><div class="kpi-title">✅ Aprovados</div><div class="kpi-value" style="color:#001E57;">R$ {m_aprov:,.2f}</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="premium-card"><div class="kpi-title">💸 Pagos</div><div class="kpi-value val-pago">R$ {m_pago:,.2f}</div></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="premium-card"><div class="kpi-title">❌ Recusados</div><div class="kpi-value val-negado">R$ {m_neg:,.2f}</div></div>', unsafe_allow_html=True)
            st.markdown(gerar_tabela_premium(df), unsafe_allow_html=True)

    # --- ABA: PAINEL DO ADMIN ---
    elif menu == "📊 Painel do Admin":
        st.markdown('<h1 class="clean-title">Central de Despache Express</h1>', unsafe_allow_html=True)
        
        def processar_acao_clean(id_target, novo_status, log_msg, motivo_rejeicao=""):
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            cursor = conn.cursor()
            
            query = (
                "SELECT r.despesa, r.valor, r.categoria, r.c_custo, r.data, u.email, u.nome_completo, r.usuario "
                "FROM reembolsos r "
                "JOIN usuarios u ON r.usuario = u.usuario "
                "WHERE r.id = ?"
            )
            pedido = cursor.execute(query, (id_target,)).fetchone()
            
            if pedido:
                despesa, valor, categoria, c_custo, data, email_colaborador, nome_usuario, usuario_dono = pedido
                cursor.execute("UPDATE reembolsos SET status=? WHERE id=?", (novo_status, id_target))
                
                msg_notif = f"Sua solicitação #{id_target} ({despesa}) foi alterada para {novo_status}."
                if novo_status == "NEGADO" and motivo_rejeicao:
                    msg_notif += f" Motivo: {motivo_rejeicao}"
                
                cursor.execute("INSERT INTO notificacoes (usuario, mensagem, lida, data_hora) VALUES (?, ?, 0, ?)",
                               (usuario_dono, msg_notif, datetime.now().strftime('%d/%m/%Y %H:%M:%S')))
                
                conn.commit()
                registrar_log(st.session_state['user_info']['user'], f"{log_msg} ID {id_target}")
                conn.close()
                st.success(f"Status atualizado para {novo_status}!")
                st.rerun()
            else:
                conn.close()
                st.error("Erro: ID não localizado.")

        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df_todos = pd.read_sql("SELECT id as 'ID', usuario as 'Funcionário', despesa as 'Descrição', categoria as 'Categoria', c_custo as 'Centro de Custo', valor as 'Valor (R$)', status as 'Status', data as 'Data Lançamento', caminho_arquivo FROM reembolsos ORDER BY id DESC", conn)
        conn.close()
        
        tab_pendente, tab_aprovado, tab_historico = st.tabs(["⏳ Aguardando Análise", "💸 Pronto para Pagamento", "🗂️ Histórico Geral"])
        
        with tab_pendente:
            st.markdown(gerar_tabela_premium(df_todos[df_todos['Status'] == 'PENDENTE']), unsafe_allow_html=True)
            
        with tab_aprovado:
            st.markdown(gerar_tabela_premium(df_todos[df_todos['Status'] == 'APROVADO']), unsafe_allow_html=True)
            
            # Exportador de Lote
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div style="background:#f8fafc; border-radius:12px; padding:20px; border:1px solid #e2e8f0;">', unsafe_allow_html=True)
            st.markdown('<p style="font-weight:700; color:#001E57; margin-bottom:10px; font-size:16px;">📅 Exportação de Lote Mensal para o Banco</p>', unsafe_allow_html=True)
            
            meses_nome = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
            c_mes, c_ano, c_btn = st.columns([1.5, 1, 1.5])
            with c_mes: mes_sel = st.selectbox("Mês Competência", list(meses_nome.keys()), format_func=lambda x: meses_nome[x], index=datetime.now().month - 1)
            with c_ano: ano_sel = st.selectbox("Ano Competência", [2025, 2026, 2027], index=1)
            
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            df_lote_cru = pd.read_sql("SELECT r.id, u.nome_completo, u.cpf, u.telefone, r.despesa, r.valor, r.data, r.status FROM reembolsos r JOIN usuarios u ON r.usuario = u.usuario WHERE r.status = 'APROVADO'", conn)
            conn.close()
            
            with c_btn:
                st.write("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if not df_lote_cru.empty:
                    df_lote_cru['dt_parsed'] = pd.to_datetime(df_lote_cru['data'], errors='coerce')
                    df_filtrado = df_lote_cru[(df_lote_cru['dt_parsed'].dt.month == mes_sel) & (df_lote_cru['dt_parsed'].dt.year == ano_sel)].copy()
                    if not df_filtrado.empty:
                        buffer_lote = io.BytesIO()
                        with pd.ExcelWriter(buffer_lote, engine='openpyxl') as writer:
                            df_filtrado.drop(columns=['dt_parsed', 'data']).to_excel(writer, sheet_name='LOTE MENSAL', index=False)
                        buffer_lote.seek(0)
                        st.download_button(label=f"📥 Baixar Lote {meses_nome[mes_sel].upper()}", data=buffer_lote, file_name=f"LOTE_{meses_nome[mes_sel].upper()}.xlsx")
                    else: st.button("⚠️ Sem itens este mês", disabled=True)
                else: st.button("✨ Fila Limpa", disabled=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with tab_historico:
            st.markdown(gerar_tabela_premium(df_todos[df_todos['Status'].isin(['PAGO', 'NEGADO'])]), unsafe_allow_html=True)

        # --- PAINEL DE AÇÕES RÁPIDAS COM DISPARADOR WHATSAPP ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<p style="font-weight:700; color:#001E57; margin-bottom:20px; font-size:18px;">🕹️ Painel de Ações Rápidas</p>', unsafe_allow_html=True)
        
        # Adicionado o status PAGO para permitir selecionar e re-enviar WhatsApp caso necessário
        df_acionaveis = df_todos[df_todos['Status'].isin(['PENDENTE', 'APROVADO', 'NEGADO', 'PAGO'])].copy()
        
        if df_acionaveis.empty:
            st.info("✨ Nenhuma ação pendente no momento.")
        else:
            df_acionaveis['selector_text'] = df_acionaveis.apply(lambda r: f"#{r['ID']} - {r['Funcionário']} | {r['Descrição']} (R$ {r['Valor (R$)']:.2f}) [{r['Status']}]", axis=1)
            col_ctrl, col_preview = st.columns([1.3, 1])
            
            with col_ctrl:
                item_selecionado = st.selectbox("Selecione o lançamento para despachar:", df_acionaveis['selector_text'].tolist())
                row_sel = df_acionaveis[df_acionaveis['selector_text'] == item_selecionado].iloc[0]
                
                id_target = int(row_sel['ID'])
                status_atual = row_sel['Status']
                caminho_comprovante = row_sel['caminho_arquivo']
                usuario_dono = row_sel['Funcionário']
                
                conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                dados_func = conn.cursor().execute("SELECT nome_completo, telefone FROM usuarios WHERE usuario=?", (usuario_dono,)).fetchone()
                conn.close()
                
                nome_completo = dados_func[0] if dados_func else usuario_dono
                telefone_func = dados_func[1] if dados_func else ""
                
                st.markdown(f"**Status Atual:** `{status_atual}` | **Colaborador:** {nome_completo}")
                
                if status_atual == "PENDENTE":
                    if st.button("✅ Aprovar Documento"):
                        processar_acao_clean(id_target, "APROVADO", "APROVOU REEMBOLSO")
                elif status_atual == "APROVADO":
                    if st.button("💸 Marcar como PAGO (Liquidar)"):
                        processar_acao_clean(id_target, "PAGO", "PAGOU REEMBOLSO")
                
                # 🔥 MÓDULO DE INTEGRAÇÃO DO WHATSAPP DE PAGAMENTO SUCESSO
                if status_atual == "PAGO":
                    st.success("🎉 Este reembolso já foi liquidado no sistema!")
                    if telefone_func:
                        # Limpa o telefone removendo caracteres especiais para a URL
                        tel_limpo = "".join(filter(str.isdigit, telefone_func))
                        if not tel_limpo.startswith("55") and len(tel_limpo) >= 10:
                            tel_limpo = "55" + tel_limpo
                        
                        # Monta a mensagem padrão corporativa em negrito do WhatsApp
                        msg_wa = (
                            f"Olá, *{nome_completo}*!\n\n"
                            f"Informamos que a sua solicitação de reembolso *#{id_target}* (*{row_sel['Descrição']}*) "
                            f"no valor de *R$ {row_sel['Valor (R$)']:.2f}* foi liquidada e o pagamento já foi efetuado "
                            f"pela controladoria da *Duarte Gestão*.\n\n"
                            f"Por favor, confira o saldo em sua conta cadastrada. Obrigado!"
                        )
                        msg_encoded = urllib.parse.quote(msg_wa)
                        link_whatsapp_envio = f"https://wa.me/{tel_limpo}?text={msg_encoded}"
                        
                        st.markdown(f'<a href="{link_whatsapp_envio}" target="_blank" class="btn-whatsapp" style="background-color:#25D366; text-align:center;">💬 Enviar Notificação de Pagamento via WhatsApp</a>', unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ Não foi possível gerar o link: Telefone não cadastrado para este usuário.")
                
                if status_atual in ["PENDENTE", "APROVADO"]:
                    st.write("---")
                    motivo = st.text_input("Motivo da Recusa (Obrigatório para negar):", key=f"motivo_{id_target}")
                    if st.button("❌ Negar Reembolso"):
                        if motivo.strip():
                            processar_acao_clean(id_target, "NEGADO", "REJEITOU REEMBOLSO", motivo)
                        else:
                            st.error("Insira o motivo da recusa antes de clicar.")
            
            with col_preview:
                st.markdown("**📄 Comprovante Digitalizado**")
                if caminho_comprovante and os.path.exists(caminho_comprovante):
                    if caminho_comprovante.lower().endswith('.pdf'):
                        st.caption("Documento PDF. Clique para baixar e revisar:")
                        with open(caminho_comprovante, "rb") as f:
                            st.download_button("📥 Baixar PDF", f, file_name=os.path.basename(caminho_comprovante))
                    else:
                        st.image(caminho_comprovante, use_container_width=True)
                else:
                    st.info("Nenhum arquivo de comprovante foi anexado a esta solicitação.")
        st.markdown('</div>', unsafe_allow_html=True)

        # --- UTILITÁRIO DE INFRAESTRUTURA: MONITOR DE PRODUÇÃO (CHEFES / CONTAS) ---
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("👥 [PRODUÇÃO] Lista de Usuários Cadastrados no Sistema"):
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            df_users = pd.read_sql("SELECT cpf as 'CPF Key', nome_completo as 'Nome Completo', email as 'E-mail', telefone as 'Telefone', senha as 'Senha Ativa' FROM usuarios", conn)
            conn.close()
            st.dataframe(df_users, use_container_width=True)

    # --- ABA: PAINEL EXECUTIVO ---
    elif menu == "📈 Painel Executivo":
        st.markdown('<h1 class="clean-title">Painel Executivo de Controladoria</h1>', unsafe_allow_html=True)
        st.markdown('<div class="premium-card">📊 Métricas de desempenho financeiro e relatórios consolidados da Duarte Gestão.</div>', unsafe_allow_html=True)
        st.info("Módulo de inteligência analítica estruturado. Dados em sincronia com o banco principal.")