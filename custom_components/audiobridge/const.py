DOMAIN = "audiobridge"
DEFAULT_PORT = 23
DEFAULT_NAME = "AudioBRIDGE Matrix"
ZONE_COUNT = 8
SOURCE_COUNT = 8

DEFAULT_ZONE_NAMES = {
    f"zone_{index}_name": f"Zona {index}"
    for index in range(1, ZONE_COUNT + 1)
}

DEFAULT_SOURCE_NAMES = {
    f"source_{index}_name": f"Entrada {index}"
    for index in range(1, SOURCE_COUNT + 1)
}

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