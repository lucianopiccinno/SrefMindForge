# CIANOAI SrefMindForge — Blueprint di Ricostruzione

**Versione attuale:** smf-7
**Data:** 22/02/2026
**Autore:** Luciano / CIANOAI

---

## 1. Panoramica del progetto

SrefMindForge e' una web app offline (singolo file HTML) che suggerisce i migliori
SREF Midjourney per la richiesta dell'utente, basandosi su 4 parametri:

- **Visual Style** (23 valori: Fantasy, Cyberpunk, Sci-Fi, Gothic, Horror, Anime/Manga, Watercolor, Ink/Sketch, Photorealism, Illustration, Abstract, Minimalist, Geometric, 3D/Render, Vintage/Retro, Nature, Urban, Painting, Surreal, Pastel/Soft, Vibrant/Pop, Noir, Steampunk)
- **Subject** (13 valori: Portrait, Landscape, Creature, Character, Architecture, Nature, Space, Urban, Mythology, Fashion, Abstract concept, Interior, Still life)
- **Mood** (12 valori: Dark, Ethereal, Epic, Serene, Whimsical, Melancholic, Mysterious, Futuristic, Romantic, Chaotic, **Dramatic**, **Elegant**)
- **Color Palette** (12 valori: Pastel, Neon, Monochrome, Sepia, Vibrant, Muted, Golden, Dark, Cold blues, Earth tones, **Purple/Violet**, **Warm/Fire**)

L'output e':
- 3 SREF puri (singoli, score decrescente, geo-diversi)
- 2 mix consigliati (2-3 SREF combinati con pesi ::2 ::1)
- Prompt Midjourney completo pronto da copiare (architettura 8 componenti)

---

## 2. Struttura file

```
SrefMindForge APP/
├── build_index.py          — script generatore (fonte di verita')
├── index.html              — app generata (NON modificare manualmente)
├── codici_attivazione.txt  — 100 codici PRO (seed fisso, riproducibili)
├── BLUEPRINT.md            — questo file
└── _BACKUP/
    └── build_index_backup_YYYYMMDD.py
```

**Fonte dati SREF:**
```
C:\Users\Luciano\Desktop\MITAKPA\SREF\sref_full.json
```
- 3525 entry
- Campi: sref, nome, categoria, fonte, description, keywords, analysis, hashtags, manuale

---

## 3. Come rigenerare l'app

```bash
cd "C:\Users\Luciano\Desktop\MITAKPA\SrefMindForge APP"
python build_index.py
```

Output: `index.html` (circa 2750 KB) — aprire con doppio click nel browser.

**Requisiti:** Python 3.10+, nessuna dipendenza esterna.

---

## 4. Architettura build_index.py

### 4.1 Dizionari di keyword (tagging)

`STYLE_KEYWORDS`, `SUBJECT_KEYWORDS`, `MOOD_KEYWORDS`, `PALETTE_KEYWORDS`:
dizionari Python con tag → lista keyword. Il testo di ogni SREF (nome + description +
keywords + analysis + hashtags) viene confrontato con le keyword. Se match → tag assegnato.

`GEO_KEYWORDS`: dizionario geo-famiglia → keyword da `analysis`. Assegna la famiglia
geometrica (soft-wash, organic-curves, flat-color, line-based, continuous-tone,
geometric-hard, volumetric-hard, organic-dark, surreal-open, unknown).

**Fallback tagging** (`_apply_fallbacks`): per SREF con 0 tag su una dimensione,
assegna tag di fallback basati su geo e style. Garantisce 100% copertura su tutti e 4 i parametri.

### 4.2 Scoring (JS)

```
score = style_match*3 + subject_match*2 + mood_match*1 + palette_match*1
      + manuale_bonus*0.5 + random(0, 0.49)
```

Il componente random garantisce risultati diversi ad ogni ricerca.

### 4.3 Selezione pure SREFs

