DOMAIN = "audiobridge"
DEFAULT_PORT = 23
DEFAULT_NAME = "AudioBRIDGE Matrix"
ZONE_COUNT = 8
SOURCE_COUNT = 8
GROUP_COUNT = 4

DEFAULT_ZONE_NAMES = {
    f"zone_{index}_name": f"Zona {index}"
    for index in range(1, ZONE_COUNT + 1)
}

DEFAULT_SOURCE_NAMES = {
    f"source_{index}_name": f"Entrada {index}"
    for index in range(1, SOURCE_COUNT + 1)
}

DEFAULT_GROUP_NAMES = {
    f"group_{index}_name": f"Grupo {index}"
    for index in range(1, GROUP_COUNT + 1)
}


def parse_group_zone_ids(value):
    """Converte um conjunto de zonas em lista de ids válidos.

    Aceita strings como "1-3,5,8", listas e inteiros.
    """
    if value in (None, "", [], (), set()):
        return []

    if isinstance(value, int):
        values = [value]
    elif isinstance(value, str):
        values = [part.strip() for part in value.split(",") if part.strip()]
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]

    parsed = []
    seen = set()

    for item in values:
        if item is None:
            continue

        if isinstance(item, int):
            candidates = [item]
        else:
            text = str(item).strip()
            if not text:
                continue
            if "-" in text:
                try:
                    start, end = text.split("-", 1)
                    start_int = int(start)
                    end_int = int(end)
                    candidates = list(range(min(start_int, end_int), max(start_int, end_int) + 1))
                except (TypeError, ValueError):
                    continue
            else:
                try:
                    candidates = [int(text)]
                except ValueError:
                    continue

        for zone_id in candidates:
            if 1 <= int(zone_id) <= ZONE_COUNT and int(zone_id) not in seen:
                parsed.append(int(zone_id))
                seen.add(int(zone_id))

    return parsed


# Mapeamento das 8 entradas/fontes do equipamento
SOURCES = {
    "Entrada 1": 1,
    "Entrada 2": 2,
    "Entrada 3": 3,
    "Entrada 4": 4,
    "Entrada 5": 5,
    "Entrada 6": 6,
    "Entrada 7": 7,
    "Entrada 8": 8,
}