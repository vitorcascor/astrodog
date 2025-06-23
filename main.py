import swisseph as swe
import datetime
import pytz
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from tkinter import Canvas, PhotoImage
from tkinter import ttk, messagebox
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# =============================================================================
# CONSTANTES ASTROLÓGICAS (Mantidas do seu código original)
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
    'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇'
}


planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter',
           'Saturn', 'Uranus', 'Neptune', 'Pluto']

signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

# Define element colors and sign-to-element mapping
element_colors = {
    'Fire': 'red',
    'Earth': 'green',
    'Air': '#eb8204',
    'Water': 'blue'
}

sign_elements = {
    'Aries': 'Fire', 'Leo': 'Fire', 'Sagittarius': 'Fire',
    'Taurus': 'Earth', 'Virgo': 'Earth', 'Capricorn': 'Earth',
    'Gemini': 'Air', 'Libra': 'Air', 'Aquarius': 'Air',
    'Cancer': 'Water', 'Scorpio': 'Water', 'Pisces': 'Water'
}

# Pre-load planet images
planet_images = {}
for planet_name, image_path in planet_symbols.items():
    try:
        planet_images[planet_name] = mpimg.imread(image_path)
    except FileNotFoundError:
        print(f"Warning: Image not found for {planet_name} at {image_path}. Using text symbol.")
        planet_images[planet_name] = None # Mark as not found

# Global variables for chart display and details
canvas = None
toolbar = None
fig = None
details_text_widget = None # To hold the Text widget for details tab

# Helper function to get sign from longitude
def get_sign(longitude):
    sign_index = int(longitude / 30) % 12
    return signs[sign_index]

def get_degree_in_sign(longitude):
    return longitude % 30

