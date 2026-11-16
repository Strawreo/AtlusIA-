# Comparação: TF-IDF puro x Híbrido (TF-IDF + Fatoração de Matrizes)

Gerado por `notebooks/04_comparar_filmes.py`.

- Catálogo: 9106 filmes; 7665 estão no modelo de fatoração.
- TF-IDF puro: `score = 0.85 * tfidf + 0.15 * nota/10`.
- Híbrido: `score = ALFA * colab + (1 - ALFA) * tfidf + 0.1 * nota/10` (30 sementes); filmes fora do modelo: `tfidf + 0.1 * nota/10`.
- Métricas: `iguais_tfidf` = filmes em comum com o top-10 do TF-IDF puro; `tfidf_medio` = aderência ao tema dos jogos; `nota_media` = vote_average médio; `votos_mediana` = popularidade.

## Persona: Souls-like

Jogos: Elden Ring (180h), Dark Souls III (90h), Bloodborne-like (40h)

### Top-10 lado a lado

| # | TF-IDF puro | Híbrido α=0.3 | Híbrido α=0.6 | Híbrido α=0.9 |
|---|---|---|---|---|
| 1 | Nightbreed (1990) | DragonHeart (1996) | Beowulf & Grendel (2005) | Wishmaster (1997) |
| 2 | DragonHeart (1996) | Conan the Barbarian (2011) | Wishmaster (1997) | Impostor (2001) |
| 3 | Onibaba (1964) | Red Sonja (1985) | Leviathan (1989) | Leviathan (1989) |
| 4 | Black Death (2010) | Beowulf & Grendel (2005) | Red Sonja (1985) | Max Payne (2008) |
| 5 | Your Highness (2011) | Last Knights (2015) | Impostor (2001) | The Stepfather (2009) |
| 6 | Dragonheart 3: The Sorcerer's Curse (2015) | Black Knight (2001) | Reign of Fire (2002) | Judge Dredd (1995) |
| 7 | Seventh Son (2014) | Solomon Kane (2009) | Gods of Egypt (2016) | 13 Sins (2014) |
| 8 | Excalibur (1981) | Dragonslayer (1981) | Conan the Barbarian (2011) | Fist Fight (2017) |
| 9 | Journey to the West: Conquering the Demons (2013) | The Visitors II: The Corridors of Time (1998) | Cirque du Freak: The Vampire's Assistant (2009) | Gods of Egypt (2016) |
| 10 | DragonHeart: A New Beginning (2000) | Your Highness (2011) | 13 Sins (2014) | The Punisher (1989) |

### Métricas

| Modelo | iguais_tfidf | tfidf_medio | nota_media | votos_mediana |
|---|---|---|---|---|
| TF-IDF puro | 10.0 | 0.194 | 6.06 | 173.5 |
| Híbrido α=0.3 | 2.0 | 0.162 | 5.71 | 319.5 |
| Híbrido α=0.6 | 0.0 | 0.059 | 5.69 | 282.5 |
| Híbrido α=0.9 | 0.0 | 0.008 | 5.68 | 255.5 |

### Detalhes (scores e explicação)

**TF-IDF puro**

| title | vote_average | similaridade | porque |
|---|---|---|---|
| Nightbreed | 6.4 | 0.211 | dark fantasy, fantasy, monster |
| DragonHeart | 6.4 | 0.198 | knight, medieval, fantasy |
| Onibaba | 7.6 | 0.174 | medieval, demon, survival |
| Black Death | 5.9 | 0.204 | medieval, knight, horror |
| Your Highness | 5.2 | 0.215 | sword and sorcery, knight, fantasy |
| Dragonheart 3: The Sorcerer's Curse | 4.5 | 0.215 | knight, medieval, fantasy |
| Seventh Son | 5.2 | 0.202 | dark fantasy, sword and sorcery, fantasy |
| Excalibur | 7.1 | 0.167 | sword and sorcery, knight, fantasy |
| Journey to the West: Conquering the Demons | 6.8 | 0.168 | demon, fantasy, adventure |
| DragonHeart: A New Beginning | 5.5 | 0.186 | knight, medieval, fantasy |

