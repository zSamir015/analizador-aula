"""Interfaz gráfica del analizador AULA (Etapa 2, puntos 5 y 6).

    python3 interfaz.py

Punto 6: el botón "Seleccionar archivo" solicita el archivo de entrada (además
de accesos rápidos a los archivos de ejemplo del proyecto).
Punto 5: los errores se muestran mientras se evalúa el archivo (la interfaz se
suscribe al manejador de errores) y el botón "Ver tabla de símbolos" abre la
tabla de símbolos interactiva al terminar.
"""

import re
import sys
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from aula import (
    ERRORES,
    ManejadorErrores,
    TablaSimbolos,
    analizar_archivo,
    analizar_lineas,
)
from aula.tokens import DIAS, PALABRAS_RESERVADAS, TIPOS_DATO
from aula.validador import leer_archivo

PAUSA_MS = 28  # tiempo entre líneas para mostrar el avance en vivo

# Paletas de color (Oscuro estilo IDE por defecto + Claro académico de 2a6b03b)
TEMAS = {
    "oscuro": {
        "nombre": "Oscuro",
        "fondo": "#0B0F17",
        "superficie": "#111827",
        "superficie_alt": "#161F30",
        "editor": "#0D131F",
        "gutter": "#090D16",
        "borde": "#1E293B",
        "borde_fuerte": "#334155",
        "texto": "#F1F5F9",
        "tenue": "#94A3B8",
        "apagado": "#64748B",
        "acento": "#2563EB",
        "acento_activo": "#1D4ED8",
        "acento_claro": "#38BDF8",
        "azul_fondo": "#172554",
        "verde": "#10B981",
        "verde_fondo": "#062E22",
        "rojo": "#F43F5E",
        "rojo_fondo": "#2D0F18",
        "ambar": "#F59E0B",
        "scroll_thumb": "#334155",
        "scroll_activo": "#475569",
        "fila_par": "#111A2B",
        # Sintaxis en el visor de código
        "syn_reservada": "#60A5FA",
        "syn_tipo": "#38BDF8",
        "syn_dia": "#FBBF24",
        "syn_entidad": "#34D399",
        "syn_cadena": "#A7F3D0",
        "syn_numero": "#FB923C",
        "syn_comentario": "#64748B",
    },
    "claro": {
        "nombre": "Claro",
        "fondo": "#F3F5F8",
        "superficie": "#FFFFFF",
        "superficie_alt": "#F8FAFC",
        "editor": "#FFFFFF",
        "gutter": "#F1F5F9",
        "borde": "#D8DEE6",
        "borde_fuerte": "#CBD2DA",
        "texto": "#1F2933",
        "tenue": "#52606D",
        "apagado": "#7B8794",
        "acento": "#2563EB",
        "acento_activo": "#1D4ED8",
        "acento_claro": "#1D4ED8",
        "azul_fondo": "#EFF4FF",
        "verde": "#15803D",
        "verde_fondo": "#ECFDF3",
        "rojo": "#B42318",
        "rojo_fondo": "#FEF3F2",
        "ambar": "#B45309",
        "scroll_thumb": "#CBD2DA",
        "scroll_activo": "#9AA5B1",
        "fila_par": "#F8FAFC",
        # Sintaxis en el visor de código
        "syn_reservada": "#1D4ED8",
        "syn_tipo": "#0369A1",
        "syn_dia": "#B45309",
        "syn_entidad": "#047857",
        "syn_cadena": "#15803D",
        "syn_numero": "#C2410C",
        "syn_comentario": "#7B8794",
    },
}

