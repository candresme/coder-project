# src/db.py
import mysql.connector
from mysql.connector import Error

def connect_to_mariadb():
    try:
        # Coloca la información de tu base de datos MariaDB
        connection = mysql.connector.connect(
            host='localhost',
            database='task-app',
            user='root',
            password='root123'
        )
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"Conectado a la base de datos MariaDB Server version {db_info}")
            return connection

    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def close_connection(connection):
    if connection.is_connected():
        connection.close()
        print("Conexión cerrada")
