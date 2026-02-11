# 🚨 Gestiones SOS

Sistema de gestión y seguimiento de siniestros con análisis de pagos y reportes estadísticos.

## 📋 Descripción

Aplicación web desarrollada con NiceGUI para la gestión integral de siniestros, permitiendo el registro, seguimiento y análisis de gestiones, pagos y documentación asociada. Incluye módulos de reportes con visualizaciones interactivas utilizando Plotly.

## ✨ Características

- **Gestión de Siniestros**: Registro y seguimiento de gestiones con toda la información relevante
- **Gestión de Pagos**: Control de pagos con diferentes formas de pago, pagadores y destinatarios
- **Gestión de Períodos**: Control de períodos activos para reportes y cálculos
- **Reportes y Estadísticas**: 
  - Análisis por forma de pago
  - Análisis por pagador y destinatario
  - Comparaciones específicas (SM como pagador vs destinatario)
  - Gráficos interactivos con Plotly
  - Tarjetas de estadísticas generales
- **Gestión de Documentos**: Sistema de carga y vinculación de documentos
- **Importación desde Excel**: Carga masiva de gestiones desde archivos Excel
- **Migración desde Access**: Herramienta de migración desde bases de datos Access

## 🛠️ Tecnologías

- **Framework Web**: [NiceGUI](https://nicegui.io/) 3.6+
- **Base de Datos**: SQLite
- **Procesamiento de Datos**: [Polars](https://pola.rs/) 1.37+
- **Visualizaciones**: [Plotly](https://plotly.com/python/) 6.5+
- **Conectividad DB**: PyODBC (para migración desde Access)
- **Excel**: OpenPyXL, FastExcel
- **Validación**: Pydantic 2.12+

## 📦 Instalación

### Requisitos Previos

- Python 3.12 o superior
- [uv](https://docs.astral.sh/uv/) (gestor de paquetes y entornos)

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd sos_g
   ```

2. **Instalar dependencias con uv**
   ```bash
   uv sync
   ```

3. **Configurar la base de datos**
   
   La primera vez que ejecutes la aplicación, se creará automáticamente la base de datos SQLite. Si necesitas migrar datos desde Access:
   
   ```bash
   uv run migrar.py
   ```

## 🚀 Uso

### Iniciar la aplicación

```bash
uv run main.py
```

La aplicación estará disponible en: `http://localhost:8080`

### Estructura de la Aplicación

```
sos_g/
├── main.py              # Punto de entrada de la aplicación
├── migrar.py            # Script de migración desde Access
├── db.accdb             # Base de datos Access (origen)
├── pyproject.toml       # Configuración del proyecto
├── sql/
│   └── create.sql       # Script de creación de tablas SQLite
├── files/
│   └── docs/            # Documentos adjuntos
└── src/
    ├── config.py        # Configuración general
    ├── commons.py       # Utilidades comunes
    ├── state.py         # Estado global de la app
    ├── db/              # Capa de base de datos
    │   ├── connection.py
    │   └── database.py
    ├── pages/           # Páginas de la aplicación
    │   ├── gestiones.py
    │   ├── pagos.py
    │   ├── periodos.py
    │   └── reportes.py
    └── components/      # Componentes reutilizables
        ├── navbar.py
        ├── dialog_gestion.py
        ├── dialog_pago.py
        └── documentos_gestion.py
```

## 📊 Módulos Principales

### Gestiones
- Visualización de gestiones en tabla
- Filtrado por diferentes criterios
- Edición de gestiones existentes
- Gestión de documentos adjuntos
- Importación masiva desde Excel

### Pagos
- Registro de pagos asociados a gestiones
- Control de formas de pago
- Gestión de pagadores y destinatarios
- Visualización y filtrado de pagos

### Períodos
- Control de períodos activos
- Activación/desactivación de períodos
- Afecta filtros y reportes

### Reportes
- **Tarjetas de Estadísticas**: Gestiones activas, total de pagos, importe total
- **Análisis por Forma de Pago**: Gráficos de importes y cantidad de pagos por mes
- **Análisis por Agentes**: Comparación de pagadores y destinatarios
- **Comparación SM**: Análisis específico de SM como pagador vs destinatario
- Datos agrupados por año y mes usando Polars
- Gráficos interactivos con Plotly

## 🗃️ Base de Datos

### Tablas Principales

- `gestiones`: Registro de siniestros con toda la información
- `pagos`: Pagos asociados a gestiones
- `formaspago`: Catálogo de formas de pago
- `agentes`: Pagadores y destinatarios
- `periodos`: Control de períodos activos
- `documentos`: Documentos adjuntos a gestiones

## 🎨 Interfaz

- Tema oscuro por defecto
- Diseño responsive con Tailwind CSS
- Colores personalizados:
  - Primary: `#dc2656` (Rojo)
  - Secondary: `#ea580c` (Naranja)
  - Accent: `#fbbf24` (Amarillo)

## 🔧 Desarrollo

### Instalar dependencias de desarrollo

```bash
uv sync --group dev
```

### Herramientas de desarrollo

- **Ruff**: Linter y formatter
- **IPyKernel**: Para notebooks Jupyter

### Ejecutar en modo desarrollo

```bash
uv run main.py
```

El modo `reload=True` está activado, por lo que los cambios se recargan automáticamente.

## 📝 Notas

- La base de datos SQLite se crea automáticamente en `sos.db`
- Los documentos se almacenan en `files/docs/`
- La aplicación usa hot-reload para desarrollo
- Puerto por defecto: 8080

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es privado y de uso interno.

## 👥 Autores

- Desarrollo inicial - Sistema de Gestión de Siniestros

## 🐛 Reporte de Bugs

Si encuentras algún bug o tienes sugerencias, por favor abre un issue en el repositorio.