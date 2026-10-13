# Duarte Gestão — Painel administrativo

Cópia de trabalho do aplicativo Streamlit com melhoria da área de administração. Mantém o banco SQLite e os fluxos de status já existentes (`PENDENTE`, `APROVADO`, `PAGO`, `NEGADO`); não importa o CSV automaticamente e não altera dados de produção.

## Executar

1. Use uma cópia/ambiente de teste, nunca a base de produção para o primeiro teste.
2. Instale as dependências listadas em `requirements.txt`.
3. Execute `streamlit run app.py`.

A cópia não inclui banco de dados: o arquivo SQLite de origem no pacote estava vazio. Ao iniciar sem configurar corretamente o banco, a aplicação pode criar uma base vazia. **Não publique esta cópia no ambiente real antes de confirmar e testar o caminho/conexão do banco usado pela versão atualmente implantada.** O pacote também não inclui a pasta com comprovantes: o CSV guarda caminhos de referência, não os arquivos de imagem/PDF. Recupere os comprovantes a partir de backup de arquivos ou volume persistente antes de presumir que estão disponíveis.

## O que mudou

- Filtros de funcionário, status, categoria, período e busca por descrição/centro de custo/ID.
- Ordenação e paginação de 50 itens por vez; filtros e limites são aplicados na consulta SQLite.
- Contadores por status.
- Ações individuais para aprovação, pagamento e recusa, com verificação do status atual e notificação já existente.
- Lista administrativa de usuários sem exibir CPF, telefone, e-mail ou senha.
- A mensagem WhatsApp permanece uma abertura de texto pré-preenchido e não é tratada como confirmação de envio.

Não há ações em lote. “Mensagem enviada” não é um status persistido no esquema existente.
