# Auditoria de seguranca preliminar

Data: 2026-07-31

| Item | Severidade | Acao nesta branch |
|---|---:|---|
| Uploads/fotos reais versionados | Alta | Removidos do conteudo atual |
| PRDs e relatorios internos com credenciais/dados | Alta | Removidos do conteudo atual |
| `SECRET_KEY` com fallback hardcoded | Alta | Removido; variavel obrigatoria |
| Senha admin hardcoded em seed | Alta | Substituida por `ADMIN_PASSWORD` |
| `.gitignore` sem cobertura para uploads/memory/test reports | Media | Reforcado |

## Pendencias

- Limpar historico Git antigo.
- Confirmar se o repositorio deve permanecer publico.
- Rotacionar a credencial antiga se usada fora de ambiente demonstrativo.
- Revisar dados seed demonstrativos antes de qualquer deploy publico.
