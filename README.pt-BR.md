[🇺🇸 English](README.md) | [🇧🇷 Português](README.pt-BR.md)

# privguard

privguard é um pacote Python local-first que intercepta dados pessoais brasileiros (PII) e
segredos antes que eles alcancem provedores externos de LLM como Anthropic ou OpenAI. Ele
roda inteiramente no seu ambiente de desenvolvimento — não há componente de serviço hospedado.
Quando a detecção não consegue produzir um payload seguro verificado, o privguard falha de
forma fechada (fail-closed) e bloqueia o prompt em vez de permitir a passagem de dados sensíveis.

O foco inicial é em dados sensíveis brasileiros: CPF, CNPJ, CNH, dados bancários e de conta,
chaves de API, variáveis de ambiente, credenciais e arquivos locais sensíveis. O pacote age
localmente na fronteira do agente (Claude Code `UserPromptSubmit` + `PreToolUse`) para impedir
que dados sensíveis saiam da máquina.

## Instalação

```bash
pip install privguard            # instalação base (sem dependências de runtime de terceiros)
pip install "privguard[full]"    # adiciona o analisador Presidio para detecção mais rica
```

Requer Python ≥ 3.10. Para notas de compatibilidade do extra `[full]` com Python 3.14, consulte
[`docs/install.md`](docs/install.md).

## Início rápido

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
mapa de desanonimização.

