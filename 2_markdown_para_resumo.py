#!/usr/bin/env python3
"""
Etapa 2: Gera um resumo jurídico detalhado do contrato usando IA local (Ollama).

O objetivo NÃO é simplificar para leigos, e sim reduzir o volume de texto
mantendo a precisão técnica: partes, valores, prazos, condições e penalidades
são preservados literalmente.

Para evitar compressão excessiva, o contrato é dividido em blocos (por cláusula)
e cada bloco é resumido separadamente. Isso preserva muito mais detalhe do que
enviar o documento inteiro de uma vez, principalmente em modelos menores.

Pré-requisitos:
    1. Ollama instalado e rodando: https://ollama.com
    2. Um modelo baixado, ex:  ollama pull llama3.2:3b
    3. pip install requests

Uso:
    python 2_markdown_para_resumo.py
    python 2_markdown_para_resumo.py --modelo qwen2.5:14b
    python 2_markdown_para_resumo.py --blocos 6000     # blocos maiores
    python 2_markdown_para_resumo.py --sem-blocos      # documento inteiro de uma vez
"""

import argparse
import re
from pathlib import Path

import requests

PASTA_MARKDOWN = Path("markdown")
PASTA_RESUMOS = Path("resumos")
OLLAMA_URL = "http://localhost:11434/api/generate"

# Tamanho padrão de cada bloco, em caracteres. Blocos menores = mais detalhe
# preservado, porém mais chamadas ao modelo (mais lento).
TAMANHO_BLOCO_PADRAO = 4000

PROMPT_BLOCO = """Você é um advogado experiente produzindo um resumo técnico de contrato
para outros profissionais da área. O leitor conhece terminologia jurídica.

Resuma o TRECHO DE CONTRATO abaixo. Seu objetivo é REDUZIR O VOLUME DE TEXTO,
não simplificar o conteúdo.

Regras obrigatórias:
- Mantenha a terminologia jurídica. NÃO traduza termos técnicos para linguagem leiga.
- Preserve LITERALMENTE todos os dados objetivos: valores, percentuais, prazos, datas,
  índices de reajuste, número de dias, foro, nomes das partes e qualificações.
- Elimine apenas: redundâncias, fórmulas de praxe, remissões repetitivas e texto
  meramente protocolar.
- NÃO invente, extrapole nem preencha lacunas. Se algo não está no trecho, não mencione.
- NÃO comente, NÃO opine e NÃO avalie riscos. Apenas condense o que está escrito.
- Mantenha a ordem original dos assuntos.
- Escreva em prosa objetiva, sem bullets e sem títulos.
- Se o trecho for meramente protocolar e não tiver conteúdo relevante, responda
  exatamente: [SEM CONTEUDO RELEVANTE]

TRECHO DO CONTRATO:
{conteudo}

RESUMO TÉCNICO DO TRECHO:"""

PROMPT_DOCUMENTO_INTEIRO = """Você é um advogado experiente produzindo um resumo técnico de contrato
para outros profissionais da área. O leitor conhece terminologia jurídica.

Resuma o CONTRATO abaixo. Seu objetivo é REDUZIR O VOLUME DE TEXTO,
não simplificar o conteúdo.

Regras obrigatórias:
- Mantenha a terminologia jurídica. NÃO traduza termos técnicos para linguagem leiga.
- Preserve LITERALMENTE todos os dados objetivos: valores, percentuais, prazos, datas,
  índices de reajuste, número de dias, foro, nomes das partes e qualificações.
- Cubra obrigatoriamente, na ordem: qualificação das partes, objeto, obrigações de
  cada parte, preço e forma de pagamento, reajuste, vigência e prazos, garantias,
  penalidades e multas, hipóteses de rescisão, confidencialidade e foro.
- Elimine apenas redundâncias e texto protocolar.
- NÃO invente, extrapole nem preencha lacunas.
- NÃO comente, NÃO opine e NÃO avalie riscos.
- Escreva em prosa objetiva, sem bullets e sem títulos.

CONTRATO:
{conteudo}

RESUMO TÉCNICO:"""


def chamar_ollama(prompt: str, modelo: str, temperatura: float = 0.2) -> str:
    """Temperatura baixa por padrão: reduz invenção de dados em texto jurídico."""
    resposta = requests.post(
        OLLAMA_URL,
        json={
            "model": modelo,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperatura},
        },
        timeout=1200,
    )
    resposta.raise_for_status()
    return resposta.json().get("response", "").strip()


def _agrupar(pedacos: list[str], tamanho_max: int, separador: str = "\n\n") -> list[str]:
    """Junta pedaços consecutivos até encostar no limite."""
    blocos = []
    atual = ""
    for pedaco in pedacos:
        pedaco = pedaco.strip()
        if not pedaco:
            continue
        if atual and len(atual) + len(pedaco) + len(separador) > tamanho_max:
            blocos.append(atual)
            atual = pedaco
        else:
            atual = f"{atual}{separador}{pedaco}" if atual else pedaco
    if atual:
        blocos.append(atual)
    return blocos


