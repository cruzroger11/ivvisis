import openpyxl
import io
from models import Venta, Compra, Producto

class ReportGenerator:
    @staticmethod
    def generate_sales_excel(ventas):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reporte de Ventas IVVI"
        
        headers = ['ID Factura', 'Fecha', 'Cliente', 'RUC Cliente', 'Vendedor', 'Total']
        ws.append(headers)
        
        # Estilo básico para cabeceras
        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True)
        
        for v in ventas:
            ws.append([
                f"FAC-{v.id:06d}",
                v.fecha.strftime('%d/%m/%Y %H:%M'),
                v.cliente.nombre if v.cliente else 'N/A',
                v.cliente.ruc if v.cliente else 'N/A',
                v.usuario.nombre if v.usuario else 'Sistema',
                v.total
            ])
            
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_purchases_excel(compras):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reporte de Compras IVVI"
        
        headers = ['ID Compra', 'Fecha', 'Factura Proveedor', 'Proveedor', 'Bodega', 'Total']
        ws.append(headers)
        
        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True)
            
        for c in compras:
            ws.append([
                f"COM-{c.id:06d}",
                c.fecha.strftime('%d/%m/%Y %H:%M'),
                c.numero_factura or 'Sin Ref',
                c.proveedor.razon_social if c.proveedor else 'N/A',
                c.bodega.nombre if c.bodega else 'N/A',
                c.total
            ])
            
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_inventory_excel(productos):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Estado de Almacén IVVI"
        
        headers = ['SKU', 'Producto', 'Categoría', 'Unidad', 'Precio Venta', 'Stock Actual', 'Mínimo', 'Estado Stock']
        ws.append(headers)
        
        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True)
            
        for p in productos:
            estado = "CRÍTICO" if p.stock_actual <= p.stock_minimo else "ÓPTIMO"
            ws.append([
                p.sku,
                p.nombre,
                p.categoria.nombre if p.categoria else 'N/A',
                p.unidad.nombre if p.unidad else 'N/A',
                p.precio_venta,
                p.stock_actual,
                p.stock_minimo,
                estado
            ])
            
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_kardex_excel(kardex_items):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Kardex de Auditoría IVVI"
        
        headers = ['Fecha', 'Hora', 'Tipo Movimiento', 'Documento/REF', 'SKU', 'Producto/Material', 'Cantidad', 'Responsable', 'Observaciones']
        ws.append(headers)
        
        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True)
            
        for m in kardex_items:
            sign = '+' if m.tipo_movimiento == 'ENTRADA' else '-'
            ws.append([
                m.fecha.strftime('%d/%m/%Y'),
                m.fecha.strftime('%H:%M:%S'),
                m.tipo_movimiento,
                f"REF-{m.documento_id}",
                m.producto.sku if m.producto else 'N/A',
                m.producto.nombre if m.producto else 'N/A',
                f"{sign}{m.cantidad}",
                m.usuario.nombre if m.usuario else 'Sistema',
                m.observacion or 'Sin observaciones adicionales'
            ])
            
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer
