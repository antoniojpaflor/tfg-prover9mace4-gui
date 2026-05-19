import sys
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QTabWidget, QFileDialog, QGroupBox, QCheckBox, QStackedWidget)
from PyQt6.QtGui import QFont, QAction

# Importamos las funciones del launcher multiplataforma
from launcher import ejecutar_prover9, ejecutar_mace4

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.archivo_actual_p9 = None
        self.archivo_actual_m4 = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Prover9-Mace4 GUI - TFG Antonio J. Parras")
        self.setGeometry(100, 100, 1100, 800)
        
        self.crear_barra_menus()
        
        self.tabs = QTabWidget()
        self.tab_prover9 = QWidget()
        self.tab_mace4 = QWidget()
        
        self.tabs.addTab(self.tab_prover9, "Demostrador Prover9")
        self.tabs.addTab(self.tab_mace4, "Buscador de Modelos Mace4")
        
        self.configurar_tab_prover9()
        self.configurar_tab_mace4()
        
        self.setCentralWidget(self.tabs)

    def crear_barra_menus(self):
        barra_menus = self.menuBar()
        menu_archivo = barra_menus.addMenu("&Archivo")
        
        accion_nuevo = QAction("Nuevo Proyecto", self)
        accion_nuevo.triggered.connect(self.nuevo_proyecto)
        
        accion_abrir = QAction("&Abrir Archivo (.in)...", self)
        accion_abrir.setShortcut("Ctrl+O")
        accion_abrir.triggered.connect(self.abrir_archivo)
        
        accion_guardar = QAction("&Guardar", self)
        accion_guardar.setShortcut("Ctrl+S")
        accion_guardar.triggered.connect(self.guardar_archivo)
        
        accion_exportar = QAction("&Exportar Salida (.out)...", self)
        accion_exportar.triggered.connect(self.exportar_salida)
        
        accion_salir = QAction("&Salir", self)
        accion_salir.triggered.connect(self.close)
        
        menu_archivo.addAction(accion_nuevo)
        menu_archivo.addSeparator()
        menu_archivo.addAction(accion_abrir)
        menu_archivo.addAction(accion_guardar)
        menu_archivo.addSeparator()
        menu_archivo.addAction(accion_exportar)
        menu_archivo.addSeparator()
        menu_archivo.addAction(accion_salir)

    def crear_panel_insercion(self, editor_destino):
        grupo = QGroupBox("Inserción Rápida")
        layout_grupo = QVBoxLayout()
        estilo_btn = "padding: 5px; font-weight: bold; background-color: #f0f0f0;"
        
        layout_grupo.addWidget(QLabel("Operadores lógicos:"))
        operadores = [
            ("Negación ( - )", " - "),
            ("Conjunción ( & )", " & "),
            ("Disyunción ( | )", " | "),
            ("Implicación ( -> )", " -> "),
            ("Equivalencia ( <-> )", " <-> ")
        ]
        
        for nombre, simbolo in operadores:
            btn = QPushButton(nombre)
            btn.setStyleSheet(estilo_btn)
            btn.clicked.connect(lambda checked, s=simbolo: editor_destino.insertPlainText(s))
            layout_grupo.addWidget(btn)
            
        layout_grupo.addStretch()
        grupo.setLayout(layout_grupo)
        grupo.setFixedWidth(180)
        return grupo

    def configurar_tab_prover9(self):
        fuente_codigo = QFont("Courier New", 11)
        layout_principal = QHBoxLayout()
        columna_derecha = QVBoxLayout()
        
        # --- CONTROL DE MODO VISTA ---
        self.chk_modo_p9 = QCheckBox("Modo Avanzado (Editor de código libre)")
        self.chk_modo_p9.toggled.connect(lambda checked: self.vista_stack_p9.setCurrentIndex(1 if checked else 0))
        columna_derecha.addWidget(self.chk_modo_p9)
        
        # Stack para alternar entre el formulario limpio y el editor libre
        self.vista_stack_p9 = QStackedWidget()
        
        # VISTA A: Formulario Limpio (Por defecto)
        vista_limpia = QWidget()
        layout_limpio = QVBoxLayout(vista_limpia)
        layout_limpio.setContentsMargins(0, 0, 0, 0)
        
        layout_limpio.addWidget(QLabel("Premisas / Hipótesis (una por línea, sin 'formulas(sos).' ni puntos):"))
        self.premisas_p9 = QTextEdit()
        self.premisas_p9.setFont(fuente_codigo)
        self.premisas_p9.setPlainText("p -> q\np")
        layout_limpio.addWidget(self.premisas_p9)
        
        layout_limpio.addWidget(QLabel("Teorema / Conclusión a demostrar (sin 'formulas(goals).' ni puntos):"))
        self.conclusion_p9 = QTextEdit()
        self.conclusion_p9.setFont(fuente_codigo)
        self.conclusion_p9.setPlainText("q")
        self.conclusion_p9.setMaximumHeight(100)
        layout_limpio.addWidget(self.conclusion_p9)
        
        # VISTA B: Editor Libre (Como estaba antes)
        vista_libre = QWidget()
        layout_libre = QVBoxLayout(vista_libre)
        layout_libre.setContentsMargins(0, 0, 0, 0)
        layout_libre.addWidget(QLabel("Editor libre Prover9 (Código completo):"))
        self.entrada_libre_p9 = QTextEdit()
        self.entrada_libre_p9.setFont(fuente_codigo)
        self.entrada_libre_p9.setPlainText("formulas(sos).\n  p -> q.\n  p.\nend_of_list.\n\nformulas(goals).\n  q.\nend_of_list.")
        layout_libre.addWidget(self.entrada_libre_p9)
        
        # Añadimos ambas vistas al Stack
        self.vista_stack_p9.addWidget(vista_limpia) # Índice 0
        self.vista_stack_p9.addWidget(vista_libre)  # Índice 1
        columna_derecha.addWidget(self.vista_stack_p9)
        
        # Botón de ejecución
        self.btn_p9 = QPushButton("Verificar Deducción (Prover9)")
        self.btn_p9.setStyleSheet("font-weight: bold; background-color: #1e3d59; color: white; padding: 10px;")
        self.btn_p9.clicked.connect(self.procesar_prover9)
        columna_derecha.addWidget(self.btn_p9)
        
        # Salida
        columna_derecha.addWidget(QLabel("Resultado del Análisis:"))
        self.salida_p9 = QTextEdit()
        self.salida_p9.setFont(fuente_codigo)
        self.salida_p9.setReadOnly(True)
        columna_derecha.addWidget(self.salida_p9)
        
        # Panel de inserción rápida conectado al editor libre
        layout_principal.addWidget(self.crear_panel_insercion(self.entrada_libre_p9))
        layout_principal.addLayout(columna_derecha)
        self.tab_prover9.setLayout(layout_principal)

    def configurar_tab_mace4(self):
        fuente_codigo = QFont("Courier New", 11)
        layout_principal = QHBoxLayout()
        columna_derecha = QVBoxLayout()
        
        # --- CONTROL DE MODO VISTA ---
        self.chk_modo_m4 = QCheckBox("Modo Avanzado (Editor de código libre)")
        self.chk_modo_m4.toggled.connect(lambda checked: self.vista_stack_m4.setCurrentIndex(1 if checked else 0))
        columna_derecha.addWidget(self.chk_modo_m4)
        
        self.vista_stack_m4 = QStackedWidget()
        
        # VISTA A: Formulario Limpio
        vista_limpia = QWidget()
        layout_limpio = QVBoxLayout(vista_limpia)
        layout_limpio.setContentsMargins(0, 0, 0, 0)
        
        layout_limpio.addWidget(QLabel("Premisas / Hipótesis (una por línea, sin código):"))
        self.premisas_m4 = QTextEdit()
        self.premisas_m4.setFont(fuente_codigo)
        self.premisas_m4.setPlainText("p -> q")
        layout_limpio.addWidget(self.premisas_m4)
        
        layout_limpio.addWidget(QLabel("Objetivo que sospechas falso (sin código):"))
        self.conclusion_m4 = QTextEdit()
        self.conclusion_m4.setFont(fuente_codigo)
        self.conclusion_m4.setPlainText("q")
        self.conclusion_m4.setMaximumHeight(100)
        layout_limpio.addWidget(self.conclusion_m4)
        
        # VISTA B: Editor Libre
        vista_libre = QWidget()
        layout_libre = QVBoxLayout(vista_libre)
        layout_libre.setContentsMargins(0, 0, 0, 0)
        layout_libre.addWidget(QLabel("Editor libre Mace4 (Código completo):"))
        self.entrada_libre_m4 = QTextEdit()
        self.entrada_libre_m4.setFont(fuente_codigo)
        self.entrada_libre_m4.setPlainText("formulas(sos).\n  p -> q.\nend_of_list.\n\nformulas(goals).\n  q.\nend_of_list.")
        layout_libre.addWidget(self.entrada_libre_m4)
        
        self.vista_stack_m4.addWidget(vista_limpia)
        self.vista_stack_m4.addWidget(vista_libre)
        columna_derecha.addWidget(self.vista_stack_m4)
        
        # Botón de ejecución
        self.btn_m4 = QPushButton("Buscar Contraejemplo (Mace4)")
        self.btn_m4.setStyleSheet("font-weight: bold; background-color: #17b978; color: white; padding: 10px;")
        self.btn_m4.clicked.connect(self.procesar_mace4)
        columna_derecha.addWidget(self.btn_m4)
        
        columna_derecha.addWidget(QLabel("Resultado del Análisis:"))
        self.salida_m4 = QTextEdit()
        self.salida_m4.setFont(fuente_codigo)
        self.salida_m4.setReadOnly(True)
        columna_derecha.addWidget(self.salida_m4)
        
        layout_principal.addWidget(self.crear_panel_insercion(self.entrada_libre_m4))
        layout_principal.addLayout(columna_derecha)
        self.tab_mace4.setLayout(layout_principal)

    # --- PARSER / COCINADOR DE SINTAXIS (Evita errores al usuario) ---

    def cocinar_entrada(self, caja_premisas, caja_conclusion):
        """Toma las líneas limpias del usuario y fabrica el archivo sintáctico de Prover9"""
        lineas_premisas = caja_premisas.toPlainText().split('\n')
        conclusion = caja_conclusion.toPlainText().strip()
        
        texto_cocinado = "formulas(sos).\n"
        for linea in lineas_premisas:
            linea_limpia = linea.strip()
            if linea_limpia:
                # Si el usuario no puso el punto final obligatorio de Prover9, se lo ponemos nosotros
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
        """
        Analiza minuciosamente la salida de los binarios. Si detecta fallos sintácticos
        o que el motor no ha podido procesar el problema, intercepta el texto y lo
        traduce a un formato amigable para el usuario.
        """
        # Limpiamos espacios por seguridad
        texto = salida_cruda.strip()
        
        # Si la salida viene completamente vacía o es un error crítico del launcher
        if not texto or "Error crítico" in texto or "Error en la ejecución" in texto:
            return f"❌ ERROR DE ENTORNO:\n--------------------------------------------------\n{salida_cruda}"

        # Diccionario de palabras clave que usa Prover9/Mace4 cuando algo va mal
        patrones_error = [
            "fatal_error", 
            "LABEL: syntax error", 
            "syn_err", 
            "cloffset",          # Indica que el parser de cláusulas falló en una posición
            "appears more than once", 
            "error"
        ]
        
        # Comprobamos si el texto contiene alguna de las marcas de error de los binarios
        hay_error_sintactico = any(patron in texto for patron in patrones_error)
        
        # Caso especial para Prover9 en Modo Simple: si no hay error sintáctico pero tampoco se ha probado el teorema
        # significa que las premisas no son suficientes o el motor se ha quedado a medias.
        pestaña_activa = self.tabs.currentIndex()
        es_modo_simple = (not self.chk_modo_p9.isChecked()) if pestaña_activa == 0 else (not self.chk_modo_m4.isChecked())

        if hay_error_sintactico:
            return (
                "❌ ERROR DE SINTAXIS DETECTADO\n"
                "--------------------------------------------------\n"
                "El motor lógico no ha podido interpretar tus fórmulas.\n\n"
                "Por favor, revisa lo siguiente:\n"
                " 1. ¿Has puesto operadores entre todas las variables? (Ej: usa 'p & q' en lugar de 'p q').\n"
                " 2. ¿Hay algún paréntesis abierto que no se haya cerrado?\n"
                " 3. ¿Estás usando caracteres extraños? Recuerda usar: - (negación), & (conjunción), | (disyunción), -> (implicación).\n\n"
                "=== DETALLE TÉCNICO DEL MOTOR ===\n"
                f"{salida_cruda}"
            )
            
        elif pestaña_activa == 0 and es_modo_simple and "THEOREM PROVED" not in texto:
            return (
                "⚠️ EL TEOREMA NO SE PUDO DEMOSTRAR\n"
                "--------------------------------------------------\n"
                "Prover9 ha analizado las premisas pero NO ha encontrado una forma lógica de demostrar "
                "la conclusión propuesta.\n\n"
                "Sugerencias:\n"
                " - Revisa si te falta añadir alguna hipótesis o premisa intermedia.\n"
                " - Comprueba en la pestaña 'Mace4' si existe un contraejemplo que desmonte este teorema.\n\n"
                "=== DETALLE TÉCNICO DEL MOTOR ===\n"
                f"{salida_cruda}"
            )

        # Si todo ha ido bien (ha demostrado el teorema o Mace4 ha hallado el modelo), devolvemos la salida limpia
        return salida_cruda
        """Analiza la salida de los binarios y si hay errores los traduce a lenguaje humano"""
        if "fatal_error" in salida_cruda or "LABEL: syntax error" in salida_cruda or "syn_err" in salida_cruda:
            # Buscamos patrones de errores comunes de Prover9
            return (
                "❌ ERROR DE SINTAXIS DETECTADO\n"
                "--------------------------------------------------\n"
                "El motor lógico no ha podido entender las fórmulas.\n\n"
                "Causas comunes:\n"
                " - Has olvidado poner un operador entre dos variables (ej: 'p q' en vez de 'p & q').\n"
                " - Hay un paréntesis abierto que nunca se cerró.\n"
                " - Estás usando un carácter no permitido en Prover9.\n\n"
                "Detalle técnico del motor:\n"
                f"{salida_cruda}"
            )
        return salida_cruda

    # --- EJECUCIÓN DE BOTONES ---

    def procesar_prover9(self):
        self.btn_p9.setEnabled(False)
        self.salida_p9.setPlainText("Prover9 está procesando las cláusulas...")
        
        # Si la casilla "Modo Avanzado" NO está marcada, cocinamos el texto automático
        if not self.chk_modo_p9.isChecked():
            texto_final = self.cocinar_entrada(self.premisas_p9, self.conclusion_p9)
        else:
            texto_final = self.entrada_libre_p9.toPlainText()
            
        resultado_crudo = ejecutar_prover9(texto_final)
        resultado_final = self.limpiar_y_traducir_error(resultado_crudo)
        
        self.salida_p9.setPlainText(resultado_final)
        self.btn_p9.setEnabled(True)

    def procesar_mace4(self):
        self.btn_m4.setEnabled(False)
        self.salida_m4.setPlainText("Mace4 está buscando un contraejemplo finito...")
        
        if not self.chk_modo_m4.isChecked():
            texto_final = self.cocinar_entrada(self.premisas_m4, self.conclusion_m4)
        else:
            texto_final = self.entrada_libre_m4.toPlainText()
            
        resultado_crudo = ejecutar_mace4(texto_final)
        resultado_final = self.limpiar_y_traducir_error(resultado_crudo)
        
        self.salida_m4.setPlainText(resultado_final)
        self.btn_m4.setEnabled(True)

    # --- LÓGICA DE ARCHIVOS (GESTIÓN SIMPLIFICADA) ---

    def nuevo_proyecto(self):
        if self.tabs.currentIndex() == 0:
            self.premisas_p9.clear()
            self.conclusion_p9.clear()
            self.entrada_libre_p9.clear()
            self.salida_p9.clear()
        else:
            self.premisas_m4.clear()
            self.conclusion_m4.clear()
            self.entrada_libre_m4.clear()
            self.salida_m4.clear()

    def abrir_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir Archivo Lógico", "", "Archivos de Entrada (*.in *.p9 *.txt)")
        if ruta:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
            # Al abrir un archivo completo, forzamos el modo avanzado para que se vea el código real
            if self.tabs.currentIndex() == 0:
                self.chk_modo_p9.setChecked(True)
                self.entrada_libre_p9.setPlainText(contenido)
            else:
                self.chk_modo_m4.setChecked(True)
                self.entrada_libre_m4.setPlainText(contenido)

    def guardar_archivo(self):
        pestaña_activa = self.tabs.currentIndex()
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar Archivo Lógico", "", "Archivos de Entrada (*.in)")
        if ruta:
            texto_a_guardar = ""
            if pestaña_activa == 0:
                texto_a_guardar = self.entrada_libre_p9.toPlainText() if self.chk_modo_p9.isChecked() else self.cocinar_entrada(self.premisas_p9, self.conclusion_p9)
            else:
                texto_a_guardar = self.entrada_libre_m4.toPlainText() if self.chk_modo_m4.isChecked() else self.cocinar_entrada(self.premisas_m4, self.conclusion_m4)
                
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(texto_a_guardar)

    def exportar_salida(self):
        editor_salida = self.salida_p9 if self.tabs.currentIndex() == 0 else self.salida_m4
        if editor_salida.toPlainText().strip():
            ruta, _ = QFileDialog.getSaveFileName(self, "Exportar Reporte de Salida", "", "Archivos de Reporte (*.out *.txt)")
            if ruta:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(editor_salida.toPlainText())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())