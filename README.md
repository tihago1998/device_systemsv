# device_systems

API REST para la gestión de usuarios, dispositivos tecnológicos y préstamos del sistema **device_systems**, desarrollada con **FastAPI**, **SQLAlchemy** y **Alembic**.

Proyecto desarrollado para las actividades del programa ADSO - SENA:

| Actividad                          | Versión | Contenido                                                         |
| ---------------------------------- | ------- | ----------------------------------------------------------------- |
| GA1-220501096-01-AA1-EV07          | 1.0.0   | FastAPI básico: GET, POST y modelos Pydantic                      |
| GA1-220501096-01-AA1-EV08          | 2.0.0   | CRUD completo, manejo de errores, Swagger/OpenAPI y `Depends()`   |
| GA1-220501096-01-AA1-EV09          | 3.0.0   | Persistencia en base de datos con SQLAlchemy y SQLite             |
| GA1-220501096-01-AA1-EV10          | 4.0.0   | Migraciones con Alembic, relaciones entre modelos y consultas con joins |

La versión 4.0.0 se desarrolló en la rama **`device_systems_alembic_relaciones`**, unificada con `main`.

## Descripción

`device_systems` es una API REST para administrar el préstamo de equipos tecnológicos:

- **Usuarios** (`/users`): CRUD, filtros por rol, estado y texto, y consulta de sus préstamos y dispositivos asignados.
- **Dispositivos** (`/devices`): CRUD de laptops, tablets, proyectores, cámaras, routers y monitores, con filtros por tipo, disponibilidad, marca y búsqueda.
- **Préstamos** (`/loans`): prestar un dispositivo a un usuario, devolverlo y consultar préstamos con la información del usuario y del dispositivo (joins), con filtros por estado, usuario, dispositivo, correo, tipo y fechas.

Los datos se guardan en una **base de datos SQLite** (`device_systems.db`) mediante el ORM **SQLAlchemy**, y la estructura de la base de datos se versiona con **migraciones de Alembic**. La API aplica validaciones con Pydantic, constraints e integridad referencial en la base de datos, reglas de negocio (no prestar un equipo ocupado, no devolver dos veces), manejo de errores con `HTTPException` e inyección de dependencias con `Depends()`.

## Tecnologías utilizadas

- Python 3.14
- FastAPI
- Uvicorn
- Pydantic v2 (+ email-validator)
- SQLAlchemy 2
- Alembic
- SQLite

## Instalación de dependencias

```bash
python -m venv venv
venv\Scripts\activate        # Windows (en Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
```

## Crear la base de datos (migraciones)

La aplicación ya no crea las tablas al iniciar: la estructura se aplica con Alembic. Antes de ejecutar el servidor por primera vez:

```bash
alembic upgrade head
```

Esto crea `device_systems.db` con las tablas `users`, `devices`, `loans` y `alembic_version`. El archivo `.db` no se sube al repositorio (está en `.gitignore`).

## Ejecución del servidor

```bash
uvicorn app.main:app --reload
```

La API queda disponible en `http://localhost:8000`, con documentación interactiva en:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Estructura del proyecto

```
device_systemsv/
│── app/
│   │── main.py
│   │── database/
│   │   └── connection.py
│   │── models/
│   │   │── user_model.py
│   │   │── device_model.py
│   │   └── loan_model.py
│   │── schemas/
│   │   │── user_schema.py
│   │   │── device_schema.py
│   │   └── loan_schema.py
│   │── routes/
│   │   │── user_routes.py
│   │   │── device_routes.py
│   │   └── loan_routes.py
│   │── services/
│   │   │── user_service.py
│   │   │── device_service.py
│   │   └── loan_service.py
│   │── dependencies/
│   │   │── database_dependency.py
│   │   │── user_dependencies.py
│   │   │── device_dependencies.py
│   │   └── loan_dependencies.py
│── alembic/
│   │── env.py
│   └── versions/
│       │── 78ad4166a2e4_create_users_table.py
│       └── 46413d96466f_create_devices_and_loans_tables.py
│── alembic.ini
│── images/            (capturas de las pruebas)
│── requirements.txt
│── README.md
```

| Carpeta        | Responsabilidad                                                          |
| -------------- | ------------------------------------------------------------------------ |
| `database`     | Conexión a la base de datos: engine, `SessionLocal` y `Base`             |
| `models`       | Modelos SQLAlchemy: cómo se guardan los datos (tablas, columnas y relaciones) |
| `schemas`      | Modelos Pydantic: qué datos entran y salen de la API                     |
| `routes`       | Definición de endpoints                                                  |
| `services`     | Lógica de negocio, operaciones CRUD y consultas con joins                |
| `dependencies` | Funciones reutilizables inyectadas con `Depends()` (sesión de BD, buscar usuario/dispositivo/préstamo o 404, rol) |
| `alembic`      | Configuración de migraciones y scripts de cada versión de la base de datos |

## Migraciones con Alembic

Alembic guarda cada cambio en la estructura de la base de datos como un script en `alembic/versions/`, y registra en la tabla `alembic_version` cuál es la versión aplicada. Así los cambios quedan versionados en Git junto con el código y se aplican igual en cualquier computador.

### Configuración

- `alembic init alembic` creó la carpeta `alembic/` y el archivo `alembic.ini`.
- `alembic/env.py` usa la misma URL de la aplicación (`DATABASE_URL` de `app/database/connection.py`) y `Base.metadata`, e importa `app.models` para que Alembic conozca `User`, `Device` y `Loan`.
- `render_as_batch=True`: SQLite no soporta todos los `ALTER TABLE`, así que Alembic recrea la tabla cuando hace falta.
- `app/main.py` ya **no** usa `Base.metadata.create_all`: las tablas solo se crean con migraciones.