**Híbrido α=0.3**

| title | vote_average | tfidf | colab | score | porque |
|---|---|---|---|---|---|
| DragonHeart | 6.4 | 0.198 | 0.664 | 0.402 | knight, medieval, fantasy \| parecido com Alice Through the Looking Glass |
| Conan the Barbarian | 5.2 | 0.167 | 0.767 | 0.399 | sword and sorcery, fantasy, battle \| parecido com Seventh Son |
| Red Sonja | 5.0 | 0.151 | 0.794 | 0.394 | sword and sorcery, fantasy, magic \| parecido com DragonHeart |
| Beowulf & Grendel | 6.1 | 0.133 | 0.799 | 0.394 | sword and sorcery, fantasy, battle \| parecido com Conan the Barbarian |
| Last Knights | 6.2 | 0.167 | 0.666 | 0.379 | medieval, knight, adventure \| parecido com Black Knight |
| Black Knight | 5.1 | 0.177 | 0.677 | 0.378 | medieval, knight, fantasy \| parecido com The Visitors II: The Corridors of Time |
| Solomon Kane | 5.6 | 0.118 | 0.747 | 0.363 | sword and sorcery, fantasy, adventure \| parecido com Seventh Son |
| Dragonslayer | 6.5 | 0.117 | 0.719 | 0.363 | sword and sorcery, fantasy, magic \| parecido com Nightbreed |
| The Visitors II: The Corridors of Time | 5.8 | 0.174 | 0.601 | 0.36 | medieval, knight, demon \| parecido com Black Knight |
| Your Highness | 5.2 | 0.215 | 0.521 | 0.359 | sword and sorcery, knight, fantasy \| parecido com Black Knight |

**Híbrido α=0.6**

| title | vote_average | tfidf | colab | score | porque |
|---|---|---|---|---|---|
| Beowulf & Grendel | 6.1 | 0.133 | 0.799 | 0.594 | sword and sorcery, fantasy, battle \| parecido com Conan the Barbarian |
| Wishmaster | 5.6 | 0.008 | 0.887 | 0.591 | horror \| parecido com Black Knight |
| Leviathan | 6.0 | 0.023 | 0.863 | 0.587 | adventure, monster, horror \| parecido com Red Sonja |
| Red Sonja | 5.0 | 0.151 | 0.794 | 0.587 | sword and sorcery, fantasy, magic \| parecido com DragonHeart |
| Impostor | 6.1 | 0.0 | 0.872 | 0.584 | parecido com DragonHeart |
| Reign of Fire | 6.0 | 0.035 | 0.844 | 0.581 | fantasy, adventure \| parecido com DragonHeart |
| Gods of Egypt | 5.2 | 0.031 | 0.859 | 0.58 | fantasy \| parecido com DragonHeart |
| Conan the Barbarian | 5.2 | 0.167 | 0.767 | 0.579 | sword and sorcery, fantasy, battle \| parecido com Seventh Son |
| Cirque du Freak: The Vampire's Assistant | 5.5 | 0.036 | 0.848 | 0.578 | fantasy, adventure \| parecido com Conan the Barbarian |
| 13 Sins | 6.2 | 0.007 | 0.854 | 0.577 | horror \| parecido com Conan the Barbarian |

**Híbrido α=0.9**

