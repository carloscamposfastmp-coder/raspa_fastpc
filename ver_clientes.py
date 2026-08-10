import sqlite3

def listar_clientes():
    conn = sqlite3.connect("clientes_interesse.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT cnpj, razao_social, endereco, status_mercadopago, data_consulta FROM clientes")
    registros = cursor.fetchall()
    
    print("\n" + "="*80)
    print(f"{'CNPJ':<20} | {'RAZÃO SOCIAL':<30} | {'STATUS MP':<10}")
    print("="*80)
    
    if not registros:
        print("Nenhum cliente salvo no banco de dados ainda.")
    else:
        for reg in registros:
            cnpj, razao, endereco, status, data = reg
            print(f"{cnpj:<20} | {razao[:28]:<30} | {status:<10}")
            print(f"   └─ Endereço: {endereco}")
            print("-" * 80)
            
    conn.close()

if __name__ == "__main__":
    listar_clientes()