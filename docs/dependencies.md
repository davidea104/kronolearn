# Dependencias reproducibles

KronoLearn usa `requirements.in` como fuente declarativa de dependencias directas y `requirements.txt` como
artefacto reproducible instalable. `requirements.txt` fija las dependencias directas y transitivas con versiones
exactas y contiene hashes SHA-256 generados para cada artefacto. No se utiliza Poetry.

## Estado actual (resumen)

- Fuente declarativa: `requirements.in` (existe)
- Artefacto reproducible: `requirements.txt` (existe, versiones fijadas y hashes SHA-256 incluidos)

## Instalación

Crear y activar un entorno virtual local; no instalar paquetes globalmente:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

`.venv/` está ignorado por el repositorio. Las versiones fijadas y los hashes en `requirements.txt` permiten reproducir
la selección de paquetes y verificar la integridad de los artefactos descargados.

## Generar hashes

Este repositorio contiene un `requirements.txt` con hashes SHA-256 generados por `pip-compile`. Para regenerar el
lockfile con hashes use el entorno virtual del proyecto y el siguiente comando (exacto):

```sh
.venv/bin/pip-compile --generate-hashes --output-file=requirements.txt requirements.in
```

Notas:

- `pip-compile` calcula los hashes reales de los artefactos descargados; no agregue hashes manualmente.
- Asegúrese de ejecutar el comando en un entorno controlado y revisar los cambios antes de commitearlos.

## Actualización controlada (flujo recomendado)

1. Actualizar una versión directa en `requirements.in` tras validar compatibilidad con Python 3.14.
2. En el entorno virtual, instalar o actualizar `pip-tools` si no está disponible:

```sh
python3 -m pip install --upgrade pip pip-tools
```

3. Regenerar `requirements.txt` con hashes (si procede):

```sh
.venv/bin/pip-compile --generate-hashes --output-file=requirements.txt requirements.in
```

4. Verificar la instalación desde el lockfile (validando hashes):

```sh
.venv/bin/python -m pip install --require-hashes -r requirements.txt
```

5. Validar localmente las pruebas y comprobaciones (`ruff`, tests unitarios, etc.) según `specs/001-project-foundation/tests-strategy.md`.

No editar manualmente las dependencias transitivas de `requirements.txt`; se resuelven desde `requirements.in`.

## CI y Railway (recomendaciones)

- CI (GitHub Actions):
   - Si el workflow debe regenerar `requirements.txt` automáticamente, incluya un paso que instale `pip-tools` y ejecute
      `pip-compile --generate-hashes` en un job de mantenimiento. Alternativamente, regenere el lockfile localmente y
      haga commit del `requirements.txt` actualizado.
   - Para instalaciones en CI, preferible usar:

      ```sh
      python -m pip install --require-hashes -r requirements.txt
      ```

- Railway (producción):
   - Preferible: compilar/lockear dependencias antes del despliegue y desplegar con `requirements.txt` ya comprometido.
   - Si Railway debe ejecutar `pip install` en build, asegúrese de que el build step ejecuta:

      1) instalar Node/otros runtimes si procede;
      2) `python -m pip install -r requirements.txt` (no exponer `DATABASE_URL` ni secretos en logs);
      3) `python manage.py collectstatic --noinput` antes de iniciar Gunicorn.

## Cómo comprobar que el lockfile está actualizado

- Método rápido (manual): ejecutar `pip-compile --generate-hashes --output-file=requirements.txt requirements.in` y
   comprobar si el archivo resultante cambia. Si no hay cambios, el lockfile está actualizado.
- No ejecute este paso automáticamente en CI sin revisar cambios; preferible regenerarlo en un entorno controlado y
   revisar/commitear el resultado.


## Recomendaciones finales

- Mantener `requirements.in` como fuente de verdad para dependencias directas.
- Mantener `requirements.txt` como artefacto reproducible y versionado en el repositorio (ahora con hashes).
- Usar la opción `--generate-hashes` de `pip-compile` para regenerar el lockfile de forma reproducible.
- No editar manualmente dependencias transitivas ni hashes generados.
