import os
import sys
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ModuleNotFoundError:
    print("[ERRO] Instale as dependências: python -m pip install selenium webdriver-manager requests")
    sys.exit(1)

URL_MP = "https://www.mercadopago.com.br/point-fast/account-consult"
SPREADSHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1Sk9n1TO-tv8GqTVegme428BeYR7g25JeBltBOXpdGqE/export?format=csv&gid=0"

def testar_primeiro_cnpj():
    print("Buscando CNPJs da planilha...")
    resp = requests.get(SPREADSHEET_CSV_URL)
    cnpjs = list(set(re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', resp.text)))
    
    if not cnpjs:
        print("[ERRO] Nenhum CNPJ encontrado na planilha!")
        return

    cnpj_teste = cnpjs[0]
    print(f"Testando com o CNPJ: {cnpj_teste}\n")

    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    user_data_dir = os.path.join(os.getcwd(), "perfil_chrome_selenium")
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument("--start-maximized")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    driver.get(URL_MP)
    wait = WebDriverWait(driver, 20)

    try:
        print("Aguardando campo de texto visível e interativo...")
        # Localiza um campo de texto visível na tela
        input_cnpj = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='text'], input[type='number'], input")))
        
        # Clica para dar foco antes de digitar
        input_cnpj.click()
        
        # Limpa o campo usando atalhos de teclado para evitar o erro 'invalid element state'
        input_cnpj.send_keys(Keys.CONTROL + "a")
        input_cnpj.send_keys(Keys.BACKSPACE)
        
        # Digita o CNPJ
        input_cnpj.send_keys(cnpj_teste)
        print("CNPJ digitado com sucesso.")

        time.sleep(1)

        print("Enviando formulário...")
        # Tenta dar ENTER no campo ou clicar no botão
        input_cnpj.send_keys(Keys.ENTER)
        
        print("Aguardando 5 segundos para resposta...")
        time.sleep(5)

        texto_pagina = driver.find_element(By.TAG_NAME, "body").text
        print("\n--- TRECHO DA RESPOSTA NA TELA ---")
        print(texto_pagina[:600])
        print("----------------------------------\n")

    except Exception as e:
        print(f"\n[ERRO DURANTE O TESTE]: {e}")

if __name__ == "__main__":
    testar_primeiro_cnpj()