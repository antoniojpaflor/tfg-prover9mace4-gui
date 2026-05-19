import subprocess
import platform

def ejecutar_motor_logico(comando_base, texto_entrada):
    """
    Función genérica interna que interactúa con los binarios en segundo plano.
    Detecta de forma dinámica si el sistema operativo es Windows para enrutar
    la petición a través del subsistema de Linux (WSL).
    """
    sistema = platform.system()  # Devuelve 'Windows', 'Linux' o 'Darwin' (macOS)
    
    # Construimos el comando final adaptándonos al entorno de ejecución
    if sistema == 'Windows':
        # En Windows, redirigimos el comando al Ubuntu de WSL donde compilamos los binarios
        comando_final = ['wsl', '-d', 'Ubuntu-24.04'] + comando_base
    else:
        # En Linux o macOS nativo, ejecutamos el binario directamente del PATH del sistema
        comando_final = comando_base

    try:
        # Lanzamos el subproceso de forma asíncrona mediante pipes de entrada/salida
        proceso = subprocess.Popen(
            comando_final,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  # UTF-8 nativo para Python 3 (evita lidiar con bytes crudos)
        )
        
        # Inyectamos las fórmulas al flujo de entrada y capturamos la respuesta del motor
        stdout, stderr = proceso.communicate(input=texto_entrada)
        
        # Si el ejecutable devuelve un código de error de sistema, lo reportamos
        if proceso.returncode != 0 and not stdout:
            return f"Error en la ejecución del binario:\n{stderr}"
            
        return stdout
        
    except FileNotFoundError:
        if sistema == 'Windows':
            return (
                "Error crítico: No se ha detectado la distribución WSL especificada o "
                "los binarios lógicos no están instalados en /usr/local/bin dentro de ella."
            )
        else:
            return (
                f"Error crítico: El ejecutable '{comando_base[0]}' no está instalado o "
                "no es accesible en el PATH de este sistema."
            )

def ejecutar_prover9(texto_entrada):
    """
    Punto de entrada público para interactuar con el Demostrador de Teoremas Prover9.
    """
    return ejecutar_motor_logico(['prover9'], texto_entrada)

def ejecutar_mace4(texto_entrada):
    """
    Punto de entrada público para interactuar con el Buscador de Modelos y Contraejemplos Mace4.
    """
    return ejecutar_motor_logico(['mace4'], texto_entrada)


# --- BLOQUE DE PRUEBA AUTÓNOMA ---
# Este bloque solo se ejecuta si lanzas este script directamente (ej: python launcher.py)
# Sirve para verificar los motores lógicos de forma independiente a la interfaz gráfica.
if __name__ == "__main__":
    print(f"Detectando entorno... Sistema actual: {platform.system()}")
    
    # 1. Caso de prueba básico para Prover9
    ejemplo_prover9 = """
    formulas(sos).
      p -> q.
      p.
    end_of_list.

    formulas(goals).
      q.
    end_of_list.
    """
    print("\n--- Probando Prover9 ---")
    print("Enviando problema deductivo...")
    salida_p9 = ejecutar_prover9(ejemplo_prover9)
    
    if "THEOREM PROVED" in salida_p9:
        print(">> ¡Éxito! Prover9 funciona y ha demostrado el teorema.")
    else:
        print(">> Hubo un problema con la salida de Prover9.")

    # 2. Caso de prueba básico para Mace4 (Búsqueda de un contraejemplo)
    ejemplo_mace4 = """
    formulas(sos).
      p -> q.
    end_of_list.

    formulas(goals).
      q.
    end_of_list.
    """
    print("\n--- Probando Mace4 ---")
    print("Enviando problema inválido para forzar la búsqueda de un modelo...")
    salida_m4 = ejecutar_mace4(ejemplo_mace4)
    
    if "Exiting with 1 model" in salida_m4 or "model(s) found" in salida_m4 or "interpretation" in salida_m4:
        print(">> ¡Éxito! Mace4 funciona y ha hallado un contraejemplo válido.")
    else:
        print(">> Hubo un problema con la salida de Mace4.")