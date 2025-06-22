import swisseph as swe
import datetime
import pytz
import matplotlib.pyplot as plt
import numpy as np

# =============================================================================
# CONFIGURAÇÃO INICIAL - Dados de nascimento
# =============================================================================
date_input = "2003-08-15"
time_input = "21:30"
timezone_input = "America/Sao_Paulo"
latitude = float(-22.9035)  # Rio de Janeiro
longitude = float(-43.2096)  # Rio de Janeiro

# =============================================================================
# PROCESSAMENTO DE DATA E HORA
# =============================================================================
# Converte string de data/hora para objeto datetime
birth_date = datetime.datetime.strptime(f"{date_input} {time_input}", "%Y-%m-%d %H:%M")

# Configura timezone com fallback para UTC
try:
    timezone = pytz.timezone(timezone_input)
except pytz.UnknownTimeZoneError:
    print("Timezone inválida. Usando UTC por padrão.")
    timezone = pytz.utc

# Aplica timezone local e converte para UTC
birth_date = timezone.localize(birth_date)
utc_birth_date = birth_date.astimezone(pytz.utc)

# Calcula Dia Juliano (formato usado pela Swiss Ephemeris)
jd = swe.julday(utc_birth_date.year, utc_birth_date.month, utc_birth_date.day,
                utc_birth_date.hour + utc_birth_date.minute / 60.0)

# =============================================================================
# CONSTANTES ASTROLÓGICAS
# =============================================================================
planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter',
           'Saturn', 'Uranus', 'Neptune', 'Pluto']
signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

print(f"\nMapa astral para {birth_date} (UTC: {utc_birth_date})\n")

# =============================================================================
# CÁLCULO DAS POSIÇÕES PLANETÁRIAS
# =============================================================================
planet_positions = []
for i, name in enumerate(planets):
    lon, lat, dist = swe.calc_ut(jd, i, swe.FLG_SWIEPH)[0][:3]
    sign_index = int(lon // 30)
    degree_in_sign = lon % 30
    sign_name = signs[sign_index]
    
    # Armazena a posição do planeta para uso posterior no gráfico
    planet_positions.append((name, lon))
    print(f"{name}: {degree_in_sign:.2f}° {sign_name}")

# =============================================================================
# ANÁLISE E DESENHO DE ASPECTOS
# =============================================================================
def get_aspect_info(lon1, lon2, orb=8):
    """
    Determina o aspecto entre duas longitudes e a cor da linha.
    
    Args:
        lon1, lon2: Longitudes dos planetas (0-360°)
        orb: Orbe permitido para o aspecto (padrão: 8°)
    
    Returns:
        Tupla (nome_aspecto, cor_linha) ou None se não houver aspecto
    """
    # Adicionando Sextil (60°)
    aspects = {
        "Conjunction": (0, 'red'),      # Conjunção
        "Opposition": (180, 'red'),     # Oposição
        "Trine": (120, 'blue'),         # Trino
        "Square": (90, 'red'),          # Quadratura
        "Sextile": (60, 'blue'),        # Sextil (adicionado)
    }
    
    diff = abs(lon1 - lon2)
    if diff > 180:
        diff = 360 - diff
    
    for aspect_name, (angle, color) in aspects.items():
        if abs(diff - angle) <= orb:
            return aspect_name, color
    return None

print("\nAspectos encontrados:")
# Lista para armazenar informações dos aspectos para desenhar as linhas
aspect_lines_info = []

for i in range(len(planet_positions)):
    for j in range(i + 1, len(planet_positions)):
        name1, lon1 = planet_positions[i]
        name2, lon2 = planet_positions[j]
        
        aspect_info = get_aspect_info(lon1, lon2)
        if aspect_info:
            aspect_name, color = aspect_info
            print(f"{name1} {aspect_name} {name2}")
            # Armazena as longitudes dos planetas e a cor da linha
            aspect_lines_info.append((lon1, lon2, color))

# =============================================================================
# SISTEMA DE CASAS (PLACIDUS)
# =============================================================================
houses, ascmc = swe.houses(jd, latitude, longitude, b'P')

print("\nCúspides das Casas (Placidus):")
for i in range(12):
    sign_index = int(houses[i] // 30)
    degree_in_sign = houses[i] % 30
    print(f"Casa {i+1}: {degree_in_sign:.2f}° {signs[sign_index]}")

# Extrai Ascendente e Meio-do-Céu
asc = ascmc[0]
mc = ascmc[1]
asc_sign = signs[int(asc // 30)]
mc_sign = signs[int(mc // 30)]

print(f"\nAscendente: {asc % 30:.2f}° {asc_sign}")
print(f"Meio-do-Céu (MC): {mc % 30:.2f}° {mc_sign}")

# =============================================================================
# VISUALIZAÇÃO GRÁFICA - MAPA ASTROLÓGICO
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})

ax.set_theta_direction(1) # Sentido anti-horário

# Ajuste do offset para que o Ascendente (Casa 1) esteja à esquerda (270 graus)
# Testando com 180 - asc, que funciona bem para a maioria dos casos para alinhar Aries no topo
# e o Ascendente à esquerda.
theta_offset_degrees = (180 - asc + 360) % 360 
ax.set_theta_offset(np.radians(theta_offset_degrees))


ax.set_yticklabels([])
ax.set_xticklabels([])

# =============================================================================
# DESENHO DOS ELEMENTOS DO MAPA
# =============================================================================
# Desenha cúspides das casas
for cusp_lon in houses:
    angle = np.radians(cusp_lon)
    ax.plot([angle, angle], [0.0, 1.0], color='black', linestyle='--', linewidth=0.8)

# Desenha planetas e seus rótulos
planet_r_pos = 0.75 # Posição radial dos planetas
for planet, lon in planet_positions:
    angle = np.radians(lon)
    ax.plot(angle, planet_r_pos, 'o', color='blue', markersize=6)
    ax.text(angle, planet_r_pos + 0.05, planet, fontsize=8, ha='center', va='center')

# Desenha círculo externo (zodíaco)
circle = plt.Circle((0, 0), 1.0, transform=ax.transData._b, fill=False, color='black', linewidth=1.5)
ax.add_artist(circle)

# Desenha divisões dos signos e seus rótulos
for i in range(12):
    sign_start_lon = i * 30
    angle_start = np.radians(sign_start_lon)
    ax.plot([angle_start, angle_start], [0.95, 1.0], color='black', linewidth=0.5)
    
    sign_center_lon = sign_start_lon + 15
    angle_center = np.radians(sign_center_lon)
    ax.text(angle_center, 1.05, signs[i], fontsize=9, ha='center', va='center')

# =============================================================================
# DESENHO DAS LINHAS DE ASPECTO (NOVA SEÇÃO)
# =============================================================================
# As linhas de aspecto devem conectar os planetas.
# A posição radial dos planetas é 'planet_r_pos'.
# Você pode ajustar a posição radial das linhas se quiser que elas fiquem mais internas
aspect_line_r_pos = planet_r_pos # Conectando os planetas na mesma linha radial

for lon1, lon2, color in aspect_lines_info:
    angle1 = np.radians(lon1)
    angle2 = np.radians(lon2)
    # Desenha uma linha entre os dois pontos (planetas)
    ax.plot([angle1, angle2], [aspect_line_r_pos, aspect_line_r_pos], color=color, linewidth=1.5, linestyle='-')

# =============================================================================
# FINALIZAÇÃO E EXIBIÇÃO
# =============================================================================
plt.title("Mapa Astral (Visual) com Aspectos", y=1.08, fontsize=14) # Atualiza o título
plt.tight_layout()
plt.show()