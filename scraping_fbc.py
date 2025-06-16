import json
import re
from datetime import datetime
import pandas as pd
import asyncio
import traceback
from selenium_driverless import webdriver
from selenium_driverless.types.by import By
from selenium_driverless.types.webelement import WebElement
from selenium_driverless.types.webelement import NoSuchElementException

# Lista de productos
# product_ids = ["118323391", "15643401", "110037565", "138124130", "17287672", "17127319", "15784952", "139603723", "7001702", "17243432"]
product_ids = ["118323391"]

# Datos cliente
USER_DATA = {
    "email": "performance_test@falabella.cl",
    "region": "METROPOLITANA DE SANTIAGO",
    "comuna": "LAS CONDES",
    "calle": "Rosario Norte",
    "numero": "660"
}



async def get_shipping_info_for_product(product_id: str):

    print(f"--- Processing Product ID: {product_id} ---")
    
    options = webdriver.ChromeOptions()
    
    # Navegador
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
    options.add_argument(f"--user-agent={user_agent}")
    
    # Ventana
    options.add_argument("--window-size=1920,1060")
    
    # Protección anti-bots
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    
    # Headless mode
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    from utils import _parse_date, _comparar_dos_opciones, encontrar_mejor_opcion_segun_reglas
    
    
    try:
        
        async with webdriver.Chrome(options=options) as driver:

            
            await driver.get(f"https://www.falabella.com/falabella-cl/product/{product_id}", wait_load=True)
            print(f"🟢 Página de producto {product_id} cargada.")

            pdp_compra_internacional, pdp_envio_gratis_app = False, False

            try:
                await driver.find_element(By.XPATH, "//p[contains(@class, 'international-text') and contains(., 'Compra internacional')]")
                pdp_compra_internacional = True
                print("✅ Encontrado en PDP: 'Compra internacional'")
            except NoSuchElementException:
                pass

            try:
                await driver.find_element(By.XPATH, "//span[contains(@class, 'pod-badges-item-PDP') and contains(., 'gratis') and contains(., 'app')]")
                pdp_envio_gratis_app = True
                print("✅ Encontrado en PDP: 'Envío gratis app'")
            except NoSuchElementException:
                pass

            try:
                add_to_cart_button = await driver.find_element(By.ID, 'add-to-cart-button', timeout=10)
                await add_to_cart_button.click(move_to=True)
                print("🟢 Click en 'Agregar al carro'.")
            
            except Exception as e:
                print("🔄 Intentando actualizar la página (F5)...") 
                await driver.refresh()

                add_to_cart_button = await driver.find_element(By.ID, 'add-to-cart-button', timeout=10)
                await add_to_cart_button.click(move_to=True)
                print("🟢 Click en 'Agregar al carro'.")
            
            # Variantes -----------------------------------------------------------------------------------------
            variant_selected = False
            button_text = ""

            try:
                operator_container = await driver.find_element(By.ID, "testId-Operator-container", timeout=3)
                print("✅ Contenedor de 'Operador' encontrado.")
                
                first_available_option = await operator_container.find_element(By.CSS_SELECTOR, "button.operator:not([disabled])")
                
                button_text = await first_available_option.text
                await driver.execute_script("arguments[0].click();", first_available_option)
                print(f"🟢 Se hizo click en la opción de operador: '{button_text}'")
                variant_selected = True

            except NoSuchElementException:
                try:
                    size_container = await driver.find_element(By.CSS_SELECTOR, "div.size-options", timeout=3)
                    print("✅ Contenedor de 'Talla' encontrado.")
                    

                    first_available_option = await size_container.find_element(By.CSS_SELECTOR, "button.size-button:not([disabled])")

                    button_text = await first_available_option.text
                    await driver.execute_script("arguments[0].click();", first_available_option)
                    print(f"🟢 Se hizo click en la opción de talla: '{button_text}'")
                    variant_selected = True

                except NoSuchElementException:
                    pass

            if variant_selected:
                go_to_cart_button = await driver.find_element(By.ID, "add-to-cart-button-lightbox", timeout=10)
                await driver.execute_script("arguments[0].click();", go_to_cart_button)
                print("🟢 Click en 'Agregar al Carro'.")


            
            # Garantía extendida --------------------------------------------------------------------------------------
            try:
                await driver.find_element(By.XPATH, "//p[contains(., 'Protege tu producto')]", timeout=5)
                print("✅ Opción de Garantía encontrado.")
            
                continuar_sin_garantia_btn = await driver.find_element(By.XPATH, "//button[normalize-space()='Continuar sin protección']", timeout=5)
                await driver.execute_script("arguments[0].click();", continuar_sin_garantia_btn)
                
                print("🟢 Click en 'Continuar sin protección'.")

            except NoSuchElementException:
                pass

            go_to_cart_button = await driver.find_element(By.ID, "linkButton", timeout=10)
            await driver.execute_script("arguments[0].click();", go_to_cart_button)
            print("🟢 Click en 'Ir al carro'.")


            try:
                continue_purchase_button = await driver.find_element(By.XPATH, "//button[text()='Continuar compra']", timeout=10)
                await continue_purchase_button.click(move_to=True)
                print("🟢 Click en 'Continuar compra'.")
            except NoSuchElementException:
                continue_purchase_button = await driver.find_element(By.XPATH, "//button[starts-with(@id, 'popover-trigger-')]", timeout=10)
                await continue_purchase_button.click(move_to=True)
                print("🟢 Click en 'Continuar compra'.")   

            try:
                email_input = await driver.find_element(By.ID, "testId-Input-email", timeout=10)
                await email_input.send_keys(USER_DATA["email"])
            except NoSuchElementException:
                email_input = await driver.find_element(By.CSS_SELECTOR, "input[data-testid='testId-Input-email']", timeout=10)
                await email_input.send_keys(USER_DATA["email"])

            continue_button = await driver.find_element(By.ID, "continueButton", timeout=10)
            await continue_button.click(move_to=True)
            print("🟢 Mail ingresado.")
            
            region_dropdown = await driver.find_element(By.XPATH, "//input[@placeholder='Selecciona una región']", timeout=10)
            await region_dropdown.click()
            region_option = await driver.find_element(By.XPATH, f"//button[contains(., '{USER_DATA['region']}')]", timeout=10)
            await region_option.click()
            print(f"🟢 Región seleccionada: {USER_DATA['region']}.")

            comuna_dropdown = await driver.find_element(By.XPATH, "//input[@placeholder='Selecciona una comuna']", timeout=10)
            await comuna_dropdown.click()
            comuna_option = await driver.find_element(By.XPATH, f"//button[contains(., '{USER_DATA['comuna']}')]", timeout=10)
            await comuna_option.click()
            print(f"🟢 Comuna seleccionada: {USER_DATA['comuna']}.")

            street_input = await driver.find_element(By.ID, "testId-Input-street", timeout=10)
            await street_input.send_keys(USER_DATA['calle'])
            print(f"🟢 Calle ingresada: {USER_DATA['calle']}.")
            
            number_input = await driver.find_element(By.ID, "testId-Input-number", timeout=10)
            await number_input.send_keys(USER_DATA["numero"])
            print(f"🟢 Número: {USER_DATA['numero']}.")
        
            confirm_address_button = await driver.find_element(By.ID, "testId-infoModalFooter-button", timeout=10)
            await driver.execute_script("arguments[0].click();", confirm_address_button)
            print("🟢 Click en 'Confirmar dirección'.")

            save_address_button = await driver.find_element(By.XPATH, "//button[contains(., 'Confirmar y Guardar')]", timeout=10)            
            await driver.execute_script("arguments[0].click();", save_address_button)
            print("🟢 Click en 'Confirmar y Guardar'.")

            print("⏳ Esperando a que cargue la opción 'Envío a domicilio'...")
            envio_domicilio_element = await driver.find_element(By.XPATH, '//p[contains(text(), "Envío a domicilio")]', timeout=10)
            print("✅ Opción 'Envío a domicilio' encontrada.")

    
            print("🕵️ Buscando la sección de 'Envío a domicilio' para extraer sus opciones...")


            opciones_de_envio = []

            try:
                seccion_envio_domicilio = await driver.find_element(By.XPATH, "//p[normalize-space()='Envío a domicilio']/../..")
                hijos_directos = await seccion_envio_domicilio.find_elements(By.XPATH, "./div")
                
                if len(hijos_directos) > 1:
                    contenedores_de_opciones = hijos_directos[1:]
                    print(f"✅ Se procesarán {len(contenedores_de_opciones)} contenedores de opciones de envío.")

                    for i, opcion_contenedor in enumerate(contenedores_de_opciones):
                        
                        # Variables de búsqueda
                        promesa, precio, free_shipping_label, envio_gratis_app = "", "", False, False


                        try:
                            promise_container = await opcion_contenedor.find_element(By.XPATH, ".//div[p[starts-with(@id, 'shipment-')]]", timeout=1)
                            raw_text = await promise_container.text
                            promesa = " ".join(raw_text.split()).replace(" ,", ",")

                        except NoSuchElementException:
                            try:
                                promise_container = await opcion_contenedor.find_element(By.ID, "shipment-option-homeDeliveryDateRange", timeout=1)
                                raw_text = await promise_container.text
                                promesa = " ".join(raw_text.split())

                            except NoSuchElementException:
                                print(f"🟡 Info (Opción {i+1}): No se encontró el texto de la promesa")


                        try:

                            price_elem = await opcion_contenedor.find_element(By.CSS_SELECTOR, "span[data-testid='shipment-price']", timeout=1)
                            precio = await price_elem.text

                        except NoSuchElementException:
                            print(f"🟡 Info (Opción {i+1}): No se encontró el precio.")                        

                        try:
                            await opcion_contenedor.find_element(By.CSS_SELECTOR, "div[data-testid='free-shipping-badge']", timeout=1)
                            envio_gratis_app = True
                        except NoSuchElementException:
                            pass

                        try:
                            await opcion_contenedor.find_element(By.CSS_SELECTOR, "span[data-testid='free-shipment-label']", timeout=1)
                            free_shipping_label = True
                        except NoSuchElementException:
                            pass
                        
                        opciones_de_envio.append({
                            "opcion_nro": i + 1,
                            "promesa_entrega": promesa,
                            "precio_envio": precio,
                            "tiene_free_shipping_label": free_shipping_label,
                            "tiene_envio_gratis_app": envio_gratis_app
                        })
                else:
                    print("🟡 No se encontraron contenedores de opciones de envío (solo se encontró el título).")

            except NoSuchElementException:
                print("❌ ERROR: No se pudo encontrar la sección de 'Envío a domicilio'.")


            # Formato promesa ------------------------------------------
            meses = {
                'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
            }
            hoy = datetime.now()
            fecha_actual_str = hoy.strftime('%d/%m/%Y')

            def formatear_fecha(tupla_fecha, fecha_referencia):
                dia_str, mes_str = tupla_fecha
                dia = int(dia_str)
                mes = meses.get(mes_str)
                if not mes: return ""
                
                ano = fecha_referencia.year
                if mes < fecha_referencia.month:
                    ano += 1
                
                try:
                    return datetime(ano, mes, dia).strftime("%d/%m/%Y")
                except ValueError:
                    return ""

            for opcion in opciones_de_envio:
                promesa_texto = opcion.get("promesa_entrega", "")
                
                opcion["specificDate"] = ""
                opcion["dateRangeLB"] = ""
                opcion["dateRangeUB"] = ""

                if "entre" in promesa_texto.lower():
                    dias = re.findall(r'\b(\d{1,2})\b', promesa_texto)
                    meses_encontrados = re.findall(r'de\s+([a-z]{3})', promesa_texto)
                    if len(dias) == 2 and len(meses_encontrados) == 1:
                        mes_comun = meses_encontrados[0]
                        opcion["dateRangeLB"] = formatear_fecha((dias[0], mes_comun), hoy)
                        opcion["dateRangeUB"] = formatear_fecha((dias[1], mes_comun), hoy)
                    elif len(dias) == 2 and len(meses_encontrados) == 2:
                        opcion["dateRangeLB"] = formatear_fecha((dias[0], meses_encontrados[0]), hoy)
                        opcion["dateRangeUB"] = formatear_fecha((dias[1], meses_encontrados[1]), hoy)
                else:
                    match_fecha_especifica = re.search(r"(\d{1,2})\s+de\s+([a-z]{3})", promesa_texto)
                    if match_fecha_especifica:
                        opcion["specificDate"] = formatear_fecha(match_fecha_especifica.groups(), hoy)

            filas_para_excel = []

            if not opciones_de_envio:
                print(f"🟡 No se encontraron opciones de envío para el producto {product_id}.")
                filas_para_excel.append({
                    "product_id": product_id,
                    "fecha_actual": fecha_actual_str,
                    "pdp_compra_internacional": pdp_compra_internacional,
                    "pdp_envio_gratis_app": pdp_envio_gratis_app,
                    "promesa": "N/A",
                    "precio": "N/A",
                    "free_shipping_label": "N/A",
                    "envio_gratis_app": "N/A",
                    "specificDate": "",
                    "dateRangeLB": "",
                    "dateRangeUB": ""
                })
            else:
                mejor_opcion = encontrar_mejor_opcion_segun_reglas(opciones_de_envio)
                
                if mejor_opcion:
                    fila = {
                        "product_id": product_id,
                        "fecha_actual": fecha_actual_str,
                        "pdp_compra_internacional": pdp_compra_internacional,
                        "pdp_envio_gratis_app": pdp_envio_gratis_app,
                        "promesa": mejor_opcion.get("promesa_entrega"),
                        "precio": mejor_opcion.get("precio_envio"),
                        "free_shipping_label": mejor_opcion.get("tiene_free_shipping_label"),
                        "envio_gratis_app": mejor_opcion.get("tiene_envio_gratis_app"),
                        "specificDate": mejor_opcion.get("specificDate", ""),
                        "dateRangeLB": mejor_opcion.get("dateRangeLB", ""),
                        "dateRangeUB": mejor_opcion.get("dateRangeUB", "")
                    }
                    filas_para_excel.append(fila)
            
            print("\n--- Resultados: ---")
            print(json.dumps(filas_para_excel, indent=2, ensure_ascii=False))

            # Pausa entre productos -------------------
            # await asyncio.to_thread(input)
            
            return filas_para_excel
            

    except Exception as e:
        print(f"❌ Ocurrió un error al procesar el producto {product_id}.")
        print(f"Detalles del error: {e}")
        traceback.print_exc()
        print("---------------------------------------\n")
        return None 


async def main():

    all_products_data = []

    for pid in product_ids:
        product_data = await get_shipping_info_for_product(pid)
        if product_data:
            all_products_data.extend(product_data)

    df = pd.DataFrame(all_products_data)
    df.to_excel("resultados_scraping.xlsx", index=False)


if __name__ == "__main__":
    asyncio.run(main())