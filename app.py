from flask import Flask, jsonify, render_template
from db_config import get_connection

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ventas')
def ventas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            V.ID_Venta AS ID_Venta,
            C.Nombre AS Cliente,
            V.Monto AS Monto,
            TO_CHAR(V.Fecha, 'YYYY-MM-DD') AS Fecha,
            VE.Nombre AS Vendedor
        FROM Venta V
        JOIN Cliente C ON V.ID_Cliente = C.ID_Cliente
        JOIN Vendedor VE ON V.ID_Vendedor = VE.ID_Vendedor
        ORDER BY V.Fecha DESC
    """)
    rows = cur.fetchall()
    columns = [col[0] for col in cur.description]
    result = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return jsonify(result)

# 🆕 NUEVO ENDPOINT PARA PROBAR DATOS CRUDOS DE LA TABLA VENTA
@app.route('/api/prueba')
def prueba():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM VENTA")
    rows = cur.fetchall()
    columns = [col[0] for col in cur.description]
    result = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return jsonify(result)

@app.route('/api/debug')
def debug():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM VENTA")
    cantidad = cur.fetchone()[0]
    conn.close()
    return f"Total ventas: {cantidad}"




@app.route('/rutas')
def rutas_page():
    return render_template('rutas.html')

@app.route('/vendedores')
def vendedores_page():
    return render_template('vendedores.html')

@app.route('/clientes')
def clientes_page():
    return render_template('clientes.html')

@app.route('/reportes')
def reportes_page():
    return render_template('reportes.html')

if __name__ == '__main__':
    app.run(debug=True)
