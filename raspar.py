import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ModuleNotFoundError:
    print("\n[ERRO] A biblioteca 'webdriver-manager' não foi encontrada.")
    print("Execute: python -m pip install selenium webdriver-manager\n")
    sys.exit(1)


def carregar_navegador_autenticado():
    chrome_options = Options()
    
    # Mantém a janela aberta após execução
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Aponta para o MESMO perfil onde o login foi realizado no login.py
    user_data_dir = os.path.join(os.getcwd(), "perfil_chrome_selenium")
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    
    chrome_options.add_argument("--start-maximized")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Burlar detecção de automação
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def executar_raspagem():
    driver = carregar_navegador_autenticado()
    
    # -------------------------------------------------------------
    # DIGITE AQUI A URL ONDE FICAM OS DADOS QUE VOCÊ QUER RASPAGEM:
    url_alvo = "https://example.com"
    # -------------------------------------------------------------
    
    print(f"Acessando a página: {url_alvo}...")
    driver.get(url_alvo)
    
    # Exemplo de espera até um elemento carregar na tela (espera até 10 segundos)
    wait = WebDriverWait(driver, 10)
    
    try:
        # Exemplo: Espera uma tag <h1> carregar para pegar o texto
        # Ajuste a tag, ID ou Class conforme o site que você vai raspar
        elemento = wait.until(EC.presence_of_element_at_located((By.TAG_NAME, "h1")))
        print("\n--- DADOS ENCONTRADOS ---")
        print("Texto capturado:", elemento.text)
        print("-------------------------\n")
        
    except Exception as e:
        print(f"Erro ou tempo limite excedido ao buscar elemento: {e}")


if __name__ == "__main__":
    executar_raspagem()