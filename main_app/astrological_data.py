import swisseph as swe
import datetime
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import numpy as np

# Supondo que essas constantes vêm de seu arquivo constants.py
from .constants import (
    NATAL_POINTS_CALCULABLE, HORARY_POINTS_CALCULABLE,
    RETROGRADE_PLANETS, SIGNS # Certifique-se de que SIGNS está definido
)

class AstrologicalData:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="astral_chart_app")
        self.tf = TimezoneFinder()

    def get_location_details(self, location_input_str):
        """Obtém latitude, longitude e fuso horário para uma localização."""
        try:
            location = self.geolocator.geocode(location_input_str)
            if not location:
                return None, None, None, "Localização não encontrada."

            latitude = location.latitude
            longitude = location.longitude
            timezone_id = self.tf.timezone_at(lng=longitude, lat=latitude)

            if not timezone_id:
                timezone_id = "UTC" # Fallback
                return latitude, longitude, timezone_id, "Fuso horário não determinado. Usando UTC."

            return latitude, longitude, timezone_id, None # No error

        except Exception as e:
            return None, None, None, f"Erro ao buscar localização: {e}"

    def _is_day_chart(self, sun_lon, houses):
        """
        Determina se o mapa é diurno ou noturno.
        Um mapa é diurno se o Sol está acima do horizonte (Casas 7 a 12).
        houses[0] é o Ascendente (Cúspide da Casa 1)
        houses[6] é o Descendente (Cúspide da Casa 7)
        """
        asc_lon = houses[0]
        des_lon = (houses[0] + 180) % 360 # Descendente é 180 graus do Ascendente

        # Normaliza longitudes para um range contínuo se necessário para comparação
        # Isso lida com o cruzar de 0/360 graus
        if des_lon < asc_lon:
            if sun_lon >= asc_lon or sun_lon < des_lon:
                return True # Sol no hemisfério superior
            else:
                return False # Sol no hemisfério inferior
        else:
            if sun_lon >= asc_lon and sun_lon < des_lon:
                return False # Sol no hemisfério inferior
            else:
                return True # Sol no hemisfério superior

    def calculate_chart_data(self, chart_type, house_system, date_str, time_str, latitude, longitude, timezone_id):
        """
        Calcula as posições dos planetas, nodos, Part of Fortune e cúspides das casas.
        Retorna um dicionário com os dados do mapa ou None em caso de erro.
        """
        try:
            if chart_type == 'natal':
                birth_date = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            elif chart_type == 'horary':
                birth_date = datetime.datetime.now(pytz.timezone(timezone_id))
                date_str = birth_date.strftime("%Y-%m-%d") # Update for display
                time_str = birth_date.strftime("%H:%M") # Update for display

            utc_birth_date = birth_date.astimezone(pytz.utc)
            jd = swe.julday(utc_birth_date.year, utc_birth_date.month, utc_birth_date.day,
                            utc_birth_date.hour + utc_birth_date.minute / 60.0)

            point_positions = []
            swe_points_map = {
                'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
                'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
                'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE,
                'Pluto': swe.PLUTO, 'True Node': swe.MEAN_NODE # Ou swe.TRUE_NODE se preferir
            }

            points_to_calculate = NATAL_POINTS_CALCULABLE if chart_type == 'natal' else HORARY_POINTS_CALCULABLE

            for name in points_to_calculate:
                if name in swe_points_map:
                    swe_id = swe_points_map.get(name)
                    xx = swe.calc_ut(jd, swe_id, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
                    
                    lon = xx[0]         # Longitude
                    speed = xx[3]       # Velocidade da longitude (graus/dia)

                    is_retrograde = False
                    if name in RETROGRADE_PLANETS and speed < 0:
                        is_retrograde = True

                    point_positions.append({
                        'name': name,
                        'lon': lon,
                        'retrograde': is_retrograde,
                        'speed': speed
                    })

            # Calculate Houses
            houses_bytes = b'P' if house_system == 'Placidus' else b'R'
            houses, ascmc = swe.houses(jd, latitude, longitude, houses_bytes)
            asc = ascmc[0]
            mc = ascmc[1]

            # --- MODIFICAÇÃO AQUI PARA A PARTE DA FORTUNA ---
            moon_lon = next((p['lon'] for p in point_positions if p['name'] == 'Moon'), None)
            sun_lon = next((p['lon'] for p in point_positions if p['name'] == 'Sun'), None)

            if moon_lon is not None and sun_lon is not None:
                is_day_chart = self._is_day_chart(sun_lon, houses)

                if is_day_chart:
                    # Fórmula diurna: Asc + Lua - Sol
                    fortune_lon = (asc + moon_lon - sun_lon) % 360
                else:
                    # Fórmula noturna: Asc - Lua + Sol
                    fortune_lon = (asc - moon_lon + sun_lon) % 360
                    # Garante que o resultado seja positivo
                    if fortune_lon < 0:
                        fortune_lon += 360

                point_positions.append({'name': 'Fortune', 'lon': fortune_lon, 'retrograde': False, 'speed': 0})
            # --- FIM DA MODIFICAÇÃO ---
            
            # Calculate South Node (180 degrees opposite to True Node)
            true_node_lon = next((p['lon'] for p in point_positions if p['name'] == 'True Node'), None)
            if true_node_lon is not None:
                south_node_lon = (true_node_lon + 180) % 360
                point_positions.append({'name': 'True Node South', 'lon': south_node_lon, 'retrograde': False, 'speed': 0})

            # Format house cusps for display
            textual_house_cusps = []
            for i in range(1, 13):
                cusp_lon = houses[i-1]
                sign_at_cusp = self._get_sign(cusp_lon)
                degree_in_sign = self._get_degree_in_sign(cusp_lon)
                degrees = int(degree_in_sign)
                minutes = int((degree_in_sign - degrees) * 60)
                textual_house_cusps.append(f"Casa {i}: {degrees}°{minutes:02d}' {sign_at_cusp}")

            # Calculate aspects
            aspects_data, textual_aspects = self._calculate_aspects(point_positions)

            # Format point positions for display
            textual_point_positions = []
            for p_data in point_positions:
                sign_of_point = self._get_sign(p_data['lon'])
                degree_in_sign = self._get_degree_in_sign(p_data['lon'])
                degrees = int(degree_in_sign)
                minutes = int((degree_in_sign - degrees) * 60)
                retro_status = " (R)" if p_data['retrograde'] else ""
                textual_point_positions.append(
                    f"{p_data['name']}: {degrees}°{minutes:02d}' {sign_of_point}{retro_status} ({p_data['lon']:.2f}°)"
                )

            return {
                'chart_type': chart_type,
                'house_system': house_system,
                'birth_date': birth_date,
                'date_str': date_str,
                'time_str': time_str,
                'jd': jd,
                'latitude': latitude,
                'longitude': longitude,
                'timezone_id': timezone_id,
                'point_positions': point_positions,
                'houses': houses,
                'asc': asc,
                'mc': mc,
                'textual_house_cusps': textual_house_cusps,
                'aspects_data': aspects_data,
                'textual_aspects': textual_aspects,
                'textual_point_positions': textual_point_positions
            }, None # No error

        except ValueError as e:
            return None, f"Erro no formato de data/hora: {e}. Use AAAA-MM-DD e HH:MM."
        except pytz.UnknownTimeZoneError:
            return None, "Fuso horário inválido. Verifique o local ou o fuso."
        except Exception as e:
            return None, f"Erro inesperado no cálculo astrológico: {e}"

    def _get_sign(self, longitude):
        """Helper to get sign from longitude."""
        sign_index = int(longitude / 30) % 12
        return SIGNS[sign_index]

    def _get_degree_in_sign(self, longitude):
        """Helper to get degree within sign from longitude."""
        return longitude % 30

    def _calculate_aspects(self, point_positions, orb=8):
        """Calcula e formata os aspectos entre os planetas."""
        aspects = {
            "Conjunção": (0, 'red'),
            "Oposição": (180, 'red'),
            "Trígono": (120, '#008000'), # Green
            "Quadratura": (90, 'red'),
            "Sextil": (60, '#008000'), # Green
        }

        aspect_lines_info = []
        textual_aspects = []
        
        # Filter for actual planets for aspects (excluding nodes/fortune)
        planet_names_for_aspects = [
            'Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
            'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'
        ]
        
        aspect_points = [p for p in point_positions if p['name'] in planet_names_for_aspects]

        for i in range(len(aspect_points)):
            for j in range(i + 1, len(aspect_points)):
                name1 = aspect_points[i]['name']
                lon1 = aspect_points[i]['lon']
                name2 = aspect_points[j]['name']
                lon2 = aspect_points[j]['lon']

                diff = abs(lon1 - lon2)
                if diff > 180:
                    diff = 360 - diff

                for aspect_name, (angle, color) in aspects.items():
                    if abs(diff - angle) <= orb:
                        aspect_lines_info.append({'point1': name1, 'point2': name2, 'color': color})
                        textual_aspects.append(f"{name1} - {name2}: {aspect_name} ({diff:.2f}°)")
                        break # Found an aspect, move to next pair
        return aspect_lines_info, textual_aspects