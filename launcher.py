"""!
@file launcher.py
@brief Módulo de ejecución y comunicación con los motores lógicos Prover9 y Mace4.

Este módulo abstrae la capa del sistema operativo, encargándose de localizar
los binarios adecuados según la plataforma (Windows, Linux, macOS) y lanzar 
los subprocesos de manera segura controlando los tiempos de ejecución.
"""
import subprocess
import platform
import os
import sys
from datetime import datetime
from PyQt6.QtCore import QProcess


def obtener_ruta_recurso(nombre_archivo):
    """!
    @brief Obtiene la ruta absoluta al recurso, compatible con desarrollo y con PyInstaller.
    
    @param nombre_archivo Nombre del archivo binario a buscar (con o sin extensión .exe).
    @return Ruta completa y segura al ejecutable dentro de la carpeta 'bin'.
    """
    try:
        ruta_base = sys._MEIPASS
    except Exception:
        ruta_base = os.path.abspath(".")
    return os.path.join(ruta_base, 'bin', nombre_archivo)


def ejecutar_motor_logico(comando_base, texto_entrada, hilo=None):
    """!
    @brief Ejecuta un motor lógico utilizando QProcess para evitar bloqueos en la interfaz.
    
    Delega el proceso nativo al bucle de eventos de Qt, permitiendo una 
    interrupción segura (kill) sin dejar procesos huérfanos ni bloquear tuberías.
    
    @param comando_base Lista con el nombre del motor (ej. ['prover9']).
    @param texto_entrada Código fuente completo que se enviará a la entrada estándar.
    @param hilo Referencia opcional al HiloMotor para comprobar la bandera de cancelación.
    @return Salida estándar (stdout) decodificada, "CANCELADO" o mensaje de error.
    """
    sistema = platform.system()
    nombre_binario = comando_base[0]
    
    if sistema == 'Windows': nombre_binario += '.exe'
    elif sistema == 'Linux': nombre_binario += '_linux'
    elif sistema == 'Darwin': nombre_binario += '_mac'
        
    ruta_binario = obtener_ruta_recurso(nombre_binario)
    
    if hilo is not None and hilo.cancelado:
        return "CANCELADO"
        
    proceso = QProcess()
    
    proceso.start(ruta_binario, comando_base[1:])
    
    if not proceso.waitForStarted(2000):
        return f"Error crítico: No se pudo iniciar el proceso en {ruta_binario}."
        
    proceso.write(texto_entrada.encode('utf-8'))
    proceso.closeWriteChannel()
    
    while not proceso.waitForFinished(500):
        if hilo is not None and hilo.cancelado:
            proceso.kill()
            proceso.waitForFinished(1000)
            return "CANCELADO"
            
    stdout = proceso.readAllStandardOutput().data().decode('utf-8', errors='replace')
    stderr = proceso.readAllStandardError().data().decode('utf-8', errors='replace')
    
    if proceso.exitCode() != 0 and not stdout.strip():
        return f"Error de ejecución (Código de salida: {proceso.exitCode()}):\nIntentando ejecutar: {ruta_binario}\nDetalles: {stderr}"
        
    return stdout


def ejecutar_prover9(texto_entrada, hilo=None):
    """!
    @brief Envoltorio específico para iniciar el demostrador de teoremas Prover9.
    
    @param texto_entrada Código fuente de Prover9 listo para procesar.
    @param hilo Referencia al hilo de PyQt para el control de cancelación.
    @return Tupla con el resultado (texto) y la hora de finalización.
    """
    hora_ejecucion = datetime.now().strftime("%H:%M:%S")
    resultado = ejecutar_motor_logico(['prover9'], texto_entrada, hilo)
    return resultado, hora_ejecucion


def ejecutar_mace4(texto_entrada, hilo=None):
    """!
    @brief Envoltorio específico para iniciar el buscador de modelos finitos Mace4.
    
    @param texto_entrada Código fuente de Mace4 listo para procesar.
    @param hilo Referencia al hilo de PyQt para el control de cancelación.
    @return Tupla con el resultado (texto) y la hora de finalización.
    """
    hora_ejecucion = datetime.now().strftime("%H:%M:%S")
    resultado = ejecutar_motor_logico(['mace4'], texto_entrada, hilo)
    return resultado, hora_ejecucion