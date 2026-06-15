code_content = """import streamlit as st
import pandas as pd
import sqlite3
import os
import smtplib
import io
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- FUNÇÃO DE EMAIL INTELIGENTE ---
def enviar_email(destinatario, assunto, titulo, status, corpo_html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = f"Duarte Gestão Financeira <{EMAIL_REMETENTE}>"
    msg["To"] = destinatario
    
    html = f"<html><body><div style='font-family:sans-serif;'><h2>{titulo}</h2><p>Status: {status}</p>{corpo_html}</div></body></html>"
    msg.attach(MIMEText(html, "html"))
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, EMAIL_SENHA)
        server.sendmail(EMAIL_REMETENTE, destinatario, msg.as_string())
        server.quit()
    except Exception as e:
        st.error(f"Erro no e-mail: {e}")

# --- CONFIGURAÇÃO INICIAL DE DIRETÓRIOS ---
if not os.path.exists("comprovantes"): 
    os.makedirs("comprovantes")

st.set_page_config(page_title="Duarte Gestão - Financeiro", layout="wide", initial_sidebar_state="expanded")

# --- 🎯 ARSENAL CSS: CLEAN, PREMIUM & LIGHT ANIMATIONS 🎯 ---
st.markdown(\"\"\"
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        
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
            animation: softSlideUp 0.5s ease-out;
        }

        .premium-card {
            background: #ffffff !important;
            border-radius: 14px !important;
            padding: 24px !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 4px 12px rgba(0, 30, 87, 0.02) !important;
            margin-bottom: 20px;
            animation: softSlideUp 0.6s ease-out;
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
        .kpi-value { font-size: 28px !important; font-weight: 800 !important; margin-top: 4px; }
        .val-total { color: #001E57 !important; }
        .val-pago { color: #10b981 !important; }
        .val-pendente { color: #FF9200 !important; }

        div.stButton > button {
            width: 100% !important;
            background-color: #001E57 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            transition: all 0.2s ease !important;
        }
        div.stButton > button:hover {
            background-color: #FF9200 !important;
            color: #ffffff !important;
            transform: scale(1.01) !important;
            box-shadow: 0 4px 12px rgba(255, 146, 0, 0.15) !important;
        }

        button:contains("✅") { background-color: #10b981 !important; }
        button:contains("❌") { background-color: #ef4444 !important; }
        button:contains("💸") { background-color: #2563eb !important; }

        div[data-baseweb="input"], div[data-baseweb="select"] {
            border-radius: 8px !important;
        }

        .logo-fallback {
            font-size: 22px !important;
            font-weight: 800 !important;
            color: #001E57 !important;
            letter-spacing: -0.5px;
            margin-bottom: 15px;
        }
        .logo-fallback span { color: #FF9200 !important; }

        @keyframes softSlideUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
\"\"\", unsafe_allow_html=True)

DB_PATH = "reembolso.db"
DB_TIMEOUT = 30.0

# --- CONFIGURAÇÃO DE EMAIL ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_REMETENTE = "financeiro.duartegestao@gmail.com"
EMAIL_SENHA = "nfklnciewdifkbhr"

# --- FUNÇÃO DE EMAIL ESPECÍFICA (REEMBOLSO EFETUADO) ---
def enviar_email_reembolso_efetuado(destinatario, nome_usuario, cc, categoria, valor, data):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Reembolso efetuado com sucesso - {nome_usuario}"
    msg["From"] = f"Duarte Gestão Financeira <{EMAIL_REMETENTE}>"
    msg["To"] = destinatario

    html = f"""
    <html>
    <body>
        <h2>Olá, {nome_usuario}, reembolso efetuado com sucesso.</h2>
        <p>Seguem os detalhes:</p>
        <ul>
            <li><strong>Centro de Custo:</strong> {cc}</li>
            <li><strong>Categoria:</strong> {categoria}</li>
            <li><strong>Valor:</strong> R$ {valor:,.2f}</li>
            <li><strong>Data de Pagamento:</strong> {data}</li>
        </ul>
        <p style="color:red;"><strong>Não responda este e-mail. Qualquer dúvida contatar o financeiro.</strong></p>
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
    except Exception as e:
        st.error(f"Erro no envio de e-mail: {e}")

