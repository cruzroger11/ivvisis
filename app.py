import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from models import (
    db, Usuario, Cliente, Proveedor, Producto, 
    Categoria, UnidadMedida, Bodega, Empleado, 
    Compra, DetalleCompra, Venta, DetalleVenta, 
    Kardex, InventarioService
)
import datetime
import io
from sqlalchemy import func

from routes.auth import auth_bp
from routes.auth_utils import login_required, role_required, get_current_user

app = Flask(__name__)
app.secret_key = 'ivvi_secret_key_pro'

# Configuración base de datos SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    # Semilla inicial: Administrador
    if not Usuario.query.filter_by(rol='Administrador').first():
        admin = Usuario(
            nombre="Administrador IVVI", 
            telefono="0999999999", 
            email="admin@ivvi.com", 
            direccion="Oficinas IVVI",
            rol="Administrador", 
            password="admin123"
        )
        db.session.add(admin)
        db.session.commit()

app.register_blueprint(auth_bp)

@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())

@app.route('/')
@login_required
def index():
    # ── KPIs BÁSICOS ────────────────────────────────────────────────
    total_productos = Producto.query.count()
    total_clientes = Cliente.query.count()
    
    hoy = datetime.datetime.now()
    inicio_mes = datetime.datetime(hoy.year, hoy.month, 1)
    
    ventas_mes = db.session.query(func.sum(Venta.total)).filter(Venta.fecha >= inicio_mes).scalar() or 0.0
    compras_mes = db.session.query(func.sum(Compra.total)).filter(Compra.fecha >= inicio_mes).scalar() or 0.0
    
    # ── VALOR DEL INVENTARIO (Estimado) ──────────────────────────────
    # Valor = Stock * Costo (Usamos costo de la última compra o 0)
    valor_inventario = 0.0
    for p in Producto.query.all():
        # Intentar obtener el último costo de compra
        ultimo_detalle = DetalleCompra.query.filter_by(producto_id=p.id).order_by(DetalleCompra.id.desc()).first()
        costo = ultimo_detalle.costo_unitario if ultimo_detalle else 0.0
        valor_inventario += (p.stock_actual * costo)

    # ── DATOS PARA GRÁFICOS (Últimos 15 días) ────────────────────────
    labels_dias = []
    data_ventas = []
    data_compras = []
    
    for i in range(14, -1, -1):
        fecha_d = hoy - datetime.timedelta(days=i)
        fecha_str = fecha_d.strftime('%d %b')
        labels_dias.append(fecha_str)
        
        # Suma ventas del día
        v_dia = db.session.query(func.sum(Venta.total)).filter(
            func.date(Venta.fecha) == fecha_d.date(),
            Venta.estado != 'Anulada'
        ).scalar() or 0.0
        data_ventas.append(v_dia)
        
        # Suma compras del día
        c_dia = db.session.query(func.sum(Compra.total)).filter(
            func.date(Compra.fecha) == fecha_d.date(),
            Compra.estado != 'Anulada'
        ).scalar() or 0.0
        data_compras.append(c_dia)

    # ── DISTRIBUCIÓN DE STOCK (Doughnut Chart) ──────────────────────
    # Materia Prima específica
    p_premium = Producto.query.filter_by(sku='ACE-PRE-BULK').first()
    p_estandar = Producto.query.filter_by(sku='ACE-EST-BULK').first()
    
    stock_premium = p_premium.stock_actual if p_premium else 0
    stock_estandar = p_estandar.stock_actual if p_estandar else 0
    
    # Producto Terminado (Envasados)
    pt_count = db.session.query(func.sum(Producto.stock_actual)).join(Categoria).filter(Categoria.nombre == 'Aceite Envasado').scalar() or 0

    productos_bajo_stock = Producto.query.filter(Producto.stock_actual <= Producto.stock_minimo).all()
    ultimas_ventas = Venta.query.order_by(Venta.id.desc()).limit(5).all()
    
    return render_template('index.html', 
                           tp=total_productos, tc=total_clientes,
                           vm=ventas_mes, cm=compras_mes,
                           valor_inv=valor_inventario,
                           labels_grafico=labels_dias,
                           ventas_grafico=data_ventas,
                           compras_grafico=data_compras,
                           stock_premium=stock_premium,
                           stock_estandar=stock_estandar,
                           stock_pt=pt_count,
                           bajo_stock=productos_bajo_stock,
                           ventas=ultimas_ventas,
                           now=hoy)

