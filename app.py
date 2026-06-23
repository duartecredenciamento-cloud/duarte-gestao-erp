import streamlit as st
import sqlite3
import pandas as pd
import base64
from datetime import datetime
import io

# Configuração da página - Premium e Responsiva
st.set_page_config(
    page_title="Duarte Gestão | Sistema de Reembolsos",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeção de CSS Premium e Identidade Visual Clássica da Duarte Gestão
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFC;
    }
    
    /* Logomarca Customizada Duarte Gestão - Identidade Forte */
    .logo-container {
        background: linear-gradient(135deg, #001E57 0%, #002D80 100%);
        padding: 30px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 30px;
        border-bottom: 5px solid #FF9200;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .logo-main {
        color: #FFFFFF;
        font-size: 32px;
        font-weight: 700;
        letter-spacing: 1px;
        margin: 0;
    }
    .logo-sub {
        color: #FF9200;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-top: 5px;
    }
    
    /* Cards Premium */
    .premium-card {
        background-color: #FFFFFF;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border-left: 5px solid #001E57;
        margin-bottom: 20px;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #001E57 0%, #003399 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.08);
        text-align: center;
    }
    
    /* Tabelas Responsivas */
    .responsive-table-container {
        width: 100%;
        overflow-x: auto;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        min-width: 600px;
    }
    
    .custom-table th {
        background-color: #001E57;
        color: white;
        text-align: left;
        padding: 12px;
        font-weight: 600;
    }
    
    .custom-table td {
        padding: 12px;
        border-bottom: 1px solid #E2E8F0;
        color: #334155;
    }
    
    /* Badges de Status */
    .badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
    }
    .badge-pendente { background-color: #FEF3C7; color: #D97706; }
    .badge-aprovado { background-color: #D1FAE5; color: #059669; }
    .badge-pago { background-color: #DBEAFE; color: #2563EB; }
    .badge-negado { background-color: #FEE2E2; color: #DC2626; }
    
    /* Botão WhatsApp */
    .btn-whatsapp {
        background-color: #25D366;
        color: white !important;
        padding: 12px 24px;
        border-radius: 6px;
        text-decoration: none;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-top: 10px;
        box-shadow: 0 4px 6px rgba(37, 211, 102, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# Inicialização do Banco de Dados (SQLite)
def init_db():
    conn = sqlite3.connect("reembolsos.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            cpf TEXT PRIMARY KEY,
            nome TEXT,
            telefone TEXT,
            senha TEXT,
            cargo TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS solicitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpf_usuario TEXT,
            nome_usuario TEXT,
            descricao TEXT,
            categoria TEXT,
            valor REAL,
            data TEXT,
            status TEXT,
            comprovante TEXT
        )
    """)
    
    # Criar admin e time inicial se vazio
    c.execute("SELECT * FROM usuarios WHERE cargo='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios VALUES ('00000000000', 'Erick Admin', '11918551349', 'admin123', 'admin')")
        c.execute("INSERT INTO usuarios VALUES ('11111111111', 'Aline Silva', '11988888888', '1234', 'colaborador')")
        c.execute("INSERT INTO usuarios VALUES ('22222222222', 'Lucas Souza', '11977777777', '1234', 'colaborador')")
        c.execute("INSERT INTO usuarios VALUES ('33333333333', 'Patricia Costa', '11966666666', '1234', 'colaborador')")
        
        c.execute("""
            INSERT INTO solicitacoes (cpf_usuario, nome_usuario, descricao, categoria, valor, data, status, comprovante) 
            VALUES 
            ('11111111111', 'Aline Silva', 'Visita Técnica Operacional - Projeto DNA Care', 'Transporte', 145.80, '2026-06-15', 'Pendente', ''),
            ('22222222222', 'Lucas Souza', 'Almoço de Alinhamento - Manual Vivest', 'Alimentação', 92.00, '2026-06-18', 'Aprovado', ''),
            ('33333333333', 'Patricia Costa', 'Assinatura Ferramenta de TI - Fisio Life', 'Ferramentas/Software', 299.90, '2026-06-20', 'Pago', '')
        """)
    conn.commit()
    conn.close()

init_db()

# Funções Utilitárias
def limpar_cpf(cpf):
    return "".join(filter(str.isdigit, cpf))

def buscar_usuario(cpf):
    conn = sqlite3.connect("reembolsos.db")
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE cpf=?", (cpf,))
    user = c.fetchone()
    conn.close()
    return user

def atualizar_senha(cpf, nova_senha):
    conn = sqlite3.connect("reembolsos.db")
    c = conn.cursor()
    c.execute("UPDATE usuarios SET senha=? WHERE cpf=?", (nova_senha, cpf))
    conn.commit()
    conn.close()

if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = None

# --- EXIBIÇÃO DA LOGO ANTIGA/TRADICIONAL ---
st.markdown("""
    <div class="logo-container">
        <div class="logo-main">DUARTE GESTÃO</div>
        <div class="logo-sub">SISTEMA INTERNO DE REEMBOLSOS</div>
    </div>
""", unsafe_allow_html=True)

# --- FLUXO DE AUTENTICAÇÃO ---
if not st.session_state.logado:
    st.write("Insira o seu CPF para acessar o painel de despesas.")
    
    tab_login, tab_cadastro, tab_recuperar = st.tabs(["🔑 Entrar", "📝 Novo Cadastro", "🔒 Esqueci a Senha"])
    
    # Aba 1: Login
    with tab_login:
        with st.form("form_login", clear_on_submit=False):
            st.markdown("### Acesso ao Sistema")
            login_cpf = st.text_input("CPF (Apenas números)", max_chars=11, placeholder="Ex: 12345678901")
            login_senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            
            st.markdown("<p style='font-size:12px; color:#64748B;'>💡 <b>Dica de Praticidade:</b> Ao clicar em entrar, autorize o seu navegador a 'Salvar Senha' para agilizar os próximos acessos.</p>", unsafe_allow_html=True)
            
            botao_entrar = st.form_submit_button("Entrar no Painel", use_container_width=True)
            
            if botao_entrar:
                cpf_limpo = limpar_cpf(login_cpf)
                user = buscar_usuario(cpf_limpo)
                
                if user and user[3] == login_senha:
                    st.session_state.logado = True
                    st.session_state.usuario = {"cpf": user[0], "nome": user[1], "telefone": user[2], "cargo": user[4]}
                    st.success(f"Login realizado com sucesso! Bem-vindo(a), {user[1]}.")
                    st.rerun()
                else:
                    st.error("CPF ou Senha incorretos. Por favor, revise as informações.")
                    
    # Aba 2: Cadastro
    with tab_cadastro:
        with st.form("form_cadastro"):
            st.markdown("### Criar Perfil de Colaborador")
            cad_nome = st.text_input("Nome Completo", placeholder="Ex: Aline Silva")
            cad_cpf = st.text_input("CPF (Apenas números)", max_chars=11, placeholder="Ex: 11122233344")
            cad_tel = st.text_input("Telefone com DDD (Apenas números)", placeholder="Ex: 11999999999")
            cad_senha = st.text_input("Crie uma Senha Forte", type="password")
            
            botao_cadastrar = st.form_submit_button("Finalizar Meu Cadastro", use_container_width=True)
            
            if botao_cadastrar:
                cpf_limpo = limpar_cpf(cad_cpf)
                tel_limpo = limpar_cpf(cad_tel)
                
                if not cad_nome or len(cpf_limpo) != 11 or not tel_limpo or not cad_senha:
                    st.warning("Preencha todos os campos corretamente para validar o perfil.")
                else:
                    if buscar_usuario(cpf_limpo):
                        st.error("Este CPF já se encontra registrado no sistema.")
                    else:
                        conn = sqlite3.connect("reembolsos.db")
                        c = conn.cursor()
                        c.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?, 'colaborador')", (cpf_limpo, cad_nome, tel_limpo, cad_senha))
                        conn.commit()
                        conn.close()
                        st.success("🎉 Perfil criado com sucesso! Faça login na primeira aba.")

    # Aba 3: Recuperação com o Novo Número Atualizado
    with tab_recuperar:
        st.markdown("### 🔑 Recuperação de Acesso")
        st.write("Confirme seus dados cadastrais para redefinir sua senha imediatamente:")
        
        rec_cpf = st.text_input("Digite seu CPF cadastrado", max_chars=11, key="rec_cpf")
        rec_tel = st.text_input("Digite seu Telefone cadastrado", key="rec_tel")
        
        if rec_cpf and rec_tel:
            cpf_limpo = limpar_cpf(rec_cpf)
            tel_limpo = limpar_cpf(rec_tel)
            user = buscar_usuario(cpf_limpo)
            
            if user and limpar_cpf(user[2]) == tel_limpo:
                st.success("✅ Identidade validada! Insira a sua nova senha abaixo:")
                nova_senha = st.text_input("Nova Senha", type="password", key="nova_senha")
                confirma_nova_senha = st.text_input("Confirme a Nova Senha", type="password", key="confirma_nova_senha")
                
                if st.button("Gravar Nova Senha", use_container_width=True):
                    if nova_senha == confirma_nova_senha and nova_senha != "":
                        atualizar_senha(cpf_limpo, nova_senha)
                        st.balloons()
                        st.success("✨ Excelente! Senha atualizada. Prossiga para a aba de Entrada.")
                    else:
                        st.error("As senhas digitadas não batem. Repita a operação.")
            elif user:
                st.error("❌ Os dados informados não batem com o cadastro de segurança.")
        
        st.markdown("---")
        st.markdown("#### 🛠️ Problemas com o número antigo?")
        st.write("Caso não consiga recuperar pelo formulário automático, solicite a redefinição direta ao suporte clicando abaixo:")
        
        # LINK ATUALIZADO: Direcionando para o número 11 91855-1349
        link_suporte_whatsapp = "https://wa.me/5511918551349?text=Olá,%20esqueci%20minha%20senha%20de%20acesso%20ao%20Painel%20de%20Reembolsos%20da%20Duarte%20Gestão.%20Poderia%20redefinir%20para%20mim?"
        st.markdown(f'<a href="{link_suporte_whatsapp}" target="_blank" class="btn-whatsapp">💬 Solicitar Suporte via WhatsApp</a>', unsafe_allow_html=True)

else:
    # --- INTERFACE PRINCIPAL (SESSÃO ATIVA) ---
    user_atual = st.session_state.usuario
    st.sidebar.markdown(f"### 👤 {user_atual['nome']}")
    st.sidebar.markdown(f"**Nível:** {user_atual['cargo'].upper()}")
    if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario = None
        st.rerun()
        
    # --- VISÃO COLABORADOR ---
    if user_atual["cargo"] == "colaborador":
        menu_colab = st.sidebar.radio("Menu de Opções", ["✨ Solicitar Reembolso", "📋 Meus Pedidos"])
        
        if menu_colab == "✨ Solicitar Reembolso":
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.markdown("### Solicitar Novo Reembolso")
            with st.form("form_solicitacao", clear_on_submit=True):
                desc = st.text_input("Descrição do Gasto / Nome do Projeto", placeholder="Ex: Almoço comercial - Projeto DNA Care")
                cat = st.selectbox("Categoria", ["Transporte", "Alimentação", "Hospedagem", "Ferramentas/Software", "Outros"])
                valor = st.number_input("Valor Total (R$)", min_value=0.01, step=0.10, format="%.2f")
                upload_file = st.file_uploader("Anexe o Comprovante Fiscal (Imagem/PDF)", type=["png", "jpg", "jpeg", "pdf"])
                
                btn_enviar = st.form_submit_button("Enviar para Auditoria", use_container_width=True)
                if btn_enviar:
                    if not desc or valor <= 0:
                        st.error("Por favor, preencha a descrição correta e o valor do gasto.")
                    else:
                        comp_b64 = ""
                        if upload_file is not None:
                            comp_b64 = base64.b64encode(upload_file.read()).decode("utf-8")
                        data_atual = datetime.now().strftime("%Y-%m-%d")
                        
                        conn = sqlite3.connect("reembolsos.db")
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO solicitacoes (cpf_usuario, nome_usuario, descricao, categoria, valor, data, status, comprovante)
                            VALUES (?, ?, ?, ?, ?, ?, 'Pendente', ?)
                        """, (user_atual["cpf"], user_atual["nome"], desc, cat, valor, data_atual, comp_b64))
                        conn.commit()
                        conn.close()
                        st.success("🚀 Solicitação enviada com sucesso!")
            st.markdown('</div>', unsafe_allow_html=True)
            
        elif menu_colab == "📋 Meus Pedidos":
            st.markdown("### Acompanhamento de Pedidos")
            conn = sqlite3.connect("reembolsos.db")
            df = pd.read_sql_query("SELECT id, descricao, categoria, valor, data, status FROM solicitacoes WHERE cpf_usuario=?", conn, params=(user_atual["cpf"],))
            conn.close()
            
            if df.empty:
                st.info("Você não realizou nenhum pedido de reembolso até o momento.")
            else:
                html_table = '<div class="responsive-table-container"><table class="custom-table"><thead><tr><th>ID</th><th>Descrição</th><th>Categoria</th><th>Valor</th><th>Data</th><th>Status</th></tr></thead><tbody>'
                for index, row in df.iterrows():
                    status_class = f"badge-{row['status'].lower()}"
                    html_table += f"<tr><td>#{row['id']}</td><td>{row['descricao']}</td><td>{row['categoria']}</td><td>R$ {row['valor']:.2f}</td><td>{row['data']}</td><td><span class='badge {status_class}'>{row['status']}</span></td></tr>"
                html_table += '</tbody></table></div>'
                st.markdown(html_table, unsafe_allow_html=True)

    # --- VISÃO ADMINISTRADOR (ERICK) ---
    elif user_atual["cargo"] == "admin":
        menu_admin = st.sidebar.radio("Painel do Gestor", ["📥 Central de Aprovações", "📈 Painel Executivo", "📊 Exportar Dados"])
        
        if menu_admin == "📥 Central de Aprovações":
            st.markdown("### Auditoria de Reembolsos Recebidos")
            conn = sqlite3.connect("reembolsos.db")
            df_admin = pd.read_sql_query("SELECT * FROM solicitacoes", conn)
            conn.close()
            
            if df_admin.empty:
                st.info("Sem solicitações no banco de dados.")
            else:
                filtro_status = st.selectbox("Status para Análise", ["Todos", "Pendente", "Aprovado", "Pago", "Negado"])
                df_filtered = df_admin if filtro_status == "Todos" else df_admin[df_admin["status"] == filtro_status]
                
                for index, row in df_filtered.iterrows():
                    with st.expander(f"📦 ID #{row['id']} | {row['nome_usuario']} — R$ {row['valor']:.2f} [{row['status']}]"):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.markdown(f"**Quem solicitou:** {row['nome_usuario']} (CPF: {row['cpf_usuario']})")
                            st.markdown(f"**Gasto / Destino:** {row['descricao']}")
                            st.markdown(f"**Categoria Informada:** {row['categoria']} | **Data:** {row['data']}")
                            st.markdown(f"## Valor Requerido: R$ {row['valor']:.2f}")
                            
                            novo_status = st.selectbox("Atualizar Status Operacional:", ["Pendente", "Aprovado", "Pago", "Negado"], key=f"sel_{row['id']}", index=["Pendente", "Aprovado", "Pago", "Negado"].index(row['status']))
                            
                            if st.button("Confirmar Alteração", key=f"btn_{row['id']}", use_container_width=True):
                                conn = sqlite3.connect("reembolsos.db")
                                c = conn.cursor()
                                c.execute("UPDATE solicitacoes SET status=? WHERE id=?", (novo_status, row['id']))
                                conn.commit()
                                conn.close()
                                st.success("Status modificado com sucesso!")
                                st.rerun()
                                
                            user_destino = buscar_usuario(row['cpf_usuario'])
                            if user_destino:
                                tel_destino = user_destino[2]
                                msg_texto = f"Olá {row['nome_usuario']}, o status do seu pedido de reembolso #{row['id']} ({row['descricao']}) foi alterado para: *{novo_status}*."
                                msg_encoded = msg_texto.replace(" ", "%20")
                                url_wa = f"https://wa.me/55{tel_destino}?text={msg_encoded}"
                                st.markdown(f'<a href="{url_wa}" target="_blank" class="btn-whatsapp">💬 Enviar Notificação via WhatsApp</a>', unsafe_allow_html=True)
                                
                        with col2:
                            st.markdown("**Visualização do Comprovante:**")
                            if row['comprovante'] != "":
                                try:
                                    st.image(base64.b64decode(row['comprovante']), use_container_width=True)
                                except:
                                    st.warning("Formato de comprovante não renderizável diretamente (PDF).")
                            else:
                                st.info("Sem comprovante anexo.")
                                
        elif menu_admin == "📈 Painel Executivo":
            st.markdown("### Visão Consolidada de Fluxo de Caixa")
            conn = sqlite3.connect("reembolsos.db")
            df_dash = pd.read_sql_query("SELECT categoria, valor, status FROM solicitacoes", conn)
            conn.close()
            
            if df_dash.empty:
                st.info("Insira dados de reembolsos para estruturar os gráficos.")
            else:
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.markdown(f'<div class="metric-card"><h3>💰 Total Liquidado (Pago)</h3><h2>R$ {df_dash[df_dash["status"] == "Pago"]["valor"].sum():.2f}</h2></div>', unsafe_allow_html=True)
                with m2:
                    st.markdown(f'<div class="metric-card" style="background: linear-gradient(135deg, #FF9200 0%, #E08100 100%);"><h3>⏳ Total Pendente</h3><h2>R$ {df_dash[df_dash["status"] == "Pendente"]["valor"].sum():.2f}</h2></div>', unsafe_allow_html=True)
                with m3:
                    st.markdown(f'<div class="metric-card" style="background: #64748B;"><h3>📊 Total Geral Auditado</h3><h2>R$ {df_dash["valor"].sum():.2f}</h2></div>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                g1, g2 = st.columns(2)
                with g1:
                    st.markdown('<div class="premium-card"><b>📊 Distribuição por Status Financeiro</b>', unsafe_allow_html=True)
                    st.bar_chart(data=df_dash.groupby('status')['valor'].sum().reset_index(), x='status', y='valor', color='#001E57')
                    st.markdown('</div>', unsafe_allow_html=True)
                with g2:
                    st.markdown('<div class="premium-card"><b>🏷️ Custos por Categoria de Despesa</b>', unsafe_allow_html=True)
                    st.bar_chart(data=df_dash.groupby('categoria')['valor'].sum().reset_index(), x='categoria', y='valor', color='#FF9200')
                    st.markdown('</div>', unsafe_allow_html=True)
                    
        elif menu_admin == "📊 Exportar Dados":
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.markdown("### Exportar Dados para Contabilidade")
            
            conn = sqlite3.connect("reembolsos.db")
            df_export = pd.read_sql_query("SELECT id, cpf_usuario, nome_usuario, descricao, categoria, valor, data, status FROM solicitacoes", conn)
            conn.close()
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Relatorio_Reembolsos')
                
            st.download_button(
                label="📥 Baixar Planilha Consolidada (Excel .xlsx)",
                data=buffer.getvalue(),
                file_name=f"DuarteGestao_Reembolsos_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)