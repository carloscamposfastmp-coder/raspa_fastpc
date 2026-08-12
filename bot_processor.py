import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from google_sheets import GoogleSheetsHandler

# --- CONFIGURAÇÕES ---
SPREADSHEET_ID = "1-iltotMo6k2MZKcHfU9dpBG87v8Juf6dNyH7x0Baez0"
GOOGLE_CREDS_FILE = "credentials.json"  # Certifique-se de salvar suas credenciais do Google aqui

# Inicializa o handler do Google Sheets
sheets_client = GoogleSheetsHandler(GOOGLE_CREDS_FILE, SPREADSHEET_ID)


def safe_click(driver, locator, timeout=10):
    """
    Função utilitária para clicar com segurança em elementos interceptados por modals/overlays.
    """
    try:
        # 1. Espera o overlay/modal desaparecer se existir
        try:
            WebDriverWait(driver, 3).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "andes-modal__overlay"))
            )
        except TimeoutException:
            pass # Se não sumir em 3s, tenta o clique forçado

        # 2. Tenta aguardar o elemento estar clicável e clica normalmente
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        element.click()
    except (ElementClickInterceptedException, TimeoutException):
        # 3. Fallback: Se ainda houver bloqueio/overlay, força o clique via JavaScript
        print("  -> Overlay/Bloqueio detectado. Executando clique forçado via JS...")
        element = driver.find_element(*locator)
        driver.execute_script("arguments[0].click();", element)


def processar_cnpj(driver, cnpj: str, index: int, total: int):
    print(f"\n======================================================================")
    print(f"[{index}/{total}] Processando CNPJ: {cnpj}")
    
    try:
        print(f"-> Digitando CNPJ {cnpj}...")
        # (Insira aqui sua lógica de digitação do CNPJ no campo)

        # Exemplo de tratamento para múltiplas contas
        # Detecta se há modal de múltiplas contas
        multiplas_contas = False
        try:
            # Substitua o seletor abaixo pelo seletor exato do seu fluxo
            btn_conta_1 = (By.CSS_SELECTOR, "button.andes-button--loud")
            
            # Checa se o botão de seleção de conta está presente
            if driver.find_elements(*btn_conta_1):
                multiplas_contas = True
                print("-> Múltiplas contas detectadas para o CNPJ. Selecionando conta 1...")
                safe_click(driver, btn_conta_1)
        except Exception as e:
            raise Exception(f"Falha ao selecionar conta no modal: {str(e)}")

        # Exemplo de extração de dados
        status = "cliente sem cadastro"
        cust_id = "Não informado"
        email = "Não informado"
        obs = "Múltiplas contas tratadas" if multiplas_contas else "Conta única"

        print(f"-> Status: {status} | Cust ID: {cust_id} | Email: {email}")

        # Registra na planilha online
        sheets_client.atualizar_status_cnpj(
            cnpj=cnpj,
            status=status,
            cust_id=cust_id,
            email=email,
            observacao=obs
        )

    except Exception as e:
        erro_msg = f"ERRO: {str(e)[:100]}"
        print(f"[ERRO NO PROCESSAMENTO DE {cnpj}]: {e}")
        
        # Grava a falha na planilha sem derrubar o script
        sheets_client.atualizar_status_cnpj(
            cnpj=cnpj,
            status="Erro no processamento",
            cust_id="N/A",
            email="N/A",
            observacao=erro_msg
        )


# --- LOOP PRINCIPAL ---
if __name__ == "__main__":
    # Configuração do WebDriver (ajuste com suas opções se necessário)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)

    # Exemplo de lista obtida do seu arquivo ou planilha
    cnpjs_para_processar = [
        "26.896.226/0001-06",
        "07.688.766/0001-50",
        "62.083.255/0001-12",
        "43.510.250/0001-84", # Este falhou no seu log anterior
        "59.086.331/0001-39"
    ]

    total = len(cnpjs_para_processar)
    for i, cnpj in enumerate(cnpjs_para_processar, start=1):
        processar_cnpj(driver, cnpj, i, total)

    driver.quit()