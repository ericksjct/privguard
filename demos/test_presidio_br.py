"""
Teste do Microsoft Presidio para contexto BRASILEIRO.

PII coberta por recognizers customizados:
  - CPF (com validação de DV)
  - CNPJ (com validação de DV)
  - RG (formato comum SP/genérico)
  - CNH (com validação de DV)
  - Telefone BR (fixo/celular, com/sem DDD/+55)
  - CEP
  - Placa de veículo (antiga AAA-1234 e Mercosul AAA1A23)
  - Título de eleitor (com validação de DV)
  - PIS/PASEP/NIS (com validação de DV)
  - Cartão SUS (com validação Luhn-like)
  - E-mail e IP (recognizers padrão do Presidio reaproveitados)

Todos os dados abaixo são FICTÍCIOS, gerados apenas para teste.
"""
import re
from typing import List, Optional

from presidio_analyzer import (
    AnalyzerEngine,
    Pattern,
    PatternRecognizer,
    RecognizerRegistry,
    EntityRecognizer,
    RecognizerResult,
)
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


# --------------------------------------------------------------------------- #
# Validadores de dígito verificador
# --------------------------------------------------------------------------- #
def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def valida_cpf(cpf: str) -> bool:
    cpf = _digits(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in (9, 10):
        s = sum(int(cpf[n]) * ((i + 1) - n) for n in range(i))
        d = (s * 10) % 11
        d = 0 if d == 10 else d
        if d != int(cpf[i]):
            return False
    return True


def valida_cnpj(cnpj: str) -> bool:
    cnpj = _digits(cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    for pesos, pos in ((pesos1, 12), (pesos2, 13)):
        s = sum(int(cnpj[i]) * pesos[i] for i in range(len(pesos)))
        d = s % 11
        d = 0 if d < 2 else 11 - d
        if d != int(cnpj[pos]):
            return False
    return True


def valida_cnh(cnh: str) -> bool:
    cnh = _digits(cnh)
    if len(cnh) != 11 or cnh == cnh[0] * 11:
        return False
    dsc = 0
    s = 0
    for i, peso in enumerate(range(9, 0, -1)):
        s += int(cnh[i]) * peso
    dv1 = s % 11
    if dv1 >= 10:
        dv1 = 0
        dsc = 2
    s = 0
    for i, peso in enumerate(range(1, 10)):
        s += int(cnh[i]) * peso
    dv2 = (s % 11) - dsc
    if dv2 < 0:
        dv2 += 11
    if dv2 >= 10:
        dv2 = 0
    return dv1 == int(cnh[9]) and dv2 == int(cnh[10])


def valida_titulo_eleitor(t: str) -> bool:
    t = _digits(t)
    if len(t) < 10 or len(t) > 12:
        return False
    t = t.zfill(12)
    uf = int(t[8:10])
    if uf < 1 or uf > 28:
        return False
    s1 = sum(int(t[i]) * (i + 2) for i in range(8))
    dv1 = s1 % 11
    if dv1 == 10:
        dv1 = 0
    s2 = int(t[8]) * 7 + int(t[9]) * 8 + dv1 * 9
    dv2 = s2 % 11
    if dv2 == 10:
        dv2 = 0
    return dv1 == int(t[10]) and dv2 == int(t[11])


def valida_pis(pis: str) -> bool:
    pis = _digits(pis)
    if len(pis) != 11 or pis == pis[0] * 11:
        return False
    pesos = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s = sum(int(pis[i]) * pesos[i] for i in range(10))
    d = 11 - (s % 11)
    if d >= 10:
        d = 0
    return d == int(pis[10])


def valida_cartao_sus(c: str) -> bool:
    c = _digits(c)
    if len(c) != 15:
        return False
    s = sum(int(c[i]) * (15 - i) for i in range(15))
    return s % 11 == 0


# --------------------------------------------------------------------------- #
# Recognizer base com hook de validação
# --------------------------------------------------------------------------- #
class ChecksumPatternRecognizer(PatternRecognizer):
    """PatternRecognizer que rebaixa o score quando o DV não confere."""

    def __init__(self, *args, validator=None, valid_score: float = 0.9,
                 invalid_score: float = 0.05, **kwargs):
        super().__init__(*args, **kwargs)
        self._validator = validator
        self._valid_score = valid_score
        self._invalid_score = invalid_score

    def analyze(self, text, entities, nlp_artifacts=None):
        results = super().analyze(text, entities, nlp_artifacts)
        if not self._validator:
            return results
        out = []
        for r in results:
            chunk = text[r.start:r.end]
            if self._validator(chunk):
                r.score = max(r.score, self._valid_score)
                out.append(r)
            else:
                r.score = self._invalid_score  # mantém para inspeção
                out.append(r)
        return out


# --------------------------------------------------------------------------- #
# Definição dos recognizers BR
# --------------------------------------------------------------------------- #
def build_br_recognizers() -> List[EntityRecognizer]:
    cpf = ChecksumPatternRecognizer(
        supported_entity="BR_CPF",
        supported_language="pt",
        patterns=[
            Pattern("cpf_formatado", r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", 0.6),
            Pattern("cpf_numerico",  r"\b\d{11}\b", 0.3),
        ],
        context=["cpf", "documento", "rg/cpf", "cadastro de pessoa"],
        validator=valida_cpf,
    )

    cnpj = ChecksumPatternRecognizer(
        supported_entity="BR_CNPJ",
        supported_language="pt",
        patterns=[
            Pattern("cnpj_formatado", r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b", 0.7),
            Pattern("cnpj_numerico",  r"\b\d{14}\b", 0.3),
        ],
        context=["cnpj", "empresa", "razão social", "pessoa jurídica"],
        validator=valida_cnpj,
    )

    cnh = ChecksumPatternRecognizer(
        supported_entity="BR_CNH",
        supported_language="pt",
        patterns=[Pattern("cnh", r"\b\d{11}\b", 0.2)],
        context=["cnh", "carteira de motorista", "habilitação"],
        validator=valida_cnh,
    )

    rg = PatternRecognizer(
        supported_entity="BR_RG",
        supported_language="pt",
        patterns=[
            Pattern("rg_sp",  r"\b\d{2}\.\d{3}\.\d{3}-[\dxX]\b", 0.6),
            Pattern("rg_alt", r"\b\d{1,2}\.\d{3}\.\d{3}\b", 0.4),
        ],
        context=["rg", "registro geral", "identidade", "ssp"],
    )

    telefone = PatternRecognizer(
        supported_entity="BR_PHONE",
        supported_language="pt",
        patterns=[
            Pattern("celular_+55", r"\+55\s?\(?\d{2}\)?\s?9\d{4}-?\d{4}", 0.85),
            Pattern("fixo_+55",    r"\+55\s?\(?\d{2}\)?\s?[2-5]\d{3}-?\d{4}", 0.8),
            Pattern("celular_ddd", r"\(?\b\d{2}\)?\s?9\d{4}-?\d{4}\b", 0.7),
            Pattern("fixo_ddd",    r"\(?\b\d{2}\)?\s?[2-5]\d{3}-?\d{4}\b", 0.6),
        ],
        context=["telefone", "celular", "tel", "fone", "whatsapp", "contato"],
    )

    cep = PatternRecognizer(
        supported_entity="BR_CEP",
        supported_language="pt",
        patterns=[Pattern("cep", r"\b\d{5}-?\d{3}\b", 0.6)],
        context=["cep", "endereço"],
    )

    placa = PatternRecognizer(
        supported_entity="BR_PLACA",
        supported_language="pt",
        patterns=[
            Pattern("placa_antiga",   r"\b[A-Z]{3}-?\d{4}\b", 0.7),
            Pattern("placa_mercosul", r"\b[A-Z]{3}\d[A-Z]\d{2}\b", 0.85),
        ],
        context=["placa", "veículo", "carro", "moto"],
    )

    titulo = ChecksumPatternRecognizer(
        supported_entity="BR_TITULO_ELEITOR",
        supported_language="pt",
        patterns=[
            Pattern("titulo_formatado", r"\b\d{4}\s\d{4}\s\d{4}\b", 0.6),
            Pattern("titulo_numerico",  r"\b\d{12}\b", 0.4),
        ],
        context=["título", "eleitor", "tse"],
        validator=valida_titulo_eleitor,
    )

    pis = ChecksumPatternRecognizer(
        supported_entity="BR_PIS_PASEP",
        supported_language="pt",
        patterns=[
            Pattern("pis_formatado", r"\b\d{3}\.\d{5}\.\d{2}-\d\b", 0.7),
            Pattern("pis_numerico",  r"\b\d{11}\b", 0.2),
        ],
        context=["pis", "pasep", "nis", "nit"],
        validator=valida_pis,
    )

    sus = ChecksumPatternRecognizer(
        supported_entity="BR_CARTAO_SUS",
        supported_language="pt",
        patterns=[
            Pattern("sus_formatado", r"\b\d{3}\s\d{4}\s\d{4}\s\d{4}\b", 0.7),
            Pattern("sus_numerico",  r"\b\d{15}\b", 0.4),
        ],
        context=["sus", "cartão sus", "cns", "saúde"],
        validator=valida_cartao_sus,
    )

    return [cpf, cnpj, cnh, rg, telefone, cep, placa, titulo, pis, sus]


# --------------------------------------------------------------------------- #
# Amostras BR (fictícias)
# --------------------------------------------------------------------------- #
SAMPLES = [
    # 1. CPF + nome + e-mail
    "O cliente Exemplo da Silva, portador do CPF 168.995.350-09, "
    "pode ser contatado em exemplo.silva@dominio.test.",

    # 2. CNPJ + razão social + endereço
    "A empresa Exemplo Comercio Ltda, CNPJ 60.746.948/0001-12, fica na "
    "Rua das Acácias, 250, Jardim América, São Paulo - SP, CEP 01453-000.",

    # 3. RG + CNH + data de nascimento
    "Mariana Oliveira Lima, RG 35.482.918-7 SSP/SP, CNH 02650306461, "
    "nascida em 14/03/1990.",

    # 4. Telefone celular e fixo + WhatsApp
    "Para urgências, ligue (11) 98765-4321 ou para o fixo +55 21 3456-7890. "
    "WhatsApp comercial: 11 4002-8922.",

    # 5. Título de eleitor + zona/seção
    "Eleitor: João da Silva, título 1234 5678 0167, zona 045, seção 123, "
    "votando em Belo Horizonte/MG.",

    # 6. PIS/PASEP + dados trabalhistas
    "Funcionário Pedro Henrique Costa, PIS 120.6443.131-7, admitido em 02/05/2018 "
    "na unidade de Curitiba.",

    # 7. Cartão SUS + atendimento médico
    "Paciente Ana Beatriz Ferreira, cartão SUS 898 0026 8169 1690, atendida "
    "no Hospital São Lucas pela Dra. Patrícia Mendes.",

    # 8. Placa de veículo + multa
    "Veículo placa BRA2E19 (Mercosul) e a antiga ABC-1234 foram autuados "
    "pela autoridade de trânsito de Porto Alegre.",

    # 9. Caso denso: CPF + CNPJ + cartão de crédito + IP
    "Em 22/04/2025, o usuário CPF 390.533.447-05 da empresa CNPJ "
    "60.746.948/0001-12 efetuou pagamento com o cartão 5555 4444 3333 1111 "
    "a partir do IP 200.221.2.45.",

    # 10. Pessoa pública/médico + telefone + e-mail institucional
    "Dr. Ricardo Alves Pereira, CRM-SP 145.890, agenda pelo (11) 3045-0099 ou "
    "ricardo.pereira@hospitalsiriolibanes.org.br.",
]


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #
def build_analyzer() -> AnalyzerEngine:
    nlp_conf = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "pt", "model_name": "pt_core_news_lg"}],
    }
    nlp_engine = NlpEngineProvider(nlp_configuration=nlp_conf).create_engine()

    registry = RecognizerRegistry(supported_languages=["pt"])
    registry.load_predefined_recognizers(languages=["pt"])
    for r in build_br_recognizers():
        registry.add_recognizer(r)

    return AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["pt"],
    )