| title | vote_average | tfidf | colab | score | porque |
|---|---|---|---|---|---|
| Wishmaster | 5.6 | 0.008 | 0.887 | 0.855 | horror \| parecido com Black Knight |
| Impostor | 6.1 | 0.0 | 0.872 | 0.846 | parecido com DragonHeart |
| Leviathan | 6.0 | 0.023 | 0.863 | 0.839 | adventure, monster, horror \| parecido com Red Sonja |
| Max Payne | 5.2 | 0.0 | 0.873 | 0.838 | parecido com Conan the Barbarian |
| The Stepfather | 5.4 | 0.007 | 0.868 | 0.836 | horror \| parecido com Black Knight |
| Judge Dredd | 5.4 | 0.0 | 0.867 | 0.834 | parecido com DragonHeart |
| 13 Sins | 6.2 | 0.007 | 0.854 | 0.832 | horror \| parecido com Conan the Barbarian |
| Fist Fight | 6.2 | 0.0 | 0.852 | 0.829 | parecido com Your Highness |
| Gods of Egypt | 5.2 | 0.031 | 0.859 | 0.828 | fantasy \| parecido com DragonHeart |
| The Punisher | 5.5 | 0.006 | 0.855 | 0.825 | adventure \| parecido com Black Knight |

## Persona: Cozy

Jogos: Stardew Valley (200h), Animal Crossing-like (60h), Spiritfarer (25h)

### Top-10 lado a lado

| # | TF-IDF puro | Híbrido α=0.3 | Híbrido α=0.6 | Híbrido α=0.9 |
|---|---|---|---|---|
| 1 | Miss You Already (2015) | The Fox and the Hound (1981) | The Fox and the Hound (1981) | Guys and Dolls (1955) |
| 2 | Barbie as The Princess & the Pauper (2004) | Corrina, Corrina (1994) | An American Tail (1986) | From Up on Poppy Hill (2011) |
| 3 | Over the Garden Wall (2014) | Spirit: Stallion of the Cimarron (2002) | Guys and Dolls (1955) | An American Tail (1986) |
| 4 | Banana (2010) | Barbie as The Princess & the Pauper (2004) | From Up on Poppy Hill (2011) | Anastasia (1997) |
| 5 | Ernest & Celestine (2012) | Snow Cake (2006) | Corrina, Corrina (1994) | Annie (1982) |
| 6 | Kronk's New Groove (2005) | An American Tail (1986) | Spirit: Stallion of the Cimarron (2002) | The Fox and the Hound (1981) |
| 7 | Lilo & Stitch 2: Stitch has a Glitch (2005) | Finding Dory (2016) | Anastasia (1997) | Pocahontas (1995) |
| 8 | Hachi: A Dog's Tale (2009) | Beaches (1988) | Beaches (1988) | The Greatest Show on Earth (1952) |
| 9 | Bears (2014) | Pete's Dragon (1977) | Pocahontas (1995) | Beaches (1988) |
| 10 | The Good Dinosaur (2015) | Thumbelina (1994) | Treasure Planet (2002) | Spirit: Stallion of the Cimarron (2002) |

### Métricas

| Modelo | iguais_tfidf | tfidf_medio | nota_media | votos_mediana |
|---|---|---|---|---|
| TF-IDF puro | 10.0 | 0.206 | 7.1 | 212.5 |
| Híbrido α=0.3 | 1.0 | 0.152 | 6.74 | 197.0 |
| Híbrido α=0.6 | 0.0 | 0.098 | 6.97 | 607.0 |
| Híbrido α=0.9 | 0.0 | 0.078 | 6.89 | 338.0 |

### Detalhes (scores e explicação)

**TF-IDF puro**

| title | vote_average | similaridade | porque |
|---|---|---|---|
| Miss You Already | 7.3 | 0.292 | friendship, family, comedy |
| Barbie as The Princess & the Pauper | 6.9 | 0.219 | friendship, family, animation |
| Over the Garden Wall | 8.2 | 0.194 | family, animation |
| Banana | 7.2 | 0.202 | family, animation, comedy |
| Ernest & Celestine | 7.6 | 0.183 | friendship, family, animation |
| Kronk's New Groove | 6.0 | 0.211 | friendship, family, animation |
| Lilo & Stitch 2: Stitch has a Glitch | 6.3 | 0.204 | friendship, family, animation |
| Hachi: A Dog's Tale | 7.7 | 0.178 | friendship, family, drama |
| Bears | 7.2 | 0.185 | family, nature |
| The Good Dinosaur | 6.6 | 0.195 | nature, family, animation |

**Híbrido α=0.3**

