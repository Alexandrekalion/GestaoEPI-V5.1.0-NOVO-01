# Politica de seguranca

## Dados que nao devem ser versionados

- Arquivos `.env` reais.
- Senhas, tokens, hashes e chaves.
- Backups, bancos de dados e relatorios exportados.
- Fotos reais, uploads de entrega e dados biometricos.
- CPFs, dados de colaboradores, empresas ou clientes.
- Artefatos internos de agentes/testes.

## Pendencias

- Limpar historico Git antigo se dados ou credenciais ja estiverem publicados.
- Confirmar se o repositorio deve permanecer publico.
- Rotacionar qualquer segredo usado fora de ambiente demonstrativo.
