# HANDOFF: Productionize → Implementer — Fase: Hardening de testes (fail-closed first)

> Sugestão de path: `docs/gsd/handovers/hardening-testes-fail-closed.md`
> Projeto: **privguard** — guarda local-first de PII/segredos antes de LLM externo.

---

## Contexto mínimo

O projeto tem 85 testes de detecção/masking passando, mas todos exercitam o **caminho feliz** ("PII bem-formatada → mascara"). Falta cobertura de tudo que define uma ferramenta *fail-closed* de segurança: caminho de falha, evasão, e robustez da própria detecção. Coverage real está **desconhecido** (README reporta contagem de testes, não `--cov`).

Esta fase fecha esses buracos. Ordem por severidade: o que torna a ferramenta contornável ou silenciosamente fail-open vem primeiro.

---

## Mudança

Adicionar suítes de teste, guards de robustez e um gate de coverage. **Não** alterar a lógica de detecção existente exceto onde um teste novo provar bug (nesse caso, abrir thread de Fixer, não corrigir aqui).

---

## Pré-passo obrigatório — medir o baseline

Antes de escrever qualquer teste novo:

```bash
pytest --cov=privguard --cov-report=term-missing --cov-branch
```

Registrar o `%` de branch coverage e a lista de linhas/branches `missing` no HANDOFF de volta. **`--cov-branch` é mandatório** — numa ferramenta fail-closed, o que importa é cobertura dos ramos de *bloqueio*, não de linha.

---

## Passos (ordenados por dependência e severidade)

### TIER 1 — Quebram o propósito da ferramenta

**P1. Suíte fail-closed por injeção de falha** *(fazer primeiro — barato e crítico)*
Provar que toda falha do detector resulta em **block**, nunca em pass-through silencioso.
- Detector lança exceção → block
- Presidio (`[full]`) ausente mas invocado → degrada para block, não para allow
- Timeout do detector → block
- Input gigante (ex. 10 MB) → block ou rejeição explícita, nunca OOM/crash que mate o hook
- Config inválida no `pyproject.toml` → fail-closed, não stack trace que derruba o hook
- **Critério:** cada cenário tem um teste que asserta exit code / decisão de block. Zero caminhos onde exceção → allow.

**P2. Suíte de evasão / adversarial**
Inputs que tentam escapar da detecção:
- Unicode: homoglyphs (cirílico/fullwidth nos dígitos), zero-width chars no meio do CPF, combining chars
- Fragmentação: CPF quebrado entre linhas, whitespace injetado entre dígitos
- Encoding: secret em base64/hex/URL-encoded
- Concatenação em código: `"123.456" + ".789-09"`, f-strings
- PII dentro de code fence / markdown link / comentário
- **Critério:** cada vetor tem teste documentando o comportamento atual (mask, block, ou pass-through). Onde houver pass-through, marcar com label `RISCO` no STATE e abrir decisão — não silenciar.

**P3. Guard de ReDoS + limite de tamanho**
Regex sobre texto não-confiável roda em todo prompt.
- Teste de timeout por regex (input projetado para backtracking catastrófico)
- Guard de tamanho máximo de input antes da regex
- Avaliar migração das regex de risco para `re2` (sem backtracking) — registrar como ADR se adotado
- **Critério:** nenhum input sintético leva o detector a >N ms; guard de tamanho testado.

### TIER 2 — Pegam bug que passa verde

**P4. Mutation testing**
Rodar `mutmut` (ou `cosmic-ray`) sobre `privguard/` (foco: validadores de checksum e lógica de decisão block/allow).
- **Critério:** relatório de mutation score gerado; mutantes sobreviventes em código de checksum/decisão viram testes novos. (Contexto: histórico do projeto tem bug de sinal invertido mascarado por teste verde — é exatamente isso que mutation pega.)

**P5. Property-based nos validadores** (`hypothesis`)
- Nenhum CPF/CNPJ checksum-válido escapa; nenhum random 11-dígitos vira CPF
- Idempotência: `mask(mask(x)) == mask(x)`
- Lenient é superset estrito do strict (nunca mascara *menos* que strict)
- **Critério:** properties acima como testes hypothesis, sem falsos contraexemplos.

**P6. Edge cases dos checksums**
- Sequências repetidas (`111.111.111-11`, `000...`) que passam no DV clássico mas são inválidas → blacklist explícita e testada
- CNPJ análogo; DV = 0 (boundary)
- Cartão SUS: faixas definitivo (1,2) vs provisório (7,8,9)
- Placa antiga vs Mercosul: caso de ambiguidade/overlap
- **Critério:** cada edge tem teste; blacklist coberta.

**P7. Corpus de false positives + resolução de overlap**
- Montar corpus sintético de texto legítimo (código PT-BR, docs) e medir FP rate
- Testar overlap: `123.456.789-09` casando parcial com phone; determinismo da ordem quando entidades se sobrepõem
- **Critério:** FP rate medido e documentado; resolução de overlap determinística e testada.

### TIER 3 — Detector funciona, hook não

**P8. E2E real dos hooks**
- I/O real do `UserPromptSubmit`/`PreToolUse`: schema JSON via stdin/stdout, exit codes (block vs allow)
- Documentar/testar o comportamento do Claude Code se o **próprio hook** crashar (fail-open ou fail-closed do lado deles)
- **Critério:** teste E2E por console script (`privguard-user-prompt`, `privguard-pre-tool`); comportamento de crash documentado em `docs/`.

