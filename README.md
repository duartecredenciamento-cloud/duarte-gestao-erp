# Duarte Repay

Aplicação web para controle de reembolsos, com interface HTML/CSS/JavaScript, servidor Python e SQLite.

## O que está incluído

- Acesso por CPF/login, cadastro de colaboradores e perfil administrativo.
- Solicitações com descrição, categoria, centro de custo, valor, data e comprovante PDF/JPG/PNG.
- Fluxo de aprovação, notificações, edição de solicitações elegíveis e exportação CSV.
- **WhatsApp:** em cada detalhe existe uma mensagem preparada que pode ser revisada; o botão abre a conversa (para administradores, o número cadastrado do colaborador quando disponível). O envio continua manual, feito pela pessoa no WhatsApp.
- **Meus pedidos:** contador do total de solicitações, independente dos filtros selecionados.
- **Painel executivo:** cartões reorganizados e gráficos responsivos para centros de custo e categorias, com rótulos e valores legíveis.
- Importação controlada de CSV/ZIP e ferramentas de OCR locais opcionais.

## Executar localmente

Requer Python 3.11+ e não usa dependências Python externas.

```bash
python server.py
```

Acesse `http://localhost:8080`. Para criar o primeiro administrador, configure `SESSION_SECRET`, `ADMIN_BOOTSTRAP_PASSWORD`, `ADMIN_BOOTSTRAP_CPF` e `ADMIN_BOOTSTRAP_NAME` antes do primeiro início. Não use credenciais de exemplo em produção.

Para execução em HTTPS, mantenha `COOKIE_SECURE=1`. Em testes locais com HTTP, use `COOKIE_SECURE=0`.

## Testes

```bash
python tests/smoke_test.py
```

## Deploy e dados

Antes de publicar, configure uma chave de sessão persistente e um volume persistente para o banco e comprovantes. Faça backup e teste a restauração. **Este pacote é uma atualização do código-fonte, não publica automaticamente a versão no Railway nem migra os dados do sistema atual.** Teste primeiro em homologação e confira o repositório, as variáveis privadas e as permissões antes de substituir o serviço em produção.

## Principais arquivos

- `server.py` — servidor e regras da aplicação.
- `static/index.html`, `static/app.css`, `static/app.js` — interface e comportamento.
- `tests/smoke_test.py` — teste de fumaça.
