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

# --- CONFIGURAÇÃO INICIAL DA PÁGINA ---
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

# --- 🎯 ARSENAL CSS: IDENTIDADE COMPLETA & ANIMAÇÕES ---
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

@keyframes softSlideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
tr { transition: background-color 0.2s ease !important; }
</style>
""", unsafe_allow_html=True)

DB_PATH = "reembolso.db"
DB_TIMEOUT = 30.0
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_REMETENTE = "financeiro.duartegestao@gmail.com"
EMAIL_SENHA = "zbvwzhnsjlqperfr"

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
    lista_admins = [
        ('admin', 'Duarte1234#', 'financeiro.duartegestao@gmail.com', 'admin', 'ADMINISTRADOR PRINCIPAL', '000.000.000-00', '(00) 00000-0000'),
        ('operacional', 'Duarte1234#', 'financeiro.duartegestao@gmail.com', 'admin', 'OPERACIONAL ADMINISTRATIVO', '000.000.000-00', '(00) 00000-0000'),
        ('financeiro', 'Duarte1234#', 'financeiro.duartegestao@gmail.com', 'admin', 'FINANCEIRO DIRETORIA', '000.000.000-00', '(00) 00000-0000')
    ]
    
    # 👤 LISTA DE USUÁRIOS COMUNS (Acesso Restrito)
    lista_usuarios_comuns = [
        ('15413186843', '090573', 'diretoria@duartegestao.com.br', 'usuario', 'Cristiane A Duarte', '15413186843', '11959353330'),
        ('26218440818', 'Bb240977*', 'bethania.duarte@duartegestao.com.br', 'usuario', 'Bethania Duarte', '26218440818', '11949957937')
    ]

    for u in lista_admins + lista_usuarios_comuns: 
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
                    path = f"comprovantes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{arq.name}" if arq else ""
                    if arq:
                        with open(path, "wb") as f: f.write(arq.getbuffer())
                    
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
        df_completo = pd.read_sql(f"SELECT id as 'ID', despesa as 'Descrição', categoria as 'Categoria', c_custo as 'Centro de Custo', valor as 'Valor (R$)', status as 'Status', data as 'Data', caminho_arquivo FROM reembolsos WHERE usuario='{st.session_state['user_info']['user']}' ORDER BY id DESC", conn)
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
                                if caminho_atual and os.path.exists(caminho_atual):
                                    try: os.remove(caminho_atual)
                                    except: pass
                                caminho_atual = f"comprovantes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{novo_arq.name}"
                                with open(caminho_atual, "wb") as f: f.write(novo_arq.getbuffer())
                            
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

        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df_todos = pd.read_sql("SELECT id as 'ID', usuario as 'Funcionário', despesa as 'Descrição', categoria as 'Categoria', c_custo as 'Centro de Custo', valor as 'Valor (R$)', status as 'Status', data as 'Data Lançamento', caminho_arquivo FROM reembolsos ORDER BY id DESC", conn)
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
                usuario_dono = row_sel['Funcionário']

                conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                dados_func = conn.cursor().execute("SELECT nome_completo, telefone FROM usuarios WHERE usuario=?", (usuario_dono,)).fetchone()
                conn.close()

                nome_completo = dados_func[0] if dados_func else usuario_dono
                telefone_func = dados_func[1] if dados_func else ""

                if status_atual == "PENDENTE":
                    if st.button("✅ Aprovar Documento"): processar_acao_clean(id_target, "APROVADO", "APROVOU REEMBOLSO")
                elif status_atual == "APROVADO":
                    if st.button("💸 Marcar como PAGO (Liquidar)"): processar_acao_clean(id_target, "PAGO", "PAGOU REEMBOLSO")

                if status_atual == "PAGO" and telefone_func:
                    tel_limpo = "".join(filter(str.isdigit, telefone_func))
                    if not tel_limpo.startswith("55") and len(tel_limpo) >= 10: tel_limpo = "55" + tel_limpo
                    msg_wa = f"Olá, *{nome_completo}*!\n\nSua solicitação de reembolso *#{id_target}* (*{row_sel['Descrição']}*) de *R$ {row_sel['Valor (R$)']:.2f}* foi paga com sucesso!"
                    st.markdown(f'<a href="https://wa.me/{tel_limpo}?text={urllib.parse.quote(msg_wa)}" target="_blank" class="btn-whatsapp">💬 Enviar Notificação via WhatsApp</a>', unsafe_allow_html=True)

                if status_atual in ["PENDENTE", "APROVADO"]:
                    motivo = st.text_input("Motivo da Recusa:", key=f"motivo_{id_target}")
                    if st.button("❌ Negar Reembolso"):
                        if motivo.strip(): processar_acao_clean(id_target, "NEGADO", "REJEITOU REEMBOLSO", motivo)
                        else: st.error("Insira o motivo.")

                # 🔥 ZONA DE PERIGO: EXCLUSÃO DEFINITIVA
                st.write("---")
                st.markdown("<p style='color:#ef4444; font-weight:700; font-size:14px; margin-bottom:5px;'>⚠️ Zona de Perigo</p>", unsafe_allow_html=True)
                confirmar_exclusao = st.checkbox("Estou ciente de que esta ação apagará permanentemente o registro do banco de dados.", key=f"del_chk_{id_target}")
                
                if st.button("🗑️ Excluir Lançamento Permanente", key=f"del_btn_{id_target}"):
                    if confirmar_exclusao:
                        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                        cursor = conn.cursor()
                        if caminho_comprovante and os.path.exists(caminho_comprovante):
                            try: os.remove(caminho_comprovante)
                            except: pass
                        cursor.execute("DELETE FROM reembolsos WHERE id=?", (id_target,))
                        conn.commit(); conn.close()
                        st.success(f"Lançamento #{id_target} apagado!")
                        st.rerun()
                    else:
                        st.error("Marque a caixa de confirmação primeiro.")

            # 📥 AQUI ESTÁ O CONSERTO DO DOWNLOAD DA IMAGEM
            with col_preview:
                if caminho_comprovante and os.path.exists(caminho_comprovante):
                    st.markdown("**📄 Arquivo em anexo:**")
                    
                    if caminho_comprovante.lower().endswith('.pdf'):
                        st.caption("Documento PDF. Clique no botão abaixo para baixar e revisar:")
                    else:
                        st.image(caminho_comprovante, use_container_width=True)
                        st.caption("Imagem do comprovante. Clique no botão abaixo para salvar uma cópia:")
                    
                    # O botão de baixar agora aparece SEMPRE, não importa se é imagem ou PDF
                    with open(caminho_comprovante, "rb") as f:
                        st.download_button(
                            label="📥 Baixar Comprovante", 
                            data=f, 
                            file_name=os.path.basename(caminho_comprovante),
                            use_container_width=True
                        )
                else: 
                    st.info("Sem arquivo em anexo.")
                    
        st.markdown('</div>', unsafe_allow_html=True)

        # --- AQUI ESTÁ A RESTAURAÇÃO DA SUA LISTA DE USUÁRIOS NO ADMIN ---
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("👥 [PRODUÇÃO] Lista de Usuários Cadastrados no Sistema"):
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            df_users = pd.read_sql("SELECT cpf as 'CPF Key', nome_completo as 'Nome Completo', email as 'E-mail', telefone as 'Telefone', senha as 'Senha Ativa' FROM usuarios", conn)
            conn.close()
            st.dataframe(df_users, use_container_width=True)

    # --- 📈 ABA: PAINEL EXECUTIVO ---
    elif menu == "📈 Painel Executivo":
        st.markdown('<h1 class="clean-title">Painel Executivo de Controladoria</h1>', unsafe_allow_html=True)
        st.markdown('<div class="premium-card">📊 Métricas de desempenho financeiro consolidado da Duarte Gestão.</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📥 Backup de Segurança Total (Botão de Pânico)")
        st.write("Baixe a cópia de segurança completa de todos os dados salvos no sistema para salvaguarda externa:")
        
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df_backup = pd.read_sql("SELECT * FROM reembolsos", conn)
        conn.close()

        if not df_backup.empty:
            csv_backup = df_backup.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 BAIXAR HISTÓRICO COMPLETO (CSV)",
                data=csv_backup,
                file_name=f"BACKUP_GERAL_DUARTE_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
        else:
            st.info("Nenhum dado financeiro para exportar no momento.")