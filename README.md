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

**Não é necessário:** conhecimento de programação, Git instalado, conta em
nenhum serviço, ou conexão com a internet depois da instalação.

---

## Instalação

> **Nunca usou terminal antes?** Sem problema. Este guia assume que você não tem
> nada instalado e explica cada passo, incluindo o que é cada coisa. Você **não
> precisa instalar o Git** — o download é feito direto pelo navegador.
>
> Reserve cerca de 30 minutos na primeira vez. Depois de instalado, rodar o
> pipeline leva poucos minutos.

### Antes de começar: o que é o "terminal"

Algumas etapas pedem para você digitar comandos. Isso é feito numa janela preta
(ou azul) chamada **terminal** ou **PowerShell** no Windows. Você digita uma
linha, aperta Enter, e espera aparecer o resultado.

**Como abrir o terminal já dentro da pasta certa (Windows):**

1. Abra a pasta do projeto no Explorador de Arquivos
2. Clique na **barra de endereço** no topo (onde aparece o caminho da pasta)
3. Apague o que estiver escrito, digite `powershell` e aperte **Enter**

Uma janela azul vai abrir, já posicionada na pasta do projeto. É nela que os
comandos deste guia devem ser digitados.

> Se um comando der erro, não tem problema — a seção
> [Solução de problemas](#solução-de-problemas) no fim deste README explica os
> erros mais comuns.

---

### Passo 1 — Baixar o projeto

1. Acesse [github.com/mpdosreis/contratos-podcast](https://github.com/mpdosreis/contratos-podcast)
2. Clique no botão verde **`< > Code`**
3. No menu que abrir, clique em **Download ZIP**
4. Abra a pasta Downloads, clique com o botão direito no arquivo baixado e
   escolha **Extrair tudo**
5. Extraia para um caminho curto e sem acentos — por exemplo `C:\contratos-podcast`

> **Por que sem acentos?** Caminhos com acentos ou espaços às vezes causam erro
> em ferramentas de linha de comando. `C:\contratos-podcast` funciona sempre.

Ao entrar na pasta extraída, você deve ver os arquivos `1_pdf_para_markdown.py`,
`2_markdown_para_roteiro.py`, `3_roteiro_para_audio.py` e `README.md`.

> Se ao abrir a pasta você encontrar **outra pasta com o mesmo nome dentro**,
> entre nela — o Windows às vezes cria essa camada extra ao extrair. Os arquivos
> `.py` precisam estar visíveis logo ao abrir a pasta que você vai usar.

---

### Passo 2 — Instalar o Python

O Python é a linguagem em que os scripts foram escritos. Sem ele, nada roda.

1. Acesse [python.org/downloads](https://www.python.org/downloads/)
2. Clique no botão amarelo **Download Python** (a versão mais recente serve)
3. Execute o instalador baixado
4. **Na primeira tela, marque a caixa "Add python.exe to PATH"** (fica embaixo,
   e vem desmarcada por padrão)
5. Clique em **Install Now** e aguarde

> ⚠️ **A caixa "Add python.exe to PATH" é o erro nº 1 de quem está começando.**
> Sem ela marcada, o terminal responde `python não é reconhecido` mais adiante.
> Se você esqueceu, basta rodar o instalador de novo, escolher **Modify** e
> marcar a opção.

**Conferindo se deu certo:** abra o terminal (como explicado acima) e digite:

```powershell
python --version
```

Deve aparecer algo como `Python 3.12.4`. Se aparecer uma mensagem de erro,
reinstale marcando a caixa do PATH.

---

### Passo 3 — Instalar as bibliotecas do Python

Com o terminal aberto **dentro da pasta do projeto**, digite:

```powershell
pip install -r requirements.txt
```

Isso baixa duas bibliotecas: o **PyMuPDF** (lê os PDFs) e o **requests** (conversa
com o Ollama). Vai aparecer bastante texto na tela — é normal. Quando voltar a
aparecer o cursor esperando um novo comando, terminou.

---

### Passo 4 — Instalar o Ollama (a IA que escreve o roteiro)

O Ollama é o programa que roda modelos de IA na sua máquina, sem internet.

1. Acesse [ollama.com/download](https://ollama.com/download)
2. Baixe a versão do seu sistema e instale normalmente (avançar, avançar,
   concluir)
3. Depois de instalado, ele fica rodando sozinho em segundo plano — você vai ver
   um ícone de lhama perto do relógio, no canto inferior direito da tela

Agora é preciso baixar um **modelo** (o "cérebro" que o Ollama usa). No terminal:

```powershell
ollama pull llama3.2:3b
```

O download tem cerca de 2 GB e leva alguns minutos. Escolha o modelo conforme a
memória RAM da sua máquina:

| Sua RAM | Comando | Observação |
|---|---|---|
| 8 GB ou CPU sem placa de vídeo | `ollama pull llama3.2:3b` | leve e rápido |
| 16 GB | `ollama pull llama3.1:8b` | melhor qualidade de texto |
| 32 GB ou GPU dedicada | `ollama pull qwen2.5:14b` | melhor com texto jurídico |

> **Não sabe quanta RAM tem?** No Windows, aperte `Ctrl + Shift + Esc` para abrir
> o Gerenciador de Tarefas, vá na aba **Desempenho** e clique em **Memória**. Na
> dúvida, comece pelo `llama3.2:3b` — ele funciona em qualquer máquina.

---

### Passo 5 — Instalar o Piper (a voz do podcast)

O Piper transforma o roteiro em áudio falado. Ele não tem instalador: é só
baixar e descompactar.

1. Acesse [github.com/rhasspy/piper/releases](https://github.com/rhasspy/piper/releases)
2. Na versão mais recente (no topo da página), procure a lista **Assets** e baixe
   o arquivo do seu sistema:
   - **Windows:** `piper_windows_amd64.zip`
   - **Linux:** `piper_linux_x86_64.tar.gz`
   - **macOS:** `piper_macos_x64.tar.gz` (ou `_aarch64` se for Apple Silicon)
3. Extraia o arquivo baixado
4. **Copie todo o conteúdo extraído para dentro da pasta do projeto** — ou seja,
   o `piper.exe` deve ficar lado a lado com os arquivos `1_pdf_para_markdown.py`,
   `2_markdown_para_roteiro.py` etc.

> **Por que copiar para dentro da pasta?** Assim você evita mexer nas variáveis
> de ambiente do Windows, que é uma configuração chata e fácil de errar. Deixando
> o `piper.exe` junto dos scripts, tudo funciona sem configuração extra.
>
> ⚠️ Copie **todos** os arquivos extraídos, não apenas o `piper.exe`. As DLLs e a
> pasta `espeak-ng-data` que vêm junto são necessárias para ele funcionar.

---

### Passo 6 — Baixar uma voz em português

O Piper sozinho não fala nada: ele precisa de um arquivo de voz.

1. Acesse a [lista oficial de vozes (VOICES.md)](https://github.com/rhasspy/piper/blob/master/VOICES.md)
2. Aperte `Ctrl + F` e busque por **`pt_BR`**
3. Escolha uma voz e baixe **os dois arquivos** dela:

| Voz | Perfil | Peso |
|---|---|---|
| `pt_BR-faber-medium` | masculina, boa qualidade | médio |
| `pt_BR-edresson-low` | masculina, mais leve | leve |

> ⚠️ **Cada voz tem dois arquivos** e os dois são obrigatórios:
> - `pt_BR-faber-medium.onnx` (a voz em si, arquivo maior)
> - `pt_BR-faber-medium.onnx.json` (as configurações, arquivo pequeno)
>
> Se faltar o `.json`, o Piper acusa erro ao rodar.

4. Crie uma pasta chamada `vozes` dentro da pasta do projeto e coloque os dois
   arquivos lá dentro.

> **Quer duas vozes diferentes conversando no podcast?** Baixe também a
> `pt_BR-edresson-low` (os dois arquivos dela) e coloque na mesma pasta `vozes`.

---

### Conferindo: sua pasta deve estar assim

```
contratos-podcast/
├── 1_pdf_para_markdown.py
├── 2_markdown_para_roteiro.py
├── 3_roteiro_para_audio.py
├── requirements.txt
├── README.md
├── piper.exe                      ← veio do Passo 5 (Windows)
├── espeak-ng-data/                ← veio junto do Piper
├── pdfs/                          ← crie esta pasta e coloque seus contratos
└── vozes/                         ← crie esta pasta
    ├── pt_BR-faber-medium.onnx
    └── pt_BR-faber-medium.onnx.json
```

As pastas `markdown/`, `roteiros/` e `audio/` **não precisam ser criadas por
você** — os scripts geram automaticamente ao rodar.

Se a sua pasta está parecida com isso, a instalação terminou. 🎉

---

## Uso

São três comandos, rodados em sequência. Todos devem ser digitados no terminal
**aberto dentro da pasta do projeto** (veja [como abrir](#antes-de-começar-o-que-é-o-terminal)).

### 1. Coloque os contratos na pasta `pdfs/`

Se a pasta não existir, crie uma chamada exatamente `pdfs` dentro do projeto.
Pode colocar vários PDFs de uma vez — cada um vira um episódio separado.

### 2. Extrair o texto dos PDFs

```powershell
python 1_pdf_para_markdown.py
```

O script mostra na tela o nome de cada arquivo enquanto processa. Ao terminar,
uma pasta `markdown/` terá sido criada com os textos extraídos. Leva poucos
segundos.

### 3. Gerar o roteiro do podcast

```powershell
python 2_markdown_para_roteiro.py --modelo llama3.2:3b
```

Para um roteiro em formato de conversa entre dois apresentadores, acrescente
`--vozes 2` no fim:

```powershell
python 2_markdown_para_roteiro.py --modelo llama3.2:3b --vozes 2
```

> ⏱️ **Esta é a etapa mais demorada.** A IA está lendo o contrato inteiro e
> escrevendo o roteiro. Em uma máquina sem placa de vídeo, pode levar de 2 a 10
> minutos por contrato. Parece travado, mas está trabalhando — deixe rodando.
>
> 💡 Feche o navegador e outros programas pesados antes de rodar esta etapa,
> principalmente se sua máquina tem 8 GB de RAM.

> ⚠️ Troque `llama3.2:3b` pelo modelo que você baixou no Passo 4, caso tenha
> escolhido outro.

### 4. Revise o roteiro antes de gerar o áudio

Abra os arquivos `.txt` gerados na pasta `roteiros/` (podem ser abertos no
Bloco de Notas) e leia o conteúdo.

**Não pule esta etapa.** Modelos de IA que rodam localmente podem simplificar
demais ou errar detalhes de valores, prazos e condições de rescisão. Corrija o
que for necessário direto no arquivo `.txt` e salve — a próxima etapa vai usar
exatamente o que estiver ali. Veja [Limitações](#limitações).

### 5. Gerar o áudio

```powershell
python 3_roteiro_para_audio.py --voz-a vozes/pt_BR-faber-medium.onnx
```

Com duas vozes (só faz sentido se você usou `--vozes 2` na etapa 3):

```powershell
python 3_roteiro_para_audio.py --voz-a vozes/pt_BR-faber-medium.onnx --voz-b vozes/pt_BR-edresson-low.onnx
```

> ⚠️ O caminho depois de `--voz-a` precisa bater exatamente com o nome do arquivo
> que você baixou. Se você escolheu outra voz, ajuste o nome no comando.

Pronto — os episódios finais estarão em `audio/`, em formato `.wav`. Podem ser
abertos em qualquer tocador de música.

### Opcional: converter para MP3

Arquivos `.wav` são grandes. Para converter em MP3, instale o
[ffmpeg](https://ffmpeg.org/) e rode:

```powershell
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

**`python não é reconhecido como um comando interno ou externo`**
O Python não foi adicionado ao PATH durante a instalação. Rode o instalador do
Python de novo, escolha **Modify** e marque **"Add python.exe to PATH"**. Feche
e reabra o terminal depois.

**`can't open file ... [Errno 2] No such file or directory`**
O terminal está aberto em outra pasta, não na do projeto. Digite `dir` e aperte
Enter: se os arquivos `.py` não aparecerem na lista, você está no lugar errado.
Feche o terminal e abra novamente pela barra de endereço da pasta correta.

**`ModuleNotFoundError: No module named 'fitz'`**
As bibliotecas do Passo 3 não foram instaladas. Rode `pip install -r requirements.txt`
com o terminal na pasta do projeto.

**`Nenhum PDF encontrado em ...`**
A pasta `pdfs` não existe ou está vazia. Crie a pasta com esse nome exato (tudo
minúsculo, sem acento) dentro do projeto e coloque os PDFs dentro.

**`Não consegui conectar ao Ollama em localhost:11434`**
O Ollama não está rodando. Procure o ícone de lhama perto do relógio; se não
estiver lá, abra o Ollama pelo menu Iniciar e espere alguns segundos antes de
rodar o comando de novo.

**`ERRO: comando 'piper' não encontrado`**
O `piper.exe` não está na pasta do projeto. Confira se ele está lado a lado com
os arquivos `.py` — e se as DLLs e a pasta `espeak-ng-data` foram copiadas junto.

**O Piper reclama de arquivo faltando ao gerar o áudio**
Provavelmente falta o segundo arquivo da voz. Cada voz tem um `.onnx` **e** um
`.onnx.json`, e os dois precisam estar na pasta `vozes`.

**A máquina trava ou fica muito lenta na etapa 2**
O modelo é grande demais para a RAM disponível. Troque para `llama3.2:3b` ou
`phi3:mini` e feche navegador e outros aplicativos pesados antes de rodar.

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
