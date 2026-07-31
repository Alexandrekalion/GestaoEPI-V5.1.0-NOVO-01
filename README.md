# GestaoEPI V5.1.0 NOVO 01

Sistema web para gestao de EPIs, colaboradores, empresas, estoque, entregas, kits, relatorios e rastreabilidade operacional.

> Status: em revisao para organizacao profissional e saneamento de dados sensiveis.

## Tecnologias

- Python
- FastAPI
- MongoDB
- React
- Tailwind CSS

## Configuracao

Use `.env.example` como base e defina segredos reais somente no ambiente seguro.

Nunca versione `.env`, backups, bancos de dados, uploads reais, fotos, CPFs, dados biometricos, hashes de senha ou informacoes internas de clientes.

## Seguranca

Esta branch remove uploads/artefatos internos versionados do conteudo atual e exige `SECRET_KEY`/`ADMIN_PASSWORD` por ambiente. A remocao nao limpa historico Git antigo.

Veja [SECURITY.md](SECURITY.md) e [docs/security-audit.md](docs/security-audit.md).

## Licenca

Projeto proprietario. Todos os direitos reservados.
