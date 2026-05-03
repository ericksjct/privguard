"""
Camada 6 — Demo de LLM local (Ollama).

Ollama nao esta instalado neste ambiente. Este script:
  1) Tenta detectar Ollama no PATH ou em http://127.0.0.1:11434.
  2) Se encontrado, executa uma chamada ao modelo enviando texto sintetico
     mascarado e mostra que o trafego nao sai da maquina (resposta vinda de
     localhost).
  3) Se nao encontrado, imprime instrucoes minimas de setup.

Por que isto importa para Sicoob:
  - Tarefas com PII de cooperado em texto livre (ex: classificar reclamacoes,
    extrair entidades de boletins, sumarizar atendimentos) podem rodar 100%
    on-prem com modelos como llama3.1:8b ou qwen2.5:7b sob NDA.
  - Nenhum byte sai da maquina. Compliance dura (LGPD art. 46) trivial.

Trade-off:
  - Modelos abertos sao MENOS capazes que Claude para raciocinio complexo.
  - Use estrategia hibrida: Ollama para dados sensiveis, Claude (com camadas
    1-5) para o resto.
"""
import http.client
import json
import shutil
import sys


OLLAMA_HOST = "127.0.0.1"
OLLAMA_PORT = 11434


def has_ollama_binary() -> bool:
    return shutil.which("ollama") is not None


def has_ollama_server() -> bool:
    try:
        conn = http.client.HTTPConnection(OLLAMA_HOST, OLLAMA_PORT, timeout=2)
        conn.request("GET", "/api/tags")
        return conn.getresponse().status == 200
    except OSError:
        return False


def setup_instructions() -> None:
    print("=" * 80)
    print("Ollama nao detectado. Instalacao minima (Windows):")
    print("=" * 80)
    print("  1) winget install Ollama.Ollama")
    print("     ou: https://ollama.com/download")
    print()
    print("  2) Apos instalar (servico inicia automaticamente):")
    print("     ollama pull llama3.1:8b        # ~4.7 GB, generico bom em pt-BR")
    print("     ollama pull qwen2.5:7b         # ~4.4 GB, excelente seguir instrucao")
    print("     ollama pull phi4:14b           # ~9 GB, raciocinio mais forte")
    print()
    print("  3) Testar:")
    print("     ollama run llama3.1:8b 'classifique esta mensagem em 1 palavra: ...'")
    print()
    print("  4) Endpoint OpenAI-compatible para integrar:")
    print("     POST http://127.0.0.1:11434/v1/chat/completions")
    print()
    print("Estrategia hibrida sugerida:")
    print("  - Tarefa contem PII real de cooperado -> Ollama local")
    print("  - Tarefa generica de codigo/refactor   -> Claude (camadas 1-5)")
    print("=" * 80)


def call_ollama(prompt: str, model: str = "llama3.1:8b") -> str:
    body = json.dumps({"model": model, "prompt": prompt, "stream": False})
    conn = http.client.HTTPConnection(OLLAMA_HOST, OLLAMA_PORT, timeout=120)
    conn.request("POST", "/api/generate", body, {"Content-Type": "application/json"})
    resp = conn.getresponse()
    data = json.loads(resp.read())
    return data.get("response", "")


def main() -> int:
    print(f"Ollama binario no PATH: {has_ollama_binary()}")
    server_up = has_ollama_server()
    print(f"Servidor Ollama em {OLLAMA_HOST}:{OLLAMA_PORT}: {server_up}")

    if not server_up:
        print()
        setup_instructions()
        return 1

    prompt = (
        "Em UMA palavra, classifique o sentimento desta reclamacao sintetica de "
        "cooperado (<BR_CPF>): '<TEXTO_RECLAMACAO>'. Resposta:"
    )
    print("\nChamando Ollama em localhost com prompt sintetico mascarado...")
    out = call_ollama(prompt)
    print(f"\nResposta: {out.strip()}")
    print("\nObservacao: trafego nao saiu da maquina (HTTP local).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