**P9. Cobertura de payload no `PreToolUse` (matcher `.*`)**
Risco real é PII *dentro* do payload da tool, não no prompt.
- `Read` puxando `.env`; `Bash` com `echo $DATABASE_URL`; `Write`/`Edit` gravando segredo
- **Critério:** teste por tipo de tool (Bash/Read/Write/Edit/Glob…) provando que o parser extrai o campo certo de cada um.

**P10. Precedência de config**
- env var vs `pyproject.toml` vs default; combinação `LENIENT` + `DETECT_NAMES`
- `policy-check` com provider desconhecido → tratado como external (afirmado no README — testar)
- **Critério:** matriz de precedência coberta.

**P11. Cleanup — path safety**
- `_PROTECTED` inviolável mesmo se `.env` aparecer nos patterns do `pyproject`
- Symlink apontando pra fora da protected list; path traversal (`../`) num pattern
- `--apply` respeita protected list
- **Critério:** cada vetor de escape testado; nenhum deleta path protegido.

### TIER 4 — Operacional / contexto corporativo (LGPD)

**P12. Observabilidade / auditoria**
- Log auditável no block **sem vazar o PII no próprio log**
- **Critério:** teste assertando que o log de um block não contém o valor sensível original; trilha mínima presente.

**P13. Encoding legado**
- Fixtures em `cp1252`/`latin-1` (comum em sistema financeiro BR) + BOM
- Pergunta-âncora: **CPF em arquivo cp1252 ainda é detectado?** (o re-encode para hex escapes pode destruir o match)
- **Critério:** teste multi-encoding; comportamento documentado se houver perda de recall.

**P14. Benchmark de latência**
- Hook no caminho crítico de cada prompt: medir p50/p99 com prompts grandes
- **Critério:** baseline de latência registrado (não precisa otimizar agora — só medir e documentar).

**P15. Matriz de versões + supply chain**
- CI testando Python 3.10→3.14 (gating 3.14 já mencionado nos docs)
- `[full]` (Presidio→spaCy→modelos): pinned/lockfile; scan de CVE
- **Critério:** matriz CI verde; deps pinadas.

**P16. Name detection (quando ligado)** *(menor prioridade)*
- FP/FN com nomes compostos, sobrenomes raros, acentuação contra IBGE Censo
- **Critério:** corpus próprio de FP/FN com baseline.

---

## Contrato técnico

- Stack de teste: `pytest`, `pytest-cov`, `hypothesis`, `mutmut`. Adicionar como dev-deps em `pyproject.toml`.
- Gate de coverage: configurar `--cov-fail-under=<X>` no `pyproject.toml`/CI. Definir `X` a partir do baseline do pré-passo (não chutar antes de medir). **Branch coverage**, não line.
- Cada suíte nova em arquivo próprio sob `tests/` seguindo o padrão de nomeação existente (`tests/test_*.py`).
- Onde um teste novo expuser bug de lógica: **não corrigir aqui** — registrar com label `RISCO` ou `DECISÃO`, abrir thread de Fixer.

## Arquivos a colar na thread do Implementer

- `pyproject.toml` (dev-deps, scripts, config de cov/cleanup)
- `privguard/cleanup.py` (lista `_PROTECTED`)
- `tests/test_detection.py` e `tests/test_v1_regression_gate.py` (padrão e fixtures sintéticos canônicos)
- Módulo(s) de validação de checksum e o módulo que decide block/allow
- Os console scripts dos hooks (`privguard-user-prompt`, `privguard-pre-tool`)
- `AGENTS.md`

## Critério de pronto (da fase)

1. Baseline de coverage medido e registrado.
2. Tiers 1 e 2 implementados e verdes (mínimo inegociável — são o núcleo do fail-closed).
3. Gate `--cov-fail-under` ativo no CI.
4. Mutation score reportado; mutantes sobreviventes em checksum/decisão tratados.
5. Qualquer pass-through de evasão marcado como `RISCO`/`DECISÃO`, nunca silenciado.

## Dependências

- Nenhuma externa de rede em runtime de teste (manter local-first). Modelos do Presidio, se necessários, mockados ou marcados `@pytest.mark.requires_full`.

## Restrições herdadas (do AGENTS.md — inegociáveis)

- **Nunca** ler ou escrever `.env`, `data_sensivel/`, ou qualquer path do `_PROTECTED` em `privguard/cleanup.py`.
- **Só** fixtures sintéticos de `tests/test_v1_regression_gate.py` — proibido inventar PII brasileira nova em teste/exemplo/doc.
- Padrão **fail-closed**: na dúvida sobre capability de uma surface, bloquear, não permitir.
- **Falha Segura:** se a sintaxe de uma lib de teste (`mutmut`, `hypothesis`) for incerta, admitir e perguntar — não alucinar API.

## Fora de escopo desta fase

- Codex masking (declarado `experimental block-only` no README — não é regressão).
- Deanonymization (v1 é irreversível por design).
- Integração LangChain/LlamaIndex/SDK genérico (declarado fora de escopo).
- Correção de bugs de lógica descobertos (vão pra Fixer, não pra cá).
- Otimização de performance (P14 só mede; otimizar é fase futura).