# =============================================================================
# FUNÇÃO PARA CALCULAR E PLOTAR O MAPA ASTRAL (adaptada para a GUI)
# =============================================================================
def plot_astral_chart(date_str, time_str, location_input_str, chart_frame, details_frame):
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

    # 2. Processamento de Data e Hora (como no seu código)
    try:
        birth_date = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        timezone = pytz.timezone(timezone_id)
        birth_date = timezone.localize(birth_date)
        utc_birth_date = birth_date.astimezone(pytz.utc)
    except ValueError:
        messagebox.showerror("Erro de Data/Hora", "Formato de data ou hora inválido. Use AAAA-MM-DD e HH:MM.")
        return None # Return None to indicate failure
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
            "Conjunção": (0, 'red'),
            "Oposição": (180, 'red'),
            "Trígono": (120, '#008000'),
            "Quadratura": (90, 'red'),
            "Sextil": (60, '#008000'),
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
    for i in range(len(planet_positions)):
        for j in range(i + 1, len(planet_positions)):
            name1 = planet_positions[i]['name']
            lon1 = planet_positions[i]['lon']
            name2 = planet_positions[j]['name']
            lon2 = planet_positions[j]['lon']

            aspect_info = get_aspect_info(lon1, lon2)
            if aspect_info:
                aspect_name, color, actual_diff = aspect_info
                aspect_lines_info.append({'planet1': name1, 'planet2': name2, 'color': color})
                textual_aspects.append(f"{name1} {planet_unicode_symbols.get(name1, '')} - {name2} {planet_unicode_symbols.get(name2, '')}: {aspect_name} ({actual_diff:.2f}°)")

    # =============================================================================
    # SISTEMA DE CASAS (PLACIDUS) (Mantido do seu código)
    # =============================================================================
    houses, ascmc = swe.houses(jd, latitude, longitude, b'P')

    asc = ascmc[0]
    mc = ascmc[1]

    # Store house cusp information
    textual_house_cusps = []
    for i in range(1, 13): # Houses are 1-12
        cusp_lon = houses[i-1] # swe.houses returns 0-indexed array for 12 houses
        sign_at_cusp = get_sign(cusp_lon)
        degree_in_sign = get_degree_in_sign(cusp_lon)
        degrees = int(degree_in_sign)
        minutes = int((degree_in_sign - degrees) * 60)
        textual_house_cusps.append(f"Casa {i}: {degrees}°{minutes:02d}' {sign_unicode_symbols.get(sign_at_cusp, '')} {sign_at_cusp}")

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
    image_center_r = 0.90
    degree_text_r = 0.80
    minutes_text_r = 0.72

    # AJUSTES PARA O TRAÇO DOS PLANETAS
    planet_tick_r_outer = 1.0
    planet_tick_r_inner = 0.98
    planet_tick_linewidth = 1.5
    planet_tick_linestyle = '-'

    # AJUSTES PARA O TRAÇO DOS PLANETAS 2
    planet_tick_r_outer_inner_circle = 0.55
    planet_tick_r_inner_circle = 0.53

    # Para o ajuste angular (lateral)
    angular_overlap_threshold_degrees = 4.0
    angular_offset_step_degrees = 4.0

    # Tamanhos das fontes
    degree_text_fontsize = 10
    minutes_text_fontsize = 8

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
                # Handle wrapping around 0/360 degrees
                if potential_lon_min > potential_lon_max: # e.g., 350-10 degrees
                    if not ((potential_lon_max < occupied_lon_min and potential_lon_min > occupied_lon_max) or \
                            (occupied_lon_max < potential_lon_min and occupied_lon_min > potential_lon_max)):
                        is_overlapping = True
                        break
                elif occupied_lon_min > occupied_lon_max: # e.g., occupied is 350-10 degrees
                    if not ((occupied_lon_max < potential_lon_min and occupied_lon_min > potential_lon_max) or \
                            (potential_lon_max < occupied_lon_min and potential_lon_min > occupied_lon_max)):
                        is_overlapping = True
                        break
                else: # No wrapping for either
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

        processed_planets_drawing_info.append({
            'name': p_data['name'],
            'original_lon': original_lon,
            'adjusted_lon': current_lon_adjusted,
        })

    planet_plot_info_map = {p['name']: p for p in processed_planets_drawing_info}

    # Desenha cúspides das casas (linhas divisórias)
    for cusp_lon in houses:
        angle = np.radians(cusp_lon)
        ax.plot([angle, angle], [0.55, 1.0], color='gray', linestyle='-', linewidth=1.5)

    # Desenha círculo externo (zodíaco)
    circle_outer = plt.Circle((0, 0), 1.0, transform=ax.transData._b, fill=False, color='black', linewidth=1.5)
    ax.add_artist(circle_outer)

    # Desenha o círculo interno (representando o centro do mapa) mais forte
    circle_inner = plt.Circle((0, 0), 0.55, transform=ax.transData._b, fill=False, color='gray', linewidth=1.5)
    ax.add_artist(circle_inner)

    # Desenha uma nova camada de circulo interno
    circle_inner_outer = plt.Circle((0, 0), 0.65, transform=ax.transData._b, fill=False, color='gray', linewidth=1.5)
    ax.add_artist(circle_inner_outer)

    # Escrever o número de cada casa no centro angular entre cúspides
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

    # --- DESENHO DAS DIVISÕES DOS SIGNOS E SEUS SÍMBOLOS ---
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

        # Get element color for the sign
        element = sign_elements.get(sign_name, None)
        color = element_colors.get(element, 'black') # Default to black if element not found

        ax.text(angle_center, 1.040, sign_sym, fontsize=18, ha='center', va='center', weight='bold', color=color)

    # --- DESENHO DOS PLANETAS COM AJUSTES ANGULARES E TRAÇOS ---
    textual_planet_positions = []
    for p_info in processed_planets_drawing_info:
        planet_name = p_info['name']
        original_lon = p_info['original_lon']
        adjusted_lon = p_info['adjusted_lon']

        # Add to textual planet positions
        sign_of_planet = get_sign(original_lon)
        degree_in_sign = get_degree_in_sign(original_lon)
        degrees = int(degree_in_sign)
        minutes = int((degree_in_sign - degrees) * 60)
        textual_planet_positions.append(f"{planet_name} {planet_unicode_symbols.get(planet_name, '')}: {degrees}°{minutes:02d}' {sign_unicode_symbols.get(sign_of_planet, '')} {sign_of_planet} ({original_lon:.2f}°)")

        original_angle = np.radians(original_lon)
        ax.plot([original_angle, original_angle], [planet_tick_r_inner_circle, planet_tick_r_outer_inner_circle], # Draw tick mark for planet
                color='black', linewidth=planet_tick_linewidth, linestyle=planet_tick_linestyle)

        adjusted_angle = np.radians(adjusted_lon)

        # Use image if available, otherwise use text symbol
        if planet_images.get(planet_name) is not None:
            imagebox = OffsetImage(planet_images[planet_name], zoom=0.5)
            ab = AnnotationBbox(imagebox, (adjusted_angle, image_center_r),
                                frameon=False, pad=0.0,
                                xycoords='data', boxcoords="data")
            ax.add_artist(ab)
        else:
            # Fallback to text symbol if image not found
            planet_symbol = planet_unicode_symbols.get(planet_name, '?') # Use specific planet unicode symbols
            ax.text(adjusted_angle, image_center_r, planet_symbol,
                    fontsize=16, ha='center', va='center', weight='bold')


        degree_decimal = original_lon % 30
        degrees = int(degree_decimal)
        minutes = int((degree_decimal - degrees) * 60)

        degree_text = f"{degrees}°"
        minutes_text = f"{minutes:02d}'"

        ax.text(adjusted_angle, degree_text_r, degree_text,
                fontsize=degree_text_fontsize, ha='center', va='center')

        ax.text(adjusted_angle, minutes_text_r, minutes_text,
                fontsize=minutes_text_fontsize, ha='center', va='center')
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

        aspect_radial_pos = 0.53
        ax.plot([angle1, angle2], [aspect_radial_pos, aspect_radial_pos],
                color=color, linewidth=1.5, linestyle='-')

    # =============================================================================
    # FINALIZAÇÃO E EXIBIÇÃO DENTRO DO TKINTER
    # =============================================================================
    ax.set_title(f"Mapa Astral para {birth_date.strftime('%Y-%m-%d %H:%M')}\n{location_input_str} (Lat: {latitude:.2f}, Lon: {longitude:.2f})", y=1.08, fontsize=14)
    plt.tight_layout()

    # Create a Tkinter canvas and embed the Matplotlib figure
    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Add Matplotlib navigation toolbar
    toolbar = NavigationToolbar2Tk(canvas, chart_frame)
    toolbar.update()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Populate the details text widget
    details_text_widget.config(state=tk.NORMAL) # Enable editing
    details_text_widget.delete(1.0, tk.END) # Clear previous content

    details_text_widget.insert(tk.END, f"--- Detalhes do Mapa Astral para {birth_date.strftime('%Y-%m-%d %H:%M')} ---\n\n")
    details_text_widget.insert(tk.END, f"Local: {location_input_str} (Lat: {latitude:.2f}, Lon: {longitude:.2f}, Fuso: {timezone_id})\n\n")

    details_text_widget.insert(tk.END, "=== Posições Planetárias ===\n")
    for pos_str in textual_planet_positions:
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


    details_text_widget.config(state=tk.DISABLED) # Disable editing

    return fig # Return the figure to manage its lifecycle


