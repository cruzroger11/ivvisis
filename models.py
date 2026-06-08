from db import db
from datetime import datetime

# --- BASE DE DATOS Y POO ---

class ConfiguracionGlobal(db.Model):
    """ PARAMETROS CENTRALES DEL SISTEMA """
    __tablename__ = 'configuracion_global'
    id = db.Column(db.Integer, primary_key=True)
    nombre_empresa = db.Column(db.String(150), default='IVVI S.A.')
    ruc = db.Column(db.String(50), default='1790045623001')
    tasa_cambio = db.Column(db.Float, default=36.00)

class Persona(db.Model):
    """
    CLASE BASE (Abstracción e Herencia)
    Implementa los datos comunes para cualquier entidad humana o jurídica en el sistema.
    """
    __tablename__ = 'personas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(120))
    direccion = db.Column(db.String(250))
    tipo_persona = db.Column(db.String(50)) # Para herencia de tabla unida

    __mapper_args__ = {
        'polymorphic_identity': 'persona',
        'polymorphic_on': tipo_persona
    }

    def mostrar_resumen(self):
        """ Ejemplo de método base para polimorfismo """
        return f"{self.nombre} ({self.email})"

class Usuario(Persona):
    """
    Entidad de acceso al sistema (Herencia de Persona).
    """
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, db.ForeignKey('personas.id'), primary_key=True)
    rol = db.Column(db.String(50), nullable=False) # Administrador, Operador, Vendedor, Gerencia
    password = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(20), default='Activo')

    __mapper_args__ = {
        'polymorphic_identity': 'usuario',
    }

class Cliente(Persona):
    """
    Entidad de ventas (Herencia de Persona).
    """
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, db.ForeignKey('personas.id'), primary_key=True)
    ruc = db.Column(db.String(20), unique=True)
    contacto_principal = db.Column(db.String(100))
    observaciones = db.Column(db.Text)
    estado = db.Column(db.String(20), default='Activo')

    __mapper_args__ = {
        'polymorphic_identity': 'cliente',
    }

class Empleado(Persona):
    """
    Entidad de personal (Herencia de Persona).
    """
    __tablename__ = 'empleados'
    id = db.Column(db.Integer, db.ForeignKey('personas.id'), primary_key=True)
    cargo = db.Column(db.String(100))
    estado = db.Column(db.String(20), default='Activo')
    observaciones = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'empleado',
    }

class Proveedor(db.Model):
    """
    Entidad de compras. 
    Se mantiene como tabla independiente por la complejidad de campos específicos empresariales.
    """
    __tablename__ = 'proveedores'
    id = db.Column(db.Integer, primary_key=True)
    razon_social = db.Column(db.String(150), nullable=False)
    ruc = db.Column(db.String(20), unique=True)
    contacto = db.Column(db.String(100))
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(120))
    direccion = db.Column(db.String(250))
    pais = db.Column(db.String(100))
    banco = db.Column(db.String(100))
    numero_cuenta = db.Column(db.String(100))
    observaciones = db.Column(db.Text)
    estado = db.Column(db.String(20), default='Activo')

# --- MAESTROS DE INVENTARIO ---

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(250))

class UnidadMedida(db.Model):
    __tablename__ = 'unidades_medida'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False) # Litros, Galones, Kilos, etc.
    abreviatura = db.Column(db.String(10))

class Bodega(db.Model):
    __tablename__ = 'bodegas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(250))

class Producto(db.Model):
    """
    CATÁLOGO DE PRODUCTOS (Encapsulación)
    """
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))
    unidad_id = db.Column(db.Integer, db.ForeignKey('unidades_medida.id'))
    precio_venta = db.Column(db.Float, default=0.0)
    stock_minimo = db.Column(db.Integer, default=5)
    factor_conversion = db.Column(db.Float, default=1.0) # Cuántas uds inventario por 1 ud compra
    estado = db.Column(db.String(20), default='Activo')
    
    # Campo calculado o centralizado
    stock_actual = db.Column(db.Integer, default=0)

    # Relaciones
    categoria = db.relationship('Categoria', backref='productos', lazy=True)
    unidad = db.relationship('UnidadMedida', backref='productos', lazy=True)

    def validar_stock(self, cantidad):
        """ Encapsula la validación de disponibilidad """
        return self.stock_actual >= cantidad

    def es_bajo_stock(self):
        return self.stock_actual <= self.stock_minimo

# --- OPERACIONES ---

class Compra(db.Model):
    """ CABECERA DE COMPRA """
    __tablename__ = 'compras'
    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    numero_factura = db.Column(db.String(50))
    bodega_id = db.Column(db.Integer, db.ForeignKey('bodegas.id'))
    observaciones = db.Column(db.Text)
    
    # Manejo Multimoneda
    moneda = db.Column(db.String(3), default='NIO')
    tasa_cambio = db.Column(db.Float, default=1.0)
    total = db.Column(db.Float, default=0.0) # Total expresado en la moneda original de transacción
    total_base = db.Column(db.Float, default=0.0) # Total normalizado forzosamente a la moneda principal de la compañía (NIO)
    estado = db.Column(db.String(20), default='Completada') # Completada, Anulada

    # Relaciones
    proveedor = db.relationship('Proveedor', backref='compras', lazy=True)
    bodega = db.relationship('Bodega', backref='compras', lazy=True)
    detalles = db.relationship('DetalleCompra', backref='compra', lazy=True, cascade="all, delete-orphan")

