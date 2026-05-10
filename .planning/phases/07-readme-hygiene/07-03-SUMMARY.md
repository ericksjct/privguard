---
plan: 07-03
phase: 07-readme-hygiene
status: complete
completed: 2026-05-10
requirements: [DOC-01]
---

## Summary

Created `README.pt-BR.md` — a full Brazilian Portuguese translation of `README.md` — closing DOC-01 and resolving the broken cross-language switcher link.

## What was built

- **README.pt-BR.md** (217 lines) at repo root — full pt-BR translation of all 9 D-04 sections

## Verification

All acceptance criteria passed:

| Check | Result |
|-------|--------|
| File exists at repo root | ✓ |
| Line 1 is cross-language switcher | ✓ `[🇺🇸 English](README.md) \| [🇧🇷 Português](README.pt-BR.md)` |
| `block-supported` ≥ 2 | ✓ (3 occurrences) |
| `experimental block-only` ≥ 2 | ✓ (4 occurrences) |
| `privguard-user-prompt` present | ✓ |
| `privguard-pre-tool` present | ✓ |
| `<BR_CPF>` present | ✓ |
| `<BR_CNPJ>` present | ✓ |
| `<TOKEN>` present | ✓ |
| ≥ 150 lines | ✓ (217 lines) |
| All 9 D-04 sections in pt-BR | ✓ |
| Broken link resolved | ✓ |

## All 9 D-04 sections present

1. Instalação (line 16)
2. Início rápido (line 26)
3. Uso da CLI (line 51)
4. Configuração do hook do Claude Code (line 74)
5. Matriz de capacidades (line 108)
6. O que o privguard NÃO faz (line 122)
7. Política de fixture-apenas-sintéticos (line 141)
8. FAQ (line 157)
9. Para agentes de código (line 204)

## DOC-01 closure

DOC-01 is **fully satisfied**:
- English half: `README.md` (completed by plan 07-02)
- Portuguese half: `README.pt-BR.md` (completed by this plan)

Both files share the same cross-language switcher on line 1, linking bidirectionally.

## Key files

- `README.pt-BR.md` — created (217 lines)

## Self-Check: PASSED
