from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from db_config import get_connection
import smtplib
import random
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'clavesecreta'

@app.route('/')
def index2():
    return render_template('index2.html')

@app.route('/dashboard')
def index():
    conn = get_connection()
    cursor = conn.cursor()

    # Gráfico 1: Vendedores activos/inactivos
    cursor.execute("SELECT Estado, COUNT(*) FROM Vendedor GROUP BY Estado")
    estado_data = {row[0].capitalize(): row[1] for row in cursor.fetchall()}

    # Gráfico 2: Vendedores por zona
    cursor.execute("SELECT Zona_Asignada, COUNT(*) FROM Vendedor GROUP BY Zona_Asignada")
    zona_data = cursor.fetchall()

    # Gráfico 3: Top 5 zonas
    cursor.execute("""
        SELECT Zona_Asignada, COUNT(*) AS Total
        FROM Vendedor
        GROUP BY Zona_Asignada
        ORDER BY Total DESC
        FETCH FIRST 5 ROWS ONLY
    """)
    top5_zonas = cursor.fetchall()

    # Gráfico 4: Línea - Top 5 municipios con más clientes
    cursor.execute("""
        SELECT Municipio, COUNT(*) AS Total
        FROM Cliente
        GROUP BY Municipio
        ORDER BY Total DESC
        FETCH FIRST 5 ROWS ONLY
    """)
    top5_municipios = cursor.fetchall()

    import random
    line_chart_data = {
        "labels": [f"M{m}" for m in range(1, 13)],
        "datasets": []
    }
    for mun, _ in top5_municipios:
        line_chart_data["datasets"].append({
            "label": mun,
            "data": [random.randint(50, 200) for _ in range(12)],
            "borderWidth": 2
        })

    # Ventas - Top 5 vendedores con más ventas
    cursor.execute("""
        SELECT V.Nombre || ' ' || V.Apellido, COUNT(*) AS total
        FROM Venta VE
        JOIN Vendedor V ON VE.ID_Vendedor = V.ID_Vendedor
        GROUP BY V.Nombre, V.Apellido
        ORDER BY total DESC FETCH FIRST 5 ROWS ONLY
    """)
    top_vendedores = cursor.fetchall()

    # Ventas por paquete
    cursor.execute("""
        SELECT PI.Descripcion, COUNT(*) AS total
        FROM Venta VE
        JOIN PaqueteInternet PI ON VE.ID_Paquete = PI.ID_Paquete
        GROUP BY PI.Descripcion
    """)
    ventas_por_paquete = cursor.fetchall()

    # Ventas mensuales (últimos 12 meses)
    cursor.execute("""
        SELECT TO_CHAR(Fecha, 'YYYY-MM') AS mes, COUNT(*) AS total
        FROM Venta
        WHERE Fecha >= ADD_MONTHS(TRUNC(SYSDATE, 'MM'), -11)
        GROUP BY TO_CHAR(Fecha, 'YYYY-MM')
        ORDER BY mes
    """)
    ventas_mensuales = cursor.fetchall()

    # Estado de rutas
    cursor.execute("SELECT Estado, COUNT(*) FROM Ruta GROUP BY Estado")
    rutas_estado_data = {row[0].capitalize(): row[1] for row in cursor.fetchall()}

    # Rutas vs Ventas por Departamento
    cursor.execute("SELECT Departamento, COUNT(*) FROM Ruta GROUP BY Departamento")
    rutas_por_depto = dict(cursor.fetchall())

    cursor.execute("""
        SELECT C.Departamento, COUNT(*) FROM Venta V
        JOIN Cliente C ON V.ID_Cliente = C.ID_Cliente
        GROUP BY C.Departamento
    """)
    ventas_por_depto = dict(cursor.fetchall())

    departamentos = list(set(rutas_por_depto.keys()).union(set(ventas_por_depto.keys())))
    rutas_ventas_depto_data = {
        "departamentos": sorted(departamentos),
        "rutas": [rutas_por_depto.get(dep, 0) for dep in sorted(departamentos)],
        "ventas": [ventas_por_depto.get(dep, 0) for dep in sorted(departamentos)]
    }

    # NUEVO: Rutas vs Clientes por Municipio
    cursor.execute("""
        SELECT
            C.Municipio,
            COUNT(DISTINCT R.ID_Ruta) AS TotalRutas,
            COUNT(DISTINCT C.ID_Cliente) AS TotalClientes
        FROM Cliente C
        LEFT JOIN Ruta R ON C.Municipio = R.Municipio
        GROUP BY C.Municipio
        ORDER BY C.Municipio
        FETCH FIRST 10 ROWS ONLY
    """)
    resultado = cursor.fetchall()
    rutas_clientes_municipio = {
        "municipios": [r[0] for r in resultado],
        "rutas": [r[1] for r in resultado],
        "clientes": [r[2] for r in resultado]
    }

    cursor.close()
    conn.close()

    return render_template("index.html",
                           estado_data=estado_data,
                           zona_data=zona_data,
                           top5_zonas=top5_zonas,
                           line_chart_data=line_chart_data,
                           top_vendedores=top_vendedores,
                           ventas_por_paquete=ventas_por_paquete,
                           ventas_mensuales=ventas_mensuales,
                           rutas_estado_data=rutas_estado_data,
                           rutas_ventas_depto_data=rutas_ventas_depto_data,
                           rutas_clientes_municipio=rutas_clientes_municipio)


