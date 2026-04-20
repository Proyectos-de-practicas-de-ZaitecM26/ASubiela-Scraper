import unittest
from unittest.mock import patch

from app import create_app
from app.chatbot import _build_system_prompt
from app.services.chat_skills import get_chat_skill_decision


class ChatSkillsDecisionTests(unittest.TestCase):
    def test_blocks_off_topic_messages(self):
        decision = get_chat_skill_decision("Como hago una tortilla de patatas?")

        self.assertTrue(decision.blocked)
        self.assertEqual(
            decision.block_message,
            "Pregunta algo relacionado con el BOE, por favor",
        )

    def test_allows_boe_related_messages(self):
        decision = get_chat_skill_decision("Busca oposiciones en Madrid para hoy")

        self.assertFalse(decision.blocked)
        self.assertIsNotNone(decision.skill_name)

    def test_allows_alternative_search_wording(self):
        decision = get_chat_skill_decision("Muéstrame donde sale la convocatoria por provincia de Valencia")

        self.assertFalse(decision.blocked)
        self.assertIn(decision.skill_name, {"boe_search_and_filter", "province_department_focus", "convocatoria_summary"})

    def test_allows_summary_wording_without_literal_keyword(self):
        decision = get_chat_skill_decision("Hazme un resumen de esta convocatoria y dime que contiene")

        self.assertFalse(decision.blocked)
        self.assertEqual(decision.skill_name, "convocatoria_summary")

    def test_allows_latest_updates_wording(self):
        decision = get_chat_skill_decision("Que hay nuevo en el ultimo boe")

        self.assertFalse(decision.blocked)
        self.assertEqual(decision.skill_name, "latest_updates")

    def test_detects_boe_reference_summary(self):
        decision = get_chat_skill_decision("resumen del boe-a-2026-8444")

        self.assertFalse(decision.blocked)
        self.assertEqual(decision.skill_name, "boe_reference_summary")
        self.assertIsNotNone(decision.extra_instructions)
        self.assertIn("BOE-A-2026-8444", decision.extra_instructions)
        self.assertIsNotNone(decision.direct_answer)
        self.assertIn("BOE-A-2026-8444", decision.direct_answer)

    def test_allows_vigente_style_wording(self):
        decision = get_chat_skill_decision("Quiero ver oposiciones vigentes y convocatorias vigentes")

        self.assertFalse(decision.blocked)
        self.assertEqual(decision.skill_name, "latest_updates")

    def test_allows_bases_and_requisitos_wording(self):
        decision = get_chat_skill_decision("Bases de la convocatoria y requisitos de acceso")

        self.assertFalse(decision.blocked)
        self.assertIn(decision.skill_name, {"convocatoria_summary", "general_boe"})

    def test_allows_plazas_y_provincia_wording(self):
        decision = get_chat_skill_decision("Qué plazas hay por provincia de Girona")

        self.assertFalse(decision.blocked)
        self.assertIn(decision.skill_name, {"boe_search_and_filter", "province_department_focus"})

    def test_normalizes_oep_wording(self):
        decision = get_chat_skill_decision("Quiero ver la OEP publicada este mes")

        self.assertFalse(decision.blocked)
        self.assertIn(decision.skill_name, {"latest_updates", "general_boe"})

    def test_normalizes_admitidos_excluidos_wording(self):
        decision = get_chat_skill_decision("Necesito la lista admitidos y la lista excluidos")

        self.assertFalse(decision.blocked)
        self.assertEqual(decision.skill_name, "convocatoria_summary")

    def test_blocks_obvious_non_boe_content_even_with_question_style(self):
        decision = get_chat_skill_decision("Podrias explicarme como hacer una paella?")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.skill_name, "scope_blocker")

    def test_blocks_random_non_boe_question(self):
        decision = get_chat_skill_decision("Cuales son los mejores ejercicios para espalda?")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.skill_name, "scope_blocker")

    def test_blocks_non_boe_trending_wording(self):
        decision = get_chat_skill_decision("Que pasa con el futbol hoy?")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.skill_name, "scope_blocker")

    def test_allows_legal_followup_summary_without_literal_boe(self):
        decision = get_chat_skill_decision("resumen del artículo 5 de esa norma")

        self.assertFalse(decision.blocked)
        self.assertIn(decision.skill_name, {"convocatoria_summary", "general_boe"})

    def test_allows_legal_followup_deadline_question(self):
        decision = get_chat_skill_decision("si se publicó el 2026-04-20, cuál es la fecha límite exacta")

        self.assertFalse(decision.blocked)
        self.assertIn(decision.skill_name, {"latest_updates", "convocatoria_summary", "general_boe"})

    def test_allows_legal_cross_reference_wording(self):
        decision = get_chat_skill_decision("explica el artículo citado en la disposición adicional si no viene en el texto")

        self.assertFalse(decision.blocked)
        self.assertIn(decision.skill_name, {"convocatoria_summary", "general_boe"})


class ChatbotRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(TESTING=True)

    def test_route_blocks_off_topic_messages(self):
        client = self.app.test_client()

        response = client.post(
            "/api/chatbot",
            json={"message": "Como hago una tortilla de patatas?"},
        )

        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(
            payload["answer"],
            "Pregunta algo relacionado con el BOE, por favor",
        )

    def test_route_uses_chatbot_fallback_for_boe_messages(self):
        client = self.app.test_client()

        with patch("app.routes.main.chatbot", return_value="Respuesta simulada") as mocked_chatbot:
            response = client.post(
                "/api/chatbot",
                json={"message": "Busca oposiciones en Madrid para hoy"},
            )

        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["answer"], "Respuesta simulada")
        mocked_chatbot.assert_called_once()

    def test_route_blocks_alternative_off_topic_wording(self):
        client = self.app.test_client()

        response = client.post(
            "/api/chatbot",
            json={"message": "Podrias explicarme como hacer una paella?"},
        )

        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(
            payload["answer"],
            "Pregunta algo relacionado con el BOE, por favor",
        )

    def test_route_allows_more_flexible_boe_wording(self):
        client = self.app.test_client()

        with patch("app.routes.main.chatbot", return_value="Respuesta flexible") as mocked_chatbot:
            response = client.post(
                "/api/chatbot",
                json={"message": "Muéstrame donde sale la convocatoria por provincia de Valencia"},
            )

        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["answer"], "Respuesta flexible")
        mocked_chatbot.assert_called_once()

    def test_route_blocks_latest_non_boe_style_question(self):
        client = self.app.test_client()

        response = client.post(
            "/api/chatbot",
            json={"message": "Que pasa con el futbol hoy?"},
        )

        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(
            payload["answer"],
            "Pregunta algo relacionado con el BOE, por favor",
        )

    def test_route_uses_reference_summary_path(self):
        client = self.app.test_client()

        with patch("app.routes.main.chatbot", return_value="Resumen referencia") as mocked_chatbot:
            response = client.post(
                "/api/chatbot",
                json={"message": "resumen del boe-a-2026-8444"},
            )

        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["ok"])
        self.assertIn("BOE-A-2026-8444", payload["answer"])
        mocked_chatbot.assert_not_called()

    def test_system_prompt_uses_full_prompt_always(self):
        prompt = _build_system_prompt()

        self.assertIn("ROL Y MISIÓN", prompt)
        self.assertIn("RESTRICCIONES ESTRICTAS", prompt)
        self.assertIn("FALLBACK ESTÁNDAR", prompt)


if __name__ == "__main__":
    unittest.main()