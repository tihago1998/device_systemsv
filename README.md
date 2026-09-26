# device_systems

API REST para la gestión de usuarios, dispositivos tecnológicos y préstamos del sistema **device_systems**, desarrollada con **FastAPI**, **SQLAlchemy** y **Alembic**, y protegida con **OAuth2 + JWT**, contraseñas con hash **bcrypt**, **CORS**, middleware de trazabilidad y **rate limiting**.

Proyecto desarrollado para las actividades del programa ADSO - SENA:

| Actividad                          | Versión | Contenido                                                         |
| ---------------------------------- | ------- | ----------------------------------------------------------------- |
| GA1-220501096-01-AA1-EV07          | 1.0.0   | FastAPI básico: GET, POST y modelos Pydantic                      |
| GA1-220501096-01-AA1-EV08          | 2.0.0   | CRUD completo, manejo de errores, Swagger/OpenAPI y `Depends()`   |
| GA1-220501096-01-AA1-EV09          | 3.0.0   | Persistencia en base de datos con SQLAlchemy y SQLite             |
| GA1-220501096-01-AA1-EV10          | 4.0.0   | Migraciones con Alembic, relaciones entre modelos y consultas con joins |
| GA1-220501096-01-AA1-EV11          | 5.0.0   | Seguridad: OAuth2 + JWT, hash con passlib, roles, middleware, CORS, rate limiting y Pydantic v2 avanzado |

La versión 5.0.0 se desarrolló en la rama **`device_systems_security`**, unificada con `main`.

## Descripción

`device_systems` es una API REST para administrar el préstamo de equipos tecnológicos:

- **Usuarios** (`/users`): CRUD, filtros por rol, estado y texto, y consulta de sus préstamos y dispositivos asignados.
- **Dispositivos** (`/devices`): CRUD de laptops, tablets, proyectores, cámaras, routers y monitores, con filtros por tipo, disponibilidad, marca y búsqueda.
- **Préstamos** (`/loans`): prestar un dispositivo a un usuario, devolverlo y consultar préstamos con la información del usuario y del dispositivo (joins), con filtros por estado, usuario, dispositivo, correo, tipo y fechas.
- **Autenticación** (`/auth`): registro con contraseña segura, login OAuth2 que entrega un token JWT y consulta del usuario autenticado.

Desde la versión 5.0.0 la API es **segura**: las contraseñas se guardan como hash bcrypt, las rutas privadas exigen un token JWT, cada operación se autoriza según el rol (`admin`, `support`, `user`), solo los frontends autorizados pueden consumirla desde el navegador (CORS), cada petición queda registrada con un identificador único (middleware) y los endpoints sensibles tienen un límite de peticiones por minuto (rate limiting). Ver la sección [Seguridad (EV11)](#seguridad-ev11).

Los datos se guardan en una **base de datos SQLite** (`device_systems.db`) mediante el ORM **SQLAlchemy**, y la estructura de la base de datos se versiona con **migraciones de Alembic**. La API aplica validaciones con Pydantic, constraints e integridad referencial en la base de datos, reglas de negocio (no prestar un equipo ocupado, no devolver dos veces), manejo de errores con `HTTPException` e inyección de dependencias con `Depends()`.

## Tecnologías utilizadas

- Python 3.14
- FastAPI
- Uvicorn
- Pydantic v2 (+ email-validator)
- SQLAlchemy 2
- Alembic
- SQLite
- passlib + bcrypt (hash de contraseñas)
- python-jose (tokens JWT)
- python-multipart (formulario OAuth2 del login)
- slowapi (rate limiting)
- python-dotenv (variables de entorno desde `.env`)

## Instalación de dependencias

```bash
python -m venv venv
venv\Scripts\activate        # Windows (en Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
```

## Variables de entorno (`.env`)

La configuración sensible **no se escribe en el código**. Copie el archivo de ejemplo y cambie los valores:

```bash
copy .env.example .env       # Windows (en Linux/Mac: cp .env.example .env)
python -c "import secrets; print(secrets.token_hex(32))"   # genera una SECRET_KEY segura
```

| Variable                      | Uso                                                              | Ejemplo                                      |
| ----------------------------- | ---------------------------------------------------------------- | -------------------------------------------- |
| `DATABASE_URL`                | Conexión a la base de datos (la usa también Alembic)             | `sqlite:///./device_systems.db`              |
| `SECRET_KEY`                  | Clave con la que se firman los JWT. **Obligatoria**: sin ella la API no arranca | cadena aleatoria de 64 caracteres |
| `ALGORITHM`                   | Algoritmo de firma del JWT                                       | `HS256`                                      |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Minutos de validez del token                                     | `30`                                         |
| `CORS_ORIGINS`                | Frontends autorizados, separados por coma                        | `http://localhost:5173,http://localhost:3000` |
| `RATE_LIMIT_ENABLED`          | Activa o desactiva el rate limiting                              | `true`                                       |

El archivo `.env` está en `.gitignore`; al repositorio solo se sube `.env.example`, sin secretos reales.

## Crear la base de datos (migraciones)

La aplicación ya no crea las tablas al iniciar: la estructura se aplica con Alembic. Antes de ejecutar el servidor por primera vez:

```bash
alembic upgrade head
```

Esto crea `device_systems.db` con las tablas `users`, `devices`, `loans` y `alembic_version`. El archivo `.db` no se sube al repositorio (está en `.gitignore`).

### Crear el primer administrador

`POST /auth/register` solo permite crear cuentas con rol `user` (así nadie puede registrarse como administrador por su cuenta). El primer admin se crea desde la terminal; la contraseña se pide por teclado y se guarda como hash:

```bash
python -m app.auth.create_admin --name "Santiago Varela" --email admin@device.com
```

Luego ese admin puede registrar usuarios `support` o `admin` enviando su token en `POST /auth/register` o `POST /users`.

> Los usuarios que ya existían antes de la migración `7695ce3eeaef` quedaron con la contraseña temporal **`Temporal2026`** (solo para desarrollo), para poder iniciar sesión con ellos en las pruebas.

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
│   │── config.py                 (variables de entorno: SECRET_KEY, JWT, CORS, rate limit)
│   │── auth/
│   │   │── auth_routes.py        (POST /auth/register, POST /auth/login, GET /auth/me)
│   │   │── auth_service.py       (registro y autenticación)
│   │   │── security.py           (hash bcrypt y tokens JWT)
│   │   └── create_admin.py       (script para crear el primer admin)
│   │── database/
│   │   └── connection.py
│   │── models/
│   │   │── user_model.py
│   │   │── device_model.py
│   │   └── loan_model.py
│   │── schemas/
│   │   │── user_schema.py
│   │   │── device_schema.py
│   │   │── loan_schema.py
│   │   └── auth_schema.py
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
│   │   │── auth_dependency.py
│   │   │── user_dependencies.py
│   │   │── device_dependencies.py
│   │   └── loan_dependencies.py
│   │── middlewares/
│   │   │── request_middleware.py (X-Request-ID, X-Process-Time, cabeceras y log)
│   │   └── rate_limit.py         (slowapi: límites por endpoint y respuesta 429)
│── alembic/
│   │── env.py
│   └── versions/
│       │── 78ad4166a2e4_create_users_table.py
│       │── 46413d96466f_create_devices_and_loans_tables.py
│       └── 7695ce3eeaef_add_authentication_fields_to_users.py
│── .env                (no se sube a GitHub)
│── .env.example
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
| `dependencies` | Funciones reutilizables inyectadas con `Depends()` (sesión de BD, usuario autenticado, roles, buscar usuario/dispositivo/préstamo o 404) |
| `auth`         | Autenticación: rutas `/auth`, hash de contraseñas y creación/validación de tokens JWT |
| `middlewares`  | Middleware de trazabilidad y cabeceras, y configuración del rate limiting |
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
| `7695ce3eeaef` | add authentication fields to users   | Columna `hashed_password` (obligatoria) en `users`; los usuarios existentes reciben el hash de una contraseña temporal |

### Comandos usados

```bash
alembic init alembic                                              # inicializar Alembic
alembic revision --autogenerate -m "create devices and loans tables"  # generar migración comparando modelos y BD
alembic revision --autogenerate -m "add authentication fields to users"  # migración de EV11
alembic upgrade head                                              # aplicar migraciones pendientes
alembic history                                                   # ver historial de migraciones
alembic current                                                   # ver versión aplicada
alembic downgrade -1                                              # revertir la última migración
```

**Errores al aplicar migraciones:** si una migración falla, Alembic detiene el proceso y no actualiza `alembic_version`, por lo que la base de datos queda en la última versión correcta. Se corrige el script y se vuelve a ejecutar `alembic upgrade head`; si hace falta deshacer un cambio ya aplicado se usa `alembic downgrade -1`. Antes de generar la migración de `devices` y `loans` se verificó con `alembic check` que solo se detectaran esas dos tablas nuevas.

**Migración de EV11:** la migración autogenerada agregaba `hashed_password` como `NOT NULL` directamente, lo que falla porque la tabla `users` ya tenía registros (SQLite no sabe qué valor ponerles). Se ajustó en tres pasos: (1) agregar la columna permitiendo `NULL`, (2) guardar en los usuarios existentes el hash bcrypt de una contraseña temporal y (3) volver la columna obligatoria. Después, `alembic check` confirmó que el modelo y la base de datos quedaron iguales.

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
| `hashed_password` | String(255) | `nullable=False`. Solo el hash bcrypt; nunca se expone en las respuestas |
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
| `UserCreate`   | POST (crear, solo admin)     | `name`, `email`, `role`, `password` obligatorios; `is_active` opcional (True) |
| `UserUpdate`   | PUT (actualización completa) | `name`, `email`, `role` e `is_active`, todos obligatorios      |
| `UserPatch`    | PATCH (actualización parcial)| Todos opcionales                                               |
| `UserResponse` | Respuesta                    | `id`, `name`, `email`, `role`, `is_active`, `created_at` (**sin** `hashed_password`) |
| `UserRegister` | POST `/auth/register`        | `name`, `email`, `password`, `confirm_password`; `role` opcional (`user`) |
| `UserLogin`    | POST `/auth/login`           | `email`, `password` (en Swagger llegan como formulario OAuth2: `username` = correo) |
| `Token`        | Respuesta del login          | `access_token`, `token_type` (`bearer`)                        |
| `TokenData`    | Contenido del JWT            | `email` (claim `sub`) y `role`                                 |

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

La columna **Protección** indica qué se necesita para usar cada endpoint. Sin token o con un token inválido la API responde `401`; con un rol no permitido, `403`.

### Auth

| Operación                    | Método | Ruta              | Protección              | Código esperado                    |
| ---------------------------- | ------ | ----------------- | ----------------------- | ---------------------------------- |
| Registrar usuario            | POST   | `/auth/register`  | Pública (rol `user`); admin para registrar `admin`/`support` | 201 / 400 / 403 / 422 / 429 |
| Iniciar sesión (token JWT)   | POST   | `/auth/login`     | Pública                 | 200 / 401 / 403 / 429              |
| Usuario autenticado          | GET    | `/auth/me`        | Usuario autenticado     | 200 / 401                          |

### Users

| Operación                    | Método | Ruta                        | Protección                   | Código esperado            |
| ---------------------------- | ------ | --------------------------- | ---------------------------- | -------------------------- |
| Listar usuarios              | GET    | `/users/`                   | Usuario autenticado          | 200 / 400 / 401 / 429      |
| Consultar usuario            | GET    | `/users/{user_id}`          | Usuario autenticado          | 200 / 401 / 404            |
| Préstamos de un usuario      | GET    | `/users/{user_id}/loans`    | Autenticado (`user`: solo los suyos) | 200 / 401 / 403 / 404 |
| Dispositivos asignados       | GET    | `/users/{user_id}/devices`  | Autenticado (`user`: solo los suyos) | 200 / 401 / 403 / 404 |
| Crear usuario                | POST   | `/users/`                   | Admin                        | 201 / 400 / 401 / 403 / 422 |
| Actualizar completo          | PUT    | `/users/{user_id}`          | Admin                        | 200 / 400 / 401 / 403 / 404 / 422 |
| Actualizar parcial           | PATCH  | `/users/{user_id}`          | Admin                        | 200 / 400 / 401 / 403 / 404 / 422 |
| Eliminar usuario             | DELETE | `/users/{user_id}`          | Admin                        | 204 / 401 / 403 / 404 / 409 |

### Devices

| Operación                    | Método | Ruta                          | Protección          | Código esperado                 |
| ---------------------------- | ------ | ----------------------------- | ------------------- | ------------------------------- |
| Listar dispositivos          | GET    | `/devices/`                   | Pública (catálogo)  | 200 / 422                       |
| Consultar dispositivo        | GET    | `/devices/{device_id}`        | Pública (catálogo)  | 200 / 404                       |
| Historial de préstamos       | GET    | `/devices/{device_id}/loans`  | Admin o support     | 200 / 401 / 403 / 404           |
| Registrar dispositivo        | POST   | `/devices/`                   | Admin o support     | 201 / 400 / 401 / 403 / 422     |
| Actualizar completo          | PUT    | `/devices/{device_id}`        | Admin o support     | 200 / 400 / 401 / 403 / 404 / 409 / 422 |
| Actualizar parcial           | PATCH  | `/devices/{device_id}`        | Admin o support     | 200 / 400 / 401 / 403 / 404 / 409 / 422 |
| Eliminar dispositivo         | DELETE | `/devices/{device_id}`        | Admin               | 204 / 401 / 403 / 404 / 409     |

### Loans

| Operación                          | Método | Ruta                        | Protección                   | Código esperado                 |
| ---------------------------------- | ------ | --------------------------- | ---------------------------- | ------------------------------- |
| Listar préstamos                   | GET    | `/loans/`                   | Admin o support              | 200 / 400 / 401 / 403 / 422     |
| Listar préstamos con usuario y dispositivo | GET | `/loans/details`       | Admin o support              | 200 / 400 / 401 / 403 / 422     |
| Consultar préstamo                 | GET    | `/loans/{loan_id}`          | Autenticado (`user`: solo los suyos) | 200 / 401 / 403 / 404   |
| Registrar préstamo                 | POST   | `/loans/`                   | Autenticado (`user`: solo a su nombre) | 201 / 401 / 403 / 404 / 409 / 422 / 429 |
| Devolver dispositivo               | PATCH  | `/loans/{loan_id}/return`   | Admin o support              | 200 / 401 / 403 / 404 / 409     |
| Cambiar estado (active/overdue)    | PATCH  | `/loans/{loan_id}`          | Admin o support              | 200 / 401 / 403 / 404 / 409 / 422 |

### Security

| Operación                              | Método | Ruta    | Protección | Código esperado |
| -------------------------------------- | ------ | ------- | ---------- | --------------- |
| Estado de la API                       | GET    | `/`     | Pública    | 200 OK          |
| Información y configuración de seguridad (sin secretos) | GET | `/info` | Pública | 200 OK |

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
| Error de validación (datos o filtros con valores no permitidos, contraseña débil) | `422 Unprocessable Entity` |
| Token ausente, inválido o vencido; login incorrecto | `401 Unauthorized`  |
| Usuario sin permisos (rol no permitido) o inactivo  | `403 Forbidden`     |
| Se superó el límite de peticiones                   | `429 Too Many Requests` |

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
| `get_current_user`        | `auth_dependency.py`     | Base de todas las rutas protegidas                     | Lee el token de `Authorization: Bearer`, valida firma y vencimiento, y busca al usuario (`401` si falla) |
| `get_current_active_user` | `auth_dependency.py`     | Todo `/users`, todo `/loans`, `GET /auth/me`           | Igual que el anterior, pero rechaza usuarios inactivos (`403`)      |
| `require_admin`           | `auth_dependency.py`     | Crear/editar/eliminar usuarios, eliminar dispositivos  | Solo deja pasar al rol `admin` (`403`)                              |
| `require_admin_or_support`| `auth_dependency.py`     | Crear/editar dispositivos, devoluciones, reportes de préstamos | Solo deja pasar a `admin` o `support` (`403`)              |
| `get_optional_user`       | `auth_dependency.py`     | `POST /auth/register`                                  | Token opcional: sin token devuelve `None`; con token inválido, `401` |
| `get_api_info`            | `main.py`                | `GET /info`                                            | Entrega nombre, versión y configuración de seguridad (sin secretos) |

Las dependencias también pueden depender de otras: `get_user_or_404` recibe la sesión de `get_db` para consultar el usuario. Así, la búsqueda del usuario y el error `404` se escriben una sola vez y se reutilizan en los cuatro endpoints que reciben `user_id`, y los servicios reciben directamente el usuario ya validado. Lo mismo pasa con la seguridad: `require_admin` depende de `get_current_active_user`, que a su vez depende de `get_current_user` y de `get_db`, formando una cadena de validaciones que FastAPI resuelve antes de ejecutar el endpoint.

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

## Seguridad (EV11)

### Cambios respecto a la versión 4.0.0

| Antes (EV10)                                         | Ahora (EV11)                                                                 |
| ---------------------------------------------------- | ---------------------------------------------------------------------------- |
| Cualquiera podía usar todos los endpoints            | Rutas privadas con OAuth2 + JWT y permisos por rol                           |
| Los usuarios no tenían contraseña                    | Contraseña segura validada con Pydantic y guardada como hash bcrypt          |
| Autenticación simulada con `x-token: secreto123`     | Eliminada; reemplazada por tokens JWT firmados y con vencimiento             |
| Configuración escrita en el código                   | Variables de entorno en `.env` (`SECRET_KEY`, CORS, JWT, rate limit)         |
| Middleware que solo agregaba `X-App-Name` y `X-API-Version` | Middleware de trazabilidad: `X-Request-ID`, `X-Process-Time`, log de cada petición y cabeceras de seguridad |
| Sin control de peticiones                            | Rate limiting con slowapi en login, registro, listado de usuarios y préstamos |
| Sin CORS                                             | CORS con lista explícita de frontends autorizados                           |

### Hash de contraseñas con passlib (`app/auth/security.py`)

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

get_password_hash("Segura2026")   # -> "$2b$12$Qm1v..." (distinto cada vez)
verify_password("Segura2026", hash_guardado)   # -> True
```

- La contraseña llega en texto plano **solo** en el cuerpo de `POST /auth/register` (o `POST /users`) y se convierte en hash dentro de `user_service.create_user`, antes de crear el objeto `User`. En la base de datos solo existe la columna `hashed_password`.
- **bcrypt** agrega una "sal" aleatoria a cada hash, así que dos usuarios con la misma contraseña tienen hashes distintos, y es lento a propósito, lo que hace muy costoso un ataque de fuerza bruta.
- El hash no se puede "desencriptar": para el login se vuelve a calcular con la contraseña recibida y se compara (`verify_password`).
- Ningún schema de respuesta tiene `password` ni `hashed_password`, así que la API nunca los devuelve.

### Login con OAuth2 y JWT

```
1. POST /auth/login  (form: username=correo, password)
2. La API busca el usuario por correo y verifica la contraseña con bcrypt
3. Si es correcta, crea un JWT firmado con SECRET_KEY: {"sub": correo, "role": rol, "exp": vencimiento}
4. Respuesta: {"access_token": "eyJ...", "token_type": "bearer"}
5. El cliente envía en cada petición protegida:  Authorization: Bearer eyJ...
6. get_current_user valida la firma y el vencimiento, y busca el usuario en la base de datos
```

- Se usa `OAuth2PasswordBearer(tokenUrl="auth/login")`, por eso Swagger muestra el botón **Authorize**: se escribe el correo en *username*, la contraseña, y Swagger envía el token automáticamente en las rutas con candado.
- El token vence a los `ACCESS_TOKEN_EXPIRE_MINUTES` minutos (30 por defecto). Un token vencido, mal formado o con la firma alterada responde `401`.
- Si el correo no existe o la contraseña es incorrecta, el mensaje es el mismo (`Correo o contraseña incorrectos`) y el tiempo de respuesta también, para no revelar qué correos están registrados.
- El rol se lee de la base de datos en cada petición (no del token), así que si un admin cambia el rol o desactiva un usuario, el cambio aplica de inmediato.

### Protección de rutas y roles (`app/dependencies/auth_dependency.py`)

| Ruta (según la guía)          | Protección requerida | Dependencia usada          | Sin token / token inválido | Rol no permitido |
| ----------------------------- | -------------------- | -------------------------- | -------------------------- | ---------------- |
| `GET /users`                  | Usuario autenticado  | `get_current_active_user`  | 401                        | —                |
| `GET /users/{user_id}`        | Usuario autenticado  | `get_current_active_user`  | 401                        | —                |
| `POST /devices`               | Admin o support      | `require_admin_or_support` | 401                        | 403              |
| `PUT /devices/{device_id}`    | Admin o support      | `require_admin_or_support` | 401                        | 403              |
| `DELETE /devices/{device_id}` | Admin                | `require_admin`            | 401                        | 403              |
| `POST /loans`                 | Usuario autenticado  | `get_current_active_user`  | 401                        | 403 si un `user` pide un préstamo a nombre de otro |
| `PATCH /loans/{loan_id}/return` | Admin o support    | `require_admin_or_support` | 401                        | 403              |
| `GET /loans/details`          | Admin o support      | `require_admin_or_support` | 401                        | 403              |

Las demás rutas también quedaron protegidas (ver la [tabla de endpoints](#tabla-de-endpoints)): crear, editar y eliminar usuarios es solo de `admin`, y un usuario con rol `user` solo puede ver sus propios préstamos. `require_roles(*roles)` genera la dependencia para cualquier combinación de roles:

```python
require_admin = require_roles("admin")
require_admin_or_support = require_roles("admin", "support")

@router.delete("/{device_id}", dependencies=[Depends(require_admin)])
```

### Validaciones avanzadas con Pydantic v2

| Herramienta               | Dónde                                    | Qué valida                                                           |
| ------------------------- | ---------------------------------------- | -------------------------------------------------------------------- |
| `Field()`                 | Todos los schemas                        | Longitudes (`min_length=8`, `max_length=72` en la contraseña), `gt=0` en IDs, descripciones y ejemplos para Swagger |
| `field_validator("password")` | `UserRegister`, `UserCreate`         | Mínimo una mayúscula, una minúscula y un número, sin espacios        |
| `field_validator("name")` | `UserBase`, `UserPatch`, `UserRegister`  | Quita espacios sobrantes y rechaza nombres de solo espacios          |
| `field_validator("email")`| Schemas de usuario y auth                | Guarda el correo en minúsculas (`Ana@Sena.edu.co` = `ana@sena.edu.co`) |
| `model_validator(mode="after")` | `UserRegister`                     | `password` y `confirm_password` deben coincidir, y la contraseña no puede contener el usuario del correo |
| `model_config = ConfigDict(from_attributes=True)` | Schemas de respuesta | Construir la respuesta desde el objeto SQLAlchemy                   |
| `Literal[...]`            | `Role`, `LoanStatus`, `DeviceType`       | Solo se aceptan los valores permitidos                               |

Ejemplo de respuesta con contraseña débil (`"password": "sinmayusculas"`):

```json
{
  "detail": [{
    "type": "value_error",
    "loc": ["body", "password"],
    "msg": "Value error, La contraseña debe tener: al menos una letra mayúscula, al menos un número"
  }]
}
```

> bcrypt solo tiene en cuenta los primeros 72 bytes de la contraseña; por eso `max_length=72`.

### CORS configurado

CORS (*Cross-Origin Resource Sharing*) es la regla con la que el **navegador** decide si una página de un dominio (por ejemplo un frontend en `http://localhost:5173`) puede leer las respuestas de una API que está en otro dominio (`http://localhost:8000`). Si la API no lo autoriza, el navegador bloquea la respuesta.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,        # ["http://localhost:5173", "http://localhost:3000"] desde .env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time", "X-App-Name", "X-API-Version"],
)
```

- `allow_origins`: solo los frontends de desarrollo de React/Vite (`5173`) y React/Next (`3000`). Se configuran en `.env`, así en producción se cambia por el dominio real sin tocar el código.
- `allow_credentials=True`: permite que el navegador envíe cookies o la cabecera `Authorization` con el token.
- `allow_methods=["*"]` y `allow_headers=["*"]`: se aceptan todos los métodos (GET, POST, PUT, PATCH, DELETE) y cabeceras (incluida `Authorization`), porque el control de quién puede llamar la API ya lo hace `allow_origins`.
- `expose_headers`: permite que el JavaScript del frontend lea las cabeceras propias del middleware, como `X-Request-ID`.
- CORS se agrega como el middleware **más externo**, para que incluso las respuestas de error (`401`, `403`, `429`) lleven las cabeceras CORS y el frontend pueda leer el mensaje.

**¿Por qué no usar `allow_origins=["*"]` en producción cuando hay credenciales?**
Con `"*"` cualquier página de internet quedaría autorizada para llamar a la API desde el navegador de un usuario. Si además se permiten credenciales, una página maliciosa que el usuario visite podría hacer peticiones a la API usando la sesión o el token de ese usuario y leer sus datos o actuar en su nombre. Por eso la especificación de CORS prohíbe combinar `Access-Control-Allow-Origin: *` con `Access-Control-Allow-Credentials: true` (los navegadores rechazan esa respuesta), y la práctica correcta es listar explícitamente los dominios confiables. En las pruebas, un origen no autorizado (`http://malicioso.com`) recibe `400 Disallowed CORS origin` en la verificación previa (*preflight*) y no recibe la cabecera `Access-Control-Allow-Origin`.

### Middleware personalizado (`app/middlewares/request_middleware.py`)

Se ejecuta en **todas** las peticiones, antes y después del endpoint:

| Cabecera / acción          | Para qué sirve                                                                       |
| -------------------------- | ------------------------------------------------------------------------------------ |
| `X-Request-ID`             | Identificador único de la petición. Si el cliente envía uno válido se propaga; si no, se genera (8 caracteres). Permite seguir una petición en los logs |
| `X-Process-Time`           | Tiempo que tardó la API en responder, en segundos (`0.0042`)                          |
| `X-App-Name`               | `device_systems`                                                                     |
| `X-API-Version`            | `5.0.0`                                                                              |
| `X-Content-Type-Options: nosniff` | El navegador no intenta adivinar el tipo de contenido                          |
| `X-Frame-Options: DENY`    | La API no se puede mostrar dentro de un `iframe` de otra página                       |
| Log en consola             | `GET /users/ -> 200 (0.0042s) [request_id=8f42e9c1]`: método, ruta, código y tiempo   |

Un `X-Request-ID` recibido solo se acepta si tiene letras, números, `-` o `_` (máximo 64); así nadie puede meter texto falso en los logs.

### Rate limiting (`app/middlewares/rate_limit.py`)

Se usa **slowapi**, que cuenta las peticiones de cada cliente (por dirección IP) en una ventana de un minuto:

| Endpoint              | Límite                 | Motivo                                                  |
| --------------------- | ---------------------- | ------------------------------------------------------- |
| `POST /auth/login`    | 5 solicitudes/minuto   | Frenar ataques de fuerza bruta para adivinar contraseñas |
| `POST /auth/register` | 3 solicitudes/minuto   | Evitar la creación masiva de cuentas                    |
| `GET /users`          | 30 solicitudes/minuto  | Evitar la extracción masiva de datos de usuarios        |
| `POST /loans`         | 10 solicitudes/minuto  | Evitar el abuso de solicitudes de préstamo              |

```python
@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), ...):
```

Al superar el límite la API responde `429 Too Many Requests` con la cabecera `Retry-After: 60`:

```json
{"detail": "Demasiadas solicitudes. Límite permitido: 5 per 1 minute. Intente de nuevo más tarde."}
```

Los contadores se guardan en memoria (se reinician al reiniciar el servidor). `RATE_LIMIT_ENABLED=false` en `.env` desactiva los límites, útil solo para pruebas automatizadas.

## Pruebas funcionales (EV11)

| #  | Escenario de la guía                  | Petición                                                    | Resultado esperado                                 |
| -- | ------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------- |
| 1  | Registro de usuario                   | `POST /auth/register`                                       | `201 Created`, sin `password` ni `hashed_password` |
| 2  | Registro con contraseña débil         | `POST /auth/register` con `"password": "sinmayusculas"`     | `422` con el detalle de las reglas incumplidas     |
| 3  | Registro con email duplicado          | `POST /auth/register` con un correo existente               | `400 El correo ya está registrado`                 |
| 4  | Login correcto                        | `POST /auth/login`                                          | `200` con `access_token` y `token_type: bearer`    |
| 5  | Login con contraseña incorrecta       | `POST /auth/login`                                          | `401 Correo o contraseña incorrectos`              |
| 6  | Consulta de `/auth/me`                | `GET /auth/me` con `Authorization: Bearer <token>`          | `200` con los datos del usuario, sin el hash       |
| 7  | Ruta protegida sin token              | `GET /users/` sin `Authorization`                           | `401 Not authenticated`                            |
| 8  | Acceso con token inválido             | `GET /users/` con `Bearer abc.def.ghi`                      | `401 No se pudo validar el token de acceso`        |
| 9  | Usuario sin permisos                  | `GET /loans/details` con token de rol `user`                | `403 Permiso denegado: se requiere rol admin o support` |
| 10 | Crear dispositivo con rol permitido   | `POST /devices/` con token de `support`                     | `201 Created`                                      |
| 11 | Eliminar dispositivo con rol no permitido | `DELETE /devices/{id}` con token de `support`           | `403 Permiso denegado: se requiere rol admin`      |
| 12 | Configuración CORS                    | `OPTIONS /users/` con `Origin: http://localhost:5173`       | `200` con `access-control-allow-origin: http://localhost:5173` y `access-control-allow-credentials: true` |
| 13 | Cabeceras del middleware              | Cualquier petición                                          | `X-App-Name`, `X-Process-Time`, `X-Request-ID`, `X-API-Version` |
| 14 | Activación de rate limiting           | 6 × `POST /auth/login` en menos de un minuto                | Las 5 primeras responden; la 6.ª, `429 Too Many Requests` |
| 15 | Swagger/OpenAPI                       | `GET /docs`                                                 | Botón **Authorize**, candados en rutas protegidas, tags Auth, Users, Devices, Loans y Security |

Además se probó: registrarse como `admin` sin token (`403`), que un admin sí pueda registrar un `support` (`201`), que `confirm_password` distinta sea rechazada por el `model_validator` (`422`), un token con la firma alterada (`401`), que un `user` no pueda pedir un préstamo a nombre de otro (`403`) pero sí a su nombre (`201`), y que un origen CORS no autorizado sea rechazado.

**Cómo probar la configuración CORS con curl** (simula la verificación previa del navegador):

```bash
curl -i -X OPTIONS http://localhost:8000/users/ -H "Origin: http://localhost:5173" -H "Access-Control-Request-Method: GET"
curl -i -X OPTIONS http://localhost:8000/users/ -H "Origin: http://malicioso.com" -H "Access-Control-Request-Method: GET"
```

## Evidencia de pruebas (EV11)

> **Pendiente:** tomar las capturas y guardarlas en `images/` con estos nombres.

### Estructura del proyecto

![Estructura del proyecto](images/ev11_01_estructura_proyecto.png)

### Migración Alembic aplicada (`alembic upgrade head`)

![Migración aplicada](images/ev11_02_alembic_upgrade.png)

### Registro de usuario → 201

![Registro](images/ev11_03_register_201.png)

### Registro con contraseña débil → 422

![Contraseña débil](images/ev11_04_register_password_debil_422.png)

### Registro con email duplicado → 400

![Email duplicado](images/ev11_05_register_email_duplicado_400.png)

### Login y token generado → 200

![Login](images/ev11_06_login_token_200.png)

### Login con contraseña incorrecta → 401

![Login incorrecto](images/ev11_07_login_incorrecto_401.png)

### `GET /auth/me` → 200

![auth me](images/ev11_08_auth_me_200.png)

### Acceso sin token → 401

![Sin token](images/ev11_09_sin_token_401.png)

### Acceso con token inválido → 401

![Token inválido](images/ev11_10_token_invalido_401.png)

### Acceso con rol no permitido → 403

![Rol no permitido](images/ev11_11_rol_no_permitido_403.png)

### Crear dispositivo con rol support → 201

![Dispositivo support](images/ev11_12_crear_dispositivo_support_201.png)

### Eliminar dispositivo con rol support → 403

![Eliminar support](images/ev11_13_eliminar_dispositivo_support_403.png)

### Swagger/OpenAPI con OAuth2 (botón Authorize)

![Swagger OAuth2](images/ev11_14_swagger_oauth2.png)

### Configuración CORS

![CORS](images/ev11_15_cors.png)

### Cabeceras del middleware

![Cabeceras](images/ev11_16_cabeceras_middleware.png)

### Rate limiting → 429

![Rate limiting](images/ev11_17_rate_limit_429.png)

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

## Reflexión personal (EV11)

Hasta esta guía, `device_systems` funcionaba bien, pero cualquiera que conociera la dirección de la API podía crear, modificar o borrar lo que quisiera. Me di cuenta de que una API puede estar "terminada" y aun así no estar lista para usarse de verdad, porque no sabe quién le está hablando ni si esa persona tiene permiso para hacer lo que pide.

Lo primero que me cambió la forma de pensar fue el manejo de contraseñas. Al principio creía que bastaba con no mostrarlas en las respuestas, pero entendí que ni siquiera deben guardarse: con bcrypt solo se guarda un hash, y para el login se vuelve a calcular y se compara. Me llamó la atención que la misma contraseña genere un hash distinto cada vez, y que eso sea justamente lo que la protege si alguien llegara a robarse la base de datos.

Con OAuth2 y JWT entendí la diferencia entre autenticación y autorización. El token responde "¿quién eres?" (401 si no se puede saber) y los roles responden "¿qué puedes hacer?" (403 si no tienes permiso). Me gustó que, gracias a `Depends()`, proteger una ruta sea tan sencillo como agregar `require_admin`, y que la misma idea que usé en EV08 para el 404 ahora sirva para la seguridad.

CORS, el middleware y el rate limiting me mostraron que la seguridad no es una sola cosa, sino varias capas: CORS decide qué páginas pueden usar la API desde el navegador, el middleware deja un rastro de cada petición con su `X-Request-ID` para poder investigar un problema, y el límite de peticiones evita que alguien pruebe miles de contraseñas en el login. Cuando vi el `429` después del quinto intento entendí lo fácil que sería un ataque de fuerza bruta si ese límite no existiera.

Para mí, la seguridad en una API REST es tan importante como que funcione, porque detrás de los datos hay personas: sus correos, sus contraseñas y los equipos que tienen a cargo. Una API insegura puede funcionar perfecto hasta el día en que alguien la usa mal. Esta guía me enseñó a pensar no solo en "qué debe hacer la API", sino también en "qué no se debe poder hacer con ella".

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
