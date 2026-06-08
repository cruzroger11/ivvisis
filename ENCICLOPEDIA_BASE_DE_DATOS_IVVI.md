# 📚 Enciclopedia de la Base de Datos: IVVI S.A.

Este documento es el compendio total de los pilares, la estructura y la lógica de la base de datos de gestión industrial.

---

## 1. Los 5 Pilares del Conocimiento (Reseteo Mental)
Antes de ver tablas, debemos entender para qué sirven:
1.  **Propósito:** La Trazabilidad Industrial. Nada se mueve sin dejar huella.
2.  **Maestros:** Los cimientos (Productos, Personas).
3.  **Flujo:** Las transacciones que mueven el stock.
4.  **Integridad:** Las reglas que prohíben borrar historial.
5.  **Auditoría:** El **Kárdex**, la caja negra inmutable.

---

## 2. Distribución Lógica (Los 4 Departamentos)
La información se organiza en estos grandes "bloques" funcionales:
*   **Identidad:** Centraliza Clientes, Usuarios y Empleados en torno a la tabla `personas`.
*   **Inventario:** El catálogo maestro de productos, categorías y bodegas.
*   **Operaciones:** El día a día; Compras a proveedores y Ventas a clientes.
*   **Auditoría:** El registro permanente de movimientos de material y ajustes.

---

## 3. Mapa Visual de Conexiones
Para ver este sistema de forma profesional y ordenada, utiliza este código en **[dbdiagram.io](https://dbdiagram.io/)**:

```dbml
// === IVVI S.A. - CÓDIGO MAESTRO COMPLETO ===

Table personas {
  id integer [primary key]
  nombre varchar
  email varchar
  tipo_persona varchar 
}

Table usuarios {
  id integer [primary key]
  rol varchar
}

Table clientes {
  id integer [primary key]
  ruc varchar
}

Table productos {
  id integer [primary key]
  sku varchar [unique]
  nombre varchar
  stock_actual float
  categoria_id integer
  unidad_id integer
}

Table categorias {
  id integer [primary key]
  nombre varchar
}

Table compras {
  id integer [primary key]
  proveedor_id integer
  fecha timestamp
  total float
}

Table detalles_compra {
  id integer [primary key]
  compra_id integer
  producto_id integer
  cantidad float
}

Table ventas {
  id integer [primary key]
  cliente_id integer
  fecha timestamp
  total float
}

Table detalles_venta {
  id integer [primary key]
  venta_id integer
  producto_id integer
  cantidad float
}

Table kardex {
  id integer [primary key]
  producto_id integer
  tipo_movimiento varchar
  cantidad float
}

Table configuracion_global {
  id integer [primary key]
  nombre_empresa varchar
  tasa_cambio float
}

// RELACIONES CLAVE
Ref: personas.id < usuarios.id
Ref: personas.id < clientes.id
Ref: categorias.id < productos.categoria_id
Ref: compras.id < detalles_compra.compra_id
Ref: productos.id < detalles_compra.producto_id
Ref: ventas.id < detalles_venta.venta_id
Ref: productos.id < detalles_venta.producto_id
Ref: productos.id < kardex.producto_id
```

---

## 4. Diccionario Técnico de Tablas
Aquí tienes la lista física de lo que realmente existe en tu base de datos:

| Grupo | Tabla | Propósito Principal |
| :--- | :--- | :--- |
| **Identidad** | `personas` | La base de datos de nombres y correos. |
| | `usuarios` | Control de entrada al sistema y roles. |
| | `clientes` | A quiénes les facturamos el producto. |
| **Maestros** | `productos` | El catálogo de aceites y envases (stock). |
| | `categorias` | Separa Materia Prima de Insumos. |
| | `unidades_medida` | Define las magnitudes (L, Gal, UND). |
| **Movimientos** | `compras` | Registro de facturas de proveedores. |
| | `detalles_compra` | El desglose ítem por ítem de cada compra. |
| | `ventas` | Facturación nacional y registro de ventas. |
| | `detalles_venta` | Lo que el cliente lleva en cada factura. |
| **Control** | `kardex` | **El Libro de Actas.** Historial de stock. |
| | `configuracion_global`| **El Cerebro.** RUC corporativo y Tasa de Cambio. |

---

## 5. El Caso Especial: Configuración Global
Esta tabla actúa como un **Singleton** (solo existe una fila). 
*   **¿Por qué está sola?** Porque no se repite; no necesitas una línea de conexión para cada venta. Es un manual de reglas que todo el sistema consulta para saber la **Tasa de Cambio** y los datos de IVVI S.A. al imprimir PDFs.

---

## 6. Guía de Navegación Rápida
| Si buscas saber... | Debes mirar... |
| :--- | :--- |
| **¿Quién vendió este bidón?** | `ventas` (vendedor_id) unido a `usuarios`. |
| **¿Qué factura trajo este stock?** | El `documento_id` del `kardex` que diga "COMPRA-X". |
| **¿Cuánto aceite premium tenemos?** | El campo `stock_actual` en `productos`. |

---
*Documento consolidado para IVVI S.A. - Estructura definitiva de datos.*
