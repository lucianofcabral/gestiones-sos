# HACER

## Todas las tablas

- Consistencia de estilos: Donde haya ícono de elimnar/inactivar o editar usar siempre el mismo íscono.

## Grupos

- Mostrar La fecha de creación en cada fila (puede ayudar)
- Filtros
  - Texto que filtre x nombre de grupo
  - Fecha
- Falta Agregar documentos
- Agregar Gestión de la lista de Grouped Claims (mostrar tabla y poder selccionar varias para agregar al grupo).
- Al Eliminar una gestión de un grupo se debe poder elegir entre dos caminos:
  1. Crear automáticamente un grupo nuevo para esta gestión con los mismos documentos asociados y por nombre la fecha en formato ISO, Dominio, Poliza, Cliente.
  2. Permitir asociar a un grupo distinto ya existente seleccionándolo de la tabla de grupos y obviamente se debe poder filtrar para buscar el correcto.

## Facturas

- Agregar un campo que sea una descripción tanto a la base de datos como al modelo y que pueda ser NULL.
- Poder agregar documento
- Cambiar la page completamente, parece más un dialog (créalo como dialog que se pueda llamar desde distintas pages).
- La page debe mostrar un listado de las facturas con los filtros de periodo, fecha y descripción
- Cada fila se debe poder inactivar y seleccionar para editar a través del dialog.  

## Período

- Sacar el botón de **AGREGAR** periodo porque ta estñan generados
- Sólo mostrar los periodos del mes correinte o anteriores
- Sacar la posibilidad de eliminar periodos en cada fila
- En lugar de una tabla, mostrar un card por cada uno Donde se vea El mes, las facturas en forma de items con su número, descripción e importe y la cantidad de notas de crédito con la suma mtotal de los importes de las notas de crédito.
- Al seleccionar uno se podrá agregar facturas y ver dos tablas:
  1. Facturas: Se podrá agregar Facturas, inactivarlas o editarlas en un diálogo aparte.
  2. Notas de crédito (Se desasociará del período)

## Nueva Gestión

- Debe dejar de ser una page y pasar a ser un dialog.

## Importar Gestiones

- Debe dejar de ser una page y pasar a ser un dialog.

## Gestión

- Filtros:
  - Tipo
  - Texto para Cliente, dominio, nro gestion, poliza
  - Tiene pagos
  - No tiene pagos
  - Tiene nota de credito
  - No Tiene nota de credito
  - Resuelta
- Agregar botón de agregar gestión que abra el dialgo de nueva gestión
- Agregar botón de importar gestiones que abra el dialgo de importar gestiones


## General

- Permitir ordenar en todas las tablas
