# device_systems

API REST para la gestión de usuarios del sistema **device_systems**, desarrollada con **FastAPI**.

Proyecto desarrollado para las actividades del programa ADSO - SENA:

| Actividad                          | Versión | Contenido                                                         |
| ---------------------------------- | ------- | ----------------------------------------------------------------- |
| GA1-220501096-01-AA1-EV07          | 1.0.0   | FastAPI básico: GET, POST y modelos Pydantic                      |
| GA1-220501096-01-AA1-EV08          | 2.0.0   | CRUD completo, manejo de errores, Swagger/OpenAPI y `Depends()`   |
| GA1-220501096-01-AA1-EV09          | 3.0.0   | Persistencia en base de datos con SQLAlchemy y SQLite             |

## Descripción

`device_systems` es una API REST que permite administrar usuarios (crear, consultar, filtrar, ordenar, actualizar y eliminar). Desde la versión 3.0.0 los usuarios ya no se guardan en una lista en memoria sino en una **base de datos SQLite** (`device_systems.db`) mediante el ORM **SQLAlchemy**, por lo que los datos se conservan aunque el servidor se reinicie.

La API aplica validaciones con Pydantic, constraints en el modelo de base de datos, parámetros de ruta y consulta, modelos de respuesta, cabeceras HTTP personalizadas, manejo de errores con `HTTPException` e inyección de dependencias con `Depends()`.

## Tecnologías utilizadas

- Python 3.14
- FastAPI
- Uvicorn
- Pydantic v2 (+ email-validator)
- SQLAlchemy 2
- SQLite

## Instalación de dependencias

```bash
python -m venv venv
venv\Scripts\activate        # Windows (en Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
```

## Ejecución del servidor

```bash
uvicorn app.main:app --reload
```

La API queda disponible en `http://localhost:8000`, con documentación interactiva en:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Al iniciar, la aplicación crea automáticamente el archivo `device_systems.db` y la tabla `users` si todavía no existen (`Base.metadata.create_all` en `app/main.py`). El archivo `.db` no se sube al repositorio (está en `.gitignore`).

## Estructura del proyecto

```
device_systemsv/
│── app/
│   │── main.py
│   │── database/
│   │   └── connection.py
│   │── models/
│   │   └── user_model.py
│   │── schemas/
│   │   └── user_schema.py
│   │── routes/
│   │   └── user_routes.py
│   │── services/
│   │   └── user_service.py
│   │── dependencies/
│   │   │── database_dependency.py
│   │   └── user_dependencies.py
│── images/            (capturas de las pruebas)
│── requirements.txt
│── README.md
```

| Carpeta        | Responsabilidad                                                          |
| -------------- | ------------------------------------------------------------------------ |
| `database`     | Conexión a la base de datos: engine, `SessionLocal` y `Base`             |
| `models`       | Modelos SQLAlchemy: cómo se guardan los datos (tablas y columnas)        |
| `schemas`      | Modelos Pydantic: qué datos entran y salen de la API                     |
| `routes`       | Definición de endpoints                                                  |
| `services`     | Lógica de negocio y operaciones CRUD sobre la base de datos              |
| `dependencies` | Funciones reutilizables inyectadas con `Depends()` (sesión de BD, usuario, rol) |

## Base de datos con SQLAlchemy

### Conexión (`app/database/connection.py`)

- `DATABASE_URL = "sqlite:///./device_systems.db"`: base de datos SQLite en la raíz del proyecto.
- `engine`: objeto que se conecta a la base de datos.
- `SessionLocal`: fábrica de sesiones; cada petición abre su propia sesión.
- `Base`: clase base de la que heredan los modelos.
- `get_session()`: crea una sesión nueva.

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

`UserResponse` usa `model_config = ConfigDict(from_attributes=True)` para construirse directamente desde el objeto SQLAlchemy.

## Tabla de endpoints

| Operación           | Método | Ruta               | Código esperado            |
| ------------------- | ------ | ------------------ | -------------------------- |
| Listar usuarios     | GET    | `/users/`          | 200 OK / 400 (rol inválido)|
| Consultar usuario   | GET    | `/users/{user_id}` | 200 OK / 404               |
| Crear usuario       | POST   | `/users/`          | 201 Created / 400 / 422    |
| Actualizar completo | PUT    | `/users/{user_id}` | 200 OK / 404 / 400 / 422   |
| Actualizar parcial  | PATCH  | `/users/{user_id}` | 200 OK / 404 / 400 / 422   |
| Eliminar usuario    | DELETE | `/users/{user_id}` | 204 No Content / 404       |
| Información API     | GET    | `/info`            | 200 OK                     |

Parámetros de consulta de `GET /users/` (se pueden combinar):

| Parámetro   | Valores                         | Por defecto | Ejemplo                                  |
| ----------- | ------------------------------- | ----------- | ---------------------------------------- |
| `role`      | `admin`, `support`, `user`      | —           | `/users/?role=support`                   |
| `is_active` | `true`, `false`                 | —           | `/users/?is_active=true`                 |
| `order_by`  | `id`, `name`, `created_at`      | `id`        | `/users/?order_by=name`                  |
| `order`     | `asc`, `desc`                   | `asc`       | `/users/?order_by=created_at&order=desc` |
| `skip`      | entero ≥ 0                      | `0`         | `/users/?skip=10`                        |
| `limit`     | entero entre 1 y 100            | `100`       | `/users/?limit=5`                        |

## Ejemplos de peticiones y respuestas

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

