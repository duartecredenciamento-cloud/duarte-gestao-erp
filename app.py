import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL E PASTAS ---
if not os.path.exists("comprovantes"): 
    os.makedirs("comprovantes")

st.set_page_config(page_title="Duarte Reembolsos", layout="wide")

DB_PATH = "reembolso.db"
DB_TIMEOUT = 30.0  # Evita o erro de "database is locked" esperando até 30 segundos

# --- FUNÇÕES AUXILIARES DE BANCO DE DADOS (ABRE E FECHA CONEXÃO NA HORA) ---
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
    conn.commit()

    # Popular os ADMs Iniciais com segurança
    adms_iniciais = [
        ('admin', '1234', 'admin@erp.com', 'admin', 'ADMINISTRADOR PRINCIPAL', '000.000.000-00', '(00) 00000-0000'),
        ('operacional', '1234', 'op@erp.com', 'admin', 'OPERACIONAL ADMINISTRATIVO', '000.000.000-00', '(00) 00000-0000'),
        ('financeiro', '1234', 'fin@erp.com', 'admin', 'FINANCEIRO DIRETORIA', '000.000.000-00', '(00) 00000-0000')
    ]
    for u in adms_iniciais:
        try:
            cursor.execute("INSERT INTO usuarios VALUES (?,?,?,?,?,?,?)", u)
            conn.commit()
        except sqlite3.IntegrityError:
            pass
    conn.close()

def registrar_log(user, acao):
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (usuario_acao, acao, data_hora) VALUES (?,?,?)", (user, acao, datetime.now()))
    conn.commit()
    conn.close()

# Inicializa as tabelas de forma segura
inicializar_banco()

# --- CONTROLE DE SESSÃO ---
if "logado" not in st.session_state: 
    st.session_state["logado"] = False

# --- TELA DE ACESSO (DESLOGADO) ---
if not st.session_state["logado"]:
    st.title("🔐 DUARTE REEMBOLSOS - ACESSO")
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
                registrar_log(user[0], "LOGIN NO SISTEMA SUCCESSO")
                st.rerun()
            else: 
                st.error("USUÁRIO OU SENHA INVÁLIDOS!")
            
    with tab2:
        st.subheader("📝 FORMULÁRIO DE CADASTRO")
        with st.form("cadastro_novo", clear_on_submit=True):
            new_u = st.text_input("ESCOLHA SEU USUÁRIO (LOGIN)")
            new_p = st.text_input("ESCOLHA UMA SENHA", type="password")
            new_nome = st.text_input("NOME COMPLETO")
            new_cpf = st.text_input("CPF")
            new_tel = st.text_input("TELEFONE DE CONTATO")
            new_e = st.text_input("E-MAIL CORPORATIVO")
            
            if st.form_submit_button("CADASTRAR FUNCIONÁRIO"):
                if new_u and new_p and new_nome and new_cpf:
                    try:
                        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO usuarios VALUES (?,?,?,?,?,?,?)", 
                                       (new_u, new_p, new_e, 'usuario', new_nome, new_cpf, new_tel))
                        conn.commit()
                        conn.close()
                        
                        registrar_log("SISTEMA", f"NOVO FUNCIONARIO CADASTRADO: {new_u}")
                        st.success("CADASTRO REALIZADO COM SUCESSO! CLIQUE NA ABA 'ENTRAR' AO LADO.")
                    except sqlite3.IntegrityError: 
                        st.error("ESTE NOME DE USUÁRIO JÁ ESTÁ EM USO!")
                else:
                    st.warning("PREENCHA TODOS OS CAMPOS OBRIGATÓRIOS!")

