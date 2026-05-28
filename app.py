import streamlit as st
import pandas as pd
import sqlite3
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
if not os.path.exists("comprovantes"): 
    os.makedirs("comprovantes")

st.set_page_config(page_title="Duarte Gestão Analytics", layout="wide", initial_sidebar_state="expanded")

# --- 🚀 ARSENAL DE ESTILIZAÇÃO E ANIMAÇÃO CSS MONSTRO 🚀 ---
st.markdown("""
    <style>
        /* Importação de Fonte High-Tech */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
        
        * { font-family: 'Inter', sans-serif; }

        /* Fundo Geral do App - Dark Obsidian Space */
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at 50% 30%, #151824 0%, #090a0f 100%) !important;
            color: #ffffff !important;
        }
        
        /* Sidebar Estilo Cyber-Control */
        [data-testid="stSidebar"] {
            background-color: #0d0f17 !important;
            border-right: 2px solid rgba(0, 242, 254, 0.1) !important;
        }

        /* Títulos Principais Neon */
        .neon-title {
            font-size: 38px !important;
            font-weight: 800 !important;
            background: linear-gradient(45deg, #00f2fe, #4facfe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 25px;
            animation: pulseGlow 3s infinite ease-in-out;
        }

        /* Painel Glassmorphism (Efeito Vidro de Luxo para BI) */
        .bi-card {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border-radius: 16px !important;
            padding: 24px !important;
            border: 1px solid rgba(255, 255, 255, 0.07) !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4) !important;
            transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
            margin-bottom: 20px;
        }
        .bi-card:hover {
            transform: translateY(-5px) !important;
            border-color: rgba(0, 242, 254, 0.4) !important;
            box-shadow: 0 12px 40px 0 rgba(0, 242, 254, 0.15) !important;
        }

        /* KPIS Dinâmicos Customizados */
        .kpi-val { font-size: 34px !important; font-weight: 800 !important; margin-top: 5px; }
        .kpi-solicitado { color: #00f2fe !important; text-shadow: 0 0 15px rgba(0, 242, 254, 0.4); }
        .kpi-pago { color: #00ff87 !important; text-shadow: 0 0 15px rgba(0, 255, 135, 0.4); }
        .kpi-pendente { color: #febf00 !important; text-shadow: 0 0 15px rgba(254, 191, 0, 0.4); }

        /* Botões Mutantes e Ultra-Reativos */
        div.stButton > button {
            width: 100% !important;
            background: linear-gradient(135deg, #1f2438 0%, #0d0f17 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            padding: 14px 20px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        }
        div.stButton > button:hover {
            transform: scale(1.03) !important;
            color: #ffffff !important;
            border-color: #00f2fe !important;
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.3) !important;
        }

        /* Botões de Ação Crítica com Cores Customizadas de Alta Intensidade */
        button:contains("✅") { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important; color: white !important; border: none !important; }
        button:contains("❌") { background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%) !important; color: white !important; border: none !important; }
        button:contains("💸") { background: linear-gradient(135deg, #7f00ff 0%, #e100ff 100%) !important; color: white !important; border: none !important; }
        button:contains("📥") { background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%) !important; color: white !important; border: none !important; }

        /* Estilização Avançada de Tabelas/Dataframes */
        .stDataFrame {
            background: rgba(13, 15, 23, 0.7) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 14px !important;
            padding: 10px;
        }

        /* Animações Keyframe */
        @keyframes pulseGlow {
            0% { filter: drop-shadow(0 0 2px rgba(0,242,254,0.2)); }
            50% { filter: drop-shadow(0 0 12px rgba(0,242,254,0.5)); }
            100% { filter: drop-shadow(0 0 2px rgba(0,242,254,0.2)); }
        }
    </style>
""", unsafe_allow_html=True)

DB_PATH = "reembolso.db"
DB_TIMEOUT = 30.0

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = "financeiro.duartegestao@gmail.com"
SMTP_PASS = "rotrhqmtmdbundgu"

