# Duarte Gestão — Sistema de Reembolsos 2.0

Inclui `app.py`, dependências, configuração de runtime e marca visual. Preserva os fluxos atuais e incorpora aviso de atualização, identidade visual renovada e importação protegida de backup CSV.

## Importar o CSV
No **Painel Executivo** (perfil `admin`), quando não houver nenhuma solicitação no banco, envie o arquivo CSV e revise a prévia. A tela verifica colunas, IDs, status, valores, datas e referências de anexo. Digite `IMPORTAR` para confirmar. A operação acrescenta as solicitações numa transação atômica e guarda uma cópia do SQLite antes da gravação. Se o banco já tiver solicitações, a importação é bloqueada para evitar duplicação ou substituição acidental.

A restauração não inclui usuários/senhas nem os bytes dos comprovantes. Referências aos comprovantes só funcionam se os arquivos existirem no armazenamento.

## Persistência no Railway — configurar antes do deploy
Não publique antes de proteger/recuperar o banco atualmente usado e anexar um volume persistente **ao serviço do aplicativo**. Configure os caminhos conforme o mount path indicado pelo Railway:

- `REEMBOLSO_DB_PATH=/caminho/do/volume/reembolso.db`
- `REEMBOLSO_UPLOAD_DIR=/caminho/do/volume/comprovantes`

Para instalação realmente nova sem conta administrativa, é possível configurar `ADMIN_BOOTSTRAP_PASSWORD` e `ADMIN_BOOTSTRAP_EMAIL`. Esta versão não recria senhas padrão e não sobrescreve usuários existentes.

A cópia anterior à importação fica na pasta `backups` ao lado do banco. Isso protege contra falhas de importação, mas não contra perda do volume: mantenha exportações externas e backups independentes. O pacote é código para revisão, não foi publicado nem conectado à produção; o banco fornecido no material original estava vazio.

## Executar localmente
Com Python 3.11, instale `requirements.txt` e inicie com `streamlit run app.py`. Não substitua o banco real por um SQLite vazio.
