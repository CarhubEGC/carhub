# Guía de despliegue en Render

Guía cronológica para desplegar Carhub como preproducción en Render usando una
base de datos MariaDB externa. No contiene credenciales reales: los valores
marcados como pendientes deben copiarse de los paneles de Render y del proveedor
de base de datos.

## 1. Qué hace cada parte

- **GitHub Actions CI** ejecuta las pruebas con una MariaDB temporal. No usa la
  base de datos de Render ni necesita credenciales de producción.
- **Render** ejecuta la aplicación web.
- **Filess.io** (u otro proveedor compatible) puede proporcionar la MariaDB
  externa. Filess.io es una opción, no un requisito.
- **GitHub Actions CD** puede pedir a Render que despliegue después de que pasen
  las pruebas. Para eso hay que adaptar el workflow actual.

No se deben copiar credenciales de producción a CI ni subir archivos `.env` con
valores reales al repositorio.

## 2. Diagnóstico del primer despliegue

El log de Render muestra:

```text
Can't connect to MySQL server on 'localhost' ([Errno 111] Connection refused)
```

En Render, `localhost` es el propio contenedor de la aplicación; no es la base de
datos. `MARIADB_HOSTNAME` debe ser el host remoto que indique el proveedor de
MariaDB. El nombre `db` solo sirve cuando la aplicación y MariaDB comparten la
red de Docker Compose.

El log también muestra Python 3.14. El servicio parece haberse creado con el
runtime nativo de Python. Este repositorio ya tiene un Dockerfile para Render
que fija Python 3.13: [`docker/images/Dockerfile.render`](docker/images/Dockerfile.render).
Usarlo también evita depender de la versión Python que Render elija por defecto.

## 3. Elegir entorno y rama

Antes de crear/configurar el servicio, decidir si será preproducción o
producción:

- Para **preproducción**, usar un servicio separado y, si es posible, una base
  de datos separada; conectar el servicio a `trunk`.
- Para **producción**, usar el servicio y la base de datos de producción;
  normalmente se despliega desde `main`.

En la captura de Render aparecía seleccionado **Production**. No crear ahí el
servicio si la intención es probar en preproducción. El plan de `$7/mes` también
aparecía seleccionado; comprobar el coste y cambiarlo si se quiere usar otro
plan.

## 4. Crear la base de datos MariaDB

1. Crear una base MariaDB en Filess.io u otro proveedor compatible.
2. Copiar del panel del proveedor:
   - hostname o endpoint;
   - puerto;
   - nombre de la base;
   - usuario;
   - contraseña.
3. Confirmar que permite conexiones desde Render y consultar sus requisitos de
   TLS/firewall.

No inventar estos valores. No usar `localhost`, `127.0.0.1` ni `db` como host
para una base externa. No usar la base `uvlhubdb_test` del CI en producción.

## 5. Configurar el servicio web en Render

1. Crear un **Web Service** conectado al repositorio `CarhubEGC/carhub`.
2. Seleccionar el entorno adecuado y la rama decidida en el paso 3.
3. Configurar el servicio para usar **Docker**, no el runtime nativo de Python.
4. Dejar **Root Directory** vacío y establecer **Dockerfile Path** en:

   ```text
   docker/images/Dockerfile.render
   ```

5. Dejar que el Dockerfile defina la instalación y el comando de inicio; no usar
   los comandos Python sugeridos automáticamente por Render.
6. Copiar del panel de Render el dominio público asignado después de crear el
   nuevo servicio. El servicio anterior fue borrado, así que no asumir que su
   URL sigue vigente ni que Render reutilizará `carhub-hrlj.onrender.com`.

El Dockerfile de Render espera a MariaDB, ejecuta las migraciones y después
inicia Gunicorn. El primer arranque no terminará correctamente hasta que las
variables de conexión a la base estén bien configuradas.

## 6. Añadir variables de entorno en Render

En la página del servicio, abrir **Environment** y añadir variables. Los valores
sensibles se guardan en Render; no se escriben en el repositorio.

En la captura actual aparecen las cinco variables MariaDB, `FLASK_APP_NAME`,
`FLASK_ENV`, `SECRET_KEY` y `WORKING_DIR`. Falta añadir `DOMAIN`. Créalo después
de que Render asigne la URL al nuevo servicio. Los valores no sensibles de la
aplicación quedan así:

```env
FLASK_APP_NAME=UVLHUB.IO
FLASK_ENV=production
DOMAIN=<hostname-del-nuevo-servicio.onrender.com>
WORKING_DIR=/workspace/
```

Sustituir el marcador por el hostname que muestre el nuevo servicio, sin
`https://`. No usar la URL del servicio borrado.

| Variable | Valor y origen |
|---|---|
| `FLASK_APP_NAME` | `UVLHUB.IO`, como en [`.env.docker.production.example`](.env.docker.production.example). |
| `FLASK_ENV` | `production`. También para una instancia de preproducción: es la configuración de ejecución, no la rama Git. |
| `DOMAIN` | El hostname público del nuevo servicio asignado por Render, sin `https://`. El código actual construye algunos enlaces como `http://{DOMAIN}`; ver la nota de HTTPS al final. |
| `SECRET_KEY` | Generar una clave aleatoria; no reutilizar la de otra instancia. En PowerShell o en una terminal con Python: `python -c "import secrets; print(secrets.token_hex(32))"`. |
| `MARIADB_HOSTNAME` | Hostname remoto que da el proveedor MariaDB; nunca `localhost` en Render. |
| `MARIADB_PORT` | Puerto indicado por el proveedor. No asumir `3306` si el panel muestra otro. |
| `MARIADB_DATABASE` | Nombre de la base indicado por el proveedor. |
| `MARIADB_USER` | Usuario de la base indicado por el proveedor. |
| `MARIADB_PASSWORD` | Contraseña de ese usuario, indicada/generada por el proveedor. |
| `WORKING_DIR` | `/workspace/`, como en el ejemplo de producción y el Dockerfile de Render. |

