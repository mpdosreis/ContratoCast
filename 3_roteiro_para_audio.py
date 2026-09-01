#!/usr/bin/env python3
"""
Etapa 3: Converte os roteiros de texto em áudio usando Piper TTS (100% offline).

Pré-requisitos:
    1. Instalar o Piper: https://github.com/rhasspy/piper
       (binário standalone, sem necessidade de GPU)
    2. Baixar voz(es) em pt-BR, ex:
       - pt_BR-faber-medium (masculina)
       - pt_BR-edresson-low (masculina, mais leve)
       procure em: https://github.com/rhasspy/piper/blob/master/VOICES.md
    3. Colocar os arquivos .onnx (e .onnx.json) numa pasta, ex: ./vozes/

Uso (uma voz):
    python 3_roteiro_para_audio.py --voz-a vozes/pt_BR-faber-medium.onnx

Uso (diálogo com duas vozes):
    python 3_roteiro_para_audio.py \\
        --voz-a vozes/pt_BR-faber-medium.onnx \\
        --voz-b vozes/pt_BR-edresson-low.onnx
"""

import argparse
import subprocess
import wave
from pathlib import Path

PASTA_ROTEIROS = Path("roteiros")
PASTA_AUDIO = Path("audio")


def rodar_piper(texto: str, modelo_onnx: str, destino_wav: Path):
    """Chama o binário do piper via subprocess, passando o texto pelo stdin."""
    comando = ["piper", "--model", modelo_onnx, "--output_file", str(destino_wav)]
    resultado = subprocess.run(
        comando, input=texto.encode("utf-8"), capture_output=True
    )
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.decode("utf-8", errors="ignore"))


def concatenar_wavs(caminhos_wav: list[Path], destino: Path, silencio_ms: int = 400):
    if not caminhos_wav:
        return
    with wave.open(str(caminhos_wav[0]), "rb") as primeiro:
        params = primeiro.getparams()

    with wave.open(str(destino), "wb") as saida:
        saida.setparams(params)
        n_bytes_silencio = int(params.framerate * (silencio_ms / 1000)) * params.sampwidth * params.nchannels
        silencio = b"\x00" * n_bytes_silencio

        for i, caminho in enumerate(caminhos_wav):
            with wave.open(str(caminho), "rb") as w:
                saida.writeframes(w.readframes(w.getnframes()))
            if i < len(caminhos_wav) - 1:
                saida.writeframes(silencio)


def processar_dialogo(roteiro_texto: str, voz_a: str, voz_b: str, pasta_tmp: Path) -> list[Path]:
    """Roteiro em formato 'APRESENTADOR_A: ...' / 'APRESENTADOR_B: ...' -> lista de wavs na ordem."""
    pasta_tmp.mkdir(exist_ok=True)
    wavs = []
    idx = 0
    for linha in roteiro_texto.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        if linha.upper().startswith("APRESENTADOR_A:"):
            fala = linha.split(":", 1)[1].strip()
            voz = voz_a
        elif linha.upper().startswith("APRESENTADOR_B:"):
            fala = linha.split(":", 1)[1].strip()
            voz = voz_b
        else:
            continue
        if not fala:
            continue
        destino = pasta_tmp / f"trecho_{idx:04d}.wav"
        rodar_piper(fala, voz, destino)
        wavs.append(destino)
        idx += 1
    return wavs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--voz-a", required=True, help="Caminho do modelo .onnx do Piper (voz principal)")
    parser.add_argument("--voz-b", default=None, help="Caminho do modelo .onnx do 2º apresentador (opcional, diálogo)")
    args = parser.parse_args()

    PASTA_ROTEIROS.mkdir(exist_ok=True)
    PASTA_AUDIO.mkdir(exist_ok=True)

    roteiros = sorted(PASTA_ROTEIROS.glob("*.txt"))
    if not roteiros:
        print(f"Nenhum roteiro encontrado em {PASTA_ROTEIROS.resolve()}")
        print("Rode primeiro o 2_markdown_para_roteiro.py")
        return

    for roteiro_path in roteiros:
        print(f"Gerando áudio para: {roteiro_path.name}")
        texto = roteiro_path.read_text(encoding="utf-8")
        destino_final = PASTA_AUDIO / f"{roteiro_path.stem}.wav"

        try:
            if args.voz_b:
                pasta_tmp = PASTA_AUDIO / f"_tmp_{roteiro_path.stem}"
                wavs = processar_dialogo(texto, args.voz_a, args.voz_b, pasta_tmp)
                if not wavs:
                    print("  Aviso: roteiro não está no formato APRESENTADOR_A/B, gerando com voz única.")
                    rodar_piper(texto, args.voz_a, destino_final)
                else:
                    concatenar_wavs(wavs, destino_final)
                    for w in wavs:
                        w.unlink()
                    pasta_tmp.rmdir()
            else:
                rodar_piper(texto, args.voz_a, destino_final)
        except FileNotFoundError:
            print("  ERRO: comando 'piper' não encontrado. Confira se está instalado e no PATH.")
            return
        except Exception as e:
            print(f"  ERRO: {e}")
            continue

        print(f"  -> salvo em {destino_final}")

    print("\nConcluído.")


if __name__ == "__main__":
    main()