# --- MAESTROS (CRUD) ---

@app.route('/productos', methods=['GET'])
@login_required
def productos():
    prods = Producto.query.all()
    cats = Categoria.query.all()
    return render_template('productos.html', items=prods, categorias=cats)

@app.route('/productos/gestion', methods=['GET', 'POST'])
@login_required
def gestion_producto():
    id_prod = request.args.get('id')
    tipo = request.args.get('tipo', 'venta') # Puede ser 'venta' o 'planta'
    modo_edicion = None
    
    if id_prod:
        modo_edicion = Producto.query.get(id_prod)
        if modo_edicion.categoria and modo_edicion.categoria.nombre == 'Producto Terminado':
            tipo = 'venta'
        else:
            tipo = 'planta'
            
    if request.method == 'POST':
        # Guardar / Editar desde el nuevo módulo de formulario
        id_post = request.form.get('id')
        sku, nombre, desc = request.form['sku'], request.form['nombre'], request.form['descripcion']
        cat_id, uni_id = int(request.form['categoria_id']), int(request.form['unidad_id'])
        precio = float(request.form.get('precio', 0.0))
        stock_min = int(request.form['stock_minimo'])
        
        if id_post:
            p = Producto.query.get(id_post)
            p.sku, p.nombre, p.descripcion = sku, nombre, desc
            p.categoria_id, p.unidad_id, p.precio_venta = cat_id, uni_id, precio
            p.stock_minimo = stock_min
            flash('Referencia de material actualizada', 'success')
        else:
            p = Producto(sku=sku, nombre=nombre, descripcion=desc, categoria_id=cat_id, unidad_id=uni_id, precio_venta=precio, stock_minimo=stock_min)
            db.session.add(p)
            flash('Nuevo Material/Producto añadido al Maestro', 'success')
            
        db.session.commit()
        return redirect(url_for('productos'))
        
    cats = Categoria.query.all()
    unis = UnidadMedida.query.all()
    return render_template('producto_form.html', p=modo_edicion, categorias=cats, unidades=unis, tipo=tipo)

# Rutas Auxiliares (Categorías, Unidades, Bodegas, Empleados)
@app.route('/categorias', methods=['GET', 'POST'])
@login_required
@role_required('Administrador')
def categorias():
    if request.method == 'POST':
        cid = request.form.get('id')
        nombre, desc = request.form['nombre'], request.form['descripcion']
        if cid:
            c = Categoria.query.get(cid)
            c.nombre, c.descripcion = nombre, desc
            flash('Categoría actualizada', 'success')
        else:
            c = Categoria(nombre=nombre, descripcion=desc)
            db.session.add(c)
            flash('Categoría creada', 'success')
        db.session.commit()
        return redirect(url_for('categorias'))
    return render_template('maestros/categorias.html', items=Categoria.query.all())

@app.route('/unidades', methods=['GET', 'POST'])
@login_required
@role_required('Administrador')
def unidades():
    if request.method == 'POST':
        uid = request.form.get('id')
        nombre, abr = request.form['nombre'], request.form['abreviatura']
        if uid:
            u = UnidadMedida.query.get(uid)
            u.nombre, u.abreviatura = nombre, abr
            flash('Unidad actualizada', 'success')
        else:
            u = UnidadMedida(nombre=nombre, abreviatura=abr)
            db.session.add(u)
            flash('Unidad de medida creada', 'success')
        db.session.commit()
        return redirect(url_for('unidades'))
    return render_template('maestros/unidades.html', items=UnidadMedida.query.all())

@app.route('/bodegas', methods=['GET', 'POST'])
@login_required
@role_required('Administrador')
def bodegas():
    if request.method == 'POST':
        bid = request.form.get('id')
        nombre, ubi = request.form['nombre'], request.form['ubicacion']
        if bid:
            b = Bodega.query.get(bid)
            b.nombre, b.ubicacion = nombre, ubi
            flash('Bodega actualizada', 'success')
        else:
            b = Bodega(nombre=nombre, ubicacion=ubi)
            db.session.add(b)
            flash('Bodega creada', 'success')
        db.session.commit()
        return redirect(url_for('bodegas'))
    return render_template('maestros/bodegas.html', items=Bodega.query.all())

