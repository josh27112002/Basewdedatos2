

import oracledb

def get_connection():
    # Crear el DSN (Data Source Name)
    dsn = oracledb.makedsn("DAVID", 1522, service_name="XE")

    # Establecer conexión como SYS con rol SYSDBA
    connection = oracledb.connect(
        user="sys",
        password="Oracle123",  # contraseña
        dsn=dsn,
        mode=oracledb.SYSDBA  #Importante: para conectarte como SYSDBA
    )
    return connection



