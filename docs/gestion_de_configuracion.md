# Gestión de Configuración

## Fecha

09/11/2026

Este documento describe la metodología de gestión de configuración que seguirá el grupo para garantizar buenas prácticas en el desarrollo del proyecto.

## Version
 
 | Versión | Contenido       |
 |---------|-----------------|
 | 1.0.0   | Versión inicial |
 | 1.0.1   | Corrección bug 25  |

## Índice

1. [Estándares de código](#1-estándares-de-código)
2. [Políticas de mensajes de commit](#2-políticas-de-mensajes-de-commit)
3. [Plantillas de propuestas](#3-plantillas-de-propuestas)
4. [Estructura de repositorios y ramas por defecto](#4-estructura-de-repositorios-y-ramas-por-defecto)
5. [Estrategia de ramas (EGCFlow)](#5-estrategia-de-ramas-egcflow)
   - [Ramas de Soporte](#ramas-de-soporte)
      - [Ramas `features`](#1-ramas-features)
      - [Ramas `bugfix`](#2-ramas-bugfix)
   - [Cómo desarrollar ramas de feature](#cómo-desarrollar-ramas-de-feature)
   - [Cómo solucionar errores en una release](#cómo-solucionar-errores-en-una-release)
6. [Políticas de versionado](#6-políticas-de-versionado)
7. [Definición de "hecho"](#7-definición-de-hecho)


# 1. Estándares de código

Los estándares de código son dependientes de las decisiones que el linter tome sobre nuestro código
        
# 2. Políticas de mensajes de commit

Se utiliza Conventional Commits, en concreto con la siguiente estructura:

```
<tipo>: <descripción>

<cuerpo opcional>

[Closes/Refs] #<id-issue>
```

Donde:

- `<tipo>` puede ser:
  - `feat` para nuevas características
  - `fix` para correcciones de errores
  - `devops` para modificaciones en integración continua y despliegue continuo
  - `docs` para cambios en la documentación
  - `refactor` para refactorizaciones del código
  - `test` para la adición o modificación en pruebas (```test```(utils): agregar pruebas unitarias para la función de formateo de fechas)
  - `<descripción>` es una breve explicación del cambio (fix: ```corregir error en el cálculo de totales```)
  - `[cuerpo opcional]` proporciona contexto adicional sobre el cambio 

    >>fix: corregir error en el cálculo de totales
    >```
    >El problema ocurría cuando un usuario eliminaba un producto del carrito 
    >y los totales no se actualizaban correctamente. Ahora, el total se recalcula 
    >cada vez que se elimina un producto.
    >```

- `[nota(s) de pie opcional(es)]` puede incluir el número (_#_) del _issue_ al que va relacionado o información sobre cambios importantes

    >>feat: agregar soporte para pagos con PayPal
    >>
    >>Se implementó la integración con la API de PayPal para permitir pagos en la plataforma.
    >```
    >BREAKING CHANGE: Se modificó la estructura del endpoint `/payments`.
    >Closes #123
    >```

# 3. Plantillas de propuestas

### Propuesta de pruebas

Se utilizará la siguiente estructura para proponer la realización de una prueba:
```
  name: Propuesta de Testing

  about: Proponer pruebas para verificar el comportamiento del proyecto.

  title: '[TEST] '

  xlabels: ['testing', 'necesita revisión']

  xassignees: ''
```
#### Descripción de las pruebas
Describe las pruebas que se propone añadir o mejorar.

#### Objetivo/Aportación de las pruebas
Explica qué comportamiento, requisito o posible regresión se quiere verificar.

#### Comportamiento o funcionalidad que se va a probar
Indica qué parte del proyecto se probará y cuál es su comportamiento actual.

#### Casos de prueba
Enumera los escenarios que deberían cubrirse, incluyendo los casos límite o de error que sean relevantes.
1. ...
2. ...

#### Resultado esperado
Describe los resultados que deberían obtenerse al ejecutar las pruebas.

#### Entorno o tipo de pruebas
Indica, si se conoce, si se trata de pruebas unitarias, de integración o de extremo a extremo, y cualquier requisito para ejecutarlas.

---
### Propuesta de mejora

Se utilizará la siguiente estructura para proponer la realización de una mejora:
```
name: Propuesta de Mejora

about: Crear un reporte sobre una posible mejora sobre el código actual.

title: '[PROPUESTA DE MEJORA]'

labels: ['mejora', 'considerar mejora']

assignees: ''
```
#### Descripción de la propuesta
Una descripción clara y concisa de la propuesta de mejora.

#### Objetivo/Aportación de la propuesta
Una descripción clara sobre cuál es el valor añadido de la propuesta de mejora.

#### Comportamiento actual
Una descripción clara sobre como funciona actualmente.

#### Comportamiento esperado
Una descripción clara sobre como debería funcionar el proyecto tras incluir esta propuesta.

#### Testing sugerido
Una descripción sobre pruebas que ayudarian a verificar la correcta funcionalidad de la propuesta.

#### Pasos para reproducir
1. Ir a '...'
2. Hacer clic en '...'
3. Desplazarse hasta '...'
4. Ver el resultado.

---

### Propuesta de refactorización

Se utilizará la siguiente estructura para proponer la realización de una refactorización:

```
name: Propuesta de Refactorización

about: Crear un reporte sobre una posible refactorización del código actual.

title: '[REFACTOR] '

labels: ['refactor', 'considerar refactorización']

assignees: ''
```
#### Descripción de la propuesta
Una descripción clara y concisa de la refactorización propuesta.

#### Objetivo/Aportación de la propuesta
Explica qué aspecto del código se quiere mejorar y qué beneficios se esperan, por ejemplo, en legibilidad, mantenibilidad o rendimiento.

#### Comportamiento actual
Describe cómo funciona actualmente el código afectado y qué dificultades presenta.

#### Comportamiento esperado
Describe cómo debería quedar el código tras la refactorización, indicando si debe mantenerse el mismo comportamiento para las personas usuarias.

#### Testing sugerido
Indica qué pruebas permitirían comprobar que la refactorización funciona correctamente y que no introduce regresiones.

#### Archivos o componentes afectados
Indica las partes del proyecto que podrían verse afectadas por la propuesta.

---

### Propuesta de funcionalidad

Se utilizará la siguiente estructura para proponer la realización de una funcionalidad:

```
name: Solicitud de funcionalidad

about: Crear un reporte sobre una posible nueva funcionalidad.

title: '[FEATURE REQUEST]'

labels: ['feature', 'considerar nueva funcionalidad']

assignees: ''
```
#### Descripción de la propuesta
Una descripción clara y concisa de la nueva funcionalidad.

#### Objetivo/Aportación de la propuesta
Una descripción clara sobre cuál es el valor añadido de la nueva funcionalidad.

#### Comportamiento actual
Una descripción clara sobre como funciona actualmente, enfocandose en lo que falta que esta funcionalidad cubre.

#### Comportamiento esperado
Una descripción clara sobre como debería funcionar el proyecto tras incluir esta nueva funcionalidad.

#### Testing sugerido
Una descripción sobre pruebas que ayudarian a verificar la nueva funcionalidad.

#### Pasos para reproducir
1. Ir a '...'
2. Hacer clic en '...'
3. Desplazarse hasta '...'
4. Ver el resultado.

---

### Reporte de ug

Se utilizará la siguiente estructura para reportar la aparición de un bug:

```
name: Reporte de Error (Bug)

about: Crea un reporte para ayudar a solucionar un fallo.

title: '[BUG] '

labels: ['bug', 'necesita revisión']

assignees: ''
```

#### Descripción del problema
Una descripción clara y concisa del error.

#### Pasos para reproducir
1. Ir a '...'
2. Hacer clic en '...'
3. Desplazarse hasta '...'
4. Ver el error.

#### Comportamiento esperado
Una descripción clara de lo esperado que pasara.

#### Entorno usado
Una descripción clara del entorno que se usa incluido versionado.

#### Capturas de pantalla
Si aplica, añade capturas para explicar el problema.

## 4. Estructura de repositorios y ramas por defecto

Para gestionar el desarrollo de nuestro proyecto de manera organizada y eficiente, utilizaremos Git como sistema de control de versiones. Todo nuestro código lo alojamos en un repositorio de GitHub, al que todos los miembros del equipo podremos acceder a través del siguiente enlace:


[Github](https://github.com/CarhubEGC/carhub.git)

Para estructurar correctamente nuestro repositorio y coordinar el trabajo en equipo, usaremos la estrategia de ramas conocida como EGCFlow. Con esta metodología, definiremos un flujo de trabajo estructurado que nos permitirá integrar los cambios de manera controlada y minimizar posibles conflictos en el código.

La estructura del repositorio se basará en dos ramas principales, que nos servirán como base del desarrollo. A partir de ellas, crearemos ramas específicas para nuevas funcionalidades, correcciones y versiones del proyecto. A continuación, explicamos la organización de las ramas y las reglas que seguiremos para su gestión:

- **main**: En esta rama almacenaremos las versiones estables y listas para producción del proyecto.

- **trunk**: En esta rama llevaremos a cabo el desarrollo principal. Todas las nuevas funcionalidades y mejoras serán implementadas aquí antes de ser integradas en main una vez finalizadas y validadas.

### Estructura de carpetas
 
El repositorio parte de un fork de [uvlhub](https://github.com/EGCETSII/uvlhub), por lo que mantiene su organización. La raíz del proyecto en la rama `trunk` queda así:
 
```
carhub/
├── .devcontainer/                  # Configuración del entorno de desarrollo en contenedor
├── .github/                        # Workflows de GitHub Actions y plantilla de commits
├── app/                            # Código fuente de la aplicación
├── docker/                         # Ficheros de configuración para despliegue con Docker
├── docs/                           # Documentación del proyecto
├── migrations/                     # Migraciones de la base de datos
├── rosemary/                       # Herramienta CLI del proyecto
├── scripts/                        # Scripts de utilidad y automatización
├── tests/                          # Pruebas del proyecto
├── vagrant/                        # Configuración para entornos con Vagrant
├── .env.docker.example             # Variables de entorno de ejemplo (Docker)
├── .env.docker.production.example  # Variables de entorno de ejemplo (Docker, producción)
├── .env.local.example              # Variables de entorno de ejemplo (local)
├── .env.vagrant.example            # Variables de entorno de ejemplo (Vagrant)
├── .env.selenium                   # Variables de entorno para pruebas con Selenium
├── .gitattributes
├── .gitignore
├── .gitmessage                     # Plantilla de mensajes de commit
├── conftest.py                     # Configuración global de pytest
├── GUIA_DESPLIEGUE_RENDER.md       # Guía de despliegue en Render
├── pyproject.toml                  # Configuración del proyecto Python
├── README.md
└── requirements.txt                # Dependencias del proyecto
```

## 5. Estrategia de ramas (EGCFlow)

### Ramas de Soporte

Además de las ramas principales mencionadas anteriormente, en este proyecto utilizaremos ramas de soporte para facilitar el desarrollo de nuevas funcionalidades o corregir errores. Las ramas de soporte se dividen en dos tipos:

#### 1. Ramas `features`

Cuando queremos agregar una nueva funcionalidad al proyecto, creamos una rama `feature` a partir de `trunk`. Aquí es donde trabajaremos hasta que la funcionalidad este completa siguiendo nuestra definicion de DONE. Una vez terminada, la fusionaremos de vuelta en `trunk` para que forme parte del desarrollo principal.

#### 2. Ramas `bugfix`  

Si durante la fase de release encontramos errores que necesitan corregirse, creamos una rama `bugfix` a partir de `trunk`. Aquí trabajamos en las correcciones necesarias para garantizar que la versión esté lista para su entrega. Una vez solucionados los problemas, fusionamos los cambios de vuelta en `trunk`.

### Cómo desarrollar ramas de feature

Para desarrollar una nueva funcionalidad, crearemos una rama de `feature` a partir de la rama `trunk` utilizando el siguiente comando:

```bash
git checkout -b feature/myFeature/numero-issue trunk
```
Cada tarea tendrá su propia rama, nombrada de acuerdo con la tarea, y la crearemos a partir de la rama `trunk`. En esa rama, implementaremos todos los cambios necesarios. Una vez que la tarea esté terminada, realizaremos un merge a `trunk` utilizando la opción no fast forward para asegurarnos de que no se pierdan cambios y que la fusión se haga correctamente.

### Cómo solucionar errores en una release

Para solucionar errores en una release, hemos decidido crear ramas **`bugfix`** específicas. Esto es necesario porque si trabajamos todos en la misma rama `trunk` para corregir errores, podría haber conflictos. Por tanto, para gestionar estas correcciones de manera eficiente y evitar conflictos, creamos ramas dedicadas a los **bugfixes en trunk**.

El proceso que seguiremos será el siguiente:

- **Crearemos una rama `bugfix`**: A partir de la rama de `trunk` correspondiente, crearemos una rama con un nombre específico que incluya la versión y el número del error. Por ejemplo, si tenemos que corregir el error `task/numero-issue`, el comando sería:

   ```bash
   git checkout -b bugfix/vX.Y.Z/task/numero-issue trunk
   ```

   De esta forma, nos aseguramos de estar trabajando en una rama separada para el bugfix y evitamos problemas de conflictos con el trabajo en la rama `trunk`.

- **Realizaremos las correcciones necesarias**: En esta nueva rama `bugfix`, realizaremos las correcciones necesarias para solucionar el problema en la release.

- **Fusionaremos de vuelta en `trunk`**: Después de que se realicen las correcciones necesarias en la rama `bugfix`, fusionaremos la rama en la rama `trunk` correspondiente para aplicar el arreglo de bug en la versión final.

## 6. Políticas de versionado

En nuestro proyecto, aplicamos el versionado semántico para mantener nuestras versiones claras y predecibles. Así es como lo hacemos:

### 1. Cambios Grandes: Versionado Mayor (MAJOR) en Marcha

Cuando introducimos cambios que rompen la compatibilidad, incrementamos el número mayor. Por ejemplo, en la primera release se ha aumentado la versión mayor.

* Este tipo de cambio refleja transformaciones significativas en la estructura o funcionalidad del proyecto.
* Siempre que incrementamos el Major, ponemos a cero el Minor y el Patch.

### 2. Nuevas Funcionalidades: Versionado Menor (MINOR) en Juego

Añadimos nuevas funcionalidades sin romper la compatibilidad, y para reflejarlo, incrementamos el número menor. Por ejemplo, de la versión 2.0.0 de la rama main, tras añadir nuevas funcionalidades incrementamos la versión menor, pasando a 2.1.0.

* Esto muestra que hemos expandido las capacidades del proyecto.
* Cuando incrementamos el Minor, ponemos a cero el Patch.

### 3. Correcciones: Versionado de Parche (PATCH) en Uso

Corregimos errores que no afectan la compatibilidad, y para esto, incrementamos el número de parche. Por ejemplo, de la versión 1.0.0 de la rama release, tras la correción de errores se ha incrementado al versión parche, pasando a 1.0.1.

* Esto nos esta ayudando a mantener la estabilidad y la calidad del proyecto.

## 7. Definición de "hecho"

Para nuestra definición de hecho que se le aplica a las tareas el grupo ha concluido que cualquier tarea de código que ha sido realizada por integración continua y se pueda desplegar automáticamente sigue su correcto funcionamiento.

Siguiendo estos pasos consideramos que cualquier tarea de documentación en "Done" ha sido comprobada que se implementado de forma correcta y cumple con los requisitos.

Siguiendo estos pasos consideramos que cualquier tarea relacionada con resolución de incidencias ha encontrado e implementado una solución a la incidencia y lo ha comunicado al usuario.
