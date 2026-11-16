"""
Bibliotecas de jogos fictícias (personas) para testar os recomendadores
até a integração com a API da Steam ficar pronta.

Formato de cada jogo: {"nome": str, "tags": [tags da Steam], "horas": horas jogadas}
"""

PERSONAS = {
    "Souls-like": [
        {"nome": "Elden Ring", "tags": ["Souls-like", "Dark Fantasy", "Open World", "RPG", "Difficult"], "horas": 180},
        {"nome": "Dark Souls III", "tags": ["Souls-like", "Dark Fantasy", "Difficult", "RPG"], "horas": 90},
        {"nome": "Bloodborne-like", "tags": ["Souls-like", "Horror", "Dark Fantasy", "Gore"], "horas": 40},
    ],
    "Cozy": [
        {"nome": "Stardew Valley", "tags": ["Farming Sim", "Cozy", "Relaxing", "Cute"], "horas": 200},
        {"nome": "Animal Crossing-like", "tags": ["Cute", "Relaxing", "Cozy"], "horas": 60},
        {"nome": "Spiritfarer", "tags": ["Cozy", "Story Rich", "Cute", "Relaxing"], "horas": 25},
    ],
    "FPS / Guerra": [
        {"nome": "Call of Duty", "tags": ["FPS", "Military", "War", "Action", "Shooter"], "horas": 300},
        {"nome": "Battlefield 1", "tags": ["FPS", "War", "Military", "Historical"], "horas": 80},
        {"nome": "Hell Let Loose", "tags": ["FPS", "World War II", "Military"], "horas": 30},
    ],
    "Sci-fi / Cyberpunk": [
        {"nome": "Cyberpunk 2077", "tags": ["Cyberpunk", "Open World", "RPG", "Sci-fi"], "horas": 120},
        {"nome": "Mass Effect", "tags": ["Sci-fi", "Space", "Story Rich", "RPG", "Aliens"], "horas": 70},
    ],
}
