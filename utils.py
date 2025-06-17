from datetime import datetime
from functools import reduce
import asyncio
from selenium_driverless.types.by import By



async def ingresar_email_y_verificar(driver, email, max_retries=3):

    for intento in range(max_retries):
        if intento > 0:
            print(f"🟢 Intento {intento + 1} de {max_retries} ---")

        try:
            email_input = await driver.find_element(By.ID, "testId-Input-email", timeout=10)
            await email_input.clear()
            await email_input.send_keys(email)
            
            continue_button = await driver.find_element(By.ID, "continueButton", timeout=10)
            await continue_button.click(move_to=True)

            await asyncio.sleep(1) 

            # Elemento de error
            elementos_error = await driver.find_elements(By.XPATH, "//p[text()='Ingresa tu correo electrónico para continuar']")

            if len(elementos_error) == 0:
                # Lista vacía = no se encontró el texto de error = ¡ÉXITO!
                print("🟢 Email ingresado y clic en 'Continuar'.")
                return True
            else:
                # La lista tiene elementos = se encontró el texto de error = FALLO.
                print("🟡 El formulario no avanzó.")
                if intento < max_retries - 1:
                    print("Refrescando la página para el siguiente intento...")
                    await driver.refresh()
                
        except Exception as e:
            print(f"🔴 Ocurrió un error inesperado: {e}")
            if intento < max_retries - 1:
                print("Refrescando la página para el siguiente intento...")
                await driver.refresh()

    print(f"\n🔴 No se pudo avanzar en el formulario después de {max_retries} intentos.")
    
    return False



async def hacer_clic_y_verificar_cambio_url(driver, by, value, element_description='el elemento', target_url = '', max_retries=3):
    
    for intento in range(max_retries):
        if intento > 0:
            print(f"🟢 Intento {intento + 1} de {max_retries} para hacer clic en '{element_description}' ---")
        try:           
            elemento = await driver.find_element(by, value, timeout=10)
            await elemento.click(move_to=True)
            print(f"🟢 Click en '{element_description}'.")

            tiempo_inicio = asyncio.get_event_loop().time()
            current_url = await driver.current_url
            
            while current_url != target_url:
                transcurrido = asyncio.get_event_loop().time() - tiempo_inicio
                if transcurrido > 10:
                    print(f"🔴 Tiempo de espera de {10}s agotado. La URL no cambió.")
                    break
                current_url = await driver.current_url
            
            print(f"URL después del clic: {current_url}")

            if current_url == target_url:
                print(f"✅ ¡Éxito! La URL ha cambiado correctamente tras el clic en '{element_description}'.")
                return True
            
            print("🟡 La URL no cambió en este intento.")
            if intento < max_retries - 1:
                print("Refrescando la página para reintentar...")
                await driver.refresh()

        except Exception as e:
            print(f"🔴 Ocurrió un error en el intento {intento + 1} al interactuar con '{element_description}': {e}")
            if intento < max_retries - 1:
                print("Refrescando la página para reintentar...")
                await driver.refresh()
                

    print(f"\n🔴 Se alcanzó el número máximo de reintentos sin éxito para '{element_description}'.")
    return False


# FUNCIONES PARA ELEGIR LA MEJOR FECHA ----------------------------------------
# -----------------------------------------------------------------------------
# FUNCIÓN 1: Ayudante para convertir strings de fecha a objetos datetime
# -----------------------------------------------------------------------------
def _parse_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except (ValueError, TypeError):
        return datetime.max

# -----------------------------------------------------------------------------
# FUNCIÓN 2: Lógica central para comparar únicamente DOS opciones
# -----------------------------------------------------------------------------
def _comparar_dos_opciones(op1: dict, op2: dict) -> dict:

    op1_es_rango = bool(op1.get("dateRangeLB"))
    op2_es_rango = bool(op2.get("dateRangeLB"))

    # Escenario 1: Fecha Específica vs. Fecha Específica
    # Gana la que tenga la fecha más temprana.
    if not op1_es_rango and not op2_es_rango:
        fecha1 = _parse_date(op1.get("specificDate"))
        fecha2 = _parse_date(op2.get("specificDate"))
        return op1 if fecha1 <= fecha2 else op2

    # Escenario 2: Rango de Fechas vs. Rango de Fechas
    # Gana la que tenga la fecha LÍMITE (UB) más temprana.
    if op1_es_rango and op2_es_rango:
        ub1 = _parse_date(op1.get("dateRangeUB"))
        ub2 = _parse_date(op2.get("dateRangeUB"))
        return op1 if ub1 <= ub2 else op2

    # Escenario 3: Fecha Específica (op1) vs. Rango (op2)
    if not op1_es_rango and op2_es_rango:
        fecha_especifica = _parse_date(op1.get("specificDate"))
        rango_ub = _parse_date(op2.get("dateRangeUB"))
        # Gana el rango si su fecha límite (UB) es igual o anterior a la específica.
        return op2 if rango_ub <= fecha_especifica else op1
    
    # Escenario 4: Rango (op1) vs. Fecha Específica (op2)
    if op1_es_rango and not op2_es_rango:
        rango_ub = _parse_date(op1.get("dateRangeUB"))
        fecha_especifica = _parse_date(op2.get("specificDate"))
        # Gana el rango si su fecha límite es igual o anterior a la específica.
        return op1 if rango_ub <= fecha_especifica else op2
    
    # Si algo falla o no entra en las categorías, devuelve la primera opción.
    return op1

# -----------------------------------------------------------------------------
# FUNCIÓN 3: Función principal que procesa la lista completa de opciones
# -----------------------------------------------------------------------------
def encontrar_mejor_opcion_segun_reglas(opciones_de_envio: list) -> dict:
    if not opciones_de_envio:
        return None
    if len(opciones_de_envio) == 1:
        return opciones_de_envio[0]
    
    return reduce(_comparar_dos_opciones, opciones_de_envio)