def build_operators() -> dict:
    return {
        "DEFAULT":            OperatorConfig("replace", {"new_value": "<REDACTED>"}),
        "PERSON":             OperatorConfig("replace", {"new_value": "<PESSOA>"}),
        "EMAIL_ADDRESS":      OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 6, "from_end": False}),
        "LOCATION":           OperatorConfig("replace", {"new_value": "<LOCAL>"}),
        "DATE_TIME":          OperatorConfig("replace", {"new_value": "<DATA>"}),
        "URL":                OperatorConfig("replace", {"new_value": "<URL>"}),
        "IP_ADDRESS":         OperatorConfig("replace", {"new_value": "<IP>"}),
        "CREDIT_CARD":        OperatorConfig("mask", {"masking_char": "X", "chars_to_mask": 12, "from_end": False}),
        "BR_CPF":             OperatorConfig("replace", {"new_value": "<CPF>"}),
        "BR_CNPJ":            OperatorConfig("replace", {"new_value": "<CNPJ>"}),
        "BR_RG":              OperatorConfig("replace", {"new_value": "<RG>"}),
        "BR_CNH":             OperatorConfig("replace", {"new_value": "<CNH>"}),
        "BR_PHONE":           OperatorConfig("replace", {"new_value": "<TEL>"}),
        "BR_CEP":             OperatorConfig("replace", {"new_value": "<CEP>"}),
        "BR_PLACA":           OperatorConfig("replace", {"new_value": "<PLACA>"}),
        "BR_TITULO_ELEITOR":  OperatorConfig("replace", {"new_value": "<TITULO>"}),
        "BR_PIS_PASEP":       OperatorConfig("replace", {"new_value": "<PIS>"}),
        "BR_CARTAO_SUS":      OperatorConfig("replace", {"new_value": "<SUS>"}),
    }


