# Dependencias reproducibles

KronoLearn usa `requirements.in` como fuente declarativa de dependencias directas y `requirements.txt` como lockfile
instalable. `requirements.txt` fija las dependencias directas y transitivas con versiones exactas. Actualmente no
incluye hashes de descarga.
No se utiliza Poetry.

## Instalación

Crear y activar un entorno virtual local; no instalar paquetes globalmente:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

`.venv/` está ignorado por el repositorio. Las versiones fijadas permiten reproducir la selección de paquetes; los
hashes de descarga quedan pendientes de incorporarse al lockfile.

## Actualización controlada

1. Actualizar una versión directa en `requirements.in` después de verificar su compatibilidad con Python 3.14.
2. En el entorno virtual, instalar o actualizar `pip-tools`:

   ```sh
   python3 -m pip install --upgrade pip pip-tools
   ```

3. Regenerar el lockfile con hashes:

   ```sh
   pip-compile --output-file=requirements.txt requirements.in
   ```

4. Reinstalar desde cero o verificar el archivo generado:

   ```sh
   python3 -m pip install -r requirements.txt
   ```

5. Ejecutar las validaciones locales definidas en `specs/001-project-foundation/tests-strategy.md`.

No editar manualmente las dependencias transitivas de `requirements.txt`; se resuelven desde `requirements.in`.