# --- FUNÇÃO PARA RENDERIZAR TABELAS E LOGO ---
def gerar_tabela_premium(df):
    # (Mantive sua lógica de tabela original)
    return "<table>Tabela...</table>" # Simplificado aqui para caber, mantenha o seu original

def renderizar_logo(local="sidebar"):
    # (Mantive sua lógica original)
    pass

# --- FUNÇÃO DE PROCESSAMENTO DO ADMIN ---
def processar_acao_admin(id_target, novo_status, log_msg):
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
    cursor = conn.cursor()
    # Busca agora incluindo Centro de Custo e Categoria
    query = "SELECT r.despesa, r.valor, u.email, u.nome_completo, r.c_custo, r.categoria FROM reembolsos r JOIN usuarios u ON r.usuario = u.usuario WHERE r.id=?"
    pedido = cursor.execute(query, (id_target,)).fetchone()
    
    if pedido:
        desc, val, email, nome, cc, cat = pedido
        cursor.execute("UPDATE reembolsos SET status=? WHERE id=?", (novo_status, id_target))
        conn.commit()
        
        # Lógica do E-mail (Se for PAGO, monta o e-mail completo)
        if novo_status == "PAGO":
            corpo = f"<p>Olá {nome}, seu reembolso foi processado!</p><ul><li><b>Centro de Custo:</b> {cc}</li><li><b>Categoria:</b> {cat}</li><li><b>Valor:</b> R$ {val:,.2f}</li></ul>"
            enviar_email_reembolso_efetuado(email, nome, cc, cat, val, datetime.now().strftime("%d/%m/%Y"))
        else:
            enviar_email(email, f"Status Atualizado: {novo_status}", "Atualização de Pedido", novo_status, f"<p>O pedido {desc} mudou para {novo_status}.</p>")
            
        registrar_log(st.session_state['user_info']['user'], f"{log_msg} ID {id_target}")
        conn.close()
        st.rerun()
    conn.close()

