# Despliegue local de CarHub con FakeNodo

## 1. Preparar el entorno

Abre Docker Desktop y espera a que el motor esté activo. Ejecuta los comandos de esta guía en PowerShell desde la raíz del repositorio, en `trunk` o en una rama que incluya FakeNodo.

```powershell
docker info
docker compose version

if (-not (Test-Path .env)) {
    Copy-Item .env.docker.example .env
}
```

El archivo de ejemplo configura CarHub para usar la MariaDB local de Docker. Si ya tienes un `.env`, comprueba que `MARIADB_HOSTNAME` sea `db` y que las credenciales correspondan a la base local.

Compose usa `http://fakenodo:5000/api/deposit/depositions` por defecto. Si tienes `ZENODO_API_URL` configurada, déjala con ese valor o elimina la variable para que se aplique el valor por defecto. Puedes hacer la prueba sin `ZENODO_ACCESS_TOKEN` ni credenciales de filess.io.

## 2. Arrancar el entorno

```powershell
docker compose -f docker/docker-compose.dev.yml up -d --build web nginx
docker compose -f docker/docker-compose.dev.yml ps
```

Compose inicia CarHub, Nginx, MariaDB, FakeNodo y Selenium Hub. La primera compilación puede tardar varios minutos. Cuando FakeNodo aparezca como `healthy` y CarHub haya terminado de inicializar la base, abre [CarHub local](http://localhost/).

### Si la compilación de MariaDB se queda esperando

Si se detiene en `apt-get update` dentro del Dockerfile de MariaDB, cancela la compilación con `Ctrl+C`. Esta variante usa la imagen oficial de la misma versión, que ya trae el cliente de MariaDB. La configuración adicional se pasa por la entrada estándar de Compose.

```powershell
docker compose -f docker/docker-compose.dev.yml build web fakenodo

@'
services:
  db:
    build: !reset null
    image: mariadb:12.0.2
'@ | docker compose -f docker/docker-compose.dev.yml -f - up -d --no-build web nginx
```

## 3. Probar una subida con FakeNodo

1. Crea una cuenta en [Registro local](http://localhost/signup/) e inicia sesión. CarHub guarda esa cuenta en la MariaDB local.
2. En **Upload dataset**, sube un archivo UVL. Puedes usar [`file1.uvl`](../app/features/dataset/uvl_examples/file1.uvl). Completa el título y la descripción del dataset, y los campos del modelo si aparecen en el formulario.
3. Guarda y abre **My datasets**. El dataset debe aparecer como sincronizado con un DOI como `10.5072/fakenodo.1`.
4. Abre el enlace al registro de FakeNodo o visita [`http://localhost/fakenodo/records/1`](http://localhost/fakenodo/records/1). Sustituye `1` por el ID de tu depósito. Comprueba que el JSON contiene el mismo DOI que muestra CarHub.

## 4. Consultar logs y detener el entorno

```powershell
docker compose -f docker/docker-compose.dev.yml logs --tail 100 web fakenodo
docker compose -f docker/docker-compose.dev.yml stop
```

Los usuarios y datasets de CarHub se conservan en el volumen de MariaDB. FakeNodo usa SQLite en memoria con la configuración de desarrollo y pierde sus depósitos al reiniciar el contenedor. Después de reiniciarlo, sube un dataset nuevo para repetir la prueba.