@app.route('/empleados', methods=['GET', 'POST'])
@login_required
@role_required('Administrador')
def empleados():
    if request.method == 'POST':
        eid = request.form.get('id')
        nombre, cargo, tel = request.form['nombre'], request.form['cargo'], request.form['telefono']
        if eid:
            e = Empleado.query.get(eid)
            e.nombre, e.cargo, e.telefono = nombre, cargo, tel
            flash('Empleado actualizado', 'success')
        else:
            e = Empleado(nombre=nombre, cargo=cargo, telefono=tel)
            db.session.add(e)
            flash('Empleado creado', 'success')
        db.session.commit()
        return redirect(url_for('empleados'))
    return render_template('maestros/empleados.html', items=Empleado.query.all())

@app.route('/clientes', methods=['GET', 'POST'])
@login_required
@role_required('Administrador', 'Vendedor')
def clientes():
    if request.method == 'POST':
        cid = request.form.get('id')
        nombre, ruc, tel = request.form['nombre'], request.form['ruc'], request.form['telefono']
        email, dir = request.form['email'], request.form['direccion']
        if cid:
            c = Cliente.query.get(cid)
            c.nombre, c.ruc, c.telefono, c.email, c.direccion = nombre, ruc, tel, email, dir
            flash('Cliente actualizado', 'success')
        else:
            c = Cliente(nombre=nombre, ruc=ruc, telefono=tel, email=email, direccion=dir)
            db.session.add(c)
            flash('Cliente registrado', 'success')
        db.session.commit()
        return redirect(url_for('clientes'))
    return render_template('clientes.html', items=Cliente.query.all())

@app.route('/proveedores', methods=['GET', 'POST'])
@login_required
@role_required('Administrador', 'Operador de Almacén')
def proveedores():
    if request.method == 'POST':
        pid = request.form.get('id')
        rs, ruc, tel = request.form['razon_social'], request.form['ruc'], request.form['telefono']
        email = request.form['email']
        if pid:
            p = Proveedor.query.get(pid)
            p.razon_social, p.ruc, p.telefono, p.email = rs, ruc, tel, email
            flash('Proveedor actualizado', 'success')
        else:
            p = Proveedor(razon_social=rs, ruc=ruc, telefono=tel, email=email)
            db.session.add(p)
            flash('Proveedor registrado', 'success')
        db.session.commit()
        return redirect(url_for('proveedores'))
    return render_template('proveedores.html', items=Proveedor.query.all())

# --- OPERACIONES ---

