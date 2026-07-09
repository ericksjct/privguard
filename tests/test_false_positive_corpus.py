"""P7 false-positive corpus + overlap-determinism tests (Phase 10 / TEST-07).

A synthetic corpus of legitimate PT-BR developer text (code, docs prose,
version numbers, dates, issue IDs) that must produce zero or near-zero hits;
the measured FP rate is asserted and recorded in the SUMMARY. Overlap tests
prove that when candidate spans compete, the winner is deterministic across
repeated runs.

No production code is changed. Competitive-overlap inputs reuse the canonical
synthetic constants from test_v1_regression_gate — no new PII is invented.
"""

from __future__ import annotations

from privguard.detection import detect

from test_v1_regression_gate import SYNTH_CPF, SYNTH_CNPJ

# ---------------------------------------------------------------------------
# Benign corpus — legitimate PT-BR developer text, expected to be clean
# ---------------------------------------------------------------------------

BENIGN_CORPUS: list[str] = [
    "def calcular_total(itens): return sum(i.preco for i in itens)",
    "atualize a dependencia para a versao 1.2.3 antes do deploy",
    "o bug foi corrigido no commit abc1234 da branch main",
    "reuniao marcada para 2024-01-15 as 14h no escritorio",
    "veja a issue ABC-123 e o PR #456 no repositorio",
    "o servico responde em http://localhost:8080/health",
    "instale com pip install privguard e rode os testes",
    "a cobertura de testes subiu de 82% para 86% neste ciclo",
    "erro na linha 42 do arquivo detection.py ao validar entrada",
    "o timeout padrao e de 30 segundos por requisicao",
    "documentacao disponivel em docs/install.md e docs/uso.md",
    "a versao do python usada e 3.14.3 no ambiente local",
    "revisar o modulo policy.py e o modulo masking.py amanha",
    "total de 1087 statements e 424 branches medidos",
    "chamada retornou status 200 com corpo json valido",
    "o arquivo pyproject.toml define as dependencias do projeto",
    "servidor na porta 5432 para o banco de dados de teste",
    "cpf, cnpj, e cartao sus sao tipos brasileiros suportados",
    "a data limite e 31/12/2024 para entrega do relatorio",
    "o hook roda em cada prompt antes do envio ao provedor",
]

# Measured FP rate on this corpus is 0.0 (see SUMMARY). The ceiling leaves
# headroom so a single benign-string regression is caught without CI flake.
FP_RATE_CEILING = 0.05


def _fp_rate() -> tuple[float, int, int]:
    docs_with_hits = 0
    total_hits = 0
    for text in BENIGN_CORPUS:
        hits = detect(text, lenient=False)
        if hits:
            docs_with_hits += 1
            total_hits += len(hits)
    return docs_with_hits / len(BENIGN_CORPUS), docs_with_hits, total_hits


def test_false_positive_rate_within_ceiling() -> None:
    rate, docs_with_hits, total_hits = _fp_rate()
    # Pin the measured rate: this corpus is designed to be clean, so the
    # current behavior is zero false positives.
    assert rate <= FP_RATE_CEILING, (
        f"FP rate {rate:.3f} exceeds ceiling {FP_RATE_CEILING} "
        f"({docs_with_hits} docs / {total_hits} hits)"
    )
    assert docs_with_hits == 0, "expected a clean benign corpus (0 false positives)"


def test_false_positive_corpus_is_nontrivial() -> None:
    # Guard the guard: a corpus that shrank to nothing would pass vacuously.
    assert len(BENIGN_CORPUS) >= 15


# ---------------------------------------------------------------------------
# Overlap resolution determinism
# ---------------------------------------------------------------------------


def _runs(text: str, n: int = 5) -> set[tuple[tuple[str, int, int], ...]]:
    return {
        tuple((h.kind, h.start, h.end) for h in detect(text, lenient=False))
        for _ in range(n)
    }


def test_cpf_vs_phone_overlap_is_deterministic() -> None:
    # A formatted CPF sits adjacent to a phone-shaped span; the detector must
    # pick the same winner on every run.
    text = f"contato {SYNTH_CPF} ou (11) 91234-5678 apos as 18h"
    runs = _runs(text)
    assert len(runs) == 1
    kinds = {kind for run in runs for (kind, _s, _e) in run}
    assert "BR_CPF" in kinds


def test_boleto_vs_pis_overlap_is_deterministic() -> None:
    # A 44-49 digit boleto barcode shares its digit run with shorter PIS/CPF
    # candidates; the longest/highest-score span must win deterministically.
    boleto = "0" * 47
    text = f"linha digitavel {boleto} referente ao pagamento"
    runs = _runs(text)
    assert len(runs) == 1


def test_valid_cnpj_overlap_stable() -> None:
    text = f"empresa {SYNTH_CNPJ} matriz e filial"
    runs = _runs(text)
    assert len(runs) == 1
    kinds = {kind for run in runs for (kind, _s, _e) in run}
    assert "BR_CNPJ" in kinds