| title | vote_average | tfidf | colab | score | porque |
|---|---|---|---|---|---|
| The Fox and the Hound | 7.0 | 0.185 | 0.821 | 0.446 | friendship, family, animation \| parecido com Pete's Dragon |
| Corrina, Corrina | 6.4 | 0.161 | 0.806 | 0.418 | friendship, family, comedy \| parecido com Kronk's New Groove |
| Spirit: Stallion of the Cimarron | 7.4 | 0.128 | 0.809 | 0.406 | animation, family, comedy \| parecido com Kronk's New Groove |
| Barbie as The Princess & the Pauper | 6.9 | 0.219 | 0.595 | 0.401 | friendship, family, animation \| parecido com Simon Birch |
| Snow Cake | 7.3 | 0.173 | 0.678 | 0.397 | friendship, small town, drama \| parecido com Thumbelina |
| An American Tail | 6.6 | 0.108 | 0.848 | 0.396 | family, animation, drama \| parecido com The Fox and the Hound |
| Finding Dory | 6.8 | 0.126 | 0.79 | 0.394 | animation, family, comedy \| parecido com Kronk's New Groove |
| Beaches | 6.5 | 0.108 | 0.823 | 0.388 | friendship, comedy, drama \| parecido com The Fox and the Hound |
| Pete's Dragon | 6.4 | 0.159 | 0.705 | 0.387 | friendship, family, animation \| parecido com The Fox and the Hound |
| Thumbelina | 6.1 | 0.157 | 0.712 | 0.385 | family, animation, drama \| parecido com The Fox and the Hound |

**Híbrido α=0.6**

| title | vote_average | tfidf | colab | score | porque |
|---|---|---|---|---|---|
| The Fox and the Hound | 7.0 | 0.185 | 0.821 | 0.636 | friendship, family, animation \| parecido com Pete's Dragon |
| An American Tail | 6.6 | 0.108 | 0.848 | 0.618 | family, animation, drama \| parecido com The Fox and the Hound |
| Guys and Dolls | 6.9 | 0.014 | 0.903 | 0.616 | comedy \| parecido com The Fox and the Hound |
| From Up on Poppy Hill | 7.6 | 0.033 | 0.872 | 0.612 | animation, drama \| parecido com Corrina, Corrina |
| Corrina, Corrina | 6.4 | 0.161 | 0.806 | 0.612 | friendship, family, comedy \| parecido com Kronk's New Groove |
| Spirit: Stallion of the Cimarron | 7.4 | 0.128 | 0.809 | 0.611 | animation, family, comedy \| parecido com Kronk's New Groove |
| Anastasia | 7.4 | 0.078 | 0.84 | 0.609 | family, animation \| parecido com The Fox and the Hound |
| Beaches | 6.5 | 0.108 | 0.823 | 0.602 | friendship, comedy, drama \| parecido com The Fox and the Hound |
| Pocahontas | 6.7 | 0.08 | 0.835 | 0.6 | animation, family, drama \| parecido com The Fox and the Hound |
| Treasure Planet | 7.2 | 0.081 | 0.817 | 0.594 | animation, family, based on novel \| parecido com The Fox and the Hound |

**Híbrido α=0.9**

| title | vote_average | tfidf | colab | score | porque |
|---|---|---|---|---|---|
| Guys and Dolls | 6.9 | 0.014 | 0.903 | 0.883 | comedy \| parecido com The Fox and the Hound |
| From Up on Poppy Hill | 7.6 | 0.033 | 0.872 | 0.864 | animation, drama \| parecido com Corrina, Corrina |
| An American Tail | 6.6 | 0.108 | 0.848 | 0.84 | family, animation, drama \| parecido com The Fox and the Hound |
| Anastasia | 7.4 | 0.078 | 0.84 | 0.838 | family, animation \| parecido com The Fox and the Hound |
| Annie | 6.2 | 0.044 | 0.856 | 0.836 | family, comedy, drama \| parecido com Kronk's New Groove |
| The Fox and the Hound | 7.0 | 0.185 | 0.821 | 0.827 | friendship, family, animation \| parecido com Pete's Dragon |
| Pocahontas | 6.7 | 0.08 | 0.835 | 0.826 | animation, family, drama \| parecido com The Fox and the Hound |
| The Greatest Show on Earth | 6.6 | 0.002 | 0.836 | 0.819 | drama \| parecido com The Fox and the Hound |
| Beaches | 6.5 | 0.108 | 0.823 | 0.817 | friendship, comedy, drama \| parecido com The Fox and the Hound |
| Spirit: Stallion of the Cimarron | 7.4 | 0.128 | 0.809 | 0.815 | animation, family, comedy \| parecido com Kronk's New Groove |

