import unittest
from flask import Flask
from models import db, Producto, Persona, Usuario, Cliente, InventarioService, Categoria, UnidadMedida
import os

class IvviTest(unittest.TestCase):

    def setUp(self):
        # Configuración de App de Prueba
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        db.init_app(self.app)

        with self.app.app_context():
            db.create_all()
            # Semillas básicas para pruebas
            cat = Categoria(nombre="Aceites")
            uni = UnidadMedida(nombre="Galones", abreviatura="gal")
            db.session.add_all([cat, uni])
            db.session.commit()
            
            # Almacenamos solo los IDs para evitar problemas de sesión (DetachedInstanceError)
            self.cat_id = cat.id
            self.uni_id = uni.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_creacion_producto(self):
        """ Prueba 1: Creación de Producto y POO """
        with self.app.app_context():
            p = Producto(
                sku="PROD-001", 
                nombre="Aceite de Palma", 
                categoria_id=self.cat_id,
                unidad_id=self.uni_id,
                stock_actual=10,
                stock_minimo=5
            )
            db.session.add(p)
            db.session.commit()
            
            p_db = Producto.query.filter_by(sku="PROD-001").first()
            self.assertIsNotNone(p_db)
            self.assertEqual(p_db.stock_actual, 10)

    def test_herencia_persona_usuario(self):
        """ Prueba 2: Herencia entre Persona y Usuario """
        with self.app.app_context():
            u = Usuario(
                nombre="Test User",
                email="test@ivvi.com",
                rol="Vendedor",
                password="123"
            )
            db.session.add(u)
            db.session.commit()
            
            # Verificar que existe tanto como Usuario como Persona (ID compartido)
            u_db = Usuario.query.filter_by(email="test@ivvi.com").first()
            self.assertEqual(u_db.nombre, "Test User")
            self.assertEqual(u_db.rol, "Vendedor")

    def test_validacion_stock_insuficiente(self):
        """ Prueba 3: Regla de Negocio - No vender sin stock """
        with self.app.app_context():
            p = Producto(sku="PROD-LOW", nombre="Stock Bajo", stock_actual=2)
            db.session.add(p)
            db.session.commit()
            
            # Escenario: Intentar vender 5 cuando hay 2
            success = p.validar_stock(5)
            self.assertFalse(success, "El sistema permitió validar stock inexistente.")

    def test_flujo_inventario_kardex(self):
        """ Prueba 4: Registro Kardex Automático """
        with self.app.app_context():
            p = Producto(sku="P-TEST", nombre="Producto Test", stock_actual=10)
            u = Usuario(nombre="Admin", rol="Administrador", password="123", email="ad@ivvi.com")
            db.session.add_all([p, u])
            db.session.commit()
            
            # Registrar Entrada (Compra)
            res = InventarioService.registrar_entrada(p.id, 5, "C-001", u.id, "Compra Test")
            
            # Verificar cambios
            p_updated = Producto.query.get(p.id)
            self.assertEqual(p_updated.stock_actual, 15)
            
            # Verificar que el Kardex tenga el registro
            from models import Kardex
            mov = Kardex.query.filter_by(documento_id="C-001").first()
            self.assertIsNotNone(mov)
            self.assertEqual(mov.tipo_movimiento, "ENTRADA")

    def test_conversion_industrial_tm_l(self):
        """ Prueba 5: Conversión Industrial (TM a L) """
        with self.app.app_context():
            p_bulk = Producto(sku="O-BULK", nombre="Aceite Bulk", factor_conversion=1100.0, stock_actual=0)
            u = Usuario(nombre="Logistica", rol="Operador", password="123", email="log@ivvi.com")
            db.session.add_all([p_bulk, u])
            db.session.commit()
            
            # Compramos 2 TM. El stock debe subir 2200 Litros.
            cantidad_tm = 2.0
            InventarioService.registrar_entrada(p_bulk.id, cantidad_tm * p_bulk.factor_conversion, "COMPRA-TM", u.id)
            
            p_updated = Producto.query.filter_by(sku="O-BULK").first()
            self.assertEqual(p_updated.stock_actual, 2200)

    def test_envasado_atomico(self):
        """ Prueba 6: Producción/Envasado Atómico (Descuento Doble) """
        with self.app.app_context():
            # Mock de datos para producción (Fruto Dorado 19L)
            p_oil = Producto(sku="ACE-EST-BULK", nombre="Aceite Est", stock_actual=100)
            p_env = Producto(sku="BID-VACIO-19L", nombre="Bidon", stock_actual=10)
            p_pt  = Producto(sku="PRO-EST-19L", nombre="PT 19L", stock_actual=0)
            u = Usuario(nombre="Planta", rol="Administrador", password="1", email="p@ivvi.com")
            db.session.add_all([p_oil, p_env, p_pt, u])
            db.session.commit()
            
            # Producir 2 bidones de 19L
            # Debe descontar 38L de aceite y 2 bidones vacios. Debe sumar 2 PT.
            success, msg = InventarioService.registrar_produccion("ESTANDAR-19L", 2, u.id)
            
            p_oil_up = Producto.query.filter_by(sku="ACE-EST-BULK").first()
            p_env_up = Producto.query.filter_by(sku="BID-VACIO-19L").first()
            p_pt_up  = Producto.query.filter_by(sku="PRO-EST-19L").first()
            
            self.assertTrue(success)
            self.assertEqual(p_oil_up.stock_actual, 100 - 38)
            self.assertEqual(p_env_up.stock_actual, 10 - 2)
            self.assertEqual(p_pt_up.stock_actual, 2)

    def test_integridad_referencial_kardex(self):
        """ Prueba 7: Integridad y Autoría del Kárdex """
        with self.app.app_context():
            p = Producto(sku="P-AUTH", nombre="P", stock_actual=10)
            u = Usuario(nombre="Auditor", rol="Administrador", password="1", email="a@ivvi.com")
            db.session.add_all([p, u])
            db.session.commit()
            
            InventarioService.registrar_salida(p.id, 1, "DOC-AUDIT", u.id, "Muestra de calidad")
            
            from models import Kardex
            mov = Kardex.query.filter_by(documento_id="DOC-AUDIT").first()
            # Validar que el movimiento esté amarrado a un usuario real
            self.assertEqual(mov.usuario.nombre, "Auditor")
            self.assertEqual(mov.producto.sku, "P-AUTH")

if __name__ == '__main__':
    unittest.main()
