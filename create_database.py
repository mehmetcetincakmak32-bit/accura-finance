"""
Veritabanını manuel olarak oluştur
"""
import pyodbc
import os

# Veritabanı oluşturma bağlantı stringi (master veritabanına bağlan)
connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=.;"
    "DATABASE=master;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes"
)

try:
    print("SQL Server'a bağlanıyor...")
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Veritabanının var olup olmadığını kontrol et
    check_db_query = "SELECT name FROM sys.databases WHERE name = 'AccuraFinanceDB'"
    cursor.execute(check_db_query)
    result = cursor.fetchone()
    
    if result:
        print("AccuraFinanceDB veritabanı zaten mevcut.")
    else:
        print("AccuraFinanceDB veritabanını oluşturuyor...")
        create_db_query = "CREATE DATABASE AccuraFinanceDB"
        cursor.execute(create_db_query)
        print("Veritabanı başarıyla oluşturuldu!")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Şimdi yeni veritabanına bağlan ve tabloları oluştur
    print("\nTabloları oluşturuyor...")
    
    new_connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=.;"
    "DATABASE=AccuraFinanceDB;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes"
    )
    
    conn = pyodbc.connect(new_connection_string)
    cursor = conn.cursor()
    
    # SQL dosyasını oku ve çalıştır
    sql_file_path = os.path.join('src', 'database', 'create_tables.sql')
    if os.path.exists(sql_file_path):
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_commands = file.read()
        
        # SQL komutlarını "GO" ile ayır ve tek tek çalıştır
        commands = sql_commands.split('GO')
        for command in commands:
            command = command.strip()
            if command:
                try:
                    cursor.execute(command)
                except Exception as e:
                    print(f"SQL komutu hatası: {e}")
                    print(f"Komut: {command[:100]}...")
        
        conn.commit()
        print("Tablolar başarıyla oluşturuldu!")
    
    # İlk veriyi yükle
    initial_data_path = os.path.join('src', 'database', 'initial_data.sql')
    if os.path.exists(initial_data_path):
        print("İlk veri yükleniyor...")
        with open(initial_data_path, 'r', encoding='utf-8') as file:
            sql_commands = file.read()
        
        # SQL komutlarını "GO" ile ayır ve tek tek çalıştır
        commands = sql_commands.split('GO')
        for command in commands:
            command = command.strip()
            if command:
                try:
                    cursor.execute(command)
                except Exception as e:
                    print(f"Veri yükleme hatası: {e}")
                    print(f"Komut: {command[:100]}...")
        
        conn.commit()
        print("İlk veri başarıyla yüklendi!")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Veritabanı kurulumu tamamlandı!")
    print("Artık uygulamayı çalıştırabilirsiniz.")
    
except Exception as e:
    print(f"❌ Hata: {e}")
    
input("\nDevam etmek için Enter tuşuna basın...")
