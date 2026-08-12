import gspread
from oauth2client.service_account import ServiceAccountCredentials

class GoogleSheetsHandler:
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        """
        Inicializa a conexão com a API do Google Sheets.
        :param credentials_file: Caminho para o arquivo JSON de credenciais da Service Account.
        :param spreadsheet_id: ID da planilha do Google.
        """
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        self.spreadsheet_id = spreadsheet_id
        self.credentials_file = credentials_file
        self.sheet = None
        self._connect()

    def _connect(self):
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_file, self.scope
            )
            client = gspread.authorize(creds)
            self.sheet = client.open_by_key(self.spreadsheet_id).sheet1
            print("[INFO] Conexão com Google Sheets estabelecida com sucesso!")
        except Exception as e:
            print(f"[ERRO] Falha ao conectar ao Google Sheets: {e}")
            self.sheet = None

    def atualizar_status_cnpj(self, cnpj: str, status: str, cust_id: str, email: str, observacao: str = ""):
        """
        Localiza a linha do CNPJ e atualiza os campos de retorno.
        """
        if not self.sheet:
            print("[AVISO] Google Sheets não configurado. Salvando apenas localmente.")
            return

        try:
            # Busca a célula contendo o CNPJ na planilha
            cell = self.sheet.find(cnpj)
            if cell:
                row = cell.row
                # Assume a estrutura de colunas:
                # Coluna A: CNPJ | Coluna B: Status | Coluna C: Cust ID | Coluna D: Email | Coluna E: Observação
                self.sheet.update(f"B{row}:E{row}", [[status, cust_id, email, observacao]])
                print(f"[GOOGLE SHEETS] ✓ Linha {row} atualizada para o CNPJ {cnpj}")
            else:
                print(f"[GOOGLE SHEETS] CNPJ {cnpj} não encontrado na planilha. Adicionando nova linha...")
                self.sheet.append_row([cnpj, status, cust_id, email, observacao])
        except Exception as e:
            print(f"[ERRO] Erro ao atualizar linha no Google Sheets: {e}")