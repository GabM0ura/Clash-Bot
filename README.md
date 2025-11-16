# Clash-Bot — protótipo ADB + OpenCV

Este repositório contém um scaffold inicial para um bot que captura a tela de um dispositivo Android (emulador) via `adb`, realiza detecção por template com OpenCV e envia toques (`input tap`) via `adb`.

Aviso importante
- Automatizar interações com o jogo pode violar os Termos de Serviço do Clash of Clans e resultar em banimento.
- Teste somente em contas secundárias ou em um ambiente de teste.

Requisitos
- Python 3.9+ instalado
- `adb` (Android Platform Tools) disponível no `PATH`
- Emulador Android rodando em resolução Full HD (1920x1080) ou similar e visível via `adb devices`

Instalação
1. Crie um ambiente virtual (recomendado):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instale dependências:

```powershell
pip install -r requirements.txt
```

Uso
1. Coloque imagens de template (por exemplo, um botão do jogo) em uma pasta do projeto.
2. Execute o script apontando para a imagem do template. Exemplo:

```powershell
python -m bot.adb_bot --template templates/btn_attack.png --threshold 0.88 --loop
```

Lançador simples (Windows)
--------------------------
Removi a GUI e adicionei um lançador simples para Windows chamado `INICIAR.bat` na raiz do repositório.

Uso rápido no Windows (duplo-clique):

 - Dê um duplo-clique em `INICIAR.bat` para iniciar o fluxo `keyboard_deploy_flow` (padrão: `--keys 1-8`).

Uso manual (PowerShell):

```powershell
python -m bot.keyboard_deploy_flow --keys 1-8
```

Instalando e testando `adb` no Windows
--------------------------------------
Se o `INICIAR.bat` falhar com erro relacionado a `adb` (arquivo não encontrado), siga estes passos:

1. Baixe o Android Platform Tools (contém `adb`) de:
	https://developer.android.com/studio/releases/platform-tools
2. Extraia o conteúdo (uma pasta com `adb.exe`).
3. Teste no PowerShell apontando diretamente para o `adb.exe`:

```powershell
# Substitua pelo caminho real onde extraiu
C:\path\to\platform-tools\adb.exe devices
```

4. Para usar `adb` em qualquer terminal, adicione a pasta ao `PATH` (apenas para esta sessão):

```powershell
$env:PATH = "$env:PATH;C:\path\to\platform-tools"
adb devices
```

5. Ou defina `ADB_PATH` para apontar ao `adb.exe` (útil se não quiser mexer no PATH):

```powershell
$env:ADB_PATH = 'C:\path\to\platform-tools\adb.exe'
python -m bot.keyboard_deploy_flow --keys 1-8
```

Se ainda houver erro, cole aqui a saída de `adb devices` e a primeira parte do log — eu ajudo a diagnosticar.

Se preferir executar outro fluxo, rode diretamente qualquer um dos módulos:

```powershell
python -m bot.attack_flow --attack-dir templates\attack_buttons --end-dir templates\end_screens
python -m bot.adb_bot --templates-dir templates --loop
```

Usar sem ADB (alternativa)
---------------------------
Se o seu emulador já aceita teclas do teclado quando a sua janela está em foco, você não precisa do `adb` para enviar teclas — pode usar o script sem-ADB:

```powershell
python -m bot.keyboard_deploy_noadb --focus-window "BlueStacks"
# ou apenas:
python -m bot.keyboard_deploy_noadb --once
```

Observações:
- Este método usa `pyautogui` para enviar teclas/mouse ao sistema operacional. Ele depende da janela do emulador estar em foco e de o emulador mapear teclas do host para o jogo.
- Se quiser automação baseada em visão (capturar a tela do emulador), ADB ainda é a opção mais robusta porque permite `adb exec-out screencap -p` e `input tap` mesmo quando a janela não está em foco.
- Instale dependências adicionais com:

```powershell
pip install pyautogui pygetwindow
```

Opções principais
- `--template` (`-t`): caminho para a imagem de template (PNG/JPG)
- `--templates-dir` (`-d`): diretório com várias imagens de template; o script tentará todas
- `--threshold`: threshold de similaridade (0-1). Ajuste conforme necessidade.
- `--loop`: mantém o script procurando e tocando em loop
- `--once`: toca uma vez ao encontrar e sai
- `--randomize`: randomiza a posição do toque dentro da área do template (reduce pattern detection)
- `--jitter`: quantidade de jitter (pixels) para randomização quando não há bbox do template
- `--scale-min`, `--scale-max`, `--scale-steps`: controle da busca multi-escala (padrões: 0.8,1.2,9)

Como prosseguir
- Melhorias de detecção: permitir múltiplas escalas, usar OCR para textos, ou treinar um classificador baseado em exemplos.
- Fluxos: criar módulos para "ataque" e "upgrade" que combinem várias detecções e ações encadeadas.

Contribuições e segurança
- Não posso ajudar a implementar funcionalidades que visem roubar, trapacear ou causar danos a terceiros. Este scaffold é educacional — use com responsabilidade.