@app.route('/compras', methods=['GET', 'POST'])
@login_required
@role_required('Administrador', 'Operador de Almacén')
def compras():
    if request.method == 'POST':
        prov_id = int(request.form['proveedor_id'])
        usr_id = get_current_user().id
        nums_prod = request.form.getlist('producto_id[]')
        cants = request.form.getlist('cantidad[]')
        costos = request.form.getlist('costo[]')
        n_factura = request.form['numero_factura']
        bodega_id = request.form['bodega_id']
        
        moneda = request.form.get('moneda', 'NIO')
        tasa_cambio = float(request.form.get('tasa_cambio', 1.0))
        
        prov = Proveedor.query.get(prov_id)
        
        # Validar bloqueo oficial
        for pid in nums_prod:
            prod = Producto.query.get(pid)
            if prod.sku == 'ACE-EST-BULK' and 'Inducaribe' not in prov.razon_social:
                flash(f'Error: El Aceite Estándar solo puede comprarse a Inducaribe S.A.', 'error')
                return redirect(url_for('compras'))
            if prod.sku == 'ACE-PRE-BULK' and 'Olmeca' not in prov.razon_social:
                flash(f'Error: El Aceite Premium solo puede comprarse a Olmeca', 'error')
                return redirect(url_for('compras'))

        # Fecha real del documento físico (opcional, si no viene usa now)
        fecha_str = request.form.get('fecha_factura')
        try:
            fecha_doc = datetime.datetime.fromisoformat(fecha_str) if fecha_str else datetime.datetime.now()
        except Exception:
            fecha_doc = datetime.datetime.now()

        nueva_compra = Compra(proveedor_id=prov_id, numero_factura=n_factura, bodega_id=bodega_id, moneda=moneda, tasa_cambio=tasa_cambio, fecha=fecha_doc)
        db.session.add(nueva_compra)
        db.session.flush()
        
        total_compra = 0.0
        for pid, cant, cost in zip(nums_prod, cants, costos):
            p_obj = Producto.query.get(pid)
            cant_compra = float(cant)
            costo_factura = float(cost) # Costo por Unidad de Compra (ej. por Tonelada)
            
            # Aplicar conversión si existe (ej: TM -> Litros)
            factor = p_obj.factor_conversion or 1.0
            cantidad_inventario = cant_compra * factor
            costo_inventario = costo_factura / factor if factor > 0 else costo_factura
            
            subtot = cant_compra * costo_factura # El subtotal de la factura se mantiene igual
            total_compra += subtot
            
            det = DetalleCompra(compra_id=nueva_compra.id, producto_id=pid, cantidad=cantidad_inventario, costo_unitario=costo_inventario, subtotal=subtot)
            db.session.add(det)
            
            obs_kardex = f"Compra fact #{n_factura}"
            if factor > 1:
                obs_kardex += f" (Conv: {cant_compra} TM -> {cantidad_inventario} L)"
            
            InventarioService.registrar_entrada(pid, cantidad_inventario, f"COMPRA-{nueva_compra.id}", usr_id, obs_kardex)
            
        nueva_compra.total = total_compra
        nueva_compra.total_base = total_compra * tasa_cambio
        
        db.session.commit()
        flash('Compra Multimoneda registrada con éxito y Kárdex actualizado', 'success')
        return redirect(url_for('compras'))

    from models import ConfiguracionGlobal
    conf = ConfiguracionGlobal.query.first()
    
    prods = Producto.query.join(Categoria).filter(Categoria.nombre != 'Producto Terminado').all()
    provs = Proveedor.query.all()
    bods  = Bodega.query.all()
    cmps  = Compra.query.order_by(Compra.fecha.desc()).limit(10).all()
    return render_template('compras.html', productos=prods, proveedores=provs, bodegas=bods, items=cmps, conf=conf)

@app.route('/ventas', methods=['GET', 'POST'])
@login_required
@role_required('Administrador', 'Vendedor')
def ventas():
    if request.method == 'POST':
        cliente_id = int(request.form['cliente_id'])
        vendedor_id = get_current_user().id
        nums_prod = request.form.getlist('producto_id[]')
        cants = request.form.getlist('cantidad[]')
        
        # Generar número de factura automático: 001-001-XXXXXX
        ultimo_id = db.session.query(func.max(Venta.id)).scalar() or 0
        numero_factura = f"001-001-{(ultimo_id + 1):06d}"
        nueva_venta = Venta(cliente_id=cliente_id, vendedor_id=vendedor_id, numero_factura=numero_factura, total=0.0)
        db.session.add(nueva_venta)
        db.session.flush()
        
        total_acumulado = 0
        for pid, cant in zip(nums_prod, cants):
            prod = Producto.query.get(pid)
            cantidad = int(cant)
            if InventarioService.registrar_salida(pid, cantidad, f"VENTA-{nueva_venta.id}", vendedor_id, "Venta POS"):
                sub = (prod.precio_venta or 0) * cantidad
                det = DetalleVenta(venta_id=nueva_venta.id, producto_id=pid, cantidad=cantidad, precio_unitario=prod.precio_venta or 0, subtotal=sub)
                db.session.add(det)
                total_acumulado += sub
            else:
                db.session.rollback()
                flash(f'Stock insuficiente para {prod.nombre}', 'error')
                return redirect(url_for('ventas'))
        
        nueva_venta.total = total_acumulado
        db.session.commit()
        flash('Venta nacional procesada correctamente', 'success')
        return redirect(url_for('ventas'))

    vnts = Venta.query.order_by(Venta.fecha.desc()).limit(10).all()
    prods = Producto.query.join(Categoria).filter(Categoria.nombre == 'Producto Terminado').all()
    clis = Cliente.query.all()
    return render_template('ventas.html', items=vnts, productos=prods, clientes=clis)

