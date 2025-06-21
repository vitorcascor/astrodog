import swisseph as swe
import datetime
import pytz
import matplotlib.pyplot as plt
import numpy as np

# Define plotting function
def plot_birth_chart(planet_positions, aspects_found):
    fig, ax = plt.subplots(figsize=(8,8), subplot_kw={'polar': True})
    
    # Aries starts at 0 degrees (top)
    ax.set_theta_zero_location('E')  # East corresponds to 0 radian (you can try 'N' or 'E')
    ax.set_theta_direction(-1)  # clockwise
    
    # Remove grid and labels
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Zodiac sign lines every 30 degrees
    for angle_deg in range(0, 360, 30):
        ax.plot([np.deg2rad(angle_deg), np.deg2rad(angle_deg)], [0, 1], color='gray', lw=1)
    
    # Plot planets on circumference
    for name, lon in planet_positions:
        angle = np.deg2rad(lon)
        ax.plot(angle, 1, 'o', label=name, markersize=10)
        ax.text(angle, 1.1, name, fontsize=12, ha='center', va='center')
    
    # Draw aspects lines inside the circle
    for (p1, p2, aspect) in aspects_found:
        name1, lon1 = p1
        name2, lon2 = p2
        angle1 = np.deg2rad(lon1)
        angle2 = np.deg2rad(lon2)
        
        ax.plot([angle1, angle2], [1, 1], lw=1, alpha=0.7)
    
    plt.title("Birth Chart")
    plt.show()

# Your astrology data functions
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

def calculate_planets_and_aspects(birth_date, timezone_str='America/Sao_Paulo'):
    timezone = pytz.timezone(timezone_str)
    birth_date = timezone.localize(birth_date)
    utc_birth_date = birth_date.astimezone(pytz.utc)

    jd = swe.julday(utc_birth_date.year, utc_birth_date.month, utc_birth_date.day,
                    utc_birth_date.hour + utc_birth_date.minute / 60.0)

    planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter',
               'Saturn', 'Uranus', 'Neptune', 'Pluto']

    planet_positions = []
    for i, name in enumerate(planets):
        lon, lat, dist = swe.calc_ut(jd, i)[0][:3]
        planet_positions.append((name, lon))

    aspects_found = []
    for i in range(len(planet_positions)):
        for j in range(i + 1, len(planet_positions)):
            name1, lon1 = planet_positions[i]
            name2, lon2 = planet_positions[j]
            aspect = get_aspect(lon1, lon2)
            if aspect:
                aspects_found.append(((name1, lon1), (name2, lon2), aspect))
    
    return planet_positions, aspects_found, birth_date, utc_birth_date

# Main code
if __name__ == "__main__":
    birth_date = datetime.datetime(2003, 8, 15, 21, 30)
    planet_positions, aspects_found, local_birth, utc_birth = calculate_planets_and_aspects(birth_date)

    print(f"Birth chart for {local_birth} (UTC: {utc_birth})\n")
    for name, lon in planet_positions:
        degree_in_sign = lon % 30
        sign_index = int(lon // 30)
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        sign_name = signs[sign_index]
        print(f"{name}: {degree_in_sign:.2f}° {sign_name}")

    print("\nAspects found:")
    for (p1, p2, aspect) in aspects_found:
        print(f"{p1[0]} {aspect} {p2[0]}")

    # Plot the chart
    plot_birth_chart(planet_positions, aspects_found)