- `200 OK` — operación exitosa (GET, PUT, PATCH)
- `201 Created` — usuario creado exitosamente
- `204 No Content` — usuario eliminado exitosamente
- `400 Bad Request` — correo duplicado, PATCH sin campos o rol no permitido en el filtro
- `404 Not Found` — usuario no encontrado (GET, PUT, PATCH o DELETE por ID)
- `422 Unprocessable Entity` — datos inválidos según Pydantic

## Uso de Depends()

Las dependencias están en `app/dependencies/` y se inyectan en las rutas con `Depends()`:

| Dependencia               | Archivo                  | Dónde se usa                                           | Qué hace                                                            |
| ------------------------- | ------------------------ | ------------------------------------------------------ | ------------------------------------------------------------------- |
| `get_db`                  | `database_dependency.py` | Todos los endpoints de `/users`                        | Abre una sesión de base de datos por petición y la cierra al final  |
| `get_user_or_404`         | `user_dependencies.py`   | `GET`, `PUT`, `PATCH` y `DELETE` de `/users/{user_id}` | Busca el usuario en la base de datos y lanza `404` si no existe     |
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

Los errores de validación de datos (`422`) son generados automáticamente por Pydantic a partir de las reglas definidas en los modelos: longitud mínima del nombre, formato de email y valores permitidos de rol al crear o actualizar. En PATCH, los campos enviados como `null` se ignoran, por lo que un cuerpo como `{"name": null}` se trata como una actualización sin datos (`400`).

El correo duplicado se controla en dos niveles: el servicio consulta primero si el email ya existe (`get_user_by_email`) y, como respaldo, si la base de datos rechaza el registro por el constraint `unique` (`IntegrityError`), se hace `rollback` y se responde igualmente `400`. El rol también está protegido en la base de datos con un `CHECK`, además de la validación de Pydantic.

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

## Reflexión personal (EV09)

Esta guía fue un cambio grande respecto a las anteriores. Hasta ahora los usuarios vivían en una lista dentro del código, y cada vez que reiniciaba el servidor todo volvía a como estaba al principio. Al conectar la API con una base de datos, lo primero que me llamó la atención fue crear un usuario, apagar el servidor, volver a prenderlo… y ver que el usuario seguía ahí. Parece algo sencillo, pero ahí entendí la diferencia entre una API de práctica y una que de verdad podría usarse en un proyecto real.

Lo que más me costó al principio fue entender por qué tenía dos "modelos" del mismo usuario: el de SQLAlchemy y los schemas de Pydantic. Pensaba que era repetir lo mismo. Con la práctica me quedó claro que cada uno tiene su trabajo: el modelo de SQLAlchemy dice cómo se guarda el usuario en la tabla, y los schemas dicen qué datos puede mandar el cliente y qué le devuelve la API. Por ejemplo, el `id` y la fecha de creación los pone el sistema, así que no tiene sentido pedirlos al crear un usuario, pero sí mostrarlos en la respuesta.

También aprendí que los errores no siempre son del código. Mientras tomaba las capturas en Swagger, un filtro por rol me devolvía "Rol no permitido" y no entendía por qué, hasta que vi en la URL que se me había colado un espacio antes de la palabra. Eso me enseñó a leer con calma la respuesta y la URL antes de pensar que la API estaba mala. Y me gustó ver que las validaciones funcionaban, porque la API rechazó el dato raro en lugar de guardarlo.

En general, siento que esta actividad me acercó más a cómo se trabaja en un proyecto de verdad: con base de datos, con ramas en Git para cada parte del trabajo y probando cada endpoint antes de darlo por terminado. Todavía me falta practicar más consultas y trabajar con bases de datos más grandes como MySQL o PostgreSQL, pero ya tengo una base clara para seguir avanzando.

## Reflexión personal (EV08)

Desarrollar `device_systems` con FastAPI me permitió entender por qué este framework se ha vuelto tan popular para construir APIs REST en Python. La validación automática con Pydantic fue lo que más me sorprendió: solo con definir el modelo de datos, la API ya rechaza correos mal formados, roles no permitidos o nombres demasiado cortos, sin que yo tenga que escribir esas validaciones a mano.

Separar el proyecto en `routes`, `services`, `data` y `dependencies` cambió la forma en que pienso el código. Al principio todo estaba mezclado en un solo archivo de rutas, pero mover la lógica de negocio a `services` hizo que las rutas quedaran mucho más simples y fáciles de leer — cada una solo se encarga de recibir la petición y devolver la respuesta, mientras que la lógica real vive en otro lugar.

El uso de `Depends()` fue el concepto que más me costó entender al principio, pero una vez lo apliqué en `get_user_or_404`, quedó claro su valor: en vez de repetir la búsqueda del usuario y el manejo del error 404 en GET, PUT, PATCH y DELETE, esa lógica queda centralizada en una sola función que todas esas rutas reutilizan.

Implementar PUT, PATCH y DELETE con sus respectivos códigos de estado (200, 204, 404, 400) me hizo prestar más atención a algo que antes pasaba por alto: que cada operación HTTP tiene una semántica esperada, y que responder con el código correcto es parte de construir una API bien diseñada, no solo un detalle técnico.

En general, este proyecto me dejó una base sólida para seguir construyendo APIs con FastAPI, entendiendo no solo cómo hacer que funcionen, sino cómo organizarlas de una forma mantenible.

## Autor

Santiago Varela Peña - Aprendiz ADSO, SENA
