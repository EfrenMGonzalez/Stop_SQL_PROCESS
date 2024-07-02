import pyodbc
from cryptography.fernet import Fernet
import os
import yaml
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, scrolledtext
import threading

# Configura la conexión a tu base de datos
config = {
    'server': '',
    'username': '',
    'password': '',
    'config_key':''
}

def getDataBases():
    password = descifrar_contrasena(config["password"], config["config_key"])
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config["server"]};UID={config["username"]};PWD={password}'
    conn = pyodbc.connect(conn_str)
    
    cursor = conn.cursor()
    query = "SELECT name FROM sys.databases WHERE name NOT IN ('master', 'model', 'msdb', 'tempdb')"
            

    cursor.execute(query)
    databases = [row.name for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return databases

def probar_conexion(ip, usuario, contrasena):
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={ip};UID={usuario};PWD={contrasena}'
        conn = pyodbc.connect(conn_str)
        conn.close()
        messagebox.showinfo("Información", "Conexión exitosa")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo conectar a la base de datos: {e}")

def guardar_configuracion(ip, usuario, contrasena):
     # Genera una clave única para cada ejecución del programa
    clave = generar_clave()  
    # Cifra la contraseña
    contrasena_cifrada = cifrar_contrasena(contrasena, clave)
    config = {
        'server': ip,
        'username': usuario,
        'password': contrasena_cifrada.decode(),
        'config_key':clave
    }
    with open('configuracion.yaml', 'w') as file:
        yaml.dump(config, file)
    messagebox.showinfo("Información", "Configuración guardada correctamente")
    root.quit()

def generar_clave():
    return Fernet.generate_key()

def cifrar_contrasena(contrasena, clave):# Función para cifrar la contraseña
    fernet = Fernet(clave)
    return fernet.encrypt(contrasena.encode())

def descifrar_contrasena(contrasena_cifrada, clave):# Función para descifrar la contraseña
    fernet = Fernet(clave)
    return fernet.decrypt(contrasena_cifrada.encode()).decode()

def drop_process(db_name):
# Conéctate a la base de datos
    password = descifrar_contrasena(config["password"], config["config_key"])
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config["server"]};UID={config["username"]};PWD={password}'
    conn = pyodbc.connect(conn_str)
    conn.autocommit = True  # Habilitar el autocommit
    cursor = conn.cursor()

    # Ejecuta el sp_who2
    cursor.execute("EXEC sp_who2")
    rows = cursor.fetchall()

    # Filtra los procesos de la base de datos especificada
    
    process_ids = [row.SPID for row in rows if row.DBName == db_name]

    # Matar los procesos seleccionados
    if not process_ids:
        log(f'No se encontro ningun proceso para la base de datos "{db_name}"')
    else:
        for spid in process_ids:
            try:
                kill_cursor = conn.cursor()
                kill_cursor.execute(f"KILL {spid}")
                conn.commit()
                kill_cursor.close()
                log(f'Proceso {spid} terminado.')
            except Exception as e:
                log(f'Error al terminar el proceso {spid}: {e}')

    # Cerrar la conexión
    cursor.close()
    conn.close()

def log(message):
    global log_text
    log_text.config(state=tk.NORMAL)
    log_text.insert(tk.END, message + "\n")
    log_text.config(state=tk.DISABLED)
    log_text.yview(tk.END)

def leer_configuracion():
    global config
    print(config["server"])
    with open('configuracion.yaml', 'r') as file:
        config = yaml.safe_load(file)

def verificaCombo(valor,ruta):
    if(valor==""):
        log(f"No se seleciono ninguna base de datos")
        messagebox.showerror(f"Error 404", f"No se seleciono ninguna base de datos")
    else:
        drop_process(valor)

def cancelar():
    root.quit()

if __name__ == "__main__":
    if not os.path.exists('configuracion.yaml'):
        root = tk.Tk()
        root.geometry('300x350')
        root.title("Configuración del Programa")

        tk.Label(root, text="IP del Servidor:").pack(pady=5)
        ip_entry = tk.Entry(root)
        ip_entry.pack(pady=5)

        tk.Label(root, text="Usuario de BD:").pack(pady=5)
        usuario_entry = tk.Entry(root)
        usuario_entry.pack(pady=5)

        tk.Label(root, text="Contraseña:").pack(pady=5)
        contrasena_entry = tk.Entry(root, show="*")
        contrasena_entry.pack(pady=5)

        tk.Button(root, text="Probar Conexión", command=lambda: probar_conexion(
            ip_entry.get(), usuario_entry.get(), contrasena_entry.get())).pack(pady=5)

        tk.Button(root, text="Guardar", command=lambda: guardar_configuracion(
            ip_entry.get(), usuario_entry.get(), contrasena_entry.get())).pack(pady=20)
        tk.Button(root, text="Cancelar", command=cancelar).pack(pady=5)

        root.mainloop()
    else:
        leer_configuracion()
        root = tk.Tk()
        root.geometry('570x400')
        root.title("Terminar Procesos")
        # Crear área de texto desplazable para el registro
        log_text = scrolledtext.ScrolledText(root, state=tk.DISABLED, height=10)
        log_text.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
       
        # Mostrar información del servidor y espacio libre
        label = tk.Label(root, text=f"Servidor: {config['server']}", anchor="w", justify="left")
        label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        # ComboBox para seleccionar la base de datos
        label_bd = tk.Label(root, text=f"Selecciona una base de datos", anchor="w", justify="left")
        label_bd.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        DBnames = ttk.Combobox(root, values=getDataBases())
        DBnames.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        # Botón para respaldo específico
        btn_respaldo_especifico = tk.Button(root, text="Terminar Proceso", command=lambda: threading.Thread(target=verificaCombo, args=(DBnames.get(), drop_process)).start())
        btn_respaldo_especifico.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # Botón para salir de la aplicación
        btn_salir = tk.Button(root, text="Salir", command=root.quit)
        btn_salir.grid(row=5, column=0, padx=10, pady=10, sticky="w")

        # Ajustar el tamaño y la posición de los widgets usando grid
        root.grid_rowconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        root.grid_rowconfigure(2, weight=1)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)

        # Ejecutar la aplicación
        root.mainloop()
