<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![CI][ci-shield]][ci-url]
[![Python][python-shield]][python-url]
[![License][license-shield]][license-url]

[🇧🇷 Português](README.md) | [🇺🇸 English](README.en.md)

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/ericksjct/privguard">
    <img src="privguard_thumb.png" alt="privguard" width="520">
  </a>

  <h3 align="center">privguard</h3>

  <p align="center">
    Guarda local-first que impede PII brasileiro e segredos de vazarem para LLMs externos.
    <br />
    <a href="docs/install.md"><strong>Explore a documentação »</strong></a>
    <br />
    <br />
    <a href="https://github.com/ericksjct/privguard/issues/new?labels=bug">Reportar bug</a>
    &middot;
    <a href="https://github.com/ericksjct/privguard/issues/new?labels=enhancement">Pedir feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Índice</summary>
  <ol>
    <li>
      <a href="#sobre-o-projeto">Sobre o projeto</a>
      <ul>
        <li><a href="#construído-com">Construído com</a></li>
      </ul>
    </li>
    <li>
      <a href="#começando">Começando</a>
      <ul>
        <li><a href="#pré-requisitos">Pré-requisitos</a></li>
        <li><a href="#instalação">Instalação</a></li>
      </ul>
    </li>
    <li>
      <a href="#uso">Uso</a>
      <ul>
        <li><a href="#início-rápido">Início rápido</a></li>
        <li><a href="#cli">CLI</a></li>
        <li><a href="#hook-do-claude-code">Hook do Claude Code</a></li>
        <li><a href="#o-que-o-privguard-captura">O que captura</a></li>
        <li><a href="#o-que-o-privguard-não-captura-por-padrão">O que não captura</a></li>
        <li><a href="#comportamento-fail-closed">Comportamento fail-closed</a></li>
        <li><a href="#matriz-de-capacidades">Matriz de capacidades</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contribuindo">Contribuindo</a></li>
    <li><a href="#licença">Licença</a></li>
    <li><a href="#contato">Contato</a></li>
    <li><a href="#agradecimentos">Agradecimentos</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## Sobre o projeto

privguard é um pacote Python local-first que intercepta dados pessoais brasileiros (PII) e
segredos antes que eles alcancem provedores externos de LLM como Anthropic ou OpenAI. Ele
roda inteiramente no seu ambiente de desenvolvimento — não há componente de serviço hospedado.
Quando a detecção não consegue produzir um payload seguro verificado, o privguard falha de
forma fechada (fail-closed) e bloqueia o prompt em vez de permitir a passagem de dados sensíveis.

O foco inicial é em dados sensíveis brasileiros: CPF, CNPJ, CNH, dados bancários e de conta,
chaves de API, variáveis de ambiente, credenciais e arquivos locais sensíveis. O pacote age
localmente na fronteira do agente (Claude Code `UserPromptSubmit` + `PreToolUse`) para impedir
que dados sensíveis saiam da máquina.

Por que ele existe:

* **Zero vazamento em texto claro** para provedores externos é o valor central — não um efeito colateral.
* **Fail-closed por padrão** — na dúvida, bloqueia. Uma falha do detector ou input hostil bloqueia, nunca libera silenciosamente.
* **Fixtures apenas sintéticos** — PII real nunca entra em testes, exemplos ou commits.

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

### Construído com

[![Python][python-badge]][python-url]
[![Presidio][presidio-badge]][presidio-url]
[![spaCy][spacy-badge]][spacy-url]

O caminho de detecção base é stdlib-only (sem dependências de terceiros em runtime). O extra
`[full]` adiciona o Microsoft Presidio + spaCy para detecção mais rica.

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- GETTING STARTED -->
## Começando

### Pré-requisitos

Python ≥ 3.10. Para notas de compatibilidade do extra `[full]` com Python 3.14, consulte
[`docs/install.md`](docs/install.md).

### Instalação

```bash
pip install privguard            # instalação base (sem dependências de runtime de terceiros)
pip install "privguard[full]"    # adiciona o analisador Presidio para detecção mais rica
```

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- USAGE EXAMPLES -->
## Uso

### Início rápido

Após instalar, redirecione qualquer texto para `privguard mask` para substituir valores sensíveis
detectados por placeholders tipados. O privguard nunca modifica a fonte original — ele imprime a
saída mascarada no stdout e encerra:

