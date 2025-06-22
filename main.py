import swisseph as swe
import datetime
import pytz
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# =============================================================================
# CONSTANTES ASTROLÓGICAS (Mantidas do seu código original)
# =============================================================================
planet_symbols = {
    'Sun': '☉',      # Sol
    'Moon': '☽',     # Lua
    'Mercury': '☿',  # Mercúrio
    'Venus': '♀',    # Vênus
    'Mars': '♂',     # Marte
    'Jupiter': '♃',  # Júpiter
    'Saturn': '♄',   # Saturno
    'Uranus': '♅',   # Urano
    'Neptune': '♆',  # Netuno
    'Pluto': '♇'     # Plutão
}

sign_unicode_symbols = {
    'Aries': '♈',
    'Taurus': '♉',
    'Gemini': '♊',
    'Cancer': '♋',
    'Leo': '♌',
    'Virgo': '♍',
    'Libra': '♎',
    'Scorpio': '♏',
    'Sagittarius': '♐',
    'Capricorn': '♑',
    'Aquarius': '♒',
    'Pisces': '♓'
}

planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter',
           'Saturn', 'Uranus', 'Neptune', 'Pluto']

signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

# =============================================================================
# FUNÇÃO PARA CALCULAR E PLOTAR O MAPA ASTRAL (adaptada para a GUI)
# =============================================================================
def plot_astral_chart(date_str, time_str, location_input_str):
    # 1. Geocodificação: Obter Lat/Lon/Timezone
    geolocator = Nominatim(user_agent="astral_chart_app")
    tf = TimezoneFinder()

    try:
        location = geolocator.geocode(location_input_str)
        if not location:
            messagebox.showerror("Erro de Localização", f"Não foi possível encontrar a localização para: '{location_input_str}'. Verifique a ortografia ou tente ser mais específico (ex: 'Paris, France').")
            return

        latitude = location.latitude
        longitude = location.longitude
        timezone_id = tf.timezone_at(lng=longitude, lat=latitude)

        if not timezone_id:
            messagebox.showwarning("Fuso Horário", "Não foi possível determinar o fuso horário para a localização. Usando UTC por padrão.")
            timezone_id = "UTC"

    except Exception as e:
        messagebox.showerror("Erro de Geocodificação", f"Ocorreu um erro ao buscar a localização: {e}")
        return

    # 2. Processamento de Data e Hora (como no seu código)
    try:
        birth_date = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        timezone = pytz.timezone(timezone_id)
        birth_date = timezone.localize(birth_date)
        utc_birth_date = birth_date.astimezone(pytz.utc)
    except ValueError:
        messagebox.showerror("Erro de Data/Hora", "Formato de data ou hora inválido. Use AAAA-MM-DD e HH:MM.")
        return
    except pytz.UnknownTimeZoneError:
        messagebox.showwarning("Fuso Horário", "Fuso horário inválido. Usando UTC por padrão.")
        timezone = pytz.utc
        birth_date = timezone.localize(birth_date)
        utc_birth_date = birth_date.astimezone(pytz.utc)

    jd = swe.julday(utc_birth_date.year, utc_birth_date.month, utc_birth_date.day,
                    utc_birth_date.hour + utc_birth_date.minute / 60.0)

    # =============================================================================
    # CÁLCULO DAS POSIÇÕES PLANETÁRIAS (Mantido do seu código)
    # =============================================================================
    planet_positions = []
    for i, name in enumerate(planets):
        xx = swe.calc_ut(jd, i, swe.FLG_SWIEPH)[0]
        lon = xx[0]
        planet_positions.append({'name': name, 'lon': lon})

    # =============================================================================
    # ANÁLISE E DESENHO DE ASPECTOS (Mantido do seu código)
    # =============================================================================
    def get_aspect_info(lon1, lon2, orb=8):
        aspects = {
            "Conjunction": (0, 'red'),
            "Opposition": (180, 'red'),
            "Trine": (120, '#008000'),
            "Square": (90, 'red'),
            "Sextile": (60, '#008000'),
        }

        diff = abs(lon1 - lon2)
        if diff > 180:
            diff = 360 - diff

        for aspect_name, (angle, color) in aspects.items():
            if abs(diff - angle) <= orb:
                return aspect_name, color
        return None

    aspect_lines_info = []
    for i in range(len(planet_positions)):
        for j in range(i + 1, len(planet_positions)):
            name1 = planet_positions[i]['name']
            lon1 = planet_positions[i]['lon']
            name2 = planet_positions[j]['name']
            lon2 = planet_positions[j]['lon']

            aspect_info = get_aspect_info(lon1, lon2)
            if aspect_info:
                aspect_name, color = aspect_info
                aspect_lines_info.append({'planet1': name1, 'planet2': name2, 'color': color})

    # =============================================================================
    # SISTEMA DE CASAS (PLACIDUS) (Mantido do seu código)
    # =============================================================================
    houses, ascmc = swe.houses(jd, latitude, longitude, b'P')

    asc = ascmc[0]
    mc = ascmc[1]

    # =============================================================================
    # VISUALIZAÇÃO GRÁFICA - MAPA ASTROLÓGICO (Mantido do seu código)
    # =============================================================================
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})

    ax.set_theta_direction(1)
    theta_offset_degrees = (180 - asc + 360) % 360
    ax.set_theta_offset(np.radians(theta_offset_degrees))

    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.grid(False)

    # Configurações de posição e espaçamento
    planet_symbol_r = 0.90
    degree_text_r = 0.80

    # AJUSTES PARA O TRAÇO DOS PLANETAS
    planet_tick_r_outer = 1.0
    planet_tick_r_inner = 0.98
    planet_tick_linewidth = 1.5
    planet_tick_linestyle = '-'

    # Para o ajuste angular (lateral)
    angular_overlap_threshold_degrees = 4.0
    angular_offset_step_degrees = 4.0

    # Tamanhos das fontes
    planet_symbol_fontsize = 16
    degree_text_fontsize = 10

    # Reorganiza planetas para calcular ajustes de sobreposição angular
    processed_planets_drawing_info = []
    sorted_planets = sorted(planet_positions, key=lambda p: p['lon'])

    # Lógica para aplicar offsets angulares
    occupied_angular_slots = []

    for p_data in sorted_planets:
        original_lon = p_data['lon']
        current_lon_adjusted = original_lon

        found_slot = False
        max_iterations = 30
        iteration = 0

        while not found_slot and iteration < max_iterations:
            potential_lon_min = (current_lon_adjusted - (angular_overlap_threshold_degrees / 2)) % 360
            potential_lon_max = (current_lon_adjusted + (angular_overlap_threshold_degrees / 2)) % 360

            is_overlapping = False
            for occupied_lon_min, occupied_lon_max, occupied_center_lon in occupied_angular_slots:
                if (potential_lon_min < occupied_lon_max and potential_lon_max > occupied_lon_min) or \
                   (occupied_lon_min < potential_lon_max and occupied_lon_max > potential_lon_min):
                    is_overlapping = True
                    break

                if potential_lon_min > potential_lon_max and \
                   ((potential_lon_min <= occupied_lon_max and occupied_lon_max <= 360) or \
                    (0 <= occupied_lon_min and occupied_lon_min <= potential_lon_max)):
                    is_overlapping = True
                    break

                if occupied_lon_min > occupied_lon_max and \
                   ((occupied_lon_min <= potential_lon_max and potential_lon_max <= 360) or \
                    (0 <= potential_lon_min and potential_lon_min <= occupied_lon_max)):
                    is_overlapping = True
                    break

            if is_overlapping:
                current_lon_adjusted = (current_lon_adjusted + angular_offset_step_degrees) % 360
            else:
                found_slot = True
                occupied_angular_slots.append((potential_lon_min, potential_lon_max, current_lon_adjusted))

            iteration += 1

        if not found_slot:
            print(f"Aviso: Não foi possível encontrar um slot livre para {p_data['name']}. Usando a última posição calculada.")

        processed_planets_drawing_info.append({
            'name': p_data['name'],
            'original_lon': original_lon,
            'adjusted_lon': current_lon_adjusted,
        })

    planet_plot_info_map = {p['name']: p for p in processed_planets_drawing_info}

    # Desenha cúspides das casas (linhas divisórias)
    for cusp_lon in houses:
        angle = np.radians(cusp_lon)
        ax.plot([angle, angle], [0.0, 1.0], color='black', linestyle='-', linewidth=1.5)

    # Desenha círculo externo (zodíaco)
    circle_outer = plt.Circle((0, 0), 1.0, transform=ax.transData._b, fill=False, color='black', linewidth=1.5)
    ax.add_artist(circle_outer)

    # Desenha o círculo interno (representando o centro do mapa) mais forte
    circle_inner = plt.Circle((0, 0), 0.5, transform=ax.transData._b, fill=False, color='black', linewidth=1.5)
    ax.add_artist(circle_inner)

    # Escrever o número de cada casa no centro angular entre cúspides
    house_number_r = 0.4

    for i in range(12):
        cusp_start = houses[i]
        cusp_end = houses[(i + 1) % 12]

        if cusp_end < cusp_start:
            cusp_end += 360

        house_center_lon = (cusp_start + cusp_end) / 2 % 360
        angle_center = np.radians(house_center_lon)

        ax.text(angle_center, house_number_r, str(i + 1),
                fontsize=14, ha='center', va='center', weight='bold')

    # === DESENHO DAS DIVISÕES DOS SIGNOS E SEUS SÍMBOLOS ===
    sign_line_r_inner = 1
    sign_line_r_outer = 1.03

    for i in range(12):
        sign_start_lon = i * 30
        angle_start = np.radians(sign_start_lon)

        ax.plot([angle_start, angle_start], [sign_line_r_inner, sign_line_r_outer],
                color='black', linewidth=1.0)

        sign_center_lon = sign_start_lon + 15
        angle_center = np.radians(sign_center_lon)
        sign_name = signs[i]
        sign_sym = sign_unicode_symbols.get(sign_name, '?')
        ax.text(angle_center, 1.040, sign_sym, fontsize=18, ha='center', va='center', weight='bold')

    # === DESENHO DOS PLANETAS COM AJUSTES ANGULARES E TRAÇOS ===
    for p_info in processed_planets_drawing_info:
        planet_name = p_info['name']
        original_lon = p_info['original_lon']
        adjusted_lon = p_info['adjusted_lon']

        original_angle = np.radians(original_lon)
        ax.plot([original_angle, original_angle], [planet_tick_r_inner, planet_tick_r_outer],
                color='black', linewidth=planet_tick_linewidth, linestyle=planet_tick_linestyle)

        adjusted_angle = np.radians(adjusted_lon)
        planet_symbol = planet_symbols.get(planet_name, '?')

        ax.text(adjusted_angle, planet_symbol_r, planet_symbol,
                fontsize=planet_symbol_fontsize, ha='center', va='center', weight='bold')

        degree_decimal = original_lon % 30
        degrees = int(degree_decimal)
        minutes = int((degree_decimal - degrees) * 60)

        degree_text = f"{degrees}°{minutes:02d}'"

        ax.text(adjusted_angle, degree_text_r, degree_text,
                fontsize=degree_text_fontsize, ha='center', va='center')

    # =============================================================================
    # DESENHO DAS LINHAS DE ASPECTO (Mantido do seu código)
    # =============================================================================
    for aspect_info in aspect_lines_info:
        name1 = aspect_info['planet1']
        name2 = aspect_info['planet2']
        color = aspect_info['color']

        lon1 = next(p for p in processed_planets_drawing_info if p['name'] == name1)['original_lon']
        lon2 = next(p for p in processed_planets_drawing_info if p['name'] == name2)['original_lon']

        angle1 = np.radians(lon1)
        angle2 = np.radians(lon2)

        aspect_radial_pos = (planet_tick_r_inner + circle_inner.radius) / 2
        ax.plot([angle1, angle2], [aspect_radial_pos, aspect_radial_pos],
                color=color, linewidth=1.5, linestyle='-')

    # =============================================================================
    # FINALIZAÇÃO E EXIBIÇÃO
    # =============================================================================
    plt.title(f"Mapa Astral para {birth_date.strftime('%Y-%m-%d %H:%M')} em {location_input_str}", y=1.08, fontsize=14)
    plt.tight_layout()
    plt.show()

