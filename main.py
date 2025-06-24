import swisseph as swe
import datetime
import pytz
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# =============================================================================
# CONSTANTES ASTROLÓGICAS
# =============================================================================
planet_symbols = {
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

# Novos pontos astrológicos para imagens (apenas caminhos, as imagens não existem ainda)
# Você pode adicionar os caminhos corretos aqui quando tiver as imagens
additional_point_symbols_paths = {
    'Fortune': 'imagens/roda-da-fortuna.png', # Exemplo de caminho
    'True Node': 'imagens/nodo-norte.png',     # Exemplo de caminho
    'True Node South': 'imagens/nodo-sul.png', # Exemplo de caminho para o Nodo Sul
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

# Add planet unicode symbols for fallback if images are not found
planet_unicode_symbols = {
    'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂',
    'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇',
    'Fortune': '⊗', # Símbolo da Roda da Fortuna
    'True Node': '☊', # Símbolo do Nodo Norte
    'True Node South': '☋' # Símbolo do Nodo Sul
}

# Define planets and additional points for natal and horary charts
# Removi 'True Node South' de NATAL_POINTS_CALCULABLE e HORARY_POINTS_CALCULABLE, pois é derivado
# e será adicionado após o cálculo do True Node. Isso evita cálculo duplicado.
NATAL_POINTS_CALCULABLE = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter',
                 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'True Node']
HORARY_POINTS_CALCULABLE = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter',
                  'Saturn', 'True Node']

# Planetas que podem ser retrógrados (Sol e Lua nunca são considerados retrógrados)
RETROGRADE_PLANETS = ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']

# O limiar de velocidade não é mais usado para a lógica de retrogradação, mas pode ser mantido para outros propósitos.
# Se a velocidade for MENOR que 0 (negativa), será retrógrado.
RETROGRADE_SPEED_THRESHOLD = -0.001 # Mantido apenas como referência, mas não usado na nova lógica de retrogradação.

signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

element_colors = {
    'Fire': 'red',
    'Earth': 'green',
    'Air': '#eb8204', # Orange
    'Water': 'blue'
}

sign_elements = {
    'Aries': 'Fire', 'Leo': 'Fire', 'Sagittarius': 'Fire',
    'Taurus': 'Earth', 'Virgo': 'Earth', 'Capricorn': 'Earth',
    'Gemini': 'Air', 'Libra': 'Air', 'Aquarius': 'Air',
    'Cancer': 'Water', 'Scorpio': 'Water', 'Pisces': 'Water'
}

# Pre-load planet and additional point images
all_point_images = {}
# Load planet images
for planet_name, image_path in planet_symbols.items():
    try:
        all_point_images[planet_name] = mpimg.imread(image_path)
    except FileNotFoundError:
        print(f"Warning: Image not found for {planet_name} at {image_path}. Using text symbol.")
        all_point_images[planet_name] = None # Mark as not found

# Load additional point images (Fortune, True Node, True Node South)
for point_name, image_path in additional_point_symbols_paths.items():
    try:
        all_point_images[point_name] = mpimg.imread(image_path)
    except FileNotFoundError:
        print(f"Warning: Image not found for {point_name} at {image_path}. Using text symbol.")
        all_point_images[point_name] = None # Mark as not found

# Global variables for chart display and details
canvas = None
toolbar = None
fig = None
details_text_widget = None # To hold the Text widget for details tab
notebook = None # Will be defined in create_gui
input_frame = None # Will be defined in create_gui
back_button = None # Will be defined in create_gui

# Helper function to get sign from longitude
def get_sign(longitude):
    sign_index = int(longitude / 30) % 12
    return signs[sign_index]

def get_degree_in_sign(longitude):
    return longitude % 30

