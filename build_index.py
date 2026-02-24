"""
build_index.py — genera index.html con JSON SREF enrichito e app offline embedded.
"""
import json
import base64
import random
import datetime
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

MASTER_KEY = "CIANOAI-SrefMindForge-2026-AES256"


def encrypt_json_aes256(data: list, passphrase: str) -> str:
    import hashlib
    key = hashlib.sha256(passphrase.encode('utf-8')).digest()
    plaintext = json.dumps(data, ensure_ascii=True, separators=(',', ':')).encode('utf-8')
    iv = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    combined = iv + tag + ciphertext  # iv(12) + tag(16) + ct(N)
    return base64.b64encode(combined).decode('ascii')


BASE_DIR   = Path(__file__).parent
SREF_JSON  = Path(r"C:\Users\Luciano\Desktop\MITAKPA\SREF\sref_full.json")
OUTPUT_HTML = BASE_DIR / "index.html"
OUTPUT_CODES = BASE_DIR / "codici_attivazione.txt"

# Scadenza batch codici: 1 anno dalla data di generazione
EXPIRY_DATE = "2027-02-22"

# Seed fisso: stessi 100 codici a ogni rebuild (codici già distribuiti restano validi)
_CODE_SEED = "smf-v1-2026"
_CODE_CHARS = "abcdefghjkmnpqrstuvwxyz23456789"  # no 0/O/1/l/i


def _generate_codes() -> list[str]:
    """Genera 100 codici attivazione univoci e riproducibili (seed fisso)."""
    rng = random.Random(_CODE_SEED)
    codes: set[str] = set()
    while len(codes) < 100:
        a = "".join(rng.choice(_CODE_CHARS) for _ in range(4))
        b = "".join(rng.choice(_CODE_CHARS) for _ in range(4))
        c = "".join(rng.choice(_CODE_CHARS) for _ in range(6))
        codes.add(f"smf-{a}-{b}-{c}")
    return sorted(codes)


PREMIUM_CODES_PLAIN: list[str] = _generate_codes()

# Codici bruciati/revocati — rimossi dall'app anche se ancora nel TXT
BLACKLISTED_CODES: set[str] = {
    "smf-2grk-94z5-5jz5mw",  # #1 — usato e revocato 22/02/2026
}

# ---------------------------------------------------------------------------
# Dizionari keyword per tagging
# ---------------------------------------------------------------------------

STYLE_KEYWORDS: dict[str, list[str]] = {
    "fantasy": [
        "fantasy", "fairy tale", "fairytale", "mythical", "mystical",
        "enchanted", "arcane", "sorcery", "elven", "wizard", "magical realm",
        "high fantasy", "fairy", "faerie", "fae",
        "magical", "enchantment", "spell", "rune", "runic", "mystical energy",
        "ethereal magic", "legendary", "heroic fantasy", "dark fantasy",
        "mythological", "ancient legend", "fantastical", "folklore",
        "druidic", "shamanic", "celestial realm", "divine magic", "arcane magic",
        "fantasy art", "fantasy world", "mythic realm", "supernatural",
        "fantastical creature", "mystical being", "otherworldly magic",
        "mystical glow", "dragon", "griffin", "phoenix", "mermaid", "unicorn",
        "knight", "sorcerer", "sorceress", "elf", "dwarf", "goblin",
        "ancient magic", "magical creature", "enchanted forest", "magical world",
    ],
    "cyberpunk": [
        "cyberpunk", "cyber-punk", "neon city", "dystopia", "hacker",
        "neural implant", "biopunk", "synthwave", "cyber aesthetic", "tech noir",
        "neon-lit", "megacity", "corpo",
        "cyber", "neon glow", "glitch", "hologram", "augmented reality",
        "neural", "circuit", "LED", "future city", "dystopic",
        "corporate", "dark future", "urban tech", "neon street",
        "synthetic", "technopunk", "wired", "data stream", "virtual",
        "cyber city", "matrix", "digital world", "tech city",
        "android", "cyborg", "implant", "bionic", "electric neon",
    ],
    "sci_fi": [
        "sci-fi", "science fiction", "space station", "spaceship", "alien world",
        "android", "robot", "starship", "deep space", "interstellar", "galactic",
        "futurism", "retro futuristic", "retrofuturistic",
        "space", "cosmic", "galaxy", "nebula", "planet", "astronaut",
        "stellar", "orbital", "alien", "extraterrestrial", "space age",
        "futuristic", "advanced technology", "space exploration",
        "scifi", "spacecraft", "exoplanet", "space opera",
        "quantum", "laser", "energy beam", "space suit", "zero gravity",
        "alien landscape", "space colony", "robotic", "mechanical future",
    ],
    "gothic": [
        "gothic", "goth", "victorian dark", "cathedral", "vampire",
        "dark victorian", "baroque dark", "memento mori", "occult",
        "dark cathedral", "shadow gothic",
        "victorian", "dark romantic", "gargoyle", "spire",
        "crypt", "tomb", "graveyard", "cemetery", "gothic architecture",
        "dark medieval", "haunted mansion", "dark abbey",
        "gothic art", "neo-gothic", "gothic style", "dark baroque",
        "black lace", "mourning", "medieval dark", "occultism",
        "gothic fantasy", "wrought iron", "stained glass dark",
        "gothic illustration", "dark ornate", "brooding victorian",
    ],
    "horror": [
        "horror", "terror", "nightmare", "creepy", "macabre", "grotesque",
        "sinister", "haunted", "eldritch", "visceral fear", "dread",
        "disturbing", "unsettling", "eerie", "ghastly", "horrific",
        "terrifying", "blood", "gore", "horror art", "horror film",
        "scary", "frightening", "ominous dread", "cosmic horror",
        "supernatural horror", "dark entity", "demon possession",
        "body horror", "psychological horror", "decay", "rot",
        "haunting", "spectral horror", "monster horror", "dreadful",
    ],
    "anime_manga": [
        "anime", "manga", "chibi", "kawaii", "shonen", "shojo",
        "japanese animation", "otaku", "cel shade",
        "japanese art", "japanese style", "anime style", "manga style",
        "anime illustration", "anime character", "manga character",
        "anime aesthetic", "japanese illustration", "anime art",
        "light novel", "visual novel", "studio ghibli", "anime fantasy",
        "anime inspired", "eastern animation", "japanese cartoon",
        "cel-shaded", "anime eyes", "big eyes", "dynamic anime", "manga panel",
    ],
    "watercolor": [
        "watercolor", "watercolour", "aquarelle", "watercolor wash",
        "watercolor painting",
        "water color", "paint wash", "soft paint", "fluid paint",
        "transparent paint", "layered wash", "ink wash", "gouache",
        "watercolor illustration", "painted", "painterly wash", "soft brush",
        "flowing paint", "color bleed", "wet-on-wet", "painted style",
        "loose brush", "spontaneous paint", "watercolor style",
        "delicate wash", "luminous wash", "color bloom",
    ],
    "ink_sketch": [
        "ink drawing", "sketch", "pen and ink", "linework", "crosshatching",
        "charcoal sketch", "grisaille", "sketchwork", "brushwork ink",
        "ink illustration",
        "line art", "pencil sketch", "brush stroke", "ink stroke", "pen work",
        "hand drawn", "hand-drawn", "hatching", "etching", "engraving",
        "charcoal", "graphic novel", "comic book art", "black ink",
        "brushwork", "sketched", "calligraphic", "bold stroke",
        "sumi ink", "lithograph", "woodcut", "wood engraving", "stipple",
        "scraperboard", "quill", "etched", "inked", "raw linework",
    ],
    "photorealism": [
        "photorealistic", "photorealism", "hyperrealistic", "ultra realistic",
        "lifelike", "cinematic photography", "documentary photo",
        "realistic", "photography", "photo quality", "DSLR", "photograph",
        "camera", "hyper detail", "ultra detail", "real life",
        "true to life", "naturalistic", "razor sharp", "photographic quality",
        "photo-realistic", "detailed photography", "high resolution",
        "film photography", "cinematic shot", "studio photography",
        "subsurface scatter", "photographic realism", "lifelike render",
    ],
    "illustration": [
        "illustration", "storybook illustration", "children's art",
        "book illustration", "editorial illustration", "digitalism",
        "digital illustration",
        "illustrated", "illustrative", "digital art", "digital painting",
        "character illustration", "concept art", "game art", "book art",
        "commercial illustration", "graphic design", "vector illustration",
        "flat illustration", "2D illustration", "professional illustration",
        "art style", "artistic", "creative illustration", "design illustration",
        "concept illustration", "narrative illustration", "visual development",
    ],
    "abstract": [
        "abstract art", "non-representational", "abstract composition",
        "pure abstraction", "abstract expressionism", "geometric abstraction",
        "abstract", "non-figurative", "abstract shapes", "color field",
        "gestural", "expressionist", "experimental", "non-objective",
        "pure form", "conceptual", "visual abstraction", "abstract style",
        "fluid abstraction", "dynamic abstraction", "color abstraction",
        "texture abstraction", "pattern abstraction", "free form",
        "abstract pattern", "deconstructed", "fragmented form",
    ],
    "minimalist": [
        "minimalist", "minimalism", "minimal aesthetic", "sparse composition",
        "negative space", "clean minimal", "less is more",
        "minimal", "clean", "simple", "simplified", "sparse",
        "stripped down", "bare", "elegant simplicity", "minimal design",
        "zen design", "reduction", "minimal composition", "white space",
        "essential", "clean lines", "pure minimal", "minimal style",
        "sleek", "uncluttered", "refined", "simple form", "void space",
    ],
    "geometric": [
        "geometric pattern", "geometric design", "polygon", "tessellation",
        "angular geometry", "hexagonal", "crystalline structure",
        "geometric", "geometry", "geometric art", "geometric shapes",
        "angular", "polygonal", "triangular", "mathematical",
        "structured", "ordered", "grid", "symmetry", "symmetric",
        "architectural geometry", "precision", "faceted",
        "low-poly", "isometric", "crystalline", "lattice", "tile pattern",
        "mosaic", "fractal", "geometric abstract",
    ],
    "3d_render": [
        "3d render", "cgi", "digital render", "3d modeling", "blender",
        "octane render", "ray tracing", "volumetric render",
        "3D", "three-dimensional", "rendered", "computer generated",
        "CGI art", "3D art", "volumetric", "photorealistic 3D",
        "digital model", "3D scene", "Unreal Engine",
        "physically based", "3D rendering", "subsurface scatter",
        "ambient occlusion", "PBR", "game engine", "realtime render",
        "3D illustration", "sculpted", "modeled", "rendered scene",
    ],
    "vintage_retro": [
        "vintage", "retro aesthetic", "1970s", "1980s", "1950s", "nostalgic",
        "antique", "aged photograph", "old school", "sepia toned",
        "mid-century", "film grain",
        "retro", "old fashioned", "classic", "throwback", "bygone era",
        "1960s", "1940s", "1930s", "aged", "patina", "weathered",
        "vintage style", "retro style", "art deco", "art nouveau",
        "halftone", "offset print", "letterpress", "old poster",
        "vintage poster", "old film", "film photography", "grain",
        "polaroid", "faded photo", "aged paper", "vintage illustration",
    ],
    "nature": [
        "nature scene", "botanical", "wildlife", "landscape nature",
        "natural environment", "flora and fauna", "wilderness",
        "nature", "natural", "organic", "botanical art", "plant",
        "flower", "trees", "leaves", "forest", "woodland",
        "garden", "meadow", "natural world", "wildlife art",
        "earth", "outdoor", "ecosystem", "environment",
        "nature photography", "wild nature", "natural beauty",
        "scenic nature", "nature inspired", "organic nature",
        "overgrown", "lush vegetation", "foliage", "moss", "fern",
    ],
    "urban": [
        "urban", "graffiti", "street art", "cityscape", "metropolitan",
        "street photography", "urban decay",
        "city", "town", "urban landscape", "street", "building",
        "downtown", "urban life", "city life",
        "urban art", "street culture", "concrete",
        "brick wall", "alley", "rooftop", "urban scene", "city street",
        "industrial", "subway", "public space", "urban environment",
        "city lights", "neon sign", "urban grit", "street culture",
    ],
    "painting": [
        "oil painting", "acrylic painting", "canvas", "fine art painting",
        "classical painting", "brushstroke", "impressionist", "expressionist",
        "painted", "painting", "oil paint", "acrylic", "canvas texture",
        "painterly", "brushwork", "impasto", "fine art", "gallery art",
        "master painting", "plein air", "studio painting", "classical art",
        "painting style", "art paint", "painted style", "thick paint",
        "museum quality", "old master", "portrait painting",
        "landscape painting", "figurative painting", "alla prima",
    ],
    "surreal": [
        "surreal", "surrealism", "dreamlike", "uncanny", "subconscious",
        "dream logic", "impossible scene",
        "surrealist", "dream", "dreamy", "dream world", "dream-like",
        "impossible", "illogical", "bizarre", "strange", "weird",
        "otherworldly", "magical realism", "dreamscape", "fantasy dream",
        "mind bending", "surreal art", "hallucinatory", "psychedelic",
        "metaphysical", "symbolic", "allegorical", "subconscious imagery",
        "dali", "magritte", "impossible geometry", "dream surreal",
    ],
    "pastel_soft": [
        "pastel palette", "soft pastel", "gentle tones", "delicate colors",
        "blush tones", "soft hues", "baby pink",
        "pastel", "soft colors", "gentle colors", "delicate palette",
        "light tones", "pink", "lilac", "lavender", "mint",
        "cream", "ivory", "blush", "rose", "soft pink",
        "candy color", "fairy tale colors", "pastel art", "soft art",
        "gentle art", "sweet colors", "tender palette",
        "powder blue", "peach", "soft yellow", "chalky pastels",
    ],
    "vibrant_pop": [
        "vibrant", "pop art", "bold colors", "maximum saturation",
        "high chroma", "vivid", "colorful burst", "saturated",
        "vivid colors", "intense color", "bold", "energetic",
        "high energy", "neon color", "bright", "colorful",
        "multicolor", "rainbow", "fluorescent", "explosive color",
        "graphic", "poster art", "pop culture", "street pop",
        "vibrant art", "color explosion", "ultra vivid", "electric color",
        "lichtenstein", "andy warhol", "pop illustration", "bold graphic",
    ],
    "noir": [
        "film noir", "noir aesthetic", "black and white", "chiaroscuro",
        "shadow play", "shadow contrast", "monochrome film",
        "noir", "dark atmosphere", "high contrast", "dramatic shadow",
        "deep shadow", "noir style", "crime film", "detective",
        "hard-boiled", "expressionist", "low key lighting", "dramatic lighting",
        "shadow and light", "black shadows", "white highlight",
        "stark contrast", "silhouette", "dark mood", "brooding atmosphere",
        "rain reflection", "venetian blinds shadow", "smoke haze",
    ],
    "steampunk": [
        "steampunk", "steam punk", "victorian machinery", "brass gears",
        "clockwork", "aetherpunk", "steam engine",
        "steam", "gear", "cog", "machinery", "victorian", "brass",
        "copper", "bronze", "mechanical", "clockwork mechanism",
        "industrial victorian", "steampunk art", "steam powered",
        "gas lamp", "boiler", "rivets", "antique machine", "steam age",
        "dirigible", "airship", "steam punk style", "mechanical steampunk",
        "patinated", "ornate machinery", "victorian tech",
    ],
}

SUBJECT_KEYWORDS: dict[str, list[str]] = {
    "portrait": [
        "portrait", "facial", "face study", "close-up figure",
        "person portrait", "bust", "headshot",
        "face", "human face", "woman", "man", "girl", "boy", "person",
        "close up", "close-up", "head", "shoulders", "figure",
        "character portrait", "character face", "detailed face",
        "expression", "eyes", "emotion", "human", "figure study",
        "person study", "close portrait", "artistic portrait",
        "character study", "head portrait", "individual portrait",
    ],
    "landscape": [
        "landscape", "scenery", "panoramic", "vista", "terrain",
        "wilderness landscape", "horizon", "scenic view",
        "landscape art", "outdoor scene", "environmental scene",
        "nature landscape", "open landscape", "vast landscape",
        "scenic", "panorama", "sweeping view", "distant horizon",
        "rolling hills", "valley", "mountain landscape", "coastal",
        "seascape", "countryside", "rural", "open land", "vast terrain",
        "dramatic landscape", "epic landscape", "natural landscape",
    ],
    "creature": [
        "creature", "beast", "monster", "mythical creature", "dragon",
        "demon", "entity", "animal hybrid", "chimera",
        "animal", "beast form", "creature design", "fantasy creature",
        "supernatural creature", "monster design", "magical creature",
        "hybrid creature", "alien creature",
        "wolf", "cat", "bird", "serpent", "spirit creature",
        "spirit animal", "totem", "mythical beast", "legendary creature",
        "dark creature", "evil creature", "angelic creature",
        "phoenix", "griffin", "hydra", "basilisk", "gargoyle",
    ],
    "character": [
        "character", "hero", "warrior", "protagonist", "knight",
        "wanderer", "adventurer", "figure design", "solitary figure",
        "character design", "character art", "full body", "full-body",
        "standing figure", "walking", "action pose", "pose",
        "fighter", "soldier", "assassin", "rogue", "mage",
        "sorcerer", "witch", "ranger", "explorer", "hunter",
        "character concept", "game character", "film character",
        "hero character", "villain", "protagonist design",
    ],
    "architecture": [
        "architecture", "building", "structure", "facade", "monument",
        "architectural", "interior space", "constructed",
        "architectural design", "building design", "exterior",
        "structure design", "castle", "temple", "tower", "palace",
        "citadel", "fortress", "dungeon", "cathedral", "church",
        "ruins", "ancient building", "fantasy architecture",
        "sci-fi architecture", "futuristic building", "urban architecture",
        "architectural style", "building facade", "architectural art",
    ],
    "nature": [
        "botanical", "garden", "flora", "trees", "forest",
        "plant life", "organic growth", "nature",
        "flowers", "plants", "woodland", "jungle", "tropical",
        "botanical illustration", "nature art", "floral", "greenery",
        "leaf", "foliage", "grass", "moss", "fern", "mushroom",
        "underwater life", "coral", "botanical study", "wild plant",
        "overgrown", "nature scene", "lush vegetation", "nature design",
    ],
    "space": [
        "space", "cosmic", "galaxy", "nebula", "stars", "planet",
        "astronaut", "deep space", "stellar",
        "space art", "outer space", "space scene", "space landscape",
        "alien planet", "moon", "sun", "universe", "cosmos",
        "space station", "spaceship", "rocket", "asteroid", "comet",
        "black hole", "supernova", "star cluster", "space exploration",
        "space opera", "orbital", "interstellar", "galactic art",
    ],
    "urban": [
        "urban scene", "city street", "downtown", "alley",
        "metropolis", "street scene", "city",
        "urban environment", "cityscape", "city life", "urban art",
        "street", "building", "traffic", "crowd", "urban landscape",
        "night city", "urban decay", "ghetto", "suburb",
        "concrete jungle", "city lights", "urban photography",
        "architectural urban", "urban culture",
    ],
    "mythology": [
        "mythology", "mythological", "god", "goddess", "deity",
        "legend", "myth", "ancient god", "pantheon",
        "mythic", "divine", "sacred", "ancient myth", "mythological figure",
        "greek mythology", "norse mythology", "egyptian mythology",
        "roman mythology", "celtic mythology", "ancient legend",
        "heroic myth", "legendary figure", "mythic hero",
        "creation myth", "divine being", "religious art",
        "ancient deity", "mythological creature", "folklore deity",
        "zeus", "thor", "odin", "anubis", "olympus",
    ],
    "fashion": [
        "fashion", "garment", "couture", "clothing", "wearable",
        "outfit", "fashion design", "apparel",
        "fashion art", "fashion illustration", "fashion portrait",
        "model", "fashion model", "dress", "costume", "wardrobe",
        "fashion editorial", "runway", "haute couture", "design fashion",
        "wearable art", "fashion concept", "clothing design",
        "fashion photography", "stylish", "fashionable",
    ],
    "abstract_concept": [
        "abstract concept", "metaphor", "symbolic", "conceptual art",
        "philosophical", "allegory",
        "concept", "conceptual", "symbolic art", "metaphorical",
        "idea art", "thought", "abstract idea", "conceptual design",
        "philosophical art", "allegorical", "narrative art",
        "symbolic design", "visual metaphor", "conceptual illustration",
        "intellectual art", "mind concept", "visual concept",
    ],
    "interior": [
        "interior", "indoor", "inside space", "room design",
        "living space", "domestic", "home",
        "interior design", "room", "living room", "bedroom", "kitchen",
        "bathroom", "hallway", "library interior", "study room",
        "interior scene", "indoor scene", "home interior",
        "architectural interior", "room scene", "interior art",
        "cozy interior", "dramatic interior", "luxury interior",
    ],
    "still_life": [
        "still life", "object arrangement", "artifact",
        "composition study", "object study",
        "still life art", "objects", "table setting", "arrangement",
        "product photography", "product art", "object art",
        "composition", "tabletop", "desktop", "collected objects",
        "treasure", "curio", "curiosity cabinet", "vanitas",
        "still life painting", "object portrait",
    ],
}

