import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import numpy as np

from .constants import (
    ALL_POINT_IMAGES, SIGN_UNICODE_SYMBOLS, PLANET_UNICODE_SYMBOLS,
    SIGNS, ELEMENT_COLORS, SIGN_ELEMENTS,
    IMAGE_CENTER_R, DEGREE_TEXT_R, MINUTES_TEXT_R, RETROGRADE_TEXT_R,
    POINT_TICK_R_OUTER, POINT_TICK_R_INNER, POINT_TICK_LINEWIDTH, POINT_TICK_LINESTYLE,
    POINT_TICK_R_OUTER_INNER_CIRCLE, POINT_TICK_R_INNER_CIRCLE,
    ANGULAR_OVERLAP_THRESHOLD_DEGREES, ANGULAR_OFFSET_STEP_DEGREES,
    DEGREE_TEXT_FONTSIZE, MINUTES_TEXT_FONTSIZE, RETROGRADE_TEXT_FONTSIZE,
    HOUSE_NUMBER_R, SIGN_LINE_R_INNER, SIGN_LINE_R_OUTER, ASPECT_RADIAL_POS
)

class ChartRenderer:
    def __init__(self):
        self.fig = None
        self.ax = None

    def create_chart_plot(self, chart_data):
        """
        Cria a figura e eixos do Matplotlib para o mapa astral.
        Retorna a figura Matplotlib.
        """
        if self.fig is not None:
            plt.close(self.fig) # Fecha a figura anterior se existir
            self.fig = None
        
        self.fig, self.ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})
        
        # Define a direção theta e offset para o Ascendente
        self.ax.set_theta_direction(1) # Sentido horário
        # Rotaciona o gráfico para que o Ascendente (casa 1) fique no lado esquerdo (posição 9h)
        theta_offset_degrees = (180 - chart_data['asc'] + 360) % 360
        self.ax.set_theta_offset(np.radians(theta_offset_degrees))

        self.ax.set_yticklabels([])
        self.ax.set_xticklabels([])
        self.ax.grid(False)

        self._draw_house_cusps(chart_data['houses'])
        self._draw_circles()
        self._draw_house_numbers(chart_data['houses'])
        self._draw_sign_divisions()
        self._draw_points(chart_data['point_positions'])
        self._draw_aspect_lines(chart_data['aspects_data'], chart_data['point_positions'])

        chart_title_type = "Mapa Natal" if chart_data['chart_type'] == 'natal' else "Mapa Horário"
        self.ax.set_title(
            f"{chart_title_type} ({chart_data['house_system']} Casas) para {chart_data['birth_date'].strftime('%Y-%m-%d %H:%M')}\n"
            f"{chart_data['latitude']:.2f}, {chart_data['longitude']:.2f} ({chart_data['timezone_id']})",
            y=1.08, fontsize=14
        )
        plt.tight_layout()
        
        return self.fig

    def _draw_house_cusps(self, houses):
        """Desenha as linhas das cúspides das casas."""
        for cusp_lon in houses:
            angle = np.radians(cusp_lon)
            self.ax.plot([angle, angle], [0.55, 1.0], color='gray', linestyle='-', linewidth=1.5)

    def _draw_circles(self):
        """Desenha os círculos principais do mapa."""
        circle_outer = plt.Circle((0, 0), 1.0, transform=self.ax.transData._b, fill=False, color='black', linewidth=1.5)
        self.ax.add_artist(circle_outer)

        circle_inner = plt.Circle((0, 0), 0.55, transform=self.ax.transData._b, fill=False, color='gray', linewidth=1.5)
        self.ax.add_artist(circle_inner)

        circle_inner_outer = plt.Circle((0, 0), 0.65, transform=self.ax.transData._b, fill=False, color='gray', linewidth=1.5)
        self.ax.add_artist(circle_inner_outer)

    def _draw_house_numbers(self, houses):
        """Desenha os números das casas no mapa."""
        for i in range(12):
            cusp_start = houses[i]
            cusp_end = houses[(i + 1) % 12]

            if cusp_end < cusp_start:
                cusp_end += 360

            house_center_lon = (cusp_start + cusp_end) / 2 % 360
            angle_center = np.radians(house_center_lon)

            self.ax.text(angle_center, HOUSE_NUMBER_R, str(i + 1),
                         fontsize=14, ha='center', va='center', weight='bold')

    def _draw_sign_divisions(self):
        """Desenha as divisões dos signos e seus símbolos."""
        for i in range(12):
            sign_start_lon = i * 30
            angle_start = np.radians(sign_start_lon)

            self.ax.plot([angle_start, angle_start], [SIGN_LINE_R_INNER, SIGN_LINE_R_OUTER],
                         color='black', linewidth=1.0)

            sign_center_lon = sign_start_lon + 15
            angle_center = np.radians(sign_center_lon)
            sign_name = SIGNS[i]
            sign_sym = SIGN_UNICODE_SYMBOLS.get(sign_name, '?')

            element = SIGN_ELEMENTS.get(sign_name, None)
            color = ELEMENT_COLORS.get(element, 'black')

            self.ax.text(angle_center, 1.040, sign_sym, fontsize=18, ha='center', va='center', weight='bold', color=color)

    def _draw_points(self, point_positions):
        """Desenha os símbolos dos planetas/pontos com graus, minutos e status retrógrado."""
        
        # Prepare points for angular adjustment to avoid overlap
        processed_points_drawing_info = []
        sorted_points = sorted(point_positions, key=lambda p: p['lon'])
        
        occupied_angular_slots = []

        for p_data in sorted_points:
            original_lon = p_data['lon']
            current_lon_adjusted = original_lon

            found_slot = False
            max_iterations = 30 # Limit iterations to prevent infinite loops
            iteration = 0

            while not found_slot and iteration < max_iterations:
                potential_lon_min = (current_lon_adjusted - (ANGULAR_OVERLAP_THRESHOLD_DEGREES / 2)) % 360
                potential_lon_max = (current_lon_adjusted + (ANGULAR_OVERLAP_THRESHOLD_DEGREES / 2)) % 360

                is_overlapping = False
                for occupied_lon_min, occupied_lon_max, _ in occupied_angular_slots:
                    # Logic to handle 0/360 degree wrap-around for overlap check
                    if potential_lon_min > potential_lon_max: # e.g., 350-10 degrees
                        if not ((potential_lon_max < occupied_lon_min and potential_lon_min > occupied_lon_max) or \
                                (occupied_lon_max < potential_lon_min and occupied_lon_min > potential_lon_max)):
                            is_overlapping = True
                            break
                    elif occupied_lon_min > occupied_lon_max: # e.g., occupied is 350-10 degrees
                        if not ((occupied_lon_max < potential_lon_min and potential_lon_min > potential_lon_max) or \
                                (potential_lon_max < occupied_lon_min and potential_lon_min > occupied_lon_max)):
                            is_overlapping = True
                            break
                    else: # No wrap-around for both
                        if (potential_lon_min < occupied_lon_max and potential_lon_max > occupied_lon_min):
                            is_overlapping = True
                            break

                if is_overlapping:
                    current_lon_adjusted = (current_lon_adjusted + ANGULAR_OFFSET_STEP_DEGREES) % 360
                else:
                    found_slot = True
                    occupied_angular_slots.append((potential_lon_min, potential_lon_max, current_lon_adjusted))

                iteration += 1

            if not found_slot:
                print(f"Warning: Could not find a free slot for {p_data['name']}. Using last calculated position.")

            processed_points_drawing_info.append({
                'name': p_data['name'],
                'original_lon': original_lon,
                'adjusted_lon': current_lon_adjusted,
                'retrograde': p_data['retrograde']
            })

        # Now draw points using adjusted positions
        for p_info in processed_points_drawing_info:
            point_name = p_info['name']
            original_lon = p_info['original_lon']
            adjusted_lon = p_info['adjusted_lon']
            is_retrograde = p_info['retrograde']

            original_angle = np.radians(original_lon)
            adjusted_angle = np.radians(adjusted_lon)

            # 1. Primeira marca de seleção: Perto do anel zodiacal externo
            self.ax.plot([original_angle, original_angle], [POINT_TICK_R_INNER, POINT_TICK_R_OUTER],
                    color='black', linewidth=POINT_TICK_LINEWIDTH, linestyle=POINT_TICK_LINESTYLE)

            # 2. Segunda marca de seleção: Perto do círculo interno de aspecto
            self.ax.plot([original_angle, original_angle], [POINT_TICK_R_INNER_CIRCLE, POINT_TICK_R_OUTER_INNER_CIRCLE],
                    color='black', linewidth=POINT_TICK_LINEWIDTH, linestyle=POINT_TICK_LINESTYLE)

            # Use image if available, otherwise use text symbol
            if ALL_POINT_IMAGES.get(point_name) is not None:
                imagebox = OffsetImage(ALL_POINT_IMAGES[point_name], zoom=0.5)
                ab = AnnotationBbox(imagebox, (adjusted_angle, IMAGE_CENTER_R),
                                    frameon=False, pad=0.0,
                                    xycoords='data', boxcoords="data")
                self.ax.add_artist(ab)
            else:
                # Fallback to text symbol if image not found
                point_symbol = PLANET_UNICODE_SYMBOLS.get(point_name, '?')
                self.ax.text(adjusted_angle, IMAGE_CENTER_R, point_symbol,
                             fontsize=16, ha='center', va='center', weight='bold')

            # Display degrees and minutes near the point symbol
            degree_decimal = original_lon % 30
            degrees = int(degree_decimal)
            minutes = int((degree_decimal - degrees) * 60)

            degree_text = f"{degrees}°"
            minutes_text = f"{minutes:02d}'"

            self.ax.text(adjusted_angle, DEGREE_TEXT_R, degree_text,
                    fontsize=DEGREE_TEXT_FONTSIZE, ha='center', va='center')

            self.ax.text(adjusted_angle, MINUTES_TEXT_R, minutes_text,
                    fontsize=MINUTES_TEXT_FONTSIZE, ha='center', va='center')

            # Add retrograde 'R' indicator if applicable
            if is_retrograde:
                self.ax.text(adjusted_angle, RETROGRADE_TEXT_R, "R",
                        fontsize=RETROGRADE_TEXT_FONTSIZE, ha='center', va='center', color='red', weight='bold')

    def _draw_aspect_lines(self, aspects_data, all_point_positions):
        """Desenha as linhas dos aspectos no mapa."""
        # Create a dictionary for quick lookup of adjusted longitudes
        point_lon_map = {p['name']: p['lon'] for p in all_point_positions}

        for aspect_info in aspects_data:
            name1 = aspect_info['point1']
            name2 = aspect_info['point2']
            color = aspect_info['color']

            lon1 = point_lon_map.get(name1)
            lon2 = point_lon_map.get(name2)

            if lon1 is not None and lon2 is not None:
                angle1 = np.radians(lon1)
                angle2 = np.radians(lon2)

                self.ax.plot([angle1, angle2], [ASPECT_RADIAL_POS, ASPECT_RADIAL_POS],
                             color=color, linewidth=1.5, linestyle='-')