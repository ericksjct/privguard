"""
Camada 5 — Demo de mapeamento reversível.

Pipeline:
  texto original com PII
    -> Presidio detecta entidades
    -> AnonymizerEngine aplica operator 'encrypt' (AES) com chave LOCAL
    -> texto cifrado (sem PII em claro) seria o que voce mandaria pro Claude
    -> resposta hipotetica do Claude vem com os tokens cifrados
    -> DeanonymizeEngine reverte localmente usando a mesma chave

A chave AES NUNCA sai da maquina. O Claude nunca ve o dado original.
"""
import secrets
import string
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine, DeanonymizeEngine
from presidio_anonymizer.entities import OperatorConfig, OperatorResult

# Reuso dos recognizers BR ja construidos no test_presidio_br.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from test_presidio_br import build_br_recognizers


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
        registry=registry, nlp_engine=nlp_engine, supported_languages=["pt"],
    )


def main() -> None:
    print("=" * 80)
    print("Camada 5 — Mapeamento reversivel (encrypt operator)")
    print("=" * 80)

    # Chave AES de 32 bytes ASCII (256 bits). Em producao: ler de keyring/HSM.
    alphabet = string.ascii_letters + string.digits
    key = "".join(secrets.choice(alphabet) for _ in range(32))

    text = (
        "Cooperado Exemplo Um, CPF 168.995.350-09, conta 12345-6, "
        "telefone (11) 98765-4321, email exemplo.um@dominio.test, "
        "deve ser informado sobre alteracao na taxa de juros."
    )

    print("\n[1] Texto de entrada:")
    print(f"    {len(text)} caracteres (conteudo original oculto)")

    analyzer = build_analyzer()
    anonymizer = AnonymizerEngine()
    deanon = DeanonymizeEngine()

    results = analyzer.analyze(text=text, language="pt", score_threshold=0.5)
    print(f"\n[2] Presidio detectou {len(results)} entidade(s).")

    encrypted = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators={"DEFAULT": OperatorConfig("encrypt", {"key": key})},
    )
    print("\n[3] Texto CIFRADO:")
    print(f"    {len(encrypted.text)} caracteres (tokens cifrados ocultos no stdout)")

    # Mostrar quais "items" a anonimizacao produziu (com operador encrypt)
    print(f"\n    Items: {len(encrypted.items)}")

    # Simulacao: Claude responde re-incluindo uma referencia cifrada.
    fake_resposta_claude = (
        "Confirmo: o cliente identificado por <TOKEN_CIFRADO> "
        "deve receber a comunicacao no endereco cadastrado."
    )
    print("\n[4] Resposta SIMULADA do Claude (referenciando token cifrado):")
    print(f"    {fake_resposta_claude}")

    # Reverter LOCALMENTE
    decrypted = deanon.deanonymize(
        text=encrypted.text,
        entities=encrypted.items,
        operators={"DEFAULT": OperatorConfig("decrypt", {"key": key})},
    )
    print("\n[5] Texto RESTAURADO localmente:")
    print(f"    {len(decrypted.text)} caracteres (conteudo restaurado oculto)")

    print("\n" + "=" * 80)
    print("Demo concluida. Resumo:")
    print(f"  - PII detectada: {len(results)} entidade(s)")
    print(f"  - Tamanho cifrado: {len(encrypted.text)} chars vs original {len(text)}")
    print(f"  - Match exato apos round-trip: {decrypted.text == text}")
    print("=" * 80)


if __name__ == "__main__":
    main()