MOOD_KEYWORDS: dict[str, list[str]] = {
    "dark": [
        "dark mood", "darkness", "shadow", "sinister", "ominous",
        "grim", "bleak", "foreboding", "menacing", "somber",
        "dark", "shadowy", "gloomy", "dim", "moody", "brooding",
        "black", "night", "noir", "dark atmosphere", "threatening",
        "oppressive", "heavy", "dark art", "deep dark",
        "shadow art", "dark world", "dark theme", "despair",
        "doom", "gloom", "dusk", "midnight", "deep shadow",
    ],
    "ethereal": [
        "ethereal", "otherworldly", "transcendent", "luminous",
        "celestial", "spiritual glow", "divine light", "luminescent",
        "glowing", "divine", "spiritual", "light", "radiant",
        "soft light", "heavenly", "angelic", "dreamy", "delicate",
        "pure", "magical light", "spirit light", "ghost light",
        "aura", "ethereal glow", "soft glow", "halo", "shimmer",
        "translucent", "gossamer", "otherworldly glow", "celestial light",
    ],
    "epic": [
        "epic", "grand scale", "monumental", "vast", "heroic",
        "majestic", "awe-inspiring", "legendary", "titanic",
        "grand", "massive", "enormous", "powerful", "dramatic",
        "magnificent", "incredible", "stunning", "colossal", "mighty",
        "breathtaking", "awe", "inspiring", "vast scale", "epic art",
        "epic scene", "epic battle", "heroic art", "monumental art",
        "epic fantasy", "mythic epic", "legendary epic", "grand epic",
    ],
    "serene": [
        "serene", "peaceful", "calm", "tranquil", "gentle",
        "harmonious", "quiet beauty", "still", "meditative",
        "calming", "relaxing", "soothing", "quiet",
        "soft", "zen", "balanced", "serenity",
        "pastoral", "morning", "dawn", "nature peaceful",
        "serene art", "peaceful art", "calm art", "quiet moment",
    ],
    "whimsical": [
        "whimsical", "playful", "quirky", "charming", "whimsy",
        "fanciful", "lighthearted", "joyful", "enchanting",
        "fun", "cute", "adorable", "sweet", "cheerful",
        "happy", "playful art", "charming art", "whimsy art",
        "fairy tale", "magical fun", "imaginative", "creative",
        "childlike", "storybook", "cartoon", "light mood",
        "positive", "delightful", "enchanting art",
    ],
    "melancholic": [
        "melancholic", "melancholy", "sad", "sorrowful", "lonely",
        "isolation", "contemplative", "introspective", "wistful",
        "sadness", "sorrow", "grief", "mourning", "lost",
        "empty", "alone", "desolate", "abandoned", "forgotten",
        "fading", "aging", "memory", "nostalgia", "nostalgic",
        "yearning", "longing", "bittersweet", "pensive",
        "emotional", "touching", "moving", "quiet sadness",
    ],
    "mysterious": [
        "mysterious", "mystery", "enigmatic", "cryptic", "obscure",
        "hidden", "mystifying", "unknown", "arcane mystery",
        "fog", "mist", "enigma", "shadowy", "dark mystery",
        "veiled", "concealed", "elusive", "puzzling",
        "mysterious atmosphere", "mystery art",
        "occult mystery", "arcane secret", "mystical mystery",
    ],
    "futuristic": [
        "futuristic mood", "technological", "digital age",
        "post-human", "advanced civilization", "techno",
        "future", "futuristic", "advanced", "technology", "tech",
        "digital world", "techno", "cyber", "modern future",
        "tomorrow", "speculative", "advanced technology", "high tech",
        "futuristic art", "future world", "tech mood", "sci-fi mood",
    ],
    "romantic": [
        "romantic", "romance", "love", "tender", "intimate",
        "passionate", "warm feeling", "affectionate",
        "passion", "desire", "sensual", "loving", "warm",
        "soft romantic", "romantic art", "love art", "couple",
        "tender moment", "intimate moment", "warm mood", "heart",
        "affection", "romance art", "romantic scene", "romantic light",
    ],
    "chaotic": [
        "chaotic", "chaos", "disorder", "turbulent", "explosive",
        "intense energy", "wild", "frenzied", "violent",
        "chaos art", "chaotic energy", "explosive",
        "wild energy", "intense", "turbulent", "storm",
        "destructive", "powerful chaos", "dynamic chaos",
        "chaotic scene", "energy chaos", "battle chaos", "war",
    ],
    "dramatic": [
        "dramatic", "cinematic", "theatrical", "stage-lit", "high contrast",
        "spotlight", "dramatic lighting", "dramatic scene", "dramatic portrait",
        "cinematic drama", "theatric", "staged", "grand dramatic", "cinematic tension",
        "film drama", "dramatic light", "stage light", "theatrical light",
        "dramatic composition", "dramatic atmosphere", "cinematic mood",
        "dramatic art", "dramatic photography", "cinema quality", "cinematic quality",
        "dramatic shadow", "chiaroscuro", "theater", "dramatic effect",
        "stage production", "dramatic pose", "cinematic quality",
        "dramatic rendering", "film quality", "dramatic contrast",
    ],
    "elegant": [
        "elegant", "refined", "sophisticated", "luxurious", "luxury",
        "graceful", "poised", "noble", "aristocratic", "haute couture",
        "opulent", "sumptuous", "lavish", "exquisite", "tasteful",
        "cultivated", "polished", "stately", "regal", "refinement",
        "elegant style", "elegant composition", "elevated", "dignified",
        "majestic elegance", "haute", "delicate refinement",
        "classic elegance", "sophisticated art", "elegant portrait",
        "beauty and elegance", "sleek and refined", "luxury art",
        "fine detail", "refined composition", "opulence",
    ],
}

PALETTE_KEYWORDS: dict[str, list[str]] = {
    "pastel": [
        "pastel", "soft pink", "lavender", "baby blue", "cream tones",
        "light palette", "delicate hue", "blush",
        "soft color", "gentle color", "light color", "pale color",
        "pink", "lilac", "mint", "cream", "rosy", "peach",
        "powder blue", "pale yellow", "soft purple", "soft tone",
        "candy color", "delicate palette", "pastel palette",
        "soft pastel", "pastel tones", "gentle pastel",
    ],
    "neon": [
        "neon", "fluorescent", "electric glow", "neon light",
        "bright synthetic", "luminous neon", "glow effect", "blacklight",
        "electric color", "glowing color", "bright glow", "luminous",
        "LED color", "neon palette", "neon art", "glow art",
        "UV glow", "blacklight art", "electric", "fluorescent color",
        "neon aesthetic", "glowing", "neon sign",
    ],
    "monochrome": [
        "monochrome", "black and white", "grayscale", "greyscale",
        "monochromatic", "achromatic",
        "black", "white", "grey", "gray", "monotone", "single color",
        "no color", "desaturated", "tonal", "black and white art",
        "monochrome art", "greyscale art", "b&w",
        "single tone", "ink black", "charcoal grey",
    ],
    "sepia": [
        "sepia", "amber tone", "brown tone", "aged photograph",
        "warm brownish", "sepia palette", "antique tone",
        "sepia tone", "warm sepia", "aged", "vintage tone",
        "antique", "old photo", "warm brown", "aged palette",
        "historical tone", "warm aged", "old school color",
        "brown palette", "warm vintage", "sepia art",
    ],
    "vibrant": [
        "vibrant color", "vivid", "saturated color", "high saturation",
        "maximum saturation", "colorful", "bright palette",
        "vibrant", "vivid colors", "intense color", "bold color",
        "bright color", "colorful", "multicolor", "rainbow",
        "rich color", "saturated", "strong color", "dynamic color",
        "vibrant art", "colorful art", "vivid art", "color burst",
    ],
    "muted": [
        "muted", "desaturated", "subdued color", "toned down",
        "faded", "muted palette", "low saturation", "soft muted",
        "earthy muted",
        "subtle color", "understated", "quiet color", "washed",
        "washed out", "faded color", "muted tone", "soft tone",
        "subdued", "grey tone", "desaturated art", "faded palette",
        "muted art", "quiet palette", "toned down color",
    ],
    "golden": [
        "golden", "gold palette", "amber", "warm golden",
        "ochre", "burnished gold", "golden hue", "gilded",
        "gold", "warm gold", "yellow gold", "orange gold",
        "golden hour", "sunlight", "warm light", "amber light",
        "bronze", "copper tone", "warm palette", "golden glow",
        "gilded art", "golden art", "warm amber", "golden light",
    ],
    "dark": [
        "dark palette", "deep tones", "shadow tones", "almost black",
        "dim palette", "dark color", "ink black",
        "dark", "deep color", "shadow color", "black palette",
        "night palette", "dark theme color", "darkness palette",
        "near black", "dark art color", "moody dark", "deep dark",
        "somber color", "gloomy color", "deep shadow color",
    ],
    "cold_blues": [
        "cold blue", "blue palette", "teal", "cyan palette",
        "icy blue", "cerulean", "cold color", "blue tones", "steel blue",
        "blue", "cold", "cool", "icy", "frost", "winter color",
        "teal color", "cyan", "aqua", "navy", "cobalt",
        "blue art", "cold art", "cool palette", "winter palette",
        "frigid", "cold atmosphere", "blue aesthetic", "cool tone",
    ],
    "earth_tones": [
        "earth tone", "terracotta", "brown earthy", "beige",
        "rustic", "natural pigment", "warm earth", "ochre earth",
        "warm neutral",
        "brown", "earth", "soil", "wood color", "natural color",
        "warm brown", "tan", "beige", "clay", "stone color",
        "earthy", "terra", "organic color", "muddy", "autumn color",
        "warm neutral", "rustic color", "natural tone", "earth art",
    ],
    "purple_violet": [
        "purple", "violet", "indigo", "amethyst", "magenta",
        "lilac violet", "violet hue", "deep purple", "royal purple",
        "mystical violet", "plum", "mulberry", "grape", "mauve",
        "blue-violet", "violet purple", "violet sky", "purple art",
        "violet light", "purple haze", "purple tone", "violet glow",
        "indigo blue", "deep violet", "purple palette", "violet palette",
        "purple mood", "violet aesthetic", "purple magic", "violet mist",
        "purple saturation", "ultraviolet", "deep indigo",
    ],
    "warm_fire": [
        "crimson", "scarlet", "red-orange", "fire", "flame",
        "ember", "burning red", "fiery", "warm red", "bright red",
        "orange red", "red flame", "volcanic red", "molten", "lava",
        "fire red", "hot red", "fire orange", "inferno", "blaze",
        "burning", "fire color", "flame color", "hot color",
        "fire palette", "flame palette", "ember glow", "warm fire",
        "sunset red", "orange flame", "incandescent", "volcanic",
        "magma", "conflagration", "scorched", "smoldering",
    ],
}

GEO_KEYWORDS: dict[str, list[str]] = {
    "soft-wash": [
        # keyword testo libero
        "watercolor", "aquarelle", "watercolour", "color bleed",
        "wet on wet", "dissolved edge", "fluid paint", "soft blend",
        # frasi dell'analysis field (campo "Style:" e "Palette:")
        "soft chalk texture",   # 127 entry
        "pale translucent pastels",  # 92 entry
        "plein air",            # 47 entry
        "soft muted tones",     # 127 entry
        "soft focus",           # 92 entry
        "gentle wash",
    ],
    "organic-curves": [
        # keyword testo libero — "organic" da solo copre 377 entry
        "organic", "swirl", "spiral", "arabesque", "ornamental",
        "flowing", "sinuous", "fluid motion", "ribbon", "curvilinear",
        "ornate", "tendrils",
        # frasi analysis
        "storybook illustration",   # 87 entry (forme morbide)
        "digital painting",         # 56 entry
    ],
    "flat-color": [
        "flat color", "flat design", "block color",
        "bold outline", "poster style", "simplified form", "flat graphic",
        # frasi analysis
        "pure form and color",      # 85 entry
        "reduction to essence",     # 59 entry
        "period graphic design",    # 57 entry
        "limited neutral tones",    # 59 entry
        "non-representational",     # 85 entry
        "tonal reduction",          # 63 entry
    ],
    "line-based": [
        "line art", "sketch", "linework", "pen drawing", "ink",
        "hatching", "contour line", "grisaille", "crosshatch",
        "pencil", "hand drawn",
        # frasi analysis
        "calligraphic linework",    # 58 entry
        "black ink on white",       # 58 entry
        "deep shadows and charcoal",# 86 entry
        "desaturated greyish",      # 63 entry
    ],
    "continuous-tone": [
        "photorealistic", "photograph", "cinematic", "hyperrealistic",
        "photorealism",
        # frasi analysis
        "hyper realist dream",      # 95 entry
        "chiaroscuro",              # 86 entry
        "golden hour",              # 69 entry
        "retro photography",        # 53 entry
        "warm amber and gold",      # 69 entry
        "tonal reduction",          # 63 entry (anche flat, ma qui più preciso)
    ],
    "geometric-hard": [
        "geometric", "polygon", "tessellation", "crystalline",
        "grid pattern", "hexagonal", "sharp angle", "faceted",
        "hard-edge", "angular pattern", "prismatic",
    ],
    "volumetric-hard": [
        "3d render", "cgi", "blender", "octane", "subsurface scatter",
        "ray tracing", "digital sculpt", "voxel",
        # frasi analysis
        "digital glow",             # 151 entry (effetti luce 3D)
    ],
    "organic-dark": [
        "dark organic", "shadow flora", "dark forest", "midnight nature",
        "dark botanical", "gothic nature", "dark atmospheric",
        "organic shadow", "dark foliage", "moody organic",
        "dark nature", "shadow garden", "nocturnal flora",
    ],
    "surreal-open": [
        "surreal", "dreamscape", "impossible", "subconscious",
        "dreamlike", "uncanny", "liminal", "distorted reality",
        "dream logic", "hallucination", "fever dream",
        # frasi analysis
        "surrealist landscape",         # 87 entry
        "luminous impossible tones",    # 121 entry
        "dream-logic mixed palette",    # 95 entry
        "soft fantasy palette",         # 87 entry
        "soft impossible palette",      # 87 entry
        "visionary art",                # 45 entry
        "high fantasy",                 # 121 entry (elementi magici/impossibili)
    ],
}

# ---------------------------------------------------------------------------
# Funzioni di tagging
# ---------------------------------------------------------------------------

def get_text(entry: dict) -> str:
    return " ".join([
        entry.get("nome", ""),
        entry.get("description", ""),
        entry.get("keywords", ""),
        entry.get("analysis", ""),
        entry.get("hashtags", ""),
    ]).lower()


def match_tags(text: str, keyword_dict: dict[str, list[str]]) -> list[str]:
    tags = []
    for tag, keywords in keyword_dict.items():
        for kw in keywords:
            if kw.lower() in text:
                tags.append(tag)
                break
    return tags


# Fallback geo -> tag probabile per SREF non coperti da keyword matching
_GEO_SUBJECT_HINT: dict[str, list[str]] = {
    "soft-wash":       ["nature", "portrait"],
    "organic-curves":  ["nature", "creature"],
    "flat-color":      ["character", "abstract_concept"],
    "line-based":      ["character", "abstract_concept"],
    "continuous-tone": ["portrait", "landscape"],
    "geometric-hard":  ["architecture", "abstract_concept"],
    "volumetric-hard": ["character", "architecture"],
    "organic-dark":    ["creature", "mythology"],
    "surreal-open":    ["abstract_concept", "landscape"],
    "unknown":         ["abstract_concept"],
}

_GEO_STYLE_HINT: dict[str, list[str]] = {
    "soft-wash":       ["watercolor", "pastel_soft"],
    "organic-curves":  ["illustration", "painting"],
    "flat-color":      ["illustration", "minimalist"],
    "line-based":      ["ink_sketch", "geometric"],
    "continuous-tone": ["painting", "photorealism"],
    "geometric-hard":  ["geometric", "minimalist"],
    "volumetric-hard": ["3d_render", "painting"],
    "organic-dark":    ["gothic", "horror"],
    "surreal-open":    ["surreal", "fantasy"],
    "unknown":         ["illustration"],
}

_STYLE_MOOD_HINT: dict[str, list[str]] = {
    "horror":      ["dark", "mysterious"],
    "gothic":      ["dark", "mysterious"],
    "fantasy":     ["ethereal", "epic"],
    "cyberpunk":   ["futuristic", "chaotic"],
    "sci_fi":      ["futuristic"],
    "surreal":     ["mysterious", "ethereal"],
    "pastel_soft": ["serene", "ethereal"],
    "watercolor":  ["serene", "ethereal"],
    "vibrant_pop": ["whimsical", "chaotic"],
    "minimalist":  ["serene"],
    "nature":      ["serene"],
}

_STYLE_PALETTE_HINT: dict[str, list[str]] = {
    "vibrant_pop": ["vibrant"],
    "pastel_soft": ["pastel"],
    "watercolor":  ["muted", "pastel"],
    "noir":        ["monochrome", "dark"],
    "gothic":      ["dark"],
    "horror":      ["dark"],
    "vintage_retro": ["sepia", "muted"],
    "cyberpunk":   ["neon"],
    "steampunk":   ["golden", "earth_tones"],
    "ink_sketch":  ["monochrome"],
    "minimalist":  ["muted"],
}


def _apply_fallbacks(entry: dict) -> None:
    """Assegna tag di fallback per SREF con 0 match su una dimensione."""
    style  = entry.get("style_tags", [])
    mood   = entry.get("mood_tags", [])
    geo    = entry.get("geo", "unknown")

    # Subject fallback: usa geo + style
    if not entry["subject_tags"]:
        if "abstract" in style or "minimalist" in style or "geometric" in style:
            entry["subject_tags"] = ["abstract_concept"]
        else:
            entry["subject_tags"] = _GEO_SUBJECT_HINT.get(geo, ["abstract_concept"])

    # Style fallback: usa geo
    if not entry["style_tags"]:
        entry["style_tags"] = _GEO_STYLE_HINT.get(geo, ["illustration"])

    # Mood fallback: usa style
    if not entry["mood_tags"]:
        for s in style:
            if s in _STYLE_MOOD_HINT:
                entry["mood_tags"] = _STYLE_MOOD_HINT[s]
                break
        if not entry["mood_tags"]:
            entry["mood_tags"] = ["mysterious"]

    # Palette fallback: usa style, poi mood
    if not entry["palette_tags"]:
        for s in style:
            if s in _STYLE_PALETTE_HINT:
                entry["palette_tags"] = _STYLE_PALETTE_HINT[s]
                break
        if not entry["palette_tags"]:
            if "dark" in mood:
                entry["palette_tags"] = ["dark"]
            elif "ethereal" in mood or "serene" in mood:
                entry["palette_tags"] = ["muted"]
            else:
                entry["palette_tags"] = ["vibrant"]


def get_geo(text: str) -> str:
    scores: dict[str, int] = {}
    for geo, keywords in GEO_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[geo] = score
    if not scores:
        return "unknown"
    return max(scores, key=lambda k: scores[k])


# ---------------------------------------------------------------------------
# Naming CIANOAI — vocabolario brand per generare nomi unici da tag+geo
# ---------------------------------------------------------------------------

_ADJ_STYLE: dict[str, list[str]] = {
    "fantasy":       ["Arcane","Mythic","Eldritch","Ethereal","Fabled","Enchanted","Mystic","Runic","Sacred","Astral"],
    "cyberpunk":     ["Neon","Chrome","Synthetic","Digital","Glitch","Circuit","Volt","Pulse","Coded","Wired"],
    "sci_fi":        ["Stellar","Quantum","Orbital","Cosmic","Ionic","Nexus","Solar","Photon","Ether","Vector"],
    "gothic":        ["Obsidian","Nocturnal","Cinder","Vex","Pallid","Raven","Grim","Iron","Dusk","Ashen"],
    "horror":        ["Abyssal","Hollow","Cursed","Wretched","Dread","Murk","Gaunt","Bleak","Vile","Spectral"],
    "anime_manga":   ["Vivid","Kinetic","Radiant","Flash","Pure","Swift","Bold","Clear","Sharp","Bright"],
    "watercolor":    ["Fluid","Aqua","Delicate","Tender","Mellow","Bloom","Pastel","Gossamer","Silk","Petal"],
    "ink_sketch":    ["Inked","Crisp","Dense","Stark","Fine","Etch","Scratch","Raw","Drawn","Lined"],
    "photorealism":  ["Hyper","Sharp","Lucid","Exact","Ultra","Pure","Acute","Focused","Pristine","True"],
    "illustration":  ["Lush","Rich","Vibrant","Craft","Rendered","Drawn","Warm","Layered","Stacked","Polished"],
    "abstract":      ["Kinetic","Shifting","Liminal","Primal","Chaotic","Fractured","Free","Open","Fluid","Raw"],
    "minimalist":    ["Silent","Spare","Calm","Still","Mute","Bare","Lean","Void","Quiet","Clean"],
    "geometric":     ["Angular","Rigid","Exact","Faceted","Planar","Ordered","Hard","Fixed","True","Prismic"],
    "3d_render":     ["Cast","Volumic","Dense","Solid","Forge","Mass","Rendered","Sculpted","Formed","Molded"],
    "vintage_retro": ["Faded","Worn","Aged","Sepia","Amber","Mellow","Hazy","Weathered","Antique","Tarnished"],
    "nature":        ["Wild","Moss","Fern","Bloom","Grove","Lush","Verdant","Rooted","Stone","Earth"],
    "urban":         ["Grit","Steel","Slate","Cold","Stark","Dense","Raw","Concrete","Blunt","Edge"],
    "painting":      ["Impasto","Rich","Deep","Grand","Thick","Vivid","Heavy","Layered","Textured","Stroked"],
    "surreal":       ["Drift","Haze","Warp","Echo","Liminal","Flux","Eerie","Strange","Warped","Rift"],
    "pastel_soft":   ["Blush","Lilac","Gentle","Tender","Mild","Sweet","Airy","Soft","Muted","Chalky"],
    "vibrant_pop":   ["Loud","Pop","Vivid","Neon","Hot","Electric","Blazing","Radiant","Flash","Surge"],
    "noir":          ["Shadow","Smoke","Bleak","Cold","Grim","Stark","Night","Dim","Veiled","Gunmetal"],
    "steampunk":     ["Brass","Copper","Geared","Steam","Cogged","Rustic","Forged","Patina","Riveted","Burnished"],
}