Todos os valores acima são fixtures sintéticos de teste — consulte
[Política de fixture-apenas-sintéticos](#política-de-fixture-apenas-sintéticos).

## Uso da CLI

```bash
privguard info             # versão + superfície do módulo
privguard scan <text>      # somente detecção — tipos de entidade, contagens, offsets, códigos de razão
privguard mask <text>      # detecção + substituição irreversível por placeholder
privguard policy-check     # decide se um payload pode sair (padrão fail-closed)
privguard claude doctor    # instalação do hook do Claude + diagnóstico de política efetiva
privguard cleanup          # prévia em modo dry-run de artefatos limpáveis (use --apply para deletar)
```

Execute qualquer subcomando com `--help` para ver todas as flags.

Comportamentos principais:

- `privguard scan` e `privguard mask` leem da stdin quando nenhum argumento posicional é fornecido.
- `privguard policy-check` é fail-closed por padrão: alvos de provedor desconhecidos ou não
  classificados são tratados como externos e exigem mascaramento verificado.
- `privguard cleanup` é dry-run por padrão. Passe `--apply` para realmente deletar. A lista
  protegida hardcoded (`.env`, `data_sensivel/`, `.git/`, diretórios de código-fonte) é sempre
  respeitada, independentemente dos padrões que aparecem em `pyproject.toml`.
- `privguard claude doctor` não lê nenhum arquivo protegido — ele inspeciona apenas metadados do hook.

## Configuração do hook do Claude Code

Após instalar o privguard, configure dois hooks no arquivo `.claude/settings.json` do seu
projeto Claude Code:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "privguard-user-prompt" }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          { "type": "command", "command": "privguard-pre-tool" }
        ]
      }
    ]
  }
}
```

Esses dois console scripts são instalados com `pip install privguard` (declarados em
`pyproject.toml [project.scripts]`). Eles são independentes do caminho de instalação —
o Claude Code os encontra no `PATH` após a instalação.

Verifique sua instalação com `privguard claude doctor` — ele informa se os hooks estão
configurados sem ler nenhum arquivo protegido.

## Matriz de capacidades

Status de interceptação de privacidade por superfície (evidências da Fase 3 + Fase 4):

| Superfície | Status | Notas |
|---|---|---|
| Claude Code `UserPromptSubmit` | block-supported | Verificado na Fase 3 |
| Claude Code `PreToolUse` | block-supported | Verificado na Fase 3 |
| Hook de prompt do Codex | experimental block-only | Evidência da Fase 4 |
| Hook de ferramenta do Codex | experimental block-only | Evidência da Fase 4 |

Para evidências completas e lacunas restantes, consulte
[`docs/codex-compatibility.md`](docs/codex-compatibility.md).

## O que o privguard NÃO faz

privguard é uma ferramenta focada e local-first. Deliberadamente NÃO:

- **Funciona como SaaS hospedado ou proxy na nuvem.** A fronteira de privacidade permanece na
  sua máquina; dados brutos nunca saem dela via privguard.
- **Desanonimiza saída mascarada (sem superfície de desanonimização).** A v1 usa mascaramento
  irreversível — não há superfície de gerenciamento de chaves ou retenção para reverter um
  placeholder `<BR_CPF>` de volta ao original.
- **Adapta-se a pipelines LangChain, LlamaIndex ou SDK genérico.** A integração suportada é o
  Claude Code (`block-supported`); o Codex é `experimental block-only`. Consulte
  [Matriz de capacidades](#matriz-de-capacidades).
- **Protege clientes não suportados.** Clientes sem interceptação testada (sem evento de hook
  documentado, sem prova de interceptação sintética) não são rotulados como protegidos — são
  rotulados como `unsupported`.
- **Usa PII brasileiro real ou segredos de produção em testes, fixtures, exemplos ou commits.**
  Todos os valores neste repositório de testes são sintéticos. Consulte
  [Política de fixture-apenas-sintéticos](#política-de-fixture-apenas-sintéticos).

## Política de fixture-apenas-sintéticos

O conjunto de testes, exemplos de código e documentação do privguard usam apenas identificadores
brasileiros sintéticos e strings sintéticas com formato de segredo. Os valores sintéticos de CPF,
CNPJ e CNH mostrados em [Início rápido](#início-rápido) vêm de `tests/test_v1_regression_gate.py`
e são válidos em checksum, mas obviamente fabricados.

Fazemos isso porque PII real em um repositório público reproduziria o risco de exfiltração que
o privguard foi construído para prevenir. O `.gitignore` do repositório e a lista hardcoded
`_PROTECTED` da ferramenta de limpeza (em `privguard/cleanup.py`) tratam `.env`, `data_sensivel/`
e os caminhos com flag brasileira como intocáveis.

Se você contribuir com um teste, fixture ou exemplo, use as constantes existentes em
`tests/test_v1_regression_gate.py` em vez de inventar novos valores — esse arquivo é a única
fonte de verdade para fixtures sintéticos.

## FAQ

### Isso funciona com o Codex?

Os hooks do Codex são rotulados como `experimental block-only` na
[Matriz de capacidades](#matriz-de-capacidades) — o privguard pode bloquear prompts sensíveis
e payloads de ferramentas, mas não reivindica mascaramento no Codex — apenas bloqueio. As
evidências de suporte e as lacunas restantes estão documentadas em
[`docs/codex-compatibility.md`](docs/codex-compatibility.md). Trate a proteção do Codex como
bloqueio de melhor esforço até que a substituição de payload de saída seja comprovada.

### E se um CPF for perdido?

A detecção do privguard é fail-closed por design — quando um CPF (ou qualquer PII) não pode ser
mascarado com confiança, o hook bloqueia o prompt em vez de deixá-lo passar. Se você suspeita de
um CPF perdido, execute `privguard claude doctor` para verificar a instalação do hook e a política
efetiva, e `privguard scan "<texto>"` para ver o que o detector enxerga. O privguard é uma camada
de defesa, não uma garantia de 100% de recall.

### Por que ele bloqueia em vez de avisar?

O modo somente-aviso está explicitamente fora do escopo (consulte
[O que o privguard NÃO faz](#o-que-o-privguard-não-faz)). O valor central do privguard é impedir
que dados sensíveis alcancem um provedor externo de LLM — um aviso que o usuário pode ignorar não
satisfaria esse objetivo. O comportamento fail-closed estrito é o padrão para fluxos de trabalho
com provedores externos; a reescrita é usada apenas em superfícies onde a substituição de payload
de saída é verificada.

### Como estendo os padrões de limpeza?

Adicione o novo padrão a `[tool.privguard.cleanup]` em `pyproject.toml`, E adicione o mesmo
padrão ao `.gitignore` para que artefatos transitórios não possam ser commitados antes da próxima
execução de limpeza. A convenção de barra final é importante: `__pycache__/` corresponde a uma
árvore de diretórios recursivamente; `*.py[cod]` corresponde a arquivos por glob de basename.

```toml
[tool.privguard.cleanup]
patterns = [
    "__pycache__/",
    "*.py[cod]",
    # ...seu novo padrão aqui...
]
```

A ferramenta de limpeza lê esta lista em tempo de execução; a lista protegida hardcoded (`.env`,
`data_sensivel/`, diretórios de código-fonte) não pode ser substituída.

## Para agentes de código

Para agentes de código trabalhando neste repositório, consulte [AGENTS.md](AGENTS.md).

O `AGENTS.md` documenta a estrutura do projeto, convenções de código, caminhos protegidos e
contratos de segurança que se aplicam quando um agente de IA modifica esta base de código.
Regras principais que os agentes devem observar:

- Nunca leia ou escreva em `.env`, `data_sensivel/` ou qualquer caminho na lista hardcoded
  `_PROTECTED` em `privguard/cleanup.py`.
- Use apenas fixtures sintéticos de `tests/test_v1_regression_gate.py` em testes, exemplos e
  documentação — nunca invente novos valores de PII brasileiro.
- Siga o padrão fail-closed: em caso de dúvida sobre a capacidade de uma superfície, bloqueie
  em vez de permitir.