# --- ÁREA LOGADA ---
else:
    st.sidebar.title(f"👤 {st.session_state['user_info']['nome']}")
    st.sidebar.write(f"Perfil: **{st.session_state['user_info']['nivel'].upper()}**")
    
    opcoes_menu = ["💸 SOLICITAR REEMBOLSO", "📋 MEUS PEDIDOS"]
    if st.session_state['user_info']['nivel'] == 'admin':
        opcoes_menu.append("📊 PAINEL ADMIN")
        
    menu = st.sidebar.radio("NAVEGAÇÃO", opcoes_menu)
    
    if st.sidebar.button("SAIR DO SISTEMA"): 
        registrar_log(st.session_state['user_info']['user'], "LOGOUT DO SISTEMA")
        st.session_state["logado"] = False
        st.rerun()

    # --- MENU 1: SOLICITAR REEMBOLSO ---
    if menu == "💸 SOLICITAR REEMBOLSO":
        st.title("💸 NOVA SOLICITAÇÃO DE REEMBOLSO")
        with st.form("solicitar_reembolso", clear_on_submit=True):
            desc = st.text_input("DESCRIÇÃO DA DESPESA (Ex: Jantar comercial com cliente X)")
            
            cat = st.selectbox("CATEGORIA", [
                "LIMPEZA", "REMUNERAÇÃO SÓCIOS", "ALIMENTAÇÃO", "TELEFONIA E INTERNET", 
                "SOFTWARE E LICENÇAS - INFORMÁTICA", "TRANSPORTES / LOGÍSTICA", 
                "MATERIAL DE ESCRITÓRIO", "EQUIPAMENTOS DE INFORMÁTICA", "ESTACIONAMENTO", 
                "MÓVEIS E UTENSÍLIOS", "DESPESAS DE VIAGENS", "MÁQUINAS E EQUIPAMENTOS"
            ])
            
            cc = st.selectbox("CENTRO DE CUSTO", [
                "CREDENCIAMENTO", "REDE", "DIRETORIA", "DUARTE GESTÃO", "MARKETING", "FINANCEIRO"
            ])
            
            val = st.number_input("VALOR TOTAL (R$)", min_value=0.01, step=0.01)
            arquivo = st.file_uploader("ANEXAR COMPROVANTE FISCAL (JPG / PNG / PDF)", type=['jpg', 'png', 'pdf'])
            
            if st.form_submit_button("ENVIAR SOLICITAÇÃO"):
                if desc and val > 0:
                    caminho_salvo = ""
                    if arquivo:
                        caminho_salvo = f"comprovantes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{arquivo.name}"
                        with open(caminho_salvo, "wb") as f: 
                            f.write(arquivo.getbuffer())
                    
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    cursor = conn.cursor()
                    cursor.execute("""INSERT INTO reembolsos 
                                      (usuario, despesa, categoria, c_custo, valor, status, data, caminho_arquivo) 
                                      VALUES (?,?,?,?,?,?,?,?)""", 
                                   (st.session_state['user_info']['user'], desc, cat, cc, val, 'PENDENTE', datetime.now().date(), caminho_salvo))
                    conn.commit()
                    conn.close()
                    
                    registrar_log(st.session_state['user_info']['user'], f"SOLICITOU REEMBOLSO NO VALOR DE R$ {val:.2f} ({cc})")
                    st.success("SOLICITAÇÃO ENVIADA COM SUCESSO PARA ANÁLISE!")
                else:
                    st.error("POR FAVOR, INSIRA UMA DESCRIÇÃO E UM VALOR VÁLIDO!")

    # --- MENU 2: MEUS PEDIDOS ---
    elif menu == "📋 MEUS PEDIDOS":
        st.title("📋 MEU HISTÓRICO DE SOLICITAÇÕES")
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        df_meus = pd.read_sql(f"SELECT id, despesa, categoria, c_custo, valor, status, data FROM reembolsos WHERE usuario='{st.session_state['user_info']['user']}' ORDER BY id DESC", conn)
        conn.close()
        
        if df_meus.empty:
            st.info("Você ainda não possui nenhuma solicitação registrada.")
        else:
            st.dataframe(df_meus, use_container_width=True)

    # --- MENU 3: PAINEL ADMIN ---
    elif menu == "📊 PAINEL ADMIN":
        if st.session_state['user_info']['nivel'] == 'admin':
            st.title("📊 PAINEL DE GESTÃO E AUDITORIA")
            
            # Logs de Auditoria
            with st.expander("🕒 VISUALIZAR LOGS DE AUDITORIA (QUEM ACESSOU / O QUE FEZ)"):
                conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                df_logs = pd.read_sql("SELECT * FROM logs ORDER BY data_hora DESC", conn)
                conn.close()
                st.dataframe(df_logs, use_container_width=True)
            
            st.subheader("📋 TODAS AS SOLICITAÇÕES DA EMPRESA")
            conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
            df_todos = pd.read_sql("SELECT * FROM reembolsos ORDER BY id DESC", conn)
            conn.close()
            st.dataframe(df_todos, use_container_width=True)
            
            st.markdown("---")
            st.subheader("🕹️ OPERAR SOLICITAÇÃO")
            
            id_pg = st.number_input("DIGITE O ID DA SOLICITAÇÃO PARA GERENCIAR:", min_value=1, step=1)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("👁️ VER/BAIXAR COMPROVANTE", use_container_width=True):
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    cursor = conn.cursor()
                    res = cursor.execute("SELECT caminho_arquivo FROM reembolsos WHERE id=?", (id_pg,)).fetchone()
                    conn.close()
                    
                    if res and res[0] and os.path.exists(res[0]):
                        with open(res[0], "rb") as file:
                            st.download_button(label="CLIQUE PARA BAIXAR", data=file, file_name=os.path.basename(res[0]), use_container_width=True)
                    else:
                        st.error("NENHUM COMPROVANTE ENCONTRADO PARA ESTE ID!")
                        
            with col2:
                if st.button("✅ APROVAR PEDIDO", use_container_width=True):
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    cursor = conn.cursor()
                    verificar = cursor.execute("SELECT id FROM reembolsos WHERE id=?", (id_pg,)).fetchone()
                    if verificar:
                        cursor.execute("UPDATE reembolsos SET status='APROVADO' WHERE id=?", (id_pg,))
                        conn.commit()
                        conn.close()
                        registrar_log(st.session_state['user_info']['user'], f"APROVOU SOLICITACAO ID {id_pg}")
                        st.success(f"PEDIDO {id_pg} APROVADO!")
                        st.rerun()
                    else:
                        conn.close()
                        st.error("ID NÃO ENCONTRADO!")
                        
            with col3:
                if st.button("❌ NEGAR PEDIDO", use_container_width=True):
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    cursor = conn.cursor()
                    verificar = cursor.execute("SELECT id FROM reembolsos WHERE id=?", (id_pg,)).fetchone()
                    if verificar:
                        cursor.execute("UPDATE reembolsos SET status='NEGADO' WHERE id=?", (id_pg,))
                        conn.commit()
                        conn.close()
                        registrar_log(st.session_state['user_info']['user'], f"NEGOU SOLICITACAO ID {id_pg}")
                        st.warning(f"PEDIDO {id_pg} REJEITADO E NEGADO!")
                        st.rerun()
                    else:
                        conn.close()
                        st.error("ID NÃO ENCONTRADO!")
                        
            with col4:
                if st.button("💸 MARCAR COMO PAGO", use_container_width=True):
                    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
                    cursor = conn.cursor()
                    verificar = cursor.execute("SELECT id FROM reembolsos WHERE id=?", (id_pg,)).fetchone()
                    if verificar:
                        cursor.execute("UPDATE reembolsos SET status='PAGO' WHERE id=?", (id_pg,))
                        conn.commit()
                        conn.close()
                        registrar_log(st.session_state['user_info']['user'], f"PAGOU E ENCERROU SOLICITACAO ID {id_pg}")
                        st.success(f"PEDIDO {id_pg} MARCADO COMO PAGO!")
                        st.rerun()
                    else:
                        conn.close()
                        st.error("ID NÃO ENCONTRADO!")
        else:
            st.error("ACESSO NEGADO! PERFIL INSUFICIENTE.")