_ADJ_MOOD: dict[str, list[str]] = {
    "dark":        ["Void","Abyssal","Shadow","Grim","Bleak","Murk","Onyx","Umbral","Pitch","Dusky"],
    "ethereal":    ["Celestial","Lunar","Aurora","Opal","Spectral","Aether","Misty","Diaphanous","Vaporous","Pearlescent"],
    "epic":        ["Titan","Grand","Apex","Valor","Mighty","Prime","Royal","Sovereign","Colossal","Monumental"],
    "serene":      ["Still","Calm","Placid","Tranquil","Gentle","Mellow","Hushed","Soft","Mild","Restful"],
    "whimsical":   ["Playful","Quirky","Light","Airy","Merry","Brisk","Whimsy","Fanciful","Dainty","Bubbly"],
    "melancholic": ["Faded","Wistful","Pallid","Dull","Dim","Somber","Hollow","Waning","Listless","Forlorn"],
    "mysterious":  ["Veiled","Hidden","Cryptic","Obscure","Arcane","Unseen","Covert","Shadowed","Opaque","Shrouded"],
    "futuristic":  ["Nexus","Quantum","Hyper","Volt","Pulse","Chrome","Digital","Ionic","Photon","Synth"],
    "romantic":    ["Amber","Rose","Velvet","Tender","Gilded","Warmth","Bloom","Sienna","Coral","Crimson"],
    "chaotic":     ["Surge","Fierce","Frenetic","Storm","Clash","Turbulent","Kinetic","Volatile","Erratic","Fractured"],
    "dramatic":    ["Stage","Stark","Loom","Vivid","Tense","Cinematic","Bold","Pitch","Grand","Thunder"],
    "elegant":     ["Petal","Silk","Pearl","Ivory","Velvet","Refined","Lace","Satin","Gilt","Poise"],
}

_NOUN_GEO: dict[str, list[str]] = {
    "soft-wash":       ["Veil","Mist","Bloom","Wash","Canvas","Haze","Glow","Drift","Shore","Breath"],
    "organic-curves":  ["Weave","Flow","Spiral","Wave","Coil","Tendril","Arc","Curl","Loop","Vine"],
    "flat-color":      ["Block","Plane","Field","Layer","Form","Panel","Stack","Slab","Face","Tile"],
    "line-based":      ["Arc","Wire","Edge","Trace","Grid","Contour","Seam","Stroke","Path","Filament"],
    "continuous-tone": ["Shade","Gradient","Depth","Tone","Scale","Range","Hue","Spectrum","Fade","Blend"],
    "geometric-hard":  ["Prism","Facet","Apex","Shard","Vertex","Wedge","Cube","Lattice","Matrix","Frame"],
    "volumetric-hard": ["Core","Mass","Vault","Forge","Pillar","Boulder","Column","Monolith","Block","Spire"],
    "organic-dark":    ["Hollow","Root","Den","Burrow","Thorn","Knot","Lair","Gnarl","Pit","Crevice"],
    "surreal-open":    ["Void","Dream","Portal","Rift","Expanse","Beyond","Liminal","Abyss","Realm","Expanse"],
    "unknown":         ["Frame","Drift","Lens","Form","Pulse","Node","Mark","Shard","Trace","Glyph"],
}

_FALLBACK_ADJ = ["Arcane","Mystic","Void","Lunar","Prime","Deep","Raw","Bold","Dark","Pure",
                  "Soft","Grand","Ancient","Silver","Dusky","Amber","Iron","Neon","Pale","Wild"]


def _cianoai_name(entry: dict, used: set[str]) -> str:
    """Genera un nome brand CIANOAI deterministico e unico per un SREF."""
    rng = random.Random(f"smf-name-v1-{entry['sref']}")

    # Aggettivo: da style_tags, poi mood_tags, poi fallback
    adj = ""
    for tag in entry.get("style_tags", []):
        if tag in _ADJ_STYLE:
            pool = _ADJ_STYLE[tag]
            adj = pool[rng.randint(0, len(pool) - 1)]
            break
    if not adj:
        for tag in entry.get("mood_tags", []):
            if tag in _ADJ_MOOD:
                pool = _ADJ_MOOD[tag]
                adj = pool[rng.randint(0, len(pool) - 1)]
                break
    if not adj:
        adj = _FALLBACK_ADJ[rng.randint(0, len(_FALLBACK_ADJ) - 1)]

    # Sostantivo: da geo
    geo  = entry.get("geo", "unknown")
    pool = _NOUN_GEO.get(geo, _NOUN_GEO["unknown"])
    noun = pool[rng.randint(0, len(pool) - 1)]

    base = f"{adj} {noun}"
    name = base
    suffix = 2
    while name in used:
        name = f"{base} {suffix}"
        suffix += 1
    used.add(name)
    return name


def enrich(data: list[dict]) -> list[dict]:
    used_names: set[str] = set()
    for entry in data:
        text = get_text(entry)
        entry["style_tags"]   = match_tags(text, STYLE_KEYWORDS)
        entry["subject_tags"] = match_tags(text, SUBJECT_KEYWORDS)
        entry["mood_tags"]    = match_tags(text, MOOD_KEYWORDS)
        entry["palette_tags"] = match_tags(text, PALETTE_KEYWORDS)
        entry["geo"]          = get_geo(text)
        # Fallback: assegna tag basati su geo/style per SREF non coperti da keyword
        _apply_fallbacks(entry)
        entry["nome"]         = _cianoai_name(entry, used_names)
    return data


# ---------------------------------------------------------------------------
# Slim: riduce i campi prima dell'embedding (rimuove campi non usati dal browser)
# ---------------------------------------------------------------------------

def slim(entry: dict) -> dict:
    return {
        "sref": entry["sref"],
        "nome": entry["nome"],
        "manuale": entry.get("manuale", False),
        "description": entry["description"],
        "keywords": entry["keywords"],
        "geo": entry["geo"],
        "style_tags": entry["style_tags"],
        "subject_tags": entry["subject_tags"],
        "mood_tags": entry["mood_tags"],
        "palette_tags": entry["palette_tags"],
    }


# ---------------------------------------------------------------------------
# Template HTML (app offline completa — freemium)
# Placeholder: ###DATA### = JSON base64, ###CODES### = array JS codici premium
# ---------------------------------------------------------------------------

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>CIANOAI SrefMindForge</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ===== VARIABILI ===== */
:root {
  --bg: #0d0d1a; --card: #1a1a2e; --card2: #141428;
  --accent: #e94560; --pro: #9b59b6; --pro-dark: #6c3483;
  --text: #f0f0f0; --muted: #8888aa; --border: #2a2a44;
  --geo-soft-wash: #4fc3f7; --geo-organic-curves: #81c784;
  --geo-flat-color: #fff176; --geo-line-based: #ba68c8;
  --geo-continuous-tone: #4dd0e1; --geo-geometric-hard: #ff7043;
  --geo-volumetric-hard: #ffa726; --geo-organic-dark: #78909c;
  --geo-surreal-open: #ef9a9a; --geo-unknown: #aaaaaa;
}

/* ===== RESET / BASE ===== */
body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; min-height: 100vh; padding-bottom: 60px; }

