@echo off
REM INICIAR - inicia o fluxo de teclado do Clash-Bot
REM Execute este arquivo dando um duplo-clique no Windows Explorer.

SETLOCAL
echo Iniciando Clash-Bot (keyboard_deploy_flow)...

REM Tenta usar o python do PATH
python -m bot.keyboard_deploy_flow --keys 1-8

IF %ERRORLEVEL% NEQ 0 (
    echo Erro ao iniciar via `python`. Tente executar manualmente:
    echo     python -m bot.keyboard_deploy_flow --keys 1-8
)

echo Processo finalizado. Pressione qualquer tecla para fechar...
pause >nul
ENDLOCAL
