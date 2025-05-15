
import oracledb

def get_connection():
    dsn = oracledb.makedsn("localhost", 1521, sid="xe")  # usamos SID, no service_name
    connection = oracledb.connect(
        user="system",
        password="27112002",
        dsn=dsn
    )
    return connection