#REGISTRO
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        telefono = request.form['telefono']
        nombreusuario = request.form['nombreusuario']
        rol = request.form['rol']
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        codigo = str(random.randint(1000, 9999))

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Insertar usuario como NO verificado
            cursor.execute("SELECT NVL(MAX(ID_Usuario), 0) + 1 FROM UsuarioSistema")
            nuevo_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO UsuarioSistema (
                    ID_Usuario, NombreUsuario, Contraseña, Rol,
                    Nombre, Apellido, Telefono, Correo, Verificado
                ) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, 0)
            """, (nuevo_id, nombreusuario, contraseña, rol, nombre, apellido, telefono, correo))

            # Insertar código en tabla CodigosVerificacion
            cursor.execute("SELECT NVL(MAX(ID), 0) + 1 FROM CodigosVerificacion")
            id_codigo = cursor.fetchone()[0]
            cursor.execute("""
                INSERT INTO CodigosVerificacion (ID, Correo, Codigo)
                VALUES (:1, :2, :3)
            """, (id_codigo, correo, codigo))

            conn.commit()

            # Enviar correo
            msg = MIMEText(f"Tu código de verificación es: {codigo}")
            msg['Subject'] = 'Verificación de cuenta - Ninoshka'
            msg['From'] = 'wcabrerag1@miumg.edu.gt'
            msg['To'] = correo

            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login('wcabrerag1@miumg.edu.gt', 'fdyr mfdr nrhp fcsd')
            server.send_message(msg)
            server.quit()

            flash('Código enviado a tu correo. Verifica tu cuenta.', 'info')
            session['correo_verificacion'] = correo
            return redirect(url_for('verificar'))

        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('registro.html')

#Verficacion de Correo
@app.route('/verificar', methods=['GET', 'POST'])
def verificar():
    if request.method == 'POST':
        codigo_ingresado = request.form['codigo']
        correo = session.get('correo_verificacion')

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Codigo FROM CodigosVerificacion
            WHERE Correo = :1 ORDER BY CreadoEn DESC
        """, (correo,))
        codigo_real = cursor.fetchone()

        if codigo_real and codigo_real[0] == codigo_ingresado:
            cursor.execute("""
                UPDATE UsuarioSistema SET Verificado = 1 WHERE Correo = :1
            """, (correo,))
            conn.commit()
            flash("Cuenta verificada exitosamente. Ahora puedes iniciar sesión.", "success")
            return redirect(url_for('login'))
        else:
            flash("Código incorrecto. Intenta nuevamente.", "danger")

        cursor.close()
        conn.close()

    return render_template('verificar.html')