def _quebrar_texto_longo(texto: str, tamanho_max: int) -> list[str]:
    """
    Quebra um trecho maior que o limite, tentando na ordem:
    parágrafo -> frase -> corte forçado.
    """
    if len(texto) <= tamanho_max:
        return [texto]

    # 1) por parágrafo
    partes = _agrupar(texto.split("\n\n"), tamanho_max)
    if all(len(p) <= tamanho_max for p in partes):
        return partes

    # 2) por frase, nas partes que ainda estouram
    resultado = []
    for parte in partes:
        if len(parte) <= tamanho_max:
            resultado.append(parte)
            continue
        frases = re.split(r"(?<=[.;:!?])\s+", parte)
        subpartes = _agrupar(frases, tamanho_max, separador=" ")

        # 3) corte forçado, para frases isoladas gigantes (raro, mas possível)
        for sub in subpartes:
            if len(sub) <= tamanho_max:
                resultado.append(sub)
            else:
                for i in range(0, len(sub), tamanho_max):
                    resultado.append(sub[i : i + tamanho_max])
    return resultado


def dividir_em_blocos(texto: str, tamanho_max: int) -> list[str]:
    """
    Divide o markdown em blocos, preferindo quebrar nos títulos de cláusula (##).
    Cláusulas maiores que o limite são subdivididas por parágrafo e, se preciso,
    por frase. O título da cláusula é repetido no início de cada subdivisão, para
    que o modelo não perca o contexto do trecho.
    """
    partes = re.split(r"\n(?=#{1,6} )", texto)

    unidades = []
    for parte in partes:
        parte = parte.strip()
        if not parte:
            continue

        if len(parte) <= tamanho_max:
            unidades.append(parte)
            continue

        # Separa o título (se houver) do corpo da cláusula
        linhas = parte.split("\n", 1)
        if re.match(r"^#{1,6} ", linhas[0]) and len(linhas) > 1:
            titulo, corpo = linhas[0].strip(), linhas[1].strip()
        else:
            titulo, corpo = "", parte

        # Desconta o título, que será repetido em cada subdivisão
        limite_corpo = tamanho_max - len(titulo) - 20 if titulo else tamanho_max
        limite_corpo = max(limite_corpo, 500)

        subs = _quebrar_texto_longo(corpo, limite_corpo)
        for i, sub in enumerate(subs):
            if not titulo:
                unidades.append(sub)
            elif i == 0:
                unidades.append(f"{titulo}\n\n{sub}")
            else:
                unidades.append(f"{titulo} (continuação)\n\n{sub}")

    # Reagrupa unidades pequenas para não fazer chamadas desnecessárias ao modelo
    return _agrupar(unidades, tamanho_max)


def resumir_por_blocos(conteudo: str, modelo: str, tamanho_bloco: int) -> str:
    blocos = dividir_em_blocos(conteudo, tamanho_bloco)
    print(f"  Dividido em {len(blocos)} bloco(s)")

    resumos = []
    for i, bloco in enumerate(blocos, 1):
        print(f"  Resumindo bloco {i}/{len(blocos)}...", flush=True)
        try:
            resumo = chamar_ollama(PROMPT_BLOCO.format(conteudo=bloco), modelo)
        except Exception as e:
            print(f"    ERRO no bloco {i}: {e}")
            continue

        if "[SEM CONTEUDO RELEVANTE]" in resumo.upper():
            continue
        if resumo:
            resumos.append(resumo)

    return "\n\n".join(resumos)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", default="llama3.2:3b", help="Nome do modelo no Ollama")
    parser.add_argument(
        "--blocos",
        type=int,
        default=TAMANHO_BLOCO_PADRAO,
        help=f"Tamanho de cada bloco em caracteres (padrão {TAMANHO_BLOCO_PADRAO}). "
        "Menor = mais detalhe preservado, porém mais lento.",
    )
    parser.add_argument(
        "--sem-blocos",
        action="store_true",
        help="Envia o contrato inteiro de uma vez (mais rápido, resumo mais condensado)",
    )
    args = parser.parse_args()

    PASTA_MARKDOWN.mkdir(exist_ok=True)
    PASTA_RESUMOS.mkdir(exist_ok=True)

    arquivos_md = sorted(PASTA_MARKDOWN.glob("*.md"))
    if not arquivos_md:
        print(f"Nenhum .md encontrado em {PASTA_MARKDOWN.resolve()}")
        print("Rode primeiro o 1_pdf_para_markdown.py")
        return

    try:
        requests.get("http://localhost:11434", timeout=3)
    except requests.exceptions.ConnectionError:
        print("Não consegui conectar ao Ollama em localhost:11434.")
        print("Verifique se ele está rodando e tente de novo.")
        return

    for md_path in arquivos_md:
        print(f"\nResumindo: {md_path.name} (modelo={args.modelo})")
        conteudo = md_path.read_text(encoding="utf-8")

        try:
            if args.sem_blocos:
                resumo = chamar_ollama(
                    PROMPT_DOCUMENTO_INTEIRO.format(conteudo=conteudo), args.modelo
                )
            else:
                resumo = resumir_por_blocos(conteudo, args.modelo, args.blocos)
        except Exception as e:
            print(f"  ERRO: {e}")
            continue

        if not resumo:
            print("  Aviso: resumo vazio, pulando.")
            continue

        destino = PASTA_RESUMOS / f"{md_path.stem}_resumo.md"
        cabecalho = f"# Resumo — {md_path.stem}\n\n"
        destino.write_text(cabecalho + resumo, encoding="utf-8")

        reducao = 100 - (len(resumo) / len(conteudo) * 100) if conteudo else 0
        print(f"  -> salvo em {destino}")
        print(f"     {len(conteudo):,} → {len(resumo):,} caracteres ({reducao:.0f}% de redução)")

    print("\nConcluído. Revise os resumos antes de gerar a narração.")


if __name__ == "__main__":
    main()