def enviar_email_notificacao(email_destino, nome_funcionario, id_pedido, despesa, valor, status_novo):
    if not email_destino or "@" not in email_destino:
        return False, "E-mail inválido."
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = email_destino
        msg['Subject'] = f"📢 STATUS DE REEMBOLSO: {status_novo} - DUARTE GESTÃO"
        corpo = f"Olá {nome_funcionario}, o pedido #{id_pedido} de R$ {valor:.2f} foi alterado para {status_novo}."
        msg.attach(MIMEText(corpo, 'plain'))
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10)
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, email_destino, msg.as_string())
        server.quit()
        return True, "Sucesso"
    except Exception as e:
        return False, str(e)

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

# --- TELA DE ACESSO CYBERPUNK ---
if not st.session_state["logado"]:
    st.markdown('<h1 class="neon-title">⚡ DUARTE GESTÃO - ACESSO INTEGRADO</h1>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔒 ENTRAR NO SISTEMA", "📝 CADASTRAR FUNCIONÁRIO"])
    
    with tab1:
        st.markdown('<div class="bi-card">', unsafe_allow_html=True)
        u = st.text_input("USUÁRIO")
        p = st.text_input("SENHA", type="password")
        if st.button("ENTRAR NA REDE"):
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            user = conn.cursor().execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, p)).fetchone()
            conn.close()
            if user:
                st.session_state["logado"] = True
                st.session_state["user_info"] = {"user": user[0], "nivel": user[3], "nome": user[4]}
                registrar_log(user[0], "LOGIN SUCESSO")
                st.rerun()
            else: st.error("CREDENCIAIS INCORRETAS")
        st.markdown('</div>', unsafe_allow_html=True)
            
    with tab2:
        st.markdown('<div class="bi-card">', unsafe_allow_html=True)
        with st.form("cad_form", clear_on_submit=True):
            nu = st.text_input("LOGIN USUÁRIO")
            np = st.text_input("SENHA DE ACESSO", type="password")
            nn = st.text_input("NOME COMPLETO")
            nc = st.text_input("CPF")
            nt = st.text_input("TELEFONE")
            ne = st.text_input("E-MAIL COMPATIVEL")
            if st.form_submit_button("REGISTRAR NA BASE"):
                if nu and np and nn and ne:
                    try:
                        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                        conn.cursor().execute("INSERT INTO usuarios VALUES (?,?,?,?,?,?,?)", (nu, np, ne, 'usuario', nn, nc, nt))
                        conn.commit(); conn.close()
                        st.success("FUNCIONÁRIO CADASTRADO!")
                    except: st.error("MIGRATION ERROR: USUÁRIO JÁ EXISTENTE")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- INTERFACE INTERNA EXECUTIVE ---
    st.sidebar.markdown(f'<div style="padding:10px; border-left:3px solid #00f2fe; margin-bottom:20px;">'
                        f'<h3 style="margin:0; color:#fff;">{st.session_state["user_info"]["nome"]}</h3>'
                        f'<span style="color:#00f2fe; font-size:12px; font-weight:bold;">NÍVEL: {st.session_state["user_info"]["nivel"].upper()}</span>'
                        f'</div>', unsafe_allow_html=True)
    
    opcoes = ["💸 SOLICITAR REEMBOLSO", "📋 MEUS PEDIDOS"]
    if st.session_state['user_info']['nivel'] == 'admin':
        opcoes += ["📊 PAINEL ADMIN", "📈 DASHBOARD EXECUTIVE"]
        
    menu = st.sidebar.radio("SISTEMA DE NAVEGAÇÃO", opcoes)
    
    if st.sidebar.button("❌ DESCONECTAR DA SESSÃO"):
        st.session_state["logado"] = False; st.rerun()

    # --- NOVO LANÇAMENTO ---
    if menu == "💸 SOLICITAR REEMBOLSO":
        st.markdown('<h1 class="neon-title">💸 ENTRADA DE NOVA SOLICITAÇÃO</h1>', unsafe_allow_html=True)
        st.markdown('<div class="bi-card">', unsafe_allow_html=True)
        with st.form("reembolso_form", clear_on_submit=True):
            desc = st.text_input("DESCRIÇÃO DETALHADA DA OPERAÇÃO")
            cat = st.selectbox("CATEGORIA GESTÃO", ["LIMPEZA", "REMUNERAÇÃO SÓCIOS", "ALIMENTAÇÃO", "TELEFONIA E INTERNET", "SOFTWARE E LICENÇAS - INFORMÁTICA", "TRANSPORTES / LOGÍSTICA", "MATERIAL DE ESCRITÓRIO", "EQUIPAMENTOS DE INFORMÁTICA", "ESTACIONAMENTO", "MÓVEIS E UTENSÍLIOS", "DESPESAS DE VIAGENS", "MÁQUINAS E EQUIPAMENTOS"])
            cc = st.selectbox("CENTRO DE CUSTO PLANO", ["CREDENCIAMENTO", "REDE", "DIRETORIA", "DUARTE GESTÃO", "MARKETING", "FINANCEIRO"])
            val = st.number_input("VALOR EXATO NOMINAL (R$)", min_value=0.01, step=0.01)
            arq = st.file_uploader("UPLOAD COMPROVANTE FISCAL DIRETAL", type=['jpg', 'png', 'pdf'])
            
            if st.form_submit_button("💸 PROTOCOLAR SOLICITAÇÃO"):
                if desc and val > 0:
                    path = f"comprovantes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{arq.name}" if arq else ""
                    if arq:
                        with open(path, "wb") as f: f.write(arq.getbuffer())
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    conn.cursor().execute("INSERT INTO reembolsos (usuario, despesa, categoria, c_custo, valor, status, data, caminho_arquivo) VALUES (?,?,?,?,?,?,?,?)", 
                                   (st.session_state['user_info']['user'], desc, cat, cc, val, 'PENDENTE', datetime.now().date(), path))
                    conn.commit(); conn.close()
                    st.success("LANÇAMENTO REALIZADO COM SUCESSO!")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- HISTÓRICO ---
    elif menu == "📋 MEUS PEDIDOS":
        st.markdown('<h1 class="neon-title">📋 MINHAS SOLICITAÇÕES EM CURSO</h1>', unsafe_allow_html=True)
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df = pd.read_sql(f"SELECT id, despesa, categoria, c_custo, valor, status, data FROM reembolsos WHERE usuario='{st.session_state['user_info']['user']}' ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(df, use_container_width=True)

    # --- CONTROLADORA GLOBAL ADMIN ---
    elif menu == "📊 PAINEL ADMIN":
        st.markdown('<h1 class="neon-title">📊 CONTROLADORA DE REQUISIÇÕES GLOBAL</h1>', unsafe_allow_html=True)
        
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df_todos = pd.read_sql("SELECT * FROM reembolsos ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(df_todos, use_container_width=True)
        
        st.markdown('<div class="bi-card">', unsafe_allow_html=True)
        st.subheader("🕹️ TERMINAL DE DECISÃO INTEGRADA")
        id_pg = st.number_input("DIGITE O ID DO PROCESSO ALVO:", min_value=1, step=1)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("👁️ EXAMINAR DOCUMENTO"):
                conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                res = conn.cursor().execute("SELECT caminho_arquivo FROM reembolsos WHERE id=?", (id_pg,)).fetchone()
                conn.close()
                if res and res[0] and os.path.exists(res[0]):
                    with open(res[0], "rb") as f: st.download_button("BAIXAR ANEXO", data=f, file_name=os.path.basename(res[0]))
                else: st.error("NENHUM COMPROVANTE PROTOCOLADO")
        
        # Estrutura de ações limpas sem travar a interface
        def processar_acao(id_target, novo_status, log_msg):
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            cursor = conn.cursor()
            pedido = cursor.execute("SELECT r.id, u.email, u.nome_completo, r.despesa, r.valor FROM reembolsos r JOIN usuarios u ON r.usuario = u.usuario WHERE r.id=?", (id_target,)).fetchone()
            if pedido:
                cursor.execute("UPDATE reembolsos SET status=? WHERE id=?", (novo_status, id_target))
                conn.commit(); conn.close()
                registrar_log(st.session_state['user_info']['user'], f"{log_msg} ID {id_target}")
                enviar_email_notificacao(pedido[1], pedido[2], pedido[0], pedido[3], pedido[4], novo_status)
                st.rerun()
            else: conn.close(); st.error("PROCESSO NÃO LOCALIZADO")

        with c2:
            if st.button("✅ APROVAR PEDIDO"): processar_acao(id_pg, "APROVADO", "APROVOU")
        with c3:
            if st.button("❌ REJEITAR SOLICITAÇÃO"): processar_acao(id_pg, "NEGADO", "NEGOU")
        with c4:
            if st.button("💸 EFETUAR LIQUIDAÇÃO"): processar_acao(id_pg, "PAGO", "PAGOU")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 📈 DASHBOARD BI EXECUTIVE (A JOIA DA COROA) ---
    elif menu == "📈 DASHBOARD EXECUTIVE":
        st.markdown('<h1 class="neon-title">📈 DUARTE BUSINESS INTELLIGENCE METRICS</h1>', unsafe_allow_html=True)
        
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df_dash = pd.read_sql("SELECT * FROM reembolsos", conn)
        conn.close()
        
        if df_dash.empty:
            st.info("DATASTREAM COMPARTILHADO SEM ENTRADAS RELEVANTES ATÉ O MOMENTO.")
        else:
            t_geral = df_dash['valor'].sum()
            t_pago = df_dash[df_dash['status'] == 'PAGO']['valor'].sum()
            t_pend = df_dash[df_dash['status'] == 'PENDENTE']['valor'].sum()
            
            # Cards customizados estilo BI corporativo avançado
            k1, k2, k3 = st.columns(3)
            with k1:
                st.markdown(f'<div class="bi-card">'
                            f'<div style="color:#8f9cae; font-size:12px; font-weight:600; text-transform:uppercase;">Gross Solicitado Histórico</div>'
                            f'<div class="kpi-val kpi-solicitado">R$ {t_geral:,.2f}</div>'
                            f'</div>', unsafe_allow_html=True)
            with k2:
                st.markdown(f'<div class="bi-card">'
                            f'<div style="color:#8f9cae; font-size:12px; font-weight:600; text-transform:uppercase;">Volume Total Liquidado</div>'
                            f'<div class="kpi-val kpi-pago">R$ {t_pago:,.2f}</div>'
                            f'</div>', unsafe_allow_html=True)
            with k3:
                st.markdown(f'<div class="bi-card">'
                            f'<div style="color:#8f9cae; font-size:12px; font-weight:600; text-transform:uppercase;">Exposição em Análise (Pendente)</div>'
                            f'<div class="kpi-val kpi-pendente">R$ {t_pend:,.2f}</div>'
                            f'</div>', unsafe_allow_html=True)
            
            # Linha de Relatórios Gráficos Avançados
            g1, g2 = st.columns(2)
            with g1:
                st.markdown('<div class="bi-card">', unsafe_allow_html=True)
                st.markdown('<p style="font-weight:700; color:#fff; margin-bottom:15px;">📊 MATRIZ POR CENTRO DE CUSTO</p>', unsafe_allow_html=True)
                df_cc = df_dash.groupby("c_custo")["valor"].sum().reset_index()
                st.bar_chart(data=df_cc, x="c_custo", y="valor", color="#00f2fe")
                st.markdown('</div>', unsafe_allow_html=True)
                
            with g2:
                st.markdown('<div class="bi-card">', unsafe_allow_html=True)
                st.markdown('<p style="font-weight:700; color:#fff; margin-bottom:15px;">🏷️ DISTRIBUIÇÃO POR CATEGORIA DE DESPESA</p>', unsafe_allow_html=True)
                df_cat = df_dash.groupby("categoria")["valor"].sum().reset_index()
                st.bar_chart(data=df_cat, x="categoria", y="valor", color="#7f00ff")
                st.markdown('</div>', unsafe_allow_html=True)
                
            # Área de Exportação Rápida
            st.markdown('<div class="bi-card" style="text-align:center;">', unsafe_allow_html=True)
            csv = df_dash.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 EXPORTAR COMPILADO ANALÍTICO PARA AUDITORIA (.CSV)",
                data=csv,
                file_name=f"duarte_analytics_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            st.markdown('</div>', unsafe_allow_html=True)