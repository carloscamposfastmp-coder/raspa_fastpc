@echo off
:: Navega ate a pasta do projeto
cd /d C:\Agenda_fast

:: Ativa o ambiente virtual e roda o script
call venv\Scripts\activate
python PROCESSAR_CLIENTES.py

:: Opcional: Pausa para voce ver se deu erro caso esteja na frente do PC
:: timeout /t 10
exit