# =============================================================================
# FUNÇÃO PARA CALCULAR E PLOTAR O MAPA ASTRAL (adaptada para a GUI)
# =============================================================================
def plot_astral_chart(chart_type, house_system, date_str, time_str, location_input_str, chart_frame, details_frame):
    global canvas, toolbar, fig, details_text_widget

    # Clear previous plot if it exists
    if fig is not None:
        plt.close(fig) # Close the old figure to free memory
        fig = None
    if canvas is not None:
        canvas.get_tk_widget().destroy()
        canvas = None
    if toolbar is not None:
        toolbar.destroy()
        toolbar = None

    # Clear previous details text
    if details_text_widget is not None:
        details_text_widget.config(state=tk.NORMAL)
        details_text_widget.delete(1.0, tk.END)
        details_text_widget.config(state=tk.DISABLED)

    # 1. Geocodificação: Obter Lat/Lon/Timezone
    geolocator = Nominatim(user_agent="astral_chart_app")
    tf = TimezoneFinder()

    try:
        location = geolocator.geocode(location_input_str)
        if not location:
            messagebox.showerror("Erro de Localização", f"Não foi possível encontrar a localização para: '{location_input_str}'. Verifique a ortografia ou tente ser mais específico (ex: 'Paris, France').")
            return None # Return None to indicate failure

        latitude = location.latitude
        longitude = location.longitude
        timezone_id = tf.timezone_at(lng=longitude, lat=latitude)

        if not timezone_id:
            messagebox.showwarning("Fuso Horário", "Não foi possível determinar o fuso horário para a localização. Usando UTC por padrão.")
            timezone_id = "UTC"

    except Exception as e:
        messagebox.showerror("Erro de Geocodificação", f"Ocorreu um erro ao buscar a localização: {e}")
        return None # Return None to indicate failure

    # 2. Processamento de Data e Hora
    try:
        if chart_type == 'natal':
            birth_date = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        elif chart_type == 'horary':
            # Use current time for horary, and get current time for display
            # Ensure the current time is localized to the specified location's timezone
            current_local_time = datetime.datetime.now(pytz.timezone(timezone_id))
            birth_date = current_local_time

            date_str = birth_date.strftime("%Y-%m-%d") # Update date_str for display
            time_str = birth_date.strftime("%H:%M") # Update time_str for display

        utc_birth_date = birth_date.astimezone(pytz.utc)

    except ValueError:
        messagebox.showerror("Erro de Data/Hora", "Formato de data ou hora inválido. Use AAAA-MM-DD e HH:MM.")
        return None # Return None to indicate failure
    except pytz.UnknownTimeZoneError:
        messagebox.showwarning("Fuso Horário", "Fuso horário inválido. Usando UTC por padrão.")
        timezone = pytz.utc
        birth_date = timezone.localize(birth_date.replace(tzinfo=None)) # Remove old tzinfo if present
        utc_birth_date = birth_date.astimezone(pytz.utc)


    jd = swe.julday(utc_birth_date.year, utc_birth_date.month, utc_birth_date.day,
                    utc_birth_date.hour + utc_birth_date.minute / 60.0)

    # =============================================================================
    # CÁLCULO DAS POSIÇÕES PLANETÁRIAS E PONTOS ADICIONAIS
    # =============================================================================
    points_to_calculate_swe = NATAL_POINTS_CALCULABLE if chart_type == 'natal' else HORARY_POINTS_CALCULABLE

    point_positions = []
    # Map planet names to SWISSEPH constants
    swe_points_map = {
        'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
        'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
        'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE,
        'Pluto': swe.PLUTO, 'True Node': swe.MEAN_NODE # Mean Node for Nodal calculations
    }

    # Calculate standard planets/nodes
    for name in points_to_calculate_swe:
        if name in swe_points_map:
            swe_id = swe_points_map.get(name)
            xx = swe.calc_ut(jd, swe_id, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
            lon = xx[0]
            speed = xx[3]  # Correção: índice 3 é a velocidade longitudinal!

            # --- Lógica Simplificada de Retrogradação ---
            is_retrograde = False
            if name in RETROGRADE_PLANETS and speed < 0:
                is_retrograde = True

            point_positions.append({
                'name': name,
                'lon': lon,
                'retrograde': is_retrograde
            })


    # Calculate Part of Fortune separately as it requires Ascendant
    houses, ascmc = swe.houses(jd, latitude, longitude, b'P' if house_system == 'Placidus' else b'R') # Calculate with selected house system

    asc = ascmc[0]
    mc = ascmc[1]

    # Calculate Fortune (using a common formula: Asc + Moon - Sun)
    # Ensure Moon and Sun are already calculated and available in point_positions
    moon_lon = next((p['lon'] for p in point_positions if p['name'] == 'Moon'), None)
    sun_lon = next((p['lon'] for p in point_positions if p['name'] == 'Sun'), None)

    if moon_lon is not None and sun_lon is not None:
        fortune_lon = (asc + moon_lon - sun_lon) % 360
        point_positions.append({'name': 'Fortune', 'lon': fortune_lon, 'retrograde': False}) # Fortune is not retrograde
    else:
        print("Warning: Could not calculate Part of Fortune. Moon or Sun position not found.")

    # Calculate South Node (180 degrees opposite to True Node)
    true_node_lon = next((p['lon'] for p in point_positions if p['name'] == 'True Node'), None)
    if true_node_lon is not None:
        south_node_lon = (true_node_lon + 180) % 360
        point_positions.append({'name': 'True Node South', 'lon': south_node_lon, 'retrograde': False}) # Nodes are not retrograde in this sense
    else:
        print("Warning: Could not calculate South Node. True Node position not found.")


    # =============================================================================
    # ANÁLISE E DESENHO DE ASPECTOS
    # =============================================================================
    def get_aspect_info(lon1, lon2, orb=8):
        aspects = {
            "Conjunção": (0, 'red'),
            "Oposição": (180, 'red'),
            "Trígono": (120, '#008000'), # Green
            "Quadratura": (90, 'red'),
            "Sextil": (60, '#008000'), # Green
        }

        diff = abs(lon1 - lon2)
        if diff > 180:
            diff = 360 - diff

        for aspect_name, (angle, color) in aspects.items():
            if abs(diff - angle) <= orb:
                return aspect_name, color, diff # Return diff for display
        return None

    aspect_lines_info = []
    textual_aspects = []
    # Only calculate aspects between planets (not nodes or fortune for simplicity in aspects list)
    # Planets eligible for aspect calculation
    aspect_points_filter = [p['name'] for p in point_positions if p['name'] in planet_symbols.keys()] # Filter for known planets for aspects
    aspect_points = [p for p in point_positions if p['name'] in aspect_points_filter]

    for i in range(len(aspect_points)):
        for j in range(i + 1, len(aspect_points)):
            name1 = aspect_points[i]['name']
            lon1 = aspect_points[i]['lon']
            name2 = aspect_points[j]['name']
            lon2 = aspect_points[j]['lon']

            aspect_info = get_aspect_info(lon1, lon2)
            if aspect_info:
                aspect_name, color, actual_diff = aspect_info
                aspect_lines_info.append({'point1': name1, 'point2': name2, 'color': color})
                textual_aspects.append(f"{name1} {planet_unicode_symbols.get(name1, '')} - {name2} {planet_unicode_symbols.get(name2, '')}: {aspect_name} ({actual_diff:.2f}°)")

    # =============================================================================
    # SISTEMA DE CASAS
    # =============================================================================
    # House calculation is already done above to get ASC for Fortune
    # Now just format the house cusps for display
    textual_house_cusps = []
    for i in range(1, 13): # Houses are 1-12
        cusp_lon = houses[i-1]
        sign_at_cusp = get_sign(cusp_lon)
        degree_in_sign = get_degree_in_sign(cusp_lon)
        degrees = int(degree_in_sign)
        minutes = int((degree_in_sign - degrees) * 60)
        textual_house_cusps.append(f"Casa {i}: {degrees}°{minutes:02d}' {sign_unicode_symbols.get(sign_at_cusp, '')} {sign_at_cusp}")

    # =============================================================================
    # VISUALIZAÇÃO GRÁFICA - MAPA ASTROLÓGICO
    # =============================================================================
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})

    ax.set_theta_direction(1)
    theta_offset_degrees = (180 - asc + 360) % 360
    ax.set_theta_offset(np.radians(theta_offset_degrees))

    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.grid(False)

    # Configurações de posição e espaçamento
    image_center_r = 0.90 # Posição radial para o centro das imagens dos planetas
    degree_text_r = 0.80
    minutes_text_r = 0.72
    retrograde_text_r = 0.85 # Levemente acima do símbolo para 'R'

    # Posições radiais para a marca de seleção para cada ponto (da borda externa)
    point_tick_r_outer = 1.0
    point_tick_r_inner = 0.98
    point_tick_linewidth = 1.5
    point_tick_linestyle = '-'

    # Posições radiais para as marcas de seleção para os pontos próximos ao círculo interno (para aspectos)
    point_tick_r_outer_inner_circle = 0.55
    point_tick_r_inner_circle = 0.53

    # Para ajuste angular (lateral) para evitar sobreposição de símbolos
    angular_overlap_threshold_degrees = 4.0
    angular_offset_step_degrees = 4.0

    # Tamanhos de fonte
    degree_text_fontsize = 10
    minutes_text_fontsize = 8
    retrograde_text_fontsize = 9 # Menor para 'R'

    # Reorganiza os pontos para calcular ajustes angulares de sobreposição
    processed_points_drawing_info = []
    sorted_points = sorted(point_positions, key=lambda p: p['lon'])

    # Lógica para aplicar offsets angulares
    occupied_angular_slots = []

    for p_data in sorted_points:
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
                # Lida com o contorno de 0/360 graus
                if potential_lon_min > potential_lon_max: # ex: 350-10 graus
                    if not ((potential_lon_max < occupied_lon_min and potential_lon_min > occupied_lon_max) or \
                            (occupied_lon_max < potential_lon_min and occupied_lon_min > potential_lon_max)):
                        is_overlapping = True
                        break
                elif occupied_lon_min > occupied_lon_max: # ex: ocupado é 350-10 graus
                    if not ((occupied_lon_max < potential_lon_min and potential_lon_min > potential_lon_max) or \
                            (potential_lon_max < occupied_lon_min and potential_lon_min > occupied_lon_max)):
                        is_overlapping = True
                        break
                else: # Sem contorno para ambos
                    if (potential_lon_min < occupied_lon_max and potential_lon_max > occupied_lon_min):
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

        processed_points_drawing_info.append({
            'name': p_data['name'],
            'original_lon': original_lon,
            'adjusted_lon': current_lon_adjusted,
            'retrograde': p_data['retrograde']
        })

    point_plot_info_map = {p['name']: p for p in processed_points_drawing_info}

    # Desenha as cúspides das casas (linhas divisórias)
    for cusp_lon in houses:
        angle = np.radians(cusp_lon)
        ax.plot([angle, angle], [0.55, 1.0], color='gray', linestyle='-', linewidth=1.5)

    # Desenha o círculo externo (zodíaco)
    circle_outer = plt.Circle((0, 0), 1.0, transform=ax.transData._b, fill=False, color='black', linewidth=1.5)
    ax.add_artist(circle_outer)

    # Desenha o círculo interno (representando o centro do mapa) mais forte
    circle_inner = plt.Circle((0, 0), 0.55, transform=ax.transData._b, fill=False, color='gray', linewidth=1.5)
    ax.add_artist(circle_inner)

    # Desenha outra camada de círculo interno
    circle_inner_outer = plt.Circle((0, 0), 0.65, transform=ax.transData._b, fill=False, color='gray', linewidth=1.5)
    ax.add_artist(circle_inner_outer)

    # Escreve os números das casas no centro angular entre as cúspides
    house_number_r = 0.6

    for i in range(12):
        cusp_start = houses[i]
        cusp_end = houses[(i + 1) % 12]

        if cusp_end < cusp_start:
            cusp_end += 360

        house_center_lon = (cusp_start + cusp_end) / 2 % 360
        angle_center = np.radians(house_center_lon)

        ax.text(angle_center, house_number_r, str(i + 1),
                fontsize=14, ha='center', va='center', weight='bold')

    # --- DESENHA AS DIVISÕES DOS SIGNOS E SEUS SÍMBOLOS ---
    sign_line_r_inner = 1
    sign_line_r_outer = 1.05

    for i in range(12):
        sign_start_lon = i * 30
        angle_start = np.radians(sign_start_lon)

        ax.plot([angle_start, angle_start], [sign_line_r_inner, sign_line_r_outer],
                color='black', linewidth=1.0)

        sign_center_lon = sign_start_lon + 15
        angle_center = np.radians(sign_center_lon)
        sign_name = signs[i]
        sign_sym = sign_unicode_symbols.get(sign_name, '?')

        # Obtém a cor do elemento para o signo
        element = sign_elements.get(sign_name, None)
        color = element_colors.get(element, 'black') # Padrão para preto se o elemento não for encontrado

        ax.text(angle_center, 1.040, sign_sym, fontsize=18, ha='center', va='center', weight='bold', color=color)

    # --- DESENHA OS PONTOS COM AJUSTES ANGULARES E MARCAS DE SELEÇÃO ---
    textual_point_positions = []
    for p_info in processed_points_drawing_info:
        point_name = p_info['name']
        original_lon = p_info['original_lon']
        adjusted_lon = p_info['adjusted_lon']
        is_retrograde = p_info['retrograde']

        # Adiciona às posições textuais dos pontos para a aba "Detalhes"
        sign_of_point = get_sign(original_lon)
        degree_in_sign = get_degree_in_sign(original_lon)
        degrees = int(degree_in_sign)
        minutes = int((degree_in_sign - degrees) * 60)
        retro_status = " (R)" if is_retrograde else ""
        textual_point_positions.append(f"{point_name} {planet_unicode_symbols.get(point_name, '')}: {degrees}°{minutes:02d}' {sign_unicode_symbols.get(sign_of_point, '')} {sign_of_point}{retro_status} ({original_lon:.2f}°)")

        original_angle = np.radians(original_lon)

        # 1. Primeira marca de seleção: Perto do anel zodiacal externo
        ax.plot([original_angle, original_angle], [point_tick_r_inner, point_tick_r_outer],
                color='black', linewidth=point_tick_linewidth, linestyle=point_tick_linestyle)

        # 2. Segunda marca de seleção: Perto do círculo interno de aspecto
        ax.plot([original_angle, original_angle], [point_tick_r_inner_circle, point_tick_r_outer_inner_circle],
                color='black', linewidth=point_tick_linewidth, linestyle=point_tick_linestyle)


        adjusted_angle = np.radians(adjusted_lon)

        # Usa imagem se disponível, caso contrário usa símbolo de texto
        if all_point_images.get(point_name) is not None:
            imagebox = OffsetImage(all_point_images[point_name], zoom=0.5)
            ab = AnnotationBbox(imagebox, (adjusted_angle, image_center_r),
                                frameon=False, pad=0.0,
                                xycoords='data', boxcoords="data")
            ax.add_artist(ab)
        else:
            # Fallback para símbolo de texto se a imagem não for encontrada
            point_symbol = planet_unicode_symbols.get(point_name, '?')
            ax.text(adjusted_angle, image_center_r, point_symbol,
                    fontsize=16, ha='center', va='center', weight='bold')

        # Exibe graus e minutos perto do símbolo do ponto
        degree_decimal = original_lon % 30
        degrees = int(degree_decimal)
        minutes = int((degree_decimal - degrees) * 60)

        degree_text = f"{degrees}°"
        minutes_text = f"{minutes:02d}'"

        ax.text(adjusted_angle, degree_text_r, degree_text,
                fontsize=degree_text_fontsize, ha='center', va='center')

        ax.text(adjusted_angle, minutes_text_r, minutes_text,
                fontsize=minutes_text_fontsize, ha='center', va='center')

        # Adiciona o indicador retrógrado 'R' se aplicável
        if is_retrograde:
            ax.text(adjusted_angle, retrograde_text_r, "R",
                    fontsize=retrograde_text_fontsize, ha='center', va='center', color='red', weight='bold')


    # =============================================================================
    # DESENHA AS LINHAS DE ASPECTO
    # =============================================================================
    for aspect_info in aspect_lines_info:
        name1 = aspect_info['point1']
        name2 = aspect_info['point2']
        color = aspect_info['color']

        lon1 = next(p for p in processed_points_drawing_info if p['name'] == name1)['original_lon']
        lon2 = next(p for p in processed_points_drawing_info if p['name'] == name2)['original_lon']

        angle1 = np.radians(lon1)
        angle2 = np.radians(lon2)

        aspect_radial_pos = 0.53 # Posição radial para as linhas de aspecto
        ax.plot([angle1, angle2], [aspect_radial_pos, aspect_radial_pos],
                color=color, linewidth=1.5, linestyle='-')

    # =============================================================================
    # FINALIZAÇÃO E EXIBIÇÃO DENTRO DO TKINTER
    # =============================================================================
    chart_title_type = "Mapa Natal" if chart_type == 'natal' else "Mapa Horário"
    ax.set_title(f"{chart_title_type} ({house_system} Casas) para {birth_date.strftime('%Y-%m-%d %H:%M')}\n{location_input_str} (Lat: {latitude:.2f}, Lon: {longitude:.2f})", y=1.08, fontsize=14)
    plt.tight_layout()

    # Cria um canvas Tkinter e incorpora a figura Matplotlib
    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Adiciona a barra de ferramentas de navegação Matplotlib
    toolbar = NavigationToolbar2Tk(canvas, chart_frame)
    toolbar.update()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True) # Empacota novamente para garantir que a barra de ferramentas esteja visível

    # Preenche o widget de texto de detalhes
    details_text_widget.config(state=tk.NORMAL) # Habilita a edição
    details_text_widget.delete(1.0, tk.END) # Limpa o conteúdo anterior

    details_text_widget.insert(tk.END, f"--- Detalhes do {chart_title_type} ({house_system} Casas) para {birth_date.strftime('%Y-%m-%d %H:%M')} ---\n\n")
    details_text_widget.insert(tk.END, f"Local: {location_input_str} (Lat: {latitude:.2f}, Lon: {longitude:.2f}, Fuso: {timezone_id})\n\n")

    details_text_widget.insert(tk.END, "=== Posições de Pontos Astrológicos ===\n")
    for pos_str in textual_point_positions:
        details_text_widget.insert(tk.END, f"- {pos_str}\n")
    details_text_widget.insert(tk.END, "\n")

    details_text_widget.insert(tk.END, "=== Cúspides das Casas ===\n")
    for cusp_str in textual_house_cusps:
        details_text_widget.insert(tk.END, f"- {cusp_str}\n")
    details_text_widget.insert(tk.END, "\n")

    details_text_widget.insert(tk.END, "=== Aspectos ===\n")
    if textual_aspects:
        for aspect_str in textual_aspects:
            details_text_widget.insert(tk.END, f"- {aspect_str}\n")
    else:
        details_text_widget.insert(tk.END, "Nenhum aspecto maior encontrado com orbe de 8°.\n")
    details_text_widget.insert(tk.END, "\n")

    details_text_widget.config(state=tk.DISABLED) # Desabilita a edição

    return fig # Retorna a figura para gerenciar seu ciclo de vida


