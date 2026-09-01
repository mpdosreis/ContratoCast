# Contratos → Podcast

Pipeline que transforma PDFs de contratos em episódios de podcast narrados, rodando **100% offline** na sua máquina. Nenhum trecho dos documentos sai do seu computador.

```
pdfs/*.pdf
   │
   ├─[1] Extração (PyMuPDF) ──────────→ markdown/*.md
   │
   ├─[2] Roteirização (LLM via Ollama) ─→ roteiros/*.txt
   │
   └─[3] Síntese de voz (Piper TTS) ────→ audio/*.wav
```

---

## Índice

- [Por que offline](#por-que-offline)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Uso](#uso)
- [Como cada etapa funciona](#como-cada-etapa-funciona)
- [Customização](#customização)
- [Solução de problemas](#solução-de-problemas)
- [Limitações](#limitações)
- [Licença](#licença)

---

## Por que offline

Contratos costumam conter dados sensíveis: valores, nomes, CNPJs, cláusulas de confidencialidade. Enviar esse conteúdo para APIs de terceiros pode violar acordos de sigilo ou políticas internas. Este projeto usa apenas ferramentas que rodam localmente:

| Etapa | Ferramenta | Roda offline |
|---|---|---|
| Extração de PDF | PyMuPDF | ✅ |
| Geração de roteiro | Ollama (LLM local) | ✅ |
| Síntese de voz | Piper TTS | ✅ |

---

## Requisitos

**Mínimo:**
- Python 3.10+
- 8 GB de RAM (com modelo leve, ex. `llama3.2:3b`)
- ~5 GB de disco livre (modelo + vozes)
- CPU apenas — GPU não é obrigatória

**Recomendado:**
- 16 GB de RAM
- GPU dedicada (acelera bastante a etapa 2)

---

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/SEU_USUARIO/contratos-podcast.git
cd contratos-podcast
```

### 2. Dependências Python

```bash
pip install -r requirements.txt
```

> **Windows:** ao instalar o Python, marque a caixa **"Add python.exe to PATH"** na primeira tela do instalador. Sem isso, os comandos `python` e `pip` não funcionam no terminal.

### 3. Ollama (geração do roteiro)

1. Baixe em [ollama.com/download](https://ollama.com/download) e instale.
2. Baixe um modelo:

```bash
# Máquinas com 8 GB de RAM ou CPU apenas:
ollama pull llama3.2:3b

# Máquinas com 16 GB+:
ollama pull llama3.1:8b

# Máquinas com 32 GB+ ou GPU dedicada (melhor compreensão de texto jurídico):
ollama pull qwen2.5:14b
```

O Ollama sobe automaticamente como serviço e escuta em `localhost:11434`. Se não estiver rodando, use `ollama serve`.

### 4. Piper TTS (síntese de voz)

1. Baixe o binário do seu sistema em [github.com/rhasspy/piper/releases](https://github.com/rhasspy/piper/releases).
   - Windows: `piper_windows_amd64.zip`
   - Linux: `piper_linux_x86_64.tar.gz`
   - macOS: `piper_macos_x64.tar.gz` (ou `aarch64` para Apple Silicon)
2. Extraia e coloque o executável no PATH.
   > **Windows:** o jeito mais simples é colocar o `piper.exe` (e as DLLs que vêm junto) **direto na raiz do projeto**, ao lado dos arquivos `.py`. Assim não é preciso mexer nas variáveis de ambiente.
3. Baixe uma voz em português brasileiro — são **dois arquivos por voz** (`.onnx` e `.onnx.json`). Lista completa em [VOICES.md](https://github.com/rhasspy/piper/blob/master/VOICES.md).

| Voz | Perfil | Peso |
|---|---|---|
| `pt_BR-faber-medium` | masculina, boa qualidade | médio |
| `pt_BR-edresson-low` | masculina, mais leve | leve |

4. Coloque os arquivos baixados na pasta `vozes/`.

Estrutura final esperada:

```
contratos-podcast/
├── 1_pdf_para_markdown.py
├── 2_markdown_para_roteiro.py
├── 3_roteiro_para_audio.py
├── requirements.txt
├── piper.exe                 ← só no Windows, se optar por essa abordagem
├── pdfs/                     ← coloque seus contratos aqui
├── markdown/                 ← gerado pela etapa 1
├── roteiros/                 ← gerado pela etapa 2
├── audio/                    ← gerado pela etapa 3
└── vozes/
    ├── pt_BR-faber-medium.onnx
    └── pt_BR-faber-medium.onnx.json
```

---

## Uso

**1.** Coloque os PDFs em `pdfs/`.

**2.** Extraia para markdown:

```bash
python 1_pdf_para_markdown.py
```

**3.** Gere o roteiro do podcast:

```bash
# Narração com um apresentador
python 2_markdown_para_roteiro.py --modelo llama3.2:3b

# Diálogo entre dois apresentadores
python 2_markdown_para_roteiro.py --modelo llama3.2:3b --vozes 2
```

**4.** Revise os arquivos em `roteiros/`. Esta etapa é importante — veja [Limitações](#limitações).

**5.** Gere o áudio:

```bash
# Uma voz
python 3_roteiro_para_audio.py --voz-a vozes/pt_BR-faber-medium.onnx

# Duas vozes (roteiro em formato diálogo)
python 3_roteiro_para_audio.py \
    --voz-a vozes/pt_BR-faber-medium.onnx \
    --voz-b vozes/pt_BR-edresson-low.onnx
```

Os episódios finais ficam em `audio/*.wav`.

**Converter para MP3** (requer [ffmpeg](https://ffmpeg.org/)):

```bash
ffmpeg -i audio/contrato.wav -b:a 128k audio/contrato.mp3
```

---

## Como cada etapa funciona

### Etapa 1 — `1_pdf_para_markdown.py`

Lê cada PDF com PyMuPDF e aplica limpeza de texto:

- Junta palavras quebradas por hífen no fim da linha (`contra-\nto` → `contrato`)
- Reconecta parágrafos partidos pela quebra de página do PDF
- Normaliza espaços e quebras múltiplas
- Detecta cabeçalhos de cláusulas por heurística (`CLÁUSULA I`, `ARTIGO 3`, `§ 2`, linhas em caixa alta) e os converte em títulos markdown (`##`)

### Etapa 2 — `2_markdown_para_roteiro.py`

Envia cada markdown ao Ollama com um prompt que instrui o modelo a:

- adotar tom conversacional, explicando para público leigo;
- cobrir partes envolvidas, obrigações, prazos, valores, penalidades e rescisão;
- traduzir jargão jurídico sem inventar informação;
- resumir o sentido prático em vez de ler cláusula por cláusula.

No modo `--vozes 2`, o prompt pede um diálogo com falas prefixadas por `APRESENTADOR_A:` e `APRESENTADOR_B:` — formato que a etapa 3 usa para alternar as vozes.

### Etapa 3 — `3_roteiro_para_audio.py`

Chama o binário do Piper via `subprocess`, passando o texto pelo stdin.

No modo diálogo, cada fala vira um `.wav` temporário; ao final, os trechos são concatenados na ordem com 400 ms de silêncio entre eles, e os temporários são apagados.

---

## Customização

### Trocar o tom do podcast

Os prompts ficam no topo de `2_markdown_para_roteiro.py`, nas constantes `PROMPT_UMA_VOZ` e `PROMPT_DUAS_VOZES`. É o ponto de ajuste mais impactante do projeto.

Exemplos de alterações úteis:

```python
# Tom mais técnico, para público jurídico:
- Tom conversacional, como se estivesse explicando para um amigo.
+ Tom técnico-profissional, para advogados e gestores de contratos.
+ Mantenha a terminologia jurídica correta, explicando termos raros brevemente.

# Episódios mais curtos:
+ O roteiro deve ter no máximo 800 palavras, priorizando os pontos críticos.

# Foco em riscos:
+ Dê ênfase especial a cláusulas de risco: multas, rescisão unilateral,
+ foro, garantias e responsabilidade solidária.
```

### Ajustar o silêncio entre as falas

Em `3_roteiro_para_audio.py`, na função `concatenar_wavs`:

```python
def concatenar_wavs(caminhos_wav, destino, silencio_ms: int = 400):
```

Aumente para uma conversa mais pausada (ex. `700`), diminua para um ritmo mais ágil (ex. `250`).

### Mudar a heurística de detecção de cláusulas

Em `1_pdf_para_markdown.py`, na função `detectar_titulo_clausula`. Se seus contratos usam outro padrão (`SEÇÃO 4`, `Item 3.2`), adicione a regex correspondente:

```python
padroes = [
    r"^CL[ÁA]USULA\s+[\dIVXLC]+",
    r"^ARTIGO\s+[\dIVXLC]+",
    r"^SE[ÇC][ÃA]O\s+[\dIVXLC]+",   # ← novo padrão
    ...
]
```

### Usar mais de duas vozes

O formato de diálogo é definido pelo prefixo das falas. Para adicionar um terceiro apresentador, ajuste o `PROMPT_DUAS_VOZES` para incluir `APRESENTADOR_C:` e acrescente o ramo correspondente em `processar_dialogo`, na etapa 3.

### Trocar o Ollama por outro runtime

O script usa a API HTTP do Ollama em `OLLAMA_URL`. Qualquer runtime que exponha um endpoint compatível pode ser plugado ajustando `chamar_ollama` — a estrutura da requisição está isolada nessa função.

### Ajustar a velocidade da fala

O Piper aceita o parâmetro `--length_scale` (valores maiores = fala mais lenta). Para usá-lo, adicione ao comando em `rodar_piper`:

```python
comando = [
    "piper", "--model", modelo_onnx,
    "--length_scale", "1.1",        # ← 1.0 é o padrão
    "--output_file", str(destino_wav),
]
```

---

## Solução de problemas

**`ModuleNotFoundError: No module named 'fitz'`**
O PyMuPDF não foi instalado. Rode `pip install pymupdf`.

**`Não consegui conectar ao Ollama em localhost:11434`**
O serviço não está rodando. Abra o Ollama (Windows/macOS) ou rode `ollama serve` no terminal.

**`ERRO: comando 'piper' não encontrado`**
O executável não está no PATH. No Windows, a solução mais simples é copiar o `piper.exe` para a raiz do projeto.

**A máquina trava ou fica muito lenta na etapa 2**
O modelo é grande demais para a RAM disponível. Troque para `llama3.2:3b` ou `phi3:mini` e feche navegador e outros aplicativos pesados antes de rodar.

**O áudio sai com pronúncia estranha em siglas e números**
Comum em TTS. Ajuste o prompt da etapa 2 para pedir que o modelo escreva valores e siglas por extenso — ex. "R$ 1.500,00" → "mil e quinhentos reais".

**O roteiro sai truncado ou incompleto**
Contratos muito longos podem estourar a janela de contexto do modelo. Divida o markdown em partes menores ou use um modelo com contexto maior.

---

## Limitações

- **Revisão humana é necessária.** Modelos locais de 3B a 14B são bons em explicar em linguagem simples, mas podem simplificar demais ou errar detalhes de valores, prazos e condições de rescisão. Sempre revise o roteiro antes de gerar o áudio final.
- **Não substitui análise jurídica.** O output é material informativo, não parecer legal.
- **PDFs escaneados não funcionam** sem OCR. A extração depende de texto selecionável no PDF; para documentos digitalizados, é preciso passar antes por uma ferramenta de OCR (ex. [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF)).
- **Tempo de processamento.** Em CPU, a etapa 2 pode levar alguns minutos por contrato longo.

---

## Licença

MIT — veja [LICENSE](LICENSE).
