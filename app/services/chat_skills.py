from dataclasses import dataclass
import re
import unicodedata

from ..scraping.boe_scraper import extraer_provincia


BLOCK_MESSAGE = "Pregunta algo relacionado con el BOE, por favor"

TOPIC_HINTS = (
    "boe",
    "boletin oficial del estado",
    "boletin oficial",
    "oposicion",
    "oposiciones",
    "empleo publico",
    "empleo público",
    "oferta de empleo publico",
    "oferta de empleo público",
    "empleo publico",
    "convocatoria",
    "convocatorias",
    "plaza",
    "plazas",
    "sumario",
    "bases",
    "requisitos",
    "anexo",
    "plazo",
    "turno libre",
    "promocion interna",
    "promoción interna",
    "lista de admitidos",
    "lista de excluidos",
    "tribunal",
    "admitidos",
    "excluidos",
    "solicitud",
    "solicitudes",
    "proceso selectivo",
)

SEARCH_HINTS = (
    "buscar",
    "busca",
    "busqueda",
    "búsqueda",
    "encuentra",
    "donde sale",
    "dónde sale",
    "donde aparece",
    "dónde aparece",
    "muéstrame",
    "muestrame",
    "que plazas hay",
    "qué plazas hay",
    "plazas hay",
    "convocatorias hay",
    "filtrar",
    "filtra",
    "filtro",
    "mostrar",
    "listar",
    "consultar",
    "encontrar",
    "localizar",
    "oposiciones en",
    "convocatorias en",
    "plazas en",
    "por provincia",
    "por departamento",
    "por fecha",
    "por titulo",
    "por título",
    "por municipio",
    "por localidad",
    "por ayuntamiento",
)

SUMMARY_HINTS = (
    "resum",
    "resumen",
    "hazme un resumen",
    "explica",
    "explic",
    "detalla",
    "cuentame",
    "cuéntame",
    "leer",
    "lectura",
    "sintet",
    "puntos clave",
    "que dice",
    "qué dice",
    "que pone",
    "qué pone",
    "que contiene",
    "qué contiene",
    "convocatoria",
    "bases",
    "requisitos",
    "resumen de la convocatoria",
    "bases de la convocatoria",
    "requisitos de acceso",
    "plazo de presentación",
    "plazo de solicitudes",
    "fecha limite",
    "fecha límite",
    "oferta de empleo",
)

LATEST_HINTS = (
    "hoy",
    "ultim",
    "últim",
    "ultimo",
    "último",
    "reciente",
    "recientes",
    "ultimo boe",
    "último boe",
    "nueva",
    "nuevas",
    "novedad",
    "novedades",
    "publicad",
    "publicado hoy",
    "publicadas hoy",
    "que hay nuevo",
    "qué hay nuevo",
    "oposiciones vigentes",
    "convocatorias vigentes",
    "publicado esta semana",
    "publicado este mes",
)

PROVINCE_HINTS = (
    "provincia",
    "provincias",
    "departamento",
    "departamentos",
    "ministerio",
    "comunidad",
    "autonoma",
    "autónoma",
    "ayuntamiento",
    "localidad",
    "valencia",
    "madrid",
    "sevilla",
    "barcelona",
    "alicante",
    "malaga",
    "málaga",
    "girona",
    "cadiz",
    "cádiz",
    "murcia",
    "zaragoza",
    "granada",
    "cordoba",
    "córdoba",
)

INTENT_SYNONYMS = {
    "boe_topic": TOPIC_HINTS,
    "search_intent": SEARCH_HINTS,
    "summary_intent": SUMMARY_HINTS,
    "latest_intent": LATEST_HINTS,
    "location_intent": PROVINCE_HINTS,
    # Small extra normalization groups for frequent BOE wording variants.
    "oep_topic": (
        "oep",
        "oferta empleo publico",
        "oferta de empleo publico",
        "oferta de empleo público",
    ),
    "selection_list_topic": (
        "lista admitidos",
        "lista de admitidos",
        "lista excluidos",
        "lista de excluidos",
    ),
}

TOPIC_INTENTS = {
    "boe_topic",
    "oep_topic",
    "selection_list_topic",
    "search_intent",
    "summary_intent",
    "latest_intent",
    "location_intent",
    "province_name",
}

STRICT_DOMAIN_INTENTS = {
    "boe_topic",
    "oep_topic",
    "selection_list_topic",
}

SEARCH_INTENTS = {"search_intent"}
SUMMARY_INTENTS = {"summary_intent", "selection_list_topic"}
LATEST_INTENTS = {"latest_intent"}
LOCATION_INTENTS = {"location_intent", "province_name"}


@dataclass(frozen=True)
class ChatSkillDecision:
    blocked: bool
    block_message: str | None = None
    skill_name: str | None = None
    extra_instructions: str | None = None


def _normalize_text(text):
    normalized = unicodedata.normalize("NFKD", text or "")
    normalized = "".join(character for character in normalized if not unicodedata.combining(character))
    normalized = normalized.lower()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _contains_any(text, phrases):
    return any(phrase in text for phrase in phrases)


def _extract_intent_context(normalized_text, raw_text):
    context = set()

    for concept, phrases in INTENT_SYNONYMS.items():
        if _contains_any(normalized_text, phrases):
            context.add(concept)

    if extraer_provincia(raw_text):
        context.add("province_name")

    return context


def _has_any_intent(intent_context, intent_names):
    return any(intent in intent_context for intent in intent_names)


def _has_boe_domain_clue(intent_context):
    if _has_any_intent(intent_context, STRICT_DOMAIN_INTENTS):
        return True

    # Allow province-based queries only when they also look like search/filter requests.
    if "province_name" in intent_context and _has_any_intent(intent_context, {"search_intent", "location_intent"}):
        return True

    return False


def scope_blocker_skill(intent_context):
    if _has_any_intent(intent_context, TOPIC_INTENTS):
        return None
    return ChatSkillDecision(blocked=True, block_message=BLOCK_MESSAGE, skill_name="scope_blocker")


def boe_search_and_filter_skill(intent_context):
    if not _has_any_intent(intent_context, SEARCH_INTENTS):
        return None

    return ChatSkillDecision(
        blocked=False,
        skill_name="boe_search_and_filter",
        extra_instructions=(
            "Prioriza respuestas prácticas sobre búsqueda y filtrado de oposiciones del BOE. "
            "Ayuda con palabras clave, provincia, fecha, departamento, título y número de identificador. "
            "Si faltan datos, pide una aclaración breve antes de inventar resultados."
        ),
    )


def convocatoria_summary_skill(intent_context):
    if not _has_any_intent(intent_context, SUMMARY_INTENTS):
        return None

    return ChatSkillDecision(
        blocked=False,
        skill_name="convocatoria_summary",
        extra_instructions=(
            "Resume la convocatoria de forma breve y clara. "
            "Destaca qué es, a quién va dirigida, qué pide, fechas importantes y cómo leer la publicación. "
            "No te vayas a temas fuera del BOE."
        ),
    )


def latest_updates_skill(intent_context):
    if not _has_any_intent(intent_context, LATEST_INTENTS):
        return None

    return ChatSkillDecision(
        blocked=False,
        skill_name="latest_updates",
        extra_instructions=(
            "Responde sobre las novedades más recientes del BOE y oposiciones. "
            "Si el usuario no indica fecha, asume que quiere lo publicado hoy o en los últimos días y pídele aclaración si hace falta."
        ),
    )


def province_department_focus_skill(intent_context):
    if not _has_any_intent(intent_context, LOCATION_INTENTS):
        return None

    return ChatSkillDecision(
        blocked=False,
        skill_name="province_department_focus",
        extra_instructions=(
            "Enfoca la respuesta en la provincia o departamento indicado. "
            "Si el usuario menciona una provincia, ayúdale a afinar la búsqueda con ese criterio. "
            "Si solo da un departamento, pide la provincia o el filtro que falta."
        ),
    )


def get_chat_skill_decision(user_message):
    normalized_message = _normalize_text(user_message)
    intent_context = _extract_intent_context(normalized_message, user_message)

    if not _has_boe_domain_clue(intent_context):
        return ChatSkillDecision(blocked=True, block_message=BLOCK_MESSAGE, skill_name="scope_blocker")

    for skill in (
        boe_search_and_filter_skill,
        province_department_focus_skill,
        latest_updates_skill,
        convocatoria_summary_skill,
    ):
        decision = skill(intent_context)
        if decision is not None:
            return decision

    return ChatSkillDecision(blocked=False, skill_name="general_boe", extra_instructions=None)