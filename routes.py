from flask import Blueprint, render_template
from db_config import get_connection

routes = Blueprint('routes', __name__)

@routes.route('/')
def index():
    return render_template('index.html')

@routes.route('/ventas')
def ventas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT V.ID_Venta, C.Nombre AS Cliente, V.Monto, V.Fecha, VE.Nombre AS Vendedor
        FROM Venta V
        JOIN Cliente C ON V.ID_Cliente = C.ID_Cliente
        JOIN Vendedor VE ON V.ID_Vendedor = VE.ID_Vendedor
        ORDER BY V.Fecha DESC
    """)
    rows = cur.fetchall()
    columns = [col[0] for col in cur.description]
    data = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return render_template('ventas.html', ventas=data)

# Puedes ir agregando más rutas aquí (clientes, rutas, reportes, etc.)
@routes.route('/clientes')
def clientes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ID_Cliente, Nombre, Municipio, Departamento, Direccion
        FROM Cliente
        ORDER BY ID_Cliente
    """)
    rows = cur.fetchall()
    columns = [col[0].upper() for col in cur.description]
    data = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return render_template('clientes.html', clientes=data)


from flask import Blueprint, render_template
from db_config import get_connection

routes = Blueprint('routes', __name__)

@routes.route('/vendedores')
def mostrar_vendedores():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ID_Vendedor, Nombre, Apellido, Zona_Asignada, Estado FROM Vendedor")
    vendedores = cursor.fetchall()
    conn.close()
    return render_template("vendedores.html", vendedores=vendedores)
