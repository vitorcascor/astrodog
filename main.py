import swisseph as swe
import datetime
import pytz

# Entrada de dados do usuário
date_input = input("Digite sua data de nascimento (AAAA-MM-DD): ")
time_input = input("Digite seu horário de nascimento (HH:MM, 24h): ")
timezone_input = input("Digite sua timezone (ex: America/Sao_Paulo): ")
latitude = float(input("Digite sua latitude (ex: -22.9035): "))
longitude = float(input("Digite sua longitude (ex: -43.2096): "))

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
    lon, lat, dist = swe.calc_ut(jd, i)[0][:3]
    sign_index = int(lon // 30)
    degree_in_sign = lon % 30
    sign_name = signs[sign_index]
    planet_positions.append((name, lon))
    print(f"{name}: {degree_in_sign:.2f}° {sign_name}")

# Aspectos
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
houses, ascmc = swe.houses(jd, latitude, longitude.encode() if isinstance(longitude, str) else longitude, b'P')

print("\nCúspides das Casas (Placidus):")
for i in range(12):
    sign_index = int(houses[i] // 30)
    degree_in_sign = houses[i] % 30
    print(f"Casa {i+1}: {degree_in_sign:.2f}° {signs[sign_index]}")

# Ascendente e Meio-do-Céu
asc = ascmc[0]
mc = ascmc[1]
asc_sign = signs[int(asc // 30)]
mc_sign = signs[int(mc // 30)]

print(f"\nAscendente: {asc % 30:.2f}° {asc_sign}")
print(f"Meio-do-Céu (MC): {mc % 30:.2f}° {mc_sign}")
