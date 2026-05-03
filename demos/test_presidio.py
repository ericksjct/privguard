"""
Teste do Microsoft Presidio com amostras aleatórias de PII sensíveis.
Todos os dados abaixo são FICTÍCIOS, gerados apenas para teste.
"""
import random
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


def sanitize_text(text: str, results) -> str:
    """Return a display-safe string using entity markers instead of raw spans."""
    out = []
    cursor = 0
    for r in sorted(results, key=lambda x: x.start):
        out.append(text[cursor:r.start])
        out.append(f"<{r.entity_type}>")
        cursor = r.end
    out.append(text[cursor:])
    return "".join(out)


SAMPLES = [
    # 1. Email + telefone + nome
    "Hi, my name is Sarah Connor. You can reach me at sarah.connor@skynet-corp.com or call +1 (415) 555-0142.",

    # 2. SSN + endereço + data de nascimento
    "Patient John Doe, SSN 123-45-6789, born on 03/14/1985, lives at 742 Evergreen Terrace, Springfield, IL 62704.",

    # 3. Cartão de crédito + IBAN
    "Please charge card 4532-1488-0343-6467 (exp 11/27, CVV 321). Refund the IBAN GB82WEST12345698765432.",

    # 4. Endereço IP + URL + localização
    "The login attempt came from 192.168.45.213 via https://internal.acme.io/admin while the user was in Berlin, Germany.",

    # 5. Carteira de motorista + placa
    "Driver license D1234567 issued in California. The vehicle plate is 7XYZ123.",

    # 6. Conta bancária + roteamento (US)
    "Wire $4,500 from account 0987654321, routing 021000021, to recipient Michael Bloom at Chase Bank.",

    # 7. Passaporte + nacionalidade
    "Maria García, Spanish national, passport AB1234567, contacted us last Tuesday from maria.garcia@correo.es.",

    # 8. Médico + identificadores hospitalares
    "Dr. Lisa Hamilton (NPI 1356789012) treated patient MRN 778-901, diagnosed at age 47.",

    # 9. Cripto + identificadores online
    "Send 0.25 BTC to wallet bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq. Twitter handle @darkwizard91.",

    # 10. Mistura densa
    "On 2024-09-12, agent Robert Smith (badge #44721, robert.smith@fbi.gov, cell 202-555-0173) interviewed "
    "Tatiana Volkov at her residence 1809 Brookline Ave, Apt 4B, Boston, MA 02215. Her Russian passport "
    "is 75 1234567 and her US visa expires 06/30/2026.",
]


def main():
    print("=" * 80)
    print("Microsoft Presidio - Teste com PII sensíveis fictícias")
    print("=" * 80)

    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()

    operators = {
        "DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"}),
        "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
        "EMAIL_ADDRESS": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 6, "from_end": False}),
        "CREDIT_CARD": OperatorConfig("mask", {"masking_char": "X", "chars_to_mask": 12, "from_end": False}),
        "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE>"}),
        "US_SSN": OperatorConfig("replace", {"new_value": "<SSN>"}),
        "IBAN_CODE": OperatorConfig("replace", {"new_value": "<IBAN>"}),
        "IP_ADDRESS": OperatorConfig("replace", {"new_value": "<IP>"}),
        "LOCATION": OperatorConfig("replace", {"new_value": "<LOCATION>"}),
        "DATE_TIME": OperatorConfig("replace", {"new_value": "<DATE>"}),
        "URL": OperatorConfig("replace", {"new_value": "<URL>"}),
        "US_DRIVER_LICENSE": OperatorConfig("replace", {"new_value": "<DL>"}),
        "US_BANK_NUMBER": OperatorConfig("replace", {"new_value": "<BANK>"}),
        "CRYPTO": OperatorConfig("replace", {"new_value": "<CRYPTO>"}),
        "MEDICAL_LICENSE": OperatorConfig("replace", {"new_value": "<MED_LIC>"}),
    }

    random.seed(42)
    chosen = random.sample(list(enumerate(SAMPLES, 1)), k=len(SAMPLES))

    for idx, (n, text) in enumerate(chosen, 1):
        print(f"\n--- Amostra #{idx} (id original {n}) ---")
        print(f"Entrada  : {len(text)} caracteres (conteudo original oculto)")

        results = analyzer.analyze(text=text, language="en")

        if results:
            print(f"Detectado: {len(results)} entidade(s)")
            for r in sorted(results, key=lambda x: x.start):
                print(
                    f"  - {r.entity_type:<22} score={r.score:.2f} "
                    f"span={r.start}:{r.end}"
                )
        else:
            print("Detectado: nenhuma entidade.")

        anon = anonymizer.anonymize(text=text, analyzer_results=results, operators=operators)
        print(f"Saida    : {len(anon.text)} caracteres apos anonimizacao")

    print("\n" + "=" * 80)
    print("Teste concluído.")
    print("=" * 80)


if __name__ == "__main__":
    main()
