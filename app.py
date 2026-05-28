import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# --- CONFIGURAÇÃO E BANCO ---
if not os.path.exists("comprovantes"): os.makedirs("comprovantes")
st.set_page_config(page_title="Duarte Reembolsos", layout="wide")
conn = sqlite3.connect("reembolso.db", check_same_thread=False)
cursor = conn.cursor()

# Tabelas
cursor.execute("""CREATE TABLE IF NOT EXISTS usuarios 
                  (usuario TEXT PRIMARY KEY, senha TEXT, email TEXT, nivel TEXT)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS reembolsos 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, despesa TEXT, 
                   categoria TEXT, c_custo TEXT, valor REAL, status TEXT, data DATE, caminho_arquivo TEXT)""")

# Cria ADMs iniciais se não existirem
for u in [('admin', '1234', 'admin@erp.com', 'admin'), ('operacional', '1234', 'op@erp.com', 'admin'), ('financeiro', '1234', 'fin@erp.com', 'admin')]:
    try: cursor.execute("INSERT INTO usuarios VALUES (?,?,?,?)", u); conn.commit()
    except: pass

# --- FUNÇÕES DE INTERFACE ---
if "logado" not in st.session_state: st.session_state["logado"] = False

# Tela de Login com opção de Cadastro
if not st.session_state["logado"]:
    st.title("🔐 DUARTE REEMBOLSOS - ACESSO")
    tab1, tab2 = st.tabs(["ENTRAR", "CADASTRAR NOVO FUNCIONÁRIO"])
    
    with tab1:
        u = st.text_input("USUÁRIO", key="login_u")
        p = st.text_input("SENHA", type="password", key="login_p")
        if st.button("ENTRAR"):
            cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, p))
            user = cursor.fetchone()
            if user:
                st.session_state["logado"] = True
                st.session_state["user_info"] = {"user": user[0], "nivel": user[3]}
                st.rerun()
            else: st.error("DADOS INVÁLIDOS!")
            
    with tab2:
        with st.form("cadastro_novo"):
            new_u = st.text_input("ESCOLHA SEU USUÁRIO")
            new_p = st.text_input("ESCOLHA UMA SENHA", type="password")
            new_e = st.text_input("SEU E-MAIL")
            if st.form_submit_button("CADASTRAR E ACESSAR"):
                try:
                    cursor.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (new_u, new_p, new_e, 'usuario'))
                    conn.commit()
                    st.success("CADASTRO REALIZADO! FAÇA O LOGIN NA ABA AO LADO.")
                except: st.error("USUÁRIO JÁ EXISTE!")

else:
    # --- MENU PRINCIPAL (SÓ APARECE SE LOGADO) ---
    st.sidebar.title(f"👤 {st.session_state['user_info']['user']}")
    menu = st.sidebar.radio("NAVEGAÇÃO", ["💸 SOLICITAR REEMBOLSO", "📋 MEUS PEDIDOS", "📊 PAINEL ADMIN"])
    if st.sidebar.button("SAIR"): st.session_state["logado"] = False; st.rerun()

    if menu == "💸 SOLICITAR REEMBOLSO":
        st.title("💸 NOVA SOLICITAÇÃO")
        with st.form("solicitar"):
            desc = st.text_input("DESCRIÇÃO")
            cat = st.selectbox("CATEGORIA", ["LIMPEZA", "ALIMENTAÇÃO", "TELEFONIA E INTERNET", "TRANSPORTES / LOGÍSTICA", "ESTACIONAMENTO", "DESPESAS DE VIAGENS", "MÁQUINAS E EQUIPAMENTOS"])
            cc = st.selectbox("C. DE CUSTO", ["CREDENCIAMENTO", "REDE", "DIRETORIA", "DUARTE GESTÃO", "MARKETING", "FINANCEIRO"])
            val = st.number_input("VALOR", min_value=0.0)
            arquivo = st.file_uploader("ANEXAR COMPROVANTE", type=['jpg', 'png', 'pdf'])
            if st.form_submit_button("ENVIAR"):
                caminho = ""
                if arquivo:
                    caminho = f"comprovantes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{arquivo.name}"
                    with open(caminho, "wb") as f: f.write(arquivo.getbuffer())
                cursor.execute("INSERT INTO reembolsos (usuario, despesa, categoria, c_custo, valor, status, data, caminho_arquivo) VALUES (?,?,?,?,?,?,?,?)", 
                               (st.session_state['user_info']['user'], desc, cat, cc, val, 'PENDENTE', datetime.now(), caminho))
                conn.commit()
                st.success("SOLICITAÇÃO ENVIADA!")

    elif menu == "📊 PAINEL ADMIN":
        if st.session_state['user_info']['nivel'] == 'admin':
            st.title("📊 PAINEL DE PAGAMENTOS")
            st.dataframe(pd.read_sql("SELECT * FROM reembolsos", conn))
            id_pg = st.number_input("ID PARA PROCESSAR:", min_value=1)
            if st.button("MARCAR COMO PAGO"):
                cursor.execute("UPDATE reembolsos SET status='PAGO' WHERE id=?", (id_pg,))
                conn.commit()
                st.success("STATUS ATUALIZADO!")
        else: st.error("ACESSO NEGADO!")