`selectDiversePuri()`: preferisce 1 SREF per geo-famiglia nei top N per score.
Fallback: ripete geo se necessario.

### 4.4 Selezione mix

- Pool: top 200 con base_score >= 1, esclusi i 3 puri
- Mix 1: SREF_A (top pool) + SREF_B (geo compatibile diverso) + SREF_C opzionale
- Mix 2: stessa logica con SREF non usati nel Mix 1
- Pesi: SREF_A → ::2, SREF_B e SREF_C → ::1

**GEO_COMPAT map** (definita nel JS):
```
soft-wash       → soft-wash, organic-curves, flat-color, surreal-open
organic-curves  → organic-curves, soft-wash, flat-color, surreal-open, organic-dark
flat-color      → flat-color, soft-wash, organic-curves, line-based
line-based      → line-based, flat-color, continuous-tone, organic-dark
continuous-tone → continuous-tone, line-based, organic-curves, organic-dark
geometric-hard  → geometric-hard, line-based, volumetric-hard
volumetric-hard → volumetric-hard, geometric-hard, continuous-tone
organic-dark    → organic-dark, organic-curves, continuous-tone, surreal-open, line-based
surreal-open    → surreal-open, soft-wash, organic-curves, organic-dark, flat-color
unknown         → tutti
```

### 4.5 Generazione prompt (architettura 8 componenti Luciano-style)

```
[idea tradotta in inglese]
[descrittori visivi stile]
isolated on a [colore evocativo] background
[dettaglio: intricate detail o refined minimal detail]
with [3 props tematici]
[qualificatori atmosferici mood]
digital art illustration
[stile artistico dichiarato — nome e tecnica specifica]
[scena sfondo] in background
[descrittore luce mood]
```

Dizionari JS per ogni componente:
- `_VISUAL_STYLE`: per style, descrittori visivi
- `_BG_COLORS_MAP`: per palette + mood, colori evocativi sfondo
- `_PROPS_MAP`: per subject + style, "with X, Y, and Z"
- `_ATMOSPHERE_MAP`: per mood, 7-8 qualificatori evocativi
- `_ART_STYLE_DECL`: per style, dichiarazione stile artistico nominato
- `_BG_SCENE_MAP`: per subject + style, scena sfondo
- `_LIGHTING_MAP`: per mood, descrittore luce
- `_pickRand(arr)`: helper JS per selezione casuale da array

### 4.6 Sistema freemium

- Modalita' free: 3 SREF puri + 2 mix (limitato)
- Modalita' PRO: accesso completo con codice attivazione
- 100 codici generati deterministicamente con seed fisso `"smf-v1-2026"`
- Codice scadenza: `EXPIRY_DATE = "2027-02-22"`
- Codici blacklistati: `BLACKLISTED_CODES` (set) — rimossi dall'app
- Memorizzati in localStorage (`_sc_v` per versione, `_sc_k` per codice attivo)
- Verifica lato client con base64 obfuscation

### 4.7 Version stamp

Ogni rebuild che cambia il JS deve aggiornare il version stamp (es. smf-7 → smf-8).
Questo svuota localStorage utente e forza ricarica JSON.
Cerca "smf-7" nel file e sostituisci con replace_all.

---

## 5. Copertura tagging SREF (smf-7)

| Dimensione | SREF coperti | Note |
|------------|-------------|-------|
| Style      | 3525/3525 (100%) | top: illustration=1568, vibrant_pop=1018, nature=939 |
| Subject    | 3525/3525 (100%) | top: portrait=926, abstract_concept=784, nature=749 |
| Mood       | 3525/3525 (100%) | top: serene=1906, ethereal=1596, melancholic=1486 |
| Palette    | 3525/3525 (100%) | top: monochrome=1661, neon=874, vibrant=866 |

Nuovi tag smf-7:
- dramatic: 257 SREF | elegant: 449 SREF
- purple_violet: 60 SREF | warm_fire: 111 SREF