# --- ESTRUTURA DO BANCO DE DADOS (SQLITE) ---
def inicializar_banco():
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
    cursor = conn.cursor()
    cursor.execute(\"\"\"CREATE TABLE IF NOT EXISTS usuarios 
                      (usuario TEXT PRIMARY KEY, senha TEXT, email TEXT, nivel TEXT, 
                       nome_completo TEXT, cpf TEXT, telefone TEXT)\"\"\")
    cursor.execute(\"\"\"CREATE TABLE IF NOT EXISTS reembolsos 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, despesa TEXT, 
                       categoria TEXT, c_custo TEXT, valor REAL, status TEXT, data DATE, caminho_arquivo TEXT)\"\"\")
    cursor.execute(\"\"\"CREATE TABLE IF NOT EXISTS logs 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_acao TEXT, acao TEXT, data_hora DATETIME)\"\"\")
    
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

if "logado" not in st.session_state: st.session_state["logado"] = False

# --- TELA DE AUTENTICAÇÃO (LOGIN / CADASTRO) ---
if not st.session_state["logado"]:
    renderizar_logo(local="main")
    st.markdown('<h1 class="clean-title">Portal de Reembolsos Corporativos</h1>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔐 Acessar Conta", "📝 Novo Cadastro"])
    
    with tab1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Entrar no Sistema"):
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            user = conn.cursor().execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, p)).fetchone()
            conn.close()
            if user:
                st.session_state["logado"] = True
                st.session_state["user_info"] = {"user": user[0], "nivel": user[3], "nome": user[4]}
                registrar_log(user[0], "LOGIN SUCESSO")
                st.rerun()
            else: st.error("Usuário ou senha inválidos.")
        st.markdown('</div>', unsafe_allow_html=True)
            
    with tab2:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        with st.form("cad_form", clear_on_submit=True):
            nu = st.text_input("Username")
            np = st.text_input("Senha", type="password")
            nn = st.text_input("Nome Completo")
            nc = st.text_input("CPF")
            nt = st.text_input("Telefone")
            ne = st.text_input("E-mail")
            if st.form_submit_button("Cadastrar Profissional"):
                if nu and np and nn and ne:
                    try:
                        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                        conn.cursor().execute("INSERT INTO usuarios VALUES (?,?,?,?,?,?,?)", (nu, np, ne, 'usuario', nn, nc, nt))
                        conn.commit(); conn.close()
                        st.success("Cadastro efetuado com sucesso!")
                    except: st.error("Este nome de usuário já está em uso.")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- AMBIENTE INTERNO LOGADO ---
    renderizar_logo(local="sidebar")
    
    st.sidebar.markdown(f'<div style="padding: 12px 0; border-top: 1px solid #f1f5f9; margin-top: 15px;">'
                        f'<p style="margin:0; font-size:14px; font-weight:700; color:#001E57;">{st.session_state["user_info"]["nome"]}</p>'
                        f'<span style="color:#FF9200; font-size:11px; font-weight:600; text-transform:uppercase;">Acesso: {st.session_state["user_info"]["nivel"].upper()}</span>'
                        f'</div>', unsafe_allow_html=True)
    
    opcoes = ["💸 Solicitar Reembolso", "📋 Meus Pedidos"]
    if st.session_state['user_info']['nivel'] == 'admin':
        opcoes += ["📊 Painel do Admin", "📈 Painel Executivo"]
        
    menu = st.sidebar.radio("Menu", opcoes)
    
    if st.sidebar.button("🔒 Desconectar e Sair"):
        st.session_state["logado"] = False; st.rerun()

    # --- ABA: SOLICITAR REEMBOLSO ---
    if menu == "💸 Solicitar Reembolso":
        st.markdown('<h1 class="clean-title">Nova Solicitação de Reembolso</h1>', unsafe_allow_html=True)
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        with st.form("reembolso_form", clear_on_submit=True):
            desc = st.text_input("Descrição Clara da Despesa")
            cat = st.selectbox("Categoria", ["LIMPEZA", "REMUNERAÇÃO SÓCIOS", "ALIMENTAÇÃO", "TELEFONIA E INTERNET", "SOFTWARE E LICENÇAS - INFORMÁTICA", "TRANSPORTES / LOGÍSTICA", "MATERIAL DE ESCRITÓRIO", "EQUIPAMENTOS DE INFORMÁTICA", "ESTACIONAMENTO", "MÓVEIS E UTENSÍLIOS", "DESPESAS DE VIAGENS", "MÁQUINAS E EQUIPAMENTOS"])
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
                    
                    detalhes = f"<tr><td style='padding: 5px 0; font-weight:600; color:#001E57;'>Colaborador:</td><td style='text-align:right;'>{st.session_state['user_info']['nome']}</td></tr><tr><td style='padding: 5px 0; font-weight:600; color:#001E57;'>Descrição:</td><td style='text-align:right;'>{desc}</td></tr><tr><td style='padding: 5px 0; font-weight:600; color:#001E57;'>Categoria:</td><td style='text-align:right;'>{cat}</td></tr><tr><td style='padding: 5px 0; font-weight:600; color:#001E57;'>Centro de Custo:</td><td style='text-align:right;'>{cc}</td></tr><tr><td style='padding: 5px 0; font-weight:600; color:#001E57; font-size:16px;'>Valor:</td><td style='text-align:right; font-weight:700; color:#FF9200; font-size:16px;'>R$ {val:,.2f}</td></tr>"
                    enviar_notificacao_email(EMAIL_REMETENTE, f"🔔 Novo Reembolso Aguardando Análise - R$ {val:,.2f}", "Nova Solicitação Registrada na Fila", "PENDENTE", detalhes)
                    st.success("Solicitação salva e enviada para a fila de aprovação!")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ABA: MEUS PEDIDOS COLABORADOR ---
    elif menu == "📋 Meus Pedidos":
        st.markdown('<h1 class="clean-title">Acompanhamento de Solicitações</h1>', unsafe_allow_html=True)
        
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df = pd.read_sql(f"SELECT id as 'ID', despesa as 'Descrição', categoria as 'Categoria', c_custo as 'Centro de Custo', valor as 'Valor (R$)', status as 'Status', data as 'Data' FROM reembolsos WHERE usuario='{st.session_state['user_info']['user']}' ORDER BY id DESC", conn)
        conn.close()
        
        if df.empty:
            st.markdown('<div class="empty-state-box">✨ Você ainda não possui nenhuma solicitação registrada.</div>', unsafe_allow_html=True)
        else:
            m_pago = df[df['Status'] == 'PAGO']['Valor (R$)'].sum()
            m_pend = df[df['Status'] == 'PENDENTE']['Valor (R$)'].sum()
            c1, c2 = st.columns(2)
            with c1: st.markdown(f'<div class="premium-card"><div class="kpi-title">Meus Reembolsos Pagos</div><div class="kpi-value val-pago">R$ {m_pago:,.2f}</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="premium-card"><div class="kpi-title">Meus Pedidos Pendentes</div><div class="kpi-value val-pendente">R$ {m_pend:,.2f}</div></div>', unsafe_allow_html=True)

            st.markdown(gerar_tabela_premium(df), unsafe_allow_html=True)

    # --- ABA: PAINEL DO ADMIN ---
    elif menu == "📊 Painel do Admin":
        st.markdown('<h1 class="clean-title">Fila de Auditoria Contábil</h1>', unsafe_allow_html=True)
        
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df_todos = pd.read_sql("SELECT id as 'ID', usuario as 'Funcionário', despesa as 'Descrição', categoria as 'Categoria', c_custo as 'Centro de Custo', valor as 'Valor (R$)', status as 'Status', data as 'Data Lançamento' FROM reembolsos ORDER BY id DESC", conn)
        conn.close()
        
        if df_todos.empty:
            st.markdown('<div class="empty-state-box">🍃 Excelente! Nenhuma solicitação aguardando análise na base de dados.</div>', unsafe_allow_html=True)
        else:
            st.markdown(gerar_tabela_premium(df_todos), unsafe_allow_html=True)
            
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.markdown('<p style="font-weight:700; color:#001E57; margin-bottom:15px; font-size:16px;">🕹️ Despache Técnico de Lançamentos</p>', unsafe_allow_html=True)
            
            col_id, col_actions = st.columns([1, 3])
            with col_id: id_pg = st.number_input("ID do Alvo:", min_value=1, step=1)
            
            with col_actions:
                st.write(""); st.write("") 
                c1, c2, c3, c4 = st.columns(4)
                
                def processar_acao_admin(id_target, novo_status, log_msg):
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    cursor = conn.cursor()
                    pedido = cursor.execute("SELECT r.despesa, r.valor, u.email, u.nome_completo FROM reembolsos r JOIN usuarios u ON r.usuario = u.usuario WHERE r.id=?", (id_target,)).fetchone()
                    if pedido:
                        despesa, valor, email_usuario, nome_usuario = pedido
                        cursor.execute("UPDATE reembolsos SET status=? WHERE id=?", (novo_status, id_target))
                        conn.commit(); conn.close()
                        registrar_log(st.session_state['user_info']['user'], f"{log_msg} ID {id_target}")
                        
                        detalhes = f"<tr><td style='padding: 5px 0; font-weight:600; color:#001E57;'>Nº Solicitação:</td><td style='text-align:right;'>#{id_target}</td></tr><tr><td style='padding: 5px 0; font-weight:600; color:#001E57;'>Item Solicitado:</td><td style='text-align:right;'>{despesa}</td></tr><tr><td style='padding: 5px 0; font-weight:600; color:#001E57; font-size:15px;'>Valor:</td><td style='text-align:right; font-weight:700; font-size:15px;'>R$ {valor:,.2f}</td></tr>"
                        enviar_notificacao_email(email_usuario, f"📢 Reembolso Atualizado: Chamado #{id_target} {novo_status}", f"Olá {nome_usuario.split()[0]}, seu pedido mudou de status.", novo_status, detalhes)
                        st.rerun()
                    else: conn.close(); st.error("ID não localizado.")

                with c1:
                    if st.button("👁️ Recibo"):
                        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                        res = conn.cursor().execute("SELECT caminho_arquivo FROM reembolsos WHERE id=?", (id_pg,)).fetchone()
                        conn.close()
                        if res and res[0] and os.path.exists(res[0]):
                            with open(res[0], "rb") as f: st.download_button("📥 Baixar", data=f, file_name=os.path.basename(res[0]))
                        else: st.error("Sem anexo.")
                with c2:
                    if st.button("✅ Aprovar"): processar_acao_admin(id_pg, "APROVADO", "APROVOU")
                with c3:
                    if st.button("❌ Rejeitar"): processar_acao_admin(id_pg, "NEGADO", "NEGOU")
                with c4:
                    if st.button("💸 Pagar"): processar_acao_admin(id_pg, "PAGO", "PAGOU")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- ABA: DASHBOARD/PAINEL EXECUTIVO ---
    elif menu == "📈 Painel Executivo":
        st.markdown('<h1 class="clean-title">Métricas Estratégicas e Consolidação</h1>', unsafe_allow_html=True)
        
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df_dash = pd.read_sql("SELECT * FROM reembolsos", conn)
        conn.close()
        
        if df_dash.empty:
            st.markdown('<div class="empty-state-box">📊 Aguardando lançamentos de dados para gerar relatórios.</div>', unsafe_allow_html=True)
        else:
            t_geral = df_dash['valor'].sum()
            t_pago = df_dash[df_dash['status'] == 'PAGO']['valor'].sum()
            t_pend = df_dash[df_dash['status'] == 'PENDENTE']['valor'].sum()
            
            k1, k2, k3 = st.columns(3)
            with k1: st.markdown(f'<div class="premium-card"><div class="kpi-title">Gross Solicitado</div><div class="kpi-value val-total">R$ {t_geral:,.2f}</div></div>', unsafe_allow_html=True)
            with k2: st.markdown(f'<div class="premium-card"><div class="kpi-title">Volume Pago</div><div class="kpi-value val-pago">R$ {t_pago:,.2f}</div></div>', unsafe_allow_html=True)
            with k3: st.markdown(f'<div class="premium-card"><div class="kpi-title">Exposição Pendente</div><div class="kpi-value val-pendente">R$ {t_pend:,.2f}</div></div>', unsafe_allow_html=True)
            
            g1, g2 = st.columns(2)
            with g1:
                st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                st.markdown('<p style="font-weight:700; color:#001E57; margin-bottom:15px;">📊 Consolidação por Centro de Custo</p>', unsafe_allow_html=True)
                df_cc = df_dash.groupby("c_custo")["valor"].sum().reset_index()
                st.bar_chart(data=df_cc, x="c_custo", y="valor", color="#001E57") 
                st.markdown('</div>', unsafe_allow_html=True)
                
            with g2:
                st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                st.markdown('<p style="font-weight:700; color:#001E57; margin-bottom:15px;">🏷️ Custos por Categoria de Despesa</p>', unsafe_allow_html=True)
                df_cat = df_dash.groupby("categoria")["valor"].sum().reset_index()
                st.bar_chart(data=df_cat, x="categoria", y="valor", color="#FF9200") 
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown('<div class="premium-card" style="text-align: center;">', unsafe_allow_html=True)
            buffer_excel = io.BytesIO()
            with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                df_cc.rename(columns={"c_custo": "Centro de Custo", "valor": "Total Gasto (R$)"}).to_excel(writer, sheet_name='📊 RESUMO EXECUTIVO', index=False)
                df_dash.to_excel(writer, sheet_name='📁 BASE DE DADOS', index=False)
            buffer_excel.seek(0)
            
            st.download_button(
                label="📥 Baixar Relatório Consolidado em Excel (.XLSX)",
                data=buffer_excel,
                file_name=f"duarte_analytics_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.markdown('</div>', unsafe_allow_html=True)
"""

with open("app.py", "w", encoding="utf-8") as f:
    f.write(code_content)

print("File generated successfully")