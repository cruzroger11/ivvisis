from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
import io

class InvoiceGenerator:
    @staticmethod
    def generate_invoice(venta):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Cabecera Corporativa (Colores IVVI)
        p.setFillColor(colors.HexColor("#022c22"))
        p.rect(0, height - 1.5*inch, width, 1.5*inch, fill=1)
        
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 24)
        p.drawString(0.5*inch, height - 0.7*inch, "IVVI S.A.")
        
        p.setFont("Helvetica", 10)
        p.drawString(0.5*inch, height - 1.0*inch, "Aceite de Palma de Alta Calidad")
        p.drawString(0.5*inch, height - 1.2*inch, "RUC: 1790000000001 | Tel: +593 99 999 9999")

        p.setFont("Helvetica-Bold", 16)
        p.drawRightString(width - 0.5*inch, height - 0.7*inch, f"FACTURA #{venta.id}")
        p.setFont("Helvetica", 12)
        p.drawRightString(width - 0.5*inch, height - 1.0*inch, f"Fecha: {venta.fecha.strftime('%d/%m/%Y')}")

        # Datos del Cliente
        p.setFillColor(colors.black)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(0.5*inch, height - 2.0*inch, "DATOS DEL CLIENTE:")
        p.setFont("Helvetica", 11)
        p.drawString(0.5*inch, height - 2.2*inch, f"Nombre: {venta.cliente.nombre}")
        p.drawString(0.5*inch, height - 2.4*inch, f"RUC/CI: {venta.cliente.ruc}")
        p.drawString(0.5*inch, height - 2.6*inch, f"Dirección: {venta.cliente.direccion}")

        # Tabla de Detalles
        y = height - 3.2*inch
        p.setFont("Helvetica-Bold", 11)
        p.setFillColor(colors.HexColor("#015c3b"))
        p.rect(0.4*inch, y - 0.1*inch, width - 0.8*inch, 0.3*inch, fill=1)
        p.setFillColor(colors.white)
        p.drawString(0.5*inch, y, "PRODUCTO")
        p.drawString(3.5*inch, y, "CANT")
        p.drawString(4.5*inch, y, "PRECIO")
        p.drawString(5.5*inch, y, "SUBTOTAL")

        p.setFillColor(colors.black)
        p.setFont("Helvetica", 10)
        y -= 0.4*inch
        
        for det in venta.detalles:
            p.drawString(0.5*inch, y, det.producto.nombre[:40])
            p.drawString(3.5*inch, y, str(det.cantidad))
            p.drawString(4.5*inch, y, f"${det.precio_unitario:,.2f}")
            p.drawString(5.5*inch, y, f"${det.subtotal:,.2f}")
            y -= 0.25*inch
            if y < 1*inch: # Salto de página básico
                p.showPage()
                y = height - 1*inch

        # Total
        p.line(0.5*inch, y, width - 0.5*inch, y)
        y -= 0.4*inch
        p.setFont("Helvetica-Bold", 14)
        p.drawRightString(width - 0.5*inch, y, f"TOTAL: ${venta.total:,.2f}")

        # Pie de página
        p.setFont("Helvetica-Oblique", 8)
        p.drawCentredString(width/2, 0.5*inch, "Gracias por su preferencia. IVVI S.A. contribuyendo al agro.")

        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer
