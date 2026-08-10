import os
import sys
import re
import sqlite3
import time
import requests
from bs4 import BeautifulSoup
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
    print("[ERRO] Execute: python -m pip install selenium webdriver-manager requests beautifulsoup4\n")
    sys.exit(1)

# URLs do Processo
URL_MP = "https://www.mercadopago.com.br/point-fast/account-consult"
SPREADSHEET_ORIGEM_CSV = "https://docs.google.com/spreadsheets/d/1Sk9n1TO-tv8GqTVegme428BeYR7g25JeBltBOXpdGqE/export?format=csv&gid=0"

# Insira o URL do seu Google Apps Script Webhook se configurado
WEBHOOK_URL = ""


def init_db():
    """Cria a tabela e executa migração automática adicionando colunas faltantes no SQLite."""
    conn = sqlite3.connect("clientes_interesse.db")
    cursor = conn.cursor()
    
    # Cria a tabela caso não exista
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cnpj TEXT,
            razao_social TEXT,
            cust_id TEXT,
            email_mp TEXT,
            status_mercadopago TEXT,
            segmento TEXT,
            tpv_mes_atual TEXT,
            tpv_mes_passado TEXT,
            tpv_2m_atras TEXT,
            tpv_3m_atras TEXT,
            pnf TEXT,
            consultor TEXT,
            regime TEXT,
            seguimento TEXT,
            produtos TEXT,
            data_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Migração: Verifica colunas existentes e adiciona as novas se o banco for antigo
    cursor.execute("PRAGMA table_info(clientes)")
    colunas_existentes = [col[1] for col in cursor.fetchall()]
    
    colunas_necessarias = [
        ("cust_id", "TEXT"), ("email_mp", "TEXT"), ("segmento", "TEXT"),
        ("tpv_mes_atual", "TEXT"), ("tpv_mes_passado", "TEXT"),
        ("tpv_2m_atras", "TEXT"), ("tpv_3m_atras", "TEXT"),
        ("pnf", "TEXT"), ("consultor", "TEXT"), ("regime", "TEXT"),
        ("seguimento", "TEXT"), ("produtos", "TEXT")
    ]
    
    for nome_coluna, tipo_coluna in colunas_necessarias:
        if nome_coluna not in colunas_existentes:
            try:
                cursor.execute(f"ALTER TABLE clientes ADD COLUMN {nome_coluna} {tipo_coluna}")
                print(f"[BD MIGRAÇÃO] Coluna '{nome_coluna}' adicionada com sucesso ao banco.")
            except Exception as e:
                pass
                
    conn.commit()
    conn.close()


def save_cliente_local(dados_completos):
    """Salva os registros completos no banco SQLite local."""
    conn = sqlite3.connect("clientes_interesse.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO clientes (
                cnpj, razao_social, cust_id, email_mp, status_mercadopago,
                segmento, tpv_mes_atual, tpv_mes_passado, tpv_2m_atras,
                tpv_3m_atras, pnf, consultor, regime, seguimento, produtos
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dados_completos.get("cnpj"),
            dados_completos.get("razao_social"),
            dados_completos.get("cust_id"),
            dados_completos.get("email_mp"),
            dados_completos.get("status_mp"),
            dados_completos.get("segmento"),
            dados_completos.get("tpv_mes_atual"),
            dados_completos.get("tpv_mes_passado"),
            dados_completos.get("tpv_2m_atras"),
            dados_completos.get("tpv_3m_atras"),
            dados_completos.get("pnf"),
            dados_completos.get("consultor"),
            dados_completos.get("regime"),
            dados_completos.get("seguimento"),
            dados_completos.get("produtos")
        ))
        conn.commit()
        print(f"[BD LOCAL] ✓ Cliente registrado: {dados_completos.get('cnpj')} | {dados_completos.get('razao_social')}")
    except Exception as e:
        print(f"[BD LOCAL] Erro ao salvar {dados_completos.get('cnpj')}: {e}")
    finally:
        conn.close()


def enviar_para_planilha_topo(payload):
    """Envia o cliente e todas as métricas extraídas para a planilha de destino via Webhook."""
    if not WEBHOOK_URL.strip():
        print("[INFO] Webhook do Google Sheets não configurado. Salvo apenas no banco local.")
        return

    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"[GOOGLE SHEETS] ★ Registro adicionado ao TOPO da planilha! ★")
        else:
            print(f"[GOOGLE SHEETS] Falha no envio: Status {resp.status_code}")
    except Exception as e:
        print(f"[GOOGLE SHEETS] Erro no Webhook: {e}")


def obter_cnpjs_planilha():
    """Lê os CNPJs da planilha de origem."""
    print("Lendo CNPJs da planilha de origem...")
    try:
        resp = requests.get(SPREADSHEET_ORIGEM_CSV, timeout=15)
        if resp.status_code == 200:
            cnpjs = list(set(re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', resp.text)))
            print(f"-> Encontrados {len(cnpjs)} CNPJs para consultar.")
            return cnpjs
    except Exception as e:
        print(f"[ERRO] Falha ao ler planilha de origem: {e}")
    return []


def iniciar_navegador():
    """Inicializa o navegador Chrome com o perfil persistente."""
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
    return driver


def extrair_metricas_conta(driver, cnpj_padrao):
    """Extrai todas as informações e TPVs da página interna do cliente."""
    time.sleep(3)
    source = driver.page_source
    soup = BeautifulSoup(source, 'html.parser')
    texto_pagina = soup.get_text(separator="\n")

    # 1. Verifica se é cliente novo
    status_mp = "cliente sem cadastro"
    try:
        elem_sim = soup.find("span", {"data-testid": "meta-detail-value"})
        if elem_sim and elem_sim.text.strip().lower() == "sim":
            status_mp = "cliente novo SIM"
    except Exception:
        pass

    # Função auxiliar para extrair texto por expressão regular
    def buscar_regex(padrao, texto, grupo=1, default="Não informado"):
        match = re.search(padrao, texto, re.IGNORECASE)
        return match.group(grupo).strip() if match else default

    # 2. Extração de campos cadastrais básicos
    cust_id = buscar_regex(r'Cust ID\s*(\d+)', texto_pagina)
    email_mp = buscar_regex(r'E-mail\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', texto_pagina)
    segmento = buscar_regex(r'Segmento em que atua\s*(.*?)\n', texto_pagina)
    pnf = buscar_regex(r'PNF\s*(Sim|Não)', texto_pagina)
    consultor = buscar_regex(r'Consultor designado\s*(.*?)\n', texto_pagina)
    regime = buscar_regex(r'Regime tributário\s*(.*?)\n', texto_pagina)
    seguimento = buscar_regex(r'Seguimento\s*(.*?)\n', texto_pagina)

    # Razão Social exibida na tela
    razao_social = buscar_regex(r'^(.*?)\nConta do Mercado Pago', texto_pagina)

    # 3. Extração de TPVs
    def extrair_bloco_tpv(nome_bloco):
        try:
            if nome_bloco in texto_pagina:
                trecho = texto_pagina.split(nome_bloco)[1].split("TPV")[0]
                valores = re.findall(r'R\$\s*[\d.,]+', trecho)
                if valores:
                    return " | ".join(valores)
        except Exception:
            pass
        return "R$ 0,00"

    tpv_atual = extrair_bloco_tpv("TPV Mês atual")
    tpv_passado = extrair_bloco_tpv("TPV Mês passado")
    tpv_2m = extrair_bloco_tpv("TPV 2 meses atrás")
    tpv_3m = extrair_bloco_tpv("TPV 3 meses atrás")

    # 4. Produtos cadastrados (Point / Maquininhas)
    produtos_encontrados = re.findall(r'Point\s+[^\n]+|A910-\d+', texto_pagina)
    produtos_str = " / ".join(list(set(produtos_encontrados))) if produtos_encontrados else "Nenhum produto"

    return {
        "cnpj": cnpj_padrao,
        "razao_social": razao_social,
        "cust_id": cust_id,
        "email_mp": email_mp,
        "status_mp": status_mp,
        "segmento": segmento,
        "tpv_mes_atual": tpv_atual,
        "tpv_mes_passado": tpv_passado,
        "tpv_2m_atras": tpv_2m,
        "tpv_3m_atras": tpv_3m,
        "pnf": pnf,
        "consultor": consultor,
        "regime": regime,
        "seguimento": seguimento,
        "produtos": produtos_str
    }


def realizar_busca_cnpj(driver, wait, cnpj):
    """Digita o CNPJ no campo e clica no botão de confirmação inicial."""
    driver.get(URL_MP)
    input_cnpj = wait.until(EC.element_to_be_clickable((By.ID, "account")))
    input_cnpj.click()
    input_cnpj.send_keys(Keys.CONTROL + "a")
    input_cnpj.send_keys(Keys.BACKSPACE)
    
    print(f"-> Digitando CNPJ {cnpj}...")
    input_cnpj.send_keys(cnpj)
    time.sleep(1)

    btn_confirmar = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(., 'Confirmar')] | //button[@id='_r_4_']")
    ))
    btn_confirmar.click()
    time.sleep(3)


