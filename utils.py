from datetime import datetime
from functools import reduce
import asyncio
from selenium_driverless.types.by import By
from selenium_driverless.types.webelement import NoSuchElementException


class maxRetries(Exception):
    pass


# -----------------------------------------------------------------------------
# FUNCIÓN para hacer click y verificar selección
# -----------------------------------------------------------------------------
async def click_verificado_seleccion(driver, by, element, by_verifier, verifier_element, selected_item, element_description = 'Texto', click_normal = True, max_retries=3, auto_refresh = True):

    for intento in range(max_retries):
        if intento > 0:
            print(f"🔄 Intento {intento + 1} de {max_retries}...")

        try:
            elemento = await driver.find_element(by, element, timeout=10)
            if click_normal:
                await elemento.click(move_to=True)
            else:
                await driver.execute_script("arguments[0].click();", elemento)
            
            elemento_verificador = await driver.find_element(by_verifier, verifier_element, timeout=10)
            texto_verificador = await elemento_verificador.get_attribute('value')

            if texto_verificador == selected_item:
                print(f"🟢 {element_description} ingresado correctamente.")
                return True
            else:
                print("🟡 Problema al ingresar el texto.")
                if intento < max_retries - 1:
                    print("➡️ Refrescando la página para reintentar.")
                    await driver.refresh()
                
        except Exception as e:
            print(f"🔴 Ocurrió un error inesperado: {e}")
            if intento < max_retries - 1:
                print("➡️ Refrescando la página para reintentar.")
                if auto_refresh:
                    await driver.refresh()

    print(f"🔴 No se pudo avanzar en el formulario después de {max_retries} intentos.")
    raise maxRetries(f"Se agotó el número de intentos para ingresar el texto.")


# -----------------------------------------------------------------------------
# FUNCIÓN para hacer click con reintentos capturando NoSuchElementException
# -----------------------------------------------------------------------------
async def click_con_reintentos(driver, by, element, element_description, click_normal = True, max_retries=3, auto_refresh = False):
    for intento in range(max_retries):
        try:
            if intento > 0:
                print(f"🔄 Intento {intento + 1} de {max_retries}...")
            elemento = await driver.find_element(by, element, timeout=10)
            if click_normal:
                await elemento.click(move_to=True)
            else:
                await driver.execute_script("arguments[0].click();", elemento)
            
            print(f"🟢 Click en '{element_description}'.")
            return True

        except NoSuchElementException:
            print(f"🟡 Intento {intento + 1} fallido: No se encontró el elemento.")
            
            if intento < max_retries - 1:
                print("➡️ Refrescando la página para reintentar.")
                if auto_refresh:
                    await driver.refresh()
                else:
                    await asyncio.sleep(1)
            
    print(f"🔴 No se pudo hacer click en el elemento después de {max_retries} intentos.")
    
    raise maxRetries(f"Se agotó el número de intentos para hacer click en '{element_description}'")


# -----------------------------------------------------------------------------
# FUNCIÓN para ingresar texto y verificar que fue ingresado correctamente
# -----------------------------------------------------------------------------
async def send_keys_verificado(driver, by, element, input_text, element_description = 'Texto', max_retries=3, auto_refresh = True):

    for intento in range(max_retries):
        if intento > 0:
            print(f"🔄 Intento {intento + 1} de {max_retries}...")

        try:
            input_field = await driver.find_element(by, element, timeout=10)
            await input_field.clear()
            await input_field.send_keys(input_text)
            
            elemento_verificador = await driver.find_element(by, element, timeout=10)
            texto_verificador = await elemento_verificador.get_attribute('value')

            if texto_verificador == input_text:
                print(f"🟢 {element_description} ingresado correctamente.")
                return True
            else:
                print("🟡 Problema al ingresar el texto.")
                if intento < max_retries - 1:
                    print("➡️ Refrescando la página para reintentar.")
                    await driver.refresh()
                
        except Exception as e:
            print(f"🔴 Ocurrió un error inesperado: {e}")
            if intento < max_retries - 1:
                print("➡️ Refrescando la página para reintentar.")
                if auto_refresh:
                    await driver.refresh()

    print(f"🔴 No se pudo avanzar en el formulario después de {max_retries} intentos.")
    raise maxRetries(f"Se agotó el número de intentos para ingresar el texto.")



