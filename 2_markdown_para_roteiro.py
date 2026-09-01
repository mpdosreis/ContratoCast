#!/usr/bin/env python3
"""
Etapa 2: Usa uma IA local via Ollama para transformar o markdown do contrato
em um roteiro de podcast, em tom conversacional e explicativo.

Pré-requisitos:
    1. Ollama instalado e rodando: https://ollama.com
    2. Um modelo baixado, ex:  ollama pull llama3.1:8b
    3. pip install requests --break-system-packages

Uso:
    python 2_markdown_para_roteiro.py
    python 2_markdown_para_roteiro.py --modelo qwen2.5:14b
    python 2_markdown_para_roteiro.py --vozes 2   # roteiro em formato diálogo (2 apresentadores)
"""

import argparse
import json
from pathlib import Path

import requests

PASTA_MARKDOWN = Path("markdown")
PASTA_ROTEIROS = Path("roteiros")
OLLAMA_URL = "http://localhost:11434/api/generate"

PROMPT_UMA_VOZ = """Você é um roteirista de podcast especializado em explicar documentos jurídicos
para um público leigo, de forma clara, envolvente e sem perder a precisão técnica.

Transforme o contrato abaixo (em markdown) em um roteiro de podcast narrado por UM apresentador.

Regras:
- Tom conversacional, como se estivesse explicando para um amigo.
- Explique os pontos mais importantes: partes envolvidas, obrigações, prazos, valores, penalidades, rescisão.
- Traduza jargão jurídico para linguagem simples, mas sem inventar informação que não está no contrato.
- Organize em blocos temáticos com transições naturais ("agora vamos falar sobre...").
- Não leia cláusula por cláusula ipsis litteris — resuma e explique o sentido prático.
- Comece com uma introdução breve dizendo do que se trata o contrato.
- Termine com um resumo dos pontos de atenção mais importantes.
- Escreva SOMENTE o texto que será narrado, sem marcações de cena ou instruções de produção.

CONTRATO EM MARKDOWN:
{conteudo}

ROTEIRO DO PODCAST:"""

PROMPT_DUAS_VOZES = """Você é um roteirista de podcast especializado em explicar documentos jurídicos
para um público leigo. Crie um roteiro em formato de DIÁLOGO entre dois apresentadores: APRESENTADOR_A e APRESENTADOR_B.

Regras:
- APRESENTADOR_A faz perguntas e traz a perspectiva de quem está lendo o contrato pela primeira vez.
- APRESENTADOR_B explica os pontos técnicos de forma simples e didática.
- Tom natural, como uma conversa real, com interrupções e comentários leves.
- Cubra: partes envolvidas, obrigações, prazos, valores, penalidades, condições de rescisão.
- Traduza jargão jurídico sem inventar informação que não está no contrato.
- Não leia cláusula por cláusula — resuma e explique o sentido prático.
- Formate cada fala assim, uma por linha:
APRESENTADOR_A: texto da fala
APRESENTADOR_B: texto da fala
- Comece com uma introdução breve e termine com um resumo dos pontos de atenção.

CONTRATO EM MARKDOWN:
{conteudo}

ROTEIRO DO PODCAST (formato diálogo):"""


def chamar_ollama(prompt: str, modelo: str) -> str:
    resposta = requests.post(
        OLLAMA_URL,
        json={"model": modelo, "prompt": prompt, "stream": False},
        timeout=600,
    )
    resposta.raise_for_status()
    dados = resposta.json()
    return dados.get("response", "").strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", default="llama3.1:8b", help="Nome do modelo no Ollama")
    parser.add_argument("--vozes", type=int, choices=[1, 2], default=1, help="1 apresentador ou 2 (diálogo)")
    args = parser.parse_args()

    PASTA_MARKDOWN.mkdir(exist_ok=True)
    PASTA_ROTEIROS.mkdir(exist_ok=True)

    arquivos_md = sorted(PASTA_MARKDOWN.glob("*.md"))
    if not arquivos_md:
        print(f"Nenhum .md encontrado em {PASTA_MARKDOWN.resolve()}")
        print("Rode primeiro o 1_pdf_para_markdown.py")
        return

    # checagem rápida se o Ollama está rodando
    try:
        requests.get("http://localhost:11434", timeout=3)
    except requests.exceptions.ConnectionError:
        print("Não consegui conectar ao Ollama em localhost:11434.")
        print("Verifique se ele está rodando (comando: ollama serve) e tente de novo.")
        return

    template = PROMPT_DUAS_VOZES if args.vozes == 2 else PROMPT_UMA_VOZ

    for md_path in arquivos_md:
        print(f"Gerando roteiro para: {md_path.name} (modelo={args.modelo})")
        conteudo = md_path.read_text(encoding="utf-8")
        prompt = template.format(conteudo=conteudo)

        try:
            roteiro = chamar_ollama(prompt, args.modelo)
        except Exception as e:
            print(f"  ERRO ao chamar o Ollama: {e}")
            continue

        destino = PASTA_ROTEIROS / f"{md_path.stem}_roteiro.txt"
        destino.write_text(roteiro, encoding="utf-8")
        print(f"  -> salvo em {destino}")

    print("\nConcluído.")


if __name__ == "__main__":
    main()
