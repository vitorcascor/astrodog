import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
from .astrological_data import AstrologicalData
from PIL import Image, ImageTk

# Importar as classes e constantes dos outros arquivos
from .astrological_data import AstrologicalData
from .chart_renderer import ChartRenderer
from .constants import PLANET_UNICODE_SYMBOLS # Para símbolos na aba de detalhes

class ChartGUI:
    def __init__(self, master):
        self.master = master
        master.title("Calculadora de Mapa Astral")
        master.geometry("900x850")
        master.resizable(True, True)

        self.astrological_data_calculator = AstrologicalData()
        self.chart_renderer = ChartRenderer()

        self._configure_styles()
        self._create_widgets()
        self._setup_layout()
        self._update_input_fields_state() # Set initial state

    def _configure_styles(self):
        """Configura os estilos para os widgets Tkinter."""
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 10))
        style.configure("TEntry", font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10, "bold"))
        style.configure("TNotebook.Tab", font=("Arial", 10, "bold"))

    def _create_widgets(self):
        """Cria todos os widgets da interface."""
        # --- Input Frame ---
        self.input_frame = ttk.Frame(self.master, padding="20")
        self.input_fields_frame = ttk.Frame(self.input_frame, padding="15", relief="groove", borderwidth=2)

        dog_img_path = 'imagens/pope-dog-8-yrs-later-v0-9fpwk31jva5e1.png'
        dog_img = Image.open(dog_img_path)
        dog_img = dog_img.resize((250, 250), Image.LANCZOS)
        self.dog_photo = ImageTk.PhotoImage(dog_img)

        self.image_label = ttk.Label(self.input_frame, image=self.dog_photo)
        self.image_label.grid(row=0, column=1, padx=(10,0), sticky=tk.N)

        # Chart Type Selection
        ttk.Label(self.input_fields_frame, text="Tipo de Mapa:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.chart_type_var = tk.StringVar(value='natal')
        self.natal_radio = ttk.Radiobutton(self.input_fields_frame, text="Mapa Natal", variable=self.chart_type_var, value='natal', command=self._update_input_fields_state)
        self.natal_radio.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        self.horary_radio = ttk.Radiobutton(self.input_fields_frame, text="Mapa Horário (Tempo Real)", variable=self.chart_type_var, value='horary', command=self._update_input_fields_state)
        self.horary_radio.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        # Date and Time
        ttk.Label(self.input_fields_frame, text="Data (AAAA-MM-DD):").grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
        self.date_entry = ttk.Entry(self.input_fields_frame, width=30)
        self.date_entry.grid(row=2, column=1, pady=5, padx=5)
        self.date_entry.insert(0, "1970-01-01")

        ttk.Label(self.input_fields_frame, text="Hora (HH:MM):").grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
        self.time_entry = ttk.Entry(self.input_fields_frame, width=30)
        self.time_entry.grid(row=3, column=1, pady=5, padx=5)
        self.time_entry.insert(0, "00:00")

        # Location
        ttk.Label(self.input_fields_frame, text="Local (Cidade, País):").grid(row=4, column=0, sticky=tk.W, pady=5, padx=5)
        self.location_entry = ttk.Entry(self.input_fields_frame, width=30)
        self.location_entry.grid(row=4, column=1, pady=5, padx=5)
        self.location_entry.insert(0, "São Paulo, Brazil")

        # House System
        ttk.Label(self.input_fields_frame, text="Sistema de Casas:").grid(row=5, column=0, sticky=tk.W, pady=5, padx=5)
        self.house_system_var = tk.StringVar(value='Placidus')
        self.house_system_dropdown = ttk.Combobox(self.input_fields_frame, textvariable=self.house_system_var,
                                                   values=['Placidus', 'Regiomontanus'], state='readonly', width=28)
        self.house_system_dropdown.grid(row=5, column=1, sticky=tk.W, pady=5, padx=5)

        # Calculate Button
        self.calculate_button = ttk.Button(self.input_fields_frame, text="Gerar Mapa Astral", command=self._on_calculate)
        self.calculate_button.grid(row=6, column=0, columnspan=2, pady=20)

        # --- Notebook (Chart and Details Tabs) ---
        self.notebook = ttk.Notebook(self.master)

        # Chart Tab
        self.chart_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.chart_tab, text="Mapa Astral")
        self.chart_frame = ttk.Frame(self.chart_tab)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = None
        self.toolbar = None

        # Details Tab
        self.details_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.details_tab, text="Detalhes Astrológicos")
        self.details_frame = ttk.Frame(self.details_tab)
        self.details_frame.pack(fill=tk.BOTH, expand=True)

        self.details_text_widget = tk.Text(self.details_frame, wrap=tk.WORD, state=tk.DISABLED,
                                          font=("Courier New", 10), padx=10, pady=10)
        self.details_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.details_frame, command=self.details_text_widget.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.details_text_widget.config(yscrollcommand=self.scrollbar.set)

        # --- Back Button ---
        self.back_button = ttk.Button(self.master, text="←", command=self._show_input_frame, width=5)
        self.back_button.place_forget() # Initially hidden

    def _setup_layout(self):
        """Configura o layout inicial dos frames."""
        self.input_frame.pack(fill=tk.BOTH, expand=True)
        self.input_fields_frame.grid(row=0, column=0, sticky=tk.N)
        self.input_fields_frame.columnconfigure(0, weight=1)
        self.input_fields_frame.columnconfigure(1, weight=1)

    def _update_input_fields_state(self):
        """Atualiza o estado dos campos de entrada com base no tipo de mapa."""
        if self.chart_type_var.get() == 'horary':
            self.date_entry.config(state=tk.DISABLED)
            self.time_entry.config(state=tk.DISABLED)
            self.date_entry.delete(0, tk.END)
            self.time_entry.delete(0, tk.END)
            self.date_entry.insert(0, "Tempo Atual")
            self.time_entry.insert(0, "Tempo Atual")
            self.house_system_var.set('Regiomontanus')
        else: # 'natal'
            self.date_entry.config(state=tk.NORMAL)
            self.time_entry.config(state=tk.NORMAL)
            self.date_entry.delete(0, tk.END)
            self.time_entry.delete(0, tk.END)
            self.date_entry.insert(0, "1970-01-01")
            self.time_entry.insert(0, "00:00")
            self.house_system_var.set('Placidus')

    def _show_input_frame(self):
        """Esconde o notebook e mostra o frame de entrada."""
        self.notebook.pack_forget()
        self.input_frame.pack(fill=tk.BOTH, expand=True)
        self.back_button.place_forget()

        # Clean up previous chart/details
        if self.chart_renderer.fig is not None:
            plt.close(self.chart_renderer.fig)
            self.chart_renderer.fig = None
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.toolbar is not None:
            self.toolbar.destroy()
            self.toolbar = None
        
        self.details_text_widget.config(state=tk.NORMAL)
        self.details_text_widget.delete(1.0, tk.END)
        self.details_text_widget.config(state=tk.DISABLED)

    def _on_calculate(self):
        """Manipulador para o botão 'Gerar Mapa Astral'."""
        chart_type = self.chart_type_var.get()
        house_system = self.house_system_var.get()
        location_input = self.location_entry.get()
        date_input = self.date_entry.get()
        time_input = self.time_entry.get()

        if not location_input:
            messagebox.showwarning("Entrada Inválida", "Por favor, forneça uma localização.")
            return

        if chart_type == 'natal' and (not date_input or not time_input):
            messagebox.showwarning("Entrada Inválida", "Para o Mapa Natal, a data e a hora são obrigatórias.")
            return

        # Step 1: Get Location Details
        latitude, longitude, timezone_id, loc_error = self.astrological_data_calculator.get_location_details(location_input)
        if loc_error:
            messagebox.showerror("Erro de Localização", loc_error)
            return

        # Step 2: Calculate Chart Data
        chart_data, calc_error = self.astrological_data_calculator.calculate_chart_data(
            chart_type, house_system, date_input, time_input, latitude, longitude, timezone_id
        )

        if calc_error:
            messagebox.showerror("Erro de Cálculo", calc_error)
            return

        # If all calculations are successful, hide input frame and show chart/details
        self.input_frame.pack_forget()

        # Step 3: Render Chart
        fig = self.chart_renderer.create_chart_plot(chart_data)

        # Clear previous canvas/toolbar if they exist
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.toolbar:
            self.toolbar.destroy()

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.chart_frame)
        self.toolbar.update()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Step 4: Populate Details Tab
        self._populate_details_tab(chart_data, location_input)

        # Show notebook and back button
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.notebook.select(self.chart_tab)
        self.back_button.place(relx=1.0, rely=0.0, anchor=tk.NE, x=-10, y=10)

    def _populate_details_tab(self, chart_data, location_input_str):
        """Preenche o widget de texto de detalhes com os dados do mapa."""
        self.details_text_widget.config(state=tk.NORMAL)
        self.details_text_widget.delete(1.0, tk.END)

        chart_title_type = "Mapa Natal" if chart_data['chart_type'] == 'natal' else "Mapa Horário"
        self.details_text_widget.insert(tk.END, f"--- Detalhes do {chart_title_type} ({chart_data['house_system']} Casas) ---\n\n")
        self.details_text_widget.insert(tk.END, f"Data/Hora: {chart_data['birth_date'].strftime('%Y-%m-%d %H:%M')}\n")
        self.details_text_widget.insert(tk.END, f"Local: {location_input_str} (Lat: {chart_data['latitude']:.2f}, Lon: {chart_data['longitude']:.2f}, Fuso: {chart_data['timezone_id']})\n\n")

        self.details_text_widget.insert(tk.END, "=== Posições de Pontos Astrológicos ===\n")
        for pos_str in chart_data['textual_point_positions']:
            # Add unicode symbol from constants
            for p_name, p_symbol in PLANET_UNICODE_SYMBOLS.items():
                if pos_str.startswith(f"{p_name}:"):
                    pos_str = pos_str.replace(f"{p_name}:", f"{p_name} {p_symbol}:")
                    break
            self.details_text_widget.insert(tk.END, f"- {pos_str}\n")
        self.details_text_widget.insert(tk.END, "\n")

        self.details_text_widget.insert(tk.END, "=== Cúspides das Casas ===\n")
        for cusp_str in chart_data['textual_house_cusps']:
            self.details_text_widget.insert(tk.END, f"- {cusp_str}\n")
        self.details_text_widget.insert(tk.END, "\n")

        self.details_text_widget.insert(tk.END, "=== Aspectos ===\n")
        if chart_data['textual_aspects']:
            for aspect_str in chart_data['textual_aspects']:
                self.details_text_widget.insert(tk.END, f"- {aspect_str}\n")
        else:
            self.details_text_widget.insert(tk.END, "Nenhum aspecto maior encontrado com orbe de 8°.\n")
        self.details_text_widget.insert(tk.END, "\n")

        self.details_text_widget.config(state=tk.DISABLED)

    def run(self):
        """Inicia o loop principal do Tkinter."""
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.master.mainloop()

    def _on_closing(self):
        """Lida com o fechamento da janela, garantindo que as figuras Matplotlib sejam fechadas."""
        if self.chart_renderer.fig is not None:
            plt.close(self.chart_renderer.fig)
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChartGUI(root)
    app.run()