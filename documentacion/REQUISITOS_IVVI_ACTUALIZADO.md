# 📋 Especificación de Requerimientos del Sistema: ERP IVVI S.A. (Edición de Defensa Académica)

Este documento detalla los **26 pilares fundamentales** del sistema IVVI S.A. Esta especificación exhaustiva cubre la totalidad de la arquitectura implementada, verificada y lista para operación industrial.

---

## 🟢 I. Requerimientos Funcionales (15 RF)
Capacidades operativas directas que el software ofrece para la gestión del negocio.

1.  **RF-01: Gestión de Identidad y Autenticación:** Portal de acceso que valida credenciales contra una base de datos local utilizando hashing Bcrypt.
2.  **RF-02: Control de Acceso por Roles (RBAC):** Jerarquías de permisos (Admin, Operador, Vendedor) que restringen módulos y acciones según el rango.
3.  **RF-03: Catálogo Maestro de Productos y Activos:** CRUD completo para el ciclo de vida de productos, insumos y envases.
4.  **RF-04: Gestión de Entidades Externas (CRM/SRM):** Registro centralizado de Clientes, Proveedores y Empleados con trazabilidad cruzada.
5.  **RF-05: Motor de Compras Multimoneda:** Ingreso de mercancía en USD o NIO con conversión automática a moneda base (NIO).
6.  **RF-06: Gestión de Ventas y Facturación:** Registro de transacciones con número de factura secuencial y descuento de stock automático.
7.  **RF-07: Ajustes Manuales Especializados:** Corrección de inventario por Descarte (al baja) o Retorno (exclusivo Bidones 19L).
8.  **RF-08: Gestión de Producción y Envasado:** Lógica de "Kit" que consume materia prima y envases para generar Producto Terminado.
9.  **RF-09: Trazabilidad Forense (Kárdex):** Registro inmutable de cada micro-evento capturando responsable, fecha y documento origen.
10. **RF-10: Generador de Reportes Industriales (PDF):** Exportación de documentos listos para impresión legal u operativa.
11. **RF-11: Dashboard de Indicadores Clave (KPIs):** Panel gerencial con resumen de ventas, compras y alertas en tiempo real.
12. **RF-12: Sistema de Notificaciones Flash (Toasts):** Alertas visuales inmediatas que informan el éxito o fallo de cada acción al usuario.
13. **RF-13: Motor de Búsqueda Dinámica:** Filtrado en tiempo real en todas las tablas para localización instantánea de registros.
14. **RF-14: Gestión de Bodegas y Ubicaciones:** Capacidad de segregar el inventario por puntos físicos de almacenamiento.
15. **RF-15: Filtrado Cronológico Avanzado:** Capacidad de segmentar la información y reportes por rangos de fecha específicos.

---

## 🔵 II. Requerimientos No Funcionales (6 RNF)
Estándares técnicos de calidad, seguridad y rendimiento.

16. **RNF-01: Integridad Transaccional (ACID):** Garantiza que las operaciones de stock sean atómicas; si un paso falla, se revierte todo.
17. **RNF-02: Soberanía de Datos (On-Premise):** Implementación local que asegura que la data industrial nunca salga de la empresa.
18. **RNF-03: Ergonomía Visual (Glassmorphism):** Diseño de interfaz moderno orientado a reducir el estrés visual del operario.
19. **RNF-04: Continuidad Operativa (Offline First):** Capacidad de operar la facturación y almacén sin dependencia de internet.
20. **RNF-05: Arquitectura de Cero Instalación (Portabilidad):** El sistema es portable y ejecutable desde cualquier unidad local sin instaladores complejos.
21. **RNF-06: Persistencia Relacional Robusta:** Uso de motor SQLite para garantizar integridad frente a cortes de energía.

---

## 🔴 III. Reglas de Negocio (5 BR)
Restricciones lógicas innegociables que protegen la salud financiera y operativa del negocio.

22. **BR-01: Restricción de Inventario Negativo:** Bloqueo total de transacciones que intenten vender o envasar productos inexistentes.
23. **BR-02: Inmutabilidad de la Memoria (Kárdex):** Prohibición total de edición o borrado de registros de kárdex generado.
24. **BR-03: Política de Envases Retornables (Filtro 19L):** Los retornos de clientes solo se validan para envases de 19L por política de costos.
25. **BR-04: Estandarización de Tasa de Cambio:** Obligatoriedad de uso de la tasa global configurada para todas las compras internacionales.
26. **BR-05: Unicidad de Identificadores Fiscales (RUC):** Bloqueo de duplicidad de RUC en clientes y proveedores para evitar caos contable.

---
**Recuento Final:** 15 RF + 6 RNF + 5 BR = **26 Requerimientos de Nivel Industrial.**

---

## 🚀 Fase 2: Roadmap (Proyectos Futuros)
Siguiendo la visión original del proyecto, se han identificado los siguientes módulos para una etapa posterior de expansión:

1.  **Módulo de Logística y Distribución:** Gestión de flota de vehículos, asignación de conductores y seguimiento de estados de entrega (En tránsito / Entregado).
2.  **Gestión de Crédito Comercial:** Automatización de límites de crédito por cliente y bloqueo automático de ventas para cuentas con saldos vencidos.
3.  **Flujo de Aprobación Jerárquica:** Implementar estados de "Borrador" y "Autorización Gerencial" para órdenes de compra antes de su ingreso al inventario.
4.  **Seguridad de Acceso Proactiva:** Implementación de bloqueo temporal de cuentas tras intentos fallidos de inicio de sesión.
5.  **Automatización de Respaldos:** Sistema de copias de seguridad programadas y exportación automática a servicios de almacenamiento externo.
