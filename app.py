import streamlit as st
import pandas as pd
import sqlite3
import os
import smtplib
import io
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
if not os.path.exists("comprovantes"): 
    os.makedirs("comprovantes")

st.set_page_config(page_title="Duarte Gestão - Sistema Financeiro", layout="wide", initial_sidebar_state="expanded")

# --- 🎯 ARSENAL CSS: CLEAN, PREMIUM & ANIMADO 🎯 ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        
        * { font-family: 'Plus Jakarta Sans', sans-serif; }

        /* Fundo Limpo e Elegante */
        [data-testid="stAppViewContainer"] {
            background-color: #f8fafc !important;
            color: #001E57 !important;
        }
        
        /* Sidebar Total White Premium */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0 !important;
        }

        /* Títulos Corporativos */
        .clean-title {
            font-size: 32px !important;
            font-weight: 800 !important;
            color: #001E57 !important;
            letter-spacing: -0.5px;
            margin-bottom: 20px;
            animation: slideUp 0.6s ease-out;
        }

        /* Cards Estilo FinTech (Limpos com Sombras de Luxo) */
        .premium-card {
            background: #ffffff !important;
            border-radius: 16px !important;
            padding: 24px !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 4px 20px rgba(0, 30, 87, 0.03) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            margin-bottom: 20px;
            animation: slideUp 0.5s ease-out;
        }
        .premium-card:hover {
            transform: translateY(-4px) !important;
            box-shadow: 0 12px 30px rgba(0, 30, 87, 0.08) !important;
            border-color: #FF9200 !important;
        }

        /* Indicadores KPI Polidos */
        .kpi-title { color: #64748b !important; font-size: 13px !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.5px; }
        .kpi-value { font-size: 30px !important; font-weight: 800 !important; margin-top: 5px; }
        .val-total { color: #001E57 !important; }
        .val-pago { color: #10b981 !important; }
        .val-pendente { color: #FF9200 !important; }

        /* Botões Clean / Apple Style */
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
            box-shadow: 0 4px 12px rgba(255, 146, 0, 0.2) !important;
        }

        /* Botões Específicos do Painel Admin */
        button:contains("✅") { background-color: #10b981 !important; }
        button:contains("❌") { background-color: #ef4444 !important; }
        button:contains("💸") { background-color: #3b82f6 !important; }
        button:contains("📥") { background-color: #0f172a !important; }

        /* Inputs e Selectbox customizados */
        div[data-baseweb="input"], div[data-baseweb="select"] {
            border-radius: 10px !important;
            background-color: #ffffff !important;
        }

        /* Tabelas Impecáveis */
        .stDataFrame {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.01) !important;
        }

        /* Animações Fluidas */
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
""", unsafe_allow_html=True)

DB_PATH = "reembolso.db"
DB_TIMEOUT = 30.0

# --- INICIALIZAÇÃO DE BANCO E LOGS ---
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

# --- BRANDING: LOGIN DA DUARTE CONTÁBIL ---
if not st.session_state["logado"]:
    col_logo, _ = st.columns([1, 2])
    with col_logo:
        if os.path.exists("logo_4.JPG"):
            st.image("logo_4.JPG", use_container_width=True)
            
    st.markdown('<h1 class="clean-title">Portal de Gestão de Reembolsos</h1>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔐 Acessar Sistema", "📝 Novo Funcionário"])
    
    with tab1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        u = st.text_input("Usuário / Login")
        p = st.text_input("Senha Corporativa", type="password")
        if st.button("Autenticar na Nuvem"):
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            user = conn.cursor().execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, p)).fetchone()
            conn.close()
            if user:
                st.session_state["logado"] = True
                st.session_state["user_info"] = {"user": user[0], "nivel": user[3], "nome": user[4]}
                registrar_log(user[0], "LOGIN SUCESSO")
                st.rerun()
            else: st.error("Credenciais não localizadas na base.")
        st.markdown('</div>', unsafe_allow_html=True)
            
    with tab2:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        with st.form("cad_form", clear_on_submit=True):
            nu = st.text_input("Crie um Nome de Usuário")
            np = st.text_input("Defina uma Senha", type="password")
            nn = st.text_input("Nome Completo")
            nc = st.text_input("CPF")
            nt = st.text_input("Telefone Corporativo")
            ne = st.text_input("E-mail de Notificações")
            if st.form_submit_button("Finalizar Cadastro"):
                if nu and np and nn and ne:
                    try:
                        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                        conn.cursor().execute("INSERT INTO usuarios VALUES (?,?,?,?,?,?,?)", (nu, np, ne, 'usuario', nn, nc, nt))
                        conn.commit(); conn.close()
                        st.success("Funcionário registrado com sucesso!")
                    except: st.error("Este usuário já se encontra ativo no banco de dados.")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- INTERFACE INTERNA EXECUTIVE ---
    if os.path.exists("logo_4.JPG"):
        st.sidebar.image("logo_4.JPG", use_container_width=True)
        
    st.sidebar.markdown(f'<div style="padding: 12px 0; border-top: 1px solid #f1f5f9; margin-top: 10px;">'
                        f'<p style="margin:0; font-size:14px; font-weight:700; color:#001E57;">{st.session_state["user_info"]["nome"]}</p>'
                        f'<span style="color:#FF9200; font-size:11px; font-weight:600; text-transform:uppercase;">Painel: {st.session_state["user_info"]["nivel"].upper()}</span>'
                        f'</div>', unsafe_allow_html=True)
    
    opcoes = ["💸 Solicitar Reembolso", "📋 Meus Pedidos"]
    if st.session_state['user_info']['nivel'] == 'admin':
        opcoes += ["📊 Painel do Admin", "📈 Dashboard Executive"]
        
    menu = st.sidebar.radio("Navegação do Sistema", opcoes)
    
    if st.sidebar.button("🔒 Desconectar com Segurança"):
        st.session_state["logado"] = False; st.rerun()

    # --- MENU 1: NOVO REEMBOLSO ---
    if menu == "💸 Solicitar Reembolso":
        st.markdown('<h1 class="clean-title">Nova Solicitação de Reembolso</h1>', unsafe_allow_html=True)
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        with st.form("reembolso_form", clear_on_submit=True):
            desc = st.text_input("Descrição da Despesa Comercial")
            cat = st.selectbox("Categoria do Gasto", ["LIMPEZA", "REMUNERAÇÃO SÓCIOS", "ALIMENTAÇÃO", "TELEFONIA E INTERNET", "SOFTWARE E LICENÇAS - INFORMÁTICA", "TRANSPORTES / LOGÍSTICA", "MATERIAL DE ESCRITÓRIO", "EQUIPAMENTOS DE INFORMÁTICA", "ESTACIONAMENTO", "MÓVEIS E UTENSÍLIOS", "DESPESAS DE VIAGENS", "MÁQUINAS E EQUIPAMENTOS"])
            cc = st.selectbox("Centro de Custo Destino", ["CREDENCIAMENTO", "REDE", "DIRETORIA", "DUARTE GESTÃO", "MARKETING", "FINANCEIRO"])
            val = st.number_input("Valor Liquido (R$)", min_value=0.01, step=0.01)
            arq = st.file_uploader("Anexar Comprovante Digitalizado (PDF, PNG, JPG)", type=['jpg', 'png', 'pdf'])
            
            if st.form_submit_button("Protocolar Solicitação"):
                if desc and val > 0:
                    path = f"comprovantes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{arq.name}" if arq else ""
                    if arq:
                        with open(path, "wb") as f: f.write(arq.getbuffer())
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    conn.cursor().execute("INSERT INTO reembolsos (usuario, despesa, categoria, c_custo, valor, status, data, caminho_arquivo) VALUES (?,?,?,?,?,?,?,?)", 
                                   (st.session_state['user_info']['user'], desc, cat, cc, val, 'PENDENTE', datetime.now().date(), path))
                    conn.commit(); conn.close()
                    st.success("Solicitação enviada para a fila de auditoria!")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- MENU 2: MEUS PEDIDOS (REFINADO) ---
    elif menu == "📋 Meus Pedidos":
        st.markdown('<h1 class="clean-title">Acompanhamento de Solicitações</h1>', unsafe_allow_html=True)
        
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df = pd.read_sql(f"SELECT id as 'ID', despesa as 'Descrição', categoria as 'Categoria', c_custo as 'Centro de Custo', valor as 'Valor (R$)', status as 'Status', data as 'Data' FROM reembolsos WHERE usuario='{st.session_state['user_info']['user']}' ORDER BY id DESC", conn)
        conn.close()
        
        # Mini Métricas do Usuário logado para ficar "Foda"
        if not df.empty:
            m_pago = df[df['Status'] == 'PAGO']['Valor (R$)'].sum()
            m_pend = df[df['Status'] == 'PENDENTE']['Valor (R$)'].sum()
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f'<div class="premium-card"><div class="kpi-title">Meus Valores Recebidos</div><div class="kpi-value val-pago">R$ {m_pago:,.2f}</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="premium-card"><div class="kpi-title">Meus Valores em Análise</div><div class="kpi-value val-pendente">R$ {m_pend:,.2f}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<p style="font-weight:700; color:#001E57; margin-bottom:15px;">📋 Histórico Pessoal Recente</p>', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- MENU 3: PAINEL DO ADMIN (REORGANIZADO & IMPRESSIONANTE) ---
    elif menu == "📊 Painel do Admin":
        st.markdown('<h1 class="clean-title">Fila de Moderação e Auditoria Contábil</h1>', unsafe_allow_html=True)
        
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df_todos = pd.read_sql("SELECT id as 'ID', usuario as 'Funcionário', despesa as 'Descrição', categoria as 'Categoria', c_custo as 'Centro de Custo', valor as 'Valor (R$)', status as 'Status', data as 'Data Lançamento' FROM reembolsos ORDER BY id DESC", conn)
        conn.close()
        
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<p style="font-weight:700; color:#001E57; margin-bottom:15px;">🗂️ Registro Geral Interativo</p>', unsafe_allow_html=True)
        st.dataframe(df_todos, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<p style="font-weight:700; color:#001E57; margin-bottom:15px;">🕹️ Despache de Processos com 1 Clique</p>', unsafe_allow_html=True)
        
        # Layout limpo para o controle operacional
        col_id, col_actions = st.columns([1, 3])
        with col_id:
            id_pg = st.number_input("Digite o ID do Lançamento:", min_value=1, step=1)
        
        with col_actions:
            st.write("") # ajuste vertical
            st.write("") 
            c1, c2, c3, c4 = st.columns(4)
            
            def processar_acao_clean(id_target, novo_status, log_msg):
                conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                cursor = conn.cursor()
                pedido = cursor.execute("SELECT id FROM reembolsos WHERE id=?", (id_target,)).fetchone()
                if pedido:
                    cursor.execute("UPDATE reembolsos SET status=? WHERE id=?", (novo_status, id_target))
                    conn.commit(); conn.close()
                    registrar_log(st.session_state['user_info']['user'], f"{log_msg} ID {id_target}")
                    st.rerun()
                else: conn.close(); st.error("ID inválido ou inexistente.")

            with c1:
                if st.button("👁️ Ver Recibo"):
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    res = conn.cursor().execute("SELECT caminho_arquivo FROM reembolsos WHERE id=?", (id_pg,)).fetchone()
                    conn.close()
                    if res and res[0] and os.path.exists(res[0]):
                        with open(res[0], "rb") as f: st.download_button("📥 Baixar", data=f, file_name=os.path.basename(res[0]))
                    else: st.error("Sem anexo.")
            with c2:
                if st.button("✅ Aprovar"): processar_acao_clean(id_pg, "APROVADO", "APROVOU")
            with c3:
                if st.button("❌ Rejeitar"): processar_acao_clean(id_pg, "NEGADO", "NEGOU")
            with c4:
                if st.button("💸 Pagar"): processar_acao_clean(id_pg, "PAGO", "PAGOU")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- MENU 4: DASHBOARD EXECUTIVE BI ---
    elif menu == "📈 Dashboard Executive":
        st.markdown('<h1 class="clean-title">Métricas Estratégicas Integradas</h1>', unsafe_allow_html=True)
        
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df_dash = pd.read_sql("SELECT * FROM reembolsos", conn)
        conn.close()
        
        if df_dash.empty:
            st.info("Nenhuma transação efetuada para consolidar relatórios.")
        else:
            t_geral = df_dash['valor'].sum()
            t_pago = df_dash[df_dash['status'] == 'PAGO']['valor'].sum()
            t_pend = df_dash[df_dash['status'] == 'PENDENTE']['valor'].sum()
            
            # Cards de Alta Diretoria
            k1, k2, k3 = st.columns(3)
            with k1:
                st.markdown(f'<div class="premium-card"><div class="kpi-title">Gross Solicitado</div><div class="kpi-value val-total">R$ {t_geral:,.2f}</div></div>', unsafe_allow_html=True)
            with k2:
                st.markdown(f'<div class="premium-card"><div class="kpi-title">Volume Liquidado (Pago)</div><div class="kpi-value val-pago">R$ {t_pago:,.2f}</div></div>', unsafe_allow_html=True)
            with k3:
                st.markdown(f'<div class="premium-card"><div class="kpi-title">Exposição Pendente</div><div class="kpi-value val-pendente">R$ {t_pend:,.2f}</div></div>', unsafe_allow_html=True)
            
            # Gráficos com cores oficiais Duarte Contábil
            g1, g2 = st.columns(2)
            with g1:
                st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                st.markdown('<p style="font-weight:700; color:#001E57; margin-bottom:15px;">📊 Consolidação por Centro de Custo</p>', unsafe_allow_html=True)
                df_cc = df_dash.groupby("c_custo")["valor"].sum().reset_index()
                st.bar_chart(data=df_cc, x="c_custo", y="valor", color="#001E57") # Azul Oficial
                st.markdown('</div>', unsafe_allow_html=True)
                
            with g2:
                st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                st.markdown('<p style="font-weight:700; color:#001E57; margin-bottom:15px;">🏷️ Custos por Categoria de Despesa</p>', unsafe_allow_html=True)
                df_cat = df_dash.groupby("categoria")["valor"].sum().reset_index()
                st.bar_chart(data=df_cat, x="categoria", y="valor", color="#FF9200") # Laranja Oficial
                st.markdown('</div>', unsafe_allow_html=True)
                
            # Módulo de Emissão Excel Multi-Aba
            st.markdown('<div class="premium-card" style="text-align: center;">', unsafe_allow_html=True)
            st.markdown('<p style="color:#001E57; font-weight:700; margin-bottom:10px;">Exportação de Fechamento Contábil</p>', unsafe_allow_html=True)
            
            buffer_excel = io.BytesIO()
            with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                df_cc.rename(columns={"c_custo": "Centro de Custo", "valor": "Total Gasto (R$)"}).to_excel(writer, sheet_name='📊 RESUMO EXECUTIVO', index=False)
                df_dash.to_excel(writer, sheet_name='📁 BASE DE DADOS', index=False)
            buffer_excel.seek(0)
            
            st.download_button(
                label="📥 Baixar Relatório Multi-Abas em Excel (.XLSX)",
                data=buffer_excel,
                file_name=f"duarte_analytics_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.markdown('</div>', unsafe_allow_html=True)