## Persona: FPS / Guerra

Jogos: Call of Duty (300h), Battlefield 1 (80h), Hell Let Loose (30h)

### Top-10 lado a lado

| # | TF-IDF puro | Híbrido α=0.3 | Híbrido α=0.6 | Híbrido α=0.9 |
|---|---|---|---|---|
| 1 | We Were Soldiers (2002) | Midway (1976) | Midway (1976) | Jin-Roh: The Wolf Brigade (1999) |
| 2 | Midway (1976) | Casualties of War (1989) | Jin-Roh: The Wolf Brigade (1999) | A Most Wanted Man (2014) |
| 3 | '71 (2014) | The Lucky Ones (2008) | A Most Wanted Man (2014) | Frantic (1988) |
| 4 | Casualties of War (1989) | Merry Christmas, Mr. Lawrence (1983) | Frantic (1988) | The Time Machine (1960) |
| 5 | Buffalo Soldiers (2001) | Free Fire (2017) | The Time Machine (1960) | Escape from Alcatraz (1979) |
| 6 | Saints and Soldiers (2003) | The Thin Red Line (1998) | Mesrine: Killer Instinct (2008) | Taking Woodstock (2009) |
| 7 | Miracle at St. Anna (2008) | Appleseed Alpha (2014) | Escape from Alcatraz (1979) | Dracula: Prince of Darkness (1966) |
| 8 | The Dirty Dozen (1967) | Mesrine: Killer Instinct (2008) | Merry Christmas, Mr. Lawrence (1983) | My Son, My Son, What Have Ye Done (2009) |
| 9 | Platoon (1986) | Buffalo Soldiers (2001) | The Big Short (2015) | Cronos (1993) |
| 10 | Hacksaw Ridge (2016) | Saints and Soldiers (2003) | Harry Brown (2009) | In a Better World (2010) |

### Métricas

| Modelo | iguais_tfidf | tfidf_medio | nota_media | votos_mediana |
|---|---|---|---|---|
| TF-IDF puro | 10.0 | 0.273 | 6.87 | 256.0 |
| Híbrido α=0.3 | 4.0 | 0.221 | 6.71 | 126.0 |
| Híbrido α=0.6 | 1.0 | 0.07 | 7.03 | 237.5 |
| Híbrido α=0.9 | 0.0 | 0.001 | 6.73 | 141.0 |

### Detalhes (scores e explicação)

**TF-IDF puro**

| title | vote_average | similaridade | porque |
|---|---|---|---|
| We Were Soldiers | 6.7 | 0.356 | soldier, war, battle |
| Midway | 6.3 | 0.345 | soldier, war, battle |
| '71 | 6.7 | 0.279 | soldier, war, action |
| Casualties of War | 6.8 | 0.26 | soldier, war, history |
| Buffalo Soldiers | 6.5 | 0.263 | soldier, army, war |
| Saints and Soldiers | 6.6 | 0.26 | soldier, war, action |
| Miracle at St. Anna | 6.3 | 0.265 | soldier, war, world war ii |
| The Dirty Dozen | 7.5 | 0.238 | soldier, war, shootout |
| Platoon | 7.5 | 0.237 | soldier, war, battle |
| Hacksaw Ridge | 7.8 | 0.229 | soldier, war, army |

**Híbrido α=0.3**