# --- INVENTARIO Y KARDEX ---

@app.route('/inventario')
@login_required
def inventario():
    prods = Producto.query.all()
    return render_template('inventario.html', items=prods)

@app.route('/kardex')
@login_required
def kardex():
    movs = Kardex.query.order_by(Kardex.fecha.desc()).all()
    return render_template('kardex.html', items=movs)

@app.route('/inventario/ajuste', methods=['GET', 'POST'])
@login_required
@role_required('Administrador', 'Operador de Almacén')
def ajuste_inventario():
    if request.method == 'POST':
        # Validación robusta de producto_id
        raw_id = request.form.get('producto_id')
        if not raw_id:
            flash('Error: Debe seleccionar un producto válido.', 'error')
            return redirect(url_for('ajuste_inventario'))
            
        producto_id = int(raw_id)
        tipo = request.form['tipo_movimiento']
        cantidad = int(request.form['cantidad'])
        obs = request.form['observacion']
        usr_id = get_current_user().id
        
        if tipo == 'ENTRADA':
            InventarioService.registrar_entrada(producto_id, cantidad, "AJUSTE-MANUAL", usr_id, obs)
            flash('Entrada de ajuste registrada', 'success')
        elif tipo == 'SALIDA':
            if InventarioService.registrar_salida(producto_id, cantidad, "AJUSTE-MANUAL", usr_id, obs):
                flash('Salida de ajuste registrada (Merma)', 'success')
            else:
                flash('Error: Stock insuficiente', 'error')
        
        db.session.commit()
        return redirect(url_for('ajuste_inventario'))
        
    # Buscar el bidón de 19L específico para el ajuste fijo
    bidon_obj = Producto.query.filter(Producto.nombre.like('%Bidón 19L%')).first()
    
    ajustes = Kardex.query.filter_by(documento_id='AJUSTE-MANUAL').order_by(Kardex.fecha.desc()).limit(10).all()
    return render_template('ajuste_inventario.html', bidon=bidon_obj, ajustes_recientes=ajustes)

@app.route('/produccion/envasado', methods=['GET', 'POST'])
@login_required
@role_required('Administrador', 'Operador de Almacén')
def envasado():
    if request.method == 'POST':
        tipo_combo = request.form['tipo_combo']
        cantidad = int(request.form['cantidad'])
        usr_id = get_current_user().id
        
        success, message = InventarioService.registrar_produccion(tipo_combo, cantidad, usr_id)
        if success:
            db.session.commit()
            flash(message, 'success')
        else:
            flash(message, 'error')
        return redirect(url_for('envasado'))

    # Telemetría de planta
    bolk_prods = Producto.query.filter(Producto.sku.like('ACE-%-BULK')).all()
    envase_prods = Producto.query.join(Categoria).filter(Categoria.nombre == 'Insumos y Envases', db.or_(Producto.sku.like('BID-%'), Producto.sku.like('BOT-%'))).all()
    terminado_prods = Producto.query.filter(Producto.sku.like('PRO-%')).all()
    
    historial = Kardex.query.filter(Kardex.documento_id.like('PLANTA-%'), Kardex.tipo_movimiento == 'ENTRADA').order_by(Kardex.fecha.desc()).limit(10).all()
    return render_template('envasado.html', bulk=bolk_prods, vacio=envase_prods, terminados=terminado_prods, historial=historial)

# --- USUARIOS ---
@app.route('/usuarios', methods=['GET', 'POST'])
@login_required
@role_required('Administrador')
def usuarios():
    if request.method == 'POST':
        uid = request.form.get('id')
        nombre, email, rol = request.form['nombre'], request.form['email'], request.form['rol']
        pwd = request.form['password']
        if uid:
            u = Usuario.query.get(uid)
            u.nombre, u.email, u.rol = nombre, email, rol
            if pwd: u.password = pwd # Solo actualizar si se provee nueva
            flash('Usuario actualizado', 'success')
        else:
            u = Usuario(nombre=nombre, email=email, rol=rol, password=pwd)
            db.session.add(u)
            flash('Usuario creado', 'success')
        db.session.commit()
        return redirect(url_for('usuarios'))
    return render_template('usuarios.html', items=Usuario.query.all())