/* ===== HEADER ===== */
.header { background: linear-gradient(135deg,#0d0d1a 0%,#1a0a2e 50%,#0d0d1a 100%); border-bottom: 1px solid var(--border); padding: 32px 24px 24px; text-align: center; }
.header h1 { font-size: clamp(1.6rem,4vw,2.6rem); font-weight: 900; letter-spacing: .12em; }
.header h1 span { color: var(--accent); }
.header p { margin-top: 8px; color: var(--muted); font-size: .92rem; letter-spacing: .04em; }
.header-badges { display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 14px; }
.badge-tier { font-size: .7rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; padding: 4px 14px; border-radius: 20px; cursor: pointer; transition: background .15s; }
.badge-tier-free { background: var(--border); color: var(--muted); }
.badge-tier-pro { background: linear-gradient(135deg,var(--pro),var(--pro-dark)); color: #fff; }
.badge-tier:hover { opacity: .85; }

/* ===== FILTRI ===== */
.filter-section { max-width: 860px; margin: 28px auto 0; padding: 0 16px; }
.filter-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
@media(max-width:520px){ .filter-grid { grid-template-columns:1fr; } }
.filter-group label { display: block; font-size: .72rem; font-weight: 700; letter-spacing: .1em; color: var(--muted); margin-bottom: 6px; text-transform: uppercase; }
.filter-group select { width: 100%; padding: 10px 14px; background: var(--card); color: var(--text); border: 1px solid var(--border); border-radius: 8px; font-size: .95rem; cursor: pointer; appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath fill='%238888aa' d='M6 8L0 0h12z'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 14px center; }
.filter-group select:focus { outline: none; border-color: var(--accent); }

/* ===== CAMPO IDEA ===== */
.idea-section { margin-top: 14px; background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }
.idea-section label { display: block; font-size: .7rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; }
.idea-input { width: 100%; padding: 10px 14px; background: var(--card2); color: var(--text); border: 1px solid var(--border); border-radius: 6px; font-size: .92rem; font-family: inherit; }
.idea-input:focus { outline: none; border-color: var(--accent); }
.idea-hint { font-size: .7rem; color: var(--muted); margin-top: 5px; }
.idea-preview { margin-top: 10px; padding: 8px 12px; background: rgba(233,69,96,.07); border: 1px solid rgba(233,69,96,.25); border-radius: 6px; display: none; }
.idea-preview-label { font-size: .62rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--accent); margin-bottom: 4px; }
.idea-preview-text { font-family: 'Cascadia Code','Consolas',monospace; font-size: .75rem; color: #c3e88d; line-height: 1.5; overflow-wrap: break-word; word-break: break-word; }

/* ===== ROLL COUNTER ===== */
.roll-display { font-size: .72rem; color: var(--muted); }
.roll-display.roll-zero { color: var(--accent); font-weight: 700; }
.btn-reset-roll { background: transparent; border: 1px solid var(--border); color: var(--muted); border-radius: 20px; padding: 4px 12px; font-size: .68rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; cursor: pointer; transition: all .15s; }
.btn-reset-roll:hover { border-color: var(--muted); color: var(--text); }

/* ===== BUTTON PDF ===== */
.btn-pdf { padding: 10px 24px; background: linear-gradient(135deg,var(--pro),var(--pro-dark)); color: #fff; border: none; border-radius: 8px; font-size: .85rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; cursor: pointer; transition: opacity .15s; }
.btn-pdf:hover { opacity: .85; }
.pdf-bar { text-align: right; margin-top: 20px; }

/* ===== BUTTON CERCA ===== */
.btn-search { display: block; width: 100%; margin-top: 16px; padding: 14px 24px; background: var(--accent); color: #fff; border: none; border-radius: 8px; font-size: 1rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; cursor: pointer; transition: background .15s, transform .1s; }
.btn-search:hover { background: #ff2a4a; }
.btn-search:active { transform: scale(.98); }

/* ===== RISULTATI ===== */
.results-section { max-width: 1100px; margin: 36px auto 0; padding: 0 16px; display: none; }
.results-section.visible { display: block; }
.section-title { font-size: .72rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 16px; }
.section-title span { color: var(--accent); }

/* ===== CARD SREF PURO ===== */
.puri-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 16px; }
@media(max-width:800px){ .puri-grid { grid-template-columns:1fr 1fr; } }
@media(max-width:520px){ .puri-grid { grid-template-columns:1fr; } }
.card-puro { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
.card-puro:hover { border-color: var(--accent); }
.sref-number { font-size: 2.4rem; font-weight: 900; color: var(--accent); line-height: 1; letter-spacing: -.02em; }
.sref-name { font-size: 1rem; font-weight: 700; color: var(--text); line-height: 1.3; }
.badges { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.badge { font-size: .68rem; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; padding: 3px 8px; border-radius: 4px; }
.badge-manuale { background: rgba(233,69,96,.18); color: var(--accent); border: 1px solid rgba(233,69,96,.35); }
.badge-score { background: var(--border); color: var(--muted); }
.badge-geo { color: #000; }
.geo-soft-wash       { background: var(--geo-soft-wash); }
.geo-organic-curves  { background: var(--geo-organic-curves); }
.geo-flat-color      { background: var(--geo-flat-color); }
.geo-line-based      { background: var(--geo-line-based); color:#fff; }
.geo-continuous-tone { background: var(--geo-continuous-tone); }
.geo-geometric-hard  { background: var(--geo-geometric-hard); color:#fff; }
.geo-volumetric-hard { background: var(--geo-volumetric-hard); }
.geo-organic-dark    { background: var(--geo-organic-dark); color:#fff; }
.geo-surreal-open    { background: var(--geo-surreal-open); }
.geo-unknown         { background: var(--geo-unknown); color:#333; }

/* ===== DETTAGLI COLLASSABILI ===== */
.card-details { font-size: .82rem; color: var(--muted); line-height: 1.5; flex: 1; }
details { border-top: 1px solid var(--border); padding-top: 8px; }
details + details { border-top: none; padding-top: 0; margin-top: 4px; }
summary { font-size: .7rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); cursor: pointer; padding: 4px 0; user-select: none; }
summary:hover { color: var(--text); }
details p { margin-top: 6px; font-size: .8rem; line-height: 1.55; }
.kw-list { margin-top: 6px; font-size: .78rem; font-style: italic; }

/* ===== PROMPT BOX ===== */
.prompt-box { background: var(--card2); border: 1px solid var(--border); border-radius: 6px; padding: 10px 12px; }
.prompt-label { font-size: .65rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin-bottom: 5px; }
.prompt-text { font-family: 'Cascadia Code','Fira Code','Consolas',monospace; font-size: .78rem; color: #c3e88d; overflow-wrap: break-word; word-break: break-word; line-height: 1.4; }
.btn-copy { margin-top: 8px; width: 100%; padding: 7px 12px; background: transparent; color: var(--muted); border: 1px solid var(--border); border-radius: 6px; font-size: .78rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; cursor: pointer; transition: all .15s; }
.btn-copy:hover { background: var(--accent); color: #fff; border-color: var(--accent); }
.btn-copy.copied { background: #27ae60; color: #fff; border-color: #27ae60; }

/* ===== MIX CARDS ===== */
.mix-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media(max-width:700px){ .mix-grid { grid-template-columns:1fr; } }
.card-mix { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.card-mix:hover { border-color: var(--pro); }
.mix-title { font-size: .8rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; color: var(--pro); }
.mini-cards { display: flex; gap: 8px; flex-wrap: wrap; }
.mini-card { background: var(--card2); border: 1px solid var(--border); border-radius: 6px; padding: 8px 12px; flex: 1; min-width: 90px; }
.mini-card-label { font-size: .6rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--pro); margin-bottom: 4px; }
.mini-card-sref { font-size: 1.1rem; font-weight: 900; color: var(--accent); line-height: 1; }
.mini-card-name { font-size: .7rem; color: var(--muted); margin-top: 2px; line-height: 1.3; }
.mix-reason { font-size: .67rem; color: var(--pro); font-style: italic; margin-top: 4px; line-height: 1.3; }

/* ===== PRO TEASER (utenti free) ===== */
.pro-teaser { margin-top: 32px; padding: 28px; border: 2px dashed var(--pro); border-radius: 12px; text-align: center; background: rgba(155,89,182,.06); }
.pro-teaser-badge { display: inline-block; background: var(--pro); color: #fff; font-size: .65rem; font-weight: 900; letter-spacing: .15em; padding: 3px 12px; border-radius: 20px; margin-bottom: 12px; }
.pro-teaser-title { font-size: 1.1rem; font-weight: 900; color: var(--pro); margin-bottom: 8px; }
.pro-teaser-text { font-size: .85rem; color: var(--muted); margin-bottom: 18px; line-height: 1.6; }
.pro-teaser-text strong { color: var(--text); }
.btn-upgrade { display: inline-block; padding: 12px 28px; background: linear-gradient(135deg,var(--pro),var(--pro-dark)); color: #fff; border: none; border-radius: 8px; font-size: .9rem; font-weight: 800; letter-spacing: .08em; cursor: pointer; transition: opacity .15s; }
.btn-upgrade:hover { opacity: .85; }

/* ===== NO RESULTS ===== */
.no-results { text-align: center; padding: 40px 20px; color: var(--muted); }
.no-results p { font-size: 1rem; margin-bottom: 8px; }
.no-results small { font-size: .82rem; }

/* ===== TAB NAV ===== */
.app-nav { display: flex; justify-content: center; border-bottom: 1px solid var(--border); background: var(--card); }
.nav-tab { padding: 13px 36px; background: transparent; color: var(--muted); border: none; border-bottom: 3px solid transparent; font-size: .78rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; cursor: pointer; transition: all .15s; }
.nav-tab:hover { color: var(--text); }
.nav-tab.active { color: var(--accent); border-bottom-color: var(--accent); }

/* ===== RESET BAR ===== */
.reset-bar { text-align: center; margin-top: 32px; padding-top: 24px; border-top: 1px solid var(--border); }
.btn-new-search { padding: 13px 36px; background: transparent; color: var(--text); border: 2px solid var(--border); border-radius: 8px; font-size: .9rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; cursor: pointer; transition: all .15s; }
.btn-new-search:hover { border-color: var(--accent); color: var(--accent); }
.reset-hint { font-size: .72rem; color: var(--muted); margin-top: 10px; line-height: 1.5; }

/* ===== MIX WEIGHT TIP ===== */
.weight-tip { font-size: .72rem; color: var(--muted); background: rgba(155,89,182,.06); border: 1px solid var(--border); border-radius: 6px; padding: 9px 14px; margin-bottom: 14px; line-height: 1.6; }
.weight-tip strong { color: var(--text); }

/* ===== ABOUT PAGE ===== */
#tab-about { max-width: 900px; margin: 0 auto; padding: 0 16px 80px; }
.about-hero { text-align: center; padding: 72px 20px 60px; }
.about-hero-tag { font-size: .68rem; font-weight: 900; letter-spacing: .18em; text-transform: uppercase; color: var(--accent); margin-bottom: 18px; }
.about-hero-h { font-size: clamp(2rem,5vw,3.4rem); font-weight: 900; line-height: 1.1; letter-spacing: -.02em; margin-bottom: 20px; }
.about-hero-h span { color: var(--accent); }
.about-hero-sub { font-size: 1.05rem; color: var(--muted); max-width: 560px; margin: 0 auto 32px; line-height: 1.65; }
.about-hero-sub em { color: var(--text); font-style: normal; font-weight: 700; }
.about-cta { display: inline-block; padding: 15px 40px; background: var(--accent); color: #fff; border: none; border-radius: 8px; font-size: 1rem; font-weight: 900; letter-spacing: .1em; text-transform: uppercase; cursor: pointer; transition: background .15s, transform .1s; }
.about-cta:hover { background: #ff2a4a; transform: translateY(-2px); }
.about-section { padding: 52px 0; border-top: 1px solid var(--border); }
.about-section-title { font-size: 1.35rem; font-weight: 900; margin-bottom: 32px; }
.about-section-title span { color: var(--accent); }
.about-cards-3 { display: grid; grid-template-columns: repeat(3,1fr); gap: 16px; }
@media(max-width:640px){ .about-cards-3 { grid-template-columns:1fr; } }
.about-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 24px 20px; }
.about-card-icon { font-size: 2rem; font-weight: 900; color: var(--accent); margin-bottom: 12px; line-height: 1; }
.about-card-title { font-size: .92rem; font-weight: 800; margin-bottom: 8px; }
.about-card p { font-size: .82rem; color: var(--muted); line-height: 1.6; }
.about-features { display: flex; flex-direction: column; gap: 28px; }
.about-feature { display: flex; gap: 24px; align-items: flex-start; }
.about-feature-num { font-size: 2.4rem; font-weight: 900; color: var(--accent); line-height: 1; min-width: 56px; }
.about-feature-title { font-size: 1rem; font-weight: 800; margin-bottom: 6px; }
.about-feature p { font-size: .85rem; color: var(--muted); line-height: 1.65; }
.about-steps { display: grid; grid-template-columns: repeat(3,1fr); gap: 16px; }
@media(max-width:640px){ .about-steps { grid-template-columns:1fr; } }
.about-step { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 24px 20px; }
.about-step-n { font-size: 2rem; font-weight: 900; color: var(--accent); line-height: 1; margin-bottom: 10px; }
.about-step-title { font-size: .92rem; font-weight: 800; margin-bottom: 8px; }
.about-step p { font-size: .82rem; color: var(--muted); line-height: 1.6; }
.about-tier-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; max-width: 620px; margin: 0 auto; }
@media(max-width:540px){ .about-tier-grid { grid-template-columns:1fr; } }
.about-tier { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 28px 24px; position: relative; }
.about-tier.pro { border-color: var(--pro); background: rgba(155,89,182,.05); }
.about-tier-badge { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: var(--pro); color: #fff; font-size: .62rem; font-weight: 900; letter-spacing: .14em; padding: 3px 14px; border-radius: 20px; white-space: nowrap; }
.about-tier-name { font-size: .7rem; font-weight: 900; letter-spacing: .15em; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; }
.about-tier-name.pro-label { color: var(--pro); }
.about-tier-price { font-size: 2rem; font-weight: 900; margin-bottom: 20px; }
.about-tier-price small { font-size: .85rem; font-weight: 400; color: var(--muted); }
.about-tier-features { list-style: none; margin-bottom: 24px; display: flex; flex-direction: column; gap: 9px; }
.about-tier-features li { font-size: .82rem; color: var(--muted); padding-left: 18px; position: relative; line-height: 1.4; }
.about-tier-features li::before { content: "—"; position: absolute; left: 0; color: var(--accent); font-weight: 700; }
.about-tier.pro .about-tier-features li { color: var(--text); }
.about-cta-small { width: 100%; padding: 11px; background: transparent; color: var(--text); border: 1px solid var(--border); border-radius: 7px; font-size: .82rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; cursor: pointer; transition: all .15s; }
.about-cta-small:hover { border-color: var(--accent); color: var(--accent); }
.about-cta-pro { width: 100%; padding: 11px; background: linear-gradient(135deg,var(--pro),var(--pro-dark)); color: #fff; border: none; border-radius: 7px; font-size: .82rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; cursor: pointer; transition: opacity .15s; }
.about-cta-pro:hover { opacity: .85; }
.about-footer-inner { text-align: center; padding: 40px 0 0; border-top: 1px solid var(--border); }
.about-footer-brand { font-size: 1.4rem; font-weight: 900; letter-spacing: .1em; margin-bottom: 8px; }
.about-footer-brand span { color: var(--accent); }
.about-footer-inner p { font-size: .82rem; color: var(--muted); }

/* ===== PROMPT MASTER BOX ===== */
.prompt-master-box { background: rgba(233,69,96,.05); border: 1px solid rgba(233,69,96,.4); border-radius: 10px; padding: 16px 20px; margin-bottom: 24px; }
.prompt-master-label { font-size: .62rem; font-weight: 900; letter-spacing: .14em; text-transform: uppercase; color: var(--accent); margin-bottom: 8px; }
.prompt-master-text { font-family: 'Cascadia Code','Consolas',monospace; font-size: .82rem; color: #c3e88d; line-height: 1.55; overflow-wrap: break-word; word-break: break-word; min-height: 1.6em; }
.prompt-master-hint { font-size: .67rem; color: var(--muted); margin-top: 6px; }
.btn-copy-master { margin-top: 10px; padding: 7px 18px; background: var(--accent); color: #fff; border: none; border-radius: 6px; font-size: .75rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; cursor: pointer; transition: opacity .15s; }
.btn-copy-master:hover { opacity: .85; }
.btn-copy-master.copied { background: #27ae60; }

/* ===== SREF CARD (ristrutturata) ===== */
.sref-code-display { font-family: 'Cascadia Code','Consolas',monospace; font-size: .78rem; color: var(--muted); background: var(--card2); border: 1px solid var(--border); border-radius: 4px; padding: 5px 10px; margin-bottom: 8px; display: inline-block; }

/* ===== THINKING OVERLAY ===== */
.thinking-overlay { display: none; position: fixed; inset: 0; background: rgba(13,13,26,.92); z-index: 2000; align-items: center; justify-content: center; flex-direction: column; gap: 20px; }
.thinking-spinner { width: 44px; height: 44px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.thinking-msg { font-size: .9rem; color: var(--muted); font-style: italic; max-width: 360px; text-align: center; line-height: 1.5; min-height: 2.5em; transition: opacity .3s; }
.thinking-label { font-size: .65rem; font-weight: 900; letter-spacing: .18em; text-transform: uppercase; color: var(--accent); }

/* ===== MODAL PREMIUM ===== */
.modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,.78); z-index: 1000; align-items: center; justify-content: center; }
.modal-overlay.open { display: flex; }
.modal { background: var(--card); border: 1px solid var(--pro); border-radius: 16px; padding: 32px; max-width: 480px; width: 90%; }
.modal-title { font-size: 1.25rem; font-weight: 900; letter-spacing: .08em; color: var(--pro); margin-bottom: 4px; }
.modal-sub { font-size: .85rem; color: var(--muted); margin-bottom: 22px; }
.tier-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 24px; }
.tier-card { background: var(--card2); border: 1px solid var(--border); border-radius: 8px; padding: 14px; }
.tier-card.pro-card { border-color: var(--pro); }
.tier-name { font-size: .68rem; font-weight: 900; letter-spacing: .12em; text-transform: uppercase; margin-bottom: 10px; color: var(--muted); }
.tier-name.pro { color: var(--pro); }
.tier-feature { font-size: .8rem; color: var(--muted); padding: 2px 0; }
.tier-feature.on { color: var(--text); }
.tier-price { font-size: 1.5rem; font-weight: 900; color: var(--pro); margin-top: 10px; }
.tier-price small { font-size: .72rem; font-weight: 400; color: var(--muted); }
.code-section { margin-bottom: 16px; }
.code-section label { display: block; font-size: .7rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; }
.code-row { display: flex; gap: 8px; }
.code-input { flex: 1; padding: 10px 14px; background: var(--card2); color: var(--text); border: 1px solid var(--border); border-radius: 6px; font-size: .9rem; font-family: 'Cascadia Code','Consolas',monospace; }
.code-input:focus { outline: none; border-color: var(--pro); }
.btn-activate { padding: 10px 18px; background: var(--pro); color: #fff; border: none; border-radius: 6px; font-weight: 800; font-size: .85rem; cursor: pointer; white-space: nowrap; }
.btn-activate:hover { background: var(--pro-dark); }
.code-error { color: var(--accent); font-size: .78rem; margin-top: 6px; display: none; }
.btn-modal-close { width: 100%; padding: 10px; background: transparent; color: var(--muted); border: 1px solid var(--border); border-radius: 6px; cursor: pointer; font-size: .85rem; margin-top: 8px; }
.btn-modal-close:hover { color: var(--text); border-color: var(--muted); }
</style>
</head>
<body>

<!-- HEADER -->
<div class="header">
  <h1>CIANO<span>AI</span> SrefMindForge</h1>
  <p>Find the perfect Midjourney SREF &amp; write your prompt &mdash; 5000+ styles in the database</p>
  <div class="header-badges">
    <span class="badge-tier" id="tierBadge" onclick="openModal()">FREE &mdash; unlock PRO</span>
    <span class="roll-display" id="rollDisplay"></span>
    <button class="btn-reset-roll" onclick="resetRolls()" title="Reset daily search counter">RESET</button>
  </div>
</div>

<!-- TAB NAV -->
<nav class="app-nav">
  <button class="nav-tab active" id="nav-app" onclick="showTab('app')">THE APP</button>
  <button class="nav-tab" id="nav-about" onclick="showTab('about')">PRICING</button>
</nav>

<!-- TAB: APP -->
<div id="tab-app">

<!-- FILTRI -->
<div class="filter-section">
  <div class="filter-grid">
    <div class="filter-group">
      <label>Visual Style</label>
      <select id="sel-style" onchange="previewProcessedPrompt()">
        <option value="any">&#8212; Any &#8212;</option>
        <option value="fantasy">Fantasy</option>
        <option value="cyberpunk">Cyberpunk</option>
        <option value="sci_fi">Sci-Fi</option>
        <option value="gothic">Gothic</option>
        <option value="horror">Horror</option>
        <option value="anime_manga">Anime / Manga</option>
        <option value="watercolor">Watercolor</option>
        <option value="ink_sketch">Ink / Sketch</option>
        <option value="photorealism">Photorealism</option>
        <option value="illustration">Illustration</option>
        <option value="abstract">Abstract</option>
        <option value="minimalist">Minimalist</option>
        <option value="geometric">Geometric</option>
        <option value="3d_render">3D / Render</option>
        <option value="vintage_retro">Vintage / Retro</option>
        <option value="nature">Nature</option>
        <option value="urban">Urban</option>
        <option value="painting">Painting</option>
        <option value="surreal">Surreal</option>
        <option value="pastel_soft">Pastel / Soft</option>
        <option value="vibrant_pop">Vibrant / Pop</option>
        <option value="noir">Noir</option>
        <option value="steampunk">Steampunk</option>
      </select>
    </div>
    <div class="filter-group">
      <label>Subject</label>
      <select id="sel-subject" onchange="previewProcessedPrompt()">
        <option value="any">&#8212; Any &#8212;</option>
        <option value="portrait">Portrait</option>
        <option value="landscape">Landscape</option>
        <option value="creature">Creature</option>
        <option value="character">Character</option>
        <option value="architecture">Architecture</option>
        <option value="nature">Nature</option>
        <option value="space">Space</option>
        <option value="urban">Urban</option>
        <option value="mythology">Mythology</option>
        <option value="fashion">Fashion</option>
        <option value="abstract_concept">Abstract concept</option>
        <option value="interior">Interior</option>
        <option value="still_life">Still life</option>
      </select>
    </div>
    <div class="filter-group">
      <label>Mood</label>
      <select id="sel-mood" onchange="previewProcessedPrompt()">
        <option value="any">&#8212; Any &#8212;</option>
        <option value="dark">Dark</option>
        <option value="ethereal">Ethereal</option>
        <option value="epic">Epic</option>
        <option value="serene">Serene</option>
        <option value="whimsical">Whimsical</option>
        <option value="melancholic">Melancholic</option>
        <option value="mysterious">Mysterious</option>
        <option value="futuristic">Futuristic</option>
        <option value="romantic">Romantic</option>
        <option value="chaotic">Chaotic</option>
        <option value="dramatic">Dramatic</option>
        <option value="elegant">Elegant</option>
      </select>
    </div>
    <div class="filter-group">
      <label>Color Palette</label>
      <select id="sel-palette" onchange="previewProcessedPrompt()">
        <option value="any">&#8212; Any &#8212;</option>
        <option value="pastel">Pastel</option>
        <option value="neon">Neon</option>
        <option value="monochrome">Monochrome</option>
        <option value="sepia">Sepia</option>
        <option value="vibrant">Vibrant</option>
        <option value="muted">Muted</option>
        <option value="golden">Golden</option>
        <option value="dark">Dark</option>
        <option value="cold_blues">Cold blues</option>
        <option value="earth_tones">Earth tones</option>
        <option value="purple_violet">Purple / Violet</option>
        <option value="warm_fire">Warm / Fire</option>
      </select>
    </div>
  </div>

  <!-- Idea (optional) -->
  <div class="idea-section">
    <label>Your prompt idea <span style="color:var(--accent)">*</span></label>
    <input type="text" id="userIdea" class="idea-input"
           placeholder="e.g.: an elven warrior in the fog at sunset... (any language)"
           oninput="previewProcessedPrompt()">
    <div class="idea-hint">Required. Write in any language &mdash; SrefMindForge will handle everything in English for you.</div>
    <div class="idea-error" id="ideaError" style="display:none;color:var(--accent);font-size:.75rem;margin-top:5px;font-weight:700;">
      Please enter your prompt idea before searching.
    </div>
  </div>

  <button class="btn-search" id="btnSearch" onclick="cercaSref()">PROMPT + SREF &#x1F680;</button>
  <button class="btn-new-search" id="btnInlineReset" style="display:none;width:100%;margin-top:0" onclick="nuovaRicerca()">NEW SEARCH</button>
</div>

<!-- RISULTATI -->
<div class="results-section" id="results">
  <div id="results-inner"></div>
</div>

</div><!-- /tab-app -->

<!-- TAB: ABOUT (landing page) -->
<div id="tab-about" style="display:none">
  <div class="about-hero">
    <div class="about-hero-tag">CIANOAI presents</div>
    <h2 class="about-hero-h">Stop guessing.<br><span>Start creating.</span></h2>
    <p class="about-hero-sub">The only Midjourney tool that finds your perfect SREF style code <em>and</em> writes your prompt &mdash; in any language, following pro best practices.</p>
    <button class="about-cta" onclick="showTab('app')">TRY IT FREE &rarr;</button>
  </div>

  <div class="about-section">
    <div class="about-section-title">The problem with Midjourney style research</div>
    <div class="about-cards-3">
      <div class="about-card">
        <div class="about-card-icon">?</div>
        <div class="about-card-title">5,000+ SREF codes</div>
        <p>Thousands of style reference codes exist. Finding the right one by trial and error wastes hours of your time.</p>
      </div>
      <div class="about-card">
        <div class="about-card-icon">EN</div>
        <div class="about-card-title">English-only prompts</div>
        <p>Midjourney expects precise, structured English prompts. Translating and optimizing your idea is an art in itself.</p>
      </div>
      <div class="about-card">
        <div class="about-card-icon">&ne;</div>
        <div class="about-card-title">Style inconsistency</div>
        <p>Without a system, your project images look different every time. No visual coherence, no brand identity.</p>
      </div>
    </div>
  </div>

  <div class="about-section">
    <div class="about-section-title"><span>SrefMindForge</span> solves all three</div>
    <div class="about-features">
      <div class="about-feature">
        <div class="about-feature-num">01</div>
        <div>
          <div class="about-feature-title">SREF Intelligence</div>
          <p>Our scoring engine analyzes 5,000+ SREF codes across style, mood, subject and palette &mdash; returning only the ones that actually match your creative vision.</p>
        </div>
      </div>
      <div class="about-feature">
        <div class="about-feature-num">02</div>
        <div>
          <div class="about-feature-title">Prompt Engine</div>
          <p>Type your idea in any language. SrefMindForge handles the translation and restructures it following Midjourney best practices &mdash; automatically. No prompt engineering knowledge required.</p>
        </div>
      </div>
      <div class="about-feature">
        <div class="about-feature-num">03</div>
        <div>
          <div class="about-feature-title">Style Coherence</div>
          <p>Geo-compatibility analysis ensures your mix suggestions only pair visually consistent SREF families. Your project stays coherent across every single generation.</p>
        </div>
      </div>
    </div>
  </div>

  <div class="about-section">
    <div class="about-section-title">How it works &mdash; 3 steps</div>
    <div class="about-steps">
      <div class="about-step">
        <div class="about-step-n">1</div>
        <div class="about-step-title">Choose your filters</div>
        <p>Select Style, Subject, Mood and Palette to define your creative direction.</p>
      </div>
      <div class="about-step">
        <div class="about-step-n">2</div>
        <div class="about-step-title">Describe your idea</div>
        <p>Write your concept in any language. SrefMindForge translates and optimizes it for Midjourney automatically.</p>
      </div>
      <div class="about-step">
        <div class="about-step-n">3</div>
        <div class="about-step-title">Copy &amp; generate</div>
        <p>Get ready-to-use Midjourney prompts with SREF codes attached. Copy, paste, generate.</p>
      </div>
    </div>
  </div>

  <div class="about-section">
    <div class="about-section-title">Simple, honest pricing</div>
    <div class="about-tier-grid">
      <div class="about-tier">
        <div class="about-tier-name">FREE</div>
        <div class="about-tier-price">&euro;0 <small>forever</small></div>
        <ul class="about-tier-features">
          <li>3 SREF results per search</li>
          <li>2 Mix suggestions</li>
          <li>3 searches per day</li>
          <li>Write in any language, we do the rest</li>
          <li>Midjourney best practices</li>
        </ul>
        <button class="about-cta-small" onclick="showTab('app')">START FREE</button>
      </div>
      <div class="about-tier pro">
        <div class="about-tier-badge">BEST VALUE</div>
        <div class="about-tier-name pro-label">PRO</div>
        <div class="about-tier-price">&euro;4,99 <small>/month</small></div>
        <ul class="about-tier-features">
          <li>10 SREF results per search</li>
          <li>5 Mix suggestions</li>
          <li>10 searches per day</li>
          <li>Reasoning behind every suggestion</li>
          <li>PDF session download</li>
          <li>Geo-coherence guarantee</li>
        </ul>
        <button class="about-cta-pro" onclick="showTab('app');setTimeout(openModal,100)">ACTIVATE PRO</button>
      </div>
    </div>
  </div>

  <div class="about-footer-inner">
    <div class="about-footer-brand">CIANO<span>AI</span></div>
    <p>Building AI-powered creative tools for visual artists and designers.</p>
  </div>
</div><!-- /tab-about -->

<!-- THINKING OVERLAY -->
<div class="thinking-overlay" id="thinkingOverlay">
  <div class="thinking-label">SrefMindForge is thinking...</div>
  <div class="thinking-spinner"></div>
  <div class="thinking-msg" id="thinkingMsg">Consulting the style oracle...</div>
</div>

<!-- MODAL PREMIUM -->
<div class="modal-overlay" id="premModal" onclick="handleModalClick(event)">
  <div class="modal" id="premModalContent">
    <div class="modal-title">SrefMindForge PRO</div>
    <div class="modal-sub">Unlock the full potential of the SREF database</div>
    <div class="tier-grid">
      <div class="tier-card">
        <div class="tier-name">FREE</div>
        <div class="tier-feature on">3 SREF puri</div>
        <div class="tier-feature on">2 Mix consigliati</div>
        <div class="tier-feature on">3 searches / day</div>
        <div class="tier-feature">&#8212; Style details</div>
        <div class="tier-feature">&#8212; PDF Download</div>
      </div>
      <div class="tier-card pro-card">
        <div class="tier-name pro">PRO</div>
        <div class="tier-feature on">10 SREF puri</div>
        <div class="tier-feature on">5 Mix consigliati</div>
        <div class="tier-feature on">10 searches / day</div>
        <div class="tier-feature on">Style details &amp; reasoning</div>
        <div class="tier-feature on">PDF session download</div>
        <div class="tier-price">4,99&euro;<small>/mese</small></div>
      </div>
    </div>
    <div class="code-section">
      <label>Have an activation code?</label>
      <div class="code-row">
        <input type="text" id="codeInput" class="code-input" placeholder="XXXX-XXXX-XXXX"
               onkeydown="if(event.key==='Enter') activateCode()">
        <button class="btn-activate" onclick="activateCode()">ACTIVATE</button>
      </div>
      <div class="code-error" id="codeError">Invalid code. Please try again.</div>
    </div>
    <button class="btn-modal-close" onclick="closeModal()">&times; Close</button>
  </div>
</div>

<script>
/* ===== DATABASE (protetto AES-256-GCM) ===== */
var d = null;
async function _decryptData(b64) {
    var raw = Uint8Array.from(atob(b64), function(c){ return c.charCodeAt(0); });
    var iv  = raw.slice(0, 12);
    var tag = raw.slice(12, 28);
    var ct  = raw.slice(28);
    var kh = await crypto.subtle.digest('SHA-256',
        new TextEncoder().encode("CIANOAI-SrefMindForge-2026-AES256"));
    var ck = await crypto.subtle.importKey('raw', kh, {name:'AES-GCM'}, false, ['decrypt']);
    var ctT = new Uint8Array(ct.length + tag.length);
    ctT.set(ct); ctT.set(tag, ct.length);
    var dec = await crypto.subtle.decrypt({name:'AES-GCM', iv:iv, tagLength:128}, ck, ctT);
    return JSON.parse(new TextDecoder().decode(dec));
}
(async function() {
    d = await _decryptData("###DATA###");
    for (var i = d.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var t = d[i]; d[i] = d[j]; d[j] = t;
    }
    window.__sc = d;
    console.log("\u2713 database ready: " + d.length);
})();

/* ===== CONFIG FREEMIUM ===== */
const _F = { puri: 3, mix: 2 };
const _P = { puri: 10, mix: 5 };

/* Scadenza batch codici attivazione */
var _EXP = new Date("2027-02-22T23:59:59");

/* ===== CODICI PREMIUM (base64) ===== */
const _VC = ###CODES###;

/* ===== GEO ===== */
const GEO_LABELS = {
  "soft-wash":       "Soft Wash",
  "organic-curves":  "Organic Curves",
  "flat-color":      "Flat Color",
  "line-based":      "Line Based",
  "continuous-tone": "Continuous Tone",
  "geometric-hard":  "Geometric Hard",
  "volumetric-hard": "Volumetric Hard",
  "organic-dark":    "Organic Dark",
  "surreal-open":    "Surreal Open",
  "unknown":         "Versatile"
};

const GEO_COMPAT = {
  "soft-wash":       ["soft-wash","organic-curves","flat-color","surreal-open"],
  "organic-curves":  ["organic-curves","soft-wash","flat-color","surreal-open","organic-dark"],
  "flat-color":      ["flat-color","soft-wash","organic-curves","line-based"],
  "line-based":      ["line-based","flat-color","continuous-tone","organic-dark"],
  "continuous-tone": ["continuous-tone","line-based","organic-curves","organic-dark"],
  "geometric-hard":  ["geometric-hard","line-based","volumetric-hard"],
  "volumetric-hard": ["volumetric-hard","geometric-hard","continuous-tone"],
  "organic-dark":    ["organic-dark","organic-curves","continuous-tone","surreal-open","line-based"],
  "surreal-open":    ["surreal-open","soft-wash","organic-curves","organic-dark","flat-color"],
  "unknown":         ["soft-wash","organic-curves","flat-color","line-based","continuous-tone",
                      "geometric-hard","volumetric-hard","organic-dark","surreal-open","unknown"]
};

/* ===== PREMIUM ===== */
function isPro() {
  return localStorage.getItem("_sc_p") === "1" && new Date() < _EXP;
}

function tryActivate(code) {
  try {
    if (new Date() >= _EXP) {
      document.getElementById("codeError").textContent = "Code expired. Contact CIANOAI for renewal.";
      return false;
    }
    var enc = btoa(code.trim().toLowerCase());
    if (_VC.indexOf(enc) !== -1) {
      localStorage.setItem("_sc_p","1");
      localStorage.removeItem("_sc_rd"); /* reset contatore: PRO parte da 0 */
      localStorage.removeItem("_sc_rc");
      updateRollDisplay();
      return true;
    }
  } catch(e) {}
  return false;
}

function updateBadge() {
  var el = document.getElementById("tierBadge");
  if (isPro()) {
    el.textContent = "SrefMindForge PRO active";
    el.className = "badge-tier badge-tier-pro";
  } else {
    el.innerHTML = "FREE &mdash; click to unlock PRO";
    el.className = "badge-tier badge-tier-free";
  }
  updateRollDisplay();
}

function openModal() {
  document.getElementById("premModal").classList.add("open");
  document.getElementById("codeInput").value = "";
  document.getElementById("codeError").style.display = "none";
}
function closeModal() { document.getElementById("premModal").classList.remove("open"); }
function handleModalClick(e) { if (e.target.id === "premModal") closeModal(); }

function activateCode() {
  const code = document.getElementById("codeInput").value;
  if (tryActivate(code)) {
    closeModal();
    updateBadge();
    if (document.getElementById("results").classList.contains("visible")) cercaSref();
  } else {
    document.getElementById("codeError").style.display = "block";
  }
}

/* ===== TAB NAVIGATION ===== */
function showTab(name) {
  document.getElementById("tab-app").style.display   = name === "app"   ? "block" : "none";
  document.getElementById("tab-about").style.display = name === "about" ? "block" : "none";
  document.getElementById("nav-app").classList.toggle("active",   name === "app");
  document.getElementById("nav-about").classList.toggle("active", name === "about");
}

/* ===== NUOVA RICERCA (reset risultati) ===== */
function nuovaRicerca() {
  document.getElementById("results").classList.remove("visible");
  document.getElementById("results-inner").innerHTML = "";
  var ideaEl = document.getElementById("userIdea");
  if (ideaEl) ideaEl.value = "";
  /* Ripristina pulsante di ricerca */
  document.getElementById("btnSearch").style.display = "block";
  document.getElementById("btnInlineReset").style.display = "none";
  document.querySelector(".filter-section").scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ===== ROLL (limite ricerche giornaliero) ===== */
function _todayStr() { return new Date().toISOString().slice(0, 10); }

function getRollsToday() {
  var today = _todayStr();
  if (localStorage.getItem("_sc_rd") !== today) {
    localStorage.setItem("_sc_rd", today);
    localStorage.setItem("_sc_rc", "0");
  }
  return parseInt(localStorage.getItem("_sc_rc") || "0", 10);
}

function getMaxRolls() { return isPro() ? 10 : 3; }
function canRoll()     { return getRollsToday() < getMaxRolls(); }

function incrementRolls() {
  localStorage.setItem("_sc_rc", String(getRollsToday() + 1));
  updateRollDisplay();
}

function resetRolls() {
  localStorage.removeItem("_sc_rd");
  localStorage.removeItem("_sc_rc");
  updateRollDisplay();
}

function updateRollDisplay() {
  var el  = document.getElementById("rollDisplay");
  if (!el) return;
  var used = getRollsToday();
  var max  = getMaxRolls();
  var rem  = Math.max(0, max - used);
  el.textContent = rem + "/" + max + " searches left today";
  el.className = "roll-display" + (rem === 0 ? " roll-zero" : "");
}

/* ===== UTILITY ===== */
function escHtml(s) {
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;")
                  .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function geoBadgeHTML(geo) {
  const label = GEO_LABELS[geo] || "Versatile";
  const cls = "geo-" + (geo || "unknown");
  return '<span class="badge badge-geo ' + cls + '">' + label + '</span>';
}

/* ===== TRADUZIONE IT->EN + BEST PRACTICES MJ ===== */

/* Dizionario italiano -> inglese: articoli/preposizioni, soggetti, aggettivi, ambienti */
var _IT = {
  /* articoli e preposizioni (eliminati o sostituiti) */
  "vorrei":"","voglio":"","vogliamo":"","vorremmo":"",
  "crea":"","crei":"","create":"","disegna":"","dipingi":"","mostra":"","fai":"","fa":"",
  "il":"","la":"","i":"","le":"","lo":"","gli":"","l":"",
  "un":"a","una":"a","uno":"a",
  "di":"of","del":"of the","della":"of the","dello":"of the","dei":"of","delle":"of",
  "con":"with","senza":"without",
  "nel":"in the","nella":"in the","nello":"in the","nei":"in the","nelle":"in the",
  "sul":"on the","sulla":"on the","sui":"on the","sulle":"on the",
  "dal":"from the","dalla":"from the","dai":"from the","dalle":"from the",
  "al":"at the","alla":"at the","ai":"at the","alle":"at the",
  "per":"for","tra":"between","fra":"between","verso":"towards","fino":"until",
  "che":"that","come":"like","dove":"where","quando":"when","mentre":"while",
  "poi":"then","dopo":"after","prima":"before","anche":"also","solo":"only",
  "molto":"very","tanto":"so much","poco":"little","troppo":"too much",
  "ed":"and","e":"and","ma":"but","o":"or","se":"if",
  "questo":"this","questa":"this","questi":"these","queste":"these",
  "quello":"that","quella":"that","quelli":"those","quelle":"those",
  "suo":"his","sua":"her","loro":"their","mio":"my","mia":"my",
  "una volta":"old-fashioned","di una volta":"old-fashioned, vintage",
  "a volte":"sometimes","ogni tanto":"occasionally",
  /* ambienti e concetti mancanti */
  "mondo":"world","mondi":"worlds","terra":"earth","regno":"kingdom","regni":"kingdoms",
  "dominio":"dominion","egemonia":"hegemony","supremazia":"supremacy",
  "apocalisse":"apocalypse","apocalittico":"apocalyptic","apocalittica":"apocalyptic",
  "apocalittici":"apocalyptic","apocalittiche":"apocalyptic",
  "distruzione":"destruction","annientamento":"annihilation","caos":"chaos",
  "guerra":"war","battaglia":"battle","conquista":"conquest","potere":"power",
  "supremo":"supreme","suprema":"supreme","oscuro":"dark","oscura":"dark",
  "tenebre":"darkness","ombra":"shadow","morte":"death","sangue":"blood",
  "cenere":"ash","inferno":"inferno","paradiso":"paradise","abisso":"abyss",
  "acqua":"water","aria":"air","elemento":"element","magia":"magic","potenza":"power",
  "bastone":"staff","bastoni":"staffs","bacchetta":"wand","bacchette":"wands",
  "verga":"rod","canna":"rod","lama":"blade","arma":"weapon","armi":"weapons",
  "radice":"root","radici":"roots","ali":"wings","fiamma":"flame","fiamme":"flames",
  "vortice":"vortex","portale":"portal","cristallo":"crystal","frammento":"fragment",
  "creatura":"creature","creature":"creatures","anima":"soul","spirito":"spirit",
  /* soggetti - persone */
  "persona":"person","uomo":"man","donna":"woman","ragazzo":"boy","ragazza":"girl",
  "bambino":"child","bambina":"child","anziano":"elderly man","anziana":"elderly woman",
  "nonna":"grandmother","nonno":"grandfather","madre":"mother","padre":"father",
  "guerriero":"warrior","guerriera":"warrior woman","cavaliere":"knight","cavaliera":"knight",
  "mago":"wizard","maga":"sorceress","strega":"witch","stregone":"sorcerer",
  "elfo":"elf","elfa":"elf","elfico":"elven","elfica":"elven","elfici":"elven","elfiche":"elven","nano":"dwarf","gnomo":"gnome",
  "re":"king","regina":"queen","principe":"prince","principessa":"princess",
  "samurai":"samurai","ninja":"ninja","pirata":"pirate",
  "assassino":"assassin","cacciatore":"hunter","esploratrice":"explorer","esploratore":"explorer",
  "angelo":"angel","demone":"demon","diavolo":"devil",
  /* soggetti - creature */
  "drago":"dragon","mostro":"monster","bestia":"beast","lupo":"wolf","gatto":"cat",
  "aquila":"eagle","serpente":"serpent","fantasma":"ghost","zombie":"zombie",
  "robot":"robot","cyborg":"cyborg","alieno":"alien",
  /* soggetti - luoghi e ambienti */
  "cucina":"kitchen","camera":"room","stanza":"room","bagno":"bathroom","salotto":"living room",
  "castello":"castle","dungeon":"dungeon","prigione":"prison","torre":"tower","tempio":"temple",
  "foresta":"forest","bosco":"forest","giungla":"jungle","deserto":"desert",
  "montagna":"mountain","collina":"hill","valle":"valley","grotta":"cave","abisso":"abyss",
  "mare":"sea","oceano":"ocean","lago":"lake","fiume":"river","cascata":"waterfall",
  "citta":"city","villaggio":"village","mercato":"market","porto":"harbor","vicolo":"alley",
  "cielo":"sky","nuvole":"clouds","stelle":"stars","galassia":"galaxy","spazio":"space",
  "rovina":"ruin","rovine":"ruins","biblioteca":"library","laboratorio":"laboratory",
  "giardino":"garden","parco":"park","cimitero":"graveyard","chiesa":"church",
  /* oggetti */
  "spada":"sword","scudo":"shield","arco":"bow","freccia":"arrow","lancia":"spear",
  "armatura":"armor","mantello":"cloak","cappello":"hat","maschera":"mask",
  "libro":"book","mappa":"map","cristallo":"crystal","gemma":"gem","corona":"crown",
  "lanterna":"lantern","candela":"candle","fiamma":"flame","fuoco":"fire",
  "pozione":"potion","calice":"chalice","specchio":"mirror","portale":"portal",
  /* aggettivi di carattere/stato */
  "strano":"mysterious","strana":"mysterious","bizzarro":"bizarre","bizzarra":"bizarre",
  "inquietante":"unsettling","sinistro":"sinister","sinistra":"sinister",
  "magnifico":"magnificent","magnifica":"magnificent","epico":"epic","epica":"epic",
  "antico":"ancient","antica":"ancient","vecchio":"old","vecchia":"old",
  "nuovo":"new","nuova":"new","moderno":"modern","moderna":"modern","futuristico":"futuristic",
  "misterioso":"mysterious","misteriosa":"mysterious","segreto":"secret","segreta":"secret",
  "potente":"powerful","forte":"strong","fragile":"fragile","delicato":"delicate",
  "elegante":"elegant","raffinato":"refined","grezzo":"rough","rustico":"rustic",
  "dark":"dark","oscuro":"dark","oscura":"dark","luminoso":"luminous","luminosa":"luminous",
  "magico":"magical","magica":"magical","sacro":"sacred","sacra":"sacred","maledetto":"cursed",
  "solitario":"solitary","solitaria":"solitary","maestoso":"majestic","maestosa":"majestic",
  /* aggettivi fisici */
  "grande":"large","enorme":"enormous","enormi":"enormous","piccolo":"small","piccola":"small",
  "alto":"tall","alta":"tall","basso":"low","lunga":"long","lungo":"long","corto":"short",
  "pesante":"heavy","leggero":"light","sottile":"slender","robusto":"robust",
  "giovane":"young","anziano":"aged","antico":"ancient",
  /* colori */
  "rosso":"red","rossa":"red","blu":"blue","verde":"green","giallo":"yellow","arancione":"orange",
  "viola":"purple","rosa":"pink","nero":"black","nera":"black","bianco":"white","bianca":"white",
  "grigio":"grey","grigia":"grey","dorato":"golden","argentato":"silver","bronzo":"bronze",
  "cremisi":"crimson","scarlatto":"scarlet","indaco":"indigo","turchese":"teal",
  /* luce e atmosfera */
  "luce":"light","buio":"darkness","ombra":"shadow","ombre":"shadows",
  "tramonto":"sunset","alba":"dawn","mezzogiorno":"midday","notte":"night",
  "nebbia":"fog","nebbie":"foggy","fumo":"smoke","pioggia":"rain","neve":"snow",
  "tempesta":"storm","vento":"wind","caldo":"warm","freddo":"cold",
  "luminoso":"bright","fioco":"dim","intenso":"intense",
  /* stile e tecnica */
  "dipinto":"painting","disegno":"drawing","schizzo":"sketch","fotografia":"photography",
  "illustrazione":"illustration","scultura":"sculpture","incisione":"engraving",
  "acquerello":"watercolor","olio":"oil painting","pastello":"pastel",
  "digitale":"digital art","cinematografico":"cinematic","fotografico":"photographic",
  /* mood */
  "felice":"joyful","triste":"melancholic","arrabbiato":"angry","paura":"fearful",
  "tranquillo":"serene","agitato":"agitated","malinconico":"melancholic",
  "romantico":"romantic","eroico":"heroic","misterioso":"mysterious",
  /* occhi, corpo */
  "occhi":"eyes","capelli":"hair","mani":"hands","ali":"wings","coda":"tail","corna":"horns",
  "sorriso":"smile","sguardo":"gaze","viso":"face","volto":"face","corpo":"body"
};

/* Frasi da tradurre PRIMA delle singole parole (ordine importante) */
var _IT_PHRASES = [
  ["di una volta","old-fashioned, vintage style"],
  ["una volta","old-fashioned"],
  ["con gli occhi","with"],
  ["al tramonto","at sunset, golden hour"],
  ["nel buio","in the darkness"],
  ["alla luce","in the light of"],
  ["in mezzo alla","surrounded by"],
  ["in mezzo al","surrounded by"],
  ["nel mezzo di","in the midst of"],
  ["punto di vista","perspective"],
  ["primo piano","close-up"],
  ["campo lungo","wide shot"],
  ["luce del sole","sunlight"],
  ["luce della luna","moonlight"],
  ["luce delle stelle","starlight"],
  ["profondita di campo","depth of field"],
  ["resa cinematografica","cinematic render"],
  ["prospettiva cinematografica","cinematic perspective"],
  ["stile realistico","realistic style"],
  ["molto dettagliato","highly detailed"],
  ["ultra dettagliato","ultra detailed"]
];

/* ===== PROMPT ENGINE v2 — struttura ricca per prompt Midjourney efficaci ===== */

function _pickRand(arr) {
  if (!arr || !arr.length) return "";
  return arr[Math.floor(Math.random() * arr.length)];
}

/* Descrittori visivi specifici per stile (3-4 tratti che catturano l'essenza) */
var _VISUAL_STYLE = {
  "fantasy":       ["flowing enchanted robes, arcane runes, ethereal aura, mystical glow",
                    "ornate medieval armor, glowing sigils, ancient carved script, divine radiance",
                    "swirling arcane patterns, enchanted crystals, runic carvings, golden filigree",
                    "legendary weaponry, celestial markings, spectral wisps, mythical textures"],
  "cyberpunk":     ["chrome plating, neon circuit traces, glitch data overlays, holographic HUD",
                    "synthetic skin patches, data port implants, neon-lit visor, circuit-woven jacket",
                    "bioluminescent tech veins, fractured chrome, flickering neon tattoos, digital noise",
                    "augmented optics, servo-joints, heat vents, pulsing LED array"],
  "sci_fi":        ["sleek titanium hull panels, energy conduits, quantum interface display, stellar insignia",
                    "exo-armor plating, plasma conduits, zero-g stance, orbital command badge",
                    "hard-light energy barriers, anti-grav boosters, deep-space insignia, photon trail"],
  "gothic":        ["flowing dark mantle, ornate bone engravings, sharp wrought iron accents, shadowed velvet",
                    "tattered velvet robes, black iron crown, candlewax drips, crumbling stone detail",
                    "lace-edged burial shroud, silver skull motifs, gothic arches, ivy-strangled stonework"],
  "horror":        ["decayed flesh patches, hollow void eyes, torn burial cloth, visceral organic textures",
                    "cracked pale skin, inked ritual marks, rusted iron chains, dripping shadows",
                    "contorted limbs, necrotic cold glow, bone-carved sigils, rotting organic detail"],
  "anime_manga":   ["expressive shonen eyes, dynamic action motion lines, vibrant color flats, manga-bold outline",
                    "cel-shaded highlights, dramatic hair flow, sakura petal scatter, speed-blur streaks",
                    "chibi-accented features, glowing power aura, signature weapon, clean line weight"],
  "watercolor":    ["translucent pigment washes, soft bleeding edges, wet-on-wet color blooms, paper texture grain",
                    "loose gestural marks, luminous white paper reserves, flowing color pools, delicate dry brush",
                    "diffuse halo effects, pigment granulation, soft lost edges, spontaneous transparent layering"],
  "ink_sketch":    ["expressive brush strokes, cross-hatch shadow zones, bold ink silhouette, sumi-e restraint",
                    "feathered quill linework, scraperboard texture, stippled shadow zones, sepia ink wash",
                    "gestural contour lines, dense hatching, spontaneous blot marks, raw organic line energy"],
  "photorealism":  ["subsurface skin scatter, pore-level texture, micro-detail sharpness, studio HDRI light",
                    "lens bokeh depth-of-field, chromatic aberration fringe, dust-particle ambient, hyper-sharp focus",
                    "volumetric light rays, photographic color grading, ISO noise grain, raw sensor fidelity"],
  "illustration":  ["clean vector linework, flat color zones, bold graphic silhouette, storybook palette",
                    "editorial-quality inking, deliberate color story, spot-color accents, composed layout",
                    "narrative character pose, clear visual hierarchy, textured fill, punchy limited palette"],
  "abstract":      ["gestural color fields, dynamic fracture planes, impasto texture bursts, raw expressive mark",
                    "layered semi-transparent glazes, dripped pigment trails, scraped impasto texture",
                    "deconstructed form fragments, energetic brushwork, accidental beauty, pure color tension"],
  "minimalist":    ["single clean line weight, purposeful negative space, minimal two-tone palette, refined form",
                    "sparse composition, micro-detail accent, clean white field, deliberate restraint",
                    "mono-line icon elegance, stripped-back form, essential shape geometry only"],
  "geometric":     ["tessellated polygon planes, hard-edge vector precision, isometric structure, clean node lines",
                    "faceted low-poly planes, angular segment grid, sharp corner geometry, graphic boldness",
                    "interlocking shape logic, strict symmetry, flat-color polygon color fields"],
  "3d_render":     ["volumetric ambient occlusion, PBR material sheen, sub-surface scatter depth, HDR light probe",
                    "physically-based metal roughness, global illumination bounce, soft shadow contact, Octane lens",
                    "displacement map texture, ray-traced refraction, cinematic DOF blur, motion vector trail"],
  "vintage_retro": ["halftone dot grain, faded Kodachrome palette, letterpress ink bite, worn paper texture",
                    "chromolithograph color registration, film-stock grain, overprint two-color plate, aged foxing",
                    "70s earth-tone poster palette, riso-print texture, sun-bleached ink, old-press imprint"],
  "nature":        ["organic texture detail, golden-ratio composition, dew-drop micro-focus, diffused skylight",
                    "atmospheric perspective haze, wild botanical accuracy, shallow depth of field, morning mist veil",
                    "life-cycle narrative, natural color harmony, prime lens sharpness, habitat authenticity"],
  "urban":         ["concrete brutalist texture, street-level grit, neon reflection on wet asphalt, film grain",
                    "tagged surface decay, wire-shadow graphic, gritty city ambient, pollution haze",
                    "architectural compression, ambient crowd blur, raw ISO noise, overcast flat light"],
  "painting":      ["impasto loaded brushwork, alla prima wet-into-wet, museum canvas texture, glazed depth",
                    "old-master chiaroscuro, rich bitumen glaze, bristle stroke visibility, pigment body",
                    "gestural expressive marks, plein-air light capture, broken color technique, underpainting bleed"],
  "surreal":       ["impossible scale juxtaposition, dream-logic continuity break, hyper-detailed dreamscape, Magritte light",
                    "melting time references, anatomically impossible junction, gravity-defying levitation, lacquered finish",
                    "found-object symbolism, deep metaphysical shadow, forensic detail on absurd subject"],
  "pastel_soft":   ["blended chalk pastel softness, gossamer value range, powder-light color, smudged edge blur",
                    "cloud-like feathering, baby-soft diffusion, delicate tint layering, tender warm glow",
                    "sugar-spun highlight, cotton-light shadow, gentle contrast, sweet color harmony"],
  "vibrant_pop":   ["maximum chroma flat fill, Roy Lichtenstein bold outline, halftone dot grid, screaming contrast",
                    "CMYK primary punch, billboard graphic scale, high-key saturation, graphic pop boldness",
                    "poster-flat simplicity, neon sign energy, graphic symbol clarity, color-field impact"],
  "noir":          ["high-contrast chiaroscuro, rain-gloss reflection, venetian blind shadow stripe, single-source drama",
                    "deep shadow pool, silver-gelatin tonal range, smoke diffusion veil, hard-boiled graphic edge",
                    "expressionist shadow distortion, key-light cigarette haze, noir composition tension"],
  "steampunk":     ["ornate brass gear-work, Victorian riveted plating, mahogany copper inlay, sepia steam haze",
                    "clockwork mechanism detail, patinated bronze surface, boiler pressure gauge, antique leather texture",
                    "piston-driven armature, hand-wound spring coil, gaslight amber illumination, iron filigree work"],
  "any":           ["intricate surface detail, layered tonal depth, deliberate composition, considered color harmony",
                    "masterful rendering quality, balanced light-shadow ratio, professional art direction",
                    "rich visual complexity, precise value control, skilled mark-making, evocative atmosphere"]
};

/* Colori di sfondo evocativi per palette e mood */
var _BG_COLORS_MAP = {
  "pastel":       ["soft blush rose","misty lavender","powder sky blue","mint cream","peach mist","pale lilac"],
  "neon":         ["deep ultraviolet","midnight circuit black","electric void","neon abyss","pure black"],
  "monochrome":   ["obsidian black","charcoal slate","ash grey","deep charcoal","onyx","fog white"],
  "sepia":        ["aged parchment","warm amber","antique vellum","weathered ochre","sunscorched sand"],
  "vibrant":      ["rich crimson","electric cobalt","vivid emerald","royal purple","sunburst gold"],
  "muted":        ["dusty slate","dull sage","faded terracotta","muted teal","smoke grey"],
  "golden":       ["warm amber gold","burnished bronze","antique gold","sunset bronze","gilded ochre"],
  "dark":         ["midnight black","deep void","abyssal blue","obsidian","ink black","eclipse grey"],
  "cold_blues":   ["ice blue","arctic teal","deep cerulean","glacial steel","northern navy"],
  "earth_tones":  ["warm terracotta","volcanic ash","forest floor brown","rustic clay","sandstone warm"],
  "ethereal":     ["twilight violet","astral blue","dream mist grey","celestial lavender","aurora teal"],
  "epic":         ["stormy battleground grey","royal crimson","thunder black","iron cloud","deep ochre"],
  "serene":       ["soft morning sky","pale jade","cloud white","gentle seafoam","warm ivory"],
  "whimsical":    ["candy floss pink","fairy-tale lilac","cheerful mint","storybook azure","carnival peach"],
  "melancholic":  ["mourning grey","rainy slate","faded dusk violet","desaturated blue","overcast ivory"],
  "mysterious":   ["deep indigo","shadow teal","cryptic charcoal","secret forest green","eldritch purple"],
  "futuristic":   ["data-stream black","chrome white","grid blue","terminal green","quantum silver"],
  "romantic":     ["velvet rose","blush pink","candlelit cream","wine burgundy","soft mauve"],
  "chaotic":      ["storm-charged grey","fractured red","burning amber","volatile magenta","raw umber"],
  "dramatic":     ["stage-black velvet","theatrical crimson deep","cinematic iron grey","shadow tungsten","dark slate"],
  "elegant":      ["champagne ivory","warm platinum","dusty mauve silk","antique pearl","deep charcoal linen"],
  "purple_violet":["deep amethyst","twilight indigo","royal plum","violet dusk","dark orchid","cosmic violet"],
  "warm_fire":    ["volcanic crimson","ember orange-red","blaze scarlet","molten deep red","inferno amber"],
  "any":          ["deep charcoal","midnight black","rich indigo","obsidian","storm grey"]
};

/* Dichiarazione stile artistico nominato — la chiave che spinge MJ nella direzione giusta */
var _ART_STYLE_DECL = {
  "fantasy":       ["high fantasy illustration style with epic composition, rich textures, and mythological grandeur",
                    "illuminated manuscript style with gilded filigree, sacred geometry, and hand-lettered devotion",
                    "gothic fantasy style with ornate dark linework, shadowed depth, and medieval gravitas",
                    "watercolor fantasy style with luminous washes, soft lost edges, and ethereal translucency"],
  "cyberpunk":     ["neon noir digital rendering style with harsh contrast, glitch artifacts, and data-stream overlays",
                    "cyberpunk concept art style with chrome highlight bloom, rain-slicked refraction, and HUD overlays",
                    "neo-noir illustration style with deep shadow pools, neon bloom halo, and urban geometry"],
  "sci_fi":        ["hard science fiction concept art style with technical accuracy, plausible engineering, and stark beauty",
                    "space opera illustration style with dramatic cosmic scale, zero-g elegance, and crystalline detail"],
  "gothic":        ["gothic novel cover style with intricate dark engraving, sorcerous character, and eldritch atmosphere",
                    "Victorian etching style with cross-hatched shadow zones, ornate border, and ink-bitten surface",
                    "dark romanticism style with brooding chiaroscuro, symbolic depth, and gothic grandeur"],
  "horror":        ["underground horror comic style with exaggerated grotesque anatomy, visceral inking, and raw terror",
                    "rotoscope horror style with sharp silhouette edges, deep shadow zones, and stark contrast",
                    "pulp horror illustration style with maximalist shadow, nerve-shredding atmosphere, and ominous glow"],
  "anime_manga":   ["shonen manga illustration style with bold linework, kinetic energy, and iconic character design",
                    "anime key-art style with vibrant cel-shading, dramatic perspective, and collector-edition quality",
                    "manga panel style with screentone shading, expressive line weight, and narrative composition"],
  "watercolor":    ["traditional watercolor illustration style with luminous transparency, spontaneous bloom, and organic texture",
                    "botanical watercolor style with scientific precision, delicate layering, and nature-print elegance",
                    "loose gestural watercolor style with expressive wet-on-wet marks, white paper luminosity, and accidental beauty"],
  "ink_sketch":    ["sumi-e ink painting style with gestural brushwork, deliberate emptiness, and Zen economy of mark",
                    "etching style with fine cross-hatched shadow, bitten plate texture, and Old-Master depth",
                    "brush ink illustration style with spontaneous character, bold silhouette, and calligraphic line energy"],
  "photorealism":  ["hyperrealistic digital painting style with pore-level accuracy, studio lighting fidelity, and photographic depth",
                    "trompe-l'oeil photorealism style with deceptive surface illusion, crisp focus, and material authenticity"],
  "illustration":  ["editorial illustration style with narrative clarity, graphic boldness, and considered color story",
                    "storybook illustration style with warmth, character, and timeless picture-book composition",
                    "concept art illustration style with production-ready quality, environment storytelling, and visual development depth"],
  "abstract":      ["abstract expressionism style with raw gestural energy, pure pigment emotion, and spontaneous mark",
                    "lyrical abstraction style with refined color field, delicate surface tension, and meditative presence",
                    "neo-expressionist painting style with loaded impasto, fractured plane, and psychological intensity"],
  "minimalist":    ["minimalist graphic design style with radical reduction, elegant proportion, and Bauhaus discipline",
                    "Swiss international style with grid logic, sans-serif clarity, and purposeful restraint",
                    "reductive illustration style with single stroke economy, pure silhouette, and conceptual precision"],
  "geometric":     ["hard-edge geometric abstraction style with razor-clean vector edges, mathematical beauty, and color theory mastery",
                    "constructivist geometric style with primary palette, angular dynamism, and graphic energy",
                    "isometric design style with clean axonometric projection, flat-color logic, and architectural precision"],
  "3d_render":     ["Octane render CGI style with photorealistic global illumination, PBR material authenticity, and cinematic lens",
                    "Cinema4D render style with art-directed lighting, volumetric atmosphere, and commercial-grade finish",
                    "Blender Cycles style with ray-traced shadow depth, procedural texture richness, and real-time quality"],
  "vintage_retro": ["vintage travel poster style with flat color planes, hand-lettered elegance, and golden-age nostalgia",
                    "retro halftone offset print style with Benday dot texture, aged ink, and limited color register",
                    "1970s psychedelic poster style with warm earth palette, Art Nouveau curve, and counterculture spirit"],
  "nature":        ["natural history illustration style with Audubon precision, scientific botanical accuracy, and field-guide beauty",
                    "landscape photography style with Ansel Adams tonal range, foreground-to-sky depth, and natural grandeur",
                    "wildlife documentary still style with shallow DOF isolation, golden-hour warmth, and life-magazine quality"],
  "urban":         ["street photography documentary style with raw urban authenticity, available light, and decisive moment",
                    "brutalist architectural photography style with concrete poetry, shadow graphic, and structural honesty",
                    "urban reportage style with film grain texture, compressed telephoto, and social documentary weight"],
  "painting":      ["classical oil painting style with old-master glazing technique, rich bitumen depth, and museum-wall presence",
                    "plein-air impressionist painting style with broken color, gestural light capture, and outdoor immediacy",
                    "contemporary figurative painting style with loaded impasto, raw canvas showing, and expressive urgency"],
  "surreal":       ["metaphysical surrealist painting style with Magritte light, impossible calm, and symbol-laden space",
                    "Salvador Dalí dream-logic style with hyper-detailed dreamscape, melting form, and subconscious narrative",
                    "magic realist illustration style with everyday miracle, quiet revelation, and tender impossible detail"],
  "pastel_soft":   ["soft pastel chalk illustration style with powder-light color, smudged gentle edge, and intimate warmth",
                    "dreamy digital pastel style with feathered value range, cotton-light glow, and sugar-spun highlight",
                    "children's book pastel style with approachable warmth, gentle contrast, and tender storytelling color"],
  "vibrant_pop":   ["pop art illustration style with bold primary fill, Roy Lichtenstein outline, and halftone dot grid",
                    "graphic novel pop style with maximum chroma impact, billboard scale graphic, and saturated drama",
                    "street art pop style with spray-can energy, stencil precision, and public-space visual punch"],
  "noir":          ["film noir illustration style with venetian-blind shadow stripe, single-source drama, and silver-gelatin tonal range",
                    "hardboiled detective graphic style with deep shadow pool, rain-gloss reflection, and chiaroscuro tension",
                    "neo-noir digital painting style with expressionist shadow distortion, smoke veil diffusion, and moral ambiguity"],
  "steampunk":     ["steampunk concept art style with Victorian engineering obsession, polished brass beauty, and gaslight amber mood",
                    "steampunk illustration style with hand-inked gear detail, aged leather texture, and clockwork precision",
                    "steam-age fantasy style with riveted iron plate, mahogany panel inlay, and industrial romanticism"],
  "any":           ["digital art illustration style with masterful composition, deliberate lighting, and professional finish",
                    "concept art style with narrative depth, environmental storytelling, and art-direction quality",
                    "mixed-media illustration style with rich textural contrast, confident mark-making, and visual intrigue"]
};

/* Tre props tematici per soggetto — "with X, Y, and Z" */
var _PROPS_MAP = {
  "portrait":          ["an ornate gilded mirror, scattered dried petals, and a half-melted candle",
                        "an ancient leather-bound tome, a quill pen of iridescent feathers, and an hourglass",
                        "a delicate porcelain teacup, pressed wildflowers, and a sealed wax letter"],
  "landscape":         ["a distant crumbling watchtower, a solitary cypress, and churning storm clouds",
                        "an ancient stone archway, a wildflower meadow, and a winding cobblestone path",
                        "a frozen waterfall, snow-dusted pine canopy, and a pale winter moon"],
  "creature":          ["scattered bleached bones, a glowing arcane seal, and spectral flame wisps",
                        "crumbling ancient ruins, overgrown twisted vines, and smoldering embers",
                        "ritual standing stones, a sacrificial ash circle, and hovering spirit orbs"],
  "character":         ["a battered leather satchel, rolled hand-drawn maps, and a concealed dagger",
                        "enchanted spell components, an arcane focus crystal, and floating rune fragments",
                        "an ancestral heirloom weapon, a clan-marked battle standard, and a war-scarred shield"],
  "architecture":      ["ivy-consumed buttress columns, gargoyle sentinels, and a rose window glow",
                        "crumbling obsidian spires, a sacred inscribed lintel, and moss-covered foundation stones",
                        "iron gates with heraldic crests, tower battlements, and banners in storm wind"],
  "nature":            ["a dew-jeweled spider web, a rusted iron lantern, and scattered autumn leaves",
                        "a moss-covered fallen log, a wild mushroom ring, and shafts of morning light",
                        "a rain-pool reflection, a budding cherry blossom branch, and a stone garden lantern"],
  "space":             ["a dying red giant star, fragments of a shattered moon, and a deep-space nebula bloom",
                        "a derelict space station skeleton, a rogue asteroid field, and a distant exoplanet",
                        "a black hole accretion disk, a comet tail debris field, and a lone wandering satellite"],
  "urban":             ["rain-slicked neon signage, a rusted fire escape ladder, and chalk-tag graffiti walls",
                        "an overflowing dumpster, a flickering streetlamp, and a puddle reflecting city lights",
                        "food cart steam plume, wire-strung bare bulbs, and worn cobblestone street"],
  "mythology":         ["an ancient ritual altar, a carved deity idol, and smoldering sacred incense",
                        "a thunder-split sacred oak, a warrior's fallen shield, and divine lightning marks",
                        "a labyrinthine stone corridor, offerings of grain and wine, and a celestial constellation map"],
  "fashion":           ["draped silk fabric swaths, scattered ornate jewelry, and a designer perfume bottle",
                        "hand-stitched couture detail, avant-garde accessories, and a runway editorial backdrop",
                        "an antique dressmaker form, fine lace trim, and a fashion sketch portfolio"],
  "abstract_concept":  ["intersecting light beams, shattered mirror fragments, and a spiraling golden ratio",
                        "an empty ornate frame, a single floating eye, and cascading abstract geometry",
                        "a frozen moment of impact, suspended liquid droplets, and an impossible geometric void"],
  "interior":          ["a threadbare Persian rug, stacked antique books, and a fireplace ember glow",
                        "dust-moted afternoon light, a worn velvet armchair, and scattered vintage photographs",
                        "an exposed brick alcove, hanging dried herb bundles, and a writing desk with ink stains"],
  "still_life":        ["a cracked porcelain vessel, scattered dried pomegranate seeds, and a single white feather",
                        "a weathered nautical compass, a folded sea chart, and a wax-sealed glass bottle",
                        "an antique pocket watch, a pressed botanical specimen, and an aged parchment scroll"],
  "fantasy":           ["ancient spell tomes, mystical crystal orbs, and enchanted scrolls",
                        "a rune-etched crystal staff, eldritch artifacts, and hovering spirit lights",
                        "arcane alchemical vials, rune-carved weapons, and a celestial orrery"],
  "cyberpunk":         ["a holographic data display, discarded neural interface cables, and glitching screens",
                        "a neon katana, augmented-reality contact lenses, and hacked security terminals",
                        "a cracked digital billboard, exposed fiber optic conduit, and surveillance drone debris"],
  "gothic":            ["a cracked wax seal letter, dried black roses, and a shattered stained-glass shard",
                        "iron torture devices, a yellowed skull candelabra, and a locked iron maiden",
                        "a tattered burial shroud, a crumbling gargoyle fragment, and dripping black candles"],
  "any":               ["weathered ancient artifacts, scattered symbolic details, and atmospheric environmental elements",
                        "intricate textural accents, layered meaningful objects, and environmental storytelling details",
                        "period-specific props, symbolic secondary elements, and carefully placed atmospheric objects"]
};

/* Qualificatori atmosferici per mood — 7-8 parole evocative, stile Luciano */
var _ATMOSPHERE_MAP = {
  "dark":        ["shadowed recesses, deep chiaroscuro contrast, spectral cold glow, ominous depth, haunting stillness, void-black undertones, oppressive weight",
                  "ink-black shadow pools, flickering edge light, cryptic symbol scatter, cold iron texture, ghost-light bleed, abyssal peripheral darkness",
                  "heavy noir silhouette, scorched-earth undertone, sulfur-tinted haze, bone-cold light source, visceral shadow depth, silent dread"],
  "ethereal":    ["soft luminescent halo, dreamlike chiffon haze, astral shimmer veil, celestial radiance bloom, otherworldly glow pulse, translucent veil layers, airy diffusion",
                  "gossamer light scatter, angel-wing feather softness, prismatic aura fringe, levitating dust motes, spirit-light flicker, heavenly color mist",
                  "moon-glow softness, pearl-light refraction, sacred silence depth, cloud-spun texture, celestial color wash, divine presence warmth"],
  "epic":        ["thunderous shadow drama, heroic rim backlighting, monumental presence weight, battle-worn texture depth, legendary aura radiance, fierce compositional tension",
                  "storm-charged sky energy, clashing elemental force, titan-scale proportion, war-banner drama, rallying light burst, victory silhouette",
                  "destiny-driven light angle, mythic scale gravity, ancestral power echo, courage-forged steel glint, horizon-fire warmth, sacrificial ash scatter"],
  "serene":      ["gentle morning light filter, tranquil still-water reflection, peaceful silence depth, delicate shadow lace, calm luminescence wash, meditative color range",
                  "slow breath atmosphere, soft-focus ambient haze, contemplative color muting, birdsong stillness, dawn mist drift, flower-petal soft surface",
                  "zen garden breath, dappled shade lattice, still-pool mirror calm, silver light whisper, wabi-sabi imperfection beauty, morning dew texture"],
  "whimsical":   ["playful exaggerated outline, buoyant candy color, animated sparkle scatter, cheerful light bounce, charming detail density, lighthearted glow bubble",
                  "fairy-tale storybook warmth, surprise-pop composition, wonder-wide-eye scale, floating confetti particle, sugar-light shadow, merry color collision",
                  "carnival color saturation, unexpected narrative detail, delight-driven proportion, enchanted radiance, approachable warmth, innocent magical energy"],
  "melancholic": ["wistful muted color drain, introspective shadow weight, rain-memory texture, solitude spatial emptiness, faded-glory patina, quiet ache light direction",
                  "overcast flat ambient, autumnal color decay, time-worn surface texture, unspoken grief depth, last-light warmth fade, isolating compositional choice",
                  "memorial still atmosphere, sepia emotional drift, tender fragility surface, bittersweet color tension, silent witness angle, fading warmth"],
  "mysterious":  ["cryptic symbol layering, hidden depth suggestion, veiled presence ambiguity, arcane shadow scatter, enigmatic glow source, secretive atmosphere weight",
                  "half-seen form teasing, forbidden knowledge aura, coded message texture, unknown threat edge, peripheral movement shadow, rune-carved surface depth",
                  "fog-of-mystery spatial veil, ancient inscription detail, ritual circle residue, deliberate narrative gap, elusive presence, arcane concealment"],
  "futuristic":  ["data-stream particle flow, holographic overlay shimmer, chrome-on-chrome reflection, zero-g spatial logic, advanced material sheen, grid-city depth perspective",
                  "neon-bloom color cast, terminal-green ambient, synthetic texture clarity, quantum field distortion, plasma edge glow, command-bridge scale",
                  "signal-noise interference, exoplanet horizon glow, biome-dome ecosystem depth, AI-rendered light, cold efficiency beauty, technological sublime"],
  "romantic":    ["candlelit golden warmth, velvet shadow depth, rose-petal scatter softness, intimate spatial closeness, tender color saturation, longing light angle",
                  "fireplace amber glow, first-love color palette, private moment depth, whispering shadow layer, heart-shaped light dapple, warm embrace texture",
                  "twilight violet hour wash, moonlit silver warmth, secret-garden seclusion, trembling candleflame, jasmine-perfume atmosphere, devotional pull"],
  "chaotic":     ["fractured plane energy, explosive color collision, turbulent brush mark, kinetic force scatter, maximum visual entropy, velocity-blurred form",
                  "shattered reality fragment, overloaded signal noise, impact-wave distortion, storm-force diagonal, primal scream color, momentum-driven composition",
                  "riot-energy texture, cascading system failure, broken symmetry drama, white-noise static depth, emergency-light strobe, war-zone compositional debris"],
  "dramatic":    ["theatrical shadow rake, single-source punch light, deep chiaroscuro tension, stage-presence weight, cinematic composition gravity, high-contrast silhouette drama",
                  "venetian-blind shadow stripe, smoke-veil atmosphere, three-quarter back-rim light, noir-grade tonal split, cinematic depth-of-field, story-driven framing",
                  "spotlight isolation drama, oppressive shadow fill, face-carved directional light, cinematic color grade, scene-weight pause, tense negative space"],
  "elegant":     ["refined restraint composition, soft luxury texture, luminous satin surface, gold-thread detail accent, composed white-space balance, graceful proportion geometry",
                  "boudoir soft-box warmth, velvet shadow nuance, pearl-highlight skin quality, tasteful monochrome accent, editorial calm color, studied gesture poise",
                  "couture editorial clean, museum-wall calm, hushed luxury palette, impeccable finish surface, porcelain light quality, deliberate stylistic control"],
  "any":         ["intricate surface detail, layered atmospheric depth, considered light-shadow ratio, deliberate compositional tension, professional color harmony, rich visual complexity",
                  "masterful tonal range, skillful mark-making quality, evocative atmosphere, precise detail control, confident rendering, engaging visual narrative"]
};

/* Scena di sfondo tematica per soggetto */
var _BG_SCENE_MAP = {
  "portrait":          ["candlelit alchemist's chamber","moonlit palazzo balcony","ancient carved stone throne room","ivy-covered library alcove","fog-drenched cliffside"],
  "landscape":         ["distant craggy mountain silhouette","vast open primordial wilderness","crumbling civilisation ruin field","storm-lit horizon plain","ancient forest cathedral"],
  "creature":          ["smoldering volcanic crater rim","eldritch enchanted grove","age-old battlefield ruin","ethereal spirit void","deep subterranean cavern"],
  "character":         ["forgotten jungle temple","moonlit cobblestone courtyard","arcane artificer's workshop","shadowed tavern archway","wind-battered clifftop watchtower"],
  "architecture":      ["storm-darkened night sky","moonlit misty valley","ancient overgrown acropolis","lightning-split horizon","sacred geometric void"],
  "nature":            ["pristine old-growth forest","wildflower alpine meadow","fog-veiled river delta","tide-pool rocky coastline","bamboo mountain grove"],
  "space":             ["deep-space gas nebula","alien binary star system","collapsing galactic core","exoplanet ring system","dark matter void passage"],
  "urban":             ["rain-soaked megacity canyon","neon-lit underground market","rooftop city skyline","industrial harbor district","brutalist plaza at dusk"],
  "mythology":         ["sacred pantheon temple ruins","celestial divine realm","labyrinthine underworld passage","sacred mountain summit","ancient oracle grove"],
  "fashion":           ["marble editorial studio","couture runway abstraction","sun-drenched palazzo terrace","brutalist concrete gallery","romantic garden at dusk"],
  "abstract_concept":  ["infinite recursive void","fractured mirror dimension","geometric sacred space","pure color field infinity","quantum superposition realm"],
  "interior":          ["grand Victorian library","abandoned baroque salon","monastery scriptorium","cozy firelit study","ancient bathhouse interior"],
  "still_life":        ["antique collector's cabinet","painter's studio corner","dimly lit apothecary shelf","sun-warmed windowsill","quiet chapel side altar"],
  "fantasy":           ["enchanted ancient forest","mythical realm gateway","druidic stone circle","arcane floating island","ruined dragon's lair"],
  "cyberpunk":         ["rain-soaked neon megacity","underground hacker den","corporate arcology exterior","junkyard augmentation clinic","digital data-stream void"],
  "gothic":            ["crumbling Gothic cathedral","fog-shrouded cemetery","haunted manor hallway","cursed moor at midnight","subterranean crypt passage"],
  "any":               ["evocative atmospheric backdrop","ancient ruins in the distance","fog-veiled mysterious horizon","thematically resonant environment","carefully chosen contextual setting"]
};

/* Luce per mood */
var _LIGHTING_MAP = {
  "dark":        ["stark single-source candlelight with ink-black shadow pools","cold moonlight with harsh theatrical contrast","bioluminescent ghost-light in absolute darkness","ominous blood-red emergency light cast"],
  "ethereal":    ["soft celestial backlit halo diffusion","sacred diffused divine radiance","aurora-shimmer ambient glow","silver moonbeam through mist veil"],
  "epic":        ["dramatic golden-hour rim backlighting","stormy battle-sky god-ray burst","volcanic furnace light from below","military searchlight drama"],
  "serene":      ["gentle dappled morning forest light","soft overcast silver north light","warm late-afternoon golden angle","still-pool reflected ambient fill"],
  "whimsical":   ["warm fairy-light string bokeh glow","sparkling magical particle light","cotton-candy soft diffused fill","playful colour-gel party light"],
  "melancholic": ["flat overcast grey ambient","single dusty window slant","fading sunset last warmth","cold fluorescent institutional light"],
  "mysterious":  ["single flickering torch in deep shadow","moonlit with fog diffusion veil","under-lit face dramatic uplight","ultraviolet black-light reveal"],
  "futuristic":  ["cold clinical LED grid array","neon bloom urban ambient","holographic blue fill light","terminal-green monitor ambient cast"],
  "romantic":    ["warm candleflame golden fill","rosy-tinted sunset golden hour","fairy-light bokeh wrap-around","fireplace amber key with shadow"],
  "chaotic":     ["stroboscopic flash fragment lighting","lightning-strike instant illumination","fire-source dynamic dancing light","emergency siren red-blue flash"],
  "dramatic":    ["stark single-source key with deep shadow fill","theatrical ellipsoidal spotlight isolation","three-quarter rim light with heavy shadow","cinematic cross-light chiaroscuro"],
  "elegant":     ["soft beauty dish with feathered fill","warm pearled clamshell portrait light","diffused north-light studio ambient","low-angle warm window light"],
  "any":         ["professional studio three-point lighting","cinematic motivated light setup","dramatic directional key light with ambient fill","natural available light direction"]
};

/* Traduzione parola per parola usando il dizionario */
function _translateWord(w) {
  var lw = w.toLowerCase().replace(/[.,;:!?]/g,"");
  if (_IT[lw] !== undefined) return _IT[lw];
  return w; /* lascia invariata se non in dizionario */
}

function _translateIT(text) {
  var t = text;
  /* 1. frasi multi-parola */
  for (var i = 0; i < _IT_PHRASES.length; i++) {
    var re = new RegExp(_IT_PHRASES[i][0], "gi");
    t = t.replace(re, _IT_PHRASES[i][1]);
  }
  /* 2. singole parole */
  t = t.replace(/\b[\w']+\b/g, _translateWord);
  /* 3. pulizia spazi e virgole */
  t = t.replace(/\s*,\s*/g, ", ").replace(/\s+/g, " ").replace(/(,\s*)+/g, ", ").trim();
  t = t.replace(/^[,\s]+|[,\s]+$/g, "");
  return t;
}

/* ===== GRAMMAR FIX: corregge l'idea prima di usarla nel prompt =====
   Converte bare infinitive → gerund quando usato come modificatore dopo un sostantivo.
   Corregge articoli a/an. Non tocca frasi già corrette. */
function _fixGrammar(text) {
  if (!text) return text;
  var t = text.trim();

  /* Mappa verbo base / 3a sing. → gerundio */
  var VG = {
    "wear":"wearing","wears":"wearing","hold":"holding","holds":"holding",
    "ride":"riding","rides":"riding","carry":"carrying","carries":"carrying",
    "stand":"standing","stands":"standing","sit":"sitting","sits":"sitting",
    "walk":"walking","walks":"walking","run":"running","runs":"running",
    "fly":"flying","flies":"flying","fight":"fighting","fights":"fighting",
    "cast":"casting","casts":"casting","wield":"wielding","wields":"wielding",
    "summon":"summoning","summons":"summoning","raise":"raising","raises":"raising",
    "shoot":"shooting","shoots":"shooting","draw":"drawing","draws":"drawing",
    "forge":"forging","forges":"forging","command":"commanding","commands":"commanding",
    "smile":"smiling","smiles":"smiling","laugh":"laughing","laughs":"laughing",
    "gaze":"gazing","gazes":"gazing","stare":"staring","stares":"staring",
    "look":"looking","looks":"looking","float":"floating","floats":"floating",
    "emerge":"emerging","emerges":"emerging","radiate":"radiating","radiates":"radiating",
    "tower":"towering","towers":"towering","loom":"looming","looms":"looming",
    "hover":"hovering","hovers":"hovering","burn":"burning","burns":"burning",
    "glow":"glowing","glows":"glowing","shine":"shining","shines":"shining"
  };

  /* Ausiliari: dopo questi il verbo base è corretto e NON va cambiato */
  var AUX = /^(is|are|was|were|be|been|to|will|shall|may|might|can|could|would|should|must|have|has|had|do|does|did|not|and|or|with|in|on|at|a|an|the|,)$/i;

  var words = t.split(/\b/);  /* split conservando i separatori */
  for (var i = 0; i < words.length; i++) {
    var w = words[i].toLowerCase();
    if (!VG[w]) continue;
    /* Trova la parola precedente significativa (non spazio/punteggiatura) */
    var prev = "";
    for (var j = i - 1; j >= 0; j--) {
      var candidate = words[j].trim().replace(/[,;!?.]/g, "");
      if (candidate.length > 0) { prev = candidate; break; }
    }
    if (!AUX.test(prev)) {
      /* Preserva maiuscola iniziale se c'era */
      var fixed = VG[w];
      if (words[i][0] === words[i][0].toUpperCase() && words[i][0] !== words[i][0].toLowerCase()) {
        fixed = fixed[0].toUpperCase() + fixed.slice(1);
      }
      words[i] = fixed;
    }
  }
  t = words.join("");

  /* Articolo a/an: corregge prima di vocale e prima di consonante */
  t = t.replace(/\ban\s+([^aeiouAEIOU\s])/g, "a $1");
  t = t.replace(/\ba\s+([aeiouAEIOU])/g, "an $1");

  /* Pulizia spazi multipli e virgole doppie */
  t = t.replace(/\s+/g, " ").replace(/,\s*,/g, ",").trim();
  return t;
}

/* ===== PASSO 3: Coerenza — rimuove rumore e normalizza =====
   Elimina avverbi vaghi, prefissi imperativi rimasti, punteggiatura ridondante. */
function _pass3_coherence(text) {
  var t = text;

  /* Avverbi vaghi che non aggiungono valore a MJ */
  t = t.replace(/\b(very|really|so much|quite|pretty|just|a bit|a little|somewhat|rather|extremely|totally|absolutely|definitely|certainly|probably|slightly)\b\s*/gi, "");

  /* Prefissi imperativi che possono sfuggire alla traduzione */
  t = t.replace(/^(create|draw|make|show|generate|design|paint|paint me|illustrate|depict|render|imagine|picture)\s+/gi, "");

  /* "looking" ridondante: "beautiful looking" → "beautiful" */
  t = t.replace(/\b(\w+)\s+looking\b/gi, "$1");

  /* Normalizza punteggiatura */
  t = t.replace(/[,\s]+,/g, ",").replace(/,{2,}/g, ",").replace(/\s*,\s*/g, ", ");
  t = t.replace(/\s+/g, " ").trim();

  /* Articolo a/an di nuovo dopo le sostituzioni */
  t = t.replace(/\ban\s+([^aeiouAEIOU\s])/g, "a $1");
  t = t.replace(/\ba\s+([aeiouAEIOU])/g, "an $1");

  return t;
}

/* ===== PASSO 4: Best practice Midjourney — rafforza aggettivi deboli =====
   Sostituisce termini generici con equivalenti evocativi per MJ. */
var _UPGRADE_ADJ = {
  "big":       ["massive","towering","colossal","enormous"],
  "huge":      ["colossal","titanic","immense","gargantuan"],
  "small":     ["delicate","miniature","diminutive","petite"],
  "nice":      ["exquisite","refined","breathtaking"],
  "good":      ["exceptional","masterful","flawless"],
  "bad":       ["corrupted","malevolent","decayed"],
  "cool":      ["striking","captivating","mesmerizing"],
  "amazing":   ["breathtaking","spectacular","awe-inspiring"],
  "beautiful": ["resplendent","luminous","exquisite"],
  "ugly":      ["grotesque","malformed","visceral"],
  "scary":     ["terrifying","nightmarish","bone-chilling"],
  "cute":      ["endearing","charming","whimsically adorable"],
  "old":       ["ancient","time-worn","primordial"],
  "powerful":  ["formidable","omnipotent","unstoppable"],
  "epic":      ["legendary","monumental","awe-inspiring"],
  "detailed":  ["intricately detailed","richly rendered"],
  "golden":    ["burnished gold","radiant gilded","lustrous amber-gold"],
};

function _pass4_bestpractice(text) {
  var t = text;
  for (var adj in _UPGRADE_ADJ) {
    var re = new RegExp("\\b" + adj + "\\b", "gi");
    if (re.test(t)) {
      var pool = _UPGRADE_ADJ[adj];
      var rep  = pool[Math.floor(Math.random() * pool.length)];
      t = t.replace(new RegExp("\\b" + adj + "\\b", "gi"), rep);
    }
  }
  /* Pulizia finale */
  t = t.replace(/\s+/g, " ").replace(/,\s*,/g, ", ").trim();
  return t;
}

/* ===== FASE 1: rileva contesto semantico dal testo tradotto =====
   Usato quando i dropdown sono "any" per evitare componenti incoerenti. */
function _detectContext(text) {
  var t = text.toLowerCase();
  var ctx = { subject: null, mood: null, style: null };

  /* Subject: primo pattern che matcha vince */
  var SP = [
    [/\b(portrait|face|bust|headshot|close.?up|visage)\b/,                           "portrait"],
    [/\b(dragon|demon|monster|beast|creature|chimera|hydra|griffin|golem|basilisk)\b/,"creature"],
    [/\b(mage|wizard|witch|sorcerer|warrior|knight|hero|villain|fighter|assassin|ranger|hunter|paladin|rogue|warlord)\b/, "character"],
    [/\b(god|goddess|deity|divine|myth|olymp|thor|zeus|odin|anubis|legend|mytholog)\b/,"mythology"],
    [/\b(castle|temple|tower|fortress|palace|cathedral|dungeon|ruin|citadel|arena)\b/,"architecture"],
    [/\b(landscape|world|realm|kingdom|terrain|horizon|panorama|scenery|vista|wasteland)\b/, "landscape"],
    [/\b(space|galaxy|nebula|planet|star|cosmic|astronaut|spaceship|alien|orbital)\b/,"space"],
    [/\b(forest|nature|botanical|garden|flower|tree|wildlife|jungle|wilderness)\b/,   "nature"],
    [/\b(street|urban|graffiti|alley|downtown|cityscape|metropolis)\b/,               "urban"],
    [/\b(fashion|couture|model|garment|outfit|runway|wardrobe)\b/,                    "fashion"],
    [/\b(interior|room|chamber|library|salon|hallway|dungeon interior)\b/,            "interior"],
    [/\b(still life|object|artifact|potion|relic|weapon|wand|staff|sword|shield)\b/,  "still_life"],
  ];
  for (var i = 0; i < SP.length; i++) {
    if (SP[i][0].test(t)) { ctx.subject = SP[i][1]; break; }
  }

  /* Mood: priorità alta per segnali forti (dark/epic prima di serene) */
  var MP = [
    [/\b(apocal|inferno|hell|devil|demon|doom|corrupt|destruct|annihilat|devastat|wasteland|ruin|fallen)\b/, "dark"],
    [/\b(fire|blaze|flame|burn|volcanic|lava|molten|scorched|inferno|ember|smolder)\b/,                      "chaotic"],
    [/\b(epic|heroic|legendary|mighty|grand|monumental|battle|war|conquest|titan|glorious)\b/,               "epic"],
    [/\b(ethereal|celestial|divine|angelic|heaven|spirit|luminous|astral|transcend)\b/,                      "ethereal"],
    [/\b(mysterious|enigma|hidden|secret|arcane|cryptic|veiled|unknown|eldritch)\b/,                         "mysterious"],
    [/\b(dramatic|cinematic|theatr|spotlight|stage.lit|high.contrast)\b/,                                    "dramatic"],
    [/\b(elegant|refined|luxury|luxurious|noble|aristocratic|regal|opulent)\b/,                              "elegant"],
    [/\b(futurist|tech|cyber|robot|android|digital|neon|holo|synthwave)\b/,                                  "futuristic"],
    [/\b(romantic|love|tender|intimate|passion|rose|heart|velvet)\b/,                                        "romantic"],
    [/\b(sad|melan|lone|isolat|sorrow|grief|wistful|nostalgic|fading)\b/,                                    "melancholic"],
    [/\b(whimsical|playful|cute|fairy|enchanting|kawaii|storybook)\b/,                                       "whimsical"],
    [/\b(serene|peaceful|calm|tranquil|gentle|meditat|still|zen)\b/,                                         "serene"],
  ];
  for (var i = 0; i < MP.length; i++) {
    if (MP[i][0].test(t)) { ctx.mood = MP[i][1]; break; }
  }

  /* Style: rileva dal testo dell'idea */
  var STY = [
    [/\b(impasto|alla prima|oil paint|brushwork|glazed?|canvas|wet.into.wet)\b/,          "painting"],
    [/\b(fantasy|magic|arcane|enchant|spell|rune|sorcery|wizard|dragon|mage|sorcerer|warlock|demon|devil|eldritch|occult|mythic|fairy|fae)\b/,"fantasy"],
    [/\b(cyberpunk|cyber|neon city|hacker|biopunk|augment)\b/,                            "cyberpunk"],
    [/\b(sci.?fi|starship|android|exo.armor|orbital|deep.space)\b/,                      "sci_fi"],
    [/\b(gothic|vampire|gargoyle|dark.victor|crypt|occult)\b/,                            "gothic"],
    [/\b(horror|nightmare|creepy|macabre|grotesque|visceral)\b/,                          "horror"],
    [/\b(anime|manga|chibi|kawaii|cel.shad|shonen)\b/,                                    "anime_manga"],
    [/\b(watercolor|aquarell|gouache|ink wash)\b/,                                        "watercolor"],
    [/\b(surreal|dreamlike|impossible|dali|magritte|subconscious)\b/,                     "surreal"],
    [/\b(vintage|retro|1[5-9][0-9]0s|nostalgic|aged photograph)\b/,                      "vintage_retro"],
    [/\b(minimali[sz]|minimal|sparse|negative space)\b/,                                  "minimalist"],
    [/\b(geometric|polygon|tessellat|angular|crystalline|faceted)\b/,                     "geometric"],
    [/\b(steampunk|steam.?punk|clockwork|brass gear)\b/,                                  "steampunk"],
    [/\b(noir|film noir|chiaroscuro|venetian.blind|hard.boiled)\b/,                       "noir"],
  ];
  for (var i = 0; i < STY.length; i++) {
    if (STY[i][0].test(t)) { ctx.style = STY[i][1]; break; }
  }

  return ctx;
}

/* ===== FASE 2+3: costruzione prompt con 3 controlli =====
   FASE 1 — Lingua: traduzione + pulizia
   FASE 2 — Coerenza: dropdown + context rilevato dal testo → no componenti incoerenti
   FASE 3 — Struttura: 8 componenti sempre presenti, coerenti con soggetto+mood */
function processPrompt(raw) {
  var selStyle   = (document.getElementById("sel-style")   || {}).value || "any";
  var selMood    = (document.getElementById("sel-mood")    || {}).value || "any";
  var selPalette = (document.getElementById("sel-palette") || {}).value || "any";
  var selSubject = (document.getElementById("sel-subject") || {}).value || "any";

  /* PIPELINE 4 PASSI — idea grezza → idea pulita e coerente per MJ */
  /* Passo 1: lingua — usa testo pre-tradotto da _translateAny() se disponibile */
  var translated = (window.__preTranslated && window.__preTranslated.trim())
                 ? window.__preTranslated
                 : _translateIT(raw.trim());
  window.__preTranslated = null; /* consuma */
  translated = translated.replace(/^(i want |i would like |please )\s*/i, "");
  translated = translated.replace(/[.!?]+$/, "").trim();
  /* Passo 2: grammatica */
  translated = _fixGrammar(translated);
  /* Passo 3: coerenza e rimozione rumore */
  translated = _pass3_coherence(translated);
  /* Passo 4: upgrade aggettivi deboli */
  translated = _pass4_bestpractice(translated);

  /* FASE 2 — Coerenza: rileva context dal testo, integra con i dropdown */
  var ctx = _detectContext(translated);
  /* Dropdown esplicito ha priorità; se "any", usa il context rilevato dal testo */
  var style   = (selStyle   !== "any") ? selStyle   : (ctx.style   || "any");
  var mood    = (selMood    !== "any") ? selMood    : (ctx.mood    || "any");
  var palette = selPalette; /* palette sempre dal dropdown, è scelta estetica */
  var subject = (selSubject !== "any") ? selSubject : (ctx.subject || "any");

  /* FASE 3 — Struttura: 8 componenti coerenti */

  /* 1. Descrittori visivi (stile effettivo) */
  var visualDesc = _pickRand(_VISUAL_STYLE[style] || _VISUAL_STYLE["any"]);

  /* 2. Colore sfondo evocativo — priorità: palette dropdown > mood effettivo */
  var colorKey = (palette !== "any") ? palette : (mood !== "any" ? mood : "any");
  var bgColor  = _pickRand(_BG_COLORS_MAP[colorKey] || _BG_COLORS_MAP["any"]);

  /* 3. Livello di dettaglio */
  var detailLevel = (style === "minimalist") ? "refined minimal detail" : "intricate detail";

  /* 4. Props contestuali: soggetto effettivo > stile effettivo > any */
  var propKey = (subject !== "any" && _PROPS_MAP[subject]) ? subject
              : (style   !== "any" && _PROPS_MAP[style])   ? style
              : "any";
  var props = _pickRand(_PROPS_MAP[propKey] || _PROPS_MAP["any"]);

  /* 5. Qualificatori atmosferici (mood effettivo — coerente col soggetto) */
  var atmosphere = _pickRand(_ATMOSPHERE_MAP[mood] || _ATMOSPHERE_MAP["any"]);

  /* 6. Dichiarazione stile artistico nominato */
  var artStyle = _pickRand(_ART_STYLE_DECL[style] || _ART_STYLE_DECL["any"]);

  /* 7. Scena sfondo (soggetto effettivo > stile effettivo) */
  var sceneKey = (subject !== "any" && _BG_SCENE_MAP[subject]) ? subject
               : (style   !== "any" && _BG_SCENE_MAP[style])   ? style
               : "any";
  var bgScene = _pickRand(_BG_SCENE_MAP[sceneKey] || _BG_SCENE_MAP["any"]);

  /* 8. Luce (mood effettivo) */
  var lighting = _pickRand(_LIGHTING_MAP[mood] || _LIGHTING_MAP["any"]);

  /* Assemblaggio finale */
  var parts = [];
  parts.push(translated);
  if (visualDesc)  parts.push(visualDesc);
  parts.push("isolated on a " + bgColor + " background");
  parts.push(detailLevel);
  if (props)       parts.push("with " + props);
  if (atmosphere)  parts.push(atmosphere);
  parts.push("digital art illustration");
  if (artStyle)    parts.push(artStyle);
  if (bgScene)     parts.push(bgScene + " in background");
  if (lighting)    parts.push(lighting);

  return parts.filter(function(p){ return p && p.trim(); }).join(", ");
}

function getSubject() {
  var raw = ((document.getElementById("userIdea") || {}).value || "").trim();
  if (!raw) return "[your subject]";
  return processPrompt(raw);
}

function previewProcessedPrompt() {
  /* Preview rimossa dall'UI — funzione mantenuta per compatibilità chiamanti */
}

/* ===== MATRIX REVEAL ANIMATION ===== */
function matrixReveal(text, el, durationMs) {
  var charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%&*";
  var arr = text.split("").map(function() { return charset[Math.floor(Math.random()*charset.length)]; });
  var revealed = 0;
  var total    = text.length;
  var steps    = Math.max(total, 1);
  var ms       = Math.max(20, durationMs / steps);
  el.textContent = arr.join("");
  var timer = setInterval(function() {
    /* scramble non-revealed */
    for (var i = revealed; i < total; i++) {
      if (text[i] !== " ") arr[i] = charset[Math.floor(Math.random()*charset.length)];
    }
    /* reveal next char */
    while (revealed < total && text[revealed] === " ") { arr[revealed] = " "; revealed++; }
    if (revealed < total) { arr[revealed] = text[revealed]; revealed++; }
    el.textContent = arr.join("");
    if (revealed >= total) { clearInterval(timer); el.textContent = text; }
  }, ms);
}

function copyPrompt(text, btn) {
  var originalText = btn.dataset.label || btn.textContent;
  btn.dataset.label = originalText;  /* salva al primo click */
  navigator.clipboard.writeText(text).then(function() {
    btn.textContent = "COPIED!";
    btn.classList.add("copied");
    setTimeout(function(){ btn.textContent = originalText; btn.classList.remove("copied"); }, 2000);
  }).catch(function(){
    btn.textContent = "COPY ERROR";
    setTimeout(function(){ btn.textContent = originalText; }, 2000);
  });
}

/* ===== PDF EXPORT (solo PRO) ===== */
function downloadPDF() {
  if (!isPro()) { openModal(); return; }
  var ideaRaw = ((document.getElementById("userIdea") || {}).value || "").trim();
  var dateStr = new Date().toLocaleDateString("it-IT", {day:"2-digit",month:"2-digit",year:"numeric"});
  var puri  = document.querySelectorAll("#results-inner .card-puro");
  var mixes = document.querySelectorAll("#results-inner .card-mix");
  if (!puri.length && !mixes.length) { alert("Run a search first."); return; }

  var win = window.open("", "_blank");
  if (!win) { alert("Abilita i popup per generare il PDF."); return; }

  var rows = "";
  puri.forEach(function(card) {
    var num    = (card.querySelector(".sref-number") || {}).textContent || "";
    var name   = (card.querySelector(".sref-name")   || {}).textContent || "";
    var prompt = (card.querySelector(".prompt-text") || {}).textContent || "";
    rows += '<div class="row"><div class="row-num">' + num + '</div>'
      + '<div class="row-name">' + name + '</div>'
      + '<div class="row-prompt">' + prompt + '</div></div>';
  });
  var mixRows = "";
  mixes.forEach(function(card) {
    var title  = (card.querySelector(".mix-title")   || {}).textContent || "";
    var prompt = (card.querySelector(".prompt-text") || {}).textContent || "";
    mixRows += '<div class="row"><div class="row-name" style="font-weight:700;">' + title + '</div>'
      + '<div class="row-prompt">' + prompt + '</div></div>';
  });

  win.document.write('<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8">'
    + '<title>SrefMindForge Export ' + dateStr + '</title><style>'
    + 'body{font-family:Arial,Helvetica,sans-serif;background:#fff;color:#111;margin:0;padding:28px 32px;}'
    + 'h1{font-size:1.5rem;font-weight:900;letter-spacing:.08em;margin:0 0 2px;}'
    + 'h1 span{color:#e94560;}'
    + '.meta{font-size:.78rem;color:#888;margin-bottom:18px;}'
    + 'h2{font-size:.78rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;'
    + '   color:#888;border-bottom:1px solid #ddd;padding-bottom:5px;margin:18px 0 10px;}'
    + '.row{border:1px solid #e0e0e0;border-radius:6px;padding:10px 14px;margin-bottom:8px;'
    + '     page-break-inside:avoid;}'
    + '.row-num{font-size:1.4rem;font-weight:900;color:#e94560;line-height:1;}'
    + '.row-name{font-size:.88rem;font-weight:600;margin:2px 0 4px;}'
    + '.row-prompt{font-family:Consolas,monospace;font-size:.74rem;background:#f6f6f6;'
    + '            padding:6px 10px;border-radius:4px;word-break:break-all;line-height:1.45;}'
    + '.footer{font-size:.68rem;color:#aaa;border-top:1px solid #eee;padding-top:8px;margin-top:24px;}'
    + '@media print{body{padding:10px 14px;}}'
    + '</style></head><body>'
    + '<h1>CIANO<span>AI</span> SrefMindForge</h1>'
    + '<div class="meta">Export sessione &mdash; ' + dateStr
    + (ideaRaw ? ' &mdash; Idea: ' + ideaRaw : '') + '</div>');

  if (rows)    win.document.write('<h2>SREF Puri</h2>'    + rows);
  if (mixRows) win.document.write('<h2>Mix Consigliati</h2>' + mixRows);

  win.document.write('<div class="footer">Generato da CIANOAI SrefMindForge &mdash; tutti i diritti riservati</div>'
    + '</body></html>');
  win.document.close();
  win.focus();
  setTimeout(function(){ win.print(); }, 600);
}

/* ===== SCORING ===== */
function calcScore(s, style, subject, mood, palette) {
  var sc = 0;
  if (style !== "any"   && (s.style_tags   || []).indexOf(style)   !== -1) sc += 3;
  if (subject !== "any" && (s.subject_tags || []).indexOf(subject) !== -1) sc += 2;
  if (mood !== "any"    && (s.mood_tags    || []).indexOf(mood)    !== -1) sc += 1;
  if (palette !== "any" && (s.palette_tags || []).indexOf(palette) !== -1) sc += 1;
  if (s.manuale) sc += 0.1;  /* bonus piccolo: solo tie-breaker, non domina il ranking */
  return sc;
}

/* Selezione pure con diversità geo: preferisce SREF da famiglie visive diverse */
function selectDiversePuri(sorted, count) {
  var result = [], usedGeos = {}, i, s;
  /* Pass 1: max 1 SREF per famiglia geo */
  for (i = 0; i < sorted.length && result.length < count; i++) {
    s = sorted[i];
    var g = s.geo || "unknown";
    if (!usedGeos[g]) { result.push(s); usedGeos[g] = 1; }
  }
  /* Pass 2: riempi i posti rimasti (geo repeat ok) */
  for (i = 0; i < sorted.length && result.length < count; i++) {
    s = sorted[i];
    if (result.indexOf(s) === -1) result.push(s);
  }
  return result;
}

/* ===== BUILD MIX CON MOTIVAZIONI ===== */
function buildMixWithReason(pool, excluded) {
  var avail = pool.filter(function(s){ return !excluded[s.sref]; });
  if (!avail.length) return null;

  var A = avail[0];
  var compat = GEO_COMPAT[A.geo] || Object.keys(GEO_LABELS);
  var geoA = GEO_LABELS[A.geo] || "Versatile";

  var B = null, reasonB = "";
  for (var i = 1; i < avail.length; i++) {
    var s = avail[i];
    if (compat.indexOf(s.geo) !== -1 && s.geo !== A.geo) {
      B = s;
      reasonB = "Geo compatible: " + geoA + " + " + (GEO_LABELS[s.geo] || "Versatile");
      break;
    }
  }
  if (!B) {
    for (var i = 1; i < avail.length; i++) {
      var s = avail[i];
      var stA = A.style_tags || [], stS = s.style_tags || [];
      var overlap = stA.filter(function(t){ return stS.indexOf(t) !== -1; }).length;
      if (!overlap) { B = s; reasonB = "Complementary style to A — different visual language"; break; }
    }
  }
  if (!B) {
    B = avail.length > 1 ? avail[1] : null;
    if (B) reasonB = "Alternative variation — high score, different perspective";
  }
  if (!B) return { srefs:[A], weights:[2], reasons:["Score massimo nel pool"] };

  return {
    srefs: [A, B],
    reasons: ["Top score in pool — highest match for your filters", reasonB]
  };
}

/* ===== RENDER CARD PURO ===== */
function cardPuroHTML(sref, idx) {
  var pro     = isPro();
  var subject = getSubject();
  var prompt  = subject + " --sref " + sref.sref;
  var mBadge  = sref.manuale ? '<span class="badge badge-manuale">CURATED</span>' : "";

  var detailsHtml = "";
  if (pro) {
    var stTags = (sref.style_tags||[]).join(", ")   || "—";
    var suTags = (sref.subject_tags||[]).join(", ") || "—";
    var moTags = (sref.mood_tags||[]).join(", ")    || "—";
    var paTags = (sref.palette_tags||[]).join(", ") || "—";
    detailsHtml = '<div class="card-details">'
      + '<details><summary>Description</summary><p>' + escHtml(sref.description || "—") + '</p></details>'
      + '<details><summary>Keywords</summary><p class="kw-list">' + escHtml(sref.keywords || "—") + '</p></details>'
      + '<details><summary>Assigned Tags</summary><p>'
      + '<strong>Style:</strong> '   + stTags + '<br>'
      + '<strong>Subject:</strong> ' + suTags + '<br>'
      + '<strong>Mood:</strong> '    + moTags + '<br>'
      + '<strong>Palette:</strong> ' + paTags + '</p></details>'
      + '</div>';
  }

  return '<div class="card-puro">'
    + '<div class="sref-number">' + sref.sref + '</div>'
    + '<div class="sref-name">'   + escHtml(sref.nome || "—") + '</div>'
    + '<div class="badges">'      + geoBadgeHTML(sref.geo) + mBadge
    + '<span class="badge badge-score">Score ' + sref._score.toFixed(4) + '</span></div>'
    + detailsHtml
    + '<div style="margin-top:auto;padding-top:10px">'
    + '<div class="sref-code-display">--sref ' + sref.sref + '</div>'
    + '<button class="btn-copy" data-prompt="' + escHtml(prompt)
    + '" onclick="copyPrompt(this.dataset.prompt,this)">COPY PROMPT</button>'
    + '</div></div>';
}

/* ===== RENDER CARD MIX ===== */
function cardMixHTML(mix, idx, showReasons) {
  var subject = getSubject();
  /* Prompt senza pesi: MJ li blenda in parti uguali di default */
  var prompt = subject + " --sref " + mix.srefs.map(function(s){ return s.sref; }).join(" ");
  var labels = ["A", "B"];
  var miniCards = mix.srefs.map(function(s, i) {
    var reason = (showReasons && mix.reasons && mix.reasons[i])
      ? '<div class="mix-reason">' + escHtml(mix.reasons[i]) + '</div>' : "";
    return '<div class="mini-card">'
      + '<div class="mini-card-label">' + labels[i] + '</div>'
      + '<div class="mini-card-sref">' + s.sref + '</div>'
      + '<div class="mini-card-name">' + escHtml(s.nome || "—") + '</div>'
      + '<div style="margin-top:5px">' + geoBadgeHTML(s.geo) + '</div>'
      + reason + '</div>';
  }).join("");
  var title = "SREF " + mix.srefs[0].sref + " + " + mix.srefs[1].sref;
  var srefDisplay = "--sref " + mix.srefs.map(function(s){ return s.sref; }).join(" ");
  return '<div class="card-mix">'
    + '<div class="mix-title">MIX ' + (idx + 1) + ' &mdash; ' + title + '</div>'
    + '<div class="mini-cards">' + miniCards + '</div>'
    + '<div style="margin-top:auto;padding-top:10px">'
    + '<div class="sref-code-display">' + srefDisplay + '</div>'
    + '<button class="btn-copy" data-prompt="' + escHtml(prompt)
    + '" onclick="copyPrompt(this.dataset.prompt,this)">COPY PROMPT</button>'
    + '</div></div>';
}

/* ===== THINKING SIMULATION ===== */
var _THINKING_PHRASES = [
  "Consulting 5,432 style wizards...",
  "Arguing with the aesthetic algorithm...",
  "Taste-testing 847 color palettes...",
  "Waking up the geo-coherence oracle...",
  "Negotiating with surreal-open SREF families...",
  "Counting pixels in 3,525 universes...",
  "Cross-referencing vibes with the mood database...",
  "Asking ChatGPT... just kidding, doing it ourselves.",
  "Politely rejecting 2,800 mediocre SREFs...",
  "Running style compatibility at the speed of art...",
  "Teaching the engine what 'cinematic' really means...",
  "Separating the masterpieces from the meh...",
  "Calibrating the epic-ness meter...",
  "Double-checking that fog + sword = atmospheric, not weird...",
  "Brewing the perfect SREF espresso...",
];

function _showThinking(callback) {
  var overlay = document.getElementById("thinkingOverlay");
  var msgEl   = document.getElementById("thinkingMsg");
  overlay.style.display = "flex";
  var idx = 0;
  msgEl.textContent = _THINKING_PHRASES[Math.floor(Math.random() * _THINKING_PHRASES.length)];
  var interval = setInterval(function() {
    idx++;
    msgEl.textContent = _THINKING_PHRASES[Math.floor(Math.random() * _THINKING_PHRASES.length)];
  }, 600);
  setTimeout(function() {
    clearInterval(interval);
    overlay.style.display = "none";
    callback();
  }, 2200);
}

/* ===== TRADUZIONE MULTILINGUA =====
   Prova MyMemory API (free, auto-detect, any language → English).
   Fallback: dizionario locale italiano se offline o errore. */
async function _translateAny(text) {
  if (!text || !text.trim()) return text;

  var raw = text.trim();

  /* Prova dizionario locale (istantaneo, funziona offline) */
  var local = _translateIT(raw);

  /* Se il testo è già solo ASCII e il dizionario non ha cambiato nulla:
     probabilmente è già in inglese — nessuna chiamata API necessaria */
  var hasNonAscii = /[^\x00-\x7F]/.test(raw);
  var localChanged = (local.toLowerCase().trim() !== raw.toLowerCase());
  if (!hasNonAscii && !localChanged) return raw;

  /* Tenta traduzione via API (funziona solo online) */
  try {
    var controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    var tid = controller ? setTimeout(function(){ controller.abort(); }, 5000) : null;
    var opts = controller ? { signal: controller.signal } : {};
    var url = "https://api.mymemory.translated.net/get?q="
            + encodeURIComponent(raw) + "&langpair=auto|en";
    var res  = await fetch(url, opts);
    if (tid) clearTimeout(tid);
    var data = await res.json();
    if (data.responseStatus === 200
        && data.responseData
        && data.responseData.translatedText
        && data.responseData.translatedText.trim().length > 0) {
      return data.responseData.translatedText.trim();
    }
  } catch(e) { /* offline o timeout — cade sul locale */ }

  return local;
}

/* ===== RICERCA PRINCIPALE ===== */
async function cercaSref() {
  if (!window.__sc || !window.__sc.length) {
    alert("Loading SREF data, please wait a moment and try again."); return;
  }
  var resultsEl = document.getElementById("results");
  var innerEl   = document.getElementById("results-inner");

  /* Validazione campo idea obbligatorio */
  var ideaVal = ((document.getElementById("userIdea") || {}).value || "").trim();
  var errEl   = document.getElementById("ideaError");
  if (!ideaVal) {
    if (errEl) errEl.style.display = "block";
    document.getElementById("userIdea").focus();
    return;
  }
  if (errEl) errEl.style.display = "none";

  /* Controllo limite roll giornaliero */
  if (!canRoll()) {
    resultsEl.classList.add("visible");
    innerEl.innerHTML = '<div class="no-results">'
      + '<p>You have reached your daily search limit.</p>'
      + '<small>Come back tomorrow or <a href="#" onclick="openModal();return false;"'
      + ' style="color:var(--accent);">activate SrefMindForge PRO</a> for 10 searches per day.</small></div>';
    resultsEl.scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }
  incrementRolls();
  previewProcessedPrompt();

  /* Mostra overlay subito con messaggio "translating" */
  var _overlay = document.getElementById("thinkingOverlay");
  var _msgEl   = document.getElementById("thinkingMsg");
  _overlay.style.display = "flex";
  _msgEl.textContent = "Translating your idea\u2026";

  /* Traduzione async: API multilingua + fallback dizionario locale */
  var _translated = await _translateAny(ideaVal);
  window.__preTranslated = _translated;

  /* Avvia fase thinking + ricerca */
  _msgEl.textContent = _THINKING_PHRASES[Math.floor(Math.random() * _THINKING_PHRASES.length)];
  var _ti = setInterval(function(){
    _msgEl.textContent = _THINKING_PHRASES[Math.floor(Math.random() * _THINKING_PHRASES.length)];
  }, 600);
  setTimeout(function(){
    clearInterval(_ti);
    _overlay.style.display = "none";
    _doSearch();
  }, 1800);
}

function _doSearch() {
  /* Nasconde il pulsante cerca, mostra inline reset */
  document.getElementById("btnSearch").style.display = "none";
  document.getElementById("btnInlineReset").style.display = "block";
  var resultsEl = document.getElementById("results");
  var innerEl   = document.getElementById("results-inner");

  var style   = document.getElementById("sel-style").value;
  var subject = document.getElementById("sel-subject").value;
  var mood    = document.getElementById("sel-mood").value;
  var palette = document.getElementById("sel-palette").value;
  var allAny  = style==="any" && subject==="any" && mood==="any" && palette==="any";
  var pro     = isPro();
  var limits  = pro ? _P : _F;

  var scored = window.__sc.map(function(s){
    var base = calcScore(s, style, subject, mood, palette);
    /* Piccola componente casuale per rompere i pareggi: ogni ricerca dà risultati freschi */
    return Object.assign({}, s, { _score: base + (Math.random() * 1.5), _base: base });
  }).filter(function(s){
    return allAny ? s.manuale : s._base > 0;
  }).sort(function(a,b){ return b._score - a._score; });

  resultsEl.classList.add("visible");

  if (!scored.length) {
    innerEl.innerHTML = '<div class="no-results"><p>No SREF found for these filters.</p>'
      + '<small>Try relaxing one or more filters.</small></div>';
    return;
  }

  /* Pure SREFs: selezione con diversità geo */
  var puri   = selectDiversePuri(scored, limits.puri);
  var purSet = {};
  puri.forEach(function(s){ purSet[s.sref] = 1; });
  /* Mix pool: più ampio (200), soglia bassa per massima varietà */
  var poolRaw = scored.filter(function(s){
    return !purSet[s.sref] && (allAny || s._base >= 1);
  }).slice(0, 200);

  var excluded = {};
  puri.forEach(function(s){ excluded[s.sref] = 1; });

  var mixes = [];
  for (var m = 0; m < limits.mix; m++) {
    var mix = buildMixWithReason(poolRaw, excluded);
    if (!mix) break;
    mixes.push(mix);
    mix.srefs.forEach(function(s){ excluded[s.sref] = 1; });
  }

  /* Prompt master: mostrato UNA VOLTA sopra tutto */
  var masterPrompt = getSubject();
  var masterFull   = masterPrompt + " --sref [code]";
  var html = '<div class="prompt-master-box">'
    + '<div class="prompt-master-label">Your Midjourney Prompt</div>'
    + '<div class="prompt-master-text" id="masterPromptEl">' + escHtml(masterPrompt) + '</div>'
    + '<div class="prompt-master-hint">This prompt is combined with each SREF below. Use the COPY PROMPT button on each card to get the complete command.</div>'
    + '<button class="btn-copy-master" data-prompt="' + escHtml(masterPrompt)
    + '" onclick="copyPrompt(this.dataset.prompt,this)">COPY BASE PROMPT</button>'
    + '</div>';

  html += '<div class="section-title"><span>' + puri.length
        + '</span> PURE SREF &mdash; ranked by score</div>';
  html += '<div class="puri-grid">';
  html += puri.map(function(s,i){ return cardPuroHTML(s,i); }).join("");
  html += '</div>';

  if (mixes.length) {
    html += '<div class="section-title" style="margin-top:32px"><span>' + mixes.length
          + '</span> SUGGESTED MIXES</div>';
    html += '<div class="weight-tip">'
          + '<strong>Tip:</strong> these prompts use <code>--sref A B</code> (equal blend). '
          + 'To emphasize one style, add weights manually: <code>--sref A::2 B::1</code> '
          + '(A gets double weight). Try it in Midjourney to fine-tune the result.'
          + '</div>';
    html += '<div class="mix-grid">';
    html += mixes.map(function(m,i){ return cardMixHTML(m,i,pro); }).join("");
    html += '</div>';
  }

  /* Reset bar — sempre visibile a fine risultati */
  html += '<div class="reset-bar">'
    + '<button class="btn-new-search" onclick="nuovaRicerca()">NEW SEARCH</button>';
  if (pro) {
    html += '<br><div style="margin-top:10px">'
      + '<button class="btn-pdf" onclick="downloadPDF()">DOWNLOAD PDF SESSION</button></div>';
  } else {
    html += '<div class="reset-hint">With <a href="#" onclick="openModal();return false;"'
      + ' style="color:var(--pro)">SrefMindForge PRO</a> you can download the full PDF before resetting.</div>';
  }
  html += '</div>';

  if (!pro) {
    html += '<div class="pro-teaser">'
      + '<div class="pro-teaser-badge">SrefMindForge PRO</div>'
      + '<div class="pro-teaser-title">You are seeing only a portion of the results</div>'
      + '<div class="pro-teaser-text">'
      + '<strong>10 pure SREFs</strong> instead of 3 &nbsp;&middot;&nbsp;'
      + '<strong>5 Mixes</strong> instead of 2 &nbsp;&middot;&nbsp;'
      + '<strong>10 searches/day</strong> &nbsp;&middot;&nbsp;'
      + '<strong>PDF Download</strong> of the session'
      + '</div>'
      + '<button class="btn-upgrade" onclick="openModal()">Activate SrefMindForge PRO &mdash; &euro;4.99/month</button>'
      + '</div>';
  }

  innerEl.innerHTML = html;
  resultsEl.scrollIntoView({ behavior: "smooth", block: "start" });

  /* Matrix reveal sul prompt master */
  var masterEl = document.getElementById("masterPromptEl");
  if (masterEl && masterPrompt !== "[your subject]") {
    masterEl.textContent = "";
    matrixReveal(masterPrompt, masterEl, 500);
  }
} /* fine _doSearch */

/* Init — version stamp: resetta localStorage se build cambiata */
(function(){
  if (localStorage.getItem("_sc_v") !== "smf-13") {
    localStorage.removeItem("_sc_p");
    localStorage.removeItem("_sc_rd");
    localStorage.removeItem("_sc_rc");
    localStorage.setItem("_sc_v", "smf-13");
  }
})();
updateBadge();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"Lettura {SREF_JSON} ...")
    data: list[dict] = json.loads(SREF_JSON.read_text(encoding="utf-8"))
    print(f"  {len(data)} entry caricate.")

    print("Arricchimento tag ...")
    enriched = enrich(data)

    # Report copertura tagging
    total = len(enriched)
    geo_counts: dict[str, int] = {}
    tag_counts: dict[str, dict[str, int]] = {
        "style": {}, "subject": {}, "mood": {}, "palette": {}
    }
    zero_counts = {"style": 0, "subject": 0, "mood": 0, "palette": 0}
    for e in enriched:
        geo_counts[e["geo"]] = geo_counts.get(e["geo"], 0) + 1
        for dim, field in [("style","style_tags"),("subject","subject_tags"),
                           ("mood","mood_tags"),("palette","palette_tags")]:
            tags = e[field]
            if not tags:
                zero_counts[dim] += 1
            for t in tags:
                tag_counts[dim][t] = tag_counts[dim].get(t, 0) + 1
    print("  Distribuzione geo:")
    for g, c in sorted(geo_counts.items(), key=lambda x: -x[1]):
        print(f"    {g:20s} {c:5d}")
    print()
    for dim in ["style", "subject", "mood", "palette"]:
        z = zero_counts[dim]
        print(f"  {dim.upper():8s}: {total-z}/{total} con tag ({100*(total-z)/total:.1f}%) | top 5: " +
              ", ".join(f"{k}={v}" for k,v in sorted(tag_counts[dim].items(), key=lambda x:-x[1])[:5]))

    # Slim: rimuove campi non necessari al browser
    slim_data = [slim(e) for e in enriched]

    # Crittografia AES-256-GCM
    print("[PASSO] Crittografia AES-256-GCM...")
    json_b64 = encrypt_json_aes256(slim_data, MASTER_KEY)
    print(f"  Criptato: {len(json_b64):,} caratteri")
    print("Generazione HTML ...")

    # Codici premium (base64 nel JS) — esclusi quelli blacklistati
    active_codes = [c for c in PREMIUM_CODES_PLAIN if c not in BLACKLISTED_CODES]
    codes_b64 = [base64.b64encode(c.encode()).decode() for c in active_codes]
    codes_js  = json.dumps(codes_b64)

    html = HTML_TEMPLATE.replace("###DATA###", json_b64).replace("###CODES###", codes_js)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    size_kb = OUTPUT_HTML.stat().st_size / 1024
    print(f"  Scritto: {OUTPUT_HTML}  ({size_kb:.0f} KB)")
    print(f"  Codici attivi: {len(codes_b64)}  (blacklist: {len(BLACKLISTED_CODES)})")

    # Genera file TXT con tutti i codici attivazione
    today_str = datetime.date.today().strftime("%d/%m/%Y")
    lines = [
        "SrefMindForge — Codici Attivazione PRO",
        f"Generati il: {today_str}",
        f"Scadenza:    {EXPIRY_DATE}",
        "=" * 50,
        "",
    ]
    for i, code in enumerate(PREMIUM_CODES_PLAIN, 1):
        lines.append(f"  {i:3d}.  {code}")
    lines += ["", "=" * 50, "CIANOAI — uso interno, non distribuire questo file.", ""]
    OUTPUT_CODES.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Codici TXT: {OUTPUT_CODES}  ({len(PREMIUM_CODES_PLAIN)} codici)")
    print("FATTO.")


if __name__ == "__main__":
    main()

