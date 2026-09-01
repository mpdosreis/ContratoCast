#!/usr/bin/env python3
"""
Etapa 1: Extrai texto de PDFs de contratos e converte para Markdown limpo.

Uso:
    python 1_pdf_para_markdown.py

Coloca os PDFs na pasta ./pdfs/ e o resultado sai em ./markdown/
"""

import re
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    raise SystemExit(
        "Falta instalar o PyMuPDF. Rode: pip install pymupdf --break-system-packages"
    )

PASTA_PDFS = Path("pdfs")
PASTA_MARKDOWN = Path("markdown")


def limpar_texto(texto: str) -> str:
    """Remove quebras de linha soltas, hifenização e espaços duplicados."""
    # Junta palavras quebradas por hífen no fim da linha (ex: "contra-\nto" -> "contrato")
    texto = re.sub(r"-\n(?=\w)", "", texto)
    # Junta linhas que não terminam em pontuação (parágrafo quebrado pelo PDF)
    texto = re.sub(r"(?<![.:;!?\n])\n(?!\n)", " ", texto)
    # Normaliza espaços múltiplos
    texto = re.sub(r"[ \t]+", " ", texto)
    # Normaliza múltiplas quebras de linha para no máximo duas
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def detectar_titulo_clausula(linha: str) -> bool:
    """Heurística simples para identificar cabeçalhos de cláusulas em contratos."""
    padroes = [
        r"^CL[ÁA]USULA\s+[\dIVXLC]+",
        r"^ARTIGO\s+[\dIVXLC]+",
        r"^§\s*\d+",
        r"^\d+\.\s+[A-ZÀ-Ú][A-ZÀ-Ú\s]{4,}$",
        r"^[A-ZÀ-Ú][A-ZÀ-Ú\s]{6,}$",  # linha toda em maiúsculas (título)
    ]
    return any(re.match(p, linha.strip()) for p in padroes)


def converter_para_markdown(texto: str) -> str:
    linhas = texto.split("\n")
    saida = []
    for linha in linhas:
        linha_strip = linha.strip()
        if not linha_strip:
            saida.append("")
            continue
        if detectar_titulo_clausula(linha_strip):
            saida.append(f"\n## {linha_strip.title()}\n")
        else:
            saida.append(linha_strip)
    return "\n".join(saida)


def processar_pdf(caminho_pdf: Path) -> str:
    doc = fitz.open(caminho_pdf)
    texto_completo = []
    for pagina in doc:
        texto_completo.append(pagina.get_text())
    doc.close()

    texto_bruto = "\n".join(texto_completo)
    texto_limpo = limpar_texto(texto_bruto)
    markdown = converter_para_markdown(texto_limpo)

    cabecalho = f"# {caminho_pdf.stem}\n\n"
    return cabecalho + markdown


def main():
    PASTA_PDFS.mkdir(exist_ok=True)
    PASTA_MARKDOWN.mkdir(exist_ok=True)

    pdfs = sorted(PASTA_PDFS.glob("*.pdf"))
    if not pdfs:
        print(f"Nenhum PDF encontrado em {PASTA_PDFS.resolve()}")
        print("Coloque seus contratos em .pdf ali e rode de novo.")
        return

    for pdf in pdfs:
        print(f"Processando: {pdf.name}")
        try:
            md = processar_pdf(pdf)
        except Exception as e:
            print(f"  ERRO ao processar {pdf.name}: {e}")
            continue

        destino = PASTA_MARKDOWN / f"{pdf.stem}.md"
        destino.write_text(md, encoding="utf-8")
        print(f"  -> salvo em {destino}")

    print(f"\nConcluído. {len(pdfs)} arquivo(s) processado(s).")


if __name__ == "__main__":
    main()