# =============================================================================
# INTERFACE GRÁFICA (Tkinter)
# =============================================================================
def create_gui():
    def on_calculate():
        date_input = date_entry.get()
        time_input = time_entry.get()
        location_input = location_entry.get()

        if not all([date_input, time_input, location_input]):
            messagebox.showwarning("Entrada Inválida", "Por favor, preencha todos os campos.")
            return

        plot_astral_chart(date_input, time_input, location_input)

    root = tk.Tk()
    root.title("Calculadora de Mapa Astral")
    root.geometry("400x250") # Ajusta o tamanho da janela
    root.resizable(False, False)

    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Estilos (opcional, para uma aparência mais moderna)
    style = ttk.Style()
    style.configure("TLabel", font=("Arial", 10))
    style.configure("TEntry", font=("Arial", 10))
    style.configure("TButton", font=("Arial", 10, "bold"))

    # Labels e Entradas
    ttk.Label(main_frame, text="Data (AAAA-MM-DD):").grid(row=0, column=0, sticky=tk.W, pady=5)
    date_entry = ttk.Entry(main_frame, width=30)
    date_entry.grid(row=0, column=1, pady=5)
    date_entry.insert(0, "2003-08-15") # Valor padrão para teste

    ttk.Label(main_frame, text="Hora (HH:MM):").grid(row=1, column=0, sticky=tk.W, pady=5)
    time_entry = ttk.Entry(main_frame, width=30)
    time_entry.grid(row=1, column=1, pady=5)
    time_entry.insert(0, "21:30") # Valor padrão para teste

    ttk.Label(main_frame, text="Local de Nascimento (Cidade, País):").grid(row=2, column=0, sticky=tk.W, pady=5)
    location_entry = ttk.Entry(main_frame, width=30)
    location_entry.grid(row=2, column=1, pady=5)
    location_entry.insert(0, "Rio de Janeiro, Brazil") # Valor padrão para teste

    # Botão de Cálculo
    calculate_button = ttk.Button(main_frame, text="Gerar Mapa Astral", command=on_calculate)
    calculate_button.grid(row=3, column=0, columnspan=2, pady=20)

    # Configurar pesos das colunas e linhas para centralização
    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    for i in range(4): # Agora temos 4 linhas de widgets
        main_frame.rowconfigure(i, weight=1)

    root.mainloop()

if __name__ == "__main__":
    create_gui()