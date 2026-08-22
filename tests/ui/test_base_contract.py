"""Fast rendered-HTML tests for the shared base template."""

from django.contrib.auth.models import AnonymousUser
from django.template import engines
from django.test import RequestFactory, SimpleTestCase


class BaseTemplateContractTests(SimpleTestCase):
    def test_stable_blocks_render_in_their_document_regions(self):
        template = engines["django"].from_string(
            """{% extends "base.html" %}
            {% block title %}Contract title{% endblock %}
            {% block main %}MAIN:{% block content %}CONTENT{% endblock %}{% endblock %}
            {% block sidebar %}SIDEBAR{% endblock %}
            {% block fragments %}FRAGMENTS{% endblock %}
            {% block scripts %}<script>void 0</script>{% endblock %}"""
        )
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        html = template.render({"primary_navigation": ()}, request=request)
        self.assertIn("<title>Contract title</title>", html)
        self.assertIn("<main", html)
        self.assertIn("MAIN:CONTENT", html)
        self.assertLess(html.index("</main>"), html.index("SIDEBAR"))
        self.assertLess(html.index("SIDEBAR"), html.index("FRAGMENTS"))
        self.assertLess(html.index("FRAGMENTS"), html.index("<script>void 0</script>"))

    def test_semantic_navigation_and_visible_focus_rule_are_rendered(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        template = engines["django"].get_template("base.html")
        html = template.render({"primary_navigation": ()}, request=request)
        self.assertIn('<nav aria-label="Navegación principal">', html)
        self.assertIn("a:focus-visible", html)
        self.assertIn("outline: 2px solid var(--border)", html)
