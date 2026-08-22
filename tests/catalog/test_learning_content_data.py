"""Contracts for immutable learning-content definitions."""

import importlib
import json
from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from django.test import SimpleTestCase


class LearningContentDefinitionTests(SimpleTestCase):
    def definitions_module(self):
        try:
            return importlib.import_module("catalog.content_data.definitions")
        except ModuleNotFoundError as exc:
            self.fail(f"Learning content definitions are missing: {exc.name}")

    def choice(self, position):
        return {
            "position": position,
            "text": f"Opcion ficticia {position}",
            "rating": "OPTIMAL" if position == 1 else "PARTIAL",
            "consequence": "Consecuencia ficticia",
            "explanation": "Explicacion ficticia",
        }

    def unit(self, position, *, marker_prefix, with_lab):
        return {
            "position": position,
            "source_marker": f"005/{marker_prefix}/{position}",
            "title": f"Unidad ficticia {position}",
            "learning_objective": "Comprender un concepto",
            "lesson_text": "Microleccion ficticia",
            "case_prompt": "Caso ficticio",
            "source": f"KronoLearn curriculum 005/{marker_prefix}/{position}",
            "reviewed_on": "2026-08-22",
            "choices": [self.choice(index) for index in range(1, 4)],
            "lab": (
                {
                    "objective": "Practicar",
                    "initial_prompt": "Inicia el ejercicio",
                    "expected_artifact": "Un archivo ficticio",
                    "verification_checklist": ["Verificar el resultado"],
                }
                if with_lab
                else None
            ),
            "legacy_fingerprint": None,
        }

    def track(self, *, title, marker_prefix, unit_count, with_labs):
        return {
            "title": title,
            "description": "Descripcion ficticia",
            "audience": "Equipo ficticio",
            "source": "KronoLearn curriculum 005",
            "reviewed_on": "2026-08-22",
            "legacy_titles": (
                ["Fundamentos de negocio para equipos tecnicos"]
                if title == "Fundamentos de negocio para equipos técnicos"
                else []
            ),
            "module": {
                "title": "Modulo ficticio",
                "objective": "Completar el recorrido",
                "source": "KronoLearn curriculum 005/module",
                "reviewed_on": "2026-08-22",
                "units": [
                    self.unit(
                        position,
                        marker_prefix=marker_prefix,
                        with_lab=with_labs,
                    )
                    for position in range(1, unit_count + 1)
                ],
            },
        }

    def valid_document(self):
        return {
            "tracks": [
                self.track(
                    title="Crea tu registro de gastos con agentes y SDD",
                    marker_prefix="principal",
                    unit_count=7,
                    with_labs=True,
                ),
                self.track(
                    title="Fundamentos de negocio para equipos técnicos",
                    marker_prefix="secondary",
                    unit_count=3,
                    with_labs=False,
                ),
            ]
        }

    def load_document(self, document):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "learning_units.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            return self.definitions_module().load_definitions(path)

    def test_load_definitions_returns_deeply_immutable_types(self):
        definitions = self.load_document(self.valid_document())

        self.assertIsInstance(definitions, tuple)
        self.assertEqual(len(definitions), 2)
        self.assertIsInstance(definitions[0].module.units, tuple)
        self.assertIsInstance(definitions[0].module.units[0].choices, tuple)
        self.assertIsInstance(
            definitions[0].module.units[0].lab.verification_checklist,
            tuple,
        )
        self.assertEqual(definitions[0].reviewed_on, date(2026, 8, 22))
        with self.assertRaises(FrozenInstanceError):
            definitions[0].title = "Alterado"

    def test_parser_rejects_unknown_missing_and_wrongly_typed_fields(self):
        documents = []

        unknown = self.valid_document()
        unknown["unexpected"] = True
        documents.append(unknown)

        missing = self.valid_document()
        del missing["tracks"][0]["module"]["units"][0]["title"]
        documents.append(missing)

        wrong_type = self.valid_document()
        wrong_type["tracks"][0]["module"]["units"][0]["position"] = "1"
        documents.append(wrong_type)

        for document in documents:
            with self.subTest(document=document), self.assertRaises(ValueError):
                self.load_document(document)

    def test_parser_rejects_invalid_json_before_returning_definitions(self):
        with NamedTemporaryFile(
            mode="w",
            suffix=".json",
            encoding="utf-8",
            delete=False,
        ) as content_file:
            content_file.write('{"tracks": [}')
            path = Path(content_file.name)
        self.addCleanup(path.unlink, missing_ok=True)

        with self.assertRaisesRegex(ValueError, "not valid JSON"):
            self.definitions_module().load_definitions(path)

    def test_approved_corpus_has_expected_topics_and_components(self):
        definitions = self.definitions_module().load_definitions()
        principal, secondary = definitions

        self.assertEqual(
            [definition.title for definition in definitions],
            [
                "Crea tu registro de gastos con agentes y SDD",
                "Fundamentos de negocio para equipos técnicos",
            ],
        )
        self.assertEqual(
            [unit.title for unit in principal.module.units],
            [
                "Define el problema, el usuario y el alcance mínimo",
                "Convierte necesidades en historias y criterios verificables",
                "Especifica datos, comportamiento y restricciones",
                "Organiza un plan en tareas pequeñas para el agente",
                "Implementa registro, listado y persistencia de gastos",
                "Prueba privacidad, seguridad y comportamiento",
                "Despliega, verifica y evalúa el resultado",
            ],
        )
        self.assertEqual(
            [unit.title for unit in secondary.module.units],
            [
                "Relaciona el problema con una propuesta de valor",
                "Compara costos, ingresos y prioridad",
                "Comunica riesgos a áreas no técnicas",
            ],
        )

        units = principal.module.units + secondary.module.units
        self.assertEqual(
            [len(unit.choices) for unit in units],
            [4, 3, 4, 3, 4, 4, 3, 3, 4, 3],
        )
        self.assertEqual(sum(unit.lab is not None for unit in units), 7)
        self.assertEqual(
            [unit.position for unit in principal.module.units], list(range(1, 8))
        )
        self.assertEqual(
            [unit.position for unit in secondary.module.units], list(range(1, 4))
        )
        self.assertEqual(
            len({unit.source_marker for unit in units}),
            len(units),
        )

        for unit in units:
            with self.subTest(unit=unit.source_marker):
                self.assertIn(unit.source_marker, unit.source)
                self.assertLessEqual(unit.reviewed_on, datetime.now(UTC).date())
                self.assertRegex(unit.case_prompt.casefold(), r"fictici|simulad")
                self.assertNotIn("@", unit.lesson_text + unit.case_prompt)
                self.assertEqual(
                    [choice.position for choice in unit.choices],
                    list(range(1, len(unit.choices) + 1)),
                )
                self.assertTrue(
                    any(choice.rating == "OPTIMAL" for choice in unit.choices)
                )
                self.assertTrue(
                    all(
                        choice.text
                        and choice.consequence
                        and choice.explanation
                        and choice.rating in {"OPTIMAL", "PARTIAL", "INCORRECT"}
                        for choice in unit.choices
                    )
                )
                if unit.lab is not None:
                    self.assertTrue(unit.lab.objective)
                    self.assertTrue(unit.lab.initial_prompt)
                    self.assertTrue(unit.lab.expected_artifact)
                    self.assertTrue(all(unit.lab.verification_checklist))

        self.assertEqual(
            [
                (unit.position, unit.legacy_fingerprint.source)
                for unit in units
                if unit.legacy_fingerprint is not None
            ],
            [(1, "KronoLearn demo"), (1, "KronoLearn demo")],
        )
