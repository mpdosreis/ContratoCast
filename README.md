# ContratoCast

Pipeline que transforma PDFs de contratos em **resumos jurídicos narrados**, no
formato de audiolivro, rodando **100% offline** na sua máquina. Nenhum trecho dos
documentos sai do seu computador.

Voltado a quem já trabalha com contratos: o resumo mantém a terminologia técnica
e os dados objetivos (valores, prazos, percentuais, foro), reduzindo o volume de
texto sem simplificar o conteúdo.

```
pdfs/*.pdf
   │
   ├─[1] Extração (PyMuPDF) ─────────────→ markdown/*.md
   │
   ├─[2] Resumo jurídico (LLM via Ollama) → resumos/*.md
   │
   ├─[3] Adaptação p/ narração (Ollama) ──→ narracao/*.txt
   │
   └─[4] Síntese de voz (Piper TTS) ──────→ audio/*.wav
```

**Por que duas passagens de IA?** A etapa 2 cuida do conteúdo (o que entra no
resumo); a etapa 3 cuida da forma falada (escrever "trinta por cento" em vez de
"30%", desfazer listas, remover marcação). Separar as duas evita que o modelo
tente fazer as duas coisas ao mesmo tempo e acabe fazendo mal as duas.

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
| Resumo jurídico | Ollama (LLM local) | ✅ |
| Adaptação para narração | Ollama (LLM local) | ✅ |
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

