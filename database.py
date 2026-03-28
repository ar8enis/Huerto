import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "huerto.db")

def conectar():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def crear_tablas():
    conn = conectar(); cursor = conn.cursor()
    # 1. Inventario
    cursor.execute("""CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, nombre TEXT, cantidad REAL, unidad TEXT, 
        precio_unitario REAL, fecha_compra TEXT, kilos_por_bulto REAL, es_herramienta INTEGER DEFAULT 0, 
        notas TEXT, stock_minimo REAL DEFAULT 0)""")
    # 2. Terrenos
    cursor.execute("""CREATE TABLE IF NOT EXISTS terrenos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, nombre TEXT, variedad TEXT, 
        cantidad_arboles INTEGER, superficie REAL, unidad_medida TEXT)""")
    # 3. Salidas / Usos
    cursor.execute("""CREATE TABLE IF NOT EXISTS salidas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, nombre TEXT, cantidad REAL, 
        fecha TEXT, lote TEXT, notas TEXT)""")
    # 4. Préstamos
    cursor.execute("""CREATE TABLE IF NOT EXISTS prestamos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, nombre_item TEXT, persona TEXT, 
        cantidad REAL, fecha_prestamo TEXT, fecha_devolucion TEXT, estado TEXT DEFAULT 'Pendiente', notas TEXT)""")
    # 5. Bitácora
    cursor.execute("""CREATE TABLE IF NOT EXISTS bitacora (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, actividad TEXT, fecha_creada TEXT, 
        fecha_compromiso TEXT, fecha_completada TEXT, estado TEXT DEFAULT 'Pendiente', notas TEXT, lote TEXT)""")
    # 6. Recursos de Bitácora
    cursor.execute("""CREATE TABLE IF NOT EXISTS bitacora_recursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, id_bitacora INTEGER, nombre_item TEXT, 
        cantidad REAL, costo_unitario REAL, tipo_recurso TEXT)""")
    # 7. Otros nombres (reuso)
    cursor.execute("CREATE TABLE IF NOT EXISTS otros_nombres_recursos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE)")
    
    # 8. NOTAS Y FOTOS (Aquí estaban las funciones que faltaban)
    cursor.execute("""CREATE TABLE IF NOT EXISTS notas_campo (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, titulo TEXT, contenido TEXT, fecha TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS notas_fotos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, id_nota INTEGER, foto_blob BLOB)""")
    
    # 9. Ventas
    cursor.execute("""CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, fecha TEXT, lote TEXT, cantidad_cajas REAL, 
        precio_venta_caja REAL, cliente TEXT, total_venta REAL)""")

    conn.commit(); conn.close()

# --- FUNCIONES DE NOTAS (LAS QUE DABAN ERROR) ---

def guardar_nota_con_fotos(u_id, titulo, contenido, fecha, lista_fotos_bin):
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("INSERT INTO notas_campo (user_id, titulo, contenido, fecha) VALUES (?,?,?,?)",
                   (u_id, titulo, contenido, fecha))
    id_nota = cursor.lastrowid
    for foto in lista_fotos_bin:
        cursor.execute("INSERT INTO notas_fotos (id_nota, foto_blob) VALUES (?,?)", (id_nota, foto))
    conn.commit(); conn.close()

def obtener_notas_campo(u_id):
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM notas_campo WHERE user_id=? ORDER BY fecha DESC", (u_id,))
    d = cursor.fetchall(); conn.close(); return d

def obtener_notas_filtradas(u_id, mes, anio):
    conn = conectar(); cursor = conn.cursor()
    # strftime('%m', fecha) obtiene el mes de una fecha YYYY-MM-DD
    cursor.execute("""SELECT * FROM notas_campo 
                   WHERE user_id=? AND strftime('%m', fecha) = ? AND strftime('%Y', fecha) = ? 
                   ORDER BY fecha DESC""", (u_id, f"{mes:02d}", str(anio)))
    d = cursor.fetchall(); conn.close(); return d

def obtener_fotos_de_nota(id_nota):
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("SELECT foto_blob FROM notas_fotos WHERE id_nota=?", (id_nota,))
    d = [f[0] for f in cursor.fetchall()]; conn.close(); return d

def eliminar_nota_campo(id_nota):
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("DELETE FROM notas_fotos WHERE id_nota=?", (id_nota,))
    cursor.execute("DELETE FROM notas_campo WHERE id=?", (id_nota,))
    conn.commit(); conn.close()

# --- OTRAS FUNCIONES (MANTENER PARA QUE NADA FALLE) ---

def agregar_item(u_id, nombre, cantidad, unidad, precio, fecha, kilos, es_h, notas):
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("INSERT INTO inventario (user_id, nombre, cantidad, unidad, precio_unitario, fecha_compra, kilos_por_bulto, es_herramienta, notas) VALUES (?,?,?,?,?,?,?,?,?)", 
                   (u_id, nombre, cantidad, unidad, precio, fecha, kilos, es_h, notas))
    conn.commit(); conn.close()

