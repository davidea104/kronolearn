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

    def test_dark_mode_toggle_contract(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        template = engines["django"].get_template("base.html")
        html = template.render({"primary_navigation": ()}, request=request)
        self.assertEqual(html.count("data-theme-toggle aria-pressed"), 1)
        self.assertIn('aria-pressed="false"', html)
        self.assertIn(':root[data-theme="dark"]', html)
        self.assertIn('src="/static/js/theme-toggle.js"', html)

    def test_theme_toggle_is_a_chromeless_icon_with_accessible_name(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        template = engines["django"].get_template("base.html")
        html = template.render({"primary_navigation": ()}, request=request)
        self.assertIn('class="theme-toggle"', html)
        self.assertIn("theme-toggle__tooltip", html)
        self.assertIn('aria-label="Cambiar a modo oscuro"', html)

    def test_anti_fouc_script_runs_before_style_and_toggle_script(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        template = engines["django"].get_template("base.html")
        html = template.render({"primary_navigation": ()}, request=request)
        anti_fouc_index = html.index("kronolearn:theme")
        toggle_script_index = html.index('src="/static/js/theme-toggle.js"')
        style_index = html.index("<style>")
        self.assertLess(anti_fouc_index, toggle_script_index)
        self.assertLess(anti_fouc_index, style_index)
