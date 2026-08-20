# Dependencias reproducibles

Política para la línea base: todas las dependencias deben fijarse en un archivo reproducible (`requirements.txt` con hashes o `poetry.lock`). Esto permite builds reproducibles en CI y despliegue.

Recomendación mínima:

- Crear `requirements.txt` con versiones fijas y hashes (pip-compile o `pip freeze` con control). Ejemplo de formato:

```
Django==5.2.4 --hash=sha256:...
gunicorn==21.2.0 --hash=sha256:...
psycopg[binary]==3.1.0 --hash=sha256:...
```

- Documentar el flujo para actualizar dependencias en esta misma página.