#LOG IN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID_Usuario, NombreUsuario, Rol
            FROM UsuarioSistema
            WHERE Correo = :1 AND Contraseña = :2
        """, (correo, contraseña))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['usuario_id'] = user[0]
            session['nombre_usuario'] = user[1]
            session['rol'] = user[2]
            flash(" ", "success")
            return redirect(url_for('index'))
        else:
            flash("Correo o contraseña incorrectos.", "danger")

    return render_template('login.html')



#seccion ventas
@app.route('/ventas')
def ventas_page():
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    filtro = request.args.get('buscar', '').strip().lower()
    desde = request.args.get('desde', '')
    hasta = request.args.get('hasta', '')

    conn = get_connection()
    cur = conn.cursor()

    condiciones = []
    valores = {'offset': offset, 'limit': per_page}

    if filtro:
        condiciones.append("""
            (LOWER(CL.Nombre) LIKE :filtro OR LOWER(VE.Nombre) LIKE :filtro)
        """)
        valores['filtro'] = f"%{filtro}%"

    if desde:
        condiciones.append("Fecha >= TO_DATE(:desde, 'YYYY-MM-DD')")
        valores['desde'] = desde

    if hasta:
        condiciones.append("Fecha <= TO_DATE(:hasta, 'YYYY-MM-DD')")
        valores['hasta'] = hasta

    where_clause = "WHERE " + " AND ".join(condiciones) if condiciones else ""

    query = f"""
        SELECT V.ID_Venta, CL.Nombre AS Cliente, VE.Nombre || ' ' || VE.Apellido AS Vendedor,
               PI.Descripcion AS Paquete, V.Monto, TO_CHAR(V.Fecha, 'YYYY-MM-DD')
        FROM Venta V
        JOIN Cliente CL ON V.ID_Cliente = CL.ID_Cliente
        JOIN Vendedor VE ON V.ID_Vendedor = VE.ID_Vendedor
        JOIN PaqueteInternet PI ON V.ID_Paquete = PI.ID_Paquete
        {where_clause}
        ORDER BY V.Fecha DESC
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
    """

    cur.execute(query, valores)
    ventas = cur.fetchall()

    # Conteo total
    valores_count = {k: v for k, v in valores.items() if k not in ['offset', 'limit']}
    cur.execute(f"""
        SELECT COUNT(*)
        FROM Venta V
        JOIN Cliente CL ON V.ID_Cliente = CL.ID_Cliente
        JOIN Vendedor VE ON V.ID_Vendedor = VE.ID_Vendedor
        JOIN PaqueteInternet PI ON V.ID_Paquete = PI.ID_Paquete
        {where_clause}
    """, valores_count)
    total = cur.fetchone()[0]

    cur.close()
    conn.close()

    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    return render_template('ventas.html',
                           ventas=ventas,
                           page=page,
                           total_pages=total_pages,
                           filtro=filtro,
                           desde=desde,
                           hasta=hasta,
                           total=total)


#Seccion Rutas
@app.route('/rutas')
def rutas_page():
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    filtro = request.args.get('buscar', '').strip().lower()
    condiciones = []
    valores = {'offset': offset, 'limit': per_page}

    if filtro:
        palabras = filtro.split()
        for i, palabra in enumerate(palabras):
            clave = f'p{i}'
            condiciones.append(
                f"(LOWER(R.Zona) LIKE :{clave} OR LOWER(R.Municipio) LIKE :{clave} OR LOWER(V.Nombre) LIKE :{clave} OR LOWER(V.Apellido) LIKE :{clave})"
            )
            valores[clave] = f"%{palabra}%"

    where_sql = " AND ".join(condiciones)
    if where_sql:
        where_sql = "WHERE " + where_sql

    conn = get_connection()
    cur = conn.cursor()

    # Consulta principal con JOIN a VENDEDOR
    cur.execute(f"""
        SELECT R.ID_Ruta, R.Zona, R.Municipio, R.Departamento,
               V.Nombre || ' ' || V.Apellido AS Vendedor_Asignado,
               R.Estado, TO_CHAR(R.Fecha_Creacion, 'YYYY-MM-DD')
        FROM Ruta R
        JOIN Vendedor V ON R.ID_Vendedor = V.ID_Vendedor
        {where_sql}
        ORDER BY R.ID_Ruta
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
    """, valores)
    rutas = cur.fetchall()

    # Conteo total de resultados
    filtros_solo = {k: v for k, v in valores.items() if k not in ['offset', 'limit']}
    cur.execute(f"""
        SELECT COUNT(*) FROM Ruta R
        JOIN Vendedor V ON R.ID_Vendedor = V.ID_Vendedor
        {where_sql}
    """, filtros_solo)
    total = cur.fetchone()[0]

    cur.close()
    conn.close()

    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    return render_template(
        'rutas.html',
        rutas=rutas,
        page=page,
        total_pages=total_pages,
        filtro=filtro,
        total=total
    )



#seccion de Vendedores
@app.route('/vendedores')
def vendedores_page():
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    filtro = request.args.get('buscar', '').strip().lower()
    estado = request.args.get('estado', '').strip().lower()

    conn = get_connection()
    cur = conn.cursor()

    condiciones = []
    valores = {'offset': offset, 'limit': per_page}

    if filtro:
        palabras = filtro.split()
        for i, palabra in enumerate(palabras):
            clave = f'p{i}'
            condiciones.append(
                f"(LOWER(NOMBRE) LIKE :{clave} OR LOWER(APELLIDO) LIKE :{clave} OR LOWER(ZONA_ASIGNADA) LIKE :{clave})"
            )
            valores[clave] = f"%{palabra}%"

    if estado in ['activo', 'inactivo']:
        condiciones.append("LOWER(ESTADO) = :estado")
        valores['ESTADO'] = estado

    where_sql = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    query = f"""
        SELECT ID_VENDEDOR, NOMBRE, APELLIDO, ZONA_ASIGNADA, ESTADO
        FROM Vendedor
        {where_sql}
        ORDER BY ID_VENDEDOR
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
    """

    cur.execute(query, valores)
    vendedores = cur.fetchall()

    # Conteo total
    filtros_solo = {k: v for k, v in valores.items() if k not in ['offset', 'limit']}
    cur2 = conn.cursor()
    cur2.execute(f"SELECT COUNT(*) FROM Vendedor {where_sql}", filtros_solo)
    total = cur2.fetchone()[0]

    cur.close()
    cur2.close()
    conn.close()

    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    return render_template(
        'vendedores.html',
        vendedores=vendedores,
        page=page,
        total_pages=total_pages,
        filtro=filtro,
        estado=estado,
        total=total
    )


@app.route('/clientes')
def clientes_page():
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    filtro = request.args.get('buscar', '').strip().lower()

    conn = get_connection()
    cur = conn.cursor()

    condiciones = []
    valores = {'offset': offset, 'limit': per_page}

    if filtro:
        palabras = filtro.split()
        for i, palabra in enumerate(palabras):
            clave = f'p{i}'
            condiciones.append(
                f"(LOWER(Nombre) LIKE :{clave} OR LOWER(Municipio) LIKE :{clave} OR LOWER(Departamento) LIKE :{clave})"
            )
            valores[clave] = f"%{palabra}%"

    where_sql = " AND ".join(condiciones)
    if where_sql:
        where_sql = "WHERE " + where_sql

    cur.execute(f"""
        SELECT ID_Cliente, Nombre, Direccion, Municipio, Departamento
        FROM Cliente
        {where_sql}
        ORDER BY ID_Cliente
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
    """, valores)
    clientes = cur.fetchall()

    filtros_solo = {k: v for k, v in valores.items() if k not in ['offset', 'limit']}
    cur2 = conn.cursor()
    cur2.execute(f"""
        SELECT COUNT(*) FROM Cliente
        {where_sql}
    """, filtros_solo)
    total = cur2.fetchone()[0]
    cur2.close()
    conn.close()

    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    return render_template(
        'clientes.html',
        clientes=clientes,
        page=page,
        total_pages=total_pages,
        filtro=filtro,
        total=total
    )


@app.route('/reportes')
def reportes_page():
    return render_template('reportes.html')


#cerrar sesion
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for('login'))  # Redirige al index2.html (pantalla de bienvenida)

@app.route('/paquetes')
def paquetes_page():
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    filtro = request.args.get('buscar', '').strip().lower()

    conn = get_connection()
    cur = conn.cursor()

    condiciones = []
    valores = {'offset': offset, 'limit': per_page}

    if filtro:
        palabras = filtro.split()
        for i, palabra in enumerate(palabras):
            clave = f'p{i}'
            condiciones.append(
                f"(LOWER(Nombre) LIKE :{clave} OR LOWER(Descripcion) LIKE :{clave})"
            )
            valores[clave] = f"%{palabra}%"

    where_sql = " AND ".join(condiciones)
    if where_sql:
        where_sql = "WHERE " + where_sql

    cur.execute(f"""
        SELECT ID_Paquete, Nombre, Velocidad_MBPS, Precio, Descripcion
        FROM PaqueteInternet
        {where_sql}
        ORDER BY ID_Paquete
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
    """, valores)
    paquetes = cur.fetchall()

    filtros_solo = {k: v for k, v in valores.items() if k not in ['offset', 'limit']}
    cur2 = conn.cursor()
    cur2.execute(f"""
        SELECT COUNT(*) FROM PaqueteInternet
        {where_sql}
    """, filtros_solo)
    total = cur2.fetchone()[0]
    cur2.close()
    conn.close()

    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    return render_template(
        'paquetes.html',
        paquetes=paquetes,
        page=page,
        total_pages=total_pages,
        filtro=filtro,
        total=total
    )

# Seccion tiempo muerto
@app.route('/tiempomuerto')
def tiempo_muerto_page():
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page

    filtro = request.args.get('buscar', '').strip().lower()
    condiciones = []
    valores = {'offset': offset, 'limit': per_page}

    if filtro:
        palabras = filtro.split()
        for i, palabra in enumerate(palabras):
            clave = f'p{i}'
            condiciones.append(
                f"(LOWER(T.Zona) LIKE :{clave} OR LOWER(T.Municipio) LIKE :{clave} OR LOWER(V.Nombre) LIKE :{clave} OR LOWER(V.Apellido) LIKE :{clave})"
            )
            valores[clave] = f"%{palabra}%"

    where_sql = " AND ".join(condiciones)
    if where_sql:
        where_sql = "WHERE " + where_sql

    conn = get_connection()
    cur = conn.cursor()

    # Consulta principal con JOIN a VENDEDOR
    cur.execute(f"""
        SELECT T.ID_TiempoMuerto, T.Zona, T.Municipio, T.Departamento,
               V.Nombre || ' ' || V.Apellido AS Vendedor_Asignado,
               T.Estado, T.Descripcion, TO_CHAR(T.Fecha, 'YYYY-MM-DD'), T.Duracion_Horas
        FROM TiempoMuerto T
        JOIN Vendedor V ON T.ID_Vendedor = V.ID_Vendedor
        {where_sql}
        ORDER BY T.ID_TiempoMuerto
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
    """, valores)
    tiempos = cur.fetchall()

    # Conteo total
    filtros_solo = {k: v for k, v in valores.items() if k not in ['offset', 'limit']}
    cur.execute(f"""
        SELECT COUNT(*) FROM TiempoMuerto T
        JOIN Vendedor V ON T.ID_Vendedor = V.ID_Vendedor
        {where_sql}
    """, filtros_solo)
    total = cur.fetchone()[0]

    cur.close()
    conn.close()

    total_pages = (total + per_page - 1) // per_page if total > 0 else 1

    return render_template(
        'tiempomuerto.html',
        tiempos=tiempos,
        page=page,
        total_pages=total_pages,
        filtro=filtro,
        total=total
    )



if __name__ == '__main__':
    app.run(debug=True)