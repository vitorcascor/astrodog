import matplotlib.image as mpimg

# --- Constantes Astrológicas ---
PLANET_SYMBOLS_PATHS = {
    'Sun': 'imagens/planeta-velka-bila-slunce.png',
    'Moon': 'imagens/planeta-velka-bila-luna.png',
    'Mercury': 'imagens/planeta-velka-bila-merkur.png',
    'Venus': 'imagens/planeta-velka-bila-venuse.png',
    'Mars': 'imagens/planeta-velka-bila-mars.png',
    'Jupiter': 'imagens/planeta-velka-bila-jupiter.png',
    'Saturn': 'imagens/planeta-velka-bila-saturn.png',
    'Uranus': 'imagens/planeta-velka-bila-uran.png',
    'Neptune': 'imagens/planeta-velka-bila-neptun.png',
    'Pluto': 'imagens/planeta-velka-bila-pluto.png'
}

ADDITIONAL_POINT_SYMBOLS_PATHS = {
    'Fortune': 'imagens/planeta-velka-barevna-bstesti.png',
    'True Node': 'imagens/planeta-velka-bila-uzel.png',
    'True Node South': 'imagens/planeta-velka-bila-uzel-south.png',
}

# Combine all symbol paths for pre-loading images
ALL_POINT_IMAGES = {}
for point_name, image_path in {**PLANET_SYMBOLS_PATHS, **ADDITIONAL_POINT_SYMBOLS_PATHS}.items():
    try:
        ALL_POINT_IMAGES[point_name] = mpimg.imread(image_path)
    except FileNotFoundError:
        print(f"Warning: Image not found for {point_name} at {image_path}. Using text symbol.")
        ALL_POINT_IMAGES[point_name] = None # Mark as not found

SIGN_UNICODE_SYMBOLS = {
    'Aries': '♈', 'Taurus': '♉', 'Gemini': '♊', 'Cancer': '♋', 'Leo': '♌', 'Virgo': '♍',
    'Libra': '♎', 'Scorpio': '♏', 'Sagittarius': '♐', 'Capricorn': '♑', 'Aquarius': '♒', 'Pisces': '♓'
}

PLANET_UNICODE_SYMBOLS = {
    'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂',
    'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇',
    'Fortune': '⊗', 'True Node': '☊', 'True Node South': '☋'
}

NATAL_POINTS_CALCULABLE = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter',
                 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'True Node']
HORARY_POINTS_CALCULABLE = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter',
                  'Saturn', 'True Node']

RETROGRADE_PLANETS = ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

ELEMENT_COLORS = {
    'Fire': 'red', 'Earth': 'green', 'Air': '#eb8204', 'Water': 'blue'
}

SIGN_ELEMENTS = {
    'Aries': 'Fire', 'Leo': 'Fire', 'Sagittarius': 'Fire',
    'Taurus': 'Earth', 'Virgo': 'Earth', 'Capricorn': 'Earth',
    'Gemini': 'Air', 'Libra': 'Air', 'Aquarius': 'Air',
    'Cancer': 'Water', 'Scorpio': 'Water', 'Pisces': 'Water'
}

# --- Configurações de Plotagem ---
IMAGE_CENTER_R = 0.90
DEGREE_TEXT_R = 0.80
MINUTES_TEXT_R = 0.72
RETROGRADE_TEXT_R = 0.85

POINT_TICK_R_OUTER = 1.0
POINT_TICK_R_INNER = 0.98
POINT_TICK_LINEWIDTH = 1.5
POINT_TICK_LINESTYLE = '-'

POINT_TICK_R_OUTER_INNER_CIRCLE = 0.55
POINT_TICK_R_INNER_CIRCLE = 0.53

ANGULAR_OVERLAP_THRESHOLD_DEGREES = 4.0
ANGULAR_OFFSET_STEP_DEGREES = 4.0

DEGREE_TEXT_FONTSIZE = 10
MINUTES_TEXT_FONTSIZE = 8
RETROGRADE_TEXT_FONTSIZE = 9

HOUSE_NUMBER_R = 0.6
SIGN_LINE_R_INNER = 1
SIGN_LINE_R_OUTER = 1.05
ASPECT_RADIAL_POS = 0.53