# IVVI - Sistema de Gestión de Aceite de Palma 🌿

Bienvenido a la documentación oficial del sistema **IVVI**, una plataforma administrativa de alto nivel diseñada para automatizar y centralizar la gestión de compras, ventas e inventario.

## 📂 Estructura de Documentación Maestra (6 Volúmenes)
Para la defensa técnica y auditoría del sistema, se ha generado una suite documental de alto nivel académico:

1.  **[V1: Distribución del Sistema](./documentacion/1.md)**: Arquitectura de capas y estructura modular.
2.  **[V2: Principios SOLID](./documentacion/2.md)**: Implementación técnica de los 5 principios.
3.  **[V3: Ingeniería de Software](./documentacion/3.md)**: Ciclo de vida (SDLC) y justificación industrial.
4.  **[V4: Base de Datos](./documentacion/4.md)**: Modelado relacional y explicación técnica/natural.
5.  **[V5: Pruebas Unitarias](./documentacion/5.md)**: Estrategia de QA y matriz de 7 escenarios críticos.
6.  **[V6: Seguridad y Auditoría](./documentacion/6.md)**: Control de acceso (RBAC) y trazabilidad forense.

---

## 🚀 Guía de Inicio Rápido

### Requisitos Previos
- Python 3.8 o superior instalado.
- Administrador de paquetes `pip`.

### Instalación
1. Clona o descarga el repositorio en tu máquina local.
2. Abre una terminal en la carpeta raíz del proyecto.
3. Instala las dependencias necesarias:
   ```bash
   pip install flask flask-sqlalchemy reportlab openpyxl
   ```

### Ejecución
Para iniciar el servidor de desarrollo, ejecuta:
```bash
python app.py
```
El sistema estará disponible en tu navegador en la dirección: `http://127.0.0.1:5000`

---

## 🛠️ Stack Tecnológico
- **Lenguaje:** Python 3.x
- **Framework Web:** Flask (Micro-framework)
- **Base de Datos:** SQLite con SQLAlchemy (ORM)
- **Documentos:** ReportLab (PDF) y OpenPyXL (Excel)
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla) + Chart.js

## 🛡️ Aseguramiento de Calidad (Pruebas)
El sistema incluye una suite de pruebas unitarias para validar la lógica de negocio. Para ejecutarlas:
```bash
python -m unittest tests/test_ivvi.py
```

---

*Desarrollado para Inversiones IVVI S.A. - Transformación Digital del Agro.*
