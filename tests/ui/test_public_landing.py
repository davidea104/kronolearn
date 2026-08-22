"""Public landing-page contracts."""

from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import Resolver404, resolve, reverse


class MainContentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_main = False
        self.found_main = False
        self.heading_count = 0
        self.links = []
        self.text_parts = []
        self.current_link = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "main":
            self.in_main = True
            self.found_main = True
            return
        if not self.in_main:
            return
        if tag == "h1":
            self.heading_count += 1
        if tag == "a":
            self.current_link = {
                "href": attributes.get("href"),
                "role": attributes.get("role"),
                "classes": attributes.get("class", "").split(),
                "text_parts": [],
            }

    def handle_endtag(self, tag):
        if tag == "a" and self.current_link is not None:
            self.current_link["text"] = " ".join(
                " ".join(self.current_link.pop("text_parts")).split()
            )
            self.links.append(self.current_link)
            self.current_link = None
        if tag == "main":
            self.in_main = False

    def handle_data(self, data):
        if not self.in_main:
            return
        self.text_parts.append(data)
        if self.current_link is not None:
            self.current_link["text_parts"].append(data)

    @property
    def text(self):
        return " ".join(" ".join(self.text_parts).split())


class PublicLandingTests(TestCase):
    def parse_main(self, response):
        parser = MainContentParser()
        parser.feed(response.content.decode())
        self.assertTrue(parser.found_main)
        return parser

    def test_root_resolves_to_ui_index(self):
        try:
            match = resolve("/")
        except Resolver404:
            self.fail("The public root must resolve to ui:index")

        self.assertEqual(match.view_name, "ui:index")

    def test_visitor_sees_public_landing_and_account_actions(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ui/index.html")
        main = self.parse_main(response)
        self.assertEqual(main.heading_count, 1)
        self.assertIn("KronoLearn", main.text)
        self.assertIn("aprendizaje", main.text.casefold())
        self.assertIn("decisiones", main.text.casefold())

        links = {link["text"]: link for link in main.links}
        expected_actions = {
            "Crear cuenta": reverse("accounts:register"),
            "Iniciar sesión": reverse("accounts:login"),
        }
        for label, href in expected_actions.items():
            with self.subTest(label=label):
                self.assertIn(label, links)
                self.assertEqual(links[label]["href"], href)
                self.assertEqual(links[label]["role"], "button")
                self.assertIn("button", links[label]["classes"])
        self.assertNotIn("Continuar aprendiendo", links)

    def test_visitor_landing_is_static_and_excludes_out_of_scope_sections(self):
        with self.assertNumQueries(0):
            response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        main_text = self.parse_main(response).text.casefold()
        for excluded_content in (
            "blog",
            "precios",
            "testimonios",
            "contacto",
            "idioma",
        ):
            with self.subTest(content=excluded_content):
                self.assertNotIn(excluded_content, main_text)

    def test_authenticated_account_sees_only_continue_action(self):
        account = get_user_model().objects.create_user(
            email="landing-learner@example.invalid",
            display_name="Landing Learner",
            password="correct-horse-battery-staple",
        )
        self.client.force_login(account)

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        main = self.parse_main(response)
        links = {link["text"]: link for link in main.links}
        self.assertEqual(set(links), {"Continuar aprendiendo"})
        continue_action = links["Continuar aprendiendo"]
        self.assertEqual(continue_action["href"], reverse("ui:learner-home"))
        self.assertEqual(continue_action["role"], "button")
        self.assertIn("button", continue_action["classes"])
