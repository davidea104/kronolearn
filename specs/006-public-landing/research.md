# Phase 0 Research: Portada pública de KronoLearn

## Decision 1: Route and view ownership

**Decision**: Declare `path("", views.index, name="index")` in `ui/urls.py` and implement `index(request)` in `ui/views.py` as a direct render of `ui/index.html` with no decorator, service call or domain context.

**Rationale**: `kronolearn/urls.py` already includes `ui.urls` under the empty prefix, so the app-level empty path produces `/` and the namespace produces `ui:index`. A render-only view is the smallest public boundary and keeps the existing root composition frozen.

**Alternatives considered**:

- Add the route in `kronolearn/urls.py`: rejected because that file is closed and the existing include already delegates ownership to `ui`.
- Use a class-based template view: rejected because it adds indirection without configuration or extension needs.
- Redirect authenticated users from `/` to `/learn/`: rejected by the clarification that authenticated users remain on the public page and choose “Continuar aprendiendo”.

## Decision 2: Authentication-aware actions

**Decision**: Use the authenticated user already exposed to Django templates to render exactly one main action for an active authenticated account and two main actions for a visitor. Visitors receive links to `accounts:register` and `accounts:login`; authenticated accounts receive only a link to `ui:learner-home`.

**Rationale**: The choice implements the accepted clarification without adding a query, domain rule or duplicated authorization check. Access control remains owned by `/learn/`; the landing page only selects useful navigation.

**Alternatives considered**:

- Show all three actions to authenticated accounts: rejected because registration and login are incoherent after authentication and contradict the clarification.
- Redirect authenticated accounts automatically: rejected because the specification requires the landing page to remain available.
- Recheck account activity in the landing view: rejected because the feature may not redefine account authorization and `/learn/` remains the authoritative protected destination.

## Decision 3: Template composition and accessibility

**Decision**: Create `templates/ui/index.html`, extend `base.html`, use semantic heading and section markup, and render every primary action through `ui/components/button.html`. Use only existing global tokens and component styles; do not add JavaScript, remote media, forms or a new component.

**Rationale**: This follows the project template-root rule and the visual-system requirement to reuse published components. The shared base already provides Work Sans, visible focus, 44-pixel minimum targets, responsive typography and reduced-motion handling.

**Alternatives considered**:

- Hand-write anchor markup styled as buttons: rejected because it duplicates the required shared button component.
- Modify `base.html` or introduce a landing-specific stylesheet: rejected because `base.html` is closed and the page can be composed with existing layout and component primitives.
- Add decorative client-side behavior: rejected because it adds no value to the acceptance criteria and would expand the dependency and accessibility surface.

## Decision 4: Contract and regression testing

**Decision**: Add `tests/ui/test_public_landing.py` with focused Django tests for URL resolution, anonymous `200` rendering, static purpose copy, landing-content CTA destinations, authenticated CTA replacement and template usage. Re-run the existing learner-home tests plus the inactive-account and login-success tests as regression evidence.

**Rationale**: The new tests own only the new public surface and scope CTA assertions to the landing content so global navigation cannot satisfy them. Existing tests remain the source of truth for anonymous, active and inactive account behavior under `active_account_required` and for the `303` login redirect to `ui:learner-home`. This avoids duplicating account behavior in a UI feature.

**Alternatives considered**:

- Modify account or learner-home tests: rejected because those files and behaviors are closed.
- Test only rendered text: rejected because route names and destinations are explicit public contracts.
- Add browser automation as the sole check: rejected because route, response and conditional markup contracts are faster and more deterministic in the Django suite; keyboard and responsive behavior still receive a manual quickstart check.

## Decision 5: Public change documentation

**Decision**: Add one concise entry under `CHANGELOG.md` → `Unreleased` → `Added` describing the public landing page. No migration note is added.

**Rationale**: The root path changes from `Resolver404` to a successful public response, which is a public behavior change covered by the constitution. The feature changes no schema, configuration contract or persisted data, so no migration guidance applies.

**Alternatives considered**:

- Omit the changelog because it was absent from the supplied file list: rejected because the constitution explicitly requires release documentation for public behavior changes and governs conflicting feature artifacts.
- Add a migration section: rejected because there are no migrations or operator actions.

## Decision 6: Product acceptance of landing-page comprehension

**Decision**: Validate SC-002 through a timed acceptance review by the product owner. Without receiving an explanation of the page, the reviewer has 30 seconds to identify the platform purpose and both visitor access options; the result is recorded in the feature pull request.

**Rationale**: This implements the accepted clarification as a small, repeatable release gate while keeping subjective product comprehension outside automated rendering tests.

**Alternatives considered**:

- Test with five people unfamiliar with KronoLearn: rejected by the accepted clarification.
- Infer comprehension only from automated content assertions: rejected because presence of text does not prove that the intended message is understandable.

## Research Outcome

All technical context is resolved. There are no open technical questions, external integrations, persistence choices or new dependencies.
