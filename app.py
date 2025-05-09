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
    return render_template('index.html')

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


#cerrar sesion
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for('login'))  # Redirige al index2.html (pantalla de bienvenida)



if __name__ == '__main__':
    app.run(debug=True)