Fallback tagging (applicato dopo keyword matching):
- Subject: usa geo-family se 0 match (es. surreal-open → abstract_concept+landscape)
- Style: usa geo-family se 0 match
- Mood: usa style_tags se 0 match
- Palette: usa style_tags → mood_tags se 0 match

---

## 6. Naming sistema CIANOAI

Ogni SREF riceve un nome brand unico generato da:
- Aggettivo da `_ADJ_STYLE` (basato su style_tags) o `_ADJ_MOOD` o fallback
- Sostantivo da `_NOUN_GEO` (basato su geo-famiglia)
- Se collisione: aggiunge numero (es. "Arcane Veil 2")
- Seed deterministico: `random.Random(f"smf-name-v1-{sref_number}")`
- Cambio nome → cambiare seed (es. smf-name-v2-)

---

## 7. UI / Design

Dark theme, colori:
- BG principale: `#0d0d1a`
- Card: `#1a1a2e`
- Accent: `#e94560`
- Testo: `#f0f0f0`
- Muted: `#8888aa`

Layout:
- Header con nome + sottotitolo
- 4 dropdown in griglia 2x2 + campo idea + pulsante CERCA
- Sezione 3 SREF PURI (card verticali)
- Sezione 2 MIX CONSIGLIATI (card con 3 SREF interni)
- Ogni card: badge SREF, nome, geo, badge MANUALE, tags, prompt, pulsante COPIA

---

## 8. Aggiungere nuovi parametri o valori

**Nuovo valore al dropdown MOOD:**
1. Aggiungere `<option value="nuovo">Nuovo</option>` nel template HTML
2. Aggiungere `"nuovo": [...]` a `MOOD_KEYWORDS`
3. Aggiungere `"nuovo"` a `_BG_COLORS_MAP`, `_ATMOSPHERE_MAP`, `_LIGHTING_MAP`, `_ADJ_MOOD`
4. Aggiornare version stamp
5. Eseguire `python build_index.py`

**Nuovo valore al dropdown PALETTE:**
1. Aggiungere `<option value="nuovo">Nuovo</option>`
2. Aggiungere `"nuovo": [...]` a `PALETTE_KEYWORDS`
3. Aggiungere `"nuovo"` a `_BG_COLORS_MAP`
4. Aggiornare version stamp + rebuild

**Nuovo valore STYLE:**
1. Opzione HTML + STYLE_KEYWORDS entry
2. Entry in `_VISUAL_STYLE`, `_ART_STYLE_DECL`, `_PROPS_MAP`, `_BG_SCENE_MAP`, `_ADJ_STYLE`, `_GEO_STYLE_HINT`
3. Aggiornare version stamp + rebuild

---

## 9. Estensioni future possibili

- Filtro per numero SREF (range slider es. 0-500 / 500-2000 / 2000+)
- Filtro per `manuale: true` (solo SREF validati manualmente)
- Esportazione risultati come .txt
- Slider peso parametri (es. style piu' importante di palette)
- Possibilita' di escludere SREF gia' usati (blacklist locale)
- Aggiunta campo 5: "medium" (stampa, digitale, NFT, etc.)

---

## 10. File correlati e memoria di progetto

```
C:\Users\Luciano\Desktop\MITAKPA\SREF\sref_full.json   — database SREF (NON modificare)
C:\Users\Luciano\Desktop\MITAKPA\ARCHIVIO-OLD\...       — archivio prompt Luciano (555 prompt)
```

Prompt archive di Luciano (stile CIANOAI):
- Categorie: Fantasy (90), Moderno (252), Mono (27), Pop & Psy (141), Retro & Vintage (45)
- Architettura prompt: soggetto + trait cluster + sfondo evocativo + dettaglio + props + atmosfera + medium + stile + luce

CIANOAI brand: uso interno, non distribuire codici attivazione.