# =============================================================================
# INTERFACE GRÁFICA (Tkinter)
# =============================================================================
def create_gui():
    global details_text_widget, notebook, input_frame, back_button # Declara como global para acessá-los

    def update_input_fields_state():
        if chart_type_var.get() == 'horary':
            date_entry.config(state=tk.DISABLED)
            time_entry.config(state=tk.DISABLED)
            # Limpa data/hora para o modo horária para clareza
            date_entry.delete(0, tk.END)
            time_entry.delete(0, tk.END)
            date_entry.insert(0, "Tempo Atual") # Placeholder
            time_entry.insert(0, "Tempo Atual") # Placeholder
            house_system_var.set('Regiomontanus') # Define Regiomontanus como padrão para Horária
        else: # 'natal'
            date_entry.config(state=tk.NORMAL)
            time_entry.config(state=tk.NORMAL)
            # Restaura valores padrão ou deixa em branco para entrada do usuário
            date_entry.delete(0, tk.END)
            time_entry.delete(0, tk.END)
            date_entry.insert(0, "2003-08-15")
            time_entry.insert(0, "21:30")
            house_system_var.set('Placidus') # Padrão para Placidus para Natal


    def show_input_frame():
        # Esconde o notebook
        notebook.pack_forget()
        # Exibe o frame de entrada
        input_frame.pack(fill=tk.BOTH, expand=True)
        # Esconde o botão de voltar
        back_button.place_forget()

        # Fecha a figura Matplotlib ao retornar ao frame de entrada
        global fig
        if fig is not None:
            plt.close(fig)
            fig = None
        # Também limpa o texto de detalhes ao voltar
        if details_text_widget is not None:
            details_text_widget.config(state=tk.NORMAL)
            details_text_widget.delete(1.0, tk.END)
            details_text_widget.config(state=tk.DISABLED)


    def on_calculate():
        chart_type = chart_type_var.get()
        house_system = house_system_var.get()
        location_input = location_entry.get()

        date_input = date_entry.get()
        time_input = time_entry.get()

        if not location_input:
            messagebox.showwarning("Entrada Inválida", "Por favor, forneça uma localização.")
            return

        if chart_type == 'natal' and (not date_input or not time_input):
            messagebox.showwarning("Entrada Inválida", "Para o Mapa Natal, a data e a hora são obrigatórias.")
            return

        # Esconde o frame de entrada
        input_frame.pack_forget()

        # Tenta plotar o gráfico e atualizar os detalhes
        plotted_fig = plot_astral_chart(chart_type, house_system, date_input, time_input, location_input, chart_frame, details_frame)

        if plotted_fig: # Se a plotagem foi bem-sucedida
            # Empacota o notebook
            notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            notebook.select(chart_tab) # Muda automaticamente para a aba do gráfico
            # Exibe o botão de voltar no canto superior direito
            back_button.place(relx=1.0, rely=0.0, anchor=tk.NE, x=-10, y=10)
        else: # Se a plotagem falhou, volta para o frame de entrada
            show_input_frame() # Isso esconderá o botão se a plotagem falhar


    root = tk.Tk()
    root.title("Calculadora de Mapa Astral")
    root.geometry("900x850") # Ajusta o tamanho para abas e conteúdo
    root.resizable(True, True)

    # --- Frame de Entrada (Tela inicial) ---
    input_frame = ttk.Frame(root, padding="20")
    input_frame.pack(fill=tk.BOTH, expand=True) # Inicialmente visível

    style = ttk.Style()
    style.configure("TLabel", font=("Arial", 10))
    style.configure("TEntry", font=("Arial", 10))
    style.configure("TButton", font=("Arial", 10, "bold"))
    style.configure("TNotebook.Tab", font=("Arial", 10, "bold")) # Estilo para abas

    # Cria um sub-frame para as entradas para centralizá-las
    input_fields_frame = ttk.Frame(input_frame, padding="15", relief="groove", borderwidth=2)
    input_fields_frame.pack(expand=True, anchor='center') # Centraliza este frame

    # Seleção do Tipo de Mapa
    ttk.Label(input_fields_frame, text="Tipo de Mapa:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
    chart_type_var = tk.StringVar(value='natal') # Padrão para Natal
    natal_radio = ttk.Radiobutton(input_fields_frame, text="Mapa Natal", variable=chart_type_var, value='natal', command=update_input_fields_state)
    natal_radio.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
    horary_radio = ttk.Radiobutton(input_fields_frame, text="Mapa Horário (Tempo Real)", variable=chart_type_var, value='horary', command=update_input_fields_state)
    horary_radio.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)


    ttk.Label(input_fields_frame, text="Data (AAAA-MM-DD):").grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
    date_entry = ttk.Entry(input_fields_frame, width=30)
    date_entry.grid(row=2, column=1, pady=5, padx=5)
    date_entry.insert(0, "2003-08-15") # Valor padrão para teste

    ttk.Label(input_fields_frame, text="Hora (HH:MM):").grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
    time_entry = ttk.Entry(input_fields_frame, width=30)
    time_entry.grid(row=3, column=1, pady=5, padx=5)
    time_entry.insert(0, "21:30") # Valor padrão para teste

    ttk.Label(input_fields_frame, text="Local (Cidade, País):").grid(row=4, column=0, sticky=tk.W, pady=5, padx=5)
    location_entry = ttk.Entry(input_fields_frame, width=30)
    location_entry.grid(row=4, column=1, pady=5, padx=5)
    location_entry.insert(0, "Rio de Janeiro, Brazil") # Valor padrão para teste

    # Seleção do Sistema de Casas
    ttk.Label(input_fields_frame, text="Sistema de Casas:").grid(row=5, column=0, sticky=tk.W, pady=5, padx=5)
    house_system_var = tk.StringVar(value='Placidus') # Padrão para Placidus
    house_system_dropdown = ttk.Combobox(input_fields_frame, textvariable=house_system_var,
                                        values=['Placidus', 'Regiomontanus'], state='readonly', width=28)
    house_system_dropdown.grid(row=5, column=1, sticky=tk.W, pady=5, padx=5)


    calculate_button = ttk.Button(input_fields_frame, text="Gerar Mapa Astral", command=on_calculate)
    calculate_button.grid(row=6, column=0, columnspan=2, pady=20)

    # Configura as colunas para expandir
    input_fields_frame.columnconfigure(0, weight=1)
    input_fields_frame.columnconfigure(1, weight=1)
    # input_fields_frame.rowconfigure(7, weight=1) # Deixa a linha com o botão ocupar o espaço disponível

    # --- Notebook (Interface com Abas para Gráfico e Detalhes) ---
    notebook = ttk.Notebook(root)
    # Será empacotado dinamicamente por on_calculate

    # --- Aba do Gráfico ---
    chart_tab = ttk.Frame(notebook)
    notebook.add(chart_tab, text="Mapa Astral")
    chart_frame = ttk.Frame(chart_tab) # Frame para conter o gráfico Matplotlib
    chart_frame.pack(fill=tk.BOTH, expand=True)

    # --- Aba de Detalhes ---
    details_tab = ttk.Frame(notebook)
    notebook.add(details_tab, text="Detalhes Astrológicos")
    details_frame = ttk.Frame(details_tab) # Frame para conter os detalhes textuais
    details_frame.pack(fill=tk.BOTH, expand=True)

    # Widget de Texto para detalhes (usando tk.Text e um Scrollbar para melhor controle)
    details_text_widget = tk.Text(details_frame, wrap=tk.WORD, state=tk.DISABLED,
                                  font=("Courier New", 10), padx=10, pady=10)
    details_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(details_frame, command=details_text_widget.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    details_text_widget.config(yscrollcommand=scrollbar.set)

    # --- Botão "Voltar" (usando uma seta para a esquerda) ---
    # Cria o botão diretamente na janela raiz e gerencia com place()
    back_button = ttk.Button(root, text="←", command=show_input_frame, width=5) # Largura reduzida para a seta
    back_button.place_forget() # Inicialmente oculto

    # Configura o protocolo de fechamento da janela para garantir que as figuras Matplotlib sejam fechadas
    def on_closing():
        global fig
        if fig is not None:
            plt.close(fig)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Atualiza o estado inicial dos campos de entrada
    update_input_fields_state()

    root.mainloop()

if __name__ == "__main__":
    create_gui()