# --- RUTAS DE ELIMINACIÓN (Seguridad) ---

@app.route('/entidad/eliminar/<string:tipo>/<int:id>')
@login_required
@role_required('Administrador')
def eliminar_entidad(tipo, id):
    model_map = {
        'producto': Producto, 'categoria': Categoria, 'unidad': UnidadMedida,
        'bodega': Bodega, 'empleado': Empleado, 'cliente': Cliente,
        'proveedor': Proveedor, 'usuario': Usuario
    }
    if tipo not in model_map:
        flash('Tipo de entidad no válido', 'error')
        return redirect(url_for('index'))
    
    obj = model_map[tipo].query.get_or_404(id)
    try:
        db.session.delete(obj)
        db.session.commit()
        flash(f'{tipo.capitalize()} eliminado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'No se puede eliminar: el registro está siendo utilizado en otras operaciones.', 'error')
    
    # Redirigir según el tipo
    redirect_map = {
        'producto': 'productos', 'categoria': 'categorias', 'unidad': 'unidades',
        'bodega': 'bodegas', 'empleado': 'empleados', 'cliente': 'clientes',
        'proveedor': 'proveedores', 'usuario': 'usuarios'
    }
    return redirect(url_for(redirect_map[tipo]))

# --- CONFIGURACION Y REPORTES ---
from flask import send_file
from utils.pdf_generator import InvoiceGenerator
from utils.report_generator import ReportGenerator
import openpyxl

@app.route('/ventas/pdf/<int:id>')
@login_required
def generar_factura_pdf(id):
    venta = Venta.query.get_or_404(id)
    pdf_buffer = InvoiceGenerator.generate_invoice(venta)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f'Factura_IVVI_{venta.id}.pdf',
        mimetype='application/pdf'
    )

@app.route('/configuracion', methods=['GET', 'POST'])
@login_required
@role_required('Administrador')
def configuracion():
    from models import ConfiguracionGlobal
    conf = ConfiguracionGlobal.query.first()
    if not conf:
        conf = ConfiguracionGlobal()
        db.session.add(conf)
        db.session.commit()
        
    if request.method == 'POST':
        conf.nombre_empresa = request.form.get('nombre_empresa', conf.nombre_empresa)
        conf.ruc = request.form.get('ruc', conf.ruc)
        conf.tasa_cambio = float(request.form.get('tasa_cambio', conf.tasa_cambio))
        db.session.commit()
        flash('Configuración corporativa actualizada correctamente', 'success')
        return redirect(url_for('configuracion'))

    return render_template('configuracion.html', conf=conf)

@app.route('/reportes')
@login_required
def reportes():
    return render_template('reportes.html')

@app.route('/reportes/ventas/excel')
@login_required
def reporte_ventas_excel():
    vnts = Venta.query.all()
    buffer = ReportGenerator.generate_sales_excel(vnts)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'Reporte_Ventas_IVVI_{datetime.datetime.now().strftime("%Y%m%d")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# ── GESTIÓN DE TRANSACCIONES (DETALLE Y ANULACIÓN) ────────────────────

@app.route('/api/compras/<int:id>')
@login_required
def get_compra_detalle(id):
    c = Compra.query.get_or_404(id)
    detalles = []
    for d in c.detalles:
        detalles.append({
            'producto': d.producto.nombre,
            'sku': d.producto.sku,
            'cantidad': d.cantidad,
            'unidad': d.producto.unidad.abreviatura,
            'costo_unitario': d.costo_unitario,
            'subtotal': d.subtotal
        })
    return jsonify({
        'id': c.id,
        'proveedor': c.proveedor.razon_social,
        'fecha': c.fecha.strftime('%d/%m/%Y %H:%M'),
        'factura': c.numero_factura,
        'moneda': c.moneda,
        'total': c.total,
        'estado': c.estado,
        'detalles': detalles
    })

