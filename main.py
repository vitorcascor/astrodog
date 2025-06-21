import swisseph as swe
import datetime
import pytz
import matplotlib.pyplot as plt
import numpy as np

# Entrada de dados do usuário
date_input = "2003-08-15"
time_input = "21:30"
timezone_input = "America/Sao_Paulo"
latitude = float(-22.9035)
longitude = float(-43.2096)

# Parse da data e hora
birth_date = datetime.datetime.strptime(f"{date_input} {time_input}", "%Y-%m-%d %H:%M")

# Timezone
try:
    timezone = pytz.timezone(timezone_input)
except pytz.UnknownTimeZoneError:
    print("Timezone inválida. Usando UTC por padrão.")
    timezone = pytz.utc

birth_date = timezone.localize(birth_date)
utc_birth_date = birth_date.astimezone(pytz.utc)

# Dia Juliano
jd = swe.julday(utc_birth_date.year, utc_birth_date.month, utc_birth_date.day,
                utc_birth_date.hour + utc_birth_date.minute / 60.0)

# Constantes
planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter',
           'Saturn', 'Uranus', 'Neptune', 'Pluto']
signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

print(f"\nMapa astral para {birth_date} (UTC: {utc_birth_date})\n")

# Cálculo dos planetas
planet_positions = []
for i, name in enumerate(planets):
    # swe.calc_ut retorna uma tupla, pegamos os primeiros 3 elementos do primeiro item
    # para longitude, latitude e distância.
    lon, lat, dist = swe.calc_ut(jd, i, swe.FLG_SWIEPH)[0][:3]
    sign_index = int(lon // 30)
    degree_in_sign = lon % 30
    sign_name = signs[sign_index]
    planet_positions.append((name, lon))
    print(f"{name}: {degree_in_sign:.2f}° {sign_name}")

# Aspectos (mantido do seu código original)
def get_aspect(lon1, lon2, orb=8):
    aspects = {
        "Conjunction": 0,
        "Opposition": 180,
        "Trine": 120,
        "Square": 90,
    }
    diff = abs(lon1 - lon2)
    if diff > 180:
        diff = 360 - diff
    for aspect, angle in aspects.items():
        if abs(diff - angle) <= orb:
            return aspect
    return None

print("\nAspectos encontrados:")
for i in range(len(planet_positions)):
    for j in range(i + 1, len(planet_positions)):
        name1, lon1 = planet_positions[i]
        name2, lon2 = planet_positions[j]
        aspect = get_aspect(lon1, lon2)
        if aspect:
            print(f"{name1} {aspect} {name2}")

# Sistema de casas (Placidus)
# Certifique-se de que longitude seja um float ou int, não uma string, para swe.houses
houses, ascmc = swe.houses(jd, latitude, longitude, b'P')

print("\nCúspides das Casas (Placidus):")
for i in range(12):
    # as casas retornadas por swe.houses já estão em 0-360 graus para cada cúspide
    sign_index = int(houses[i] // 30)
    degree_in_sign = houses[i] % 30
    print(f"Casa {i+1}: {degree_in_sign:.2f}° {signs[sign_index]}")

# Ascendente e Meio-do-Céu
asc = ascmc[0] # Ascendente
mc = ascmc[1]  # Meio do Céu
asc_sign = signs[int(asc // 30)]
mc_sign = signs[int(mc // 30)]

print(f"\nAscendente: {asc % 30:.2f}° {asc_sign}")
print(f"Meio-do-Céu (MC): {mc % 30:.2f}° {mc_sign}")

# --- Configurações do gráfico polar ---
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})

# 1. Definir a direção do theta para sentido anti-horário (astrológico)
ax.set_theta_direction(1)

# 2. Calcular o offset para que o Ascendente fique na posição das 9 horas (270 graus)
# O Ascendente deve ser mapeado para 270 graus no gráfico polar.
# Se `asc` é a longitude do Ascendente (0-360), o offset é a diferença necessária.
# Ex: Se asc = 0 (Aries), queremos que 0 graus vá para 270 graus no plot. Offset = 270.
# Ex: Se asc = 90 (Cancer), queremos que 90 graus vá para 270 graus no plot. Offset = 180.
# theta_offset = (270 - asc + 360) % 360
theta_offset_degrees = (180 - asc + 360) % 360
ax.set_theta_offset(np.radians(theta_offset_degrees))


ax.set_yticklabels([]) # Remove rótulos de raio
ax.set_xticklabels([]) # Remove rótulos de ângulo padrão

# Desenhar cúspides das casas
# Aplicamos o offset aos ângulos das cúspides para alinhá-los corretamente
for cusp_lon in houses:
    # O ângulo no gráfico é o ângulo da cúspide mais o offset, convertido para radianos
    angle = np.radians(cusp_lon)
    ax.plot([angle, angle], [0.0, 1.0], color='gray', linestyle='--', linewidth=0.8)

# Desenhar os planetas
for planet, lon in planet_positions:
    # O ângulo do planeta no gráfico é a longitude do planeta
    angle = np.radians(lon)
    # Posição radial do planeta
    r_pos = 0.75 # Ajuste conforme necessário
    ax.plot(angle, r_pos, 'o', color='blue', markersize=6)
    # Adicionar o nome do planeta
    ax.text(angle, r_pos + 0.05, planet, fontsize=8, ha='center', va='center')


# Desenhar o círculo externo (zodíaco)
circle = plt.Circle((0, 0), 1.0, transform=ax.transData._b, fill=False, color='black', linewidth=1.5)
ax.add_artist(circle)

# Desenhar divisões e rótulos dos signos
# Vamos desenhar linhas a cada 30 graus para os signos
for i in range(12):
    sign_start_lon = i * 30
    angle_start = np.radians(sign_start_lon)
    # Desenha a linha divisória do signo
    ax.plot([angle_start, angle_start], [0.95, 1.0], color='black', linewidth=0.5)

    # Adiciona o nome do signo no centro do seu setor de 30 graus
    sign_center_lon = sign_start_lon + 15
    angle_center = np.radians(sign_center_lon)
    ax.text(angle_center, 1.05, signs[i], fontsize=9, ha='center', va='center')


# Exibir gráfico
plt.title("Mapa Astral (Visual)", y=1.08, fontsize=14)
plt.tight_layout()
plt.show()