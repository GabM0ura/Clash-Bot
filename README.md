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