def processar_cnpj(driver, wait, cnpj):
    """Gerencia a consulta de um CNPJ, tratando casos de conta única ou múltiplas contas no modal."""
    realizar_busca_cnpj(driver, wait, cnpj)

    # Verifica se abriu o modal de múltiplas contas
    radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'], label input, div[role='radiogroup'] input")
    
    if radios and len(radios) > 0:
        total_contas = len(radios)
        print(f"-> Múltiplas contas detectadas para o CNPJ ({total_contas} contas).")

        for index in range(total_contas):
            if index > 0:
                print(f"\n[Reconsultando CNPJ para selecionar a conta {index + 1}/{total_contas}]")
                realizar_busca_cnpj(driver, wait, cnpj)

            # Recarrega a lista de botões radio
            opcoes = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "input[type='radio'], label input, div[role='radiogroup'] input")
            ))
            
            print(f"-> Selecionando conta {index + 1} de {total_contas}...")
            driver.execute_script("arguments[0].click();", opcoes[index])
            time.sleep(1)

            # Clica no botão Confirmar do Modal
            btn_confirmar_modal = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Confirmar')]")
            ))
            btn_confirmar_modal.click()

            # Extrai e grava os dados da conta selecionada
            dados = extrair_metricas_conta(driver, cnpj)
            print(f"   Status: {dados['status_mp']} | Cust ID: {dados['cust_id']} | Email: {dados['email_mp']}")
            
            save_cliente_local(dados)
            enviar_para_planilha_topo(dados)
            time.sleep(2)

    else:
        # Caso de conta única
        print("-> Conta única localizada.")
        dados = extrair_metricas_conta(driver, cnpj)
        print(f"   Status: {dados['status_mp']} | Cust ID: {dados['cust_id']} | Email: {dados['email_mp']}")
        
        save_cliente_local(dados)
        enviar_para_planilha_topo(dados)


def main():
    init_db()
    cnpjs = obter_cnpjs_planilha()
    
    if not cnpjs:
        print("Nenhum CNPJ localizado na planilha.")
        return
        
    driver = iniciar_navegador()
    wait = WebDriverWait(driver, 15)
    
    print(f"\nIniciando varredura de {len(cnpjs)} CNPJs no Mercado Pago...\n")
    
    for i, cnpj in enumerate(cnpjs, 1):
        print("="*70)
        print(f"[{i}/{len(cnpjs)}] Processando CNPJ: {cnpj}")
        try:
            processar_cnpj(driver, wait, cnpj)
        except Exception as e:
            print(f"[ERRO NO PROCESSAMENTO DE {cnpj}]: {e}")
            
        time.sleep(2)


if __name__ == "__main__":
    main()