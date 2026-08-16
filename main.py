import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QTabWidget, QFileDialog, QGroupBox, QCheckBox, QStackedWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView, QStatusBar,
                             QWidgetAction, QSpinBox, QFormLayout, QComboBox, QScrollArea)
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtCore import QEvent

from launcher import ejecutar_prover9, ejecutar_mace4
from idiomas import TRADUCCIONES

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.idioma_actual = 'es_ES'
        self.ruta_archivo_actual = None  # Almacena la ruta del archivo vinculado (.in)
        self.datos_historial = []        # Caché para restaurar fórmulas del historial
        self.init_ui()
        
    def init_ui(self):
        self.setGeometry(100, 100, 1100, 900)
        
        # Widget Central y Layout Principal de la ventana (Vertical)
        widget_central = QWidget()
        layout_central_ventana = QVBoxLayout(widget_central)
        
        # 1. Contenedor de Pestañas
        self.tabs = QTabWidget()
        self.tab_prover9 = QWidget()
        self.tab_mace4 = QWidget()
        self.tabs.addTab(self.tab_prover9, "")
        self.tabs.addTab(self.tab_mace4, "")
        self.tabs.currentChanged.connect(self.actualizar_textos_interfaz)
        
        # Configuración de contenidos de las pestañas
        self.configurar_tab_prover9()
        self.configurar_tab_mace4()
        
        layout_central_ventana.addWidget(self.tabs, stretch=3)
        
        # 2. PANEL DEL HISTORIAL (Fondo de la aplicación)
        self.grupo_historial = QGroupBox("")
        layout_historial = QVBoxLayout(self.grupo_historial)
        
        self.tabla_historial = QTableWidget(0, 3) # 0 filas iniciales, 3 columnas
        self.tabla_historial.setFont(QFont("Segoe UI", 9))
        self.tabla_historial.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_historial.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_historial.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_historial.itemDoubleClicked.connect(self.recuperar_desde_historial)
        
        layout_historial.addWidget(self.tabla_historial)
        layout_central_ventana.addWidget(self.grupo_historial, stretch=1)
        
        self.setCentralWidget(widget_central)
        
        # 3. Barra de Estado (Status Bar)
        self.barra_estado = QStatusBar()
        self.setStatusBar(self.barra_estado)
        
        # 4. Filtros de eventos de foco para placeholders simulados
        self.premisas_p9.installEventFilter(self)
        self.conclusion_p9.installEventFilter(self)
        self.entrada_libre_p9.installEventFilter(self)
        self.premisas_m4.installEventFilter(self)
        self.conclusion_m4.installEventFilter(self)
        self.entrada_libre_m4.installEventFilter(self)
        
        # 5. Menús y traducción inicial
        self.crear_barra_menus()
        self.actualizar_textos_interfaz()

    def eventFilter(self, objeto, evento):
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
                    objeto.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            elif evento.type() == QEvent.Type.FocusOut:
                if not objeto.toPlainText().strip():
                    objeto.setPlainText(mapeo_ejemplos[objeto])
                    objeto.setStyleSheet("color: gray; font-family: 'Courier New'; font-size: 11pt;")
        return super().eventFilter(objeto, evento)

    def crear_barra_menus(self):
        self.menuBar().clear()
        barra_menus = self.menuBar()
        
        # Menú Archivo
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
        
        # Menú Ejemplos
        self.menu_ejemplos = barra_menus.addMenu("")
        self.accion_ej1 = QAction("", self)
        self.accion_ej1.triggered.connect(lambda: self.cargar_ejemplo_tipo(1))
        self.accion_ej2 = QAction("", self)
        self.accion_ej2.triggered.connect(lambda: self.cargar_ejemplo_tipo(2))
        self.menu_ejemplos.addAction(self.accion_ej1)
        self.menu_ejemplos.addAction(self.accion_ej2)
        
        # Menú Idioma
        self.menu_idioma = barra_menus.addMenu("")
        accion_es = QAction("Español (es-ES)", self)
        accion_es.triggered.connect(lambda: self.cambiar_idioma('es_ES'))
        accion_en = QAction("English (en-US)", self)
        accion_en.triggered.connect(lambda: self.cambiar_idioma('en_US'))
        self.menu_idioma.addAction(accion_es)
        self.menu_idioma.addAction(accion_en)

    def cambiar_idioma(self, nuevo_idioma):
        self.idioma_actual = nuevo_idioma
        self.crear_barra_menus()         
        self.actualizar_textos_interfaz() 

    def actualizar_textos_interfaz(self):
        txt = TRADUCCIONES[self.idioma_actual]
        
        # Título dinámico respetando el archivo vinculado
        self.actualizar_titulo_ventana()
        
        self.tabs.setTabText(0, txt['tab_p9'])
        self.tabs.setTabText(1, txt['tab_m4'])
        
        self.menu_archivo.setTitle(txt['menu_archivo'])
        self.accion_nuevo.setText(txt['accion_nuevo'])
        self.accion_abrir.setText(txt['accion_abrir'])
        self.accion_guardar.setText(txt['accion_guardar'])
        self.accion_exportar.setText(txt['accion_exportar'])
        self.accion_salir.setText(txt['accion_salir'])
        
        # Menú de ejemplos contextual según la pestaña activa
        self.menu_ejemplos.setTitle(txt['menu_ejemplos'])
        pestaña_activa = self.tabs.currentIndex()
        if pestaña_activa == 0:
            self.accion_ej1.setText(txt['ej_p9_1'])
            self.accion_ej2.setText(txt['ej_p9_2'])
        else:
            self.accion_ej1.setText(txt['ej_m4_1'])
            self.accion_ej2.setText(txt['ej_m4_2'])
        
        self.menu_idioma.setTitle(txt['menu_idioma'])
        
        # Elementos de la pestaña Prover9
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
        
        # Elementos de la pestaña Mace4
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
            
        # Historial y barra de estado
        self.grupo_historial.setTitle(txt['tit_historial'])
        self.tabla_historial.setHorizontalHeaderLabels([txt['col_hora'], txt['col_motor'], txt['col_resultado']])
        if not self.ruta_archivo_actual:
            self.barra_estado.showMessage(txt['status_sin_archivo'])
        else:
            self.barra_estado.showMessage(f"{txt['status_abierto']}{self.ruta_archivo_actual}")
        
        # Placeholders dinámicos simulados con control multilínea
        cajas = [
            (self.premisas_p9, txt['ph_premisas_p9']), (self.conclusion_p9, txt['ph_conclusion_p9']),
            (self.entrada_libre_p9, txt['ph_libre_p9']), (self.premisas_m4, txt['ph_premisas_m4']),
            (self.conclusion_m4, txt['ph_conclusion_m4']), (self.entrada_libre_m4, txt['ph_libre_m4'])
        ]
        for caja, texto_ejemplo in cajas:
            texto_actual = caja.toPlainText().strip()
            if not texto_actual or texto_actual in [v.strip() for v in TRADUCCIONES['es_ES'].values()] or texto_actual in [v.strip() for v in TRADUCCIONES['en_US'].values()]:
                caja.setPlainText(texto_ejemplo)
                caja.setStyleSheet("color: gray; font-family: 'Courier New'; font-size: 11pt;")

    def actualizar_titulo_ventana(self):
        """Calcula el título de la barra superior dependiendo del archivo abierto"""
        txt = TRADUCCIONES[self.idioma_actual]
        nombre_base = "Prover9-Mace4 GUI"
        if self.ruta_archivo_actual:
            nombre_fichero = os.path.basename(self.ruta_archivo_actual)
            self.setWindowTitle(f"{nombre_base} - [{nombre_fichero}]")
        else:
            self.setWindowTitle(nombre_base)

    def crear_panel_insercion(self, editor_destino):
        grupo = QGroupBox("")
        layout_grupo = QVBoxLayout()
        estilo_btn = "padding: 5px; font-weight: bold; background-color: #f0f0f0;"
        lbl_ops = QLabel("")
        layout_grupo.addWidget(lbl_ops)
        botones_ops = []
        operadores_config = [
            ('op_neg', " - "), ('op_conj', " & "), ('op_disj', " | "), 
            ('op_impl', " -> "), ('op_equiv', " <-> ")
        ]
        for clave, simbolo in operadores_config:
            btn = QPushButton("") 
            btn.setStyleSheet(estilo_btn)
            btn.clicked.connect(lambda checked, s=simbolo, c_clave=clave: self.inyectar_operador_inteligente(s, c_clave))
            layout_grupo.addWidget(btn)
            botones_ops.append((btn, clave))
        layout_grupo.addStretch()
        grupo.setLayout(layout_grupo)
        grupo.setFixedWidth(180)
        return grupo, lbl_ops, botones_ops

    def inyectar_operador_inteligente(self, simbolo, clave_op):
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
                caja.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            caja.insertPlainText(simbolo)
            caja.setFocus()

    def configurar_tab_prover9(self):
        fuente_codigo = QFont("Courier New", 11)
        layout_principal = QHBoxLayout()
        columna_derecha = QVBoxLayout()
        self.chk_modo_p9 = QCheckBox("")
        self.chk_modo_p9.toggled.connect(lambda checked: self.vista_stack_p9.setCurrentIndex(1 if checked else 0))
        columna_derecha.addWidget(self.chk_modo_p9)
        self.vista_stack_p9 = QStackedWidget()
        
        vista_limpia = QWidget()
        layout_limpio = QVBoxLayout(vista_limpia)
        layout_limpio.setContentsMargins(0, 0, 0, 0)
        self.lbl_premisas_p9 = QLabel("")
        layout_limpio.addWidget(self.lbl_premisas_p9)
        self.premisas_p9 = QTextEdit()
        self.premisas_p9.setFont(fuente_codigo)
        layout_limpio.addWidget(self.premisas_p9)
        self.lbl_conclusion_p9 = QLabel("")
        layout_limpio.addWidget(self.lbl_conclusion_p9)
        self.conclusion_p9 = QTextEdit()
        self.conclusion_p9.setFont(fuente_codigo)
        self.conclusion_p9.setMaximumHeight(100)
        layout_limpio.addWidget(self.conclusion_p9)
        
        vista_libre = QWidget()
        layout_libre = QVBoxLayout(vista_libre)
        layout_libre.setContentsMargins(0, 0, 0, 0)
        self.lbl_libre_p9 = QLabel("")
        layout_libre.addWidget(self.lbl_libre_p9)
        self.entrada_libre_p9 = QTextEdit()
        self.entrada_libre_p9.setFont(fuente_codigo)
        layout_libre.addWidget(self.entrada_libre_p9)
        
        self.vista_stack_p9.addWidget(vista_limpia)
        self.vista_stack_p9.addWidget(vista_libre)
        columna_derecha.addWidget(self.vista_stack_p9)
        
        self.btn_p9 = QPushButton("")
        self.btn_p9.setStyleSheet("font-weight: bold; background-color: #1e3d59; color: white; padding: 10px;")
        self.btn_p9.clicked.connect(self.procesar_prover9)
        columna_derecha.addWidget(self.btn_p9)
        self.lbl_res_p9 = QLabel("")
        columna_derecha.addWidget(self.lbl_res_p9)
        self.salida_p9 = QTextEdit()
        self.salida_p9.setFont(fuente_codigo)
        self.salida_p9.setReadOnly(True)
        columna_derecha.addWidget(self.salida_p9)
        
        # (Final de configurar_tab_prover9)
        self.grupo_ins_p9, self.lbl_ops_p9, self.botones_ops_p9 = self.crear_panel_insercion(self.entrada_libre_p9)
        
        # Ensamblaje de las 3 columnas: Izquierda (Inserción) - Centro (Editor) - Derecha (Opciones)
        layout_principal.addWidget(self.grupo_ins_p9)
        layout_principal.addLayout(columna_derecha)
        
        self.grupo_opciones_p9 = self.crear_panel_opciones_p9()
        layout_principal.addWidget(self.grupo_opciones_p9)
        
        self.tab_prover9.setLayout(layout_principal)

    def configurar_tab_mace4(self):
        fuente_codigo = QFont("Courier New", 11)
        layout_principal = QHBoxLayout()
        columna_derecha = QVBoxLayout()
        self.chk_modo_m4 = QCheckBox("")
        self.chk_modo_m4.toggled.connect(lambda checked: self.vista_stack_m4.setCurrentIndex(1 if checked else 0))
        columna_derecha.addWidget(self.chk_modo_m4)
        self.vista_stack_m4 = QStackedWidget()
        
        vista_limpia = QWidget()
        layout_limpio = QVBoxLayout(vista_limpia)
        layout_limpio.setContentsMargins(0, 0, 0, 0)
        self.lbl_premisas_m4 = QLabel("")
        layout_limpio.addWidget(self.lbl_premisas_m4)
        self.premisas_m4 = QTextEdit()
        self.premisas_m4.setFont(fuente_codigo)
        layout_limpio.addWidget(self.premisas_m4)
        self.lbl_objetivo_m4 = QLabel("")
        layout_limpio.addWidget(self.lbl_objetivo_m4)
        self.conclusion_m4 = QTextEdit()
        self.conclusion_m4.setFont(fuente_codigo)
        self.conclusion_m4.setMaximumHeight(100)
        layout_limpio.addWidget(self.conclusion_m4)
        
        vista_libre = QWidget()
        layout_libre = QVBoxLayout(vista_libre)
        layout_libre.setContentsMargins(0, 0, 0, 0)
        self.lbl_libre_m4 = QLabel("")
        layout_libre.addWidget(self.lbl_libre_m4)
        self.entrada_libre_m4 = QTextEdit()
        self.entrada_libre_m4.setFont(fuente_codigo)
        layout_libre.addWidget(self.entrada_libre_m4)
        
        self.vista_stack_m4.addWidget(vista_limpia)
        self.vista_stack_m4.addWidget(vista_libre)
        columna_derecha.addWidget(self.vista_stack_m4)
        
        self.btn_m4 = QPushButton("")
        self.btn_m4.setStyleSheet("font-weight: bold; background-color: #17b978; color: white; padding: 10px;")
        self.btn_m4.clicked.connect(self.procesar_mace4)
        columna_derecha.addWidget(self.btn_m4)
        self.lbl_res_m4 = QLabel("")
        columna_derecha.addWidget(self.lbl_res_m4)
        self.salida_m4 = QTextEdit()
        self.salida_m4.setFont(fuente_codigo)
        self.salida_m4.setReadOnly(True)
        columna_derecha.addWidget(self.salida_m4)
        
        self.grupo_ins_m4, self.lbl_ops_m4, self.botones_ops_m4 = self.crear_panel_insercion(self.entrada_libre_m4)
        layout_principal.addWidget(self.grupo_ins_m4)
        layout_principal.addLayout(columna_derecha)
        
        # NUEVO: Integrar el panel lateral de Mace4
        self.grupo_opciones_m4 = self.crear_panel_opciones_m4()
        layout_principal.addWidget(self.grupo_opciones_m4)
        
        self.tab_mace4.setLayout(layout_principal)

    def cocinar_entrada_p9(self, caja_premisas, caja_conclusion):
        texto_cocinado = ""
        
        # 1. Parámetros assign directamente desde la interfaz
        texto_cocinado += f"assign(max_weight, {self.spin_max_weight.value()}).\n"
        texto_cocinado += f"assign(pick_given_ratio, {self.spin_pick_ratio.value()}).\n"
        texto_cocinado += f"assign(order, {self.combo_order.currentText()}).\n"
        texto_cocinado += f"assign(eq_defs, {self.combo_eq_defs.currentText()}).\n"
        texto_cocinado += f"assign(max_seconds, {self.spin_max_seconds_p9.value()}).\n"
        
        # 2. Flags booleanos directamente desde los checkboxes
        if self.chk_expand_relational.isChecked():
            texto_cocinado += "set(expand_relational_defs).\n"
        else:
            texto_cocinado += "clear(expand_relational_defs).\n"
            
        if self.chk_restrict_denials.isChecked():
            texto_cocinado += "set(restrict_denials).\n"
        else:
            texto_cocinado += "clear(restrict_denials).\n"
            
        if self.chk_prolog_vars.isChecked():
            texto_cocinado += "set(prolog_style_variables).\n"
        else:
            texto_cocinado += "clear(prolog_style_variables).\n"

        # --- NUEVO: Extraer "All Options" solo si está activado ---
        if hasattr(self, 'grupo_all_options') and self.grupo_all_options.isChecked():
            # Meta Options
            flags_meta = {
                'auto': self.chk_auto, 'auto_setup': self.chk_auto_setup,
                'auto_limits': self.chk_auto_limits, 'auto_denials': self.chk_auto_denials,
                'auto_inference': self.chk_auto_inference, 'auto_process': self.chk_auto_process,
                'auto2': self.chk_auto2, 'raw': self.chk_raw
            }
            for flag, widget in flags_meta.items():
                if widget.isChecked():
                    texto_cocinado += f"set({flag}).\n"
                else:
                    texto_cocinado += f"clear({flag}).\n"
                
        texto_cocinado += "\n"
        
        # 3. Bloque de fórmulas
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
        texto_cocinado = ""

        # 1. Parámetros assign
        texto_cocinado += f"assign(domain_size, {self.spin_domain_size.value()}).\n"
        texto_cocinado += f"assign(start_size, {self.spin_start_size.value()}).\n"
        texto_cocinado += f"assign(end_size, {self.spin_end_size.value()}).\n"
        texto_cocinado += f"assign(increment, {self.spin_increment.value()}).\n"
        texto_cocinado += f"assign(iterate, {self.combo_iterate.currentText()}).\n"
        texto_cocinado += f"assign(max_models, {self.spin_max_models.value()}).\n"
        texto_cocinado += f"assign(max_seconds, {self.spin_max_seconds_m4.value()}).\n"
        texto_cocinado += f"assign(max_seconds_per, {self.spin_max_seconds_per.value()}).\n"
        texto_cocinado += f"assign(max_megs, {self.spin_max_megs.value()}).\n"
        texto_cocinado += f"assign(selection_order, {self.spin_selection_order.value()}).\n"
        texto_cocinado += f"assign(selection_measure, {self.spin_selection_measure.value()}).\n"

        # 2. Flags booleanos
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

        # 3. Fórmulas
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

    def limpiar_y_traducir_error(self, salida_cruda):
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

    def extraer_texto_util(self, caja, ejemplo_plantilla):
        t = caja.toPlainText().strip()
        if t == ejemplo_plantilla.strip():
            return ""
        return t

    # --- NUEVO: Gestión de la tabla del Historial ---
    def agregar_al_historial(self, hora, motor, tag_resultado, snapshot_datos):
        txt = TRADUCCIONES[self.idioma_actual]
        dict_tags = {
            'proved': txt['hist_proved'], 'no_proved': txt['hist_no_proved'],
            'counter': txt['hist_counter'], 'no_counter': txt['hist_no_counter'],
            'timeout': txt['hist_timeout'], 'error': txt['hist_error']
        }
        
        fila = self.tabla_historial.rowCount()
        self.tabla_historial.insertRow(fila)
        
        self.tabla_historial.setItem(fila, 0, QTableWidgetItem(hora))
        self.tabla_historial.setItem(fila, 1, QTableWidgetItem(motor))
        self.tabla_historial.setItem(fila, 2, QTableWidgetItem(dict_tags.get(tag_resultado, tag_resultado)))
        
        # Guardamos el snapshot en la caché indexado por la fila
        self.datos_historial.append(snapshot_datos)

    def recuperar_desde_historial(self, item):
        """Al hacer doble clic en el historial, restaura los editores a ese estado pasado"""
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
            # Forzamos estilos negros
            for c in [self.premisas_p9, self.conclusion_p9, self.entrada_libre_p9]:
                c.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
        else:
            self.chk_modo_m4.setChecked(snap['modo_avanzado'])
            self.premisas_m4.setPlainText(snap['premisas'])
            self.conclusion_m4.setPlainText(snap['conclusion'])
            self.entrada_libre_m4.setPlainText(snap['libre'])
            for c in [self.premisas_m4, self.conclusion_m4, self.entrada_libre_m4]:
                c.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")

    def procesar_prover9(self):
        self.btn_p9.setEnabled(False)
        self.salida_p9.setPlainText(TRADUCCIONES[self.idioma_actual]['msg_procesando_p9'])
        txt = TRADUCCIONES[self.idioma_actual]
        
        # Snapshot para el historial
        snapshot = {
            'pestaña': 0, 'modo_avanzado': self.chk_modo_p9.isChecked(),
            'premisas': self.premisas_p9.toPlainText(), 'conclusion': self.conclusion_p9.toPlainText(),
            'libre': self.entrada_libre_p9.toPlainText()
        }
        
        if self.chk_modo_p9.isChecked():
            texto_final = self.cocinar_entrada_p9(self.premisas_p9, self.conclusion_p9) if (premisas or conclusion) else ""
        else:
            premisas = self.extraer_texto_util(self.premisas_p9, txt['ph_premisas_p9'])
            conclusion = self.extraer_texto_util(self.conclusion_p9, txt['ph_conclusion_p9'])
            texto_final = self.cocinar_entrada(self.premisas_p9, self.conclusion_p9) if (premisas or conclusion) else ""
            
        if not texto_final.strip():
            self.salida_p9.setPlainText("❌ Error: No hay datos de entrada válidos.")
            self.btn_p9.setEnabled(True)
            return

        resultado_crudo, hora = ejecutar_prover9(texto_final, tiempo_limite=self.spin_max_seconds_p9.value())
        resultado_traducido, tag = self.limpiar_y_traducir_error(resultado_crudo)
        
        self.salida_p9.setPlainText(resultado_traducido)
        self.agregar_al_historial(hora, "Prover9", tag, snapshot)
        self.btn_p9.setEnabled(True)

    def procesar_mace4(self):
        self.btn_m4.setEnabled(False)
        self.salida_m4.setPlainText(TRADUCCIONES[self.idioma_actual]['msg_procesando_m4'])
        txt = TRADUCCIONES[self.idioma_actual]
        
        snapshot = {
            'pestaña': 1, 'modo_avanzado': self.chk_modo_m4.isChecked(),
            'premisas': self.premisas_m4.toPlainText(), 'conclusion': self.conclusion_m4.toPlainText(),
            'libre': self.entrada_libre_m4.toPlainText()
        }
        
        if self.chk_modo_m4.isChecked():
            texto_final = self.cocinar_entrada_m4(self.premisas_m4, self.conclusion_m4) if (premisas or conclusion) else ""
        else:
            premisas = self.extraer_texto_util(self.premisas_m4, txt['ph_premisas_m4'])
            conclusion = self.extraer_texto_util(self.conclusion_m4, txt['ph_conclusion_m4'])
            texto_final = self.cocinar_entrada(self.premisas_m4, self.conclusion_m4) if (premisas or conclusion) else ""

        if not texto_final.strip():
            self.salida_m4.setPlainText("❌ Error: No hay datos de entrada válidos.")
            self.btn_m4.setEnabled(True)
            return

        resultado_crudo, hora = ejecutar_mace4(texto_final, tiempo_limite=self.spin_max_seconds_m4.value())
        resultado_traducido, tag = self.limpiar_y_traducir_error(resultado_crudo)
        
        self.salida_m4.setPlainText(resultado_traducido)
        self.agregar_al_historial(hora, "Mace4", tag, snapshot)
        self.btn_m4.setEnabled(True)

    def cargar_ejemplo_tipo(self, slot_menu):
        """Carga problemas específicos calculando si el usuario está en Prover9 o Mace4"""
        txt = TRADUCCIONES[self.idioma_actual]
        pestaña = self.tabs.currentIndex()
        
        if pestaña == 0:
            # Flujo Prover9
            tipo = 'silogismo' if slot_menu == 1 else 'paradoja'
            premisas_ej = txt[f'datos_{tipo}_premisas']
            conclusion_ej = txt[f'datos_{tipo}_conclusion']
            codigo_completo_libre = self.cocinar_entrada_directa(premisas_ej, conclusion_ej)
            
            self.premisas_p9.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            self.conclusion_p9.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            self.entrada_libre_p9.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            self.premisas_p9.setPlainText(premisas_ej)
            self.conclusion_p9.setPlainText(conclusion_ej)
            self.entrada_libre_p9.setPlainText(codigo_completo_libre)
        else:
            # Flujo Mace4
            tipo = 'grupo' if slot_menu == 1 else 'conmut'
            premisas_ej = txt[f'datos_{tipo}_premisas']
            conclusion_ej = txt[f'datos_{tipo}_conclusion']
            codigo_completo_libre = self.cocinar_entrada_directa(premisas_ej, conclusion_ej)
            
            self.premisas_m4.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            self.conclusion_m4.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            self.entrada_libre_m4.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            self.premisas_m4.setPlainText(premisas_ej)
            self.conclusion_m4.setPlainText(conclusion_ej)
            self.entrada_libre_m4.setPlainText(codigo_completo_libre)

    def nuevo_proyecto(self):
        for caja in [self.premisas_p9, self.conclusion_p9, self.entrada_libre_p9, self.premisas_m4, self.conclusion_m4, self.entrada_libre_m4]:
            caja.clear()
        self.salida_p9.clear()
        self.salida_m4.clear()
        self.ruta_archivo_actual = None # Desvinculamos el archivo
        self.actualizar_textos_interfaz()

    # --- MEJORADO: Abrir archivo con vinculación real ---
    def abrir_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir / Open", "", "Inputs (*.in *.p9 *.txt)")
        if ruta:
            with open(ruta, "r", encoding="utf-8") as f: 
                contenido = f.read()
            
            self.ruta_archivo_actual = ruta # Guardamos la referencia persistente
            
            if self.tabs.currentIndex() == 0:
                self.chk_modo_p9.setChecked(True)
                self.entrada_libre_p9.setPlainText(contenido)
                self.entrada_libre_p9.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            else:
                self.chk_modo_m4.setChecked(True)
                self.entrada_libre_m4.setPlainText(contenido)
                self.entrada_libre_m4.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            
            self.actualizar_textos_interfaz()

    # --- MEJORADO: Guardar inteligente (Ctrl+S directo) ---
    def guardar_archivo(self):
        txt = TRADUCCIONES[self.idioma_actual]
        
        # Si NO hay archivo guardado previamente, abrimos el diálogo para elegir ruta (Guardar como)
        if not self.ruta_archivo_actual:
            ruta, _ = QFileDialog.getSaveFileName(self, "Guardar / Save", "", "Inputs (*.in)")
            if not ruta:
                return
            self.ruta_archivo_actual = ruta

        # Si ya hay archivo vinculado, guardamos directamente sobre él silenciosamente
        p = self.tabs.currentIndex()
        idioma_txt = TRADUCCIONES[self.idioma_actual]
        if p == 0:
            texto = self.extraer_texto_util(self.entrada_libre_p9, idioma_txt['ph_libre_p9']) if self.chk_modo_p9.isChecked() else self.cocinar_entrada_p9(self.premisas_p9, self.conclusion_p9)
        else:
            texto = self.extraer_texto_util(self.entrada_libre_m4, idioma_txt['ph_libre_m4']) if self.chk_modo_m4.isChecked() else self.cocinar_entrada_m4(self.premisas_m4, self.conclusion_m4)
        
        try:
            with open(self.ruta_archivo_actual, "w", encoding="utf-8") as f: 
                f.write(texto)
            self.barra_estado.showMessage(f"{txt['status_guardado']}{self.ruta_archivo_actual}", 4000)
            self.actualizar_titulo_ventana()
        except Exception:
            self.barra_estado.showMessage(txt['status_error_guardar'], 4000)

    def exportar_salida(self):
        editor = self.salida_p9 if self.tabs.currentIndex() == 0 else self.salida_m4
        if editor.toPlainText().strip():
            ruta, _ = QFileDialog.getSaveFileName(self, "Exportar / Export", "", "Reports (*.out *.txt)")
            if ruta:
                with open(ruta, "w", encoding="utf-8") as f: f.write(editor.toPlainText())

    def crear_panel_opciones_p9(self):
        # 1. Contenedor principal con scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(310)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: white; }")

        contenido = QWidget()
        contenido.setObjectName("fondo_blanco_p9")
        contenido.setStyleSheet("#fondo_blanco_p9 { background-color: white; }")
        layout_principal = QVBoxLayout(contenido)
        layout_principal.setContentsMargins(5, 0, 5, 0)

        # 2. --- Basic Options ---
        grupo_basico = QGroupBox("Basic Options")
        grupo_basico.setStyleSheet("QGroupBox { border: 1px solid #d0d0d0; border-radius: 4px; margin-top: 10px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        form_basico = QFormLayout()

        self.spin_max_weight = QSpinBox(); self.spin_max_weight.setRange(-1000, 100000); self.spin_max_weight.setValue(100)
        form_basico.addRow("max_weight:", self.spin_max_weight)
        self.spin_pick_ratio = QSpinBox(); self.spin_pick_ratio.setRange(-1, 100); self.spin_pick_ratio.setValue(-1)
        form_basico.addRow("pick_given_ratio:", self.spin_pick_ratio)
        self.combo_order = QComboBox(); self.combo_order.addItems(["lpo", "rpo", "kbo"])
        form_basico.addRow("order:", self.combo_order)
        self.combo_eq_defs = QComboBox(); self.combo_eq_defs.addItems(["unfold", "fold", "pass"])
        form_basico.addRow("eq_defs:", self.combo_eq_defs)
        self.chk_expand_relational = QCheckBox()
        form_basico.addRow("expand_relational_defs:", self.chk_expand_relational)
        self.chk_restrict_denials = QCheckBox()
        form_basico.addRow("restrict_denials:", self.chk_restrict_denials)
        self.spin_max_seconds_p9 = QSpinBox(); self.spin_max_seconds_p9.setRange(1, 3600); self.spin_max_seconds_p9.setValue(60)
        form_basico.addRow("max_seconds:", self.spin_max_seconds_p9)
        self.chk_prolog_vars = QCheckBox()
        form_basico.addRow("prolog_style_variables:", self.chk_prolog_vars)

        btn_reset_basico = QPushButton("Reset These to Defaults")
        btn_reset_basico.clicked.connect(self.reset_opciones_p9)
        form_basico.addRow(btn_reset_basico)

        grupo_basico.setLayout(form_basico)
        layout_principal.addWidget(grupo_basico)

        # 3. --- All Options (Desbloqueable) ---
        self.grupo_all_options = QGroupBox("All Options")
        self.grupo_all_options.setCheckable(True)
        self.grupo_all_options.setChecked(False) # Actúa como el toggle original
        self.grupo_all_options.setStyleSheet("QGroupBox { border: 1px solid #d0d0d0; border-radius: 4px; margin-top: 15px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")

        layout_all = QVBoxLayout()

        # Desplegable de Option Groups
        self.combo_grupos_p9 = QComboBox()
        self.combo_grupos_p9.addItems([
            "Meta Options", "Term Ordering", "Limits", "Search Prep",
            "Goals/Denials", "Select Given", "Inference Rules", "Rewriting",
            "Weighting", "Process Inferred", "Input/Output", "Hints", "Other Options"
        ])
        layout_all.addWidget(self.combo_grupos_p9)

        self.stack_opciones_p9 = QStackedWidget()

        # Página 0: Meta Options
        page_meta = QWidget()
        form_meta = QFormLayout(page_meta)
        form_meta.setContentsMargins(0, 5, 0, 0)

        self.chk_auto = QCheckBox(); self.chk_auto.setChecked(True)
        form_meta.addRow("auto:", self.chk_auto)
        self.chk_auto_setup = QCheckBox(); self.chk_auto_setup.setChecked(True)
        form_meta.addRow("auto_setup:", self.chk_auto_setup)
        self.chk_auto_limits = QCheckBox(); self.chk_auto_limits.setChecked(True)
        form_meta.addRow("auto_limits:", self.chk_auto_limits)
        self.chk_auto_denials = QCheckBox(); self.chk_auto_denials.setChecked(True)
        form_meta.addRow("auto_denials:", self.chk_auto_denials)
        self.chk_auto_inference = QCheckBox(); self.chk_auto_inference.setChecked(True)
        form_meta.addRow("auto_inference:", self.chk_auto_inference)
        self.chk_auto_process = QCheckBox(); self.chk_auto_process.setChecked(True)
        form_meta.addRow("auto_process:", self.chk_auto_process)
        self.chk_auto2 = QCheckBox()
        form_meta.addRow("auto2:", self.chk_auto2)
        self.chk_raw = QCheckBox()
        form_meta.addRow("raw:", self.chk_raw)

        btn_reset_meta = QPushButton("Reset These to Defaults")
        btn_reset_meta.clicked.connect(self.reset_meta_options)
        form_meta.addRow(btn_reset_meta)

        self.stack_opciones_p9.addWidget(page_meta)

        # Placeholders para los otros 12 grupos de opciones
        for _ in range(12):
            self.stack_opciones_p9.addWidget(QWidget())

        layout_all.addWidget(self.stack_opciones_p9)
        self.grupo_all_options.setLayout(layout_all)

        # Conectar el combobox con el stack de páginas
        self.combo_grupos_p9.currentIndexChanged.connect(self.stack_opciones_p9.setCurrentIndex)

        layout_principal.addWidget(self.grupo_all_options)
        layout_principal.addStretch() # Empuja el contenido hacia arriba

        scroll.setWidget(contenido)
        return scroll

    def reset_opciones_p9(self):
        self.spin_max_weight.setValue(100)
        self.spin_pick_ratio.setValue(-1)
        self.combo_order.setCurrentText("lpo")
        self.combo_eq_defs.setCurrentText("unfold")
        self.chk_expand_relational.setChecked(False)
        self.chk_restrict_denials.setChecked(False)
        self.spin_max_seconds_p9.setValue(60)
        self.chk_prolog_vars.setChecked(False)

    def reset_meta_options(self):
        self.chk_auto.setChecked(True)
        self.chk_auto_setup.setChecked(True)
        self.chk_auto_limits.setChecked(True)
        self.chk_auto_denials.setChecked(True)
        self.chk_auto_inference.setChecked(True)
        self.chk_auto_process.setChecked(True)
        self.chk_auto2.setChecked(False)
        self.chk_raw.setChecked(False)

    def crear_panel_opciones_m4(self):
        # Contenedor principal con barra de desplazamiento
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(300)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: white; }") # <--- AÑADIR ESTO

        contenido = QWidget()
        contenido.setObjectName("fondo_blanco_m4") # <--- AÑADIR ESTO
        contenido.setStyleSheet("#fondo_blanco_m4 { background-color: white; }") # <--- AÑADIR ESTO
        layout_principal = QVBoxLayout(contenido)
        layout_principal.setContentsMargins(5, 0, 5, 0)

        # --- Basic Options ---
        grupo_basico = QGroupBox("Basic Options")
        form_basico = QFormLayout()

        self.spin_domain_size = QSpinBox(); self.spin_domain_size.setRange(0, 1000); self.spin_domain_size.setValue(0)
        form_basico.addRow("domain_size:", self.spin_domain_size)
        self.spin_start_size = QSpinBox(); self.spin_start_size.setRange(1, 1000); self.spin_start_size.setValue(2)
        form_basico.addRow("start_size:", self.spin_start_size)
        self.spin_end_size = QSpinBox(); self.spin_end_size.setRange(-1, 1000); self.spin_end_size.setValue(-1)
        form_basico.addRow("end_size:", self.spin_end_size)
        self.spin_increment = QSpinBox(); self.spin_increment.setRange(1, 100); self.spin_increment.setValue(1)
        form_basico.addRow("increment:", self.spin_increment)

        self.combo_iterate = QComboBox()
        self.combo_iterate.addItems(["all", "evens", "odds", "primes", "nonprimes"]) 
        self.combo_iterate.setCurrentText("all")
        form_basico.addRow("iterate:", self.combo_iterate)

        self.spin_max_models = QSpinBox(); self.spin_max_models.setRange(-1, 10000); self.spin_max_models.setValue(1)
        form_basico.addRow("max_models:", self.spin_max_models)
        self.spin_max_seconds_m4 = QSpinBox(); self.spin_max_seconds_m4.setRange(-1, 3600); self.spin_max_seconds_m4.setValue(60)
        form_basico.addRow("max_seconds:", self.spin_max_seconds_m4)
        self.spin_max_seconds_per = QSpinBox(); self.spin_max_seconds_per.setRange(-1, 3600); self.spin_max_seconds_per.setValue(-1)
        form_basico.addRow("max_seconds_per:", self.spin_max_seconds_per)

        self.chk_prolog_vars_m4 = QCheckBox()
        form_basico.addRow("prolog_style_variables:", self.chk_prolog_vars_m4)

        grupo_basico.setLayout(form_basico)
        layout_principal.addWidget(grupo_basico)

        # --- Other Options ---
        grupo_otros = QGroupBox("Other Options")
        form_otros = QFormLayout()

        self.chk_integer_ring = QCheckBox()
        form_otros.addRow("integer_ring:", self.chk_integer_ring)
        self.chk_skolems_last = QCheckBox()
        form_otros.addRow("skolems_last:", self.chk_skolems_last)
        self.spin_max_megs = QSpinBox(); self.spin_max_megs.setRange(1, 10000); self.spin_max_megs.setValue(200)
        form_otros.addRow("max_megs:", self.spin_max_megs)
        self.chk_print_models = QCheckBox(); self.chk_print_models.setChecked(True)
        form_otros.addRow("print_models:", self.chk_print_models)

        grupo_otros.setLayout(form_otros)
        layout_principal.addWidget(grupo_otros)

        # --- Experimental Options ---
        grupo_exp = QGroupBox("Experimental Options")
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

        grupo_exp.setLayout(form_exp)
        layout_principal.addWidget(grupo_exp)

        # Botón Reset
        btn_reset = QPushButton("Reset These to Defaults")
        btn_reset.clicked.connect(self.reset_opciones_m4)
        layout_principal.addWidget(btn_reset)

        scroll.setWidget(contenido)
        return scroll

    def reset_opciones_m4(self):
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())