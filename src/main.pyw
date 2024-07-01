import pyodbc

# Configura la conexión a tu base de datos
server = 'SERVIDOR'
database = 'BASE_DE_DATOS'
username = 'USUARIO'
password = 'CONTRASEÑA'
connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

# Conéctate a la base de datos
conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

# Ejecuta el sp_who2
cursor.execute("EXEC sp_who2")
rows = cursor.fetchall()

# Filtra los procesos de la base de datos especificada
database_name = 'NOMBRE_DE_LA_BASE_DE_DATOS'
process_ids = [row.spid for row in rows if row.dbname == database_name]

# Matar los procesos seleccionados
for spid in process_ids:
    try:
        cursor.execute(f"KILL {spid}")
        conn.commit()
        print(f'Proceso {spid} terminado.')
    except Exception as e:
        print(f'Error al terminar el proceso {spid}: {e}')

# Cerrar la conexión
cursor.close()
conn.close()
