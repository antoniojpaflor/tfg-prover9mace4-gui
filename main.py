import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QTabWidget, QFileDialog, QMenuBar, QGroupBox)
from PyQt6.QtGui import QFont, QAction

# Importamos las funciones del launcher multiplataforma
from launcher import ejecutar_prover9, ejecutar_mace4

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        # Variables para controlar los archivos abiertos en cada pestaña
        self.archivo_actual_p9 = None
        self.archivo_actual_m4 = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Prover9-Mace4 GUI - TFG Antonio J. Parras")
        self.setGeometry(100, 100, 1100, 750)
        
        # 1. Creación de la Barra de Menús Superior
        self.crear_barra_menus()
        
        # 2. Contenedor de Pestañas
        self.tabs = QTabWidget()
        self.tab_prover9 = QWidget()
        self.tab_mace4 = QWidget()
        
        self.tabs.addTab(self.tab_prover9, "Demostrador Prover9")
        self.tabs.addTab(self.tab_mace4, "Buscador de Modelos Mace4")
        
        # 3. Configuración del contenido de las pestañas
        self.configurar_tab_prover9()
        self.configurar_tab_mace4()
        
        self.setCentralWidget(self.tabs)

    def crear_barra_menus(self):
        """Construye el menú superior de la aplicación"""
        barra_menus = self.menuBar()
        
        # Menú Archivo
        menu_archivo = barra_menus.addMenu("&Archivo")
        
        # Acciones del menú
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
        
        # Añadir las acciones al menú
        menu_archivo.addAction(accion_nuevo)
        menu_archivo.addSeparator()
        menu_archivo.addAction(accion_abrir)
        menu_archivo.addAction(accion_guardar)
        menu_archivo.addSeparator()
        menu_archivo.addAction(accion_exportar)
        menu_archivo.addSeparator()
        menu_archivo.addAction(accion_salir)

    def crear_panel_insercion(self, editor_destino):
        """Crea un panel lateral con botones de ayuda sintáctica para el editor que se le pase"""
        grupo = QGroupBox("Inserción Rápida")
        layout_grupo = QVBoxLayout()
        
        # Estilos estéticos para los botones del panel lateral
        estilo_btn = "padding: 5px; font-weight: bold; background-color: #f0f0f0;"
        
        # Botones de bloques estructurales
        layout_grupo.addWidget(QLabel("Estructuras:"))
        btn_estructura = QPushButton("Bloque Completo")
        btn_estructura.setStyleSheet(estilo_btn)
        btn_estructura.clicked.connect(lambda: editor_destino.insertPlainText("formulas(sos).\n  \nend_of_list.\n\nformulas(goals).\n  \nend_of_list."))
        layout_grupo.addWidget(btn_estructura)
        
        # Botones de Conectivas Lógicas básicas de Prover9
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
            # Truco de Python (default argument) para asegurar que cada botón retiene su propio símbolo
            btn.clicked.connect(lambda checked, s=simbolo: editor_destino.insertPlainText(s))
            layout_grupo.addWidget(btn)
            
        layout_grupo.addStretch() # Empuja todo hacia arriba
        grupo.setLayout(layout_grupo)
        grupo.setFixedWidth(180)
        return grupo

    def configurar_tab_prover9(self):
        fuente_codigo = QFont("Courier New", 11)
        
        # Layout horizontal principal: Columna Izquierda (Panel) + Columna Derecha (Editores)
        layout_principal = QHBoxLayout()
        
        # Columna Derecha (Contenido de Prover9)
        columna_derecha = QVBoxLayout()
        
        columna_derecha.addWidget(QLabel("Fórmulas de Entrada para Prover9:"))
        self.entrada_p9 = QTextEdit()
        self.entrada_p9.setFont(fuente_codigo)
        self.entrada_p9.setPlainText("formulas(sos).\n  p -> q.\n  p.\nend_of_list.\n\nformulas(goals).\n  q.\nend_of_list.")
        columna_derecha.addWidget(self.entrada_p9)
        
        self.btn_p9 = QPushButton("Lanzar Demostrador Prover9")
        self.btn_p9.setStyleSheet("font-weight: bold; background-color: #1e3d59; color: white; padding: 10px;")
        self.btn_p9.clicked.connect(self.procesar_prover9)
        columna_derecha.addWidget(self.btn_p9)
        
        columna_derecha.addWidget(QLabel("Resultado de la Demostración:"))
        self.salida_p9 = QTextEdit()
        self.salida_p9.setFont(fuente_codigo)
        self.salida_p9.setReadOnly(True)
        columna_derecha.addWidget(self.salida_p9)
        
        # Ensamblamos la pestaña
        layout_principal.addWidget(self.crear_panel_insercion(self.entrada_p9)) # Panel izquierdo
        layout_principal.addLayout(columna_derecha) # Panel derecho
        self.tab_prover9.setLayout(layout_principal)

    def configurar_tab_mace4(self):
        fuente_codigo = QFont("Courier New", 11)
        
        layout_principal = QHBoxLayout()
        columna_derecha = QVBoxLayout()
        
        columna_derecha.addWidget(QLabel("Fórmulas de Entrada para Mace4:"))
        self.entrada_m4 = QTextEdit()
        self.entrada_m4.setFont(fuente_codigo)
        self.entrada_m4.setPlainText("formulas(sos).\n  p -> q.\nend_of_list.\n\nformulas(goals).\n  q.\nend_of_list.")
        columna_derecha.addWidget(self.entrada_m4)
        
        self.btn_m4 = QPushButton("Lanzar Buscador de Modelos Mace4")
        self.btn_m4.setStyleSheet("font-weight: bold; background-color: #17b978; color: white; padding: 10px;")
        self.btn_m4.clicked.connect(self.procesar_mace4)
        columna_derecha.addWidget(self.btn_m4)
        
        columna_derecha.addWidget(QLabel("Estructura / Modelo Hallado:"))
        self.salida_m4 = QTextEdit()
        self.salida_m4.setFont(fuente_codigo)
        self.salida_m4.setReadOnly(True)
        columna_derecha.addWidget(self.salida_m4)
        
        layout_principal.addWidget(self.crear_panel_insercion(self.entrada_m4))
        layout_principal.addLayout(columna_derecha)
        self.tab_mace4.setLayout(layout_principal)

    # --- LÓGICA DE ARCHIVOS (PERSISTENCIA) ---

    def nuevo_proyecto(self):
        pestaña_activa = self.tabs.currentIndex()
        if pestaña_activa == 0:
            self.entrada_p9.clear()
            self.salida_p9.clear()
            self.archivo_actual_p9 = None
        else:
            self.entrada_m4.clear()
            self.salida_m4.clear()
            self.archivo_actual_m4 = None

    def abrir_archivo(self):
        pestaña_activa = self.tabs.currentIndex()
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir Archivo Lógico", "", "Archivos de Entrada (*.in *.p9 *.txt);;Todos los archivos (*)")
        
        if ruta:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
            
            if pestaña_activa == 0:
                self.entrada_p9.setPlainText(contenido)
                self.archivo_actual_p9 = ruta
            else:
                self.entrada_m4.setPlainText(contenido)
                self.archivo_actual_m4 = ruta

    def guardar_archivo(self):
        pestaña_activa = self.tabs.currentIndex()
        # Decidimos qué ruta usar según la pestaña en la que se encuentre el usuario
        ruta_actual = self.archivo_actual_p9 if pestaña_activa == 0 else self.archivo_actual_m4
        editor_actual = self.entrada_p9 if pestaña_activa == 0 else self.entrada_m4
        
        if not ruta_actual:
            # Si es la primera vez que se guarda, abrimos "Guardar como"
            ruta_actual, _ = QFileDialog.getSaveFileName(self, "Guardar Archivo Lógico", "", "Archivos de Entrada (*.in);;Todos los archivos (*)")
            if not ruta_actual:
                return # Si el usuario cancela, salimos
                
            if pestaña_activa == 0: self.archivo_actual_p9 = ruta_actual
            else: self.archivo_actual_m4 = ruta_actual
            
        with open(ruta_actual, "w", encoding="utf-8") as f:
            f.write(editor_actual.toPlainText())

    def exportar_salida(self):
        pestaña_activa = self.tabs.currentIndex()
        editor_salida = self.salida_p9 if pestaña_activa == 0 else self.salida_m4
        
        if not editor_salida.toPlainText().strip():
            return # No exportamos paneles vacíos
            
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar Reporte de Salida", "", "Archivos de Reporte (*.out *.txt)")
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(editor_salida.toPlainText())

    # --- EJECUCIÓN DE BOTONES ---

    def procesar_prover9(self):
        self.btn_p9.setEnabled(False)
        self.salida_p9.setPlainText("Prover9 está procesando las cláusulas...")
        resultado = ejecutar_prover9(self.entrada_p9.toPlainText())
        self.salida_p9.setPlainText(resultado)
        self.btn_p9.setEnabled(True)

    def procesar_mace4(self):
        self.btn_m4.setEnabled(False)
        self.salida_m4.setPlainText("Mace4 está buscando un contraejemplo finito...")
        resultado = ejecutar_mace4(self.entrada_m4.toPlainText())
        self.salida_m4.setPlainText(resultado)
        self.btn_m4.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())