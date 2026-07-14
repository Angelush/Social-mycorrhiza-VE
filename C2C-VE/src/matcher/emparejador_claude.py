"""Proponente de Capa-3 respaldado por Claude — el núcleo estocástico inyectable detrás de
emparejador.emparejar().

Este módulo provee `crear_proponer_claude(...)`, que devuelve un callable
`proponer(context) -> list[dict]` respaldado por Claude vía el SDK de Anthropic. Es el ÚNICO
lugar donde se tocan la red/las claves, y se importa de forma PEREZOSA: `anthropic` se importa
dentro de la fábrica, nunca al inicio del módulo, para que `src/matcher/emparejador.py` (el
envoltorio determinista) y toda la suite de tests permanezcan importables y ejecutables offline
con un stub.

El modelo es un asistente-herramienta acotado al nivel PROPUESTA (architecture.md, FWK-030): se
le entrega sólo el contexto sanitizado y elegible que construyó el envoltorio, y devuelve una
lista acotada de emparejamientos propuestos. No tiene NINGUNA herramienta que conecte, notifique,
rankee o persista. Lo que devuelva se valida/acota/ordena canónicamente y se descarta si es
malo, por el envoltorio determinista — nunca se confía en el modelo (ver emparejador.py). Este
cliente es un adaptador delgado; el resguardo vive en emparejador.py.

Elección de modelo: `claude-sonnet-5` — un nivel apropiado para propuestas de emparejamiento
acotado de oferta/necesidad/meta (con conciencia de costo; el envoltorio, no el modelo, es la
superficie de corrección). Sobrescribir vía `model=`.

Procedencia: escrito por Claude (skill claude-api), resguardado por src/matcher/emparejador.py.
"""

# El esquema de salida estricto que el modelo debe devolver. Un campo de escalar-de-persona /
# engagement ni siquiera puede solicitarse aquí — y si el modelo lo contrabandea de todos modos,
# el escaneo de emparejador.py descarta esa propuesta.
_ESQUEMA_PROPUESTA = {
    "type": "object",
    "properties": {
        "propuestas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "ficha": {"type": "string"},
                    "tipo": {
                        "type": "string",
                        "enum": ["oferta_cubre_necesidad", "meta_compartida", "traduccion"],
                    },
                    "razon": {"type": "string"},
                },
                "required": ["ficha", "tipo", "razon"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["propuestas"],
    "additionalProperties": False,
}

_SISTEMA = (
    "Eres el núcleo, sólo-propuesta, de un emparejador prosocial (Micorriza Capa 3). "
    "Se te da las ofertas/necesidades/metas declaradas de un consultante y una lista de "
    "candidatos que han CONSENTIDO ser mostrados, cada uno con sus propias ofertas/necesidades/"
    "metas declaradas y su celula_id. Propón una lista acotada de candidatos emparejados, cada "
    "uno con una razón breve y legible por humanos que un humano leerá antes de decidir si "
    "contactar. Tipos: 'oferta_cubre_necesidad' (tu oferta cubre su necesidad o viceversa), "
    "'meta_compartida' (comparten una meta), 'traduccion' (una necesidad tendida entre dos de "
    "los propios contextos del consultante). Reglas que DEBES seguir: propón sólo candidatos "
    "que aparezcan en el contexto dado (nunca inventes una ficha); NUNCA emitas ningún puntaje, "
    "calificación, ranking, reputación, o número de engagement/click/relevancia sobre nadie; el "
    "ORDEN de tu lista no lleva significado (un envoltorio posterior lo reordena); tu objetivo "
    "es la cooperación iniciada, nunca el engagement. Propón, no impongas — un humano dispone."
)


def crear_proponer_claude(model: str = "claude-sonnet-5", max_proposals_hint: int = 10,
                          client=None):
    """Devuelve un callable `proponer(context) -> list[dict]` respaldado por Claude.

    Importa `anthropic` de forma perezosa (nunca al inicio del módulo). El callable devuelto es
    lo que inyectas como segundo argumento de `emparejador.emparejar(solicitud, proponer)`.
    Devuelve propuestas en bruto; el envoltorio determinista las valida, descarta, ordena
    canónicamente y acota.

    Args:
        model: id de modelo de Claude (nivel apropiado para propuestas).
        max_proposals_hint: sugerencia blanda al modelo; el envoltorio impone el
            propuestas_max duro.
        client: un cliente de Anthropic ya construido, opcional (principalmente para tests que
            quieren inyectar un SDK falso sin importar anthropic).
    """
    def proponer(context: dict) -> list:
        nonlocal client
        if client is None:
            import anthropic  # perezoso — sin red/claves a menos que este callable se invoque
            client = anthropic.Anthropic()

        import json
        user = (
            "Propón hasta " + str(max_proposals_hint) + " emparejamientos para este consultante.\n\n"
            + json.dumps(context, sort_keys=True, ensure_ascii=False)
        )
        # La salida estructurada fija la forma; pensamiento adaptativo según los valores por
        # defecto de claude-api.
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=_SISTEMA,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": _ESQUEMA_PROPUESTA}},
        )
        text = next((b.text for b in response.content if getattr(b, "type", None) == "text"), "")
        try:
            parsed = json.loads(text)
        except (ValueError, TypeError):
            return []  # un envoltorio que recibe [] simplemente no muestra nada — nunca un fallo
        propuestas = parsed.get("propuestas") if isinstance(parsed, dict) else None
        return propuestas if isinstance(propuestas, list) else []

    return proponer
