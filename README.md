# LPDB-AI-ORDERING

API REST para la gestión de pedidos, desarrollada con FastAPI, SQLAlchemy y PostgreSQL.

## Tecnologías

- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- Pytest
- Uvicorn

## Funcionalidades

La API permite:

- Crear pedidos
- Consultar todos los pedidos
- Consultar un pedido por ID
- Actualizar un pedido
- Eliminar un pedido
- Validar los datos de entrada
- Manejar errores HTTP

## Estructura del proyecto

```text
LPDB-AI-ORDERING/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   └── services/
├── tests/
├── .gitignore
├── requirements.txt
└── README.md