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


def ejecutar_motor_logico(comando_base, texto_entrada):
    """!
    @brief Ejecuta un motor lógico como subproceso delegando el control temporal al propio motor.
    
    Configura el entorno según el sistema operativo, busca el binario 
    correspondiente e inicia el proceso capturando su salida estándar de forma bloqueante.
    
    @param comando_base Lista con el nombre del motor (ej. ['prover9']).
    @param texto_entrada Código fuente en formato cadena para ser procesado.
    @return Salida estándar (stdout) del motor lógico o mensaje de error formateado.
    """
    sistema = platform.system()
    nombre_binario = comando_base[0]
    
    if sistema == 'Windows': nombre_binario += '.exe'
    elif sistema == 'Linux': nombre_binario += '_linux'
    elif sistema == 'Darwin': nombre_binario += '_mac'
        
    ruta_binario = obtener_ruta_recurso(nombre_binario)
    comando_final = [ruta_binario] + comando_base[1:]
    
    opciones_subproceso = {'stdin': subprocess.PIPE, 'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE, 'text': True}
    if sistema == 'Windows': opciones_subproceso['creationflags'] = subprocess.CREATE_NO_WINDOW
    
    try:
        proceso = subprocess.Popen(comando_final, **opciones_subproceso)
        stdout, stderr = proceso.communicate(input=texto_entrada)
        
        if proceso.returncode != 0 and not stdout:
            return f"Error de ejecución (Código de salida: {proceso.returncode}):\nIntentando ejecutar: {ruta_binario}\nDetalles (Stderr): {stderr}"
        return stdout
        
    except FileNotFoundError:
        return f"Error crítico: No se encuentra el ejecutable en la ruta {ruta_binario}. Revisa la carpeta 'bin/'."
    except OSError as e:
        return f"Error del sistema operativo:\n{str(e)}"

def ejecutar_prover9(texto_entrada):
    """!
    @brief Envoltorio específico para ejecutar el demostrador de teoremas Prover9.
    
    @param texto_entrada Código fuente de Prover9 listo para ser procesado.
    @return Tupla que contiene la cadena de texto con el resultado crudo y la hora de ejecución.
    """
    hora_ejecucion = datetime.now().strftime("%H:%M:%S")
    resultado = ejecutar_motor_logico(['prover9'], texto_entrada)
    return resultado, hora_ejecucion

def ejecutar_mace4(texto_entrada):
    """!
    @brief Envoltorio específico para ejecutar el buscador de modelos finitos Mace4.
    
    @param texto_entrada Código fuente de Mace4 listo para ser procesado.
    @return Tupla que contiene la cadena de texto con el resultado crudo y la hora de ejecución.
    """
    hora_ejecucion = datetime.now().strftime("%H:%M:%S")
    resultado = ejecutar_motor_logico(['mace4'], texto_entrada)
    return resultado, hora_ejecucion