```bash
$ echo "CPF do cliente: 123.456.789-09" | privguard mask
CPF do cliente: <BR_CPF>

$ echo "CNPJ da empresa: 12.345.678/0001-95" | privguard mask
CNPJ da empresa: <BR_CNPJ>

$ echo "token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890" | privguard mask
token: <TOKEN>
```

Os placeholders seguem o vocabulário da Fase 2: `<BR_CPF>` para CPF brasileiro,
`<BR_CNPJ>` para CNPJ, `<TOKEN>` para tokens de acesso pessoal do GitHub e strings
similares com formato de segredo. O mascaramento é irreversível — a v1 não persiste um
mapa de desanonimização. Todos os valores acima são fixtures sintéticos de teste.

### CLI

```bash
privguard info             # versão + superfície do módulo
privguard scan <text>      # somente detecção — tipos de entidade, contagens, offsets, códigos de razão
privguard mask <text>      # detecção + substituição irreversível por placeholder
privguard policy-check     # decide se um payload pode sair (padrão fail-closed)
privguard claude doctor    # instalação do hook do Claude + diagnóstico de política efetiva
privguard cleanup          # prévia em modo dry-run de artefatos limpáveis (use --apply para deletar)
```

Execute qualquer subcomando com `--help` para ver todas as flags. Comportamentos principais:

* `privguard scan` e `privguard mask` leem da stdin quando nenhum argumento posicional é fornecido.
* `privguard policy-check` é fail-closed por padrão: alvos de provedor desconhecidos ou não
  classificados são tratados como externos e exigem mascaramento verificado.
* `privguard cleanup` é dry-run por padrão. Passe `--apply` para realmente deletar. A lista
  protegida hardcoded (`.env`, `data_sensivel/`, `.git/`, diretórios de código-fonte) é sempre
  respeitada, independentemente dos padrões que aparecem em `pyproject.toml`.
* `privguard claude doctor` não lê nenhum arquivo protegido — ele inspeciona apenas metadados do hook.

### Hook do Claude Code

