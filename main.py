## @mainpage Prover9-Mace4 GUI - Documentación Técnica
#
# @section intro_sec Introducción
# Bienvenido a la documentación técnica de la Interfaz Gráfica de Usuario para los motores lógicos Prover9 y Mace4. 
# Este software ha sido desarrollado como Trabajo de Fin de Grado para el Grado en Ingeniería Informática de la Universidad de Granada (UGR).
#
# @section arch_sec Arquitectura del Sistema
# La aplicación está construida utilizando Python y PyQt6, siguiendo un patrón modular y escalable:
# - <b>main.py</b>: Orquestación central, resaltado de sintaxis y gestión de eventos de la interfaz.
# - <b>launcher.py</b>: Capa de abstracción para la ejecución segura de subprocesos multiplataforma.
# - <b>idiomas.py</b>: Base de datos estática para la internacionalización y configuración estructural.
#
# @section author_sec Autor
# Desarrollado por Antonio Jose Parras Flores.

"""!
@file main.py
@brief Punto de entrada principal y definición de la interfaz gráfica de usuario (GUI).

Este archivo contiene la lógica principal de la aplicación, definiendo la ventana
principal, el resaltado de sintaxis, la gestión asíncrona de procesos lógicos 
y la orquestación entre la vista y los motores subyacentes.

@author Antonio Jose Parras Flores
@date Septiembre 2026
@version 1.0.0
"""
import sys
import os
import re

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QTabWidget, QFileDialog, QGroupBox, QCheckBox, QStackedWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView, QStatusBar,
                             QSpinBox, QFormLayout, QComboBox, QScrollArea, QMessageBox)
from PyQt6.QtGui import QFont, QAction, QSyntaxHighlighter, QTextCharFormat, QColor, QFontDatabase, QIcon
from PyQt6.QtCore import QEvent, QThread, pyqtSignal, QRegularExpression
from qt_material import apply_stylesheet

from launcher import ejecutar_prover9, ejecutar_mace4
from idiomas import TRADUCCIONES, DICCIONARIO_PANELES, SCHEMA_PROVER9