class DetalleCompra(db.Model):
    """ DETALLE DE COMPRA """
    __tablename__ = 'detalles_compra'
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'))
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'))
    cantidad = db.Column(db.Integer, nullable=False)
    costo_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    # Relación
    producto = db.relationship('Producto', lazy=True)

class Venta(db.Model):
    """ CABECERA DE VENTA """
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'))
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    numero_factura = db.Column(db.String(50))
    observaciones = db.Column(db.Text)
    total = db.Column(db.Float, default=0.0)
    estado = db.Column(db.String(20), default='Completada') # Completada, Anulada

    # Relaciones
    cliente = db.relationship('Cliente', backref='ventas', lazy=True)
    usuario = db.relationship('Usuario', backref='ventas', lazy=True)
    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True, cascade="all, delete-orphan")

class DetalleVenta(db.Model):
    """ DETALLE DE VENTA """
    __tablename__ = 'detalles_venta'
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'))
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'))
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    descuento = db.Column(db.Float, default=0.0)
    impuesto = db.Column(db.Float, default=0.0)
    subtotal = db.Column(db.Float, nullable=False)

    # Relación
    producto = db.relationship('Producto', lazy=True)

# --- KARDEX ---

class Kardex(db.Model):
    """ HISTORIAL DE MOVIMIENTOS (Trazabilidad) """
    __tablename__ = 'kardex'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo_movimiento = db.Column(db.String(50)) # ENTRADA, SALIDA, AJUSTE
    documento_id = db.Column(db.String(50))    # ID de venta o compra
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'))
    cantidad = db.Column(db.Integer, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    observacion = db.Column(db.String(250))

    # Relaciones
    producto = db.relationship('Producto', lazy=True)
    usuario = db.relationship('Usuario', lazy=True)

# --- LÓGICA DE NEGOCIO (Modularidad) ---

class InventarioService:
    """ Clase para centralizar operaciones de inventario (Polimorfismo / Abstracción) """
    
    @staticmethod
    def registrar_entrada(producto_id, cantidad, documento, usuario_id, obs="Compra"):
        prod = Producto.query.get(producto_id)
        if prod:
            prod.stock_actual += cantidad
            mov = Kardex(
                tipo_movimiento='ENTRADA',
                documento_id=documento,
                producto_id=producto_id,
                cantidad=cantidad,
                usuario_id=usuario_id,
                observacion=obs
            )
            db.session.add(mov)
            return True
        return False

    @staticmethod
    def registrar_salida(producto_id, cantidad, documento, usuario_id, obs="Venta"):
        prod = Producto.query.get(producto_id)
        if prod and prod.validar_stock(cantidad):
            prod.stock_actual -= cantidad
            mov = Kardex(
                tipo_movimiento='SALIDA',
                documento_id=documento,
                producto_id=producto_id,
                cantidad=cantidad,
                usuario_id=usuario_id,
                observacion=obs
            )
            db.session.add(mov)
            return True
        return False

    @staticmethod
    def registrar_produccion(tipo_combo, cantidad, usuario_id):
        """
        Lógica de Envasado Multimarca y Multi-Envase
        """
        config = {
            'ESTANDAR-19L': {
                'sku_oil': 'ACE-EST-BULK', 
                'sku_envase': 'BID-VACIO-19L', 
                'sku_final': 'PRO-EST-19L',
                'oil_ratio': 19,
                'nombre': 'Fruto Dorado 19L'
            },
            'PREMIUM-19L': {
                'sku_oil': 'ACE-PRE-BULK', 
                'sku_envase': 'BID-VACIO-19L', 
                'sku_final': 'PRO-PRE-19L',
                'oil_ratio': 19,
                'nombre': 'Divina Providencia 19L'
            },
            'PREMIUM-2.5G': {
                'sku_oil': 'ACE-PRE-BULK', 
                'sku_envase': 'BOT-VACIA-2.5G', 
                'sku_final': 'PRO-PRE-2.5G',
                'oil_ratio': 9.5,
                'nombre': 'Divina Providencia 2.5 Gal'
            }
        }

        if tipo_combo not in config:
            return False, "Error: Tipo de producción no reconocido."
        
        c = config[tipo_combo]
        p_bulk = Producto.query.filter_by(sku=c['sku_oil']).first()
        p_envase = Producto.query.filter_by(sku=c['sku_envase']).first()
        p_final = Producto.query.filter_by(sku=c['sku_final']).first()

        if not p_bulk or not p_envase or not p_final:
            return False, "Error: Configuración de productos (SKUs) no encontrada en catálogo."

        oil_total = cantidad * c['oil_ratio']

        # Validaciones
        if p_bulk.stock_actual < oil_total:
            return False, f"Stock insuficiente de Aceite Bulk: Se requieren {oil_total}L."
        if p_envase.stock_actual < cantidad:
            return False, f"Stock insuficiente de Envases Vacíos: Se requieren {cantidad} UND."

        # Transacción
        doc = f"PLANTA-{tipo_combo}-{datetime.now().strftime('%m%d%H%M')}"
        
        # 1. Salida ACEITE
        InventarioService.registrar_salida(p_bulk.id, oil_total, doc, usuario_id, f"Consumo envasado {c['nombre']}")
        
        # 2. Salida ENVASE
        InventarioService.registrar_salida(p_envase.id, cantidad, doc, usuario_id, f"Envases usados para {c['nombre']}")
        
        # 3. Entrada FINAL
        InventarioService.registrar_entrada(p_final.id, cantidad, doc, usuario_id, f"Producción terminada {c['nombre']}")

        return True, f"Orden de producción completada: {cantidad} unidades de {c['nombre']}."

