#!/usr/bin/env python3
"""
Etapa 3: Adapta o resumo jurídico para narração em áudio (estilo audiolivro).

Esta etapa NÃO resume mais nada e NÃO simplifica o conteúdo. Ela apenas prepara
o texto para ser ouvido por uma única voz:

- remove marcação markdown, bullets e numeração que não fazem sentido em áudio;
- escreve valores, datas, percentuais e siglas por extenso (o TTS pronuncia mal
  "R$ 1.500,00" e "CNPJ" se ficarem na forma escrita);
- transforma listas em prosa corrida, com conectivos;
- mantém tom neutro e informativo, sem locução de podcast.

Pré-requisitos:
    1. Ollama rodando com um modelo baixado
    2. pip install requests

Uso:
    python 3_resumo_para_narracao.py
    python 3_resumo_para_narracao.py --modelo qwen2.5:14b
"""

import argparse
import re
from pathlib import Path

import requests

PASTA_RESUMOS = Path("resumos")
PASTA_NARRACAO = Path("narracao")
OLLAMA_URL = "http://localhost:11434/api/generate"

TAMANHO_BLOCO = 3500

PROMPT_NARRACAO = """Você prepara textos para serem lidos em voz alta por um sintetizador de voz,
no formato de audiolivro técnico. O ouvinte é um profissional da área jurídica.

Adapte o TRECHO abaixo para narração em áudio.

Regras obrigatórias:
- NÃO resuma, NÃO corte conteúdo e NÃO simplifique termos técnicos.
  Todo o conteúdo do trecho deve permanecer.
- Escreva por extenso tudo que um sintetizador de voz pronunciaria mal:
  "R$ 1.500,00" vira "mil e quinhentos reais"
  "30%" vira "trinta por cento"
  "10/03/2025" vira "dez de março de dois mil e vinte e cinco"
  "art. 5º" vira "artigo quinto"
  "CNPJ" vira "cê enê pê jota"
  "§ 2º" vira "parágrafo segundo"
  "cláusula 4.2" vira "cláusula quatro ponto dois"
- Remova toda marcação: asteriscos, cerquilhas, bullets, numeração de lista.
- Transforme listas em frases corridas, ligadas por conectivos naturais
  ("além disso", "por sua vez", "em seguida").
- Use frases de comprimento moderado. Frases muito longas ficam cansativas em áudio.
- Tom neutro e informativo, como um audiolivro técnico.
  NÃO use saudações, NÃO se dirija ao ouvinte, NÃO faça comentários de locução.
- Não escreva nenhum título ou cabeçalho.
- Responda somente com o texto pronto para ser narrado.

TRECHO:
{conteudo}

TEXTO PARA NARRAÇÃO:"""


def chamar_ollama(prompt: str, modelo: str) -> str:
    resposta = requests.post(
        OLLAMA_URL,
        json={
            "model": modelo,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3},
        },
        timeout=1200,
    )
    resposta.raise_for_status()
    return resposta.json().get("response", "").strip()


def dividir_em_blocos(texto: str, tamanho_max: int) -> list[str]:
    """Divide por parágrafo, sem quebrar no meio de uma frase."""
    paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    blocos = []
    atual = ""
    for p in paragrafos:
        if len(atual) + len(p) + 2 > tamanho_max and atual:
            blocos.append(atual)
            atual = p
        else:
            atual = f"{atual}\n\n{p}" if atual else p
    if atual:
        blocos.append(atual)
    return blocos


def limpar_residuos(texto: str) -> str:
    """Remove marcação markdown que o modelo eventualmente deixe passar."""
    texto = re.sub(r"^#{1,6}\s*", "", texto, flags=re.MULTILINE)   # títulos
    texto = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", texto)         # negrito/itálico
    texto = re.sub(r"^\s*[-*+]\s+", "", texto, flags=re.MULTILINE)  # bullets
    texto = re.sub(r"^\s*\d+[.)]\s+", "", texto, flags=re.MULTILINE)  # listas numeradas
    texto = re.sub(r"`([^`]+)`", r"\1", texto)                      # código inline
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", default="llama3.2:3b", help="Nome do modelo no Ollama")
    args = parser.parse_args()

    PASTA_RESUMOS.mkdir(exist_ok=True)
    PASTA_NARRACAO.mkdir(exist_ok=True)

    resumos = sorted(PASTA_RESUMOS.glob("*.md"))
    if not resumos:
        print(f"Nenhum resumo encontrado em {PASTA_RESUMOS.resolve()}")
        print("Rode primeiro o 2_markdown_para_resumo.py")
        return

    try:
        requests.get("http://localhost:11434", timeout=3)
    except requests.exceptions.ConnectionError:
        print("Não consegui conectar ao Ollama em localhost:11434.")
        return

    for resumo_path in resumos:
        print(f"\nPreparando narração: {resumo_path.name}")
        conteudo = resumo_path.read_text(encoding="utf-8")

        # Remove o cabeçalho "# Resumo — ..." adicionado pela etapa anterior
        conteudo = re.sub(r"^#\s+Resumo\s+—.*?\n+", "", conteudo, count=1)

        blocos = dividir_em_blocos(conteudo, TAMANHO_BLOCO)
        print(f"  {len(blocos)} bloco(s)")

        partes = []
        for i, bloco in enumerate(blocos, 1):
            print(f"  Adaptando bloco {i}/{len(blocos)}...", flush=True)
            try:
                partes.append(chamar_ollama(PROMPT_NARRACAO.format(conteudo=bloco), args.modelo))
            except Exception as e:
                print(f"    ERRO no bloco {i}: {e}")

        if not partes:
            print("  Aviso: nada gerado, pulando.")
            continue

        texto_final = limpar_residuos("\n\n".join(partes))

        destino = PASTA_NARRACAO / f"{resumo_path.stem.replace('_resumo', '')}_narracao.txt"
        destino.write_text(texto_final, encoding="utf-8")

        palavras = len(texto_final.split())
        minutos = palavras / 150  # ~150 palavras por minuto em narração
        print(f"  -> salvo em {destino}")
        print(f"     {palavras:,} palavras (~{minutos:.0f} min de áudio)")

    print("\nConcluído. Revise a narração antes de gerar o áudio.")


if __name__ == "__main__":
    main()
