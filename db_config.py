import oracledb as cx_Oracle 

def get_connection():
    dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XE")
    connection = cx_Oracle.connect(user="system", password="27112002", dsn=dsn)
    return connection