### Historial de migraciones

| Revisión       | Descripción                          | Cambios                                                        |
| -------------- | ------------------------------------ | -------------------------------------------------------------- |
| `78ad4166a2e4` | create users table                   | Tabla `users` (la BD existente de EV09 se marcó con `alembic stamp`) |
| `46413d96466f` | create devices and loans tables      | Tablas `devices` y `loans`, llaves foráneas, índices y `CHECK` de estado |

### Comandos usados

```bash
alembic init alembic                                              # inicializar Alembic
alembic revision --autogenerate -m "create devices and loans tables"  # generar migración comparando modelos y BD
alembic upgrade head                                              # aplicar migraciones pendientes
alembic history                                                   # ver historial de migraciones
alembic current                                                   # ver versión aplicada
alembic downgrade -1                                              # revertir la última migración
```

**Errores al aplicar migraciones:** si una migración falla, Alembic detiene el proceso y no actualiza `alembic_version`, por lo que la base de datos queda en la última versión correcta. Se corrige el script y se vuelve a ejecutar `alembic upgrade head`; si hace falta deshacer un cambio ya aplicado se usa `alembic downgrade -1`. Antes de generar la migración de `devices` y `loans` se verificó con `alembic check` que solo se detectaran esas dos tablas nuevas.

## Base de datos con SQLAlchemy

### Conexión (`app/database/connection.py`)

- `DATABASE_URL = "sqlite:///./device_systems.db"`: base de datos SQLite en la raíz del proyecto.
- `engine`: objeto que se conecta a la base de datos.
- `SessionLocal`: fábrica de sesiones; cada petición abre su propia sesión.
- `Base`: clase base de la que heredan los modelos.
- `get_session()`: crea una sesión nueva.

- `PRAGMA foreign_keys=ON`: SQLite no valida las llaves foráneas por defecto; se activa en cada conexión para garantizar la integridad referencial (un préstamo no puede apuntar a un usuario o dispositivo inexistente).

La dependencia `get_db()` de `app/dependencies/database_dependency.py` usa `yield` para entregar la sesión al endpoint y cerrarla siempre al terminar la petición, incluso si ocurre un error.

### Modelo `User` (`app/models/user_model.py`) → tabla `users`

| Campo        | Tipo          | Restricción                                        |
| ------------ | ------------- | -------------------------------------------------- |
| `id`         | Integer       | Primary Key, índice                                |
| `name`       | String(100)   | `nullable=False`                                   |
| `email`      | String(120)   | `unique=True`, `nullable=False`, índice            |
| `role`       | String(20)    | `nullable=False`, `CHECK role IN ('admin', 'support', 'user')` |
| `is_active`  | Boolean       | `nullable=False`, por defecto `True`               |
| `created_at` | DateTime      | `nullable=False`, por defecto la fecha actual (UTC) |

### Modelo `Device` (`app/models/device_model.py`) → tabla `devices`

| Campo           | Tipo        | Restricción                                  |
| --------------- | ----------- | -------------------------------------------- |
| `id`            | Integer     | Primary Key, índice                          |
| `name`          | String(100) | `nullable=False`                             |
| `serial_number` | String(50)  | `unique=True`, `nullable=False`, índice      |
| `device_type`   | String(30)  | `nullable=False`, índice (laptop, tablet, proyector, camara, router, monitor) |
| `brand`         | String(50)  | Opcional                                     |
| `is_available`  | Boolean     | `nullable=False`, por defecto `True`         |
| `created_at`    | DateTime    | `nullable=False`, fecha de creación          |

### Modelo `Loan` (`app/models/loan_model.py`) → tabla `loans`

| Campo         | Tipo       | Restricción                                              |
| ------------- | ---------- | -------------------------------------------------------- |
| `id`          | Integer    | Primary Key, índice                                      |
| `user_id`     | Integer    | `ForeignKey("users.id")`, `nullable=False`, índice       |
| `device_id`   | Integer    | `ForeignKey("devices.id")`, `nullable=False`, índice     |
| `loan_date`   | DateTime   | `nullable=False`, fecha del préstamo                     |
| `return_date` | DateTime   | Opcional (se llena al devolver)                          |
| `status`      | String(20) | `nullable=False`, `CHECK status IN ('active', 'returned', 'overdue')` |

### Asociaciones entre modelos

```
users 1 ──── * loans * ──── 1 devices
```

| Relación                      | Tipo          | Código                                                  |
| ----------------------------- | ------------- | ------------------------------------------------------- |
| Un usuario tiene muchos préstamos | One-to-Many | `User.loans = relationship("Loan", back_populates="user")` |
| Un dispositivo aparece en muchos préstamos históricos | One-to-Many | `Device.loans = relationship("Loan", back_populates="device")` |
| Cada préstamo pertenece a un usuario | Many-to-One | `Loan.user = relationship("User", back_populates="loans")` |
| Cada préstamo pertenece a un dispositivo | Many-to-One | `Loan.device = relationship("Device", back_populates="loans")` |

`back_populates` conecta las dos puntas de la relación: desde un préstamo se llega a `loan.user` y `loan.device`, y desde un usuario o dispositivo a su lista `loans`. Para conservar el historial, no se puede eliminar un usuario ni un dispositivo que tenga préstamos registrados (`409`).

### Modelo SQLAlchemy vs. schema Pydantic

| Modelo SQLAlchemy (`User`)                         | Schemas Pydantic (`UserCreate`, `UserUpdate`, `UserPatch`, `UserResponse`) |
| -------------------------------------------------- | -------------------------------------------------------------------------- |
| Define cómo se **guardan** los datos en la tabla   | Define qué datos **entran y salen** de la API                              |
| Constraints de base de datos (`unique`, `nullable`, `CHECK`) | Validaciones de entrada (mínimo 3 caracteres, formato de email, rol permitido) |
| Incluye `id` y `created_at`, que genera el sistema | `UserCreate`/`UserUpdate` no los reciben; `UserResponse` sí los devuelve   |

| Schema         | Uso                          | Campos                                                         |
| -------------- | ---------------------------- | -------------------------------------------------------------- |
| `UserCreate`   | POST (crear)                 | `name`, `email`, `role` obligatorios; `is_active` opcional (True) |
| `UserUpdate`   | PUT (actualización completa) | `name`, `email`, `role` e `is_active`, todos obligatorios      |
| `UserPatch`    | PATCH (actualización parcial)| Todos opcionales                                               |
| `UserResponse` | Respuesta                    | `id`, `name`, `email`, `role`, `is_active`, `created_at`       |

| Schema               | Uso                                        |
| -------------------- | ------------------------------------------ |
| `DeviceCreate`       | POST `/devices` (`is_available` opcional)  |
| `DeviceUpdate`       | PUT `/devices/{id}` (todos obligatorios)   |
| `DevicePatch`        | PATCH `/devices/{id}` (todos opcionales)   |
| `DeviceResponse`     | Respuesta de dispositivo                   |
| `LoanCreate`         | POST `/loans` (`user_id`, `device_id`)     |
| `LoanUpdate`         | PATCH `/loans/{id}` (cambiar estado a `active` u `overdue`) |
| `LoanResponse`       | Respuesta básica de préstamo (solo IDs)    |
| `LoanDetailResponse` | Préstamo con `user` y `device` anidados (resultado del join) |

Los schemas usan `model_config = ConfigDict(from_attributes=True)` para construirse directamente desde los objetos SQLAlchemy, y `json_schema_extra` con **ejemplos** que Swagger muestra en cada endpoint.

## Tabla de endpoints

### Users

| Operación                    | Método | Ruta                        | Código esperado            |
| ---------------------------- | ------ | --------------------------- | -------------------------- |
| Listar usuarios              | GET    | `/users/`                   | 200 OK / 400 (rol inválido)|
| Consultar usuario            | GET    | `/users/{user_id}`          | 200 OK / 404               |
| Préstamos de un usuario      | GET    | `/users/{user_id}/loans`    | 200 OK / 404               |
| Dispositivos asignados       | GET    | `/users/{user_id}/devices`  | 200 OK / 404               |
| Crear usuario                | POST   | `/users/`                   | 201 Created / 400 / 422    |
| Actualizar completo          | PUT    | `/users/{user_id}`          | 200 OK / 404 / 400 / 422   |
| Actualizar parcial           | PATCH  | `/users/{user_id}`          | 200 OK / 404 / 400 / 422   |
| Eliminar usuario             | DELETE | `/users/{user_id}`          | 204 No Content / 404 / 409 |

### Devices

| Operación                    | Método | Ruta                          | Código esperado                 |
| ---------------------------- | ------ | ----------------------------- | ------------------------------- |
| Listar dispositivos          | GET    | `/devices/`                   | 200 OK / 422 (filtro inválido)  |
| Consultar dispositivo        | GET    | `/devices/{device_id}`        | 200 OK / 404                    |
| Historial de préstamos       | GET    | `/devices/{device_id}/loans`  | 200 OK / 404                    |
| Registrar dispositivo        | POST   | `/devices/`                   | 201 Created / 400 / 422         |
| Actualizar completo          | PUT    | `/devices/{device_id}`        | 200 OK / 404 / 400 / 409 / 422  |
| Actualizar parcial           | PATCH  | `/devices/{device_id}`        | 200 OK / 404 / 400 / 409 / 422  |
| Eliminar dispositivo         | DELETE | `/devices/{device_id}`        | 204 No Content / 404 / 409      |

### Loans

| Operación                          | Método | Ruta                        | Código esperado                 |
| ---------------------------------- | ------ | --------------------------- | ------------------------------- |
| Listar préstamos                   | GET    | `/loans/`                   | 200 OK / 400 / 422              |
| Listar préstamos con usuario y dispositivo | GET | `/loans/details`       | 200 OK / 400 / 422              |
| Consultar préstamo                 | GET    | `/loans/{loan_id}`          | 200 OK / 404                    |
| Registrar préstamo                 | POST   | `/loans/`                   | 201 Created / 404 / 409 / 422   |
| Devolver dispositivo               | PATCH  | `/loans/{loan_id}/return`   | 200 OK / 404 / 409              |
| Cambiar estado (active/overdue)    | PATCH  | `/loans/{loan_id}`          | 200 OK / 404 / 409 / 422        |

### Root

| Operación        | Método | Ruta    | Código esperado |
| ---------------- | ------ | ------- | --------------- |
| Estado de la API | GET    | `/`     | 200 OK          |
| Información API  | GET    | `/info` | 200 OK          |

### Reglas de negocio de préstamos

- **POST `/loans`** valida que el usuario exista (404) y esté activo (409), que el dispositivo exista (404) y que esté disponible (409). Crea el préstamo con estado `active` y cambia `is_available` del dispositivo a `false` en la misma transacción.
- **PATCH `/loans/{loan_id}/return`** valida que el préstamo exista (404) y que no esté ya devuelto (409). Lo marca `returned`, asigna `return_date` y cambia `is_available` del dispositivo a `true`.
- Un dispositivo con préstamo activo no se puede marcar a mano como disponible con PUT/PATCH (409): se libera al registrar la devolución.

