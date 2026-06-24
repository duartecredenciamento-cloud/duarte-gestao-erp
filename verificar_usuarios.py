import sqlite3
import pandas as pd
import os

db_nome = "reembolso.db"

print("\n--- 🛠️ DIAGNÓSTICO DO BANCO DE DADOS ---")

# 1. Verifica se o arquivo existe e o tamanho dele
if os.path.exists(db_nome):
    tamanho = os.path.getsize(db_nome)
    print(f"📦 Arquivo '{db_nome}' localizado.")
    print(f"📏 Tamanho do arquivo: {tamanho} bytes")
    
    # Conecta e checa as tabelas internas
    conn = sqlite3.connect(db_nome)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = [t[0] for t in cursor.fetchall()]
    print(f"🗂️ Tabelas encontradas no arquivo: {tabelas}")
    
    if "usuarios" in tabelas:
        print("\n✅ Tabela 'usuarios' localizada! Buscando dados...")
        df = pd.read_sql("SELECT cpf, nome_completo, email, telefone, senha FROM usuarios", conn)
        print("\n--- LINDAGEM DE USUÁRIOS ---")
        print(df.to_string(index=False))
    else:
        print("\n❌ Erro: O arquivo existe mas está totalmente vazio (0 tabelas).")
        print("💡 Provavelmente o banco real está na pasta anterior ou o Streamlit ainda não foi iniciado aqui.")
    
    conn.close()
else:
    print(f"❌ O arquivo '{db_nome}' não foi encontrado nesta pasta.")