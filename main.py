import swisseph as swe
import datetime
import pytz

# Perguntar ao usuário a data de nascimento
date_input = input("Digite sua data de nascimento (AAAA-MM-DD): ")
time_input = input("Digite seu horário de nascimento (HH:MM, 24h): ")
timezone_input = input("Digite sua timezone (ex: America/Sao_Paulo): ")

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

# Converter para dia juliano
jd = swe.julday(utc_birth_date.year, utc_birth_date.month, utc_birth_date.day,
                utc_birth_date.hour + utc_birth_date.minute / 60.0)

# Planetas
planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter',
           'Saturn', 'Uranus', 'Neptune', 'Pluto']

print(f"\nMapa astral para {birth_date} (UTC: {utc_birth_date})\n")

signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

# Exibir posições dos planetas
planet_positions = []
for i, name in enumerate(planets):
    lon, lat, dist = swe.calc_ut(jd, i)[0][:3]
    sign_index = int(lon // 30)
    degree_in_sign = lon % 30
    sign_name = signs[sign_index]
    planet_positions.append((name, lon))
    print(f"{name}: {degree_in_sign:.2f}° {sign_name}")

# Função para calcular aspectos
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

# Verificar aspectos
print("\nAspectos encontrados:")
for i in range(len(planet_positions)):
    for j in range(i + 1, len(planet_positions)):
        name1, lon1 = planet_positions[i]
        name2, lon2 = planet_positions[j]
        aspect = get_aspect(lon1, lon2)
        if aspect:
            print(f"{name1} {aspect} {name2}")