Após instalar o privguard, configure dois hooks no arquivo `.claude/settings.json` do seu
projeto Claude Code:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "privguard-user-prompt" } ] }
    ],
    "PreToolUse": [
      { "matcher": ".*", "hooks": [ { "type": "command", "command": "privguard-pre-tool" } ] }
    ]
  }
}
```

Esses dois console scripts são instalados com `pip install privguard` (declarados em
`pyproject.toml [project.scripts]`) e independem do caminho de instalação — o Claude Code os
encontra no `PATH`. Verifique com `privguard claude doctor`, que informa se os hooks estão
configurados sem ler nenhum arquivo protegido.

### O que o privguard captura

Tudo abaixo é **saída comprovada**, não uma lista de desejos. É o resultado literal de passar
um arquivo de fixtures sintéticos pelo `privguard mask` nas configurações padrão (modo estrito),
reproduzível com o conjunto de testes em `tests/test_detection.py`:

```text
CPF 123.456.789-09                      →  CPF <BR_CPF>
CNPJ 12.345.678/0001-95                 →  CNPJ <BR_CNPJ>
CNH 12345678900                         →  CNH <BR_CNH>
PIS 123.45678.90-0                      →  PIS <BR_PIS_PASEP>
SUS 123 4567 8901 2348                  →  SUS <BR_CARTAO_SUS>
RG 12.345.678-9                         →  RG <BR_RG>
celular +55 (11) 91234-5678             →  celular <BR_PHONE>
CEP 01310-200                           →  CEP <BR_CEP>
placa ABC-1234 e BRA1A23                →  placa <BR_PLACA_OLD> e <BR_PLACA_MERCOSUL>
api_key=sk-test-abcdefghij...           →  api_key=<API_KEY>
token ghp_ABCDEFGHIJ...                 →  token <TOKEN>
DATABASE_URL=postgres://user:pass@...   →  DATABASE_URL=<DATABASE_URL>
email contato@exemplo.com.br            →  email <EMAIL>
```

Também detectado pelo mesmo motor e coberto por `tests/test_detection.py`: IBAN (inclusive
separado por espaços), códigos de barras de boleto (`<BR_BOLETO>`), agência e conta bancária,
endereços, título de eleitor, IPs privados/públicos, cartões de crédito que passam no dígito
Luhn, chaves AWS, JWTs e atribuições `KEY=`/`SECRET=`/`PASSWORD=`.

Identificadores brasileiros são validados pelo seu **checksum** antes do mascaramento — uma
sequência aleatória de 11 dígitos não é tratada como CPF. É isso que mantém os falsos positivos
baixos; é também a origem das lacunas deliberadas abaixo.

### O que o privguard NÃO captura (por padrão)

Isto não são bugs — são limites documentados e testados. Os dois primeiros **passam intactos**
a menos que você opte explicitamente por ativá-los:

| Entrada (sintética) | Modo estrito (padrão) | Opt-in |
|---|---|---|
| `Maria Silva` (nome de pessoa) | `Maria Silva` — **não mascarado** | `PII_GUARD_DETECT_NAMES=true` → `<BR_NAME>` |
| `456.789.123-45` (CPF com checksum inválido) | `456.789.123-45` — **não mascarado** | `PII_GUARD_LENIENT=true` → `<BR_CPF>` |
| `45678912345` (11 dígitos crus, sem pontos/traço) | não mascarado como CPF | continua estrito mesmo no modo leniente (guarda de formato) |

* **Nomes ficam desligados por padrão** porque a correspondência em texto livre produz falsos
  positivos demais para ser habilitada globalmente. Ative com `PII_GUARD_DETECT_NAMES=true`.
* **Identificadores com checksum inválido ficam desligados por padrão** porque a validação estrita
  é o que impede que números cotidianos sejam mascarados por engano. Só são mascarados com
  `PII_GUARD_LENIENT=true`, e mesmo assim apenas no formato **com pontuação** `DDD.DDD.DDD-DD`.
* **Mascaramento no Codex não é oferecido** — o Codex é `experimental block-only`. O privguard
  bloqueia payloads sensíveis do Codex, mas não os reescreve.

O privguard **não garante detecção contra um ofuscador deliberado**. É um scanner local que eleva
o custo de evasão acidental e de baixo esforço. A detecção resiste a homoglyphs, caracteres
zero-width/combining, fragmentação e concatenação de identificadores com checksum, e segredos
codificados em uma camada (base64/hex/URL). Ela **não** cobre, por design: interpolação em runtime
(`f"{cpf}"` só se monta ao executar, não no texto), codificação em múltiplas camadas, e
identificadores numéricos escondidos dentro de conteúdo codificado.

### Comportamento fail-closed

Fail-closed é o padrão mesmo quando algo dá errado no próprio guard:

* **Erro no detector:** se a detecção lançar uma exceção, o hook bloqueia (código de saída 2)
  com `reason=detector_error` — nunca vira liberação silenciosa.
* **Input grande demais:** prompts e comandos acima de um limite de caracteres são bloqueados com
  `reason=input_too_large` antes de serem escaneados. O limite padrão é 1.000.000 de caracteres
  (~1 MB), ajustável via `PII_GUARD_MAX_INPUT_CHARS`. O limite só se aplica na fronteira do hook;
  a CLI `scan`/`mask` continua processando arquivos grandes normalmente.

Bloquear é o comportamento padrão; o modo é configurável via `PII_GUARD_MODE`:

| Modo | `PII_GUARD_MODE` | Comportamento ao detectar PII | Saída | Protege? |
|------|------------------|-------------------------------|-------|----------|
| `block` (padrão) | não definida ou `block` | Bloqueia; diagnóstico sanitizado no stderr | 2 | Sim (fail-closed) |
| `warn` | `warn` | Deixa passar; marca `mode_scope=local_development_non_protective` | 0 | **Não** — opt-in |
| `mask` | `mask` | Bloqueia (saída 2) e mostra versão mascarada no stderr para reenvio manual | 2 | Sim |

O modo `warn` é **explicitamente não protetivo** (dev local). O modo `mask` nunca encaminha
automaticamente um payload sanitizado — o esquema `UserPromptSubmit` do Claude Code não tem campo
de substituição de prompt, então bloquear e imprimir a versão mascarada é o único caminho seguro.

### Matriz de capacidades

Status de interceptação de privacidade por superfície (evidências da Fase 3 + Fase 4):

| Superfície | Status | Notas |
|---|---|---|
| Claude Code `UserPromptSubmit` | block-supported | Verificado na Fase 3 |
| Claude Code `PreToolUse` | block-supported | Verificado na Fase 3 |
| Hook de prompt do Codex | experimental block-only | Evidência da Fase 4 |
| Hook de ferramenta do Codex | experimental block-only | Evidência da Fase 4 |

Para evidências completas e lacunas restantes, consulte
[`docs/codex-compatibility.md`](docs/codex-compatibility.md).

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- ROADMAP -->
## Roadmap

Milestone v1.0 — todas as fases entregues e verificadas:

- [x] Fundação do pacote + CLI (`privguard`)
- [x] Núcleo de privacidade (detecção BR-first, mascaramento irreversível, política fail-closed)
- [x] Enforcement no Claude Code (`UserPromptSubmit` + `PreToolUse`)
- [x] Evidência de compatibilidade com Codex (rotulada honestamente)
- [x] Gate de regressão sintético + hardening de detecção
- [x] Hardening fail-closed (erro de detector, input gigante, ReDoS, evasão) — verificado
- [ ] Mascaramento automático via `updatedInput` no `PreToolUse` (superfície de rewrite)
- [ ] E2E dos hooks, encoding legado (cp1252), precedência de config (backlog v1.1)

Veja [issues abertas](https://github.com/ericksjct/privguard/issues) para o backlog completo.

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- CONTRIBUTING -->
## Contribuindo

Contribuições são o que torna a comunidade open-source um lugar incrível para aprender e criar.
Qualquer contribuição é **muito bem-vinda**.

1. Faça um fork do projeto
2. Crie sua branch de feature (`git checkout -b feature/algo-incrivel`)
3. Rode a suíte com o gate de cobertura (`python -m pytest`)
4. Commit (`git commit -m 'feat: adiciona algo incrível'`)
5. Push para a branch (`git push origin feature/algo-incrivel`)
6. Abra um Pull Request

**Regra inegociável — fixtures apenas sintéticos:** nunca use PII brasileiro real ou segredos de
produção em testes, exemplos ou commits. Use as constantes existentes em
`tests/test_v1_regression_gate.py` — esse arquivo é a única fonte de verdade para fixtures
sintéticos. O `.gitignore` e a lista `_PROTECTED` da ferramenta de limpeza tratam `.env`,
`data_sensivel/` e caminhos com flag brasileira como intocáveis.

Consulte [AGENTS.md](AGENTS.md) para estrutura do projeto, convenções e contratos de segurança
que se aplicam quando um agente de IA modifica esta base de código.

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- LICENSE -->
## Licença

Distribuído sob a Licença Apache 2.0. Veja [`LICENSE`](LICENSE) para mais informações.

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- CONTACT -->
## Contato

ericksjct — via [issues do GitHub](https://github.com/ericksjct/privguard/issues)

Link do projeto: [https://github.com/ericksjct/privguard](https://github.com/ericksjct/privguard)

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- ACKNOWLEDGMENTS -->
## Agradecimentos

* [Microsoft Presidio](https://github.com/microsoft/presidio) — detecção de PII no caminho `[full]`
* [spaCy](https://spacy.io) — modelos de linguagem em português
* [Best-README-Template](https://github.com/othneildrew/Best-README-Template) — estrutura deste README
* [Shields.io](https://shields.io) — badges

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
[ci-shield]: https://img.shields.io/github/actions/workflow/status/ericksjct/privguard/ci.yml?style=for-the-badge
[ci-url]: https://github.com/ericksjct/privguard/actions/workflows/ci.yml
[python-shield]: https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white
[python-url]: https://www.python.org/
[license-shield]: https://img.shields.io/badge/license-Apache%202.0-green?style=for-the-badge
[license-url]: LICENSE
[python-badge]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[presidio-badge]: https://img.shields.io/badge/Microsoft%20Presidio-0078D4?style=for-the-badge&logo=microsoft&logoColor=white
[presidio-url]: https://github.com/microsoft/presidio
[spacy-badge]: https://img.shields.io/badge/spaCy-09A3D5?style=for-the-badge&logo=spacy&logoColor=white
[spacy-url]: https://spacy.io