# Expresiones regulares para resaltado léxico en el visor de código fuente
_RE_CADENA = re.compile(r'"[^"\n]*"?')
_RE_COMENTARIO = re.compile(r"#.*$")
_RE_CODIGO_MAT = re.compile(r"\b[A-Z]{2,4}-[0-9]{3}\b")
_RE_GRUPO = re.compile(r"\b[0-9][A-Z]{2}[0-9]{3}\b")
_RE_AULA = re.compile(r"\b[0-9]{1,2}-[0-9]{3}\b")
_RE_RANGO_HORA = re.compile(
    r"\b(?:[01]?[0-9]|2[0-3]):[0-5][0-9]-(?:[01]?[0-9]|2[0-3]):[0-5][0-9]\b"
)
_RE_HORA = re.compile(r"\b(?:[01]?[0-9]|2[0-3]):[0-5][0-9]\b")
_RE_NUMERO = re.compile(r"\b[0-9]+(?:\.[0-9]+)?\b")
_RE_PALABRA = re.compile(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b")


class InterfazAULA:
    def __init__(self, ventana, tema="oscuro"):
        self.ventana = ventana
        self.ventana.title("AULA — Analizador Léxico del lenguaje de asignación de horarios")
        self.ventana.geometry("1240x800")
        self.ventana.minsize(960, 620)

        self.tema_actual = tema if tema in TEMAS else "oscuro"
        self.paleta = TEMAS[self.tema_actual]

        self.ruta = None
        self.proceso = None
        self.analizando = False
        self.validas = 0
        self.lineas = 0
        self.total_lineas = 0

        self.manejador = ManejadorErrores()
        self.tabla = TablaSimbolos()

        # Estado de diagnóstico enriquecido
        self._resultados_linea = {}   # num_linea -> ResultadoLinea
        self._todos_tokens = []       # [(ResultadoLinea, Token), ...]
        self._conteo_tokens = {}  # codigo -> int
        self._filtro_consola = "todos"
        self.ventana_tabla = None

        self.animar_var = tk.BooleanVar(value=True)
        self.filtro_token_var = tk.StringVar(value="")

        self.crear_estilos()
        self.crear_interfaz()

    # ------------------------------------------------------------------
    # Estilos y sistema de temas (compatible macOS / Windows / Linux)
    # ------------------------------------------------------------------
    def crear_estilos(self):
        base = tkfont.nametofont("TkDefaultFont")
        familia = base.actual("family")
        self.f_familia = familia
        self.f_titulo = (familia, 15, "bold")
        self.f_subtitulo = (familia, 9)
        self.f_seccion = (familia, 10, "bold")
        self.f_numero = (familia, 18, "bold")
        self.f_etiqueta = (familia, 9)
        self.f_etiqueta_neg = (familia, 9, "bold")
        mono = tkfont.nametofont("TkFixedFont").actual("family")
        self.f_mono = (mono, 10)
        self.f_mono_neg = (mono, 10, "bold")
        self.f_mono_peq = (mono, 9)

        self.estilo = ttk.Style(self.ventana)
        if "clam" in self.estilo.theme_names():
            self.estilo.theme_use("clam")

        # Barras de desplazamiento delgadas sin flechas
        for orient, lado in (("Vertical", "ns"), ("Horizontal", "ew")):
            nombre = f"{orient}.TScrollbar"
            self.estilo.layout(
                nombre,
                [
                    (
                        f"{orient}.Scrollbar.trough",
                        {
                            "sticky": lado,
                            "children": [
                                (
                                    f"{orient}.Scrollbar.thumb",
                                    {"expand": "1", "sticky": "nswe"},
                                )
                            ],
                        },
                    )
                ],
            )

        self._aplicar_estilos_tema()

    def _aplicar_estilos_tema(self):
        c = self.paleta
        familia = self.f_familia
        e = self.estilo

        self.ventana.configure(bg=c["fondo"])

        e.configure(
            ".",
            background=c["fondo"],
            foreground=c["texto"],
            bordercolor=c["borde"],
            lightcolor=c["superficie"],
            darkcolor=c["superficie"],
            font=(familia, 10),
        )
        e.configure("TFrame", background=c["fondo"])
        e.configure("Superficie.TFrame", background=c["superficie"])
        e.configure("TPanedwindow", background=c["fondo"])

        # Botones ttk estándar (funcionan correctamente en macOS Aqua, Windows y Linux)
        e.configure(
            "TButton",
            padding=(12, 6),
            background=c["superficie_alt"],
            foreground=c["texto"],
            bordercolor=c["borde_fuerte"],
            lightcolor=c["superficie_alt"],
            darkcolor=c["superficie_alt"],
            focuscolor=c["superficie_alt"],
            relief="flat",
            font=(familia, 9, "bold"),
        )
        e.map(
            "TButton",
            background=[("disabled", c["fondo"]), ("active", c["borde"])],
            foreground=[("disabled", c["apagado"])],
        )

        # Botón primario de acento
        e.configure(
            "Acento.TButton",
            padding=(14, 6),
            background=c["acento"],
            foreground="#FFFFFF",
            bordercolor=c["acento"],
            lightcolor=c["acento"],
            darkcolor=c["acento"],
            focuscolor=c["acento"],
            relief="flat",
            font=(familia, 9, "bold"),
        )
        e.map(
            "Acento.TButton",
            background=[("disabled", c["borde"]), ("active", c["acento_activo"])],
            bordercolor=[("disabled", c["borde"]), ("active", c["acento_activo"])],
            foreground=[("disabled", c["apagado"]), ("!disabled", "#FFFFFF")],
        )

        # Botones compactos de ejemplo / pestañas
        e.configure(
            "Chip.TButton",
            padding=(9, 4),
            background=c["superficie_alt"],
            foreground=c["tenue"],
            bordercolor=c["borde"],
            lightcolor=c["superficie_alt"],
            darkcolor=c["superficie_alt"],
            focuscolor=c["superficie_alt"],
            relief="flat",
            font=(familia, 9),
        )
        e.map(
            "Chip.TButton",
            background=[("disabled", c["fondo"]), ("active", c["borde"])],
            foreground=[("disabled", c["apagado"]), ("active", c["texto"])],
        )

        e.configure(
            "ChipActivo.TButton",
            padding=(9, 4),
            background=c["acento"],
            foreground="#FFFFFF",
            bordercolor=c["acento"],
            lightcolor=c["acento"],
            darkcolor=c["acento"],
            focuscolor=c["acento"],
            relief="flat",
            font=(familia, 9, "bold"),
        )
        e.map(
            "ChipActivo.TButton",
            background=[("active", c["acento_activo"])],
            foreground=[("!disabled", "#FFFFFF")],
        )

        # Barra de progreso
        e.configure(
            "Horizontal.TProgressbar",
            troughcolor=c["borde"],
            background=c["acento"],
            bordercolor=c["fondo"],
            lightcolor=c["acento"],
            darkcolor=c["acento"],
            thickness=5,
        )

        # Barras de desplazamiento
        for orient in ("Vertical", "Horizontal"):
            nombre = f"{orient}.TScrollbar"
            e.configure(
                nombre,
                background=c["scroll_thumb"],
                troughcolor=c["editor"],
                bordercolor=c["editor"],
                lightcolor=c["scroll_thumb"],
                darkcolor=c["scroll_thumb"],
                gripcount=0,
                arrowsize=10,
            )
            e.map(nombre, background=[("active", c["scroll_activo"])])

        # Treeview
        e.configure(
            "Treeview",
            background=c["editor"],
            fieldbackground=c["editor"],
            foreground=c["texto"],
            rowheight=25,
            bordercolor=c["borde"],
            lightcolor=c["editor"],
            darkcolor=c["editor"],
            borderwidth=0,
            font=self.f_mono_peq,
        )
        e.configure(
            "Treeview.Heading",
            background=c["superficie_alt"],
            foreground=c["texto"],
            bordercolor=c["borde"],
            lightcolor=c["superficie_alt"],
            darkcolor=c["superficie_alt"],
            relief="flat",
            font=(familia, 9, "bold"),
            padding=(8, 6),
        )
        e.map(
            "Treeview",
            background=[("selected", c["azul_fondo"])],
            foreground=[("selected", c["acento_claro"])],
        )
        e.map(
            "Treeview.Heading",
            background=[("active", c["borde"])],
        )

    def tarjeta(self, padre, **grid):
        """Marco con superficie elevada y borde fino de 1 px."""
        c = self.paleta
        marco = tk.Frame(
            padre,
            bg=c["superficie"],
            highlightthickness=1,
            highlightbackground=c["borde"],
            highlightcolor=c["borde"],
        )
        if grid:
            marco.grid(**grid)
        return marco

    def alternar_tema(self):
        nuevo = "claro" if self.tema_actual == "oscuro" else "oscuro"
        self.tema_actual = nuevo
        self.paleta = TEMAS[nuevo]
        self._aplicar_estilos_tema()

        # Reconstruir interfaz conservando el estado y resultados actuales
        ruta_prev = self.ruta
        resultados_prev = dict(self._resultados_linea)
        tokens_prev = list(self._todos_tokens)
        tokens_tipo_prev = dict(self._conteo_tokens)
        validas_prev = self.validas
        lineas_prev = self.lineas
        total_prev = self.total_lineas
        codigo_prev = self.editor_codigo.get("1.0", "end-1c")
        estado_prev = self.estado.get()
        tabla_habilitada = str(self.boton_tabla["state"]) == "normal"

        for hijo in self.ventana.winfo_children():
            if not isinstance(hijo, tk.Toplevel):
                hijo.destroy()

        self.crear_interfaz()

        self.ruta = ruta_prev
        self._resultados_linea = resultados_prev
        self._todos_tokens = tokens_prev
        self._conteo_tokens = tokens_tipo_prev
        self.validas = validas_prev
        self.lineas = lineas_prev
        self.total_lineas = total_prev
        self.estado.set(estado_prev)

        if ruta_prev:
            self.etiqueta_archivo.config(text=Path(ruta_prev).name)
            self.etiqueta_ruta.config(text=str(Path(ruta_prev).parent))
            self.boton_analizar.config(state="normal")

        if codigo_prev:
            self._escribir_editor(codigo_prev)
            self._aplicar_colores_lineas_editor()

        if resultados_prev or self.manejador.registros:
            self._reconstruir_vistas_tras_tema()

        if tabla_habilitada:
            self.boton_tabla.config(state="normal")

        if self.ventana_tabla is not None and self.ventana_tabla.ventana.winfo_exists():
            self.ventana_tabla.ventana.destroy()
            self.mostrar_tabla()

    # ------------------------------------------------------------------
    # Construcción de la interfaz principal
    # ------------------------------------------------------------------
    def crear_interfaz(self):
        v = self.ventana
        c = self.paleta
        v.columnconfigure(0, weight=1)
        v.rowconfigure(3, weight=1)

        # ==============================================================
        # FILA 0: ENCABEZADO SUPERIOR + SELECTOR DE TEMA Y EJEMPLOS
        # ==============================================================
        encabezado = tk.Frame(
            v,
            bg=c["superficie"],
            highlightthickness=1,
            highlightbackground=c["borde"],
        )
        encabezado.grid(row=0, column=0, sticky="ew")
        encabezado.columnconfigure(1, weight=1)

        # Marca izquierda
        marca = tk.Frame(encabezado, bg=c["superficie"])
        marca.grid(row=0, column=0, sticky="w", padx=20, pady=12)

        tk.Label(
            marca,
            text=" AULA ",
            font=self.f_mono_neg,
            bg=c["acento"],
            fg="#FFFFFF",
            padx=6,
            pady=3,
        ).pack(side="left", padx=(0, 12))

        titulos = tk.Frame(marca, bg=c["superficie"])
        titulos.pack(side="left")
        tk.Label(
            titulos,
            text="Analizador del lenguaje AULA",
            font=self.f_titulo,
            bg=c["superficie"],
            fg=c["texto"],
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            titulos,
            text="Análisis léxico con AFD, tabla de símbolos y manejo de errores léxicos",
            font=self.f_subtitulo,
            bg=c["superficie"],
            fg=c["tenue"],
            anchor="w",
        ).pack(anchor="w")

        # Accesos rápidos a ejemplos y selector de tema a la derecha del encabezado
        acciones_enc = tk.Frame(encabezado, bg=c["superficie"])
        acciones_enc.grid(row=0, column=2, sticky="e", padx=20, pady=12)

        tk.Label(
            acciones_enc,
            text="Ejemplos:",
            font=self.f_etiqueta,
            bg=c["superficie"],
            fg=c["tenue"],
        ).pack(side="left", padx=(0, 6))

        self.boton_ej_valido = ttk.Button(
            acciones_enc,
            text="✓ Válido",
            style="Chip.TButton",
            command=lambda: self.cargar_ejemplo("horario_valido.txt"),
        )
        self.boton_ej_valido.pack(side="left", padx=(0, 6))

        self.boton_ej_errores = ttk.Button(
            acciones_enc,
            text="✗ Con errores",
            style="Chip.TButton",
            command=lambda: self.cargar_ejemplo("horario_errores.txt"),
        )
        self.boton_ej_errores.pack(side="left", padx=(0, 10))

        texto_tema = "☀ Claro" if self.tema_actual == "oscuro" else "☾ Oscuro"
        self.boton_tema = ttk.Button(
            acciones_enc,
            text=texto_tema,
            style="Chip.TButton",
            command=self.alternar_tema,
        )
        self.boton_tema.pack(side="left")

        # ==============================================================
        # FILA 1: BARRA DE ARCHIVO Y ACCIONES PRINCIPALES (PUNTO 5 Y 6)
        # ==============================================================
        barra = ttk.Frame(v, padding=(20, 12, 20, 6))
        barra.grid(row=1, column=0, sticky="ew")
        barra.columnconfigure(1, weight=1)

        self.boton_archivo = ttk.Button(
            barra,
            text="Seleccionar archivo…",
            command=self.seleccionar_archivo,
        )
        self.boton_archivo.grid(row=0, column=0)

        archivo = tk.Frame(barra, bg=c["fondo"])
        archivo.grid(row=0, column=1, sticky="ew", padx=14)
        self.etiqueta_archivo = tk.Label(
            archivo,
            text="Ningún archivo seleccionado",
            font=(self.f_familia, 10, "bold"),
            bg=c["fondo"],
            fg=c["texto"],
            anchor="w",
        )
        self.etiqueta_archivo.pack(fill="x")
        self.etiqueta_ruta = tk.Label(
            archivo,
            text="Formatos aceptados: .txt en UTF-8 (con o sin BOM) o ANSI (cp1252)",
            font=self.f_etiqueta,
            bg=c["fondo"],
            fg=c["tenue"],
            anchor="w",
        )
        self.etiqueta_ruta.pack(fill="x")

        self.boton_analizar = ttk.Button(
            barra,
            text="▶ Analizar archivo",
            style="Acento.TButton",
            command=self.analizar,
            state="disabled",
        )
        self.boton_analizar.grid(row=0, column=2, padx=(0, 8))

        self.boton_tabla = ttk.Button(
            barra,
            text="⊞ Ver tabla de símbolos",
            command=self.mostrar_tabla,
            state="disabled",
        )
        self.boton_tabla.grid(row=0, column=3)

        # ==============================================================
        # FILA 2: TARJETAS DE CONTADORES Y BARRA DE PROGRESO
        # ==============================================================
        contadores = ttk.Frame(v, padding=(20, 4, 20, 0))
        contadores.grid(row=2, column=0, sticky="ew")
        self.contadores = {}
        self.sub_contadores = {}
        datos = [
            ("lineas", "Líneas analizadas", c["acento_claro"], "Con contenido ejecutable"),
            ("validas", "Líneas válidas", c["verde"], "Sin errores léxicos"),
            ("invalidas", "Líneas con error", c["rojo"], "Con al menos un error léxico"),
            ("errores", "Errores reportados", c["rojo"], "0 léxicos"),
            ("simbolos", "Símbolos usados", c["ambar"], "Capacidad 53 · Carga 0.604"),
        ]
        for i, (clave, texto, color, subtexto) in enumerate(datos):
            contadores.columnconfigure(i, weight=1, uniform="contador")
            tarjeta = self.tarjeta(
                contadores,
                row=0,
                column=i,
                sticky="ew",
                padx=(0 if i == 0 else 8, 0),
            )
            fila_sup = tk.Frame(tarjeta, bg=c["superficie"])
            fila_sup.pack(fill="x", padx=12, pady=(8, 0))
            numero = tk.Label(
                fila_sup,
                text="0",
                font=self.f_numero,
                bg=c["superficie"],
                fg=color,
            )
            numero.pack(side="left")
            tk.Label(
                tarjeta,
                text=texto,
                font=self.f_etiqueta_neg,
                bg=c["superficie"],
                fg=c["texto"],
            ).pack(anchor="w", padx=12)
            sub_lbl = tk.Label(
                tarjeta,
                text=subtexto,
                font=(self.f_familia, 8),
                bg=c["superficie"],
                fg=c["tenue"],
            )
            sub_lbl.pack(anchor="w", padx=12, pady=(0, 8))
            self.contadores[clave] = numero
            self.sub_contadores[clave] = sub_lbl

        self.progreso = ttk.Progressbar(
            contadores,
            mode="determinate",
            style="Horizontal.TProgressbar",
        )
        self.progreso.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(10, 0))

        # ==============================================================
        # FILA 3: ÁREA DE TRABAJO DIVIDIDA (CÓDIGO FUENTE | DIAGNÓSTICO)
        # ==============================================================
        division = ttk.PanedWindow(v, orient="horizontal")
        division.grid(row=3, column=0, sticky="nsew", padx=20, pady=(10, 8))

        self._construir_visor_codigo(division)
        self._construir_panel_diagnostico(division)

        # ==============================================================
        # FILA 4: BARRA DE ESTADO INFERIOR Y ATAJOS
        # ==============================================================
        estado_bar = tk.Frame(
            v,
            bg=c["superficie"],
            highlightthickness=1,
            highlightbackground=c["borde"],
        )
        estado_bar.grid(row=4, column=0, sticky="ew")

        self.estado = tk.StringVar(value="Seleccione un archivo para comenzar.")
        tk.Label(
            estado_bar,
            textvariable=self.estado,
            font=self.f_etiqueta,
            bg=c["superficie"],
            fg=c["tenue"],
            anchor="w",
        ).pack(side="left", padx=20, pady=6)

        mod = "Cmd" if sys.platform == "darwin" else "Ctrl"
        tk.Label(
            estado_bar,
            text=f"{mod}+O abrir   ·   {mod}+Enter analizar   ·   {mod}+T tabla de símbolos",
            font=self.f_etiqueta,
            bg=c["superficie"],
            fg=c["apagado"],
        ).pack(side="right", padx=20)

        chk_animar = tk.Checkbutton(
            estado_bar,
            text="Evaluación paso a paso",
            variable=self.animar_var,
            bg=c["superficie"],
            fg=c["tenue"],
            activebackground=c["superficie"],
            activeforeground=c["texto"],
            selectcolor=c["superficie_alt"],
            bd=0,
            highlightthickness=0,
            font=self.f_etiqueta,
            cursor="hand2",
        )
        chk_animar.pack(side="right", padx=12)

        tecla = "Command" if sys.platform == "darwin" else "Control"
        v.bind(f"<{tecla}-o>", lambda _e: self.seleccionar_archivo())
        v.bind(f"<{tecla}-Return>", lambda _e: self.analizar())
        v.bind(
            f"<{tecla}-t>",
            lambda _e: self.mostrar_tabla()
            if str(self.boton_tabla["state"]) == "normal"
            else None,
        )

    # ------------------------------------------------------------------
    # Panel izquierdo: Visor de código fuente con numeración y resaltado
    # ------------------------------------------------------------------
    def _construir_visor_codigo(self, division):
        c = self.paleta
        marco = ttk.Frame(division)
        division.add(marco, weight=11)
        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(1, weight=1)

        # Cabecera del panel de código
        cab = tk.Frame(marco, bg=c["fondo"])
        cab.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        tk.Label(
            cab,
            text="Código fuente de entrada",
            font=self.f_seccion,
            bg=c["fondo"],
            fg=c["texto"],
        ).pack(side="left")

        tk.Label(
            cab,
            text="✗ Con error",
            font=self.f_etiqueta,
            bg=c["fondo"],
            fg=c["rojo"],
        ).pack(side="right", padx=(10, 0))
        tk.Label(
            cab,
            text="✓ Válida",
            font=self.f_etiqueta,
            bg=c["fondo"],
            fg=c["verde"],
        ).pack(side="right")

        tarjeta = self.tarjeta(marco, row=1, column=0, sticky="nsew")
        tarjeta.columnconfigure(2, weight=1)
        tarjeta.rowconfigure(0, weight=1)

        self.numeros_linea = tk.Text(
            tarjeta,
            width=6,
            padx=6,
            pady=10,
            font=self.f_mono,
            bg=c["gutter"],
            fg=c["apagado"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            spacing1=1,
            spacing3=1,
            state="disabled",
            wrap="none",
            cursor="arrow",
            takefocus=0,
        )
        self.numeros_linea.grid(row=0, column=0, sticky="ns")
        self.numeros_linea.tag_configure("normal", foreground=c["apagado"], justify="right")
        self.numeros_linea.tag_configure("valido", foreground=c["verde"], justify="right")
        self.numeros_linea.tag_configure("error", foreground=c["rojo"], justify="right")

        tk.Frame(tarjeta, bg=c["borde"], width=1).grid(row=0, column=1, sticky="ns")

        self.editor_codigo = tk.Text(
            tarjeta,
            wrap="none",
            font=self.f_mono,
            bg=c["editor"],
            fg=c["texto"],
            insertbackground=c["acento_claro"],
            selectbackground=c["azul_fondo"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=12,
            pady=10,
            spacing1=1,
            spacing3=1,
            state="disabled",
            cursor="arrow",
        )
        self.editor_codigo.grid(row=0, column=2, sticky="nsew")

        sv = ttk.Scrollbar(tarjeta, orient="vertical", command=self._scroll_codigo_y)
        sv.grid(row=0, column=3, sticky="ns")
        sh = ttk.Scrollbar(tarjeta, orient="horizontal", command=self.editor_codigo.xview)
        sh.grid(row=1, column=2, sticky="ew")
        self._scroll_v_cod = sv
        self.editor_codigo.configure(
            yscrollcommand=self._al_scroll_codigo,
            xscrollcommand=sh.set,
        )

        # Tags de resaltado de líneas y tokens
        self.editor_codigo.tag_configure("linea_valida", background=c["verde_fondo"])
        self.editor_codigo.tag_configure("linea_error", background=c["rojo_fondo"])
        self.editor_codigo.tag_configure("linea_foco", background=c["azul_fondo"])
        self.editor_codigo.tag_configure("lexema_error", underline=True, foreground=c["rojo"])

        self.editor_codigo.tag_configure("syn_reservada", foreground=c["syn_reservada"], font=self.f_mono_neg)
        self.editor_codigo.tag_configure("syn_tipo", foreground=c["syn_tipo"], font=self.f_mono_neg)
        self.editor_codigo.tag_configure("syn_dia", foreground=c["syn_dia"], font=self.f_mono_neg)
        self.editor_codigo.tag_configure("syn_numero", foreground=c["syn_numero"])
        self.editor_codigo.tag_configure("syn_entidad", foreground=c["syn_entidad"])
        self.editor_codigo.tag_configure("syn_cadena", foreground=c["syn_cadena"])
        self.editor_codigo.tag_configure("syn_comentario", foreground=c["syn_comentario"])

        self._escribir_editor(
            "# Seleccione un archivo .txt o pulse uno de los ejemplos superiores\n"
            "# para inspeccionar su código fuente, tokens, errores y tabla de símbolos.\n"
        )

    def _scroll_codigo_y(self, *args):
        self.editor_codigo.yview(*args)
        self.numeros_linea.yview(*args)

    def _al_scroll_codigo(self, primero, ultimo):
        self._scroll_v_cod.set(primero, ultimo)
        self.numeros_linea.yview_moveto(primero)

    def _escribir_editor(self, texto):
        self.editor_codigo.configure(state="normal")
        self.editor_codigo.delete("1.0", tk.END)
        self.editor_codigo.insert("1.0", texto)
        self._resaltar_sintaxis_codigo()
        self.editor_codigo.configure(state="disabled")
        self._actualizar_gutter_codigo()

    def _actualizar_gutter_codigo(self):
        contenido = self.editor_codigo.get("1.0", "end-1c")
        total = max(1, contenido.count("\n") + 1)

        self.numeros_linea.configure(state="normal")
        self.numeros_linea.delete("1.0", tk.END)
        for n in range(1, total + 1):
            res = self._resultados_linea.get(n)
            if res is None:
                marca, tag = " ", "normal"
            elif res.valida:
                marca, tag = "✓", "valido"
            else:
                marca, tag = "✗", "error"
            salto = "\n" if n < total else ""
            self.numeros_linea.insert(tk.END, f"{marca}{n:>3} {salto}", tag)
        self.numeros_linea.configure(state="disabled")
        self.numeros_linea.yview_moveto(self.editor_codigo.yview()[0])

    def _resaltar_sintaxis_codigo(self):
        for tag in (
            "syn_reservada",
            "syn_tipo",
            "syn_dia",
            "syn_numero",
            "syn_entidad",
            "syn_cadena",
            "syn_comentario",
        ):
            self.editor_codigo.tag_remove(tag, "1.0", tk.END)

        lineas = self.editor_codigo.get("1.0", "end-1c").split("\n")
        for idx, texto in enumerate(lineas, start=1):
            if not texto:
                continue
            m_com = _RE_COMENTARIO.search(texto)
            limite = m_com.start() if m_com else len(texto)
            fragmento = texto[:limite]

            for m in _RE_PALABRA.finditer(fragmento):
                pal = m.group(0)
                ini, fin = f"{idx}.{m.start()}", f"{idx}.{m.end()}"
                if pal in TIPOS_DATO:
                    self.editor_codigo.tag_add("syn_tipo", ini, fin)
                elif pal in PALABRAS_RESERVADAS:
                    self.editor_codigo.tag_add("syn_reservada", ini, fin)
                elif pal in DIAS:
                    self.editor_codigo.tag_add("syn_dia", ini, fin)

            for patron in (_RE_RANGO_HORA, _RE_HORA, _RE_NUMERO):
                for m in patron.finditer(fragmento):
                    self.editor_codigo.tag_add(
                        "syn_numero", f"{idx}.{m.start()}", f"{idx}.{m.end()}"
                    )

            for patron in (_RE_CODIGO_MAT, _RE_GRUPO, _RE_AULA):
                for m in patron.finditer(fragmento):
                    ini, fin = f"{idx}.{m.start()}", f"{idx}.{m.end()}"
                    self.editor_codigo.tag_remove("syn_numero", ini, fin)
                    self.editor_codigo.tag_add("syn_entidad", ini, fin)

            for m in _RE_CADENA.finditer(fragmento):
                ini, fin = f"{idx}.{m.start()}", f"{idx}.{m.end()}"
                for t_prev in ("syn_reservada", "syn_tipo", "syn_dia", "syn_numero", "syn_entidad"):
                    self.editor_codigo.tag_remove(t_prev, ini, fin)
                self.editor_codigo.tag_add("syn_cadena", ini, fin)

            if m_com:
                self.editor_codigo.tag_add(
                    "syn_comentario", f"{idx}.{m_com.start()}", f"{idx}.{len(texto)}"
                )

    def _aplicar_colores_lineas_editor(self):
        self.editor_codigo.tag_remove("linea_valida", "1.0", tk.END)
        self.editor_codigo.tag_remove("linea_error", "1.0", tk.END)
        self.editor_codigo.tag_remove("lexema_error", "1.0", tk.END)
        for num, res in self._resultados_linea.items():
            if res.valida:
                self.editor_codigo.tag_add("linea_valida", f"{num}.0", f"{num}.end+1c")
            else:
                self.editor_codigo.tag_add("linea_error", f"{num}.0", f"{num}.end+1c")
                for err in res.errores:
                    c_ini = max(0, err.columna - 1)
                    c_fin = c_ini + max(1, len(err.lexema))
                    self.editor_codigo.tag_add(
                        "lexema_error", f"{num}.{c_ini}", f"{num}.{c_fin}"
                    )
        self._actualizar_gutter_codigo()

    def ir_a_linea(self, numero_linea, columna=1):
        if not numero_linea or int(numero_linea) < 1:
            return
        n = int(numero_linea)
        self.editor_codigo.tag_remove("linea_foco", "1.0", tk.END)
        self.editor_codigo.tag_add("linea_foco", f"{n}.0", f"{n}.end+1c")
        self.editor_codigo.see(f"{n}.{max(0, int(columna) - 1)}")
        self._actualizar_gutter_codigo()

    # ------------------------------------------------------------------
    # Panel derecho: Diagnóstico en vivo, Tabla de Errores, Tokens y Resumen
    # ------------------------------------------------------------------
    def _construir_panel_diagnostico(self, division):
        c = self.paleta
        marco_der = ttk.Frame(division)
        division.add(marco_der, weight=13)
        marco_der.columnconfigure(0, weight=1)
        marco_der.rowconfigure(1, weight=1)

        # Barra de pestañas del panel derecho
        barra_tabs = tk.Frame(marco_der, bg=c["fondo"])
        barra_tabs.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self._botones_tab = {}
        self._vistas_tab = {}
        for clave, texto_t in (
            ("consola", "Diagnóstico en vivo"),
            ("errores", "Tabla de errores (0)"),
            ("tokens", "Tokens (0)"),
        ):
            btn = ttk.Button(
                barra_tabs,
                text=texto_t,
                style="Chip.TButton",
                command=lambda k=clave: self._seleccionar_tab(k),
            )
            btn.pack(side="left", padx=(0, 6))
            self._botones_tab[clave] = btn

        # PanedWindow vertical para la vista principal (Resultados arriba | Resumen abajo)
        paneles = ttk.PanedWindow(marco_der, orient="vertical")
        paneles.grid(row=1, column=0, sticky="nsew")

        # Contenedor superior con las 3 pestañas intercambiables
        contenedor_sup = ttk.Frame(paneles)
        paneles.add(contenedor_sup, weight=3)
        contenedor_sup.columnconfigure(0, weight=1)
        contenedor_sup.rowconfigure(0, weight=1)

        # --- VISTA 1: Consola de resultados y errores detectados ---
        v_consola = self.tarjeta(contenedor_sup, row=0, column=0, sticky="nsew")
        v_consola.columnconfigure(0, weight=1)
        v_consola.rowconfigure(1, weight=1)
        self._vistas_tab["consola"] = v_consola

        sub_filtro = tk.Frame(
            v_consola,
            bg=c["superficie_alt"],
            highlightthickness=1,
            highlightbackground=c["borde"],
            padx=10,
            pady=4,
        )
        sub_filtro.grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(
            sub_filtro,
            text="Filtrar salida:",
            font=self.f_etiqueta,
            bg=c["superficie_alt"],
            fg=c["tenue"],
        ).pack(side="left", padx=(0, 6))

        self._botones_filtro = {}
        for modo_f, et_f in (
            ("todos", "Todo"),
            ("errores", "Solo errores"),
            ("validas", "Solo válidas"),
        ):
            bf = ttk.Button(
                sub_filtro,
                text=et_f,
                style="ChipActivo.TButton" if modo_f == self._filtro_consola else "Chip.TButton",
                command=lambda mf=modo_f: self._cambiar_filtro_consola(mf),
            )
            bf.pack(side="left", padx=(0, 4))
            self._botones_filtro[modo_f] = bf

        self.resultados = tk.Text(
            v_consola,
            wrap="none",
            font=self.f_mono,
            height=13,
            bg=c["editor"],
            fg=c["texto"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=14,
            pady=10,
            spacing1=1,
            spacing3=1,
            state="disabled",
            cursor="arrow",
            insertwidth=0,
        )
        self.resultados.grid(row=1, column=0, sticky="nsew")
        sv_res = ttk.Scrollbar(v_consola, orient="vertical", command=self.resultados.yview)
        sv_res.grid(row=1, column=1, sticky="ns")
        sh_res = ttk.Scrollbar(v_consola, orient="horizontal", command=self.resultados.xview)
        sh_res.grid(row=2, column=0, sticky="ew")
        self.resultados.configure(yscrollcommand=sv_res.set, xscrollcommand=sh_res.set)

        t = self.resultados
        t.tag_configure("valido", foreground=c["verde"], font=self.f_mono_neg)
        t.tag_configure("valido_detalle", foreground=c["tenue"])
        t.tag_configure("error_titulo", foreground=c["rojo"], font=self.f_mono_neg)
        t.tag_configure("error", foreground=c["texto"])
        t.tag_configure("indicador", foreground=c["rojo"], font=self.f_mono_neg)
        t.tag_configure("sugerencia", foreground=c["acento_claro"])
        t.tag_configure("titulo", font=self.f_mono_neg, spacing1=8, foreground=c["texto"])
        t.tag_configure("bloque_error", lmargin1=6, lmargin2=6)
        t.tag_configure("tenue", foreground=c["tenue"])

        self.escribir(t, "Seleccione un archivo y pulse «Analizar archivo».\n", "tenue")

        # --- VISTA 2: Tabla interactiva de errores (clic salta a la línea) ---
        v_errores = self.tarjeta(contenedor_sup, row=0, column=0, sticky="nsew")
        v_errores.columnconfigure(0, weight=1)
        v_errores.rowconfigure(0, weight=1)
        self._vistas_tab["errores"] = v_errores

        cols_e = ("linea", "columna", "codigo", "categoria", "lexema", "descripcion")
        self.tree_errores = ttk.Treeview(
            v_errores, columns=cols_e, show="headings", selectmode="browse"
        )
        for cid, tit_c, w_c, al_c in (
            ("linea", "Línea", 60, "e"),
            ("columna", "Col", 55, "e"),
            ("codigo", "Código", 70, "center"),
            ("categoria", "Categoría", 95, "center"),
            ("lexema", "Lexema", 120, "w"),
            ("descripcion", "Descripción y token esperado", 320, "w"),
        ):
            self.tree_errores.heading(cid, text=tit_c, anchor=al_c)
            self.tree_errores.column(
                cid, width=w_c, anchor=al_c, stretch=(cid == "descripcion")
            )
        self.tree_errores.tag_configure("par", background=c["fila_par"])
        self.tree_errores.tag_configure("LEXICO", foreground=c["rojo"])
        self.tree_errores.grid(row=0, column=0, sticky="nsew")

        sv_e = ttk.Scrollbar(v_errores, orient="vertical", command=self.tree_errores.yview)
        sv_e.grid(row=0, column=1, sticky="ns")
        self.tree_errores.configure(yscrollcommand=sv_e.set)
        self.tree_errores.bind("<<TreeviewSelect>>", self._al_seleccionar_error_tabla)

        # --- VISTA 3: Tabla interactiva de tokens reconocidos ---
        v_tokens = self.tarjeta(contenedor_sup, row=0, column=0, sticky="nsew")
        v_tokens.columnconfigure(0, weight=1)
        v_tokens.rowconfigure(1, weight=1)
        self._vistas_tab["tokens"] = v_tokens

        barra_tok = tk.Frame(
            v_tokens,
            bg=c["superficie_alt"],
            highlightthickness=1,
            highlightbackground=c["borde"],
            padx=10,
            pady=5,
        )
        barra_tok.grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(
            barra_tok,
            text="Filtrar token:",
            font=self.f_etiqueta,
            bg=c["superficie_alt"],
            fg=c["tenue"],
        ).pack(side="left", padx=(0, 6))

        ent_tok = tk.Entry(
            barra_tok,
            textvariable=self.filtro_token_var,
            width=26,
            relief="flat",
            highlightthickness=1,
            highlightbackground=c["borde_fuerte"],
            highlightcolor=c["acento"],
            bg=c["editor"],
            fg=c["texto"],
            insertbackground=c["texto"],
            font=self.f_mono_peq,
        )
        ent_tok.pack(side="left", ipady=3, ipadx=5)
        self.filtro_token_var.trace_add("write", lambda *_: self._llenar_tabla_tokens())

        cols_t = ("linea", "columna", "tipo", "lexema", "estado", "hash")
        self.tree_tokens = ttk.Treeview(
            v_tokens, columns=cols_t, show="headings", selectmode="browse"
        )
        for cid, tit_c, w_c, al_c in (
            ("linea", "Línea", 60, "e"),
            ("columna", "Col", 55, "e"),
            ("tipo", "Tipo de token", 150, "w"),
            ("lexema", "Lexema", 200, "w"),
            ("estado", "Línea", 85, "center"),
            ("hash", "Cubeta", 70, "e"),
        ):
            self.tree_tokens.heading(cid, text=tit_c, anchor=al_c)
            self.tree_tokens.column(cid, width=w_c, anchor=al_c, stretch=(cid == "lexema"))
        self.tree_tokens.tag_configure("par", background=c["fila_par"])
        self.tree_tokens.grid(row=1, column=0, sticky="nsew")

        sv_t = ttk.Scrollbar(v_tokens, orient="vertical", command=self.tree_tokens.yview)
        sv_t.grid(row=1, column=1, sticky="ns")
        self.tree_tokens.configure(yscrollcommand=sv_t.set)
        self.tree_tokens.bind("<<TreeviewSelect>>", self._al_seleccionar_token_tabla)

        # Panel inferior fijo dentro del PanedWindow: Resumen de errores y métricas
        self.resumen_texto = self.panel_texto(
            paneles, "Resumen de errores y diagnóstico", alto=6, peso=1
        )
        self.resumen_texto.tag_configure("titulo", font=self.f_mono_neg, foreground=c["acento_claro"])
        self.resumen_texto.tag_configure("tenue", foreground=c["tenue"])

        self._seleccionar_tab("consola")

    def panel_texto(self, paneles, titulo, alto, peso):
        c = self.paleta
        marco = ttk.Frame(paneles)
        paneles.add(marco, weight=peso)
        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(1, weight=1)
        tk.Label(
            marco, text=titulo, font=self.f_seccion, bg=c["fondo"], fg=c["texto"]
        ).grid(row=0, column=0, sticky="w", pady=(6, 5))
        tarjeta = self.tarjeta(marco, row=1, column=0, sticky="nsew")
        tarjeta.columnconfigure(0, weight=1)
        tarjeta.rowconfigure(0, weight=1)
        texto = tk.Text(
            tarjeta,
            wrap="word",
            font=self.f_mono,
            height=alto,
            bg=c["editor"],
            fg=c["texto"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=14,
            pady=10,
            spacing1=1,
            spacing3=1,
            state="disabled",
            cursor="arrow",
            insertwidth=0,
        )
        texto.grid(row=0, column=0, sticky="nsew")
        sv = ttk.Scrollbar(tarjeta, orient="vertical", command=texto.yview)
        sv.grid(row=0, column=1, sticky="ns")
        texto.configure(yscrollcommand=sv.set)
        return texto

    def _seleccionar_tab(self, clave):
        for k, vista in self._vistas_tab.items():
            if k == clave:
                vista.tkraise()
                self._botones_tab[k].configure(style="ChipActivo.TButton")
            else:
                self._botones_tab[k].configure(style="Chip.TButton")

    def _cambiar_filtro_consola(self, modo):
        self._filtro_consola = modo
        for k, b in self._botones_filtro.items():
            b.configure(style="ChipActivo.TButton" if k == modo else "Chip.TButton")
        self._reconstruir_consola()

    def _al_seleccionar_error_tabla(self, _evento=None):
        sel = self.tree_errores.selection()
        if not sel:
            return
        vals = self.tree_errores.item(sel[0], "values")
        if vals:
            self.ir_a_linea(int(vals[0]), int(vals[1]))

    def _al_seleccionar_token_tabla(self, _evento=None):
        sel = self.tree_tokens.selection()
        if not sel:
            return
        vals = self.tree_tokens.item(sel[0], "values")
        if vals:
            self.ir_a_linea(int(vals[0]), int(vals[1]))

    def _llenar_tabla_tokens(self):
        self.tree_tokens.delete(*self.tree_tokens.get_children())
        busq = self.filtro_token_var.get().strip().lower()
        fila = 0
        for res, tok in self._todos_tokens:
            if busq and (
                busq not in tok.lexema.lower()
                and busq not in tok.tipo.lower()
            ):
                continue
            tags = ("par",) if fila % 2 else ()
            self.tree_tokens.insert(
                "",
                "end",
                tags=tags,
                values=(
                    tok.linea,
                    tok.columna,
                    tok.tipo,
                    tok.lexema,
                    "válida" if res.valida else "con error",
                    self.tabla.indice(tok.lexema),
                ),
            )
            fila += 1

    # ------------------------------------------------------------------
    # Utilidades de escritura y actualización de métricas
    # ------------------------------------------------------------------
    @staticmethod
    def escribir(widget, texto, *tags):
        widget.configure(state="normal")
        widget.insert(tk.END, texto, tags)
        widget.configure(state="disabled")

    @staticmethod
    def limpiar(widget):
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.configure(state="disabled")

    def actualizar_contadores(self):
        invalidas = len(self.manejador.lineas_con_error)
        usados = len(self.tabla.simbolos_usados())
        est = self.tabla.estadisticas()
        lex = len(self.manejador.por_categoria("LEXICO"))

        valores = {
            "lineas": self.lineas,
            "validas": self.validas,
            "invalidas": invalidas,
            "errores": self.manejador.total,
            "simbolos": usados,
        }
        for clave, valor in valores.items():
            if clave in self.contadores:
                self.contadores[clave].config(text=str(valor))

        if "errores" in self.sub_contadores:
            self.sub_contadores["errores"].config(text=f"{lex} léxicos")
        if "simbolos" in self.sub_contadores:
            self.sub_contadores["simbolos"].config(
                text=f"Capacidad {est['capacidad']} · Carga {est['factor_carga']}"
            )
        if "validas" in self.sub_contadores:
            self.sub_contadores["validas"].config(
                text=f"{len(self._todos_tokens)} token(s) reconocidos"
            )

        self.progreso.configure(maximum=max(self.total_lineas, 1), value=self.lineas)

    def actualizar_resumen(self):
        self.limpiar(self.resumen_texto)
        lineas = self.manejador.resumen().split("\n")
        self.escribir(self.resumen_texto, lineas[0] + "\n", "titulo")
        if len(lineas) > 1:
            self.escribir(self.resumen_texto, "\n".join(lineas[1:]) + "\n")

        if self._conteo_tokens:
            res_s = ", ".join(
                f"{k}: {self._conteo_tokens[k]}"
                for k in sorted(self._conteo_tokens)
            )
            self.escribir(
                self.resumen_texto,
                f"\nTokens reconocidos por tipo: {res_s}\n",
                "tenue",
            )

    @staticmethod
    def contar_lineas(ruta):
        """Líneas con contenido (las que se evalúan), para la barra de avance."""
        try:
            texto = leer_archivo(ruta)
        except (OSError, UnicodeError):
            return 0
        return sum(
            1 for l in texto.splitlines() if l.strip() and not l.strip().startswith("#")
        )

    # ------------------------------------------------------------------
    # PARTE 6: Abrir archivo de entrada o cargar ejemplo
    # ------------------------------------------------------------------
    def cargar_ejemplo(self, nombre_archivo):
        if self.analizando:
            return
        ruta_ej = Path(__file__).resolve().parent / "ejemplos" / nombre_archivo
        if not ruta_ej.exists():
            messagebox.showerror("Ejemplo no encontrado", f"No existe {ruta_ej}")
            return
        self._establecer_archivo(str(ruta_ej))

    def seleccionar_archivo(self):
        if self.analizando:
            return

        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo AULA",
            initialdir=str(Path(__file__).resolve().parent / "ejemplos"),
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
        )
        if not ruta:
            return
        self._establecer_archivo(ruta)

    def _establecer_archivo(self, ruta):
        self.ruta = ruta
        self._resultados_linea.clear()
        self._todos_tokens.clear()
        self._conteo_tokens.clear()
        self.validas = 0
        self.lineas = 0

        self.etiqueta_archivo.config(text=Path(ruta).name)
        carpeta = Path(ruta).resolve().parent
        try:
            carpeta = "~/" + str(carpeta.relative_to(Path.home()))
        except ValueError:
            pass
        self.etiqueta_ruta.config(text=str(carpeta))
        self.estado.set("Archivo seleccionado. Listo para analizar.")
        self.boton_analizar.config(state="normal")
        self.boton_tabla.config(state="disabled")

        try:
            texto = leer_archivo(ruta).replace("\r\n", "\n").replace("\r", "\n")
            self._escribir_editor(texto)
        except (OSError, UnicodeError) as err:
            messagebox.showerror("Error al leer archivo", str(err))
            return

        self.limpiar(self.resultados)
        self.limpiar(self.resumen_texto)
        self.tree_errores.delete(*self.tree_errores.get_children())
        self.tree_tokens.delete(*self.tree_tokens.get_children())
        self._botones_tab["errores"].configure(text="Tabla de errores (0)")
        self._botones_tab["tokens"].configure(text="Tokens (0)")
        self.actualizar_contadores()
        self.escribir(
            self.resultados,
            f"Pulse «Analizar archivo» para evaluar {Path(ruta).name}.\n",
            "tenue",
        )

    # ------------------------------------------------------------------
    # Ejecución del análisis
    # ------------------------------------------------------------------
    def analizar(self):
        if self.analizando:
            return
        if not self.ruta:
            messagebox.showwarning(
                "Archivo requerido", "Primero seleccione un archivo .txt."
            )
            return

        # Si se asignó self.ruta por código externo sin llamar a _establecer_archivo,
        # cargar el texto en el visor de código automáticamente.
        if Path(self.ruta).exists():
            try:
                texto = leer_archivo(self.ruta).replace("\r\n", "\n").replace("\r", "\n")
                self._escribir_editor(texto)
            except (OSError, UnicodeError):
                pass

        self.limpiar(self.resultados)
        self.limpiar(self.resumen_texto)
        self._resultados_linea.clear()
        self._todos_tokens.clear()
        self._conteo_tokens.clear()
        self.tree_errores.delete(*self.tree_errores.get_children())
        self.tree_tokens.delete(*self.tree_tokens.get_children())
        self._botones_tab["errores"].configure(text="Tabla de errores (0)")
        self._botones_tab["tokens"].configure(text="Tokens (0)")

        self.manejador = ManejadorErrores()
        self.tabla = TablaSimbolos()
        self.validas = 0
        self.lineas = 0
        self.total_lineas = self.contar_lineas(self.ruta)

        # Suscripción al manejador de errores: cada error llega al detectarse
        self.manejador.suscribir(self.mostrar_error)

        self.analizando = True
        self.boton_tabla.config(state="disabled")
        self.boton_analizar.config(state="disabled")
        self.boton_archivo.config(state="disabled")
        self.boton_ej_valido.config(state="disabled")
        self.boton_ej_errores.config(state="disabled")
        self.estado.set("Analizando archivo…")
        self.actualizar_contadores()

        self.proceso = iter(analizar_archivo(self.ruta))
        demora = PAUSA_MS if self.animar_var.get() else 1
        self.ventana.after(demora, self.procesar_siguiente)

    def procesar_siguiente(self):
        try:
            resultado = next(self.proceso)
        except StopIteration:
            self.finalizar_analisis()
            return
        except (OSError, UnicodeError) as error:
            messagebox.showerror("Error de lectura", str(error))
            self.estado.set("No se pudo leer el archivo.")
            self.restablecer_controles()
            return
        except Exception as error:
            messagebox.showerror("Error inesperado", str(error))
            self.estado.set("El análisis se interrumpió.")
            self.restablecer_controles()
            return

        try:
            self.lineas += 1
            self._resultados_linea[resultado.numero] = resultado

            # Detectar y comunicar errores (invoca mostrar_error por cada uno)
            self.manejador.procesar(resultado)

            # Todo token reconocido entra a la tabla, aunque la línea tenga errores
            self.tabla.registrar(resultado)
            for tok in resultado.tokens:
                self._conteo_tokens[tok.tipo] = self._conteo_tokens.get(tok.tipo, 0) + 1
            if resultado.valida:
                self.validas += 1
                if self._filtro_consola in ("todos", "validas"):
                    self._escribir_linea_valida(resultado)
                self.editor_codigo.tag_add(
                    "linea_valida", f"{resultado.numero}.0", f"{resultado.numero}.end+1c"
                )
            else:
                self.editor_codigo.tag_add(
                    "linea_error", f"{resultado.numero}.0", f"{resultado.numero}.end+1c"
                )
                for err in resultado.errores:
                    c_ini = max(0, err.columna - 1)
                    c_fin = c_ini + max(1, len(err.lexema))
                    self.editor_codigo.tag_add(
                        "lexema_error",
                        f"{resultado.numero}.{c_ini}",
                        f"{resultado.numero}.{c_fin}",
                    )

            for tok in resultado.tokens:
                fila_t = len(self._todos_tokens)
                self._todos_tokens.append((resultado, tok))
                tags_t = ("par",) if fila_t % 2 else ()
                self.tree_tokens.insert(
                    "",
                    "end",
                    tags=tags_t,
                    values=(
                        tok.linea,
                        tok.columna,
                        tok.tipo,
                        tok.lexema,
                        "válida" if resultado.valida else "con error",
                        self.tabla.indice(tok.lexema),
                    ),
                )

            self._botones_tab["tokens"].configure(
                text=f"Tokens ({len(self._todos_tokens)})"
            )
            self._actualizar_gutter_codigo()
            self.actualizar_contadores()
            self.estado.set(f"Procesando línea {resultado.numero}…")
            self.resultados.see(tk.END)

            demora = PAUSA_MS if self.animar_var.get() else 1
            self.ventana.after(demora, self.procesar_siguiente)

        except Exception as error:
            messagebox.showerror("Error de procesamiento", str(error))
            self.estado.set("El análisis se interrumpió.")
            self.restablecer_controles()

    def _escribir_linea_valida(self, resultado):
        self.escribir(self.resultados, f"✓ Línea {resultado.numero:<4}", "valido")
        self.escribir(
            self.resultados,
            f"{len(resultado.tokens):>2} tokens   │ {resultado.texto.strip()}\n",
            "valido_detalle",
        )

    def _escribir_bloque_error(self, registro):
        lineas = self.manejador.formatear(registro).split("\n")
        for i, linea in enumerate(lineas):
            if i == 0:
                self.escribir(self.resultados, linea + "\n", "error_titulo", "bloque_error")
            elif linea.lstrip().startswith("Sugerencia:"):
                self.escribir(self.resultados, linea + "\n", "sugerencia", "bloque_error")
            elif "^" in linea and linea.strip().replace("|", "").strip().strip("^") == "":
                # Separar la barra "|" en color tenue y los indicadores "^^^" en color rojo
                pos_pipe = linea.find("|")
                if pos_pipe != -1:
                    self.escribir(
                        self.resultados, linea[: pos_pipe + 1], "tenue", "bloque_error"
                    )
                    self.escribir(
                        self.resultados, linea[pos_pipe + 1 :] + "\n", "indicador"
                    )
                else:
                    self.escribir(self.resultados, linea + "\n", "indicador", "bloque_error")
            else:
                self.escribir(self.resultados, linea + "\n", "error", "bloque_error")
        self.escribir(self.resultados, "\n")

    # PARTE 5: mostrar cada error en el momento en que se detecta
    def mostrar_error(self, registro):
        if self._filtro_consola in ("todos", "errores"):
            self._escribir_bloque_error(registro)
            self.resultados.see(tk.END)

        e = registro.error
        fila_e = self.manejador.total - 1
        tags_e = [e.categoria] + (["par"] if fila_e % 2 else [])
        self.tree_errores.insert(
            "",
            "end",
            tags=tags_e,
            values=(
                e.linea,
                e.columna,
                e.codigo,
                e.categoria,
                e.lexema or "—",
                f"{e.descripcion} — se esperaba {e.esperado}",
            ),
        )
        self._botones_tab["errores"].configure(
            text=f"Tabla de errores ({self.manejador.total})"
        )
        self.actualizar_resumen()

    def _reconstruir_consola(self):
        self.limpiar(self.resultados)
        for num in sorted(self._resultados_linea):
            res = self._resultados_linea[num]
            if res.valida and self._filtro_consola in ("todos", "validas"):
                self._escribir_linea_valida(res)
            elif not res.valida and self._filtro_consola in ("todos", "errores"):
                for reg in self.manejador.errores_de_linea(num):
                    self._escribir_bloque_error(reg)

        if not self.analizando and self._resultados_linea:
            self.escribir(self.resultados, "\nAnálisis finalizado\n", "titulo")
            self.escribir(
                self.resultados,
                f"{self.validas} línea(s) válida(s), "
                f"{len(self.manejador.lineas_con_error)} con errores, "
                f"{self.manejador.total} error(es) reportado(s).\n",
                "tenue",
            )

    def _reconstruir_vistas_tras_tema(self):
        self._reconstruir_consola()
        self.actualizar_resumen()
        self.actualizar_contadores()
        for fila_e, reg in enumerate(self.manejador.registros):
            e = reg.error
            tags_e = [e.categoria] + (["par"] if fila_e % 2 else [])
            self.tree_errores.insert(
                "",
                "end",
                tags=tags_e,
                values=(
                    e.linea,
                    e.columna,
                    e.codigo,
                    e.categoria,
                    e.lexema or "—",
                    f"{e.descripcion} — se esperaba {e.esperado}",
                ),
            )
        self._llenar_tabla_tokens()
        self._botones_tab["errores"].configure(
            text=f"Tabla de errores ({self.manejador.total})"
        )
        self._botones_tab["tokens"].configure(
            text=f"Tokens ({len(self._todos_tokens)})"
        )

    def finalizar_analisis(self):
        self.actualizar_resumen()
        self.actualizar_contadores()
        self.progreso.configure(value=self.progreso["maximum"])

        self.escribir(self.resultados, "\nAnálisis finalizado\n", "titulo")
        self.escribir(
            self.resultados,
            f"{self.validas} línea(s) válida(s), "
            f"{len(self.manejador.lineas_con_error)} con errores, "
            f"{self.manejador.total} error(es) reportado(s).\n",
            "tenue",
        )

        if self.manejador.hay_errores:
            self.estado.set(f"Análisis finalizado con {self.manejador.total} error(es).")
        else:
            self.estado.set("Análisis finalizado sin errores.")

        self.restablecer_controles()
        self.boton_tabla.config(state="normal")
        self.resultados.see("1.0")

    def restablecer_controles(self):
        self.analizando = False
        self.boton_archivo.config(state="normal")
        self.boton_ej_valido.config(state="normal")
        self.boton_ej_errores.config(state="normal")
        self.boton_analizar.config(state="normal" if self.ruta else "disabled")

    # PARTE 5: tabla de símbolos
    def mostrar_tabla(self):
        if self.ventana_tabla is not None and self.ventana_tabla.ventana.winfo_exists():
            if self.ventana_tabla.tabla is self.tabla:
                self.ventana_tabla.ventana.lift()
                self.ventana_tabla.ventana.focus_set()
                return
            # Se analizó otro archivo: la ventana abierta muestra la tabla anterior
            self.ventana_tabla.ventana.destroy()
        self.ventana_tabla = VentanaTabla(
            self.ventana,
            self.tabla,
            Path(self.ruta).name if self.ruta else "entrada",
            self,
        )


class VentanaTabla:
    COLUMNAS = (
        ("hash", "Índice", 80, "e"),
        ("lexema", "Lexema", 240, "w"),
        ("tipo", "Token", 160, "w"),
        ("categoria", "Categoría", 150, "w"),
        ("linea", "Línea", 90, "center"),
        ("veces", "Apariciones", 100, "e"),
    )

    LEYENDA = (
        "Índice: posición en la tabla hash, hash(lexema) % capacidad; si dos lexemas "
        "tienen el mismo índice (colisión) aparecen en filas seguidas con ese índice\n"
        "Lexema: texto tal como aparece en el archivo   ·   Token: tipo reconocido por el AFD   ·   "
        "Categoría: clase del token   ·   Línea: primera aparición   ·   "
        "Apariciones: cuántas veces aparece"
    )

    def __init__(self, padre, tabla, archivo, ui):
        self.tabla = tabla
        self.ui = ui
        c = ui.paleta

        v = self.ventana = tk.Toplevel(padre)
        v.title("Tabla de símbolos - AULA")
        v.geometry("1160x640")
        v.minsize(780, 440)
        v.configure(bg=c["fondo"])
        v.columnconfigure(0, weight=1)
        v.rowconfigure(2, weight=1)

        self._orden_col = None
        self._orden_desc = False

        e = tabla.estadisticas()
        encabezado = tk.Frame(
            v,
            bg=c["superficie"],
            highlightthickness=1,
            highlightbackground=c["borde"],
        )
        encabezado.grid(row=0, column=0, sticky="ew")
        tk.Label(
            encabezado,
            text="Tabla de símbolos del lenguaje AULA",
            font=ui.f_titulo,
            bg=c["superficie"],
            fg=c["texto"],
        ).pack(anchor="w", padx=20, pady=(14, 0))
        tk.Label(
            encabezado,
            text=f"{archivo}   ·   {len(tabla.simbolos_usados())} símbolos usados ({e['simbolos']} instalados)   ·   "
            f"capacidad {e['capacidad']}   ·   "
            f"factor de carga {e['factor_carga']}   ·   colisiones {e['colisiones']}   ·   "
            f"redimensiones {e['redimensiones']}",
            font=ui.f_subtitulo,
            bg=c["superficie"],
            fg=c["tenue"],
        ).pack(anchor="w", padx=20, pady=(2, 4))
        tk.Label(
            encabezado,
            text=self.LEYENDA,
            font=ui.f_subtitulo,
            bg=c["superficie"],
            fg=c["tenue"],
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        # Barra de herramientas: sub-vistas + buscador + filtros
        barra = ttk.Frame(v, padding=(20, 12, 20, 8))
        barra.grid(row=1, column=0, sticky="ew")

        self._botones_vista = {}
        self._marcos_vista = {}
        for k_v, tit_v in (
            ("tabla", "Vista tabular"),
            ("texto", "Texto formateado"),
        ):
            bv = ttk.Button(
                barra,
                text=tit_v,
                style="ChipActivo.TButton" if k_v == "tabla" else "Chip.TButton",
                command=lambda kv=k_v: self._cambiar_vista(kv),
            )
            bv.pack(side="left", padx=(0, 6))
            self._botones_vista[k_v] = bv

        self.no_usados = tk.BooleanVar(value=not bool(tabla.simbolos_usados()))
        tk.Checkbutton(
            barra,
            text="Incluir no usados",
            variable=self.no_usados,
            command=self.llenar,
            bg=c["fondo"],
            fg=c["tenue"],
            activebackground=c["fondo"],
            activeforeground=c["texto"],
            selectcolor=c["superficie"],
            bd=0,
            highlightthickness=0,
            font=ui.f_etiqueta,
            cursor="hand2",
        ).pack(side="right", padx=(10, 0))

        self.reservadas = tk.BooleanVar(value=True)
        tk.Checkbutton(
            barra,
            text="Incluir reservadas y días",
            variable=self.reservadas,
            command=self.llenar,
            bg=c["fondo"],
            fg=c["tenue"],
            activebackground=c["fondo"],
            activeforeground=c["texto"],
            selectcolor=c["superficie"],
            bd=0,
            highlightthickness=0,
            font=ui.f_etiqueta,
            cursor="hand2",
        ).pack(side="right", padx=(10, 0))

        self.busqueda = tk.StringVar()
        self.busqueda.trace_add("write", lambda *_: self.llenar())
        entrada = tk.Entry(
            barra,
            textvariable=self.busqueda,
            width=18,
            relief="flat",
            highlightthickness=1,
            highlightbackground=c["borde_fuerte"],
            highlightcolor=c["acento"],
            bg=c["editor"],
            fg=c["texto"],
            insertbackground=c["texto"],
            font=ui.f_mono_peq,
        )
        entrada.pack(side="right", padx=(6, 0), ipady=3, ipadx=5)
        tk.Label(
            barra, text="Buscar:", bg=c["fondo"], fg=c["tenue"], font=ui.f_etiqueta
        ).pack(side="right")

        # Contenedor de las 3 vistas
        contenedor = tk.Frame(
            v,
            bg=c["superficie"],
            highlightthickness=1,
            highlightbackground=c["borde"],
        )
        contenedor.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(0, weight=1)

        # 1. Vista Tabular (Treeview ordenable)
        m_tabla = tk.Frame(contenedor, bg=c["editor"])
        m_tabla.grid(row=0, column=0, sticky="nsew")
        m_tabla.columnconfigure(0, weight=1)
        m_tabla.rowconfigure(0, weight=1)
        self._marcos_vista["tabla"] = m_tabla

        self.arbol = ttk.Treeview(
            m_tabla,
            columns=[col[0] for col in self.COLUMNAS],
            show="headings",
            selectmode="browse",
        )
        for clave, titulo, ancho, lado in self.COLUMNAS:
            self.arbol.heading(
                clave,
                text=titulo,
                anchor=lado,
                command=lambda cl=clave: self.ordenar_por(cl),
            )
            self.arbol.column(
                clave,
                width=ancho,
                anchor=lado,
                stretch=(clave == "lexema"),
                minwidth=55,
            )
        self.arbol.tag_configure("par", background=c["fila_par"])
        self.arbol.tag_configure("reservada", foreground=c["tenue"])
        self.arbol.tag_configure("entidad", foreground=c["verde"])
        self.arbol.tag_configure("variable", foreground=c["acento_claro"])
        self.arbol.grid(row=0, column=0, sticky="nsew")

        sv = ttk.Scrollbar(m_tabla, orient="vertical", command=self.arbol.yview)
        sv.grid(row=0, column=1, sticky="ns")
        sh = ttk.Scrollbar(m_tabla, orient="horizontal", command=self.arbol.xview)
        sh.grid(row=1, column=0, sticky="ew")
        self.arbol.configure(yscrollcommand=sv.set, xscrollcommand=sh.set)
        self.arbol.bind("<<TreeviewSelect>>", self._al_seleccionar_fila)

        # 2. Vista de Texto Formateado (formatear)
        m_texto = tk.Frame(contenedor, bg=c["editor"])
        m_texto.grid(row=0, column=0, sticky="nsew")
        m_texto.columnconfigure(0, weight=1)
        m_texto.rowconfigure(0, weight=1)
        self._marcos_vista["texto"] = m_texto

        self.texto_formateado = tk.Text(
            m_texto,
            wrap="none",
            font=ui.f_mono,
            bg=c["editor"],
            fg=c["texto"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=14,
            pady=12,
        )
        self.texto_formateado.grid(row=0, column=0, sticky="nsew")
        sv_f = ttk.Scrollbar(m_texto, orient="vertical", command=self.texto_formateado.yview)
        sv_f.grid(row=0, column=1, sticky="ns")
        sh_f = ttk.Scrollbar(m_texto, orient="horizontal", command=self.texto_formateado.xview)
        sh_f.grid(row=1, column=0, sticky="ew")
        self.texto_formateado.configure(yscrollcommand=sv_f.set, xscrollcommand=sh_f.set)

        self.llenar()
        self._cambiar_vista("tabla")
        v.transient(padre)
        v.lift()
        entrada.focus_set()

    def _cambiar_vista(self, clave):
        for k, marco in self._marcos_vista.items():
            if k == clave:
                marco.tkraise()
                self._botones_vista[k].configure(style="ChipActivo.TButton")
            else:
                self._botones_vista[k].configure(style="Chip.TButton")

    def _al_seleccionar_fila(self, _evento=None):
        sel = self.arbol.selection()
        if not sel:
            return
        vals = self.arbol.item(sel[0], "values")
        if vals and str(vals[4]).isdigit() and int(vals[4]) > 0:
            self.ui.ir_a_linea(int(vals[4]), 1)

    def ordenar_por(self, columna):
        if self._orden_col == columna:
            self._orden_desc = not self._orden_desc
        else:
            self._orden_col = columna
            self._orden_desc = False
        self.llenar()

    def llenar(self):
        self.arbol.delete(*self.arbol.get_children())
        texto = self.busqueda.get().strip().lower()
        incluir_no_usados = self.no_usados.get()
        fuente = list(self.tabla) if incluir_no_usados else self.tabla.simbolos_usados()

        filas_datos = []
        for s in fuente:
            fijo = s.tipo in ("RESERVADA", "DIA")
            if fijo and not self.reservadas.get():
                continue
            if texto and (
                texto not in s.lexema.lower()
                and texto not in s.tipo.lower()
                and texto not in s.categoria.lower()
            ):
                continue
            filas_datos.append((s, fijo))

        # Orden por defecto: declaraciones/entidades primero si no se eligió columna
        prioridad = {
            "materia": 0,
            "profesor": 1,
            "aula": 2,
            "grupo": 3,
            "identificador": 5,
            "literal": 6,
            "día": 7,
            "operador": 8,
            "delimitador": 9,
            "palabra reservada": 10,
        }
        if self._orden_col is None:
            # Orden de la tabla hash: por índice y, dentro de un índice, por orden de encadenamiento
            orden = {id(sim): i for i, sim in enumerate(self.tabla)}
            filas_datos.sort(
                key=lambda item: (self.tabla.indice(item[0].lexema), orden[id(item[0])])
            )
        else:
            col = self._orden_col
            if col == "hash":
                clave_fn = lambda item: self.tabla.indice(item[0].lexema)
            elif col == "lexema":
                clave_fn = lambda item: item[0].lexema.lower()
            elif col == "tipo":
                clave_fn = lambda item: item[0].tipo
            elif col == "categoria":
                clave_fn = lambda item: item[0].categoria
            elif col == "linea":
                clave_fn = lambda item: item[0].linea or 0
            elif col == "veces":
                clave_fn = lambda item: item[0].veces
            else:
                clave_fn = lambda item: item[0].lexema
            filas_datos.sort(key=clave_fn, reverse=self._orden_desc)

        for fila, (s, fijo) in enumerate(filas_datos):
            tags = ["par"] if fila % 2 else []
            if fijo:
                tags.append("reservada")
            elif s.categoria in ("materia", "profesor", "aula", "grupo"):
                tags.append("entidad")
            elif s.categoria in ("variable", "identificador"):
                tags.append("variable")

            self.arbol.insert(
                "",
                "end",
                tags=tags,
                values=(
                    self.tabla.indice(s.lexema),
                    s.lexema,
                    s.tipo,
                    s.categoria,
                    s.linea if s.ocurrencias else "—",
                    s.veces,
                ),
            )

        # Actualizar la vista de texto formateado
        self.texto_formateado.configure(state="normal")
        self.texto_formateado.delete("1.0", tk.END)
        self.texto_formateado.insert(
            tk.END, self.tabla.formatear(incluir_no_usados=incluir_no_usados)
        )
        self.texto_formateado.configure(state="disabled")


if __name__ == "__main__":
    ventana = tk.Tk()
    app = InterfazAULA(ventana)
    ventana.mainloop()