| title | vote_average | tfidf | colab | score | porque |
|---|---|---|---|---|---|
| Midway | 6.3 | 0.345 | 0.657 | 0.502 | soldier, war, battle \| parecido com Force 10 from Navarone |
| Casualties of War | 6.8 | 0.26 | 0.569 | 0.421 | soldier, war, history \| parecido com Stop-Loss |
| The Lucky Ones | 6.3 | 0.226 | 0.624 | 0.409 | soldier, war, history \| parecido com Alatriste |
| Merry Christmas, Mr. Lawrence | 7.4 | 0.154 | 0.683 | 0.387 | soldier, history, world war ii \| parecido com Casualties of War |
| Free Fire | 6.3 | 0.216 | 0.569 | 0.385 | shootout, gun, action \| parecido com Buffalo Soldiers |
| The Thin Red Line | 7.2 | 0.174 | 0.623 | 0.381 | soldier, war, battle \| parecido com Stop-Loss |
| Appleseed Alpha | 6.4 | 0.182 | 0.627 | 0.379 | soldier, war, action \| parecido com Casualties of War |
| Mesrine: Killer Instinct | 7.3 | 0.127 | 0.722 | 0.379 | soldier, war, action \| parecido com Free Fire |
| Buffalo Soldiers | 6.5 | 0.263 | 0.422 | 0.376 | soldier, army, war \| parecido com Free Fire |
| Saints and Soldiers | 6.6 | 0.26 | 0.399 | 0.367 | soldier, war, action \| parecido com Stop-Loss |

**Híbrido α=0.6**

| title | vote_average | tfidf | colab | score | porque |
|---|---|---|---|---|---|
| Midway | 6.3 | 0.345 | 0.657 | 0.595 | soldier, war, battle \| parecido com Force 10 from Navarone |
| Jin-Roh: The Wolf Brigade | 7.4 | 0.0 | 0.86 | 0.59 | parecido com Midway |
| A Most Wanted Man | 6.5 | 0.0 | 0.865 | 0.584 | parecido com Midway |
| Frantic | 6.6 | 0.0 | 0.851 | 0.577 | parecido com Midway |
| The Time Machine | 7.5 | 0.0 | 0.804 | 0.557 | parecido com Midway |
| Mesrine: Killer Instinct | 7.3 | 0.127 | 0.722 | 0.557 | soldier, war, action \| parecido com Free Fire |
| Escape from Alcatraz | 7.3 | 0.01 | 0.786 | 0.549 | biography \| parecido com Buffalo Soldiers |
| Merry Christmas, Mr. Lawrence | 7.4 | 0.154 | 0.683 | 0.545 | soldier, history, world war ii \| parecido com Casualties of War |
| The Big Short | 7.3 | 0.034 | 0.764 | 0.545 | based on true story, biography \| parecido com Buffalo Soldiers |
| Harry Brown | 6.7 | 0.033 | 0.775 | 0.545 | action \| parecido com Midway |

**Híbrido α=0.9**

| title | vote_average | tfidf | colab | score | porque |
|---|---|---|---|---|---|
| Jin-Roh: The Wolf Brigade | 7.4 | 0.0 | 0.86 | 0.848 | parecido com Midway |
| A Most Wanted Man | 6.5 | 0.0 | 0.865 | 0.844 | parecido com Midway |
| Frantic | 6.6 | 0.0 | 0.851 | 0.832 | parecido com Midway |
| The Time Machine | 7.5 | 0.0 | 0.804 | 0.799 | parecido com Midway |
| Escape from Alcatraz | 7.3 | 0.01 | 0.786 | 0.781 | biography \| parecido com Buffalo Soldiers |
| Taking Woodstock | 6.2 | 0.0 | 0.79 | 0.773 | parecido com Midway |
| Dracula: Prince of Darkness | 6.1 | 0.0 | 0.789 | 0.771 | parecido com Midway |
| My Son, My Son, What Have Ye Done | 6.0 | 0.0 | 0.79 | 0.771 | parecido com Casualties of War |
| Cronos | 6.4 | 0.0 | 0.785 | 0.77 | parecido com The Lucky Ones |
| In a Better World | 7.3 | 0.0 | 0.773 | 0.769 | parecido com Casualties of War |