# -----------------------------------------------------------------------------
# FUNCIÓN para hacer click y verificar que un elemento deje de existir
# -----------------------------------------------------------------------------
async def click_verificado_elemento(driver, by, element, by_verifier, verifier_element, element_description='el elemento', click_normal = True, max_retries=3, auto_refresh = True):
    
    for intento in range(max_retries):
        if intento > 0:
            print(f"🔄 Intento {intento + 1} de {max_retries}...")
        try:           
            elemento = await driver.find_element(by, element, timeout=10)

            if click_normal:
                await elemento.click(move_to=True)
            else:
                await driver.execute_script("arguments[0].click();", elemento)

            print(f"🟢 Click en '{element_description}'.")

            await asyncio.sleep(1) 

            elemento_verificador = await driver.find_elements(by_verifier, verifier_element, timeout=10)

            if len(elemento_verificador) == 0:
                # Lista vacía = no se encontró el elemento verificador = ¡ÉXITO!
                print("🟢 Click verificado.")
                return True
            else:
                # La lista tiene elementos = sigue presente el elemento verificador = FALLO.
                print("🟡 El proceso no avanzó.")
                if intento < max_retries - 1:
                    print("➡️ Refrescando la página para reintentar.")
                    await driver.refresh()

        except Exception as e:
            print(f"🔴 Ocurrió un error inesperado': {e}")
            if intento < max_retries - 1:
                print("➡️ Refrescando la página para reintentar.")
                if auto_refresh:
                    await driver.refresh()
                

    print(f"🔴 No se pudo avanzar después de {max_retries} intentos.")
    raise maxRetries(f"Se agotó el número de intentos para hacer click en '{element_description}'")





# -----------------------------------------------------------------------------
# FUNCIÓN para hacer click y verificar que cambie la URL
# -----------------------------------------------------------------------------
async def click_verificado_url(driver, by, element, target_url = '', element_description='el elemento', max_retries=4, auto_refresh = True):
    
    for intento in range(max_retries):
        if intento > 0:
            print(f"🔄 Intento {intento + 1} de {max_retries}...")
        try:
            current_url = await driver.current_url
            if current_url == target_url:
                return True

            if intento < 3:
                elemento = await driver.find_element(by, element, timeout=10)
                await elemento.click(move_to=True)
                print(f"🟢 Click en '{element_description}'.")
            else:
                print("⏳ Accediendo manualmente a la url target.")
                await driver.get(target_url, wait_load=True)

            await asyncio.sleep(1)

            current_url = await driver.current_url
            if current_url == target_url:
                return True
            
            print("🟡 La URL no cambió en este intento.")
            print(f"🔍 URL después del clic: {current_url}")

            if intento < max_retries - 1:
                print("➡️ Refrescando la página para reintentar.")
                if auto_refresh:
                    await driver.refresh()

        except Exception as e:
            print(f"🔴 Ocurrió un error en el intento {intento + 1} al interactuar con '{element_description}': {e}")
            if intento < max_retries - 1:
                print("➡️ Refrescando la página para reintentar.")
                if auto_refresh:
                    await driver.refresh()
    
    
                

    print(f"🔴 Se alcanzó el número máximo de reintentos sin éxito para '{element_description}'.")


    

    raise maxRetries(f"Se agotó el número de intentos para hacer click en '{element_description}'")






# FUNCIONES PARA ELEGIR LA MEJOR FECHA ----------------------------------------
# CRITERIO: la fecha menor gana (para rango de fecha se observa soo Upper Bound)
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
def encontrar_mejor_shipping(opciones_de_envio: list) -> dict:
    if not opciones_de_envio:
        return None
    if len(opciones_de_envio) == 1:
        return opciones_de_envio[0]
    
    return reduce(_comparar_dos_opciones, opciones_de_envio)