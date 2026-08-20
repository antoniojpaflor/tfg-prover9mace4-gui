"""
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
    """
    @brief Obtiene la ruta absoluta al recurso, compatible con desarrollo y con PyInstaller.
    
    @param nombre_archivo Nombre del archivo binario a buscar (con o sin extensión .exe).
    @return Ruta completa y segura al ejecutable dentro de la carpeta 'bin'.
    """
    try:
        ruta_base = sys._MEIPASS
    except Exception:
        ruta_base = os.path.abspath(".")
    return os.path.join(ruta_base, 'bin', nombre_archivo)


def ejecutar_motor_logico(comando_base, texto_entrada, tiempo_limite=3):
    """
    @brief Ejecuta un motor lógico como subproceso y captura su salida.
    
    Configura el entorno según el sistema operativo, busca el binario 
    correspondiente y maneja los tiempos de espera y errores del sistema.
    
    @param comando_base Lista con el nombre del motor (ej. ['prover9']).
    @param texto_entrada Código fuente en formato cadena para ser procesado.
    @param tiempo_limite Tiempo máximo de ejecución en segundos (por defecto 3).
    @return Salida estándar (stdout) del motor lógico o mensaje de error formateado.
    """
    sistema = platform.system()
    nombre_binario = comando_base[0]
    
    if sistema == 'Windows':
        nombre_binario += '.exe'
        
    ruta_binario = obtener_ruta_recurso(nombre_binario)
    comando_final = [ruta_binario] + comando_base[1:]
    proceso = None
    
    try:
        proceso = subprocess.Popen(
            comando_final,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proceso.communicate(input=texto_entrada, timeout=tiempo_limite)
        
        if proceso.returncode != 0 and not stdout:
            return f"Error de ejecución (Código de salida: {proceso.returncode}):\nIntentando ejecutar: {ruta_binario}\nDetalles (Stderr): {stderr}"
            
        return stdout
        
    except subprocess.TimeoutExpired:
        if proceso:
            proceso.kill()
            proceso.communicate()
            
        if comando_base[0] == 'mace4':
            return (
                "TIMEOUT_EXPIRED_M4\n"
                "Mace4 ha agotado el tiempo límite de búsqueda sin encontrar contraejemplos.\n"
                "¡Prueba a verificarlo en la pestaña de Prover9!"
            )
        else:
            return (
                "TIMEOUT_EXPIRED_P9\n"
                "Prover9 ha agotado el tiempo límite configurado sin encontrar una demostración."
            )
            
    except FileNotFoundError:
        return f"Error crítico: No se encuentra el ejecutable en la ruta {ruta_binario}. Revisa la carpeta 'bin/'."
        
    except OSError as e:
        return f"Error del sistema operativo (¿es un .exe válido?):\n{str(e)}"


def ejecutar_prover9(texto_entrada, tiempo_limite=5):
    """
    @brief Envoltorio específico para ejecutar el demostrador de teoremas Prover9.
    
    @param texto_entrada Código fuente de Prover9 listo para ser procesado.
    @param tiempo_limite Tiempo máximo de ejecución en segundos (por defecto 5).
    @return Tupla que contiene la cadena de texto con el resultado crudo y la hora de ejecución.
    """
    hora_ejecucion = datetime.now().strftime("%H:%M:%S")
    resultado = ejecutar_motor_logico(['prover9'], texto_entrada, tiempo_limite=tiempo_limite)
    return resultado, hora_ejecucion


def ejecutar_mace4(texto_entrada, tiempo_limite=3):
    """
    @brief Envoltorio específico para ejecutar el buscador de modelos finitos Mace4.
    
    @param texto_entrada Código fuente de Mace4 listo para ser procesado.
    @param tiempo_limite Tiempo máximo de ejecución en segundos (por defecto 3).
    @return Tupla que contiene la cadena de texto con el resultado crudo y la hora de ejecución.
    """
    hora_ejecucion = datetime.now().strftime("%H:%M:%S")
    resultado = ejecutar_motor_logico(['mace4'], texto_entrada, tiempo_limite=tiempo_limite)
    return resultado, hora_ejecucion