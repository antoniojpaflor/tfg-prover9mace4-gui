import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QTabWidget, QFileDialog, QGroupBox, QCheckBox, QStackedWidget)
from PyQt6.QtGui import QFont, QAction, QColor
from PyQt6.QtCore import QEvent

from launcher import ejecutar_prover9, ejecutar_mace4
# Importamos el diccionario de idiomas
from idiomas import TRADUCCIONES

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.idioma_actual = 'es_ES'  # Idioma por defecto
        self.init_ui()
        
    def init_ui(self):
        self.setGeometry(100, 100, 1100, 800)
        
        # 1. Contenedor de Pestañas
        self.tabs = QTabWidget()
        self.tab_prover9 = QWidget()
        self.tab_mace4 = QWidget()
        self.tabs.addTab(self.tab_prover9, "")
        self.tabs.addTab(self.tab_mace4, "")
        
        # 2. Configuración de contenidos
        self.configurar_tab_prover9()
        self.configurar_tab_mace4()
        self.setCentralWidget(self.tabs)
        
        # 3. Instalamos el filtro de eventos para simular los placeholders multilínea
        self.premisas_p9.installEventFilter(self)
        self.conclusion_p9.installEventFilter(self)
        self.entrada_libre_p9.installEventFilter(self)
        self.premisas_m4.installEventFilter(self)
        self.conclusion_m4.installEventFilter(self)
        self.entrada_libre_m4.installEventFilter(self)
        
        # 4. Construimos los menús
        self.crear_barra_menus()
        
        # 5. Traducimos la interfaz por primera vez para poblar los textos
        self.actualizar_textos_interfaz()

    def eventFilter(self, objeto, evento):
        """Manejador inteligente de foco para borrar/restaurar los ejemplos multilínea"""
        txt = TRADUCCIONES[self.idioma_actual]
        
        # Mapeo de qué texto de ejemplo corresponde a qué caja
        mapeo_ejemplos = {
            self.premisas_p9: txt['ph_premisas_p9'],
            self.conclusion_p9: txt['ph_conclusion_p9'],
            self.entrada_libre_p9: txt['ph_libre_p9'],
            self.premisas_m4: txt['ph_premisas_m4'],
            self.conclusion_m4: txt['ph_conclusion_m4'],
            self.entrada_libre_m4: txt['ph_libre_m4']
        }
        
        if objeto in mapeo_ejemplos:
            # EVENTO: El usuario hace clic en el cuadro para escribir
            if evento.type() == QEvent.Type.FocusIn:
                if objeto.toPlainText().strip() == mapeo_ejemplos[objeto].strip():
                    objeto.clear()
                    objeto.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            
            # EVENTO: El usuario sale del cuadro dejándolo vacío
            elif evento.type() == QEvent.Type.FocusOut:
                if not objeto.toPlainText().strip():
                    objeto.setPlainText(mapeo_ejemplos[objeto])
                    objeto.setStyleSheet("color: gray; font-family: 'Courier New'; font-size: 11pt;")
                    
        return super().eventFilter(objeto, evento)

    def crear_barra_menus(self):
        """Construye y reconstruye la barra de menús dinámicamente"""
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
        
        # === NUEVO: Menú Ejemplos ===
        self.menu_ejemplos = barra_menus.addMenu("")
        
        self.accion_ej1 = QAction("", self)
        self.accion_ej1.triggered.connect(lambda: self.cargar_ejemplo_tipo('silogismo'))
        
        self.accion_ej2 = QAction("", self)
        self.accion_ej2.triggered.connect(lambda: self.cargar_ejemplo_tipo('paradoja'))
        
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
        """Puebla todas las etiquetas, textos, botones y placeholders simulados"""
        txt = TRADUCCIONES[self.idioma_actual]
        
        self.setWindowTitle(txt['titulo'])
        self.tabs.setTabText(0, txt['tab_p9'])
        self.tabs.setTabText(1, txt['tab_m4'])
        
        self.menu_archivo.setTitle(txt['menu_archivo'])
        self.accion_nuevo.setText(txt['accion_nuevo'])
        self.accion_abrir.setText(txt['accion_abrir'])
        self.accion_guardar.setText(txt['accion_guardar'])
        self.accion_exportar.setText(txt['accion_exportar'])
        self.accion_salir.setText(txt['accion_salir'])
        self.menu_idioma.setTitle(txt['menu_idioma'])
        self.menu_ejemplos.setTitle(txt['menu_ejemplos'])
        self.accion_ej1.setText(txt['ej_silogismo'])
        self.accion_ej2.setText(txt['ej_paradoja'])
        
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
        
        # === VINCULACIÓN DE TEXTOS SIMULADOS (Gris por defecto si no hay entrada de usuario) ===
        cajas = [
            (self.premisas_p9, txt['ph_premisas_p9']),
            (self.conclusion_p9, txt['ph_conclusion_p9']),
            (self.entrada_libre_p9, txt['ph_libre_p9']),
            (self.premisas_m4, txt['ph_premisas_m4']),
            (self.conclusion_m4, txt['ph_conclusion_m4']),
            (self.entrada_libre_m4, txt['ph_libre_m4'])
        ]
        
        for caja, texto_ejemplo in cajas:
            # Solo sobreescribimos si está vacía o si ya contenía un ejemplo anterior de otro idioma
            texto_actual = caja.toPlainText().strip()
            if not texto_actual or texto_actual in [v.strip() for v in TRADUCCIONES['es_ES'].values()] or texto_actual in [v.strip() for v in TRADUCCIONES['en_US'].values()]:
                caja.setPlainText(texto_ejemplo)
                caja.setStyleSheet("color: gray; font-family: 'Courier New'; font-size: 11pt;")

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
            # Si tiene el texto en gris de muestra, lo limpiamos antes de meter el símbolo
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
        
        self.grupo_ins_p9, self.lbl_ops_p9, self.botones_ops_p9 = self.crear_panel_insercion(self.entrada_libre_p9)
        layout_principal.addWidget(self.grupo_ins_p9)
        layout_principal.addLayout(columna_derecha)
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
        self.tab_mace4.setLayout(layout_principal)

    def cocinar_entrada(self, caja_premisas, caja_conclusion):
        lineas_premisas = caja_premisas.toPlainText().split('\n')
        conclusion = caja_conclusion.toPlainText().strip()
        
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
    
    def cocinar_entrada_directa(self, texto_premisas, texto_conclusion):
        """Variante que genera la sintaxis de Prover9/Mace4 directamente desde strings de texto"""
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
            return f"❌ ERROR:\n{salida_cruda}"

        patrones_error = ["fatal_error", "LABEL: syntax error", "syn_err", "cloffset", "appears more than once", "error"]
        if any(patron in texto for patron in patrones_error):
            if es_en:
                return f"❌ DETECTED SYNTAX ERROR\n---------------------------------\nReview operators and parenthesis.\n\n=== ENGINE LOG ===\n{salida_cruda}"
            return f"❌ ERROR DE SINTAXIS DETECTADO\n---------------------------------\nRevisa conectivas y paréntesis.\n\n=== DETALLE TÉCNICO ===\n{salida_cruda}"

        if pestaña_activa == 0:
            if "THEOREM PROVED" in texto:
                prueba_limpia = ""
                for linea in texto.split('\n'):
                    if "=== PROOF ===" in linea or "SUBPROOF" in linea or prueba_limpia:
                        prueba_limpia += linea + "\n"
                    if "end of proof" in linea: break
                
                if es_en:
                    return f"✅ THEOREM PROVED SUCCESSFULLY!\n---------------------------------\n=== PROOF STEPS ===\n{prueba_limpia.strip()}\n\n=== FULL LOG ===\n{salida_cruda}"
                return f"✅ ¡TEOREMA DEMOSTRADO CON ÉXITO!\n---------------------------------\n=== PASOS DEDUCTIVOS ===\n{prueba_limpia.strip()}\n\n=== LOG COMPLETO ===\n{salida_cruda}"
            else:
                if es_en:
                    return f"⚠️ THEOREM COULD NOT BE PROVED\n---------------------------------\n=== ENGINE LOG ===\n{salida_cruda}"
                return f"⚠️ EL TEOREMA NO SE PUDO DEMOSTRAR\n---------------------------------\n=== DETALLE TÉCNICO ===\n{salida_cruda}"
        else:
            if "model(s) found" in texto or "Exiting with 1 model" in texto or "interpretation" in texto:
                modelo_limpio = ""
                for linea in texto.split('\n'):
                    if "interpretation(" in linea or modelo_limpio:
                        modelo_limpio += linea + "\n"
                    if "end_of_interpretation" in linea: break
                
                if es_en:
                    return f"🔮 COUNTEREXAMPLE FOUND (THEOREM IS FALSE)\n---------------------------------\n=== MATRIX STRUCT ===\n{modelo_limpio.strip()}\n\n=== FULL LOG ===\n{salida_cruda}"
                return f"🔮 CONTRAEJEMPLO ENCONTRADO (EL TEOREMA ES FALSO)\n---------------------------------\n=== MATRIZ SEMÁNTICA ===\n{modelo_limpio.strip()}\n\n=== LOG COMPLETO ===\n{salida_cruda}"
            else:
                if es_en:
                    return f"ℹ️ NO COUNTEREXAMPLES FOUND\n---------------------------------\n=== ENGINE LOG ===\n{salida_cruda}"
                return f"ℹ️ MACE4 NO ENCONTRÓ CONTRAEJEMPLOS\n---------------------------------\n=== DETALLE TÉCNICO ===\n{salida_cruda}"

    def extraer_texto_util(self, caja, ejemplo_plantilla):
        """Si la caja tiene el texto de ejemplo simulado, devuelve vacío, si no, el texto real"""
        t = caja.toPlainText().strip()
        if t == ejemplo_plantilla.strip():
            return ""
        return t

    def procesar_prover9(self):
        self.btn_p9.setEnabled(False)
        self.salida_p9.setPlainText(TRADUCCIONES[self.idioma_actual]['msg_procesando_p9'])
        
        txt = TRADUCCIONES[self.idioma_actual]
        if self.chk_modo_p9.isChecked():
            texto_final = self.extraer_texto_util(self.entrada_libre_p9, txt['ph_libre_p9'])
        else:
            premisas = self.extraer_texto_util(self.premisas_p9, txt['ph_premisas_p9'])
            conclusion = self.extraer_texto_util(self.conclusion_p9, txt['ph_conclusion_p9'])
            texto_final = self.cocinar_entrada(self.premisas_p9, self.conclusion_p9) if (premisas or conclusion) else ""
            
        if not texto_final.strip():
            self.salida_p9.setPlainText("❌ Error: No hay datos de entrada válidos para ejecutar Prover9.")
            self.btn_p9.setEnabled(True)
            return

        self.salida_p9.setPlainText(self.limpiar_y_traducir_error(ejecutar_prover9(texto_final)))
        self.btn_p9.setEnabled(True)

    def procesar_mace4(self):
        self.btn_m4.setEnabled(False)
        self.salida_m4.setPlainText(TRADUCCIONES[self.idioma_actual]['msg_procesando_m4'])
        
        txt = TRADUCCIONES[self.idioma_actual]
        if self.chk_modo_m4.isChecked():
            texto_final = self.extraer_texto_util(self.entrada_libre_m4, txt['ph_libre_m4'])
        else:
            premisas = self.extraer_texto_util(self.premisas_m4, txt['ph_premisas_m4'])
            conclusion = self.extraer_texto_util(self.conclusion_m4, txt['ph_conclusion_m4'])
            texto_final = self.cocinar_entrada(self.premisas_m4, self.conclusion_m4) if (premisas or conclusion) else ""

        if not texto_final.strip():
            self.salida_m4.setPlainText("❌ Error: No hay datos de entrada válidos para ejecutar Mace4.")
            self.btn_m4.setEnabled(True)
            return

        self.salida_m4.setPlainText(self.limpiar_y_traducir_error(ejecutar_mace4(texto_final)))
        self.btn_m4.setEnabled(True)

    def nuevo_proyecto(self):
        # Al limpiar, forzamos a que el eventFilter vuelva a inyectar el gris
        for caja in [self.premisas_p9, self.conclusion_p9, self.entrada_libre_p9, self.premisas_m4, self.conclusion_m4, self.entrada_libre_m4]:
            caja.clear()
        self.salida_p9.clear()
        self.salida_m4.clear()
        self.actualizar_textos_interfaz()

    def abrir_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir / Open", "", "Inputs (*.in *.p9 *.txt)")
        if ruta:
            with open(ruta, "r", encoding="utf-8") as f: contenido = f.read()
            if self.tabs.currentIndex() == 0:
                self.chk_modo_p9.setChecked(True)
                self.entrada_libre_p9.setPlainText(contenido)
                self.entrada_libre_p9.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            else:
                self.chk_modo_m4.setChecked(True)
                self.entrada_libre_m4.setPlainText(contenido)
                self.entrada_libre_m4.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")

    def guardar_archivo(self):
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar / Save", "", "Inputs (*.in)")
        if ruta:
            p = self.tabs.currentIndex()
            txt = TRADUCCIONES[self.idioma_actual]
            if p == 0:
                texto = self.extraer_texto_util(self.entrada_libre_p9, txt['ph_libre_p9']) if self.chk_modo_p9.isChecked() else self.cocinar_entrada(self.premisas_p9, self.conclusion_p9)
            else:
                texto = self.extraer_texto_util(self.entrada_libre_m4, txt['ph_libre_m4']) if self.chk_modo_m4.isChecked() else self.cocinar_entrada(self.premisas_m4, self.conclusion_m4)
            with open(ruta, "w", encoding="utf-8") as f: f.write(texto)

    def exportar_salida(self):
        editor = self.salida_p9 if self.tabs.currentIndex() == 0 else self.salida_m4
        if editor.toPlainText().strip():
            ruta, _ = QFileDialog.getSaveFileName(self, "Exportar / Export", "", "Reports (*.out *.txt)")
            if ruta:
                with open(ruta, "w", encoding="utf-8") as f: f.write(editor.toPlainText())

    def cargar_ejemplo_tipo(self, tipo):
        """Carga un problema lógico predefinido en la pestaña activa rellenando tanto el modo simple como el avanzado"""
        txt = TRADUCCIONES[self.idioma_actual]
        pestaña = self.tabs.currentIndex()
        
        # 1. Recuperamos los datos limpios del diccionario de idiomas
        premisas_ej = txt[f'datos_{tipo}_premisas']
        conclusion_ej = txt[f'datos_{tipo}_conclusion']
        
        # 2. "Cocinamos" la sintaxis nativa completa para el modo libre usando la función que ya tenemos
        # Pasamos temporalmente textos limpios a un objeto simulado para generar la estructura completa
        codigo_completo_libre = self.cocinar_entrada_directa(premisas_ej, conclusion_ej)
        
        if pestaña == 0: # --- GESTIÓN EN PESTAÑA PROVER9 ---
            # Forzamos estilo negro para quitar el gris de placeholder simulado en todas las cajas de Prover9
            self.premisas_p9.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            self.conclusion_p9.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            self.entrada_libre_p9.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            
            # Volcamos los datos en ambos mundos a la vez
            self.premisas_p9.setPlainText(premisas_ej)
            self.conclusion_p9.setPlainText(conclusion_ej)
            self.entrada_libre_p9.setPlainText(codigo_completo_libre)
            
        else: # --- GESTIÓN EN PESTAÑA MACE4 ---
            # Forzamos estilo negro para quitar el gris en todas las cajas de Mace4
            self.premisas_m4.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            self.conclusion_m4.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            self.entrada_libre_m4.setStyleSheet("color: black; font-family: 'Courier New'; font-size: 11pt;")
            
            # Volcamos los datos en ambos mundos a la vez
            self.premisas_m4.setPlainText(premisas_ej)
            self.conclusion_m4.setPlainText(conclusion_ej)
            self.entrada_libre_m4.setPlainText(codigo_completo_libre)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())