### Consultas con joins y filtros

Las consultas de préstamos (`loan_service.list_loans`) unen las tres tablas:

```python
select(Loan)
    .join(Loan.user)
    .join(Loan.device)
    .options(contains_eager(Loan.user), contains_eager(Loan.device))
    .where(and_(*condiciones))
```

Cada filtro opcional agrega una condición: `Loan.status == ...`, `func.lower(User.email) == ...`, `Device.device_type == ...`, rango de `Loan.loan_date`, y una búsqueda con `or_(User.name.ilike(...), User.email.ilike(...), Device.name.ilike(...), Device.serial_number.ilike(...))`. `contains_eager` reutiliza el mismo join para cargar el usuario y el dispositivo de cada préstamo sin hacer consultas adicionales. `GET /users/{user_id}/devices` usa un join de `devices` con `loans` y `in_(["active", "overdue"])` para obtener los equipos que el usuario tiene prestados.

Parámetros de consulta de `GET /loans/` y `GET /loans/details`:

| Parámetro     | Valores / tipo                          | Ejemplo                                           |
| ------------- | --------------------------------------- | ------------------------------------------------- |
| `status`      | `active`, `returned`, `overdue`         | `/loans/details?status=active`                    |
| `user_id`     | entero                                  | `/loans/details?user_id=6`                        |
| `device_id`   | entero                                  | `/loans/details?device_id=3`                      |
| `user_email`  | correo (sin distinguir mayúsculas)      | `/loans/details?user_email=aprendiz@sena.edu.co`  |
| `device_type` | laptop, tablet, proyector, camara, router, monitor | `/loans/details?device_type=laptop`    |
| `date_from`   | fecha `AAAA-MM-DD`                      | `/loans/details?date_from=2026-09-01`             |
| `date_to`     | fecha `AAAA-MM-DD` (inclusive)          | `/loans/details?date_to=2026-09-30`               |
| `search`      | texto en nombre/correo del usuario o nombre/serial del equipo | `/loans/details?search=lenovo` |
| `order`       | `asc`, `desc` (por fecha de préstamo)   | `/loans/details?order=asc`                        |
| `skip`, `limit` | paginación                            | `/loans/details?limit=10`                         |

Parámetros de consulta de `GET /devices/`:

| Parámetro      | Valores                                   | Ejemplo                          |
| -------------- | ----------------------------------------- | -------------------------------- |
| `device_type`  | laptop, tablet, proyector, camara, router, monitor | `/devices/?device_type=laptop` |
| `is_available` | `true`, `false`                           | `/devices/?is_available=true`    |
| `brand`        | texto (sin distinguir mayúsculas)         | `/devices/?brand=lenovo`         |
| `search`       | texto en nombre, serial o marca (`ilike`) | `/devices/?search=thinkpad`      |
| `order_by`, `order`, `skip`, `limit` | orden y paginación  | `/devices/?order_by=name`        |

Parámetros de consulta de `GET /users/` (se pueden combinar):

| Parámetro   | Valores                         | Por defecto | Ejemplo                                  |
| ----------- | ------------------------------- | ----------- | ---------------------------------------- |
| `role`      | `admin`, `support`, `user`      | —           | `/users/?role=support`                   |
| `is_active` | `true`, `false`                 | —           | `/users/?is_active=true`                 |
| `search`    | texto en nombre o correo        | —           | `/users/?search=sena`                    |
| `order_by`  | `id`, `name`, `created_at`      | `id`        | `/users/?order_by=name`                  |
| `order`     | `asc`, `desc`                   | `asc`       | `/users/?order_by=created_at&order=desc` |
| `skip`      | entero ≥ 0                      | `0`         | `/users/?skip=10`                        |
| `limit`     | entero entre 1 y 100            | `100`       | `/users/?limit=5`                        |

## Ejemplos de peticiones y respuestas

### Dispositivos y préstamos (EV10)

