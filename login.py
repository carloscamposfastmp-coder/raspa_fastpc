import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ModuleNotFoundError:
    print("\n[ERRO] A biblioteca 'webdriver-manager' não foi encontrada.")
    print("Execute: python -m pip install selenium webdriver-manager\n")
    sys.exit(1)


def iniciar_navegador_seguro():
    chrome_options = Options()

    # 1. Mantém o navegador aberto
    chrome_options.add_experimental_option("detach", True)

    # 2. Esconde o aviso "O Chrome está sendo controlado por um software de teste automatizado"
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 3. Altera a flag de automação que o Google detecta
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # 4. Usa um perfil do Chrome dedicado para manter o login salvo e passar pelas verificações
    user_data_dir = os.path.join(os.getcwd(), "perfil_chrome_selenium")
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

    # Argumentos extras de compatibilidade
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")

    print("Iniciando o Google Chrome em modo seguro...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Injeta script JavaScript para remover o rastro 'navigator.webdriver'
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    return driver


if __name__ == "__main__":
    navegador = iniciar_navegador_seguro()

    # Redireciona para o login do Google
    url_alvo = "https://accounts.google.com/"
    navegador.get(url_alvo)

    print("\n[OK] Navegador aberto com bypass de detecção.")
    print("Tente realizar o login manualmente no Chrome que se abriu.")
    print("Como o perfil fica salvo na pasta 'perfil_chrome_selenium', você só precisará logar uma vez!\n")