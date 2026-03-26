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
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, cantidad REAL, unidad TEXT, 
        precio_unitario REAL, fecha_compra TEXT, kilos_por_bulto REAL, 
        es_herramienta INTEGER DEFAULT 0, notas TEXT, stock_minimo REAL DEFAULT 0)""")
    # 2. Terrenos
    cursor.execute("""CREATE TABLE IF NOT EXISTS terrenos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, variedad TEXT, 
        cantidad_arboles INTEGER, superficie REAL, unidad_medida TEXT)""")
    # 3. Salidas / Usos
    cursor.execute("""CREATE TABLE IF NOT EXISTS salidas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, cantidad REAL, 
        fecha TEXT, lote TEXT, notas TEXT)""")
    # 4. Préstamos
    cursor.execute("""CREATE TABLE IF NOT EXISTS prestamos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_item TEXT, persona TEXT, 
        cantidad REAL, fecha_prestamo TEXT, fecha_devolucion TEXT, 
        estado TEXT DEFAULT 'Pendiente', notas TEXT)""")
    # 5. Bitácora
    cursor.execute("""CREATE TABLE IF NOT EXISTS bitacora (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        actividad TEXT, 
        fecha_creada TEXT, 
        fecha_compromiso TEXT, 
        fecha_completada TEXT, 
        estado TEXT DEFAULT 'Pendiente', 
        notas TEXT)""")

    # --- MIGRACIÓN CRÍTICA PARA EL LOTE ---
    cursor.execute("PRAGMA table_info(bitacora)")
    columnas_bitacora = [col[1] for col in cursor.fetchall()]
    if "lote" not in columnas_bitacora:
        cursor.execute("ALTER TABLE bitacora ADD COLUMN lote TEXT DEFAULT 'Sin Lote'")
        print("Columna 'lote' agregada a bitacora.")

    # Asegurar tabla bitacora_recursos
    cursor.execute("""CREATE TABLE IF NOT EXISTS bitacora_recursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        id_bitacora INTEGER, 
        nombre_item TEXT, 
        cantidad REAL, 
        costo_unitario REAL, 
        tipo_recurso TEXT)""")

    # ... (Otras migraciones de notas que ya tenías)
    conn.commit(); conn.close()

# ACTUALIZA TAMBIÉN ESTA FUNCIÓN para que reciba el lote:
def agregar_evento(act, fc, fcom, n, recs, lote):
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("""INSERT INTO bitacora (actividad, fecha_creada, fecha_compromiso, notas, lote) 
                   VALUES (?,?,?,?,?)""", (act, fc, fcom, n, lote))
    id_b = cursor.lastrowid
    for r in recs: 
        cursor.execute("""INSERT INTO bitacora_recursos (id_bitacora, nombre_item, cantidad, costo_unitario, tipo_recurso) 
                       VALUES (?,?,?,?,?)""", (id_b, r[0], r[1], r[2], r[3]))
    conn.commit(); conn.close()
    
    # 6. Otros nombres (reuso)
    cursor.execute("CREATE TABLE IF NOT EXISTS otros_nombres_recursos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE)")
    # 7. Notas y fotos
    cursor.execute("CREATE TABLE IF NOT EXISTS notas_campo (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT, contenido TEXT, fecha TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS notas_fotos (id INTEGER PRIMARY KEY AUTOINCREMENT, id_nota INTEGER, foto_blob BLOB)")
    # 8. Ventas
    cursor.execute("""CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, lote TEXT, cantidad_cajas REAL, 
        precio_venta_caja REAL, cliente TEXT, total_venta REAL)""")

    # MIGRACIONES DE COLUMNAS (Seguridad)
    tablas_columnas = {
        "inventario": [("es_herramienta", "INTEGER DEFAULT 0"), ("notas", "TEXT"), ("stock_minimo", "REAL DEFAULT 0")],
        "salidas": [("notas", "TEXT")],
        "prestamos": [("notas", "TEXT")],
        "bitacora_recursos": [("costo_unitario", "REAL DEFAULT 0"), ("tipo_recurso", "TEXT DEFAULT 'Insumo'")]
    }
    for tabla, cols in tablas_columnas.items():
        cursor.execute(f"PRAGMA table_info({tabla})")
        existentes = [c[1] for c in cursor.fetchall()]
        for c_nom, c_tipo in cols:
            if c_nom not in existentes:
                cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {c_nom} {c_tipo}")
    conn.commit(); conn.close()

# --- FUNCIONES DE USO ---
def agregar_item(nombre, cantidad, unidad, precio, fecha, kilos, es_herramienta, notas):
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("INSERT INTO inventario (nombre, cantidad, unidad, precio_unitario, fecha_compra, kilos_por_bulto, es_herramienta, notas) VALUES (?,?,?,?,?,?,?,?)", 
                   (nombre, cantidad, unidad, precio, fecha, kilos, es_herramienta, notas))
    conn.commit(); conn.close()

def obtener_compras():
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventario ORDER BY id DESC"); d = cursor.fetchall(); conn.close(); return d

def obtener_existencias():
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("""
        SELECT nombre, unidad, (SUM(total_compra) - IFNULL(SUM(total_salida), 0)) as stock_actual
        FROM (
            SELECT nombre, unidad, SUM(cantidad) as total_compra, 0 as total_salida FROM inventario GROUP BY nombre
            UNION ALL
            SELECT nombre, '' as unidad, 0 as total_compra, SUM(cantidad) as total_salida FROM salidas GROUP BY nombre
        ) GROUP BY nombre
    """)
    d = cursor.fetchall(); conn.close(); return [x for x in d if x[2] != 0]

def obtener_alertas_stock():
    exist = obtener_existencias(); conn = conectar(); cursor = conn.cursor()
    cursor.execute("SELECT nombre, stock_minimo FROM inventario GROUP BY nombre")
    mins = {f[0]: f[1] for f in cursor.fetchall()}; conn.close()
    alertas = []
    for n, u, s in exist:
        m = mins.get(n, 0)
        if m > 0 and s <= m: alertas.append({"nombre": n, "actual": s, "minimo": m, "unidad": u})
    return alertas

def actualizar_stock_minimo(nombre, n_min):
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("UPDATE inventario SET stock_minimo=? WHERE nombre=?", (n_min, nombre))
    conn.commit(); conn.close()

def obtener_costos_promedio():
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("SELECT nombre, SUM(cantidad * precio_unitario) / SUM(cantidad) FROM inventario GROUP BY nombre")
    d = {f[0]: f[1] for f in cursor.fetchall()}; conn.close(); return d

def obtener_valor_total_bodega():
    exist = obtener_existencias(); costos = obtener_costos_promedio()
    return sum(e[2] * costos.get(e[0], 0) for e in exist)

def registrar_salida(nombre, cant, fecha, lote, notas):
    conn = conectar(); cursor = conn.cursor(); cursor.execute("INSERT INTO salidas (nombre, cantidad, fecha, lote, notas) VALUES (?,?,?,?,?)", (nombre, cant, fecha, lote, notas)); conn.commit(); conn.close()

def obtener_salidas():
    conn = conectar(); cursor = conn.cursor(); cursor.execute("SELECT * FROM salidas ORDER BY id DESC"); d = cursor.fetchall(); conn.close(); return d

def registrar_prestamo(nombre, persona, cant, fecha, notas):
    conn = conectar(); cursor = conn.cursor(); cursor.execute("INSERT INTO prestamos (nombre_item, persona, cantidad, fecha_prestamo, notas) VALUES (?,?,?,?,?)", (nombre, persona, cant, fecha, notas)); conn.commit(); conn.close()

def devolver_prestamo(id_p, fecha):
    conn = conectar(); cursor = conn.cursor(); cursor.execute("UPDATE prestamos SET fecha_devolucion=?, estado='Devuelto' WHERE id=?", (fecha, id_p)); conn.commit(); conn.close()

def obtener_prestamos(solo_pendientes=False):
    conn = conectar(); cursor = conn.cursor(); q = "SELECT * FROM prestamos"
    if solo_pendientes: q += " WHERE estado='Pendiente'"
    cursor.execute(q + " ORDER BY id DESC"); d = cursor.fetchall(); conn.close(); return d

def agregar_terreno(n, v, a, s, u):
    conn = conectar(); cursor = conn.cursor(); cursor.execute("INSERT INTO terrenos (nombre, variedad, cantidad_arboles, superficie, unidad_medida) VALUES (?,?,?,?,?)", (n,v,a,s,u)); conn.commit(); conn.close()

def obtener_terrenos():
    conn = conectar(); cursor = conn.cursor(); cursor.execute("SELECT * FROM terrenos"); d = cursor.fetchall(); conn.close(); return d

def agregar_evento(act, fc, fcom, n, recs, lote): # Agregamos 'lote'
    conn = conectar(); cursor = conn.cursor()
    # Asegúrate que tu tabla 'bitacora' tenga la columna 'lote'
    cursor.execute("""INSERT INTO bitacora (actividad, fecha_creada, fecha_compromiso, notas, lote) 
                   VALUES (?,?,?,?,?)""", (act, fc, fcom, n, lote))
    id_b = cursor.lastrowid
    for r in recs: 
        cursor.execute("""INSERT INTO bitacora_recursos (id_bitacora, nombre_item, cantidad, costo_unitario, tipo_recurso) 
                       VALUES (?,?,?,?,?)""", (id_b, r[0], r[1], r[2], r[3]))
    conn.commit(); conn.close()
    
def obtener_eventos(estado=None):
    conn = conectar(); cursor = conn.cursor(); q = "SELECT * FROM bitacora"
    if estado: q += f" WHERE estado='{estado}'"
    cursor.execute(q + " ORDER BY fecha_compromiso ASC"); d = cursor.fetchall(); conn.close(); return d

def completar_evento_db(id_b, f):
    conn = conectar(); cursor = conn.cursor(); cursor.execute("UPDATE bitacora SET estado='Completado', fecha_completada=? WHERE id=?", (f, id_b)); conn.commit(); conn.close()

def obtener_recursos_evento(id_b):
    conn = conectar(); cursor = conn.cursor(); cursor.execute("SELECT nombre_item, cantidad, costo_unitario, tipo_recurso FROM bitacora_recursos WHERE id_bitacora=?", (id_b,)); d = cursor.fetchall(); conn.close(); return d

def guardar_nota_con_fotos(t, c, f, fotos):
    conn = conectar(); cursor = conn.cursor(); cursor.execute("INSERT INTO notas_campo (titulo, contenido, fecha) VALUES (?,?,?)", (t,c,f))
    id_n = cursor.lastrowid
    for ft in fotos: cursor.execute("INSERT INTO notas_fotos (id_nota, foto_blob) VALUES (?,?)", (id_n, ft))
    conn.commit(); conn.close()

def obtener_notas_filtradas(m, a):
    conn = conectar(); cursor = conn.cursor(); cursor.execute("SELECT * FROM notas_campo WHERE strftime('%m', fecha)=? AND strftime('%Y', fecha)=? ORDER BY fecha DESC", (f"{m:02d}", str(a))); d = cursor.fetchall(); conn.close(); return d

def obtener_fotos_de_nota(id_n):
    conn = conectar(); cursor = conn.cursor(); cursor.execute("SELECT foto_blob FROM notas_fotos WHERE id_nota=?", (id_n,)); d = [x[0] for x in cursor.fetchall()]; conn.close(); return d

def registrar_venta(f, l, c, p, cl):
    conn = conectar(); cursor = conn.cursor(); cursor.execute("INSERT INTO ventas (fecha, lote, cantidad_cajas, precio_venta_caja, cliente, total_venta) VALUES (?,?,?,?,?,?)", (f,l,c,p,cl,c*p)); conn.commit(); conn.close()

def calcular_resumen_financiero():
    conn = conectar(); cursor = conn.cursor()
    cursor.execute("SELECT SUM(cantidad * precio_unitario) FROM inventario"); c = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(cantidad * costo_unitario) FROM bitacora_recursos WHERE tipo_recurso != 'Insumo'"); o = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(total_venta) FROM ventas"); v = cursor.fetchone()[0] or 0
    conn.close(); return c, o, v

# (Añade funciones simples de eliminar faltantes según necesites, siguiendo el patrón DELETE FROM tabla WHERE id=?)
def eliminar_compra(id): conn = conectar(); c = conn.cursor(); c.execute("DELETE FROM inventario WHERE id=?", (id,)); conn.commit(); conn.close()
def eliminar_salida(id): conn = conectar(); c = conn.cursor(); c.execute("DELETE FROM salidas WHERE id=?", (id,)); conn.commit(); conn.close()
def eliminar_prestamo(id): conn = conectar(); c = conn.cursor(); c.execute("DELETE FROM prestamos WHERE id=?", (id,)); conn.commit(); conn.close()
def eliminar_nota_campo(id): conn = conectar(); c = conn.cursor(); c.execute("DELETE FROM notas_fotos WHERE id_nota=?", (id,)); c.execute("DELETE FROM notas_campo WHERE id=?", (id,)); conn.commit(); conn.close()
def obtener_nombres_actividades(): conn=conectar(); c=conn.cursor(); c.execute("SELECT DISTINCT actividad FROM bitacora"); d=[x[0] for x in c.fetchall()]; conn.close(); return d
def obtener_nombres_unicos(): conn=conectar(); c=conn.cursor(); c.execute("SELECT DISTINCT nombre FROM inventario"); d=[x[0] for x in c.fetchall()]; conn.close(); return d
def guardar_nuevo_nombre_recurso(n): conn=conectar(); c=conn.cursor(); c.execute("INSERT OR IGNORE INTO otros_nombres_recursos (nombre) VALUES (?)", (n,)); conn.commit(); conn.close()
def obtener_otros_nombres_recursos(): conn=conectar(); c=conn.cursor(); c.execute("SELECT nombre FROM otros_nombres_recursos"); d=[x[0] for x in c.fetchall()]; conn.close(); return d
def obtener_ventas(): conn=conectar(); c=conn.cursor(); c.execute("SELECT * FROM ventas ORDER BY fecha DESC"); d=cursor.fetchall(); conn.close(); return d
def obtener_notas_campo(): conn=conectar(); c=conn.cursor(); c.execute("SELECT * FROM notas_campo ORDER BY fecha DESC"); d=cursor.fetchall(); conn.close(); return d