# =============================================================================
# INTERFACE GRÁFICA (Tkinter)
# =============================================================================
def create_gui():
    global details_text_widget # Declare as global to access it

    def show_input_frame():
        # Hide all other frames and show the input frame
        notebook.pack_forget() # Hide the notebook
        input_frame.pack(fill=tk.BOTH, expand=True)
        # Close the Matplotlib figure when returning to input frame
        global fig
        if fig is not None:
            plt.close(fig)
            fig = None

    def on_calculate():
        date_input = date_entry.get()
        time_input = time_entry.get()
        location_input = location_entry.get()

        if not all([date_input, time_input, location_input]):
            messagebox.showwarning("Entrada Inválida", "Por favor, preencha todos os campos.")
            return

        # Hide input frame
        input_frame.pack_forget()

        # Try to plot the chart and update details
        plotted_fig = plot_astral_chart(date_input, time_input, location_input, chart_frame, details_frame)

        if plotted_fig: # If plotting was successful, show the notebook
            notebook.pack(fill=tk.BOTH, expand=True)
            notebook.select(chart_tab) # Automatically switch to the chart tab
        else: # If plotting failed, go back to input frame
            show_input_frame()


    root = tk.Tk()
    root.title("Calculadora de Mapa Astral")
    root.geometry("900x850") # Adjust size for tabs and content
    root.resizable(True, True)

    # --- Input Frame (Initial screen) ---
    input_frame = ttk.Frame(root, padding="20")
    input_frame.pack(fill=tk.BOTH, expand=True)

    style = ttk.Style()
    style.configure("TLabel", font=("Arial", 10))
    style.configure("TEntry", font=("Arial", 10))
    style.configure("TButton", font=("Arial", 10, "bold"))
    style.configure("TNotebook.Tab", font=("Arial", 10, "bold"))

    ttk.Label(input_frame, text="Data (AAAA-MM-DD):").grid(row=0, column=0, sticky=tk.W, pady=5)
    date_entry = ttk.Entry(input_frame, width=30)
    date_entry.grid(row=0, column=1, pady=5)
    date_entry.insert(0, "2003-08-15") # Valor padrão para teste

    ttk.Label(input_frame, text="Hora (HH:MM):").grid(row=1, column=0, sticky=tk.W, pady=5)
    time_entry = ttk.Entry(input_frame, width=30)
    time_entry.grid(row=1, column=1, pady=5)
    time_entry.insert(0, "21:30") # Valor padrão para teste

    ttk.Label(input_frame, text="Local de Nascimento (Cidade, País):").grid(row=2, column=0, sticky=tk.W, pady=5)
    location_entry = ttk.Entry(input_frame, width=30)
    location_entry.grid(row=2, column=1, pady=5)
    location_entry.insert(0, "Rio de Janeiro, Brazil") # Valor padrão para teste

    calculate_button = ttk.Button(input_frame, text="Gerar Mapa Astral", command=on_calculate)
    calculate_button.grid(row=3, column=0, columnspan=2, pady=20)

    input_frame.columnconfigure(0, weight=1)
    input_frame.columnconfigure(1, weight=1)
    for i in range(4):
        input_frame.rowconfigure(i, weight=1)

    # --- Notebook (Tabbed Interface for Chart and Details) ---
    notebook = ttk.Notebook(root)
    # This will be packed only after a chart is generated

    # --- Chart Tab ---
    chart_tab = ttk.Frame(notebook)
    notebook.add(chart_tab, text="Mapa Astral")
    chart_frame = ttk.Frame(chart_tab) # Frame to hold the Matplotlib chart
    chart_frame.pack(fill=tk.BOTH, expand=True)

    # --- Details Tab ---
    details_tab = ttk.Frame(notebook)
    notebook.add(details_tab, text="Detalhes Astrológicos")
    details_frame = ttk.Frame(details_tab) # Frame to hold the textual details
    details_frame.pack(fill=tk.BOTH, expand=True)

    # Text widget for details (using scrolledtext for scrollability)
    # It's better to use tk.Text directly and add a scrollbar manually for more control
    details_text_widget = tk.Text(details_frame, wrap=tk.WORD, state=tk.DISABLED,
                                  font=("Courier New", 10), padx=10, pady=10)
    details_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(details_frame, command=details_text_widget.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    details_text_widget.config(yscrollcommand=scrollbar.set)

    # Button to return to input form (visible in both chart and details tabs)
    # Placed outside the notebook for consistent visibility
    back_button = ttk.Button(root, text="Voltar ao Questionário", command=show_input_frame)
    back_button.pack(side=tk.BOTTOM, pady=10)

    # Initially hide the back button and notebook until a chart is generated
    back_button.pack_forget()
    notebook.pack_forget()

    # Function to manage showing/hiding back button based on current frame
    def manage_back_button_visibility():
        if input_frame.winfo_ismapped():
            back_button.pack_forget()
        else:
            back_button.pack(side=tk.BOTTOM, pady=10)

    # Bind this function to notebook tab change (optional, but good for robustness)
    notebook.bind("<<NotebookTabChanged>>", lambda event: manage_back_button_visibility())

    # Set up window close protocol to ensure Matplotlib figures are closed
    def on_closing():
        global fig
        if fig is not None:
            plt.close(fig)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()

if __name__ == "__main__":
    create_gui()