## Persona: Sci-fi / Cyberpunk

Jogos: Cyberpunk 2077 (120h), Mass Effect (70h)

### Top-10 lado a lado

| # | TF-IDF puro | Híbrido α=0.3 | Híbrido α=0.6 | Híbrido α=0.9 |
|---|---|---|---|---|
| 1 | Titan A.E. (2000) | Ender's Game (2013) | Ender's Game (2013) | Gamer (2009) |
| 2 | Ender's Game (2013) | Titan A.E. (2000) | Impostor (2001) | The Shadow (1994) |
| 3 | Avatar (2009) | Stargate: Continuum (2008) | Stargate: Continuum (2008) | Impostor (2001) |
| 4 | Space Pirate Captain Harlock (2013) | Lockout (2012) | Lockout (2012) | The Last Witch Hunter (2015) |
| 5 | The Time Machine (1960) | Space Pirate Captain Harlock (2013) | The Time Machine (2002) | Supernova (2000) |
| 6 | Treasure Planet (2002) | Impostor (2001) | The Shadow (1994) | Ender's Game (2013) |
| 7 | Lifeforce (1985) | The Time Machine (2002) | Gamer (2009) | Judge Dredd (1995) |
| 8 | Moon (2009) | Meet Dave (2008) | Titan A.E. (2000) | The Time Machine (2002) |
| 9 | Zathura: A Space Adventure (2005) | Lost in Space (1998) | Judge Dredd (1995) | Johnny Mnemonic (1995) |
| 10 | Interstellar (2014) | Solomon Kane (2009) | Stargate: The Ark of Truth (2008) | Stargate: Continuum (2008) |

### Métricas

| Modelo | iguais_tfidf | tfidf_medio | nota_media | votos_mediana |
|---|---|---|---|---|
| TF-IDF puro | 10.0 | 0.242 | 6.92 | 894.0 |
| Híbrido α=0.3 | 3.0 | 0.213 | 5.95 | 388.0 |
| Híbrido α=0.6 | 2.0 | 0.167 | 6.07 | 481.5 |
| Híbrido α=0.9 | 1.0 | 0.121 | 5.78 | 511.5 |

### Detalhes (scores e explicação)

**TF-IDF puro**

| title | vote_average | similaridade | porque |
|---|---|---|---|
| Titan A.E. | 6.3 | 0.309 | alien, space, science fiction |
| Ender's Game | 6.6 | 0.262 | space, science fiction, future |
| Avatar | 7.2 | 0.248 | alien, space, science fiction |
| Space Pirate Captain Harlock | 6.4 | 0.254 | space, science fiction |
| The Time Machine | 7.5 | 0.232 | future, science fiction, adventure |
| Treasure Planet | 7.2 | 0.234 | space, alien, science fiction |
| Lifeforce | 6.2 | 0.244 | space, alien, science fiction |
| Moon | 7.6 | 0.211 | space, science fiction, artificial intelligence |
| Zathura: A Space Adventure | 6.1 | 0.236 | space, alien, science fiction |
| Interstellar | 8.1 | 0.192 | space, science fiction, artificial intelligence |

**Híbrido α=0.3**

