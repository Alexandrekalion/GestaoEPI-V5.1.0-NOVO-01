# Sistema de Gestão de EPI — PRD (Product Requirements Document)

> **Última atualização:** 28/04/2026
> **Versão atual:** 5.0.9 + Melhorias Críticas (E1)

## 1. Problema Original

A empresa utiliza o sistema **GestaoEPI v5.0.1** em produção, com 5 falhas operacionais críticas:

1. Reconhecimento facial identificando colaborador errado (falsos positivos).
2. Entrega de EPI sem variação de tamanho (P/M/G, 38/39/40).
3. Sem campo de quantidade — exigia adicionar o mesmo item várias vezes.
4. Termo de consentimento incompleto (só "Aceito", sem opção de recusa).
5. Recusa de biometria não era registrada na ficha/relatórios.

**Repositórios:**
- v5.0.1 (produção): https://github.com/Tr3mbolon4/GestaoEPI-V5.0.1
- v5.0.9 (mais nova): https://github.com/Tr3mbolon4/GestaoEPI-V5.0.9 (base utilizada)

## 2. Personas

- **Administrador / Gestor:** acesso total, audita logs, exporta relatórios PDF.
- **RH:** cadastra colaboradores, registra consentimento LGPD.
- **Segurança do Trabalho:** cadastra EPIs, fornecedores, kits.
- **Almoxarifado:** realiza entregas/devoluções com biometria.
- **Colaborador:** alvo das entregas; consentimento LGPD obrigatório.

## 3. Stack & Arquitetura

- Backend: **FastAPI + Motor (Mongo async)** — `/app/backend/server.py` (~2240 linhas, monolito por enquanto)
- Frontend: **React 19 + Tailwind + Radix UI + face-api.js (vladmandic)** — `/app/frontend/src/`
- Banco: **MongoDB** (`mongodb://localhost:27017`, DB `test_database` em dev)
- Auth: **JWT** com perfis (admin, gestor, rh, seguranca_trabalho, almoxarifado)
- Reconhecimento Facial: **TinyFaceDetector + FaceLandmark68 + FaceRecognitionNet** (descritor 128D)
- Deploy: **Emergent** (URLs vêm de `REACT_APP_BACKEND_URL` e `MONGO_URL`/`DB_NAME` no env)

## 4. Requisitos Estáticos (Core)

- Login com troca obrigatória de senha no primeiro acesso.
- Cadastro de colaboradores com foto + biometria facial opcional.
- Cadastro de EPIs (CA, NBR, validade, periodicidade de troca, tamanho).
- Entregas e devoluções com confirmação biométrica e/ou QR Code.
- Kits de EPI vinculados a setores (com obrigatoriedade).
- Alertas de EPI vencido / troca periódica.
- Relatórios PDF (entregas, ficha do colaborador, autenticação de ficha com QR).
- Auditoria de duplicidade biométrica (LGPD).
- Conformidade LGPD: log de consentimento (IP, data, navegador).

## 5. O que foi entregue (Sprint atual — 28/04/2026)

### ✅ Correções dos 5 problemas críticos da v5.0.1

| # | Problema | Solução implementada |
|---|---|---|
| 1 | Reconhecimento incorreto | Threshold subido **0.40 → 0.50**, **margem mínima de 0.06** entre 1º e 2º match (rejeita ambíguos), embedding `inputSize` **224 → 320** (melhor precisão), detection confidence **0.65 → 0.70**, log do top-2 no console |
| 2 | Sem variação de tamanho | Dropdown de seleção agrupa EPIs por nome+CA usando `<optgroup>`; quando há 2+ tamanhos, exige escolha. Badge de tamanho exibida no item |
| 3 | Sem quantidade | Input `<input type="number">` em cada item da entrega, validado contra `current_stock` (estoque máximo). |
| 4 | Termo de consentimento | Radios "Aceito" / "Não aceito" obrigatórios em **Colaboradores.js** (cadastro) e **ColaboradorDetalhes.js** (biometria). Recusa **bloqueia** captura de foto + cadastro de template + reconhecimento facial |
| 5 | Recusa não aparecia | Banner de status no Resumo da ficha + linha **"Biometria Facial"** no PDF + badge na lista de colaboradores. Endpoint `/biometric-consent` grava `accepted=false` com data e IP |

### ✅ Outras melhorias
- Devoluções (`is_return=true`) **não exigem mais** foto cadastrada (relaxado).
- PDF da ficha agora mostra status biométrico do colaborador.
- PDF de entregas e ficha mostram tamanho dos itens entregues.

### ✅ Validação
- **Backend:** 17/17 testes automatizados passaram (testing_agent_v3 — `/app/test_reports/iteration_1.json`).
- **Frontend:** Login carrega; formulários compilam sem lint errors.

## 6. Backlog / Próximos passos

### P1
- [ ] Frontend E2E: validar UX dos novos fluxos de entrega (size+qty) e do termo Aceito/Não aceito.
- [ ] Adicionar `photo_path` placeholder no seed do João da Silva (UX demo).
- [ ] Suprimir item duplicado se mesmo EPI for selecionado 2x — ou somar quantidade automaticamente.

### P2
- [ ] Refatorar `server.py` (2240 linhas) em routers: `auth_router`, `employees_router`, `deliveries_router`, `biometrics_router`, `reports_router`.
- [ ] Tornar `BIOMETRIC_DUPLICATE_THRESHOLD` configurável via env.
- [ ] Filtrar templates por setor/empresa antes de comparar (otimização para >5k templates).
- [ ] Migrar fluxo de modelos face-api.js para CDN local (resiliência offline).

### P3
- [ ] Dashboard analytics (entregas por mês, EPIs mais usados, custos).
- [ ] App mobile com câmera nativa para entregas em campo.
- [ ] Integração com folha de ponto / RH externo.

## 7. Comandos úteis

```bash
# Reiniciar serviços
sudo supervisorctl restart backend frontend

# Logs
tail -n 50 /var/log/supervisor/backend.err.log
tail -n 50 /var/log/supervisor/frontend.err.log

# Login admin (test)
curl -X POST $REACT_APP_BACKEND_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"administrador","password":"LR1a2b3c4567@"}'
```

## 8. URLs

- Preview: https://epi-delivery-enhance.preview.emergentagent.com
- API: https://epi-delivery-enhance.preview.emergentagent.com/api
