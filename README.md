# Duarte Repay

Aplicação web remodelada para controle de reembolsos, com interface HTML/CSS/JavaScript, servidor Python e SQLite. O tema escuro, acentos azul-ciano/laranja e animações sutis foram inspirados na referência Duarte Transcribe informada. A aplicação usa a logo enviada entre os materiais.

## O que está incluído

- Acesso por CPF ou login, cadastro de colaborador e recuperação mediante CPF, e-mail e telefone já registrados.
- Senhas armazenadas com PBKDF2-HMAC-SHA256 e sessões em cookie `HttpOnly`, `SameSite=Lax`.
- Dois perfis: colaborador (somente próprios pedidos) e administrador (central administrativa e painel executivo).
- Solicitação com descrição, categoria, centro de custo, valor, data e comprovante PDF/JPG/PNG.
- Edição/reenvio de pedidos pendentes ou negados, mantendo o comprovante atual.
- Fluxo validado de status: PENDENTE → APROVADO → PAGO, ou PENDENTE/APROVADO → NEGADO. Recusa exige motivo e gera notificação.
- Ações administrativas individuais e exclusão com confirmação; exportação CSV.
- Importação futura do CSV (formato do backup Duarte) ou ZIP com um CSV e comprovantes. A prévia valida usuários, status, valores, datas e duplicidade antes da confirmação. Os arquivos só são anexados quando o nome referenciado pelo CSV corresponde exatamente ao nome do comprovante dentro do ZIP. Não são feitas associações por aparência ou valor.
- Banco com WAL, timeout de lock e logs de auditoria.

## Requisitos

Python 3.11+; não requer pacotes externos.

## Executar localmente

```bash
python server.py
```

Abra `http://localhost:8080`.

Na primeira configuração, defina credenciais próprias antes de iniciar. Exemplo em macOS/Linux:

```bash
export SESSION_SECRET="uma-chave-aleatoria-longa-e-unica"
export ADMIN_BOOTSTRAP_PASSWORD="uma-senha-nova-com-ao-menos-10-caracteres"
export ADMIN_BOOTSTRAP_CPF="cpf-do-administrador-apenas-digitos"
export ADMIN_BOOTSTRAP_NAME="Nome do administrador"
python server.py
```

PowerShell:

```powershell
$env:SESSION_SECRET="uma-chave-aleatoria-longa-e-unica"
$env:ADMIN_BOOTSTRAP_PASSWORD="uma-senha-nova-com-ao-menos-10-caracteres"
$env:ADMIN_BOOTSTRAP_CPF="cpf-do-administrador-apenas-digitos"
$env:ADMIN_BOOTSTRAP_NAME="Nome do administrador"
python server.py
```

As variáveis de bootstrap criam o primeiro admin somente se ainda não existir nenhum administrador. Não use senha conhecida, exemplo literal nem credencial antiga do sistema. A senha não vem incluída no código. `ADMIN_BOOTSTRAP_EMAIL` e `ADMIN_BOOTSTRAP_PHONE` são opcionais.

## Persistência e deploy

No Railway, execute este app como serviço Python (não como site estático) e conecte **um volume persistente ao serviço da aplicação**, montado, por exemplo, em `/data`. Configure:

- `DATA_DIR=/data`
- `REEMBOLSO_DB_PATH=/data/duarte_repay.sqlite3`
- `REEMBOLSO_UPLOAD_DIR=/data/comprovantes`
- `SESSION_SECRET` (chave longa e aleatória)
- `COOKIE_SECURE=1` (padrão para produção com HTTPS)
- `ADMIN_BOOTSTRAP_PASSWORD`, `ADMIN_BOOTSTRAP_CPF` e `ADMIN_BOOTSTRAP_NAME` no primeiro arranque seguro.
- Start command: `python server.py` (ou `python3 server.py`).

Faça backup do volume e teste a restauração antes de atualizações. Nunca aponte este serviço para o Postgres de outro produto nem publique CSV, comprovantes, segredos, banco SQLite ou arquivos `.env` no GitHub. Use repositório privado e revise permissões/acesso.

`PORT` é fornecida pela plataforma. Se executar localmente em HTTP, defina `COOKIE_SECURE=0`; não desligue essa proteção em produção HTTPS.

## Importação futura

1. O administrador abre **Central do Admin → Importar backup**.
2. Envia o CSV sozinho ou um ZIP privado contendo exatamente um CSV e os comprovantes com os nomes referenciados pela coluna `caminho_arquivo`.
3. Revisa contagem, total, CPFs sem cadastro, comprovantes encontrados pelo nome e distribuição de status.
4. Cadastre/regularize os usuários antes de confirmar se algum CPF estiver ausente.
5. Confirma explicitamente. A importação é bloqueada se o banco já tiver qualquer solicitação, para não misturar históricos; configure uma base vazia, depois de protegida por backup. A mesma cópia exata de backup também é bloqueada contra nova importação.

A importação associa cada solicitação ao cadastro encontrado pelo CPF presente na coluna `usuario`. Ela **não importa nem descobre senhas existentes**. O modo de prévia não grava os lançamentos; a confirmação importa todas as linhas em transação SQLite. Faça cópia integral do banco e da pasta de comprovantes antes de migrar dados reais. CSVs/ZIPs podem conter dados pessoais/financeiros: use apenas conexão confiável, acesso administrativo e armazenamento privado.

## Limites e validação antes de produção

- Esta é uma implementação nova; não é uma atualização automática do SQLite legado e não se conecta ao Railway atual.
- Nenhum banco real, backup ou comprovante foi importado automaticamente. A seleção e associação de arquivos só ocorrem no futuro fluxo explícito de importação.
- O app ainda precisa de validação em ambiente de homologação, HTTPS, volume persistente, política de backup/retensão e teste de recuperação antes de migrar para produção.
- A recuperação de senha confirma CPF/e-mail/telefone e não envia código externo. Para produção, recomenda-se um fluxo de redefinição por e-mail verificado e limitação de tentativas.
- O cadastro público cria apenas perfil colaborador. O primeiro administrador é criado somente pela configuração de bootstrap.
- A interface executiva exibe totais e distribuição pagos; não substitui conferência contábil.

## Executar a verificação local

Na pasta do projeto, rode:

```bash
python tests/smoke_test.py
```

A verificação cria dados descartáveis em uma pasta temporária e cobre login, cadastro, sessão, envio de solicitação, controle de acesso e carregamento dos arquivos estáticos.

## Arquivos principais

- `server.py` — servidor e regras de negócio.
- `static/index.html` — estrutura da aplicação.
- `static/app.css` — tema visual, responsividade e animações.
- `static/app.js` — comportamento da interface.
- `static/logo.png` — logo Duarte fornecida.
- `Dockerfile`, `railway.json`, `.gitignore` — empacotamento e configuração inicial de deploy.
