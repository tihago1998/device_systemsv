# device_systems

API REST para la gestión de usuarios del sistema **device_systems**, desarrollada con **FastAPI**.

Proyecto desarrollado para las actividades **GA1-220501096-01-AA1-EV07** y su evolución **GA1-220501096-01-AA1-EV08** (FastAPI Intermedio) del programa ADSO - SENA.

## Descripción

`device_systems` es una API REST que permite administrar usuarios (crear, consultar, actualizar y eliminar), aplicando validaciones con Pydantic, parámetros de ruta y consulta, modelos de respuesta, cabeceras HTTP personalizadas, manejo de errores estructurado e inyección de dependencias con `Depends()`.

## Tecnologías utilizadas

- Python 3.14
- FastAPI
- Uvicorn
- Pydantic v2

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

## Estructura del proyecto

```
device_systemsv/
│── app/
│   │── main.py
│   │── routes/
│   │   └── user_routes.py
│   │── schemas/
│   │   └── user_schema.py
│   │── services/
│   │   └── user_service.py
│   │── dependencies/
│   │   └── user_dependencies.py
│   │── data/
│   │   └── users_db.py
│── images/            (capturas de las pruebas)
│── requirements.txt
│── README.md
```

| Carpeta        | Responsabilidad                                      |
| -------------- | ---------------------------------------------------- |
| `routes`       | Definición de endpoints                              |
| `schemas`      | Modelos Pydantic de entrada y salida                 |
| `services`     | Lógica de negocio                                    |
| `dependencies` | Funciones reutilizables inyectadas con `Depends()`   |
| `data`         | Simulación de base de datos en memoria               |

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

Filtros disponibles en `GET /users/`: `?role=admin|support|user` y `?is_active=true|false` (se pueden combinar).

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
  "is_active": true,
  "id": 3
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
  "is_active": true,
  "id": 2
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
  "is_active": true,
  "id": 1
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

Las dependencias están en `app/dependencies/user_dependencies.py` y se inyectan en las rutas con `Depends()`:

| Dependencia               | Dónde se usa                                              | Qué hace                                                        |
| ------------------------- | --------------------------------------------------------- | --------------------------------------------------------------- |
| `get_user_or_404`         | `GET`, `PUT`, `PATCH` y `DELETE` de `/users/{user_id}`    | Busca el usuario por ID y lanza `404` si no existe              |
| `validar_rol`             | `GET /users/` (filtro `role`)                             | Lanza `400` si el rol no es `admin`, `support` o `user`         |
| `get_api_info`            | `GET /info`                                               | Entrega la configuración general de la API (nombre y versión)   |
| `verificar_autenticacion` | Disponible para proteger rutas                            | Simula autenticación con la cabecera `x-token: secreto123`      |

Gracias a `get_user_or_404`, la búsqueda del usuario y el error `404` se escriben una sola vez y se reutilizan en los cuatro endpoints que reciben `user_id`. Así las rutas quedan cortas y los servicios reciben directamente el usuario ya validado.

## Manejo de errores

Todos los errores de negocio se manejan con `HTTPException`, devolviendo respuestas JSON consistentes con la estructura `{"detail": "mensaje del error"}`:

| Situación                         | Código | Mensaje                                         |
| --------------------------------- | ------ | ----------------------------------------------- |
| Usuario no encontrado             | 404    | `Usuario no encontrado`                         |
| Eliminación de usuario inexistente| 404    | `Usuario no encontrado`                         |
| Correo electrónico duplicado      | 400    | `El correo ya está registrado`                  |
| Rol no permitido (filtro)         | 400    | `Rol no permitido. Debe ser uno de: ...`        |
| Actualización (PATCH) sin datos   | 400    | `No se enviaron campos para actualizar`         |

Los errores de validación de datos (`422`) son generados automáticamente por Pydantic a partir de las reglas definidas en los modelos: longitud mínima del nombre, formato de email y valores permitidos de rol al crear o actualizar. En PATCH, los campos enviados como `null` se ignoran, por lo que un cuerpo como `{"name": null}` se trata como una actualización sin datos (`400`).

## Evidencia de pruebas

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

## Reflexión personal

Desarrollar `device_systems` con FastAPI me permitió entender por qué este framework se ha vuelto tan popular para construir APIs REST en Python. La validación automática con Pydantic fue lo que más me sorprendió: solo con definir el modelo de datos, la API ya rechaza correos mal formados, roles no permitidos o nombres demasiado cortos, sin que yo tenga que escribir esas validaciones a mano.

Separar el proyecto en `routes`, `services`, `data` y `dependencies` cambió la forma en que pienso el código. Al principio todo estaba mezclado en un solo archivo de rutas, pero mover la lógica de negocio a `services` hizo que las rutas quedaran mucho más simples y fáciles de leer — cada una solo se encarga de recibir la petición y devolver la respuesta, mientras que la lógica real vive en otro lugar.

El uso de `Depends()` fue el concepto que más me costó entender al principio, pero una vez lo apliqué en `get_user_or_404`, quedó claro su valor: en vez de repetir la búsqueda del usuario y el manejo del error 404 en GET, PUT, PATCH y DELETE, esa lógica queda centralizada en una sola función que todas esas rutas reutilizan.

Implementar PUT, PATCH y DELETE con sus respectivos códigos de estado (200, 204, 404, 400) me hizo prestar más atención a algo que antes pasaba por alto: que cada operación HTTP tiene una semántica esperada, y que responder con el código correcto es parte de construir una API bien diseñada, no solo un detalle técnico.

En general, este proyecto me dejó una base sólida para seguir construyendo APIs con FastAPI, entendiendo no solo cómo hacer que funcionen, sino cómo organizarlas de una forma mantenible.

## Autor

Santiago Varela Peña - Aprendiz ADSO, SENA
