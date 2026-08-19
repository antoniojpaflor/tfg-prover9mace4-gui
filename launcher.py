import subprocess
import platform
import os
import sys
from datetime import datetime


def obtener_ruta_recurso(nombre_archivo):
    """Obtiene la ruta absoluta al recurso, compatible con desarrollo y con PyInstaller"""
    try:
        ruta_base = sys._MEIPASS
    except Exception:
        ruta_base = os.path.abspath(".")
    return os.path.join(ruta_base, 'bin', nombre_archivo)


def ejecutar_motor_logico(comando_base, texto_entrada, tiempo_limite=3):
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
        
        # CAPTURA MEJORADA: Mostramos el código de salida y la ruta intentada
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
        # CAPTURA DE ERROR DE FORMATO DE WINDOWS
        return f"Error del sistema operativo (¿es un .exe válido?):\n{str(e)}"


def ejecutar_prover9(texto_entrada, tiempo_limite=5):
    hora_ejecucion = datetime.now().strftime("%H:%M:%S")
    resultado = ejecutar_motor_logico(['prover9'], texto_entrada, tiempo_limite=tiempo_limite)
    return resultado, hora_ejecucion


def ejecutar_mace4(texto_entrada, tiempo_limite=3):
    hora_ejecucion = datetime.now().strftime("%H:%M:%S")
    resultado = ejecutar_motor_logico(['mace4'], texto_entrada, tiempo_limite=tiempo_limite)
    return resultado, hora_ejecucion