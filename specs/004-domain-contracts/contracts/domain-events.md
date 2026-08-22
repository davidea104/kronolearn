# Domain Event Contracts

## `learning.signals.attempt_registered`

`attempt_registered` is a dedicated `django.dispatch.Signal` emitted by the future `learning.services.attempts.register_attempt` implementation.

### Attempt Envelope

```python
attempt_registered.send(
    sender=register_attempt,
    attempt=attempt,
    result=result,
)
```

| Argument | Contract |
| --- | --- |
| `sender` | The public `register_attempt` function |
| `attempt` | Newly persisted `learning.Attempt` |
| `result` | Frozen `learning.services.attempts.AttemptResult` for the same attempt |

Receivers accept `sender`, `attempt`, `result`, and `**kwargs` so additive signal metadata remains compatible.

### Delivery Semantics

1. The producer opens the encompassing `transaction.atomic` block.
2. It resolves the idempotency digest and either returns the prior result or creates one new attempt.
3. For a new attempt only, it constructs `AttemptResult` and calls `attempt_registered.send()` before commit.
4. Receivers execute synchronously in registration order.
5. Any receiver exception propagates and rolls back the attempt plus every earlier receiver write.
6. A retry after rollback may reuse the same idempotency key because no digest remains persisted.
7. A retry that finds a committed attempt returns its prior result without sending the event again.

`send_robust()` and `transaction.on_commit()` are outside this contract.

### Feature 004 Acceptance Boundary

Feature 004 does not invoke the STUB producer. Its contract test opens an explicit `transaction.atomic()` harness, creates test-owned rows, calls `attempt_registered.send()`, and verifies the envelope, receiver order, synchronous exception propagation, and rollback of harness and receiver writes. Creation, committed replay without re-emission, and same-key retry belong to the future feature that implements `register_attempt`.

## `learning.signals.session_completed`

`session_completed` is a dedicated `django.dispatch.Signal` emitted by the future daily-session producer.

### Session Envelope

```python
session_completed.send(
    sender=complete_session,
    enrollment=enrollment,
    completed_at=completed_at,
    idempotency_key=idempotency_digest,
)
```

| Argument | Contract |
| --- | --- |
| `sender` | The future daily-session completion function |
| `enrollment` | Persisted `learning.Enrollment` whose session completed |
| `completed_at` | Aware completion datetime interpreted in the project timezone |
| `idempotency_key` | Pre-derived 64-character HMAC digest; never a raw caller token |

Receivers accept all named arguments plus `**kwargs`. The future producer defines its canonical completion identity before implementation, derives the value through `security_digest`, and never dispatches the raw input.

### Delivery and Ownership

- Delivery is synchronous through `send()` inside the future producer transaction.
- Receiver exceptions propagate; `send_robust()` and `transaction.on_commit()` are outside the contract.
- `gamification` is the sole writer of `SeasonParticipation`.
- Persistence accepts a `ScoreEvent` with cause `session_completed`, amount zero, and no attempt without adding a cause-specific database constraint.
- The future gamification receiver, not Feature 004, guarantees that combination and uses the delivered digest before incrementing `completed_sessions`; database uniqueness makes replay idempotent.
- Feature 004 verifies the envelope, ordering, registration, propagation, and rollback with a transactional harness. It does not implement or test the functional producer.

### Consumer Registration

- `learning.apps.LearningConfig.ready()` imports `learning.receivers`, which registers only the progress hook for `attempt_registered`.
- `gamification.apps.GamificationConfig.ready()` imports `gamification.receivers`, which registers scoring, streak, and participation hooks for `attempt_registered` plus the participation hook for `session_completed`.
- Each receiver uses a stable `dispatch_uid` prefixed by its app and purpose.
- Producers import neither receiver module nor any progress, scoring, streak, or participation service.
- Receiver modules import the signal plus services owned by their own app only.

Example identifiers:

```text
learning.progress.on_attempt_registered
gamification.scoring.on_attempt_registered
gamification.streaks.on_attempt_registered
gamification.participation.on_attempt_registered
gamification.participation.on_session_completed
```

The infrastructure feature registers no-op receiver functions only if needed to prove wiring; domain behavior remains in the later owner features. Contract tests may connect a temporary receiver with `weak=False` and disconnect it in cleanup.

### Acceptance Matrix

| Scenario | Current feature evidence | Future producer evidence |
| --- | --- | --- |
| Named envelope | Temporary receiver observes each documented argument once | Producer emits after persisting its domain fact |
| Receiver order | Harness observes registration order | Producer uses synchronous `send()` |
| Receiver raises | Exception propagates and harness plus prior receiver writes roll back | Producer fact and all effects roll back |
| AppConfig `ready()` called repeatedly | One call per logical receiver, with only the documented event subset registered by each app | Same behavior under application startup |
| Committed replay and same-key retry | Not claimed while producers are STUBs | Implementing feature proves no re-emission after commit and reuse after rollback |