1. Acesse [github.com/mpdosreis/ContratoCast](https://github.com/mpdosreis/ContratoCast)
2. Clique no botão verde **`< > Code`**
3. No menu que abrir, clique em **Download ZIP**
4. Abra a pasta Downloads, clique com o botão direito no arquivo baixado e
   escolha **Extrair tudo**
5. Extraia para um caminho curto e sem acentos — por exemplo `C:\ContratoCast`

> **Por que sem acentos?** Caminhos com acentos ou espaços às vezes causam erro
> em ferramentas de linha de comando. `C:\ContratoCast` funciona sempre.

Ao entrar na pasta extraída, você deve ver os arquivos `1_pdf_para_markdown.py`,
`2_markdown_para_resumo.py`, `3_resumo_para_narracao.py`,
`4_narracao_para_audio.py` e `README.md`.

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

### Passo 4 — Instalar o Ollama (a IA que resume o contrato)

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

### Passo 5 — Instalar o Piper (a voz da narração)

O Piper transforma o texto em áudio falado. Ele não tem instalador: é só
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
   `2_markdown_para_resumo.py` etc.

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

> **Uma voz basta.** O formato é audiolivro, com narração única — não é preciso
> baixar uma segunda voz. Se quiser experimentar timbres diferentes, baixe mais
> de uma e escolha na hora de rodar a etapa 4.

---

### Conferindo: sua pasta deve estar assim

```
ContratoCast/
├── 1_pdf_para_markdown.py
├── 2_markdown_para_resumo.py
├── 3_resumo_para_narracao.py
├── 4_narracao_para_audio.py
├── requirements.txt
├── README.md
├── piper.exe                      ← veio do Passo 5 (Windows)
├── espeak-ng-data/                ← veio junto do Piper
├── pdfs/                          ← crie esta pasta e coloque seus contratos
└── vozes/                         ← crie esta pasta
    ├── pt_BR-faber-medium.onnx
    └── pt_BR-faber-medium.onnx.json
```

As pastas `markdown/`, `resumos/`, `narracao/` e `audio/` **não precisam ser
criadas por você** — os scripts geram automaticamente ao rodar.

Se a sua pasta está parecida com isso, a instalação terminou. 🎉

---

## Uso

São quatro comandos, rodados em sequência. Todos devem ser digitados no terminal
**aberto dentro da pasta do projeto** (veja [como abrir](#antes-de-começar-o-que-é-o-terminal)).

### 1. Coloque os contratos na pasta `pdfs/`

Se a pasta não existir, crie uma chamada exatamente `pdfs` dentro do projeto.
Pode colocar vários PDFs de uma vez — cada um gera um áudio separado.

### 2. Extrair o texto dos PDFs

```powershell
python 1_pdf_para_markdown.py
```

O script mostra na tela o nome de cada arquivo enquanto processa. Ao terminar,
uma pasta `markdown/` terá sido criada com os textos extraídos. Leva poucos
segundos.

### 3. Gerar o resumo jurídico

```powershell
python 2_markdown_para_resumo.py --modelo llama3.2:3b
```

O contrato é dividido em blocos (por cláusula) e cada bloco é resumido
separadamente. Você acompanha o progresso na tela e, ao final, vê quanto o texto
foi reduzido:

```
Resumindo: contrato_locacao.md (modelo=llama3.2:3b)
  Dividido em 7 bloco(s)
  Resumindo bloco 1/7...
  ...
  -> salvo em resumos\contrato_locacao_resumo.md
     48.320 → 14.905 caracteres (69% de redução)
```

> ⏱️ **Esta é a etapa mais demorada.** Cada bloco é uma chamada à IA. Em uma
> máquina sem placa de vídeo, um contrato longo pode levar de 5 a 20 minutos.
> Parece travado, mas está trabalhando — acompanhe o contador de blocos.
>
> 💡 Feche o navegador e outros programas pesados antes de rodar, principalmente
> se sua máquina tem 8 GB de RAM.

> ⚠️ Troque `llama3.2:3b` pelo modelo que você baixou no Passo 4, caso tenha
> escolhido outro.

**Resumo ficou curto demais?** Diminua o tamanho dos blocos — blocos menores
preservam mais detalhe:

```powershell
python 2_markdown_para_resumo.py --modelo llama3.2:3b --blocos 2500
```

**Resumo ficou longo demais, ou está lento?** Aumente os blocos:

```powershell
python 2_markdown_para_resumo.py --modelo llama3.2:3b --blocos 8000
```

Veja mais em [Customização](#ajustar-o-nível-de-detalhe-do-resumo).

### 4. Revise o resumo

Abra os arquivos `.md` da pasta `resumos/` (o Bloco de Notas abre normalmente) e
confira o conteúdo.

**Não pule esta etapa.** Modelos rodando localmente podem errar valores, prazos e
condições de rescisão. Corrija direto no arquivo e salve — as etapas seguintes
usam exatamente o que estiver ali. Veja [Limitações](#limitações).

### 5. Adaptar o resumo para narração

```powershell
python 3_resumo_para_narracao.py --modelo llama3.2:3b
```

Esta etapa não resume mais nada: ela reescreve o texto para ser **ouvido**.
Valores viram por extenso ("mil e quinhentos reais"), listas viram frases
corridas, e toda marcação é removida. O resultado sai em `narracao/`, com uma
estimativa da duração do áudio:

```
  -> salvo em narracao\contrato_locacao_narracao.txt
     2.140 palavras (~14 min de áudio)
```

### 6. Gerar o áudio

```powershell
python 4_narracao_para_audio.py --voz vozes/pt_BR-faber-medium.onnx
```

Para uma leitura um pouco mais pausada:

```powershell
python 4_narracao_para_audio.py --voz vozes/pt_BR-faber-medium.onnx --velocidade 1.15
```

> ⚠️ O caminho depois de `--voz` precisa bater exatamente com o nome do arquivo
> que você baixou. Se escolheu outra voz, ajuste o nome no comando.

Pronto — os áudios finais estarão em `audio/`, em formato `.wav`. Podem ser
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
- Detecta cabeçalhos de cláusulas por heurística (`CLÁUSULA I`, `ARTIGO 3`, `§ 2`,
  linhas em caixa alta) e os converte em títulos markdown (`##`)

Esses títulos não são decorativos: a etapa 2 usa eles para saber onde cortar o
documento em blocos.

### Etapa 2 — `2_markdown_para_resumo.py`

**Divide antes de resumir.** Mandar um contrato inteiro para um modelo pequeno
faz ele comprimir agressivamente — é a causa mais comum de resumo raso. O script
quebra o documento em blocos (preferindo cortar nos títulos de cláusula) e resume
cada bloco separadamente, o que preserva muito mais detalhe.

Se uma cláusula isolada exceder o limite do bloco, ela é subdividida por
parágrafo e, se necessário, por frase — e o título da cláusula é repetido no
início de cada pedaço, marcado como `(continuação)`, para o modelo não perder o
contexto.

O prompt instrui o modelo a:

- manter a terminologia jurídica, sem traduzir para linguagem leiga;
- preservar literalmente valores, percentuais, prazos, datas, índices, foro e
  qualificação das partes;
- eliminar apenas redundâncias e texto protocolar;
- não comentar, não opinar e não avaliar riscos.

A temperatura é fixada em `0.2` — valor baixo reduz a chance de o modelo inventar
dados, o que importa especialmente em texto jurídico.

Blocos meramente protocolares são descartados: o modelo responde
`[SEM CONTEUDO RELEVANTE]` e o script os ignora.

### Etapa 3 — `3_resumo_para_narracao.py`

Segunda passagem pela IA, agora só de **forma**, não de conteúdo. O prompt proíbe
explicitamente resumir ou cortar qualquer coisa, e pede:

- valores, datas, percentuais e siglas por extenso — o sintetizador de voz
  pronuncia mal `R$ 1.500,00`, `30%`, `art. 5º` e `CNPJ`;
- listas convertidas em prosa corrida, com conectivos;
- toda marcação markdown removida;
- tom neutro de audiolivro, sem saudações nem locução.

Depois da IA, uma limpeza por regex remove qualquer marcação residual que tenha
escapado (asteriscos, cerquilhas, bullets, numeração).

Ao final, o script estima a duração do áudio a 150 palavras por minuto.

### Etapa 4 — `4_narracao_para_audio.py`

Chama o binário do Piper via `subprocess`, passando o texto pelo stdin.

A síntese é feita **parágrafo a parágrafo**, e os trechos são concatenados com
500 ms de silêncio entre eles. Isso produz pausas naturais na leitura e evita
sobrecarregar o Piper com um texto único muito longo. Os arquivos temporários são
apagados ao final, inclusive se ocorrer erro no meio do processo.

O script procura o `piper.exe` na pasta do projeto antes de tentar o PATH do
sistema, e verifica se o arquivo `.onnx.json` da voz existe antes de começar.

---

## Customização

### Ajustar o nível de detalhe do resumo

**O jeito mais fácil, sem editar código:** mude o tamanho dos blocos.

```powershell
python 2_markdown_para_resumo.py --blocos 2500   # mais detalhe, mais lento
python 2_markdown_para_resumo.py --blocos 8000   # mais condensado, mais rápido
```

Blocos menores significam menos texto por chamada, então o modelo comprime menos
e preserva mais detalhe. O padrão é `4000` caracteres.

Há também o modo sem divisão, que envia o contrato inteiro de uma vez — mais
rápido, porém com resumo bem mais condensado:

```powershell
python 2_markdown_para_resumo.py --sem-blocos
```

**Trocar o modelo** também muda bastante o resultado. Modelos maiores resumem com
mais nuance, se a sua máquina aguentar:

```powershell
python 2_markdown_para_resumo.py --modelo qwen2.5:14b
```

### Mudar o que entra no resumo

O prompt fica no topo de `2_markdown_para_resumo.py`, na constante `PROMPT_BLOCO`.
É o ponto de ajuste mais impactante do projeto. Exemplos:

```python
# Focar apenas em obrigações e penalidades:
+ Priorize obrigações, penalidades e hipóteses de rescisão. Trate os demais
+ assuntos de forma mais breve.

# Resumo mais agressivo:
+ Seja mais agressivo na redução: o resumo deve ter cerca de um terço do
+ tamanho do trecho original.

# Manter citação da cláusula de origem:
+ Ao final de cada assunto, indique entre parênteses o número da cláusula
+ de onde a informação foi extraída.
```

### Mudar a heurística de detecção de cláusulas

Em `1_pdf_para_markdown.py`, na função `detectar_titulo_clausula`. Se seus
contratos usam outro padrão (`SEÇÃO 4`, `Item 3.2`), adicione a regex:

```python
padroes = [
    r"^CL[ÁA]USULA\s+[\dIVXLC]+",
    r"^ARTIGO\s+[\dIVXLC]+",
    r"^SE[ÇC][ÃA]O\s+[\dIVXLC]+",   # ← novo padrão
    ...
]
```

Vale a pena conferir: quanto melhor a detecção de cláusulas, melhor a divisão em
blocos da etapa 2 — e melhor o resumo.

### Ajustar a pronúncia de termos específicos

Se o áudio pronuncia mal alguma sigla ou termo recorrente do seu setor, adicione
o exemplo na lista do `PROMPT_NARRACAO`, em `3_resumo_para_narracao.py`:

```python
  "CNPJ" vira "cê enê pê jota"
+ "IPCA" vira "i pê cê a"
+ "SLA" vira "esse ele a"
```

### Ajustar velocidade e pausas do áudio

Ambos são parâmetros de linha de comando, sem precisar editar nada:

```powershell
python 4_narracao_para_audio.py --voz vozes/voz.onnx --velocidade 1.15 --pausa 700
```

- `--velocidade`: `1.0` é o padrão. Maior = leitura mais lenta.
- `--pausa`: silêncio entre parágrafos, em milissegundos. Padrão `500`.

### Trocar o Ollama por outro runtime

Os scripts usam a API HTTP do Ollama em `OLLAMA_URL`. Qualquer runtime que exponha
endpoint compatível pode ser plugado ajustando a função `chamar_ollama` — a
estrutura da requisição está isolada nela, nas duas etapas.

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

**`Nenhum resumo encontrado` ou `Nenhum texto encontrado`**
Você pulou uma etapa. A ordem é obrigatória: script 1, depois 2, depois 3, depois 4.
Cada um lê a pasta que o anterior gerou.

**O resumo ficou raso demais**
Diminua o tamanho dos blocos: `python 2_markdown_para_resumo.py --blocos 2500`.
Se ainda assim ficar raso, o modelo é o limitante — teste um maior, como
`llama3.1:8b` ou `qwen2.5:14b`.

**O áudio lê "R$" ou "%" em vez do valor por extenso**
Um trecho escapou da conversão na etapa 3. Corrija direto no arquivo `.txt` da
pasta `narracao/` e rode a etapa 4 de novo — ela usa exatamente o que estiver ali.

**O áudio ficou longo demais**
O resumo está pouco condensado. Aumente os blocos (`--blocos 8000`) ou ajuste o
`PROMPT_BLOCO` pedindo redução mais agressiva. Veja [Customização](#mudar-o-que-entra-no-resumo).

**O áudio sai com pronúncia estranha em siglas e números**
Comum em TTS. Ajuste o prompt da etapa 2 para pedir que o modelo escreva valores e siglas por extenso — ex. "R$ 1.500,00" → "mil e quinhentos reais".

**O resumo sai truncado ou incompleto**
Algum bloco estourou a janela de contexto do modelo. Diminua o tamanho dos blocos:
`python 2_markdown_para_resumo.py --blocos 2000`.

---

## Limitações

- **Revisão humana é necessária.** Modelos locais de 3B a 14B podem errar ou
  omitir valores, prazos e condições de rescisão. O resumo é um ponto de partida
  para leitura, não uma fonte confiável por si só — sempre revise antes de gerar
  o áudio, e volte ao contrato original em caso de dúvida.
- **Não substitui a leitura do contrato** em situações que exijam precisão:
  negociação, litígio, assinatura. O objetivo é reduzir o volume de leitura em
  triagem e revisão de rotina, não eliminar a consulta ao documento.
- **Não substitui análise jurídica.** O output é material informativo, não parecer legal.
- **PDFs escaneados não funcionam** sem OCR. A extração depende de texto selecionável no PDF; para documentos digitalizados, é preciso passar antes por uma ferramenta de OCR (ex. [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF)).
- **Tempo de processamento.** Em CPU, as etapas 2 e 3 podem levar de 5 a 30 minutos por contrato longo, já que cada bloco é uma chamada separada à IA.

---

## Licença

MIT — veja [LICENSE](LICENSE).