Los valores MariaDB se copian de **Connection Information** en Filess.io. La
contraseña que aparecía en la captura anterior debe regenerarse antes de usarla
en producción; después, actualizar `MARIADB_PASSWORD` en Render con la nueva.

`MARIADB_ROOT_PASSWORD` se usa para inicializar el contenedor MariaDB en Docker
Compose; normalmente no se necesita para conectarse a una base externa
administrada. `WEBHOOK_TOKEN` solo es necesario si se mantiene el endpoint de
despliegue propio del proyecto; no es el token del Deploy Hook de Render.

## 7. Comprobar el arranque en Render

Después de guardar las variables, desplegar y revisar **Logs**:

- Si vuelve a aparecer `localhost`, comprobar que `MARIADB_HOSTNAME` se guardó
  en el servicio correcto.
- Si aparece un error de conexión, comprobar host, puerto, usuario, contraseña,
  nombre de base y que el proveedor acepte conexiones externas.
- Si la conexión funciona, el entrypoint de Render ejecutará las migraciones.

La URL del servicio debe abrir la aplicación. La primera conexión y las
migraciones también se pueden verificar en los logs de Render.

## 8. Dejar CI funcionando en GitHub

El workflow existente
[`.github/workflows/CI_pytest.yml`](.github/workflows/CI_pytest.yml):

- ejecuta `pytest app/features/ --ignore-glob='*selenium*'`;
- se dispara en `push` y `pull_request` a `main` y `trunk`;
- inicia su propia MariaDB 12.0.2 con credenciales de prueba escritas en el
  workflow.

Por tanto, el CI actual no necesita secrets de producción, Filess.io ni un
`.env`. No cambiar sus credenciales para que apunten a la base de Render.

## 9. Conectar CD con Render

El workflow actual
[`.github/workflows/CD_webhook.yml`](.github/workflows/CD_webhook.yml) llama a
`https://WEBHOOK_DOMAIN/webhook/deploy` y envía `WEBHOOK_TOKEN`. Ese endpoint
invoca Docker y espera un contenedor existente con acceso al socket de Docker.
No es el mecanismo de despliegue de Render; no basta con rellenar esos dos
secrets para que funcione allí. Para Render, la opción más sencilla es usar su
integración nativa con los checks de GitHub:

1. En los ajustes del servicio, seleccionar **After CI Checks Pass** en
   **Auto-Deploy**.
2. Conectar el servicio a la rama correcta: `trunk` para preproducción o `main`
   para producción.
3. Confirmar que el workflow Pytest se ejecuta en esa rama y termina en éxito.
   Render desplegará ese commit después de que pasen los checks de GitHub.

Con esta opción no se necesita un Deploy Hook URL ni un secret adicional para
desplegar en Render. **On Commit** también despliega automáticamente, pero no
espera a que pasen las pruebas. **Off** desactiva el auto-deploy.

Si se decide invocar manualmente un Deploy Hook desde GitHub Actions, Render
proporciona una URL secreta en los ajustes del servicio. En ese caso sí se puede
guardarla como `RENDER_DEPLOY_HOOK_URL` y adaptar un workflow para hacerle una
petición `POST` después del CI. No usar para ello el webhook propio actual.

## 10. Qué secrets van en GitHub

Guardar cada secret solo donde lo consuma un workflow:

| Secret de GitHub | Cuándo hace falta |
|---|---|
| `RENDER_DEPLOY_HOOK_URL` | Solo si un workflow invoca manualmente el Deploy Hook. No hace falta con **After CI Checks Pass**. |
| `DOCKER_USER` y `DOCKER_PASSWORD` | Solo si se conserva [`.github/workflows/CD_dockerhub.yml`](.github/workflows/CD_dockerhub.yml), que publica la imagen en Docker Hub al crear una release. Usar un token de Docker Hub, no la contraseña personal. |

Si Render construye directamente desde el repositorio con
`docker/images/Dockerfile.render`, no hacen falta los secrets de Docker Hub para
que Render ejecute la aplicación. El workflow actual de Docker Hub es opcional y
se ejecuta en una **release**, no en cada push.

No poner las credenciales de MariaDB en GitHub Actions: la aplicación necesita
esas credenciales en Render. Tampoco configurar `WEBHOOK_DOMAIN` y
`WEBHOOK_TOKEN` para Render si se sustituye el webhook propio por el Deploy Hook
de Render.

## 11. Verificación final

1. Hacer push a `trunk`.
2. Confirmar que **Pytest** termina correctamente en GitHub Actions.
3. Confirmar que Render despliega la rama de preproducción y que sus logs muestran
   conexión a MariaDB y migraciones completadas.
4. Abrir la URL pública de Render y probar la aplicación.
5. Cuando preproducción esté validada, configurar producción como servicio y
   base de datos independientes, y desplegar desde `main`.

### Nota sobre enlaces HTTPS

`app/features/dataset/services.py` construye actualmente algunos enlaces DOI
anteponiendo `http://` a `DOMAIN`, mientras que Render sirve la URL pública por
HTTPS. Si esos enlaces deben ser seguros, el código debe actualizarse para
generarlos con `https://` antes de considerar terminado el despliegue de
producción.