| title | vote_average | tfidf | colab | score | porque |
|---|---|---|---|---|---|
| Ender's Game | 6.6 | 0.262 | 0.849 | 0.504 | space, science fiction, future \| parecido com Titan A.E. |
| Titan A.E. | 6.3 | 0.309 | 0.73 | 0.499 | alien, space, science fiction \| parecido com Ender's Game |
| Stargate: Continuum | 6.8 | 0.199 | 0.84 | 0.459 | alien, science fiction, adventure \| parecido com Titan A.E. |
| Lockout | 5.8 | 0.204 | 0.845 | 0.454 | space, future, science fiction \| parecido com Ender's Game |
| Space Pirate Captain Harlock | 6.4 | 0.254 | 0.694 | 0.45 | space, science fiction \| parecido com Stargate: Continuum |
| Impostor | 6.1 | 0.162 | 0.887 | 0.44 | alien, science fiction \| parecido com Ender's Game |
| The Time Machine | 5.8 | 0.16 | 0.865 | 0.429 | future, science fiction, adventure \| parecido com Meet Dave |
| Meet Dave | 5.1 | 0.229 | 0.687 | 0.417 | space, alien, science fiction \| parecido com Ender's Game |
| Lost in Space | 5.0 | 0.198 | 0.762 | 0.417 | space, science fiction, adventure \| parecido com Titan A.E. |
| Solomon Kane | 5.6 | 0.158 | 0.816 | 0.411 | sword and sorcery, science fiction, adventure \| parecido com Ender's Game |

**Híbrido α=0.6**

| title | vote_average | tfidf | colab | score | porque |
|---|---|---|---|---|---|
| Ender's Game | 6.6 | 0.262 | 0.849 | 0.68 | space, science fiction, future \| parecido com Titan A.E. |
| Impostor | 6.1 | 0.162 | 0.887 | 0.658 | alien, science fiction \| parecido com Ender's Game |
| Stargate: Continuum | 6.8 | 0.199 | 0.84 | 0.652 | alien, science fiction, adventure \| parecido com Titan A.E. |
| Lockout | 5.8 | 0.204 | 0.845 | 0.646 | space, future, science fiction \| parecido com Ender's Game |
| The Time Machine | 5.8 | 0.16 | 0.865 | 0.641 | future, science fiction, adventure \| parecido com Meet Dave |
| The Shadow | 5.4 | 0.091 | 0.915 | 0.64 | science fiction, adventure, fantasy \| parecido com Titan A.E. |
| Gamer | 5.6 | 0.059 | 0.925 | 0.634 | science fiction, dystopia \| parecido com Titan A.E. |
| Titan A.E. | 6.3 | 0.309 | 0.73 | 0.625 | alien, space, science fiction \| parecido com Ender's Game |
| Judge Dredd | 5.4 | 0.091 | 0.881 | 0.619 | science fiction, future, dystopia \| parecido com Titan A.E. |
| Stargate: The Ark of Truth | 6.9 | 0.133 | 0.824 | 0.617 | alien, science fiction, adventure \| parecido com Ender's Game |

**Híbrido α=0.9**

| title | vote_average | tfidf | colab | score | porque |
|---|---|---|---|---|---|
| Gamer | 5.6 | 0.059 | 0.925 | 0.894 | science fiction, dystopia \| parecido com Titan A.E. |
| The Shadow | 5.4 | 0.091 | 0.915 | 0.887 | science fiction, adventure, fantasy \| parecido com Titan A.E. |
| Impostor | 6.1 | 0.162 | 0.887 | 0.875 | alien, science fiction \| parecido com Ender's Game |
| The Last Witch Hunter | 5.7 | 0.038 | 0.893 | 0.865 | adventure, fantasy \| parecido com Ender's Game |
| Supernova | 4.9 | 0.07 | 0.89 | 0.857 | science fiction, future \| parecido com Ender's Game |
| Ender's Game | 6.6 | 0.262 | 0.849 | 0.856 | space, science fiction, future \| parecido com Titan A.E. |
| Judge Dredd | 5.4 | 0.091 | 0.881 | 0.856 | science fiction, future, dystopia \| parecido com Titan A.E. |
| The Time Machine | 5.8 | 0.16 | 0.865 | 0.853 | future, science fiction, adventure \| parecido com Meet Dave |
| Johnny Mnemonic | 5.5 | 0.082 | 0.872 | 0.848 | science fiction, cyberpunk, adventure \| parecido com Titan A.E. |
| Stargate: Continuum | 6.8 | 0.199 | 0.84 | 0.844 | alien, science fiction, adventure \| parecido com Titan A.E. |
