#!/usr/bin/env python3
"""
Etapa 4: Converte o texto de narração em áudio usando Piper TTS (100% offline).

Voz única, formato audiolivro. O texto é sintetizado parágrafo a parágrafo e
depois concatenado, o que produz pausas naturais entre os trechos e evita que
arquivos longos sobrecarreguem o Piper de uma só vez.

Pré-requisitos:
    1. Piper instalado (binário na pasta do projeto ou no PATH)
    2. Uma voz pt-BR na pasta vozes/ (arquivos .onnx e .onnx.json)

Uso:
    python 4_narracao_para_audio.py --voz vozes/pt_BR-faber-medium.onnx
    python 4_narracao_para_audio.py --voz vozes/pt_BR-faber-medium.onnx --velocidade 1.1
    python 4_narracao_para_audio.py --voz vozes/pt_BR-faber-medium.onnx --pausa 700
"""

import argparse
import subprocess
import sys
import wave
from pathlib import Path

PASTA_NARRACAO = Path("narracao")
PASTA_AUDIO = Path("audio")


def encontrar_piper() -> str:
    """Prefere o executável na pasta do projeto; cai para o PATH se não achar."""
    local = Path("piper.exe") if sys.platform == "win32" else Path("piper")
    if local.exists():
        return str(local.resolve())
    return "piper"


def rodar_piper(texto: str, modelo_onnx: str, destino_wav: Path, velocidade: float, piper_cmd: str):
    comando = [
        piper_cmd,
        "--model", modelo_onnx,
        "--length_scale", str(velocidade),
        "--output_file", str(destino_wav),
    ]
    resultado = subprocess.run(comando, input=texto.encode("utf-8"), capture_output=True)
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.decode("utf-8", errors="ignore").strip())


def concatenar_wavs(caminhos: list[Path], destino: Path, pausa_ms: int):
    if not caminhos:
        return
    with wave.open(str(caminhos[0]), "rb") as primeiro:
        params = primeiro.getparams()

    n_bytes_pausa = (
        int(params.framerate * (pausa_ms / 1000)) * params.sampwidth * params.nchannels
    )
    silencio = b"\x00" * n_bytes_pausa

    with wave.open(str(destino), "wb") as saida:
        saida.setparams(params)
        for i, caminho in enumerate(caminhos):
            with wave.open(str(caminho), "rb") as w:
                saida.writeframes(w.readframes(w.getnframes()))
            if i < len(caminhos) - 1:
                saida.writeframes(silencio)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--voz", required=True, help="Caminho do arquivo .onnx da voz")
    parser.add_argument(
        "--velocidade",
        type=float,
        default=1.0,
        help="1.0 é o padrão. Maior = mais lento (ex. 1.15). Menor = mais rápido (ex. 0.9).",
    )
    parser.add_argument(
        "--pausa", type=int, default=500, help="Pausa entre parágrafos, em milissegundos"
    )
    args = parser.parse_args()

    if not Path(args.voz).exists():
        print(f"Arquivo de voz não encontrado: {args.voz}")
        return
    if not Path(f"{args.voz}.json").exists():
        print(f"Falta o arquivo de configuração da voz: {args.voz}.json")
        print("Cada voz do Piper tem DOIS arquivos: .onnx e .onnx.json")
        return

    PASTA_NARRACAO.mkdir(exist_ok=True)
    PASTA_AUDIO.mkdir(exist_ok=True)

    textos = sorted(PASTA_NARRACAO.glob("*.txt"))
    if not textos:
        print(f"Nenhum texto encontrado em {PASTA_NARRACAO.resolve()}")
        print("Rode primeiro o 3_resumo_para_narracao.py")
        return

    piper_cmd = encontrar_piper()

    for texto_path in textos:
        print(f"\nGerando áudio: {texto_path.name}")
        conteudo = texto_path.read_text(encoding="utf-8")
        paragrafos = [p.strip() for p in conteudo.split("\n\n") if p.strip()]

        if not paragrafos:
            print("  Arquivo vazio, pulando.")
            continue

        pasta_tmp = PASTA_AUDIO / f"_tmp_{texto_path.stem}"
        pasta_tmp.mkdir(exist_ok=True)
        wavs = []

        try:
            for i, paragrafo in enumerate(paragrafos):
                print(f"  Sintetizando {i + 1}/{len(paragrafos)}...", flush=True)
                trecho = pasta_tmp / f"trecho_{i:04d}.wav"
                rodar_piper(paragrafo, args.voz, trecho, args.velocidade, piper_cmd)
                wavs.append(trecho)

            destino = PASTA_AUDIO / f"{texto_path.stem}.wav"
            concatenar_wavs(wavs, destino, args.pausa)
            print(f"  -> salvo em {destino}")

        except FileNotFoundError:
            print("  ERRO: executável do Piper não encontrado.")
            print("  Coloque o piper.exe na pasta do projeto ou adicione-o ao PATH.")
            return
        except Exception as e:
            print(f"  ERRO: {e}")
        finally:
            for w in wavs:
                w.unlink(missing_ok=True)
            if pasta_tmp.exists() and not any(pasta_tmp.iterdir()):
                pasta_tmp.rmdir()

    print("\nConcluído.")


if __name__ == "__main__":
    main()
