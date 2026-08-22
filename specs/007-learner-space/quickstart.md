# Quickstart: Validación del espacio de aprendizaje

## Prerequisitos

1. Activar el entorno virtual del proyecto e instalar `requirements.txt`.
2. Usar la rama `007-learner-space`.
3. Configurar las variables requeridas por `kronolearn.settings.test`.

Comprobar primero los contratos fundacionales:

```powershell
python manage.py test tests.learning.test_enrollment_contracts tests.learning.session.test_current_placeholder --settings=kronolearn.settings.test -v 2
```

Resultado esperado: el servicio aísla por cuenta, rechaza una cuenta que ya no está
activa, carga el track y publica `module_count` sin N+1. La ruta
`learning:session-current` debe poder revertirse con `track_id`.

## Validación automatizada enfocada

```powershell
python manage.py test tests.ui.test_learner_home --settings=kronolearn.settings.test -v 2
python manage.py check --settings=kronolearn.settings.test
ruff check learning/services/enrollment.py learning/urls/session.py learning/views/session ui/views.py tests/learning tests/ui
ruff format --check learning/services/enrollment.py learning/urls/session.py learning/views/session ui/views.py tests/learning tests/ui
```

Resultados esperados:

- una cuenta con dos inscripciones ve solo esos dos títulos, sus conteos y dos
  acciones a la sesión correspondiente;
- un track sin módulos muestra `0`;
- una cuenta sin inscripciones ve el estado vacío y el enlace al catálogo;
- dos cuentas no observan datos cruzados;
- un título con markup se presenta como texto, no como HTML;
- una solicitud anónima redirige al login con `next=/learn/`;
- una cuenta inactiva no recibe información privada;
- el login válido mantiene `/learn/` como destino.

## Suite de integración

```powershell
python manage.py test tests.ui tests.accounts.test_sessions tests.learning.test_enrollment_contracts tests.learning.session.test_current_placeholder --settings=kronolearn.settings.test -v 2
```

La matriz de CI vuelve a ejecutar `tests.ui` con PostgreSQL 16. Esta feature no
requiere una prueba de concurrencia ni una migración.

## Revisión de alcance

```powershell
git diff --name-only
```

Para la implementación de la 007 solo deben aparecer:

```text
ui/views.py
ui/templates/ui/learner_home.html
templates/ui/learner_home.html
templates/ui/components/card.html
tests/ui/
learning/services/enrollment.py
learning/urls/session.py
learning/views/session/
templates/learning/session/current.html
tests/learning/test_enrollment_contracts.py
tests/learning/session/test_current_placeholder.py
tests/integration/test_root_contracts.py
docs/contracts/domain-contracts.md
CHANGELOG.md
specs/007-learner-space/
```

La ruta bajo `ui/templates/` debe aparecer eliminada, no coexistir con la nueva
plantilla.

## Comprobación manual

```powershell
python manage.py runserver
```

1. Iniciar sesión con una cuenta activa que tenga dos inscripciones y abrir
   `http://127.0.0.1:8000/learn/`.
2. Confirmar título, conteo y acción independiente para cada track.
3. Recorrer las acciones con `Tab`; el foco debe ser visible y `Enter` debe abrir la
   ruta nombrada de la sesión del track correcto.
4. Repetir con una cuenta activa sin inscripciones y abrir el catálogo desde el
   estado vacío.
5. Verificar a 200% de zoom que el listado no se superpone y que cada acción conserva
   un área operable de al menos 44 por 44 píxeles.

El detalle completo de la respuesta esperada está en
[contracts/learner-home.md](contracts/learner-home.md).
