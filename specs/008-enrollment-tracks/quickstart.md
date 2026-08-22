# Quickstart: Exploración e inscripción en tracks

## Prerrequisitos

- Rama `008-enrollment-tracks` con la feature 004 y el contenido de la feature 005 ya fusionados en `main` (dos tracks activos publicados).
- Entorno con PostgreSQL configurado según `kronolearn/settings/test.py`.
- Una cuenta de aprendiz activa para las pruebas manuales (`accounts` ya resuelto).

## Puesta en marcha

```powershell
python manage.py migrate --settings=kronolearn.settings.test
python manage.py test tests.learning.enrollment --settings=kronolearn.settings.test -v 2
```

No se requiere ninguna migración nueva ni variable de entorno adicional.

## Escenarios de validación

1. **Listado de tracks disponibles**
   - Iniciar sesión con una cuenta de aprendiz y abrir `learning:enrollment-list`.
   - Confirmar que cada track activo aparece con título, descripción y cantidad de módulos, y que un track retirado no aparece.

2. **Detalle de un track**
   - Desde el listado, abrir el detalle de un track disponible.
   - Confirmar que se ve la información completa y la acción de inscribirse.

3. **Inscripción única**
   - Enviar el formulario de inscripción para un track disponible.
   - Confirmar en `learning.services.enrollment.list_enrollments(account)` que existe exactamente una fila `Enrollment` para esa cuenta y ese track.

4. **Doble envío secuencial**
   - Repetir el envío de inscripción para el mismo track.
   - Confirmar que sigue existiendo una sola fila y que la respuesta no muestra ningún error.

5. **Track retirado o inexistente**
   - Solicitar el detalle o la inscripción de un track retirado, y por separado de un identificador inexistente.
   - Confirmar que ambas peticiones devuelven la misma respuesta `404` genérica y que no se crea ninguna inscripción.

6. **Aislamiento entre cuentas**
   - Con dos cuentas de aprendiz distintas, inscribir cada una en el mismo track.
   - Confirmar que cada una obtiene su propia inscripción y que ninguna puede ver ni modificar la inscripción de la otra a través de estas rutas.

7. **Acceso anónimo**
   - Solicitar cualquiera de las tres rutas sin sesión iniciada.
   - Confirmar la redirección al inicio de sesión conservando el destino solicitado.

## Verificación final

```powershell
ruff check .
ruff format --check .
python manage.py test tests.learning --settings=kronolearn.settings.test -v 2
python manage.py makemigrations --check --dry-run --settings=kronolearn.settings.test
```

Confirmar que `git diff HEAD --name-only` y `git ls-files --others --exclude-standard` solo listan los archivos declarados en la lista cerrada de `plan.md`.