def sanitized_display(text: str, results: List[RecognizerResult]) -> str:
    """Return a display-safe view with entity markers in detected spans."""
    out = []
    cursor = 0
    for r in sorted(results, key=lambda item: item.start):
        out.append(text[cursor:r.start])
        out.append(f"<{r.entity_type}>")
        cursor = r.end
    out.append(text[cursor:])
    return "".join(out)


def main() -> None:
    print("=" * 80)
    print("Microsoft Presidio - Teste BR (português) com PII fictícias")
    print("=" * 80)

    analyzer = build_analyzer()
    anonymizer = AnonymizerEngine()
    operators = build_operators()

    # threshold baixo para vermos também candidatos fracos
    score_threshold = 0.3

    for n, text in enumerate(SAMPLES, 1):
        print(f"\n--- Amostra #{n} ---")
        print(f"Entrada  : {len(text)} caracteres (conteudo original oculto)")

        results = analyzer.analyze(
            text=text,
            language="pt",
            score_threshold=score_threshold,
        )
        # remove sobreposições mantendo o de maior score
        results = sorted(results, key=lambda r: (-r.score, r.start))
        kept: List[RecognizerResult] = []
        for r in results:
            if not any(not (r.end <= k.start or r.start >= k.end) for k in kept):
                kept.append(r)
        kept.sort(key=lambda r: r.start)

        if kept:
            print(f"Detectado: {len(kept)} entidade(s)")
            for r in kept:
                print(
                    f"  - {r.entity_type:<22} score={r.score:.2f} "
                    f"span={r.start}:{r.end}"
                )
        else:
            print("Detectado: nenhuma entidade.")

        anon = anonymizer.anonymize(text=text, analyzer_results=kept, operators=operators)
        print(f"Saida    : {len(anon.text)} caracteres apos anonimizacao")

    print("\n" + "=" * 80)
    print("Teste BR concluído.")
    print("=" * 80)


if __name__ == "__main__":
    main()
