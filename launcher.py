import subprocess
import platform
from datetime import datetime

def ejecutar_motor_logico(comando_base, texto_entrada, tiempo_limite=3):
    """
    Función genérica interna que interactúa con los binarios en segundo plano.
    Añade un control de 'timeout' (tiempo_limite) para evitar que procesos en bucle
    infinito congelen la aplicación principal.
    """
    sistema = platform.system()
    
    if sistema == 'Windows':
        comando_final = ['wsl', '-d', 'Ubuntu-24.04'] + comando_base
    else:
        comando_final = comando_base

    proceso = None
    try:
        proceso = subprocess.Popen(
            comando_final,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Bloqueamos el proceso con un límite de tiempo estricto (3 segundos por defecto)
        stdout, stderr = proceso.communicate(input=texto_entrada, timeout=tiempo_limite)
        
        if proceso.returncode != 0 and not stdout:
            return f"Error en la ejecución del binario:\n{stderr}"
            
        return stdout
        
    except subprocess.TimeoutExpired:
        # ¡Acción de rescate! Si el binario se pasa de tiempo, lo matamos de raíz
        if proceso:
            proceso.kill()
            # Limpiamos los buffers para liberar descriptores de archivos
            proceso.communicate()
            
        if comando_base[0] == 'mace4':
            return (
                "TIMEOUT_EXPIRED_M4\n"
                "Mace4 ha agotado el tiempo límite de búsqueda sin encontrar contraejemplos.\n"
                "Esto suele ocurrir porque el teorema es VÁLIDO (no existen fallos lógicos) "
                "y el motor se ha quedado atrapado buscando un modelo imposible infinitamente.\n"
                "¡Prueba a verificarlo en la pestaña de Prover9!"
            )
        else:
            return (
                "TIMEOUT_EXPIRED_P9\n"
                "Prover9 ha agotado el tiempo límite configurado sin encontrar una demostración.\n"
                "El problema podría ser demasiado complejo o inválido."
            )
            
    except FileNotFoundError:
        if sistema == 'Windows':
            return "Error crítico: No se ha detectado la distribución WSL o los binarios."
        else:
            return f"Error crítico: El ejecutable '{comando_base[0]}' no es accesible."

def ejecutar_prover9(texto_entrada, tiempo_limite=5):
    hora_ejecucion = datetime.now().strftime("%H:%M:%S")
    resultado = ejecutar_motor_logico(['prover9'], texto_entrada, tiempo_limite=tiempo_limite)
    return resultado, hora_ejecucion

def ejecutar_mace4(texto_entrada, tiempo_limite=3):
    hora_ejecucion = datetime.now().strftime("%H:%M:%S")
    resultado = ejecutar_motor_logico(['mace4'], texto_entrada, tiempo_limite=tiempo_limite)
    return resultado, hora_ejecucion