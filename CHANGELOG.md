# Changelog

Todos los cambios publicos relevantes de KronoLearn se documentan en este archivo.

## Unreleased

### Added

- Registro e inicio de sesion por correo canonico con cierre de sesion POST protegido por CSRF.
- Perfil propio privado que permite editar unicamente el nombre visible.
- Roles acumulativos `learner` y `content_admin`, gestionados por administradores de plataforma.
- Auditoria inmutable para cada intento autenticado de asignar o retirar el rol de contenido.
- Throttling persistente y progresivo por cuenta declarada y origen pseudonimizados.
- Pipeline CI con PostgreSQL 16, lint, formato, checks Django, drift de migraciones y suite completa.

### Changed

- La identidad principal usa `accounts.Account`, UUID y correo unico en lugar del modelo de usuario predeterminado de Django.

### Migration

- `AUTH_USER_MODEL = "accounts.Account"` debe estar configurado antes de ejecutar la primera migracion del proyecto.
- Los entornos que ya tengan tablas creadas con el usuario predeterminado de Django deben recrear una base vacia o seguir un plan de migracion de datos especifico antes de desplegar esta version. No se admite cambiar el modelo de usuario in-place como parte de esta feature.
