import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Duarte Reembolsos Pro", layout="wide")

# Conexão Banco
conn = sqlite3.connect("reembolso.db", check_same_thread=False)
cursor = conn.cursor()

# Tabelas
cursor.execute("""CREATE TABLE IF NOT EXISTS usuarios 
                  (usuario TEXT PRIMARY KEY, senha TEXT, email TEXT, nivel TEXT)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS reembolsos 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   usuario TEXT, despesa TEXT, valor REAL, status TEXT, data DATE)""")
# NOVA TABELA DE LOGS
cursor.execute("""CREATE TABLE IF NOT EXISTS logs 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   usuario_acao TEXT, acao TEXT, data_hora DATETIME)""")
conn.commit()

# --- POPULAR ADMS E LOG ---
def popular_banco():
    adms = [('admin', '1234', 'admin@erp.com', 'admin'),
            ('operacional', '1234', 'op@erp.com', 'admin'),
            ('financeiro', '1234', 'fin@erp.com', 'admin')]
    for u in adms:
        try: cursor.execute("INSERT INTO usuarios VALUES (?,?,?,?)", u); conn.commit()
        except: pass

popular_banco()

# --- FUNÇÃO DE REGISTRAR LOG ---
def registrar_log(user, acao):
    cursor.execute("INSERT INTO logs (usuario_acao, acao, data_hora) VALUES (?,?,?)", 
                   (user, acao, datetime.now()))
    conn.commit()

# --- LOGIN ---
if "logado" not in st.session_state: st.session_state["logado"] = False

def tela_login():
    st.title("🔐 Login")
    u = st.text_input("Usuário"); p = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, p))
        user = cursor.fetchone()
        if user:
            st.session_state["logado"] = True
            st.session_state["user_info"] = {"user": user[0], "nivel": user[3]}
            registrar_log(user[0], "Login no sistema")
            st.rerun()

if not st.session_state["logado"]: tela_login()
else:
    st.sidebar.title(f"👤 {st.session_state['user_info']['user']}")
    opcoes = ["💸 Solicitar Reembolso", "📋 Meus Pedidos"]
    if st.session_state['user_info']['nivel'] == 'admin':
        opcoes.extend(["📊 Painel Admin", "⚙️ Cadastrar Usuários", "🕒 Logs de Auditoria"])
    
    menu = st.sidebar.radio("Navegação", opcoes)
    if st.sidebar.button("Sair"): 
        registrar_log(st.session_state['user_info']['user'], "Logout")
        st.session_state["logado"] = False; st.rerun()

    # --- FUNÇÕES ---
    if menu == "💸 Solicitar Reembolso":
        st.title("💸 Nova Solicitação")
        with st.form("solicitar"):
            desc = st.text_input("Descrição"); val = st.number_input("Valor", min_value=0.0)
            if st.form_submit_button("Enviar"):
                cursor.execute("INSERT INTO reembolsos (usuario, despesa, valor, status, data) VALUES (?,?,?,?,?)", 
                               (st.session_state['user_info']['user'], desc, val, 'Pendente', datetime.now()))
                conn.commit()
                registrar_log(st.session_state['user_info']['user'], f"Solicitou reembolso de R${val}")
                st.success("Solicitação enviada!")

    elif menu == "🕒 Logs de Auditoria":
        st.title("🕒 Histórico de Ações (Logs)")
        st.dataframe(pd.read_sql("SELECT * FROM logs ORDER BY data_hora DESC", conn))

    elif menu == "📊 Painel Admin":
        st.title("📊 Painel de Pagamentos")
        st.dataframe(pd.read_sql("SELECT * FROM reembolsos", conn))
        id_pg = st.number_input("ID para Pagar:", min_value=1)
        if st.button("Marcar como PAGO"):
            cursor.execute("UPDATE reembolsos SET status='Pago' WHERE id=?", (id_pg,))
            conn.commit()
            registrar_log(st.session_state['user_info']['user'], f"Pagou reembolso ID {id_pg}")
            st.success("Pagamento realizado!")