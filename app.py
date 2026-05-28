import streamlit as st
import pandas as pd
import sqlite3
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL E PASTAS ---
if not os.path.exists("comprovantes"): 
    os.makedirs("comprovantes")

st.set_page_config(page_title="Duarte Reembolsos", layout="wide")

# --- INJEÇÃO DE ESTILE CSS (VISUAL PRELIMINAR) ---
st.markdown("""
    <style>
        div.stButton > button {
            border-radius: 8px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        button:contains("✅") { background-color: #2ecc71 !important; color: white !important; border: none; }
        button:contains("❌") { background-color: #e74c3c !important; color: white !important; border: none; }
        button:contains("💸") { background-color: #3498db !important; color: white !important; border: none; }
        .stDataFrame { border: 1px solid #34495e; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

DB_PATH = "reembolso.db"
DB_TIMEOUT = 30.0

# --- CREDENCIAIS DE E-MAIL ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "financeiro.duartegestao@gmail.com"
SMTP_PASS = "rotrhqmtmdbundgu"

# --- FUNÇÃO DISPARO DE E-MAIL ---
def enviar_email_notificacao(email_destino, nome_funcionario, id_pedido, despesa, valor, status_novo):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = email_destino
        msg['Subject'] = f"📢 STATUS DE REEMBOLSO: {status_novo} - DUARTE GESTÃO (PEDIDO #{id_pedido})"
        
        corpo = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">Olá, {nome_funcionario}!</h2>
                <p>O departamento financeiro atualizou o andamento do seu pedido de reembolso.</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>ID do Pedido:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">#{id_pedido}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Despesa:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{despesa}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Valor:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">R$ {valor:.2f}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Novo Status:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong style="color: #e67e22;">{status_novo}</strong></td></tr>
                </table>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #7f8c8d; text-align: center;">Este é um disparo automático do ERP Duarte Gestão Reembolsos.</p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(corpo, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, email_destino, msg.as_string())
        server.quit()
        return True, "Sucesso"
    except Exception as e:
        return False, str(e)

# --- FUNÇÕES DE BANCO DE DADOS ---
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
    
    adms_atualizados = [
        ('admin', 'Duarte1234#', 'financeiro.duartegestao@gmail.com', 'admin', 'ADMINISTRADOR PRINCIPAL', '000.000.000-00', '(00) 00000-0000'),
        ('operacional', 'Duarte1234#', 'financeiro.duartegestao@gmail.com', 'admin', 'OPERACIONAL ADMINISTRATIVO', '000.000.000-00', '(00) 00000-0000'),
        ('financeiro', 'Duarte1234#', 'financeiro.duartegestao@gmail.com', 'admin', 'FINANCEIRO DIRETORIA', '000.000.000-00', '(00) 00000-0000')
    ]
    for u in adms_atualizados:
        cursor.execute("INSERT OR REPLACE INTO usuarios VALUES (?,?,?,?,?,?,?)", u)
    conn.commit()
    conn.close()

def registrar_log(user, acao):
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (usuario_acao, acao, data_hora) VALUES (?,?,?)", (user, acao, datetime.now()))
    conn.commit()
    conn.close()

inicializar_banco()

# --- CONTROLE DE SESSÃO ---
if "logado" not in st.session_state: 
    st.session_state["logado"] = False

# --- INTERFACE DE ACESSO ---
if not st.session_state["logado"]:
    st.title("🔐 DUARTE REEMBOLSOS - ACESSO CONTÁBIL")
    tab1, tab2 = st.tabs(["ENTRAR NO SISTEMA", "CADASTRAR NOVO FUNCIONÁRIO"])
    
    with tab1:
        u = st.text_input("USUÁRIO", key="login_u")
        p = st.text_input("SENHA", type="password", key="login_p")
        if st.button("ENTRAR"):
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, p))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                st.session_state["logado"] = True
                st.session_state["user_info"] = {"user": user[0], "nivel": user[3], "nome": user[4]}
                registrar_log(user[0], "LOGIN NO SISTEMA SUCESSO")
                st.rerun()
            else: st.error("USUÁRIO OU SENHA INVÁLIDOS!")
            
    with tab2:
        st.subheader("📝 FORMULÁRIO DE CADASTRO")
        with st.form("cadastro_novo", clear_on_submit=True):
            new_u = st.text_input("ESCOLHA SEU USUÁRIO (LOGIN)")
            new_p = st.text_input("ESCOLHA UMA SENHA", type="password")
            new_nome = st.text_input("NOME COMPLETO")
            new_cpf = st.text_input("CPF")
            new_tel = st.text_input("TELEFONE DE CONTATO")
            new_e = st.text_input("E-MAIL REAL (PARA RECEBER NOTIFICAÇÃO)")
            
            if st.form_submit_button("CADASTRAR FUNCIONÁRIO"):
                if new_u and new_p and new_nome and new_cpf and new_e:
                    try:
                        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO usuarios VALUES (?,?,?,?,?,?,?)", 
                                       (new_u, new_p, new_e, 'usuario', new_nome, new_cpf, new_tel))
                        conn.commit()
                        conn.close()
                        registrar_log("SISTEMA", f"NOVO FUNCIONARIO CADASTRADO: {new_u}")
                        st.success("CADASTRO REALIZADO COM SUCESSO!")
                    except sqlite3.IntegrityError: st.error("ESTE NOME DE USUÁRIO JÁ ESTÁ EM USO!")
                else: st.warning("PREENCHA TODOS OS CAMPOS OBRIGATÓRIOS!")

else:
    # --- ÁREA INTERNA ---
    st.sidebar.title(f"👤 {st.session_state['user_info']['nome']}")
    st.sidebar.write(f"Nível de Acesso: **{st.session_state['user_info']['nivel'].upper()}**")
    
    opcoes_menu = ["💸 SOLICITAR REEMBOLSO", "📋 MEUS PEDIDOS"]
    if st.session_state['user_info']['nivel'] == 'admin':
        opcoes_menu.append("📊 PAINEL ADMIN")
        opcoes_menu.append("📈 DASHBOARD")  # Nova aba adicionada aqui!
        
    menu = st.sidebar.radio("NAVEGAÇÃO", opcoes_menu)
    
    if st.sidebar.button("SAIR DO SISTEMA"): 
        registrar_log(st.session_state['user_info']['user'], "LOGOUT DO SISTEMA")
        st.session_state["logado"] = False; st.rerun()

    # --- MENU 1: SOLICITAR ---
    if menu == "💸 SOLICITAR REEMBOLSO":
        st.title("💸 NOVA SOLICITAÇÃO DE REEMBOLSO")
        with st.form("solicitar_reembolso", clear_on_submit=True):
            desc = st.text_input("DESCRIÇÃO DA DESPESA")
            cat = st.selectbox("CATEGORIA", ["LIMPEZA", "REMUNERAÇÃO SÓCIOS", "ALIMENTAÇÃO", "TELEFONIA E INTERNET", "SOFTWARE E LICENÇAS - INFORMÁTICA", "TRANSPORTES / LOGÍSTICA", "MATERIAL DE ESCRITÓRIO", "EQUIPAMENTOS DE INFORMÁTICA", "ESTACIONAMENTO", "MÓVEIS E UTENSÍLIOS", "DESPESAS DE VIAGENS", "MÁQUINAS E EQUIPAMENTOS"])
            cc = st.selectbox("CENTRO DE CUSTO", ["CREDENCIAMENTO", "REDE", "DIRETORIA", "DUARTE GESTÃO", "MARKETING", "FINANCEIRO"])
            val = st.number_input("VALOR TOTAL (R$)", min_value=0.01, step=0.01)
            arquivo = st.file_uploader("ANEXAR COMPROVANTE FISCAL", type=['jpg', 'png', 'pdf'])
            
            if st.form_submit_button("ENVIAR SOLICITAÇÃO"):
                if desc and val > 0:
                    caminho_salvo = ""
                    if arquivo:
                        caminho_salvo = f"comprovantes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{arquivo.name}"
                        with open(caminho_salvo, "wb") as f: f.write(arquivo.getbuffer())
                    
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO reembolsos (usuario, despesa, categoria, c_custo, valor, status, data, caminho_arquivo) VALUES (?,?,?,?,?,?,?,?)", 
                                   (st.session_state['user_info']['user'], desc, cat, cc, val, 'PENDENTE', datetime.now().date(), caminho_salvo))
                    conn.commit()
                    conn.close()
                    registrar_log(st.session_state['user_info']['user'], f"SOLICITOU REEMBOLSO DE R$ {val:.2f} ({cc})")
                    st.success("SOLICITAÇÃO ENVIADA COM SUCESSO!")
                else: st.error("DADOS DE SOLICITAÇÃO INVÁLIDOS!")

    # --- MENU 2: HISTÓRICO ---
    elif menu == "📋 MEUS PEDIDOS":
        st.title("📋 MEU HISTÓRICO DE SOLICITAÇÕES")
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df_meus = pd.read_sql(f"SELECT id, despesa, categoria, c_custo, valor, status, data FROM reembolsos WHERE usuario='{st.session_state['user_info']['user']}' ORDER BY id DESC", conn)
        conn.close()
        if df_meus.empty: st.info("Nenhuma solicitação encontrada para o seu perfil.")
        else: st.dataframe(df_meus, use_container_width=True)

    # --- MENU 3: PAINEL ADMIN ---
    elif menu == "📊 PAINEL ADMIN":
        if st.session_state['user_info']['nivel'] == 'admin':
            st.title("📊 PAINEL DE GESTÃO E AUDITORIA GLOBAL")
            
            with st.expander("🕒 LOGS DE AUDITORIA"):
                conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                df_logs = pd.read_sql("SELECT * FROM logs ORDER BY data_hora DESC", conn)
                conn.close()
                st.dataframe(df_logs, use_container_width=True)
            
            st.subheader("📋 REQUISIÇÕES EM ABERTO / HISTÓRICO COMPLETO")
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            df_todos = pd.read_sql("SELECT * FROM reembolsos ORDER BY id DESC", conn)
            conn.close()
            st.dataframe(df_todos, use_container_width=True)
            
            st.markdown("---")
            id_pg = st.number_input("DIGITE O ID DA SOLICITAÇÃO PARA FAZER A OPERAÇÃO:", min_value=1, step=1)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("👁️ VER COMPROVANTE", use_container_width=True):
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    cursor = conn.cursor()
                    res = cursor.execute("SELECT caminho_arquivo FROM reembolsos WHERE id=?", (id_pg,)).fetchone()
                    conn.close()
                    if res and res[0] and os.path.exists(res[0]):
                        with open(res[0], "rb") as file:
                            st.download_button("BAIXAR COMPROVANTE", data=file, file_name=os.path.basename(res[0]), use_container_width=True)
                    else: st.error("COMPROVANTE NÃO LOCALIZADO!")
                        
            with col2:
                if st.button("✅ APROVAR PEDIDO", use_container_width=True):
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    cursor = conn.cursor()
                    pedido = cursor.execute("SELECT r.id, u.email, u.nome_completo, r.despesa, r.valor FROM reembolsos r JOIN usuarios u ON r.usuario = u.usuario WHERE r.id=?", (id_pg,)).fetchone()
                    if pedido:
                        cursor.execute("UPDATE reembolsos SET status='APROVADO' WHERE id=?", (id_pg,))
                        conn.commit()
                        conn.close()
                        registrar_log(st.session_state['user_info']['user'], f"APROVOU SOLICITACAO ID {id_pg}")
                        envio_ok, msg_log = enviar_email_notificacao(pedido[1], pedido[2], pedido[0], pedido[3], pedido[4], "APROVADO")
                        st.rerun()
                    else: conn.close(); st.error("ID DE PEDIDO INEXISTENTE!")
                        
            with col3:
                if st.button("❌ NEGAR PEDIDO", use_container_width=True):
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    cursor = conn.cursor()
                    pedido = cursor.execute("SELECT r.id, u.email, u.nome_completo, r.despesa, r.valor FROM reembolsos r JOIN usuarios u ON r.usuario = u.usuario WHERE r.id=?", (id_pg,)).fetchone()
                    if pedido:
                        cursor.execute("UPDATE reembolsos SET status='NEGADO' WHERE id=?", (id_pg,))
                        conn.commit()
                        conn.close()
                        registrar_log(st.session_state['user_info']['user'], f"NEGOU SOLICITACAO ID {id_pg}")
                        envio_ok, msg_log = enviar_email_notificacao(pedido[1], pedido[2], pedido[0], pedido[3], pedido[4], "NEGADO")
                        st.rerun()
                    else: conn.close(); st.error("ID DE PEDIDO INEXISTENTE!")
                        
            with col4:
                if st.button("💸 MARCAR COMO PAGO", use_container_width=True):
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    cursor = conn.cursor()
                    pedido = cursor.execute("SELECT r.id, u.email, u.nome_completo, r.despesa, r.valor FROM reembolsos r JOIN usuarios u ON r.usuario = u.usuario WHERE r.id=?", (id_pg,)).fetchone()
                    if pedido:
                        cursor.execute("UPDATE reembolsos SET status='PAGO' WHERE id=?", (id_pg,))
                        conn.commit()
                        conn.close()
                        registrar_log(st.session_state['user_info']['user'], f"PAGOU SOLICITACAO ID {id_pg}")
                        envio_ok, msg_log = enviar_email_notificacao(pedido[1], pedido[2], pedido[0], pedido[3], pedido[4], "PAGO")
                        st.rerun()
                    else: conn.close(); st.error("ID DE PEDIDO INEXISTENTE!")

    # --- MENU 4: DASHBOARD (NOVO!) ---
    elif menu == "📈 DASHBOARD":
        st.title("📈 DASHBOARD DE GESTÃO E ANALYTICS")
        
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df_dash = pd.read_sql("SELECT * FROM reembolsos", conn)
        conn.close()
        
        if df_dash.empty:
            st.info("Nenhum dado de reembolso localizado para gerar os gráficos ainda.")
        else:
            # Indicadores Principais (Cards)
            total_geral = df_dash['valor'].sum()
            total_pago = df_dash[df_dash['status'] == 'PAGO']['valor'].sum()
            total_pendente = df_dash[df_dash['status'] == 'PENDENTE']['valor'].sum()
            
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Total Solicitado Histórico", f"R$ {total_geral:,.2f}")
            kpi2.metric("Total Pago à Equipe ✅", f"R$ {total_pago:,.2f}")
            kpi3.metric("Aguardando Análise (Pendente) ⏳", f"R$ {total_pendente:,.2f}")
            
            st.markdown("---")
            
            # Divisão em duas colunas de gráficos
            g1, g2 = st.columns(2)
            
            with g1:
                st.subheader("📊 Gastos por Centro de Custo")
                df_cc = df_dash.groupby("c_custo")["valor"].sum().reset_index()
                st.bar_chart(data=df_cc, x="c_custo", y="valor")
                
            with g2:
                st.subheader("🏷️ Gastos por Categoria de Despesa")
                df_cat = df_dash.groupby("categoria")["valor"].sum().reset_index()
                st.bar_chart(data=df_cat, x="categoria", y="valor")
                
            st.markdown("---")
            st.subheader("📥 Exportação de Dados para Auditoria")
            
            # Geração do arquivo CSV para download
            csv_data = df_dash.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 EXPORTAR PLANILHA COMPLETA (.CSV)",
                data=csv_data,
                file_name=f"duarte_gestao_reembolsos_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )