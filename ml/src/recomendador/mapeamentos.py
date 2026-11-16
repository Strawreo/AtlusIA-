"""
Ponte entre o vocabulário da Steam e o dos filmes.

Jogos e filmes não usam as mesmas palavras ("Souls-like" não aparece em nenhum filme),
então cada tag de jogo é "traduzida" para termos que existem no texto dos filmes.

Termos com espaço viram underscore, igual foi feito no texto dos filmes
("dark fantasy" -> "dark_fantasy"), para casar como uma palavra só.
Tags sem sentido temático (Singleplayer, Indie, Co-op...) ficam de fora de propósito.
"""

TAG_PARA_TERMOS = {
    # Fantasia / RPG
    "Fantasy":            ["Fantasy", "magic", "sword and sorcery"],
    "Dark Fantasy":       ["Fantasy", "dark fantasy", "sword and sorcery", "demon", "medieval", "knight"],
    "Souls-like":         ["dark fantasy", "sword and sorcery", "knight", "medieval", "demon", "survival"],
    "Difficult":          ["survival", "battle"],
    "RPG":                ["Fantasy", "Adventure", "magic", "sword and sorcery"],
    "JRPG":               ["anime", "Animation", "Fantasy", "magic"],
    "Medieval":           ["medieval", "knight", "castle", "History"],
    "Magic":              ["magic", "witch", "Fantasy"],
    "Dragons":            ["dragon", "Fantasy", "sword and sorcery"],
    "Open World":         ["Adventure", "journey", "road trip"],
    # Terror
    "Horror":             ["Horror", "monster", "supernatural", "ghost"],
    "Survival Horror":    ["Horror", "survival", "zombie", "monster"],
    "Psychological Horror": ["Horror", "psychological thriller", "insanity", "hallucination", "Thriller"],
    "Zombies":            ["zombie", "Horror", "post-apocalyptic", "survival"],
    "Gore":               ["gore", "blood", "slasher", "Horror"],
    # Ficção científica
    "Sci-fi":             ["Science Fiction", "future", "alien", "space"],
    "Space":              ["space", "Science Fiction", "spaceship", "alien"],
    "Cyberpunk":          ["cyberpunk", "dystopia", "artificial intelligence", "Science Fiction"],
    "Post-apocalyptic":   ["post-apocalyptic", "dystopia", "survival"],
    "Robots":             ["robot", "artificial intelligence", "Science Fiction"],
    "Aliens":             ["alien", "Science Fiction", "space"],
    "Time Travel":        ["time travel", "Science Fiction"],
    "Survival":           ["survival", "island", "wilderness"],
    # Ação / guerra
    "Action":             ["Action", "fight", "explosion"],
    "FPS":                ["Action", "shootout", "soldier", "gun"],
    "Shooter":            ["Action", "shootout", "gun"],
    "Military":           ["soldier", "army", "War"],
    "War":                ["War", "battle", "soldier"],
    "World War II":       ["world war ii", "War", "nazis", "soldier"],
    "Stealth":            ["spy", "assassin", "secret agent", "infiltration"],
    "Crime":              ["Crime", "gangster", "mafia", "heist"],
    "Heist":              ["heist", "robbery", "Crime"],
    "Superhero":          ["superhero", "super powers", "based on comic"],
    "Martial Arts":       ["martial arts", "fight", "kung fu"],
    "Fighting":           ["martial arts", "fight", "competition"],
    "Western":            ["Western", "cowboy", "sheriff"],
    "Pirates":            ["pirate", "ship", "treasure", "Adventure"],
    "Ninja":              ["ninja", "samurai", "martial arts", "japan"],
    # Esporte / corrida
    "Racing":             ["car race", "car chase", "car", "racing"],
    "Sports":             ["sport", "competition"],
    "Football":           ["football", "sport"],
    # Leve / narrativo
    "Cozy":               ["friendship", "small town", "Family", "Comedy"],
    "Relaxing":           ["friendship", "Family", "nature"],
    "Farming Sim":        ["farm", "small town", "rural setting", "Family"],
    "Cute":               ["Animation", "Family", "friendship"],
    "Anime":              ["anime", "Animation", "japan"],
    "Comedy":             ["Comedy", "spoof"],
    "Funny":              ["Comedy", "dark comedy"],
    "Romance":            ["Romance", "love", "falling in love"],
    "Story Rich":         ["Drama", "coming of age", "based on novel"],
    "Mystery":            ["Mystery", "investigation", "secret"],
    "Detective":          ["detective", "investigation", "murder", "Mystery"],
    "Historical":         ["History", "biography", "based on true story"],
    "Puzzle":             ["Mystery", "puzzle"],
}


def _limpa(termo: str) -> str:
    """'dark fantasy' -> 'dark_fantasy' (mesmo tratamento dado ao texto dos filmes)."""
    return termo.replace(" ", "_")


def tags_para_texto(tags: list[str]) -> str:
    """Converte as tags de um jogo num 'documento' no vocabulário dos filmes.

    Tags que não estão na tabela são ignoradas (não geram nenhum termo).
    """
    termos = []
    for tag in tags:
        termos.extend(_limpa(t) for t in TAG_PARA_TERMOS.get(tag, []))
    return " ".join(termos)