@app.route('/compras/<int:id>/anular', methods=['POST'])
@login_required
@role_required('Administrador', 'Gerencia')
def anular_compra(id):
    c = Compra.query.get_or_404(id)
    if c.estado == 'Anulada':
        flash('Esta compra ya está anulada.', 'warning')
        return redirect(url_for('compras'))
    
    usr_id = session.get('user_id')
    # Revertir stock
    for d in c.detalles:
        # Registrar salida correctiva
        InventarioService.registrar_salida(d.producto_id, d.cantidad, f"ANULACION-C{c.id}", usr_id, f"Anulación de Compra #{c.numero_factura}")
    
    c.estado = 'Anulada'
    db.session.commit()
    flash(f'Compra #{c.id} anulada exitosamente. Stock revertido.', 'success')
    return redirect(url_for('compras'))

@app.route('/api/inventario/valorizacion')
@login_required
def get_valorizacion_detalle():
    prods = Producto.query.all()
    items = []
    total_general = 0
    
    for p in prods:
        ultimo_detalle = DetalleCompra.query.filter_by(producto_id=p.id).order_by(DetalleCompra.id.desc()).first()
        costo = ultimo_detalle.costo_unitario if ultimo_detalle else 0.0
        valor = p.stock_actual * costo
        total_general += valor
        
        if p.stock_actual > 0:
            items.append({
                'producto': p.nombre,
                'sku': p.sku,
                'stock': p.stock_actual,
                'unidad': p.unidad.abreviatura if p.unidad else '',
                'ultimo_costo': costo,
                'valor_total': valor
            })
            
    return jsonify({
        'total_general': total_general,
        'items': sorted(items, key=lambda x: x['valor_total'], reverse=True)
    })

@app.route('/api/ventas/<int:id>')
@login_required
def get_venta_detalle(id):
    v = Venta.query.get_or_404(id)
    detalles = []
    for d in v.detalles:
        detalles.append({
            'producto': d.producto.nombre,
            'sku': d.producto.sku,
            'cantidad': d.cantidad,
            'unidad': d.producto.unidad.abreviatura,
            'precio_unitario': d.precio_unitario,
            'subtotal': d.subtotal
        })
    return jsonify({
        'id': v.id,
        'cliente': v.cliente.nombre,
        'fecha': v.fecha.strftime('%d/%m/%Y %H:%M'),
        'factura': v.numero_factura,
        'total': v.total,
        'estado': v.estado,
        'detalles': detalles
    })

@app.route('/ventas/<int:id>/anular', methods=['POST'])
@login_required
@role_required('Administrador', 'Gerencia')
def anular_venta(id):
    v = Venta.query.get_or_404(id)
    if v.estado == 'Anulada':
        flash('Esta venta ya está anulada.', 'warning')
        return redirect(url_for('ventas'))
    
    usr_id = session.get('user_id')
    # Revertir stock (re-ingreso)
    for d in v.detalles:
        InventarioService.registrar_entrada(d.producto_id, d.cantidad, f"ANULACION-V{v.id}", usr_id, f"Anulación de Venta #{v.numero_factura}")
    
    v.estado = 'Anulada'
    db.session.commit()
    flash(f'Venta #{v.id} anulada exitosamente. Stock devuelto a almacén.', 'success')
    return redirect(url_for('ventas'))

@app.route('/reportes/compras/excel')
@login_required
def reporte_compras_excel():
    cmps = Compra.query.all()
    buffer = ReportGenerator.generate_purchases_excel(cmps)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'Reporte_Compras_IVVI_{datetime.datetime.now().strftime("%Y%m%d")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/reportes/inventario/excel')
@login_required
def reporte_inventario_excel():
    prods = Producto.query.all()
    buffer = ReportGenerator.generate_inventory_excel(prods)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'Reporte_Inventario_IVVI_{datetime.datetime.now().strftime("%Y%m%d")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/reportes/kardex/excel')
@login_required
@role_required('Administrador', 'Operador de Almacén', 'Gerencia')
def reporte_kardex_excel():
    items = Kardex.query.order_by(Kardex.fecha.desc()).all()
    buffer = ReportGenerator.generate_kardex_excel(items)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'Kardex_Auditoria_IVVI_{datetime.datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)