**POST /devices/** → `201 Created`

```json
{
  "name": "Laptop Lenovo ThinkPad",
  "serial_number": "LEN-2024-001",
  "device_type": "laptop",
  "brand": "Lenovo"
}
```

**POST /loans/** → `201 Created`

```json
{
  "user_id": 6,
  "device_id": 3
}
```

Respuesta (`LoanDetailResponse`, con la información relacionada del join):

```json
{
  "loan_id": 1,
  "status": "active",
  "loan_date": "2026-09-26T02:31:55.443825",
  "return_date": null,
  "user": {
    "id": 6,
    "name": "Aprendiz SENA",
    "email": "aprendiz@sena.edu.co"
  },
  "device": {
    "id": 3,
    "name": "Laptop Lenovo ThinkPad",
    "serial_number": "LEN-2024-001",
    "device_type": "laptop"
  }
}
```

**POST /loans/** con un dispositivo ya prestado → `409 Conflict`

```json
{
  "detail": "El dispositivo no está disponible para préstamo"
}
```

**PATCH /loans/1/return** → `200 OK`: el préstamo queda con `"status": "returned"` y `"return_date": "2026-09-26T02:47:21.688916"`, y el dispositivo vuelve a `"is_available": true`.

**PATCH /loans/1/return** otra vez → `409 Conflict`

```json
{
  "detail": "El préstamo ya fue devuelto"
}
```

### Usuarios

**POST /users/** → `201 Created`

```json
{
  "name": "Carlos Ruiz",
  "email": "carlos@device.com",
  "role": "user",
  "is_active": true
}
```

Respuesta:

```json
{
  "name": "Carlos Ruiz",
  "email": "carlos@device.com",
  "role": "user",
  "id": 3,
  "is_active": true,
  "created_at": "2026-09-25T23:04:04.745210"
}
```

**PUT /users/2** → `200 OK`

```json
{
  "name": "Luis Pérez",
  "email": "luis2@device.com",
  "role": "support",
  "is_active": true
}
```

Respuesta:

```json
{
  "name": "Luis Pérez",
  "email": "luis2@device.com",
  "role": "support",
  "id": 2,
  "is_active": true,
  "created_at": "2026-09-25T23:04:04.719399"
}
```

**PATCH /users/1** → `200 OK`

```json
{
  "role": "support"
}
```

Respuesta:

```json
{
  "name": "Ana Torres",
  "email": "ana@device.com",
  "role": "support",
  "id": 1,
  "is_active": true,
  "created_at": "2026-09-25T23:04:04.700822"
}
```

**DELETE /users/3** → `204 No Content` (sin cuerpo de respuesta)

**GET /users/999** → `404 Not Found`

```json
{
  "detail": "Usuario no encontrado"
}
```

**GET /users/?role=hacker** → `400 Bad Request`

```json
{
  "detail": "Rol no permitido. Debe ser uno de: admin, support, user"
}
```

## Códigos de estado usados

| Caso                         | Código                     |
| ---------------------------- | -------------------------- |
| Registro creado              | `201 Created`              |
| Consulta exitosa             | `200 OK`                   |
| Actualización / devolución exitosa | `200 OK`             |
| Eliminación exitosa          | `204 No Content`           |
| Recurso no encontrado        | `404 Not Found`            |
| Dato duplicado, PATCH sin campos, rol no permitido, rango de fechas inválido | `400 Bad Request` |
| Regla de negocio incumplida  | `409 Conflict`             |
| Error de validación (datos o filtros con valores no permitidos) | `422 Unprocessable Entity` |

## Uso de Depends()

Las dependencias están en `app/dependencies/` y se inyectan en las rutas con `Depends()`:

| Dependencia               | Archivo                  | Dónde se usa                                           | Qué hace                                                            |
| ------------------------- | ------------------------ | ------------------------------------------------------ | ------------------------------------------------------------------- |
| `get_db`                  | `database_dependency.py` | Todos los endpoints de `/users`, `/devices` y `/loans` | Abre una sesión de base de datos por petición y la cierra al final  |
| `get_user_or_404`         | `user_dependencies.py`   | Endpoints de `/users/{user_id}` (incluye `/loans` y `/devices`) | Busca el usuario en la base de datos y lanza `404` si no existe |
| `get_device_or_404`       | `device_dependencies.py` | Endpoints de `/devices/{device_id}` (incluye `/loans`) | Busca el dispositivo y lanza `404` si no existe                     |
| `get_loan_or_404`         | `loan_dependencies.py`   | `GET /loans/{loan_id}`, `PATCH /loans/{loan_id}` y `/return` | Busca el préstamo y lanza `404` si no existe                   |
| `LoanFilters`             | `loan_routes.py`         | `GET /loans/` y `GET /loans/details`                   | Agrupa los parámetros de filtro compartidos por los dos endpoints  |
| `validar_rol`             | `user_dependencies.py`   | `GET /users/` (filtro `role`)                          | Lanza `400` si el rol no es `admin`, `support` o `user`             |
| `get_api_info`            | `user_dependencies.py`   | `GET /info`                                            | Entrega la configuración general de la API (nombre, versión y BD)   |
| `verificar_autenticacion` | `user_dependencies.py`   | Disponible para proteger rutas                         | Simula autenticación con la cabecera `x-token: secreto123`          |

Las dependencias también pueden depender de otras: `get_user_or_404` recibe la sesión de `get_db` para consultar el usuario. Así, la búsqueda del usuario y el error `404` se escriben una sola vez y se reutilizan en los cuatro endpoints que reciben `user_id`, y los servicios reciben directamente el usuario ya validado.

## Manejo de errores

Todos los errores de negocio se manejan con `HTTPException`, devolviendo respuestas JSON consistentes con la estructura `{"detail": "mensaje del error"}`:

| Situación                         | Código | Mensaje                                         |
| --------------------------------- | ------ | ----------------------------------------------- |
| Usuario no encontrado             | 404    | `Usuario no encontrado`                         |
| Actualización de usuario inexistente (PUT/PATCH) | 404 | `Usuario no encontrado`          |
| Eliminación de usuario inexistente| 404    | `Usuario no encontrado`                         |
| Correo electrónico duplicado      | 400    | `El correo ya está registrado`                  |
| Rol no permitido (filtro)         | 400    | `Rol no permitido. Debe ser uno de: ...`        |
| Actualización (PATCH) sin datos   | 400    | `No se enviaron campos para actualizar`         |
| Dispositivo inexistente           | 404    | `Dispositivo no encontrado`                     |
| Préstamo inexistente              | 404    | `Préstamo no encontrado`                        |
| Número de serie duplicado         | 400    | `El número de serie ya está registrado`         |
| Dispositivo no disponible         | 409    | `El dispositivo no está disponible para préstamo` |
| Usuario inactivo pide un préstamo | 409    | `El usuario está inactivo y no puede recibir préstamos` |
| Devolver un préstamo ya devuelto  | 409    | `El préstamo ya fue devuelto`                   |
| Cambiar estado de un préstamo devuelto | 409 | `No se puede cambiar el estado de un préstamo ya devuelto` |
| Liberar a mano un equipo prestado | 409    | `El dispositivo tiene un préstamo activo; se libera al registrar la devolución` |
| Eliminar usuario o dispositivo con préstamos | 409 | `No se puede eliminar ... con préstamos registrados` |
| Filtro con valor no permitido (`status`, `device_type`, fecha mal escrita) | 422 | Detalle de validación de FastAPI |
| `date_from` mayor que `date_to`   | 400    | `Filtro inválido: date_from no puede ser mayor que date_to` |
| Error al aplicar migraciones      | —      | Alembic detiene la migración y no cambia `alembic_version` (ver *Migraciones con Alembic*) |

Los errores de validación de datos (`422`) son generados automáticamente por Pydantic a partir de las reglas definidas en los modelos: longitud mínima del nombre, formato de email y valores permitidos de rol al crear o actualizar. En PATCH, los campos enviados como `null` se ignoran, por lo que un cuerpo como `{"name": null}` se trata como una actualización sin datos (`400`).

El correo duplicado se controla en dos niveles: el servicio consulta primero si el email ya existe (`get_user_by_email`) y, como respaldo, si la base de datos rechaza el registro por el constraint `unique` (`IntegrityError`), se hace `rollback` y se responde igualmente `400`. El rol también está protegido en la base de datos con un `CHECK`, además de la validación de Pydantic.

## Pruebas funcionales (EV10)

| #  | Escenario de la guía                             | Petición                                     | Resultado                                       |
| -- | ------------------------------------------------ | -------------------------------------------- | ----------------------------------------------- |
| 1  | Ejecutar migraciones con Alembic                 | `alembic upgrade head`                       | Tablas `devices` y `loans` creadas              |
| 2  | Crear usuario                                    | `POST /users/`                               | `201 Created`                                   |
| 3  | Crear dispositivo                                | `POST /devices/`                             | `201 Created`                                   |
| 4  | Crear préstamo                                   | `POST /loans/`                               | `201 Created`, dispositivo pasa a no disponible |
| 5  | Prestar un dispositivo no disponible             | `POST /loans/`                               | `409 Conflict`                                  |
| 6  | Listar préstamos con usuario y dispositivo       | `GET /loans/details`                         | `200 OK` (join)                                 |
| 7  | Filtrar préstamos por estado                     | `GET /loans/details?status=active`           | `200 OK`                                        |
| 8  | Filtrar préstamos por tipo de dispositivo        | `GET /loans/details?device_type=laptop`      | `200 OK`, solo préstamos de laptops             |
| 9  | Consultar préstamos de un usuario                | `GET /users/6/loans`                         | `200 OK`                                        |
| 10 | Devolver un dispositivo                          | `PATCH /loans/1/return`                      | `200 OK`, `returned` con `return_date`          |
| 11 | Validar que el dispositivo vuelva a estar disponible | `GET /devices/3`                         | `200 OK`, `is_available: true`                  |
| 12 | Consultar historial de préstamos del dispositivo | `GET /devices/3/loans`                       | `200 OK`                                        |

Además se probaron los errores: usuario, dispositivo y préstamo inexistentes (`404`), usuario inactivo (`409`), devolver dos veces (`409`), serial duplicado (`400`), filtros con valores no permitidos (`422`), rango de fechas invertido (`400`), eliminar usuario o dispositivo con préstamos (`409`) y el rechazo de la base de datos a un préstamo con `user_id` inexistente (llave foránea).

## Evidencia de pruebas (EV10)

### Alembic: `alembic init alembic`

![alembic init](images/ev10_01_alembic_init.png)

### Alembic: `alembic revision --autogenerate -m "create devices and loans tables"`

![alembic revision](images/ev10_02_alembic_revision.png)

### Alembic: `alembic upgrade head`

![alembic upgrade](images/ev10_03_alembic_upgrade.png)

### Alembic: `alembic history`

![alembic history](images/ev10_04_alembic_history.png)

### Estructura de tablas generadas (SQLite Viewer)

![Tablas generadas](images/ev10_05_tablas_generadas.png)

### Swagger UI organizado por tags (Users, Devices, Loans)

![Swagger tags](images/ev10_06_swagger_tags.png)

### Crear usuario → 201

![Crear usuario](images/ev10_07_crear_usuario_201.png)

### Crear dispositivo → 201

![Crear dispositivo](images/ev10_08_crear_dispositivo_201.png)

### Crear préstamo → 201

![Crear préstamo](images/ev10_09_crear_prestamo_201.png)

### Prestar un dispositivo no disponible → 409

![Préstamo no disponible](images/ev10_10_prestamo_no_disponible_409.png)

### Consulta con join: préstamos con usuario y dispositivo → 200

![Loans details](images/ev10_11_loans_details_join.png)

### Filtro por estado → 200

![Filtro estado](images/ev10_12_filtro_estado_200.png)

### Filtro por tipo de dispositivo → 200

![Filtro tipo](images/ev10_13_filtro_tipo_200.png)

### Préstamos de un usuario → 200

![Préstamos de usuario](images/ev10_14_prestamos_usuario_200.png)

### Devolución del dispositivo → 200

![Devolución](images/ev10_15_devolucion_200.png)

### El dispositivo vuelve a estar disponible → 200

![Dispositivo disponible](images/ev10_16_dispositivo_disponible_200.png)

### Historial de préstamos del dispositivo → 200

![Historial dispositivo](images/ev10_17_historial_dispositivo_200.png)

## Pruebas funcionales (EV09)

Pruebas mínimas de la guía, ejecutadas sobre una base de datos nueva con tres usuarios de ejemplo (Ana, Luis y Beatriz):

| #  | Prueba                                   | Petición                                  | Resultado                                   |
| -- | ---------------------------------------- | ----------------------------------------- | ------------------------------------------- |
| 1  | Crear un usuario válido                  | `POST /users/`                            | `201 Created`, con `id` y `created_at`      |
| 2  | Crear usuario con email repetido         | `POST /users/`                            | `400` — `El correo ya está registrado`      |
| 3  | Listar usuarios                          | `GET /users/`                             | `200 OK`                                    |
| 4  | Consultar usuario por ID                 | `GET /users/1`                            | `200 OK`                                    |
| 5  | Consultar usuario inexistente            | `GET /users/999`                          | `404` — `Usuario no encontrado`             |
| 6  | Filtrar usuarios por rol                 | `GET /users/?role=support`                | `200 OK`, solo usuarios `support`           |
| 7  | Filtrar usuarios activos                 | `GET /users/?is_active=true`              | `200 OK`, solo usuarios activos             |
| 8  | Actualizar completo con PUT              | `PUT /users/2`                            | `200 OK`                                    |
| 9  | Actualizar parcialmente con PATCH        | `PATCH /users/1` `{"role": "support"}`    | `200 OK`                                    |
| 10 | Eliminar usuario                         | `DELETE /users/3`                         | `204 No Content`                            |
| 11 | Validar que el eliminado ya no exista    | `GET /users/3`                            | `404` — `Usuario no encontrado`             |

Pruebas adicionales de error: datos inválidos (`422`), PUT sin `is_active` (`422`), PUT/PATCH/DELETE de usuario inexistente (`404`), PUT/PATCH con email de otro usuario (`400`), PATCH vacío (`400`), rol no permitido en el filtro (`400`) y `order_by` no permitido (`422`). Después de las pruebas, los datos siguen guardados en `device_systems.db`.

## Evidencia de pruebas (EV09)

Capturas tomadas en Swagger UI (`/docs`) con la API conectada a la base de datos SQLite.

### Estructura del proyecto

Vista actual del proyecto en VS Code (incluye también los archivos agregados en EV10).

![Estructura del proyecto](images/ev09_13_estructura_proyecto.png)

### Base de datos generada (`device_systems.db`, tabla `users`)

Usuarios guardados después de las pruebas de EV09, vistos con la extensión SQLite Viewer.

![Base de datos users](images/ev09_14_base_datos_users.png)

### Endpoints disponibles en Swagger UI

![Swagger endpoints](images/ev09_01_swagger_endpoints.png)

### 1. Crear un usuario válido → 201

![POST 201](images/ev09_02_post_crear_201.png)

### 2. Crear usuario con email repetido → 400

![POST 400](images/ev09_03_post_email_repetido_400.png)

### 3. Listar usuarios → 200

![GET listar 200](images/ev09_04_get_listar_200.png)

### 4. Consultar usuario por ID → 200

![GET por ID 200](images/ev09_05_get_por_id_200.png)

### 5. Consultar usuario inexistente → 404

![GET 404](images/ev09_06_get_inexistente_404.png)

### 6. Filtrar usuarios por rol → 200

![Filtro rol 200](images/ev09_07_filtro_rol_200.png)

### 7. Filtrar usuarios activos → 200

![Filtro activos 200](images/ev09_08_filtro_activos_200.png)

### 8. Actualizar usuario completo con PUT → 200

![PUT 200](images/ev09_09_put_200.png)

### 9. Actualizar parcialmente con PATCH → 200

![PATCH 200](images/ev09_10_patch_200.png)

### 10. Eliminar usuario con DELETE → 204

![DELETE 204](images/ev09_11_delete_204.png)

### 11. Validar que el usuario eliminado ya no exista → 404

![GET eliminado 404](images/ev09_12_get_eliminado_404.png)

## Evidencia de pruebas (EV08)

### Endpoints disponibles en Swagger UI

![Endpoints](images/09_swagger_lista_endpoints.png)

### Casos exitosos

- **PUT** /users/{user_id} — actualización completa
  ![PUT 200](images/01_put_actualizar_completo_200.png)
- **PATCH** /users/{user_id} — actualización parcial
  ![PATCH 200](images/02_patch_actualizar_parcial_200.png)
- **DELETE** /users/{user_id} — eliminación exitosa
  ![DELETE 204](images/04_delete_usuario_204.png)
- **GET** /users/{user_id} — usando Depends()
  ![GET con Depends](images/07_get_usuario_con_depends_200.png)

### Casos de error

- PATCH con body vacío → 400
  ![PATCH 400](images/03_patch_body_vacio_400.png)
- GET de usuario eliminado → 404
  ![GET 404](images/05_get_usuario_eliminado_404.png)
- DELETE de usuario inexistente → 404
  ![DELETE 404](images/06_delete_usuario_inexistente_404.png)
- GET de usuario inexistente (con Depends) → 404
  ![GET Depends 404](images/08_get_usuario_con_depends_404.png)
- POST con correo duplicado → 400
  ![POST 400](images/10_post_correo_duplicado_400.png)
- POST con datos inválidos → 422
  ![POST 422](images/11_post_datos_invalidos_422.png)
- PUT de usuario inexistente → 404
  ![PUT 404](images/12_put_usuario_inexistente_404.png)

## Reflexión personal (EV10)

Esta fue la guía más grande hasta ahora y al principio me asustó un poco, porque pasé de tener una sola tabla a tener tres que dependen entre sí. Lo que más me sirvió fue ir por partes: primero Alembic, después los modelos, luego los dispositivos y al final los préstamos, cada parte en su propia rama. Así, cuando algo fallaba, sabía más o menos dónde buscar.

Con Alembic entendí para qué sirven las migraciones. Antes, si cambiaba un modelo, lo más fácil era borrar la base de datos y volver a crearla, pero así se pierden los datos. Con las migraciones cada cambio queda guardado como una "versión" de la base de datos, igual que Git guarda las versiones del código. Me gustó ver con `alembic history` el camino que ha seguido la base de datos, y que mis usuarios de la guía anterior siguieran ahí después de crear las tablas nuevas.

Las relaciones fueron lo que más me hizo pensar. Al principio no entendía bien qué hacían `relationship()` y `back_populates`, pero cuando vi que desde un préstamo podía sacar directamente el nombre del usuario y el serial del equipo, sin hacer consultas aparte, le encontré todo el sentido. También aprendí que la base de datos puede protegerse sola: con las llaves foráneas no se puede crear un préstamo de un usuario que no existe, aunque alguien se salte la API.

Las consultas con joins y filtros me mostraron que una API no es solo guardar y devolver datos: también es responder preguntas como "¿qué equipos tiene prestados esta persona?" o "¿quién ha usado esta laptop?". Y las reglas de negocio, como no prestar un equipo ocupado o no devolver dos veces el mismo préstamo, me hicieron ver la diferencia entre un error de datos (422) y un error de lógica del negocio (409). Siento que con esta guía el proyecto ya se parece a un sistema real que podría usarse en un colegio o en una oficina.

## Reflexión personal (EV09)

Esta guía fue un cambio grande respecto a las anteriores. Hasta ahora los usuarios vivían en una lista dentro del código, y cada vez que reiniciaba el servidor todo volvía a como estaba al principio. Al conectar la API con una base de datos, lo primero que me llamó la atención fue crear un usuario, apagar el servidor, volver a prenderlo… y ver que el usuario seguía ahí. Parece algo sencillo, pero ahí entendí la diferencia entre una API de práctica y una que de verdad podría usarse en un proyecto real.

Lo que más me costó al principio fue entender por qué tenía dos "modelos" del mismo usuario: el de SQLAlchemy y los schemas de Pydantic. Pensaba que era repetir lo mismo. Con la práctica me quedó claro que cada uno tiene su trabajo: el modelo de SQLAlchemy dice cómo se guarda el usuario en la tabla, y los schemas dicen qué datos puede mandar el cliente y qué le devuelve la API. Por ejemplo, el `id` y la fecha de creación los pone el sistema, así que no tiene sentido pedirlos al crear un usuario, pero sí mostrarlos en la respuesta.

También aprendí que los errores no siempre son del código. Mientras tomaba las capturas en Swagger, un filtro por rol me devolvía "Rol no permitido" y no entendía por qué, hasta que vi en la URL que se me había colado un espacio antes de la palabra. Eso me enseñó a leer con calma la respuesta y la URL antes de pensar que la API estaba mala. Y me gustó ver que las validaciones funcionaban, porque la API rechazó el dato raro en lugar de guardarlo.

Si tuviera que explicar por qué es tan importante la persistencia, diría esto: una API sin base de datos es como un cuaderno que se borra cada vez que lo cierras. Sirve para practicar, pero nadie podría usarla de verdad, porque cualquier reinicio, error o actualización del servidor haría perder todos los usuarios registrados. Con la base de datos la información queda guardada de forma segura, se puede consultar y filtrar cuando se necesite, y además la propia base de datos ayuda a cuidar que los datos sean correctos, por ejemplo no dejando repetir un correo.

En general, siento que esta actividad me acercó más a cómo se trabaja en un proyecto de verdad: con base de datos, con ramas en Git para cada parte del trabajo y probando cada endpoint antes de darlo por terminado. Todavía me falta practicar más consultas y trabajar con bases de datos más grandes como MySQL o PostgreSQL, pero ya tengo una base clara para seguir avanzando.

## Reflexión personal (EV08)

Desarrollar `device_systems` con FastAPI me permitió entender por qué este framework se ha vuelto tan popular para construir APIs REST en Python. La validación automática con Pydantic fue lo que más me sorprendió: solo con definir el modelo de datos, la API ya rechaza correos mal formados, roles no permitidos o nombres demasiado cortos, sin que yo tenga que escribir esas validaciones a mano.

Separar el proyecto en `routes`, `services`, `data` y `dependencies` cambió la forma en que pienso el código. Al principio todo estaba mezclado en un solo archivo de rutas, pero mover la lógica de negocio a `services` hizo que las rutas quedaran mucho más simples y fáciles de leer — cada una solo se encarga de recibir la petición y devolver la respuesta, mientras que la lógica real vive en otro lugar.

El uso de `Depends()` fue el concepto que más me costó entender al principio, pero una vez lo apliqué en `get_user_or_404`, quedó claro su valor: en vez de repetir la búsqueda del usuario y el manejo del error 404 en GET, PUT, PATCH y DELETE, esa lógica queda centralizada en una sola función que todas esas rutas reutilizan.

Implementar PUT, PATCH y DELETE con sus respectivos códigos de estado (200, 204, 404, 400) me hizo prestar más atención a algo que antes pasaba por alto: que cada operación HTTP tiene una semántica esperada, y que responder con el código correcto es parte de construir una API bien diseñada, no solo un detalle técnico.

En general, este proyecto me dejó una base sólida para seguir construyendo APIs con FastAPI, entendiendo no solo cómo hacer que funcionen, sino cómo organizarlas de una forma mantenible.

## Autor

Santiago Varela Peña - Aprendiz ADSO, SENA