def ruta_recurso(ruta_relativa):
    """!
    @brief Obtiene la ruta absoluta segura para PyInstaller.
    
    @param ruta_relativa Cadena con el nombre del recurso a buscar.
    @return Ruta absoluta generada dinámicamente por el sistema operativo.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, ruta_relativa)


class HiloMotor(QThread):
    """!
    @brief Hilo secundario para ejecutar los motores lógicos de forma asíncrona.
    
    Evita que la interfaz gráfica (GUI) se congele mientras Prover9 o Mace4
    realizan cálculos pesados o agotan su tiempo límite.
    """
    resultado_listo = pyqtSignal(str, str, dict)

    def __init__(self, motor, texto_final, tiempo_limite, snapshot):
        """!
        @brief Constructor del hilo de ejecución.
        
        @param motor Nombre del motor a utilizar ('prover9' o 'mace4').
        @param texto_final Cadena de texto con el código a procesar.
        @param tiempo_limite Límite de tiempo en segundos para la ejecución.
        @param snapshot Diccionario con el estado de la interfaz gráfica para el historial.
        """
        super().__init__()
        self.motor = motor
        self.texto_final = texto_final
        self.tiempo_limite = tiempo_limite
        self.snapshot = snapshot

    def run(self):
        """!
        @brief Método principal que se ejecuta en el subproceso.
        """
        if self.motor == 'prover9':
            resultado_crudo, hora = ejecutar_prover9(self.texto_final, tiempo_limite=self.tiempo_limite)
        else:
            resultado_crudo, hora = ejecutar_mace4(self.texto_final, tiempo_limite=self.tiempo_limite)
        self.resultado_listo.emit(resultado_crudo, hora, self.snapshot)


class ResaltadorProver9(QSyntaxHighlighter):
    """!
    @brief Gestor de resaltado de sintaxis en tiempo real.
    
    Aplica colores específicos a operadores lógicos, palabras clave,
    bloques estructurales y comentarios en los editores de texto.
    """
    def __init__(self, editor):
        """!
        @brief Inicializa el resaltador y define las expresiones regulares.
        
        @param editor Referencia al QTextEdit donde se aplicará el resaltado.
        """
        super().__init__(editor.document())
        self.editor = editor
        self.reglas = []

        formato_operador = QTextCharFormat()
        formato_operador.setForeground(QColor("#C586C0"))
        formato_operador.setFontWeight(QFont.Weight.Bold)
        operadores = [r"->", r"<->", r"&", r"\|", r"-", r"=", r"!="]
        for op in operadores:
            self.reglas.append((QRegularExpression(op), formato_operador))

        formato_clave = QTextCharFormat()
        formato_clave.setForeground(QColor("#569CD6"))
        formato_clave.setFontWeight(QFont.Weight.Bold)
        claves = [r"\bformulas\b", r"\bend_of_list\b", r"\bassign\b", r"\bset\b", r"\bclear\b", r"\blist\b"]
        for clave in claves:
            self.reglas.append((QRegularExpression(clave), formato_clave))

        formato_bloque = QTextCharFormat()
        formato_bloque.setForeground(QColor("#CE9178"))
        bloques = [r"\bsos\b", r"\bgoals\b", r"\busable\b", r"\bdemodulators\b", r"\bassumptions\b"]
        for bloque in bloques:
            self.reglas.append((QRegularExpression(bloque), formato_bloque))

        formato_comentario = QTextCharFormat()
        formato_comentario.setForeground(QColor("#6A9955"))
        self.reglas.append((QRegularExpression(r"%.*"), formato_comentario))

    def highlightBlock(self, text):
        """!
        @brief Aplica los formatos definidos a un bloque de texto.
        
        @param text Texto actual sobre el que se evalúan las expresiones regulares.
        """
        texto_completo = self.editor.toPlainText().strip()
        if texto_completo.startswith("Ejemplo:") or texto_completo.startswith("Example:"):
            return
            
        for expresion, formato in self.reglas:
            iterador = expresion.globalMatch(text)
            while iterador.hasNext():
                match = iterador.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), formato)


class VentanaPrincipal(QMainWindow):
    """!
    @brief Clase central de la aplicación de escritorio.
    
    Gestiona la construcción visual, el ciclo de vida de los eventos,
    el estado interno, la internacionalización y la conexión de señales y slots.
    """
    def __init__(self):
        """!
        @brief Constructor de la ventana principal.
        """
        super().__init__()
        self.idioma_actual = 'es_ES'
        self.ruta_archivo_actual = None
        self.datos_historial = []
        self.labels_subcategorias = []
        self.botones_reset_cats = []
        self.nombres_categorias = []
        self.combos_traducibles = []
        self.init_ui()

    def init_ui(self):
        """!
        @brief Construye la jerarquía visual de componentes (Layouts y Widgets).
        """
        self.setGeometry(100, 100, 1100, 900)
        self.setWindowIcon(QIcon(ruta_recurso("icono_app.ico")))
        
        widget_central = QWidget()
        layout_central_ventana = QVBoxLayout(widget_central)
        
        self.tabs = QTabWidget()
        self.tab_prover9 = QWidget()
        self.tab_mace4 = QWidget()
        self.tabs.addTab(self.tab_prover9, "")
        self.tabs.addTab(self.tab_mace4, "")
        self.tabs.currentChanged.connect(self.actualizar_textos_interfaz)
        
        self.configurar_tab_prover9()
        self.configurar_tab_mace4()
        layout_central_ventana.addWidget(self.tabs, stretch=3)
        
        self.grupo_historial = QGroupBox("")
        layout_historial = QVBoxLayout(self.grupo_historial)
        self.tabla_historial = QTableWidget(0, 3)
        self.tabla_historial.setFont(QFont("Segoe UI", 9))
        self.tabla_historial.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_historial.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_historial.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_historial.itemDoubleClicked.connect(self.recuperar_desde_historial)
        layout_historial.addWidget(self.tabla_historial)
        layout_central_ventana.addWidget(self.grupo_historial, stretch=1)
        
        self.setCentralWidget(widget_central)
        
        self.barra_estado = QStatusBar()
        self.setStatusBar(self.barra_estado)
        
        self.premisas_p9.installEventFilter(self)
        self.conclusion_p9.installEventFilter(self)
        self.entrada_libre_p9.installEventFilter(self)
        self.premisas_m4.installEventFilter(self)
        self.conclusion_m4.installEventFilter(self)
        self.entrada_libre_m4.installEventFilter(self)
        
        self.crear_barra_menus()
        self.actualizar_textos_interfaz()
        self.snapshot_guardado = self.obtener_estado_actual()

    def crear_barra_menus(self):
        """!
        @brief Crea y configura la barra de herramientas superior (File, Examples, Language).
        """
        self.menuBar().clear()
        barra_menus = self.menuBar()
        
        self.menu_archivo = barra_menus.addMenu("")
        self.accion_nuevo = QAction("", self)
        self.accion_nuevo.triggered.connect(self.nuevo_proyecto)
        self.accion_abrir = QAction("", self)
        self.accion_abrir.setShortcut("Ctrl+O")
        self.accion_abrir.triggered.connect(self.abrir_archivo)
        self.accion_guardar = QAction("", self)
        self.accion_guardar.setShortcut("Ctrl+S")
        self.accion_guardar.triggered.connect(self.guardar_archivo)
        self.accion_exportar = QAction("", self)
        self.accion_exportar.triggered.connect(self.exportar_salida)
        self.accion_salir = QAction("", self)
        self.accion_salir.triggered.connect(self.close)
        
        self.menu_archivo.addAction(self.accion_nuevo)
        self.menu_archivo.addSeparator()
        self.menu_archivo.addAction(self.accion_abrir)
        self.menu_archivo.addAction(self.accion_guardar)
        self.menu_archivo.addSeparator()
        self.menu_archivo.addAction(self.accion_exportar)
        self.menu_archivo.addSeparator()
        self.menu_archivo.addAction(self.accion_salir)
        
        self.menu_ejemplos = barra_menus.addMenu("")
        self.accion_ej1 = QAction("", self)
        self.accion_ej1.triggered.connect(lambda: self.cargar_ejemplo_tipo(1))
        self.accion_ej2 = QAction("", self)
        self.accion_ej2.triggered.connect(lambda: self.cargar_ejemplo_tipo(2))
        self.accion_ej3 = QAction("", self)
        self.accion_ej3.triggered.connect(lambda: self.cargar_ejemplo_tipo(3))
        self.menu_ejemplos.addAction(self.accion_ej1)
        self.menu_ejemplos.addAction(self.accion_ej2)
        self.menu_ejemplos.addAction(self.accion_ej3)
        
        self.menu_idioma = barra_menus.addMenu("")
        accion_es = QAction("Español (es-ES)", self)
        accion_es.triggered.connect(lambda: self.cambiar_idioma('es_ES'))
        accion_en = QAction("English (en-US)", self)
        accion_en.triggered.connect(lambda: self.cambiar_idioma('en_US'))
        self.menu_idioma.addAction(accion_es)
        self.menu_idioma.addAction(accion_en)

    def configurar_tab_prover9(self):
        """!
        @brief Orquesta los componentes visuales internos de la pestaña Prover9.
        """
        estilo_codigo = "font-family: 'JetBrains Mono'; font-size: 12pt;"
        layout_principal = QHBoxLayout()
        columna_derecha = QVBoxLayout()
        self.chk_modo_p9 = QCheckBox("")
        self.chk_modo_p9.toggled.connect(self.alternar_modo_p9)
        columna_derecha.addWidget(self.chk_modo_p9)
        self.vista_stack_p9 = QStackedWidget()
        
        vista_limpia = QWidget()
        layout_limpio = QVBoxLayout(vista_limpia)
        layout_limpio.setContentsMargins(0, 0, 0, 0)
        self.lbl_premisas_p9 = QLabel("")
        layout_limpio.addWidget(self.lbl_premisas_p9)
        self.premisas_p9 = QTextEdit()
        self.premisas_p9.setStyleSheet(estilo_codigo)
        self.resaltador_premisas_p9 = ResaltadorProver9(self.premisas_p9)
        layout_limpio.addWidget(self.premisas_p9)
        self.lbl_conclusion_p9 = QLabel("")
        layout_limpio.addWidget(self.lbl_conclusion_p9)
        self.conclusion_p9 = QTextEdit()
        self.conclusion_p9.setStyleSheet(estilo_codigo)
        self.conclusion_p9.setMaximumHeight(100)
        self.resaltador_conclusion_p9 = ResaltadorProver9(self.conclusion_p9)
        layout_limpio.addWidget(self.conclusion_p9)
        
        vista_libre = QWidget()
        layout_libre = QVBoxLayout(vista_libre)
        layout_libre.setContentsMargins(0, 0, 0, 0)
        self.lbl_libre_p9 = QLabel("")
        layout_libre.addWidget(self.lbl_libre_p9)
        self.entrada_libre_p9 = QTextEdit()
        self.entrada_libre_p9.setStyleSheet(estilo_codigo)
        self.resaltador_libre_p9 = ResaltadorProver9(self.entrada_libre_p9)
        layout_libre.addWidget(self.entrada_libre_p9)
        
        self.vista_stack_p9.addWidget(vista_limpia)
        self.vista_stack_p9.addWidget(vista_libre)
        columna_derecha.addWidget(self.vista_stack_p9)
        
        self.btn_p9 = QPushButton("")
        self.btn_p9.setStyleSheet("font-weight: bold; background-color: #2962ff; color: white; padding: 10px;")
        self.btn_p9.clicked.connect(self.procesar_prover9)
        columna_derecha.addWidget(self.btn_p9)
        self.lbl_res_p9 = QLabel("")
        columna_derecha.addWidget(self.lbl_res_p9)
        self.salida_p9 = QTextEdit()
        self.salida_p9.setReadOnly(True)
        columna_derecha.addWidget(self.salida_p9)
        
        self.grupo_ins_p9, self.lbl_ops_p9, self.botones_ops_p9 = self.crear_panel_insercion(self.entrada_libre_p9)
        layout_principal.addWidget(self.grupo_ins_p9)
        layout_principal.addLayout(columna_derecha)
        
        self.grupo_opciones_p9 = self.crear_panel_opciones_p9()
        layout_principal.addWidget(self.grupo_opciones_p9)
        self.tab_prover9.setLayout(layout_principal)

    def configurar_tab_mace4(self):
        """!
        @brief Orquesta los componentes visuales internos de la pestaña Mace4.
        """
        estilo_codigo = "font-family: 'JetBrains Mono'; font-size: 12pt;"
        layout_principal = QHBoxLayout()
        columna_derecha = QVBoxLayout()
        self.chk_modo_m4 = QCheckBox("")
        self.chk_modo_m4.toggled.connect(self.alternar_modo_m4)
        columna_derecha.addWidget(self.chk_modo_m4)
        self.vista_stack_m4 = QStackedWidget()
        
        vista_limpia = QWidget()
        layout_limpio = QVBoxLayout(vista_limpia)
        layout_limpio.setContentsMargins(0, 0, 0, 0)
        self.lbl_premisas_m4 = QLabel("")
        layout_limpio.addWidget(self.lbl_premisas_m4)
        self.premisas_m4 = QTextEdit()
        self.premisas_m4.setStyleSheet(estilo_codigo)
        self.resaltador_premisas_m4 = ResaltadorProver9(self.premisas_m4)
        layout_limpio.addWidget(self.premisas_m4)
        self.lbl_objetivo_m4 = QLabel("")
        layout_limpio.addWidget(self.lbl_objetivo_m4)
        self.conclusion_m4 = QTextEdit()
        self.conclusion_m4.setStyleSheet(estilo_codigo)
        self.conclusion_m4.setMaximumHeight(100)
        self.resaltador_conclusion_m4 = ResaltadorProver9(self.conclusion_m4)
        layout_limpio.addWidget(self.conclusion_m4)
        
        vista_libre = QWidget()
        layout_libre = QVBoxLayout(vista_libre)
        layout_libre.setContentsMargins(0, 0, 0, 0)
        self.lbl_libre_m4 = QLabel("")
        layout_libre.addWidget(self.lbl_libre_m4)
        self.entrada_libre_m4 = QTextEdit()
        self.entrada_libre_m4.setStyleSheet(estilo_codigo)
        self.resaltador_libre_m4 = ResaltadorProver9(self.entrada_libre_m4)
        layout_libre.addWidget(self.entrada_libre_m4)
        
        self.vista_stack_m4.addWidget(vista_limpia)
        self.vista_stack_m4.addWidget(vista_libre)
        columna_derecha.addWidget(self.vista_stack_m4)
        
        self.btn_m4 = QPushButton("")
        self.btn_m4.setStyleSheet("font-weight: bold; background-color: #d32f2f; color: white; padding: 10px;")
        self.btn_m4.clicked.connect(self.procesar_mace4)
        columna_derecha.addWidget(self.btn_m4)
        self.lbl_res_m4 = QLabel("")
        columna_derecha.addWidget(self.lbl_res_m4)
        self.salida_m4 = QTextEdit()
        self.salida_m4.setReadOnly(True)
        columna_derecha.addWidget(self.salida_m4)
        
        self.grupo_ins_m4, self.lbl_ops_m4, self.botones_ops_m4 = self.crear_panel_insercion(self.entrada_libre_m4)
        layout_principal.addWidget(self.grupo_ins_m4)
        layout_principal.addLayout(columna_derecha)
        
        self.grupo_opciones_m4 = self.crear_panel_opciones_m4()
        layout_principal.addWidget(self.grupo_opciones_m4)
        self.tab_mace4.setLayout(layout_principal)

    def crear_panel_insercion(self):
        """!
        @brief Crea la botonera lateral izquierda para inyectar operadores lógicos.
        
        @return Tupla (QGroupBox, QLabel, Lista de tuplas de botones).
        """
        grupo = QGroupBox("")
        layout_grupo = QVBoxLayout()
        lbl_ops = QLabel("")
        layout_grupo.addWidget(lbl_ops)
        botones_ops = []
        operadores_config = [
            ('op_neg', " - "), ('op_conj', " & "), ('op_disj', " | "), 
            ('op_impl', " -> "), ('op_equiv', " <-> ")
        ]
        for clave, simbolo in operadores_config:
            btn = QPushButton("") 
            btn.clicked.connect(lambda checked, s=simbolo, c_clave=clave: self.inyectar_operador_inteligente(s, c_clave))
            layout_grupo.addWidget(btn)
            botones_ops.append((btn, clave))
        layout_grupo.addStretch()
        grupo.setLayout(layout_grupo)
        grupo.setFixedWidth(230) 
        return grupo, lbl_ops, botones_ops

    def crear_panel_opciones_p9(self):
        """!
        @brief Genera y devuelve el panel de opciones avanzadas (derecho) para Prover9.
        
        @return Objeto QScrollArea que contiene todos los controles de configuración.
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(385)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        contenido = QWidget()
        contenido.setObjectName("fondo_blanco_p9")
        layout_principal = QVBoxLayout(contenido)
        layout_principal.setContentsMargins(5, 0, 5, 0)

        self.all_flags_p9 = {}
        self.all_assigns_p9 = {}

        self.grupo_basico_p9 = QGroupBox("Basic Options")
        form_basico = QFormLayout()

        self.spin_max_weight = QSpinBox(); self.spin_max_weight.setRange(-1000, 100000); self.spin_max_weight.setValue(100)
        form_basico.addRow("max_weight:", self.spin_max_weight)
        self.spin_pick_ratio = QSpinBox(); self.spin_pick_ratio.setRange(-1, 100); self.spin_pick_ratio.setValue(-1)
        form_basico.addRow("pick_given_ratio:", self.spin_pick_ratio)
        
        self.combo_order = QComboBox()
        for opc in ["lpo", "rpo", "kbo"]: self.combo_order.addItem(opc, opc)
        form_basico.addRow("order:", self.combo_order)
        self.combos_traducibles.append(self.combo_order)
        
        self.combo_eq_defs = QComboBox()
        for opc in ["unfold", "fold", "pass"]: self.combo_eq_defs.addItem(opc, opc)
        form_basico.addRow("eq_defs:", self.combo_eq_defs)
        self.combos_traducibles.append(self.combo_eq_defs)
        
        self.chk_expand_relational = QCheckBox()
        form_basico.addRow("expand_relational_defs:", self.chk_expand_relational)
        self.chk_restrict_denials = QCheckBox()
        form_basico.addRow("restrict_denials:", self.chk_restrict_denials)
        self.spin_max_seconds_p9 = QSpinBox(); self.spin_max_seconds_p9.setRange(1, 3600); self.spin_max_seconds_p9.setValue(60)
        form_basico.addRow("max_seconds:", self.spin_max_seconds_p9)
        self.chk_prolog_vars = QCheckBox()
        form_basico.addRow("prolog_style_variables:", self.chk_prolog_vars)

        self.btn_reset_basico_p9 = QPushButton("Reset These to Defaults")
        self.btn_reset_basico_p9.clicked.connect(self.reset_opciones_p9)
        form_basico.addRow(self.btn_reset_basico_p9)
        self.grupo_basico_p9.setLayout(form_basico)
        layout_principal.addWidget(self.grupo_basico_p9)

        self.grupo_all_options = QGroupBox("All Options")
        self.grupo_all_options.setCheckable(True)
        self.grupo_all_options.setChecked(False)
        
        layout_all = QVBoxLayout()
        self.combo_grupos_p9 = QComboBox()
        layout_all.addWidget(self.combo_grupos_p9)
        self.stack_opciones_p9 = QStackedWidget()

        for nombre_grupo, elementos in SCHEMA_PROVER9:
            self.combo_grupos_p9.addItem(nombre_grupo, nombre_grupo)
            self.nombres_categorias.append(nombre_grupo)
            page = QWidget()
            form = QFormLayout(page)
            form.setContentsMargins(0, 5, 0, 0)

            for elemento in elementos:
                tipo = elemento[0]
                if tipo == 'sub':
                    lbl = QLabel(elemento[1])
                    lbl.setStyleSheet("font-style: 'Nexa'; color: #81c784; font-weight: bold; padding-top: 8px;")
                    form.addRow(lbl)
                    self.labels_subcategorias.append((lbl, elemento[1]))
                elif tipo == 'flag':
                    _, nombre, por_defecto = elemento
                    chk = QCheckBox()
                    chk.setChecked(por_defecto)
                    form.addRow(f"{nombre}:", chk)
                    self.all_flags_p9[nombre] = (chk, por_defecto, nombre_grupo)
                elif tipo == 'spin':
                    _, nombre, val_min, val_max, por_defecto = elemento
                    spin = QSpinBox()
                    spin.setRange(val_min, val_max)
                    spin.setValue(por_defecto)
                    form.addRow(f"{nombre}:", spin)
                    self.all_assigns_p9[nombre] = (spin, por_defecto, nombre_grupo)
                elif tipo == 'combo':
                    _, nombre, opciones, por_defecto = elemento
                    combo = QComboBox()
                    for opc in opciones: combo.addItem(opc, opc)
                    combo.setCurrentText(por_defecto)
                    form.addRow(f"{nombre}:", combo)
                    self.all_assigns_p9[nombre] = (combo, por_defecto, nombre_grupo)
                    self.combos_traducibles.append(combo)

            btn_reset = QPushButton("Reset These to Defaults")
            btn_reset.clicked.connect(lambda checked, cat=nombre_grupo: self.reset_categoria_p9(cat))
            form.addRow(btn_reset)
            self.botones_reset_cats.append(btn_reset)
            self.stack_opciones_p9.addWidget(page)

        self.combo_grupos_p9.currentIndexChanged.connect(self.stack_opciones_p9.setCurrentIndex)
        layout_all.addWidget(self.stack_opciones_p9)
        self.grupo_all_options.setLayout(layout_all)

        layout_principal.addWidget(self.grupo_all_options)
        layout_principal.addStretch()
        scroll.setWidget(contenido)
        return scroll

    def crear_panel_opciones_m4(self):
        """!
        @brief Genera y devuelve el panel de opciones avanzadas (derecho) para Mace4.
        
        @return Objeto QScrollArea que contiene todos los controles de configuración.
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(385)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        contenido = QWidget()
        contenido.setObjectName("fondo_blanco_m4")
        layout_principal = QVBoxLayout(contenido)
        layout_principal.setContentsMargins(5, 0, 5, 0)

        self.grupo_basico_m4 = QGroupBox("Basic Options")
        form_basico = QFormLayout()

        self.spin_domain_size = QSpinBox(); self.spin_domain_size.setRange(0, 1000); self.spin_domain_size.setValue(0)
        form_basico.addRow("domain_size:", self.spin_domain_size)
        self.spin_start_size = QSpinBox(); self.spin_start_size.setRange(2, 1000); self.spin_start_size.setValue(2)
        form_basico.addRow("start_size:", self.spin_start_size)
        self.spin_end_size = QSpinBox(); self.spin_end_size.setRange(-1, 1000); self.spin_end_size.setValue(-1)
        form_basico.addRow("end_size:", self.spin_end_size)
        self.spin_increment = QSpinBox(); self.spin_increment.setRange(1, 100); self.spin_increment.setValue(1)
        form_basico.addRow("increment:", self.spin_increment)

        self.combo_iterate = QComboBox()
        for opc in ["all", "evens", "odds", "primes", "nonprimes"]: self.combo_iterate.addItem(opc, opc)
        self.combo_iterate.setCurrentText("all")
        form_basico.addRow("iterate:", self.combo_iterate)
        self.combos_traducibles.append(self.combo_iterate)

        self.spin_max_models = QSpinBox(); self.spin_max_models.setRange(-1, 10000); self.spin_max_models.setValue(1)
        form_basico.addRow("max_models:", self.spin_max_models)
        self.spin_max_seconds_m4 = QSpinBox(); self.spin_max_seconds_m4.setRange(-1, 3600); self.spin_max_seconds_m4.setValue(60)
        form_basico.addRow("max_seconds:", self.spin_max_seconds_m4)
        self.spin_max_seconds_per = QSpinBox(); self.spin_max_seconds_per.setRange(-1, 3600); self.spin_max_seconds_per.setValue(-1)
        form_basico.addRow("max_seconds_per:", self.spin_max_seconds_per)
        self.chk_prolog_vars_m4 = QCheckBox()
        form_basico.addRow("prolog_style_variables:", self.chk_prolog_vars_m4)

        self.grupo_basico_m4.setLayout(form_basico)
        layout_principal.addWidget(self.grupo_basico_m4)

        self.grupo_otros_m4 = QGroupBox("Other Options")
        form_otros = QFormLayout()
        self.chk_integer_ring = QCheckBox()
        form_otros.addRow("integer_ring:", self.chk_integer_ring)
        self.chk_skolems_last = QCheckBox()
        form_otros.addRow("skolems_last:", self.chk_skolems_last)
        self.spin_max_megs = QSpinBox(); self.spin_max_megs.setRange(1, 10000); self.spin_max_megs.setValue(200)
        form_otros.addRow("max_megs:", self.spin_max_megs)
        self.chk_print_models = QCheckBox(); self.chk_print_models.setChecked(True)
        form_otros.addRow("print_models:", self.chk_print_models)
        self.grupo_otros_m4.setLayout(form_otros)
        layout_principal.addWidget(self.grupo_otros_m4)

        self.grupo_exp_m4 = QGroupBox("Experimental Options")
        form_exp = QFormLayout()
        self.chk_lnh = QCheckBox(); self.chk_lnh.setChecked(True)
        form_exp.addRow("lnh:", self.chk_lnh)
        self.chk_negprop = QCheckBox(); self.chk_negprop.setChecked(True)
        form_exp.addRow("negprop:", self.chk_negprop)
        self.chk_neg_assign = QCheckBox(); self.chk_neg_assign.setChecked(True)
        form_exp.addRow("neg_assign:", self.chk_neg_assign)
        self.chk_neg_assign_near = QCheckBox(); self.chk_neg_assign_near.setChecked(True)
        form_exp.addRow("neg_assign_near:", self.chk_neg_assign_near)
        self.chk_neg_elim = QCheckBox(); self.chk_neg_elim.setChecked(True)
        form_exp.addRow("neg_elim:", self.chk_neg_elim)
        self.chk_neg_elim_near = QCheckBox(); self.chk_neg_elim_near.setChecked(True)
        form_exp.addRow("neg_elim_near:", self.chk_neg_elim_near)
        self.spin_selection_order = QSpinBox(); self.spin_selection_order.setRange(-1, 100); self.spin_selection_order.setValue(2)
        form_exp.addRow("selection_order:", self.spin_selection_order)
        self.spin_selection_measure = QSpinBox(); self.spin_selection_measure.setRange(-1, 100); self.spin_selection_measure.setValue(4)
        form_exp.addRow("selection_measure:", self.spin_selection_measure)
        self.grupo_exp_m4.setLayout(form_exp)
        layout_principal.addWidget(self.grupo_exp_m4)

        self.btn_reset_m4 = QPushButton("Reset These to Defaults")
        self.btn_reset_m4.clicked.connect(self.reset_opciones_m4)
        layout_principal.addWidget(self.btn_reset_m4)

        scroll.setWidget(contenido)
        return scroll

    def cambiar_idioma(self, nuevo_idioma):
        """!
        @brief Modifica el idioma interno y repinta todos los textos.
        
        @param nuevo_idioma Clave del nuevo idioma ('es_ES' o 'en_US').
        """
        self.idioma_actual = nuevo_idioma
        self.crear_barra_menus()         
        self.actualizar_textos_interfaz()

    def actualizar_textos_interfaz(self):
        """!
        @brief Recorre la GUI inyectando las cadenas correspondientes al idioma seleccionado.
        """
        txt = TRADUCCIONES[self.idioma_actual]
        self.actualizar_titulo_ventana()
        self.tabs.setTabText(0, txt['tab_p9'])
        self.tabs.setTabText(1, txt['tab_m4'])
        
        self.menu_archivo.setTitle(txt['menu_archivo'])
        self.accion_nuevo.setText(txt['accion_nuevo'])
        self.accion_abrir.setText(txt['accion_abrir'])
        self.accion_guardar.setText(txt['accion_guardar'])
        self.accion_exportar.setText(txt['accion_exportar'])
        self.accion_salir.setText(txt['accion_salir'])
        
        self.menu_ejemplos.setTitle(txt['menu_ejemplos'])
        pestaña_activa = self.tabs.currentIndex()
        if pestaña_activa == 0:
            self.accion_ej1.setText(txt['ej_p9_1'])
            self.accion_ej2.setText(txt['ej_p9_2'])
            self.accion_ej3.setText(txt['ej_p9_3'])
        else:
            self.accion_ej1.setText(txt['ej_m4_1'])
            self.accion_ej2.setText(txt['ej_m4_2'])
            self.accion_ej3.setText(txt['ej_m4_3'])
        
        self.menu_idioma.setTitle(txt['menu_idioma'])
        
        self.chk_modo_p9.setText(txt['chk_modo_avanzado'])
        self.lbl_premisas_p9.setText(txt['lbl_premisas_p9'])
        self.lbl_conclusion_p9.setText(txt['lbl_conclusion_p9'])
        self.lbl_libre_p9.setText(txt['lbl_libre_p9'])
        self.btn_p9.setText(txt['btn_verificar_p9'])
        self.lbl_res_p9.setText(txt['lbl_resultado'])
        self.grupo_ins_p9.setTitle(txt['grupo_insercion'])
        self.lbl_ops_p9.setText(txt['lbl_operadores'])
        for boton, clave in self.botones_ops_p9:
            boton.setText(txt[clave])
        
        self.chk_modo_m4.setText(txt['chk_modo_avanzado'])
        self.lbl_premisas_m4.setText(txt['lbl_premisas_m4'])
        self.lbl_objetivo_m4.setText(txt['lbl_objetivo_m4'])
        self.lbl_libre_m4.setText(txt['lbl_libre_m4'])
        self.btn_m4.setText(txt['btn_buscar_m4'])
        self.lbl_res_m4.setText(txt['lbl_resultado'])
        self.grupo_ins_m4.setTitle(txt['grupo_insercion'])
        self.lbl_ops_m4.setText(txt['lbl_operadores'])
        for boton, clave in self.botones_ops_m4:
            boton.setText(txt[clave])
            
        self.grupo_historial.setTitle(txt['tit_historial'])
        self.tabla_historial.setHorizontalHeaderLabels([txt['col_hora'], txt['col_motor'], txt['col_resultado']])
        if not self.ruta_archivo_actual:
            self.barra_estado.showMessage(txt['status_sin_archivo'])
        else:
            self.barra_estado.showMessage(f"{txt['status_abierto']}{self.ruta_archivo_actual}")
        
        cajas = [
            (self.premisas_p9, txt['ph_premisas_p9']), (self.conclusion_p9, txt['ph_conclusion_p9']),
            (self.entrada_libre_p9, txt['ph_libre_p9']), (self.premisas_m4, txt['ph_premisas_m4']),
            (self.conclusion_m4, txt['ph_conclusion_m4']), (self.entrada_libre_m4, txt['ph_libre_m4'])
        ]
        for caja, texto_ejemplo in cajas:
            texto_actual = caja.toPlainText().strip()
            if not texto_actual or texto_actual in [v.strip() for v in TRADUCCIONES['es_ES'].values()] or texto_actual in [v.strip() for v in TRADUCCIONES['en_US'].values()]:
                caja.setPlainText(texto_ejemplo)
                caja.setStyleSheet("color: gray; font-family: 'JetBrains Mono'; font-size: 12pt;")

        dic_paneles = DICCIONARIO_PANELES.get(self.idioma_actual, {})
        def trad(texto_ing): return dic_paneles.get(texto_ing, texto_ing)

        if hasattr(self, 'grupo_basico_p9'):
            self.grupo_basico_p9.setTitle(trad("Basic Options"))
            self.grupo_all_options.setTitle(trad("All Options"))
            self.btn_reset_basico_p9.setText(trad("Reset These to Defaults"))

            self.grupo_basico_m4.setTitle(trad("Basic Options"))
            self.grupo_otros_m4.setTitle(trad("Other Options"))
            self.grupo_exp_m4.setTitle(trad("Experimental Options"))
            self.btn_reset_m4.setText(trad("Reset These to Defaults"))

            for btn in self.botones_reset_cats: btn.setText(trad("Reset These to Defaults"))
            for lbl, orig_txt in self.labels_subcategorias: lbl.setText(trad(orig_txt))

            for i, nombre_ing in enumerate(self.nombres_categorias):
                self.combo_grupos_p9.setItemText(i, trad(nombre_ing))

            for combo in self.combos_traducibles:
                for i in range(combo.count()):
                    combo.setItemText(i, trad(combo.itemData(i)))

    def actualizar_titulo_ventana(self):
        """!
        @brief Refresca el título de la aplicación para mostrar el nombre del archivo activo.
        """
        txt = TRADUCCIONES[self.idioma_actual]
        nombre_base = "Prover9-Mace4 GUI"
        if self.ruta_archivo_actual:
            nombre_fichero = os.path.basename(self.ruta_archivo_actual)
            self.setWindowTitle(f"{nombre_base} - [{nombre_fichero}]")
        else:
            self.setWindowTitle(nombre_base)

    def nuevo_proyecto(self):
        """!
        @brief Limpia los editores de texto previa confirmación si hay cambios no guardados.
        """
        if not self.advertir_cambios_sin_guardar(): return
        for caja in [self.premisas_p9, self.conclusion_p9, self.entrada_libre_p9, self.premisas_m4, self.conclusion_m4, self.entrada_libre_m4]:
            caja.clear()
        self.salida_p9.clear()
        self.salida_m4.clear()
        self.ruta_archivo_actual = None
        self.actualizar_textos_interfaz()
        self.snapshot_guardado = self.obtener_estado_actual()

    def abrir_archivo(self):
        """!
        @brief Abre un cuadro de diálogo para cargar un archivo `.in` en el editor libre.
        """
        if not self.advertir_cambios_sin_guardar(): return
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir / Open", "", "Inputs (*.in *.p9 *.txt)")
        if ruta:
            with open(ruta, "r", encoding="utf-8") as f: contenido = f.read()
            self.ruta_archivo_actual = ruta
            if self.tabs.currentIndex() == 0:
                self.chk_modo_p9.setChecked(True)
                self.entrada_libre_p9.setPlainText(contenido)
                self.entrada_libre_p9.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
            else:
                self.chk_modo_m4.setChecked(True)
                self.entrada_libre_m4.setPlainText(contenido)
                self.entrada_libre_m4.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
            
            self.actualizar_textos_interfaz()
            self.snapshot_guardado = self.obtener_estado_actual()

    def guardar_archivo(self):
        """!
        @brief Guarda el contenido del proyecto activo en el disco físico.
        
        @return True si la operación fue exitosa, False si el usuario canceló.
        """
        txt = TRADUCCIONES[self.idioma_actual]
        if not self.ruta_archivo_actual:
            ruta, _ = QFileDialog.getSaveFileName(self, "Guardar / Save", "", "Inputs (*.in)")
            if not ruta:
                return False
            self.ruta_archivo_actual = ruta

        p = self.tabs.currentIndex()
        idioma_txt = TRADUCCIONES[self.idioma_actual]
        if p == 0:
            texto = self.extraer_texto_util(self.entrada_libre_p9, idioma_txt['ph_libre_p9']) if self.chk_modo_p9.isChecked() else self.cocinar_entrada_p9(self.premisas_p9, self.conclusion_p9)
        else:
            texto = self.extraer_texto_util(self.entrada_libre_m4, idioma_txt['ph_libre_m4']) if self.chk_modo_m4.isChecked() else self.cocinar_entrada_m4(self.premisas_m4, self.conclusion_m4)
        
        try:
            with open(self.ruta_archivo_actual, "w", encoding="utf-8") as f: f.write(texto)
            self.barra_estado.showMessage(f"{txt['status_guardado']}{self.ruta_archivo_actual}", 4000)
            self.actualizar_titulo_ventana()
            self.snapshot_guardado = self.obtener_estado_actual()
            return True
        except Exception:
            self.barra_estado.showMessage(txt['status_error_guardar'], 4000)
            return False

    def exportar_salida(self):
        """!
        @brief Exporta la consola de resultados actual a un archivo `.out`.
        """
        editor = self.salida_p9 if self.tabs.currentIndex() == 0 else self.salida_m4
        if editor.toPlainText().strip():
            ruta, _ = QFileDialog.getSaveFileName(self, "Exportar / Export", "", "Reports (*.out *.txt)")
            if ruta:
                with open(ruta, "w", encoding="utf-8") as f: f.write(editor.toPlainText())

    def cargar_ejemplo_tipo(self, slot_menu):
        """!
        @brief Carga un problema predefinido desde el diccionario de idiomas.
        
        @param slot_menu Entero (1, 2 o 3) correspondiente a la opción del menú pulsada.
        """
        if not self.advertir_cambios_sin_guardar():
            return
            
        txt = TRADUCCIONES[self.idioma_actual]
        pestaña = self.tabs.currentIndex()
        
        if pestaña == 0:
            if slot_menu == 1: tipo = 'silogismo'
            elif slot_menu == 2: tipo = 'paradoja'
            else: tipo = 'algebra'  
            
            premisas_ej = txt[f'datos_{tipo}_premisas']
            conclusion_ej = txt[f'datos_{tipo}_conclusion']
            codigo_completo_libre = self.cocinar_entrada_directa(premisas_ej, conclusion_ej)
            
            self.premisas_p9.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
            self.conclusion_p9.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
            self.entrada_libre_p9.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
            self.premisas_p9.setPlainText(premisas_ej)
            self.conclusion_p9.setPlainText(conclusion_ej)
            self.entrada_libre_p9.setPlainText(codigo_completo_libre)
        else:
            if slot_menu == 1: tipo = 'grupo'
            elif slot_menu == 2: tipo = 'conmut'
            else: tipo = 'reticulo' 
            
            premisas_ej = txt[f'datos_{tipo}_premisas']
            conclusion_ej = txt[f'datos_{tipo}_conclusion']
            codigo_completo_libre = self.cocinar_entrada_directa(premisas_ej, conclusion_ej)
            
            self.premisas_m4.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
            self.conclusion_m4.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
            self.entrada_libre_m4.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
            self.premisas_m4.setPlainText(premisas_ej)
            self.conclusion_m4.setPlainText(conclusion_ej)
            self.entrada_libre_m4.setPlainText(codigo_completo_libre)

        self.snapshot_guardado = self.obtener_estado_actual()

    def obtener_estado_actual(self):
        """!
        @brief Genera un diccionario 'snapshot' con todos los textos actuales.
        
        @return Diccionario que mapea los estados de los editores para comprobación.
        """
        return {
            'p9_av': self.chk_modo_p9.isChecked(), 'p9_p': self.premisas_p9.toPlainText(),
            'p9_c': self.conclusion_p9.toPlainText(), 'p9_l': self.entrada_libre_p9.toPlainText(),
            'm4_av': self.chk_modo_m4.isChecked(), 'm4_p': self.premisas_m4.toPlainText(),
            'm4_c': self.conclusion_m4.toPlainText(), 'm4_l': self.entrada_libre_m4.toPlainText()
        }

    def advertir_cambios_sin_guardar(self):
        """!
        @brief Lanza un MessageBox si detecta discrepancias con el último guardado.
        
        @return True si es seguro proceder, False si el usuario aborta la acción.
        """
        if getattr(self, 'snapshot_guardado', None) == self.obtener_estado_actual():
            return True

        es_en = (self.idioma_actual == 'en_US')
        titulo = "Unsaved Changes" if es_en else "Cambios sin guardar"
        mensaje = "You have unsaved changes.\nDo you want to save them before proceeding?" if es_en else "Tienes modificaciones sin guardar.\n¿Deseas guardarlas antes de continuar?"
        
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(mensaje)
        msg.setIcon(QMessageBox.Icon.Warning)
        
        btn_guardar = msg.addButton("Save" if es_en else "Guardar", QMessageBox.ButtonRole.AcceptRole)
        btn_descartar = msg.addButton("Discard" if es_en else "Descartar", QMessageBox.ButtonRole.DestructiveRole)
        btn_cancelar = msg.addButton("Cancel" if es_en else "Cancelar", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == btn_guardar:
            return self.guardar_archivo()
        elif msg.clickedButton() == btn_descartar:
            return True
        else:
            return False

    def closeEvent(self, evento):
        """!
        @brief Interceptor del cierre de ventana (cruz de Windows/macOS).
        
        @param evento Objeto de evento de cierre propiciado por Qt.
        """
        if self.advertir_cambios_sin_guardar():
            evento.accept()
        else:
            evento.ignore()

    def eventFilter(self, objeto, evento):
        """!
        @brief Filtro global para recrear el efecto Placeholder.
        
        @param objeto Componente emisor del evento.
        @param evento Evento interceptado (FocusIn o FocusOut).
        @return True si se maneja el evento nativamente.
        """
        txt = TRADUCCIONES[self.idioma_actual]
        mapeo_ejemplos = {
            self.premisas_p9: txt['ph_premisas_p9'],
            self.conclusion_p9: txt['ph_conclusion_p9'],
            self.entrada_libre_p9: txt['ph_libre_p9'],
            self.premisas_m4: txt['ph_premisas_m4'],
            self.conclusion_m4: txt['ph_conclusion_m4'],
            self.entrada_libre_m4: txt['ph_libre_m4']
        }
        if objeto in mapeo_ejemplos:
            if evento.type() == QEvent.Type.FocusIn:
                if objeto.toPlainText().strip() == mapeo_ejemplos[objeto].strip():
                    objeto.clear()
                    objeto.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
            elif evento.type() == QEvent.Type.FocusOut:
                if not objeto.toPlainText().strip():
                    objeto.setPlainText(mapeo_ejemplos[objeto])
                    objeto.setStyleSheet("color: gray; font-family: 'JetBrains Mono'; font-size: 12pt;")
        return super().eventFilter(objeto, evento) 

    def alternar_modo_p9(self, checked):
        """!
        @brief Transita entre la vista Básica y Avanzada en Prover9, traduciendo fórmulas.
        
        @param checked Booleano que indica si el modo avanzado está marcado.
        """
        txt = TRADUCCIONES[self.idioma_actual]
        if checked: 
            premisas = self.extraer_texto_util(self.premisas_p9, txt['ph_premisas_p9'])
            conclusion = self.extraer_texto_util(self.conclusion_p9, txt['ph_conclusion_p9'])
            if premisas or conclusion:
                codigo = self.cocinar_entrada_directa(premisas, conclusion)
                self.entrada_libre_p9.setPlainText(codigo)
                self.entrada_libre_p9.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
        else: 
            texto_libre = self.extraer_texto_util(self.entrada_libre_p9, txt['ph_libre_p9'])
            if texto_libre:
                p, c = self.extraer_formulas_regex(texto_libre)
                if p: 
                    self.premisas_p9.setPlainText(p)
                    self.premisas_p9.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
                if c: 
                    self.conclusion_p9.setPlainText(c)
                    self.conclusion_p9.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
        self.vista_stack_p9.setCurrentIndex(1 if checked else 0)

    def alternar_modo_m4(self, checked):
        """!
        @brief Transita entre la vista Básica y Avanzada en Mace4, traduciendo fórmulas.
        
        @param checked Booleano que indica si el modo avanzado está marcado.
        """
        txt = TRADUCCIONES[self.idioma_actual]
        if checked:
            premisas = self.extraer_texto_util(self.premisas_m4, txt['ph_premisas_m4'])
            conclusion = self.extraer_texto_util(self.conclusion_m4, txt['ph_conclusion_m4'])
            if premisas or conclusion:
                codigo = self.cocinar_entrada_directa(premisas, conclusion)
                self.entrada_libre_m4.setPlainText(codigo)
                self.entrada_libre_m4.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
        else:
            texto_libre = self.extraer_texto_util(self.entrada_libre_m4, txt['ph_libre_m4'])
            if texto_libre:
                p, c = self.extraer_formulas_regex(texto_libre)
                if p: 
                    self.premisas_m4.setPlainText(p)
                    self.premisas_m4.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
                if c: 
                    self.conclusion_m4.setPlainText(c)
                    self.conclusion_m4.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
        self.vista_stack_m4.setCurrentIndex(1 if checked else 0)

    def inyectar_operador_inteligente(self, simbolo, clave_op):
        """!
        @brief Inserta un símbolo lógico en el editor con foco o el predeterminado.
        
        @param simbolo Cadena representativa (ej. ' -> ').
        @param clave_op Clave del diccionario (para tracking).
        """
        pestaña = self.tabs.currentIndex()
        caja = None
        txt = TRADUCCIONES[self.idioma_actual]
        if pestaña == 0:
            caja = self.entrada_libre_p9 if self.chk_modo_p9.isChecked() else self.premisas_p9
            ejemplo = txt['ph_libre_p9'] if self.chk_modo_p9.isChecked() else txt['ph_premisas_p9']
        else:
            caja = self.entrada_libre_m4 if self.chk_modo_m4.isChecked() else self.premisas_m4
            ejemplo = txt['ph_libre_m4'] if self.chk_modo_m4.isChecked() else txt['ph_premisas_m4']
        if caja:
            if caja.toPlainText().strip() == ejemplo.strip():
                caja.clear()
                caja.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
            caja.insertPlainText(simbolo)
            caja.setFocus()

    def reset_opciones_p9(self):
        """!
        @brief Restaura los valores por defecto del panel visual de Prover9 (Basic Options).
        """
        self.spin_max_weight.setValue(100)
        self.spin_pick_ratio.setValue(-1)
        self.combo_order.setCurrentText("lpo")
        self.combo_eq_defs.setCurrentText("unfold")
        self.chk_expand_relational.setChecked(False)
        self.chk_restrict_denials.setChecked(False)
        self.spin_max_seconds_p9.setValue(60)
        self.chk_prolog_vars.setChecked(False)

    def reset_categoria_p9(self, categoria):
        """!
        @brief Restaura a valores por defecto los widgets de una categoría concreta.
        
        @param categoria Nombre del grupo (ej. 'Term Ordering').
        """
        for nombre, (chk, por_defecto, cat) in self.all_flags_p9.items():
            if cat == categoria:
                chk.setChecked(por_defecto)
        for nombre, (widget, por_defecto, cat) in self.all_assigns_p9.items():
            if cat == categoria:
                if isinstance(widget, QSpinBox):
                    widget.setValue(por_defecto)
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(por_defecto)

    def reset_opciones_m4(self):
        """!
        @brief Restaura los valores por defecto de todos los paneles en Mace4.
        """
        self.spin_domain_size.setValue(0)
        self.spin_start_size.setValue(2)
        self.spin_end_size.setValue(-1)
        self.spin_increment.setValue(1)
        self.combo_iterate.setCurrentText("all")
        self.spin_max_models.setValue(1)
        self.spin_max_seconds_m4.setValue(60)
        self.spin_max_seconds_per.setValue(-1)
        self.chk_prolog_vars_m4.setChecked(False)
        self.chk_integer_ring.setChecked(False)
        self.chk_skolems_last.setChecked(False)
        self.spin_max_megs.setValue(200)
        self.chk_print_models.setChecked(True)
        self.chk_lnh.setChecked(True)
        self.chk_negprop.setChecked(True)
        self.chk_neg_assign.setChecked(True)
        self.chk_neg_assign_near.setChecked(True)
        self.chk_neg_elim.setChecked(True)
        self.chk_neg_elim_near.setChecked(True)
        self.spin_selection_order.setValue(2)
        self.spin_selection_measure.setValue(4)

    def agregar_al_historial(self, hora, motor, tag_resultado, snapshot_datos):
        """!
        @brief Introduce un nuevo registro analizado en la tabla y memoria del historial.
        
        @param hora Etiqueta temporal (string).
        @param motor Nombre del motor ejecutado.
        @param tag_resultado Identificador semántico (ej. 'proved', 'counter').
        @param snapshot_datos Configuración íntegra de la UI a persistir.
        """
        txt = TRADUCCIONES[self.idioma_actual]
        dict_tags = {
            'proved': txt['hist_proved'], 'no_proved': txt['hist_no_proved'],
            'counter': txt['hist_counter'], 'no_counter': txt['hist_no_counter'],
            'timeout': txt['hist_timeout'], 'error': txt['hist_error']
        }
        self.tabla_historial.insertRow(0)
        self.tabla_historial.setItem(0, 0, QTableWidgetItem(hora))
        self.tabla_historial.setItem(0, 1, QTableWidgetItem(motor))
        self.tabla_historial.setItem(0, 2, QTableWidgetItem(dict_tags.get(tag_resultado, tag_resultado)))
        self.datos_historial.insert(0, snapshot_datos)

    def recuperar_desde_historial(self, item):
        """!
        @brief Restaura todo el estado de la UI (texto y modos) haciendo doble click en la tabla.
        
        @param item Fila seleccionada por el usuario en QTableWidget.
        """
        fila = item.row()
        if fila >= len(self.datos_historial):
            return
        snap = self.datos_historial[fila]
        pestaña = snap['pestaña']
        self.tabs.setCurrentIndex(pestaña)
        
        if pestaña == 0:
            self.chk_modo_p9.setChecked(snap['modo_avanzado'])
            self.premisas_p9.setPlainText(snap['premisas'])
            self.conclusion_p9.setPlainText(snap['conclusion'])
            self.entrada_libre_p9.setPlainText(snap['libre'])
            for c in [self.premisas_p9, self.conclusion_p9, self.entrada_libre_p9]:
                c.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")
        else:
            self.chk_modo_m4.setChecked(snap['modo_avanzado'])
            self.premisas_m4.setPlainText(snap['premisas'])
            self.conclusion_m4.setPlainText(snap['conclusion'])
            self.entrada_libre_m4.setPlainText(snap['libre'])
            for c in [self.premisas_m4, self.conclusion_m4, self.entrada_libre_m4]:
                c.setStyleSheet("color: #ffffff; font-family: 'JetBrains Mono'; font-size: 12pt;")

    def procesar_prover9(self):
        """!
        @brief Recolecta la entrada, desactiva la UI y lanza el subproceso del demostrador.
        """
        txt = TRADUCCIONES[self.idioma_actual]
        snapshot = {
            'pestaña': 0, 'modo_avanzado': self.chk_modo_p9.isChecked(),
            'premisas': self.premisas_p9.toPlainText(), 'conclusion': self.conclusion_p9.toPlainText(),
            'libre': self.entrada_libre_p9.toPlainText()
        }
        
        if self.chk_modo_p9.isChecked():
            texto_final = self.extraer_texto_util(self.entrada_libre_p9, txt['ph_libre_p9'])
        else:
            premisas = self.extraer_texto_util(self.premisas_p9, txt['ph_premisas_p9'])
            conclusion = self.extraer_texto_util(self.conclusion_p9, txt['ph_conclusion_p9'])
            texto_final = self.cocinar_entrada_p9(self.premisas_p9, self.conclusion_p9) if (premisas or conclusion) else ""
            
        if not texto_final.strip():
            self.salida_p9.setPlainText("❌ Error: No hay datos de entrada válidos.")
            return

        self.btn_p9.setEnabled(False)
        self.btn_p9.setText("Procesando... (Por favor, espera)")
        self.btn_p9.setStyleSheet("font-weight: bold; background-color: #f39c12; color: white; padding: 10px;")
        self.salida_p9.setPlainText(txt['msg_procesando_p9'])

        self.hilo_p9 = HiloMotor('prover9', texto_final, self.spin_max_seconds_p9.value(), snapshot)
        self.hilo_p9.resultado_listo.connect(self.al_terminar_prover9)
        self.hilo_p9.start()

    def al_terminar_prover9(self, resultado_crudo, hora, snapshot):
        """!
        @brief Captura la señal final de Prover9, imprime salidas y refresca historial.
        
        @param resultado_crudo Texto íntegro generado por el log del motor.
        @param hora Sello de tiempo final.
        @param snapshot Datos persistidos para vincular a esta ejecución.
        """
        resultado_traducido, tag = self.limpiar_y_traducir_error(resultado_crudo)
        self.salida_p9.setPlainText(resultado_traducido)
        self.agregar_al_historial(hora, "Prover9", tag, snapshot)
        
        txt = TRADUCCIONES[self.idioma_actual]
        self.btn_p9.setEnabled(True)
        self.btn_p9.setText(txt['btn_verificar_p9'])
        self.btn_p9.setStyleSheet("font-weight: bold; background-color: #2962ff; color: white; padding: 10px;")

    def procesar_mace4(self):
        """!
        @brief Recolecta la entrada, desactiva la UI y lanza el subproceso buscador de modelos.
        """
        txt = TRADUCCIONES[self.idioma_actual]
        snapshot = {
            'pestaña': 1, 'modo_avanzado': self.chk_modo_m4.isChecked(),
            'premisas': self.premisas_m4.toPlainText(), 'conclusion': self.conclusion_m4.toPlainText(),
            'libre': self.entrada_libre_m4.toPlainText()
        }
        
        if self.chk_modo_m4.isChecked():
            texto_final = self.extraer_texto_util(self.entrada_libre_m4, txt['ph_libre_m4'])
        else:
            premisas = self.extraer_texto_util(self.premisas_m4, txt['ph_premisas_m4'])
            conclusion = self.extraer_texto_util(self.conclusion_m4, txt['ph_conclusion_m4'])
            texto_final = self.cocinar_entrada_m4(self.premisas_m4, self.conclusion_m4) if (premisas or conclusion) else ""

        if not texto_final.strip():
            self.salida_m4.setPlainText("❌ Error: No hay datos de entrada válidos.")
            return

        self.btn_m4.setEnabled(False)
        self.btn_m4.setText("Procesando... (Por favor, espera)")
        self.btn_m4.setStyleSheet("font-weight: bold; background-color: #f39c12; color: white; padding: 10px;")
        self.salida_m4.setPlainText(txt['msg_procesando_m4'])

        self.hilo_m4 = HiloMotor('mace4', texto_final, self.spin_max_seconds_m4.value(), snapshot)
        self.hilo_m4.resultado_listo.connect(self.al_terminar_m4)
        self.hilo_m4.start()

    def al_terminar_m4(self, resultado_crudo, hora, snapshot):
        """!
        @brief Captura la señal final de Mace4, imprime matrices y refresca historial.
        
        @param resultado_crudo Texto íntegro generado por el log del motor.
        @param hora Sello de tiempo final.
        @param snapshot Datos persistidos para vincular a esta ejecución.
        """
        resultado_traducido, tag = self.limpiar_y_traducir_error(resultado_crudo)
        self.salida_m4.setPlainText(resultado_traducido)
        self.agregar_al_historial(hora, "Mace4", tag, snapshot)
        
        txt = TRADUCCIONES[self.idioma_actual]
        self.btn_m4.setEnabled(True)
        self.btn_m4.setText(txt['btn_buscar_m4'])
        self.btn_m4.setStyleSheet("font-weight: bold; background-color: #d32f2f; color: white; padding: 10px;")

    def cocinar_entrada_p9(self, caja_premisas, caja_conclusion):
        """!
        @brief Compone el script fuente .in anexando las configuraciones del usuario.
        
        @param caja_premisas Editor que contiene axiomas (sos).
        @param caja_conclusion Editor que contiene teoremas (goals).
        @return Script validado de Prover9 listo para ser ejecutado.
        """
        texto_cocinado = ""
        if hasattr(self, 'grupo_all_options') and self.grupo_all_options.isChecked():
            for nombre, (widget, _, _) in self.all_assigns_p9.items():
                val = widget.value() if isinstance(widget, QSpinBox) else widget.currentData()
                if nombre == "pick_given_ratio" and val == -1:
                    continue
                texto_cocinado += f"assign({nombre}, {val}).\n"
            for nombre, (chk, _, _) in self.all_flags_p9.items():
                if chk.isChecked(): texto_cocinado += f"set({nombre}).\n"
                else: texto_cocinado += f"clear({nombre}).\n"
        else:
            texto_cocinado += f"assign(max_weight, {self.spin_max_weight.value()}).\n"
            if self.spin_pick_ratio.value() != -1:
                texto_cocinado += f"assign(pick_given_ratio, {self.spin_pick_ratio.value()}).\n"
            texto_cocinado += f"assign(order, {self.combo_order.currentData()}).\n"
            texto_cocinado += f"assign(eq_defs, {self.combo_eq_defs.currentData()}).\n"
            texto_cocinado += f"assign(max_seconds, {self.spin_max_seconds_p9.value()}).\n"
            
            flags_basicos = [
                ('expand_relational_defs', self.chk_expand_relational),
                ('restrict_denials', self.chk_restrict_denials),
                ('prolog_style_variables', self.chk_prolog_vars)
            ]
            for nombre, widget in flags_basicos:
                if widget.isChecked(): texto_cocinado += f"set({nombre}).\n"
                else: texto_cocinado += f"clear({nombre}).\n"
                
        texto_cocinado += "\n"
        lineas_premisas = caja_premisas.toPlainText().split('\n')
        conclusion = caja_conclusion.toPlainText().strip()
        
        texto_cocinado += "formulas(sos).\n"
        for linea in lineas_premisas:
            linea_limpia = linea.strip()
            if linea_limpia:
                if not linea_limpia.endswith('.'):
                    linea_limpia += '.'
                texto_cocinado += f"  {linea_limpia}\n"
        texto_cocinado += "end_of_list.\n\n"
        
        if conclusion:
            if not conclusion.endswith('.'):
                conclusion += '.'
            texto_cocinado += f"formulas(goals).\n  {conclusion}\nend_of_list.\n"
        return texto_cocinado

    def cocinar_entrada_m4(self, caja_premisas, caja_conclusion):
        """!
        @brief Compone el script fuente .in anexando dominios de búsqueda y heurísticas.
        
        @param caja_premisas Editor que contiene axiomas (sos).
        @param caja_conclusion Editor que contiene metas sospechosas de ser falsas.
        @return Script validado de Mace4 listo para ser ejecutado.
        """
        texto_cocinado = ""
        if self.spin_domain_size.value() > 0:
            texto_cocinado += f"assign(domain_size, {self.spin_domain_size.value()}).\n"
        texto_cocinado += f"assign(start_size, {self.spin_start_size.value()}).\n"
        texto_cocinado += f"assign(end_size, {self.spin_end_size.value()}).\n"
        texto_cocinado += f"assign(increment, {self.spin_increment.value()}).\n"
        texto_cocinado += f"assign(iterate, {self.combo_iterate.currentData()}).\n"
        texto_cocinado += f"assign(max_models, {self.spin_max_models.value()}).\n"
        texto_cocinado += f"assign(max_seconds, {self.spin_max_seconds_m4.value()}).\n"
        texto_cocinado += f"assign(max_seconds_per, {self.spin_max_seconds_per.value()}).\n"
        texto_cocinado += f"assign(max_megs, {self.spin_max_megs.value()}).\n"
        texto_cocinado += f"assign(selection_order, {self.spin_selection_order.value()}).\n"
        texto_cocinado += f"assign(selection_measure, {self.spin_selection_measure.value()}).\n"

        flags_m4 = {
            'prolog_style_variables': self.chk_prolog_vars_m4, 'integer_ring': self.chk_integer_ring,
            'skolems_last': self.chk_skolems_last, 'print_models': self.chk_print_models,
            'lnh': self.chk_lnh, 'negprop': self.chk_negprop, 'neg_assign': self.chk_neg_assign,
            'neg_assign_near': self.chk_neg_assign_near, 'neg_elim': self.chk_neg_elim,
            'neg_elim_near': self.chk_neg_elim_near
        }
        for flag, widget in flags_m4.items():
            if widget.isChecked(): texto_cocinado += f"set({flag}).\n"
            else: texto_cocinado += f"clear({flag}).\n"

        texto_cocinado += "\n"
        lineas_premisas = caja_premisas.toPlainText().split('\n')
        conclusion = caja_conclusion.toPlainText().strip()
        
        texto_cocinado += "formulas(sos).\n"
        for linea in lineas_premisas:
            linea_limpia = linea.strip()
            if linea_limpia:
                if not linea_limpia.endswith('.'): linea_limpia += '.'
                texto_cocinado += f"  {linea_limpia}\n"
        texto_cocinado += "end_of_list.\n\n"

        if conclusion:
            if not conclusion.endswith('.'): conclusion += '.'
            texto_cocinado += f"formulas(goals).\n  {conclusion}\nend_of_list.\n"
        return texto_cocinado

    def cocinar_entrada_directa(self, texto_premisas, texto_conclusion):
        """!
        @brief Envuelve axiomas limpios dentro de bloques de lista sintácticos.
        
        @param texto_premisas Cadena con premisas lógicas directas.
        @param texto_conclusion Cadena con objetivos a probar.
        @return Salida formatada en código Prover9 nativo.
        """
        lineas_premisas = texto_premisas.split('\n')
        conclusion = texto_conclusion.strip()
        texto_cocinado = "formulas(sos).\n"
        for linea in lineas_premisas:
            linea_limpia = linea.strip()
            if linea_limpia:
                if not linea_limpia.endswith('.'):
                    linea_limpia += '.'
                texto_cocinado += f"  {linea_limpia}\n"
        texto_cocinado += "end_of_list.\n\n"
        if conclusion:
            if not conclusion.endswith('.'):
                conclusion += '.'
            texto_cocinado += f"formulas(goals).\n  {conclusion}\nend_of_list.\n"
        return texto_cocinado

    def extraer_texto_util(self, caja, ejemplo_plantilla):
        """!
        @brief Descarta el Placeholder garantizando strings limpios en caso de inactividad.
        
        @param caja Editor a consultar.
        @param ejemplo_plantilla Texto gris por defecto en diccionarios.
        @return Cadena vacía o texto genuino escrito.
        """
        t = caja.toPlainText().strip()
        if t == ejemplo_plantilla.strip():
            return ""
        return t

    def extraer_formulas_regex(self, texto):
        """!
        @brief Analiza y extrae fórmulas usando expresiones regulares (regex).
        
        Utilizado principalmente al transitar del modo avanzado al básico.
        
        @param texto Código fuente bruto generado previamente.
        @return Tupla con premisas (sos) y conclusión (goals) sin delimitadores.
        """
        premisas, conclusion = "", ""
        match_sos = re.search(r'formulas\(sos\)\.(.*?)(?:end_of_list\.)', texto, re.DOTALL)
        if match_sos:
            premisas = '\n'.join([l.strip().rstrip('.') for l in match_sos.group(1).strip().split('\n') if l.strip()])
            
        match_goals = re.search(r'formulas\(goals\)\.(.*?)(?:end_of_list\.)', texto, re.DOTALL)
        if match_goals:
            conclusion = '\n'.join([l.strip().rstrip('.') for l in match_goals.group(1).strip().split('\n') if l.strip()])
            
        return premisas, conclusion

    def limpiar_y_traducir_error(self, salida_cruda):
        """!
        @brief Analizador inteligente del log en bruto del demostrador.
        
        Parsea el texto para detectar teoremas probados, contramodelos 
        o errores sintácticos. Desecha líneas superfluas del compilador.
        
        @param salida_cruda Resultado íntegro stdout del subproceso OS.
        @return Tupla con el texto depurado/bilingüe y el identificador ('tag') para el historial.
        """
        texto = salida_cruda.strip()
        pestaña_activa = self.tabs.currentIndex()
        es_en = (self.idioma_actual == 'en_US')
        
        if not texto or "Error" in texto:
            return f"❌ ERROR:\n{salida_cruda}", 'error'

        patrones_error = ["fatal_error", "LABEL: syntax error", "syn_err", "cloffset", "appears more than once", "error"]
        if any(patron in texto for patron in patrones_error):
            if es_en:
                return f"❌ DETECTED SYNTAX ERROR\n---------------------------------\nReview operators.\n\n=== ENGINE LOG ===\n{salida_cruda}", 'error'
            return f"❌ ERROR DE SINTAXIS DETECTADO\n---------------------------------\nRevisa conectivas.\n\n=== DETALLE TÉCNICO ===\n{salida_cruda}", 'error'

        if "TIMEOUT_EXPIRED" in texto:
            return salida_cruda, 'timeout'

        if pestaña_activa == 0:
            if "THEOREM PROVED" in texto:
                prueba_limpia = ""
                for linea in texto.split('\n'):
                    if "=== PROOF ===" in linea or "SUBPROOF" in linea or prueba_limpia:
                        prueba_limpia += linea + "\n"
                    if "end of proof" in linea: break
                if es_en:
                    return f"✅ THEOREM PROVED SUCCESSFULLY!\n---------------------------------\n=== PROOF STEPS ===\n{prueba_limpia.strip()}\n\n=== FULL LOG ===\n{salida_cruda}", 'proved'
                return f"✅ ¡TEOREMA DEMOSTRADO CON ÉXITO!\n---------------------------------\n=== PASOS DEDUCTIVOS ===\n{prueba_limpia.strip()}\n\n=== LOG COMPLETO ===\n{salida_cruda}", 'proved'
            else:
                if es_en:
                    return f"⚠️ THEOREM COULD NOT BE PROVED\n---------------------------------\n=== ENGINE LOG ===\n{salida_cruda}", 'no_proved'
                return f"⚠️ EL TEOREMA NO SE PUDO DEMOSTRAR\n---------------------------------\n=== DETALLE TÉCNICO ===\n{salida_cruda}", 'no_proved'
        else:
            if "model(s) found" in texto or "Exiting with 1 model" in texto or "interpretation" in texto:
                modelo_limpio = ""
                for linea in texto.split('\n'):
                    if "interpretation(" in linea or modelo_limpio:
                        modelo_limpio += linea + "\n"
                    if "end_of_interpretation" in linea: break
                if es_en:
                    return f"🔮 COUNTEREXAMPLE FOUND\n---------------------------------\n=== MATRIX STRUCT ===\n{modelo_limpio.strip()}\n\n=== FULL LOG ===\n{salida_cruda}", 'counter'
                return f"🔮 CONTRAEJEMPLO ENCONTRADO (EL TEOREMA ES FALSO)\n---------------------------------\n=== MATRIZ SEMÁNTICA ===\n{modelo_limpio.strip()}\n\n=== LOG COMPLETO ===\n{salida_cruda}", 'counter'
            else:
                if es_en:
                    return f"ℹ️ NO COUNTEREXAMPLES FOUND\n---------------------------------\n=== ENGINE LOG ===\n{salida_cruda}", 'no_counter'
                return f"ℹ️ MACE4 NO ENCONTRÓ CONTRAEJEMPLOS\n---------------------------------\n=== DETALLE TÉCNICO ===\n{salida_cruda}", 'no_counter'


if __name__ == "__main__":
    import ctypes
    myappid = 'ugr.tfg.prover9mace4.gui' 
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    QFontDatabase.addApplicationFont(ruta_recurso("Nexa-Heavy.ttf"))
    
    extra_config = {
        'font_family': 'Nexa',
    }
    
    apply_stylesheet(app, theme='dark_lightgreen.xml', extra=extra_config)
    
    ventana = VentanaPrincipal()
    ventana.showMaximized()
    
    sys.exit(app.exec())