def obtener_existencias(u_id):
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("""
        SELECT nombre, unidad, (SUM(total_compra) - IFNULL(SUM(total_salida), 0)) as stock_actual
        FROM (
            SELECT nombre, unidad, SUM(cantidad) as total_compra, 0 as total_salida FROM inventario WHERE user_id=? GROUP BY nombre
            UNION ALL
            SELECT nombre, '' as unidad, 0 as total_compra, SUM(cantidad) as total_salida FROM salidas WHERE user_id=? GROUP BY nombre
        ) GROUP BY nombre
    """, (u_id, u_id))
    d = cursor.fetchall(); conn.close(); return [x for x in d if x[2] != 0]

def obtener_costos_promedio(u_id):
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("SELECT nombre, SUM(cantidad * precio_unitario) / SUM(cantidad) FROM inventario WHERE user_id=? GROUP BY nombre", (u_id,))
    d = {f[0]: f[1] for f in cursor.fetchall()}; conn.close(); return d

def obtener_valor_total_bodega(u_id):
    exist = obtener_existencias(u_id); costos = obtener_costos_promedio(u_id)
    return sum(e[2] * costos.get(e[0], 0) for e in exist)

def calcular_resumen_financiero(u_id):
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("SELECT SUM(cantidad * precio_unitario) FROM inventario WHERE user_id=?", (u_id,))
    c = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(total_venta) FROM ventas WHERE user_id=?", (u_id,))
    v = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(r.cantidad * r.costo_unitario) FROM bitacora_recursos r JOIN bitacora b ON r.id_bitacora = b.id WHERE b.user_id=? AND r.tipo_recurso != 'Insumo'", (u_id,))
    o = cursor.fetchone()[0] or 0
    conn.close(); return c, o, v

def obtener_terrenos(u_id):
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM terrenos WHERE user_id=?", (u_id,))
    d = cursor.fetchall(); conn.close(); return d

def obtener_eventos(u_id, estado=None):
    conn = conectar(); cursor = conn.cursor()
    q = "SELECT * FROM bitacora WHERE user_id=?"
    if estado: q += f" AND estado='{estado}'"
    cursor.execute(q + " ORDER BY fecha_compromiso ASC", (u_id,)); d = cursor.fetchall(); conn.close(); return d

def obtener_alertas_stock(u_id):
    exist = obtener_existencias(u_id); conn = conectar(); cursor = conn.cursor()
    cursor.execute("SELECT nombre, stock_minimo FROM inventario WHERE user_id=? GROUP BY nombre", (u_id,))
    mins = {f[0]: f[1] for f in cursor.fetchall()}; conn.close()
    alertas = []
    for n, u, s in exist:
        m = mins.get(n, 0)
        if m > 0 and s <= m: alertas.append({"nombre": n, "actual": s, "minimo": m, "unidad": u})
    return alertas

# Funciones auxiliares para Bitácora y otros módulos
def obtener_nombres_actividades(u_id):
    conn=conectar(); c=conn.cursor(); c.execute("SELECT DISTINCT actividad FROM bitacora WHERE user_id=?", (u_id,)); d=[x[0] for x in c.fetchall()]; conn.close(); return d

def obtener_nombres_unicos(u_id):
    conn=conectar(); c=conn.cursor(); c.execute("SELECT DISTINCT nombre FROM inventario WHERE user_id=?", (u_id,)); d=[x[0] for x in c.fetchall()]; conn.close(); return d

def obtener_otros_nombres_recursos():
    conn=conectar(); c=conn.cursor(); c.execute("SELECT nombre FROM otros_nombres_recursos"); d=[x[0] for x in c.fetchall()]; conn.close(); return d

def obtener_recursos_evento(id_b):
    conn = conectar(); cursor = conn.cursor(); cursor.execute("SELECT nombre_item, cantidad, costo_unitario, tipo_recurso FROM bitacora_recursos WHERE id_bitacora=?", (id_b,)); d = cursor.fetchall(); conn.close(); return d

def registrar_salida(u_id, n, q, f, l, nt):
    conn=conectar(); c=conn.cursor(); c.execute("INSERT INTO salidas (user_id, nombre, cantidad, fecha, lote, notas) VALUES (?,?,?,?,?,?)", (u_id,n,q,f,l,nt)); conn.commit(); conn.close()

def completar_evento_db(id_b, f):
    conn=conectar(); c=conn.cursor(); c.execute("UPDATE bitacora SET estado='Completado', fecha_completada=? WHERE id=?", (f, id_b)); conn.commit(); conn.close()
