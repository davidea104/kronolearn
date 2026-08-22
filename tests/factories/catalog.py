"""Deterministic factories for catalog entities and required relationships."""

from django.utils import timezone

from catalog.models import (
    Choice,
    ContentItem,
    ContentVersion,
    LabExercise,
    Module,
    Track,
)
from tests.factories.accounts import account_factory


def track_factory(**overrides) -> Track:
    title = overrides.pop("title", "Factory Track")
    defaults = {
        "description": "Factory track description",
        "audience": "Factory learners",
        "position": 101,
        "status": Track.Status.ACTIVE,
        "published_version": 1,
        **overrides,
    }
    track, _ = Track.objects.get_or_create(title=title, defaults=defaults)
    return track


def module_factory(**overrides) -> Module:
    track = overrides.pop("track", None) or track_factory()
    title = overrides.pop("title", "Factory Module")
    defaults = {
        "objective": "Factory objective",
        "position": 1,
        "status": Module.Status.ACTIVE,
        "published_version": 1,
        **overrides,
    }
    module, _ = Module.objects.get_or_create(
        track=track,
        title_key=title.casefold(),
        defaults={"title": title, **defaults},
    )
    return module


def content_item_factory(**overrides) -> ContentItem:
    module = overrides.pop("module", None) or module_factory()
    position = overrides.pop("position", 1)
    defaults = {
        "status": ContentItem.Status.PUBLISHED,
        "published_version": 1,
        **overrides,
    }
    item, _ = ContentItem.objects.get_or_create(
        module=module, position=position, defaults=defaults
    )
    return item


def content_version_factory(**overrides) -> ContentVersion:
    content_item = overrides.pop("content_item", None) or content_item_factory()
    author = overrides.pop("author", None) or account_factory()
    version_number = overrides.pop("version_number", 1)
    defaults = {
        "title": "Factory Content",
        "learning_objective": "Factory learning objective",
        "lesson_text": "Factory lesson",
        "case_prompt": "Factory case",
        "source": "Factory source",
        "author": author,
        "reviewed_on": timezone.localdate(),
        **overrides,
    }
    version, _ = ContentVersion.objects.get_or_create(
        content_item=content_item,
        version_number=version_number,
        defaults=defaults,
    )
    return version


def choice_factory(**overrides) -> Choice:
    content_version = (
        overrides.pop("content_version", None) or content_version_factory()
    )
    position = overrides.pop("position", 1)
    defaults = {
        "text": "Factory choice",
        "rating": Choice.Rating.OPTIMAL,
        "consequence": "Factory consequence",
        "explanation": "Factory explanation",
        **overrides,
    }
    choice, _ = Choice.objects.get_or_create(
        content_version=content_version,
        position=position,
        defaults=defaults,
    )
    return choice


def lab_exercise_factory(**overrides) -> LabExercise:
    content_version = (
        overrides.pop("content_version", None) or content_version_factory()
    )
    defaults = {
        "objective": "Factory lab objective",
        "initial_prompt": "Factory prompt",
        "expected_artifact": "Factory artifact",
        "verification_checklist": ["Run the factory check"],
        **overrides,
    }
    lab, _ = LabExercise.objects.get_or_create(
        content_version=content_version, defaults=defaults
    )
    return lab
