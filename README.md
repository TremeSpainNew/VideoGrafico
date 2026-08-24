# VideoGrafico

Base en Python para trabajar con videográficos ferroviarios separando dos usos:

- `editor`: creación y edición de esquemas videográficos.
- `runtime`: explotación del videográfico, visualización de estados y simulación operativa.

## Requisitos

- Python `3.14+`
- `tkinter` disponible en el sistema

## Ejecución

Editor:

```bash
python3 -m videografico.editor
```

Explotación:

```bash
python3 -m videografico.runtime
```

## Proyecto de ejemplo

Ambas aplicaciones cargan por defecto:

`data/nas816_demo.json`

## Estructura

- `videografico/model.py`: modelo de datos del videográfico
- `videografico/storage.py`: carga y guardado JSON
- `videografico/render.py`: renderizado sobre canvas
- `videografico/editor.py`: aplicación de edición
- `videografico/runtime.py`: aplicación de explotación

## Estado actual

Esta primera base permite:

- definir un esquema con fondo, tamaño y elementos
- editar posición, texto y estado de los elementos
- guardar y cargar proyectos JSON
- reutilizar el mismo render en editor y explotación
- cambiar estados en la app de explotación para simular operación

## Siguiente evolución razonable

- capas configurables según NAS 816
- catálogo ampliado de símbolos ferroviarios
- zoom y paneo
- validaciones operativas
- conexión con datos reales o simulados de enclavamiento
