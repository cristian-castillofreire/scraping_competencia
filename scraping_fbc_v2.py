import time
import json
import warnings
import asyncio
from datetime import datetime
import pandas as pd
from selenium_driverless.types.by import By
from selenium_driverless.types.webelement import NoSuchElementException
from utils import click_verificado_elemento, click_con_reintentos, send_keys_verificado, seleccionar_productos_carro, delete_cart_item
from utils import setup_driver, encontrar_mejor_shipping, formato_promesa
from utils import verification_code_email, delete_all_falabella_notifications
warnings.filterwarnings("ignore", message="got execution_context_id and unique_context=True, defaulting to execution_context_id")

# Lista de productos
# product_ids = ['2521167', '2473515', '2537673', '2558268', '2565136', '2675502', '2700993', '2701014', '2701754', '2701755', '2702948', '2707002', '2707003', '2707301', '2708797', '2712096', '2759321', '2780334', '2780336', '2789831', '2798641', '2819857', '2820362', '2827037', '2827040', '2865616', '2865619', '2892131', '2908801', '2915441', '2985129', '2998040', '3003862', '3031421', '3031463', '3031815', '3038575', '3038579', '3038580', '3066595', '3111527', '3111992', '3122360', '3135729', '3135730', '3135731', '3136861', '3166646', '3265384', '3287877', '3287878', '3305978', '3306724', '3332645', '3370076', '3370168', '3391399', '3391400', '3391401', '3397897', '3435418', '3447807', '3448861', '3466711', '3466712', '3466713', '3477988', '3480446', '3480621', '3491456', '3491457', '3512125', '3524974', '3526765', '3550468', '3550484', '3550486', '3562061', '3604978', '3617925', '3647578', '3647636', '3651417', '3653333', '3668020', '3678720', '3685373', '3693050', '3695141', '3695143', '3695143', '3695146', '3741606', '3741613', '3793334', '3794880', '3839491', '3839492', '3842992', '3843025', '3843026', '3843179', '3860939', '3860940', '3869308', '3892545', '3892548', '3903121', '3904276']
product_ids = ['2521167', '2473515', '2537673', '2558268', '2565136', '2675502', '2700993', '2701014', '2701754', '2701755', '2702948', '2707002', '2707003', '2707301', '2708797', '2712096', '2759321', '2780334', '2780336', '2789831', '2798641', '2819857', '2820362', '2827037', '2827040', '2865616', '2865619', '2892131', '2908801', '2915441', '2985129', '2998040', '3003862', '3031421', '3031463', '3031815', '3038575', '3038579', '3038580', '3066595']
# product_ids = ['2521167', '15643401', '2473515', '2537673', '2558268', '2565136', '2675502', '2700993', '2701014', '2701754', '2701755', '2702948']
# product_ids = ['15643401', '17187740']
# product_ids = ['15643401']

# Datos cliente
ADDRESS_DATA = [{
    "region": "METROPOLITANA DE SANTIAGO",
    "comuna": "LAS CONDES",
    "calle": "Yaguero",
    "numero": "7786"
},
{
    "region": "ANTOFAGASTA",
    "comuna": "ANTOFAGASTA",
    "calle": "Juan Agustín Cornejo",
    "numero": "7373"
},
{
    "region": "BIOBÍO",
    "comuna": "CONCEPCIÓN",
    "calle": "Juan Martínez De Rozas",
    "numero": "1699"
},
{
    "region": "VALPARAÍSO",
    "comuna": "VALPARAÍSO",
    "calle": "Chacabuco",
    "numero": "2012"
},
{
    "region": "LA ARAUCANÍA",
    "comuna": "TEMUCO",
    "calle": "Juan Caniullan",
    "numero": "1901"
},
{
    "region": "VALPARAÍSO",
    "comuna": "VIÑA DEL MAR",
    "calle": "1 Poniente",
    "numero": "497"
},
{
    "region": "LIBERTADOR GENERAL BERNARDO O'HIGGINS",
    "comuna": "RANCAGUA",
    "calle": "Amberes",
    "numero": "139"
},
{
    "region": "COQUIMBO",
    "comuna": "LA SERENA",
    "calle": "Avenida Balmaceda",
    "numero": "686"
}
]

ACCOUNT_DATA = [{
    "user": "performance.test.falabella@gmail.com",
    "pw": "5F94oRbO0wYkf224bRmz",
    "api" : "dyweqhjbqvqfepqf"
},
{
    "user": "PqRsT8uVwXyZ1aBc.0@gmail.com",
    "pw": "5F94oRbO0wYkf224bRmz",
    "api" : "ygjnpzfhcqpppzrg"
}
]



async def run_scraping(product_list: list[str], task_id: int):

    # Lanzar contextos con delay para reducir carga en cpu
    await asyncio.sleep(5 * (task_id + 1))

    # Lista para almacenar filas de datos para exportar
    filas_para_excel = []

    # Fecha actual
    hoy = datetime.now()
    fecha_actual_str = hoy.strftime('%d/%m/%Y')


    # Crear contexto -----------------------------------------------------------------------------
    tab_driver = None
    max_context_retries = 5

    for attempt in range(max_context_retries):
        try:
            tab_driver = await driver_global.new_context()
            break
        except Exception as e:
            if attempt < max_context_retries - 1:
                print(f"🟡 Error al crear contexto para task id {task_id} (intento {attempt + 1}/{max_context_retries}): {e}")
                print("➡️ Reintentando la creación del contexto en 5 segundos.")
                await asyncio.sleep(10)
            else:
                print(f"🔴 No fue posible crear el contexto luego de {max_context_retries} intentos. Omitiendo task id {task_id}.")
                return None


    # Iniciar sesión -----------------------------------------------------------------------------

    # ✅ Cargar login
    await tab_driver.get("https://www.falabella.com/falabella-cl/myaccount/login", wait_load=True, timeout=60)

    # 🟢 Ingresar correo
    await send_keys_verificado(driver=tab_driver, by=By.ID, element="email", input_text=ACCOUNT_DATA[task_id]["user"], element_description="Mail", auto_refresh=True)

    # 🟢 Ingresar contraseña
    await send_keys_verificado(driver=tab_driver, by=By.ID, element="password", input_text=ACCOUNT_DATA[task_id]["pw"], element_description="Contraseña", auto_refresh=False)

    # 🟢 Click en 'Ingresar'
    await click_con_reintentos(driver=tab_driver, by=By.XPATH, element="//span[text()='Ingresar']", element_description='Ingresar', timeout = 10, max_retries=10, auto_refresh = False)

    try:

        # 🔎 Buscando si se requiere A2F
        await tab_driver.find_element(By.XPATH, "//p[text()='Confirma tu inicio de sesión']", timeout=5)
        print("🔒🔑 Se requiere A2F.")

        # 🟢 Click en 'Enviar código por correo'.
        await click_verificado_elemento(driver=tab_driver,
                                by=By.XPATH,
                                element="//button[.//p[contains(text(), 'Te enviaremos un código a')]]",
                                by_verifier=By.XPATH,
                                verifier_element="//p[contains(text(), 'Ingresa el código verificador')]",
                                element_description="Correo A2F",
                                elemento_actual=False,
                                auto_refresh=False)

        # 🟢 Ingresar código de verificación
        code = verification_code_email(ACCOUNT_DATA[task_id]["user"], ACCOUNT_DATA[task_id]["api"], action="read", email_index = 0, retry_delay_seconds=10)
        input_field = await tab_driver.find_element(By.ID, "otp-0", timeout=20)
        await input_field.send_keys(code)

        # 🟢 Click en 'Continuar'.
        await click_verificado_elemento(driver=tab_driver,
                                by=By.CLASS_NAME,
                                element="new-device-otp-form-module_confirm-button-falabella-enabled__YoPgq",
                                by_verifier=By.XPATH,
                                verifier_element="//span[contains(text(), 'Datos personales')] | //h1[contains(text(), 'Datos personales')]",
                                element_description="Continuar",
                                elemento_actual=False,
                                auto_refresh=False)

        print("🔓🔑 Inicio de sesión con A2F exitoso.")


    except NoSuchElementException:
        print("🔓🔑 Inicio de sesión exitoso.")

    # --------------------------------------------------------------------------------------------


    for product_id in product_list:

        print(f"\n--- Procesando Product ID: {product_id} ---")

        try:

            seller_name = ""
            pdp_compra_internacional = False
            pdp_envio_gratis_app = False

            # 🟢 Limpiar carro ----------------------------------------------------------------------------------------
            current_url = await tab_driver.current_url
            if current_url != 'https://www.falabella.com/falabella-cl/basket':
                await tab_driver.get("https://www.falabella.com/falabella-cl/basket", wait_load=True, timeout=60)
                print("🟢 Página de carro cargada.")

            try:
                await tab_driver.find_element(By.XPATH, "//h2[contains(text(), 'Tu Carro está vacío')]", timeout=5)
                print("🟢 El carro está vacío. Procediendo a agregar productos.")

            except NoSuchElementException:
                print("🟢 El carro no está vacío. Procediendo a eliminar productos existentes.")

                await seleccionar_productos_carro(driver=tab_driver)
                await delete_cart_item(driver=tab_driver)
            # ---------------------------------------------------------------------------------------------------------


            # ✅ Cargar la página del producto
            await tab_driver.get(f"https://www.falabella.com/falabella-cl/product/{product_id}", wait_load=True, timeout=60)


            try:
                await tab_driver.find_elements(By.ID, 'add-to-cart-button', timeout=10)
                print(f"🟢 Página de producto {product_id} cargada.")

                # 🟢 Click en 'Agregar al carro' en (PDP) -----------------------------------------------------------------
                await click_con_reintentos(driver=tab_driver, by=By.ID, element='add-to-cart-button', element_description='Agregar al carro (PDP)', timeout = 20, max_retries=5, auto_refresh = True)

            except Exception:

                # ✅ Página de producto notFound --------------------------------------------------------------------------
                current_url = await tab_driver.current_url
                if current_url == 'https://www.falabella.com/falabella-cl/notFound':
                    print("⏩ El producto ya no se encuentra disponible. Avanzando al siguiente.")

                    fila = {
                            "region": "",
                            "comuna": "",
                            "calle": "",
                            "numero": "",
                            "product_id": product_id,
                            "fecha_actual": fecha_actual_str,
                            "seller_name": seller_name,
                            "pdp_compra_internacional": pdp_compra_internacional,
                            "pdp_envio_gratis_app": pdp_envio_gratis_app,
                            "promesa": "Producto no disponible (notFound)",
                            "precio": "Producto no disponible (notFound)",
                            "free_shipping_label": False,
                            "envio_gratis_app": False,
                            "specificDate": "",
                            "dateRangeLB": "",
                            "dateRangeUB": ""
                        }

                    filas_para_excel.append(fila)

                    continue
                # ---------------------------------------------------------------------------------------------------------

                # ✅ Página de '¡Qué mal! Justo se agotó' -----------------------------------------------------------------
                try:
                    producto_agotado = await tab_driver.find_elements(By.XPATH, "//h2[contains(text(), 'Justo se agotó')]", timeout=5)

                    if len(producto_agotado) > 0:
                        print("⏩ El producto está agotado. Avanzando al siguiente.")

                        fila = {
                                "region": "",
                                "comuna": "",
                                "calle": "",
                                "numero": "",
                                "product_id": product_id,
                                "fecha_actual": fecha_actual_str,
                                "seller_name": seller_name,
                                "pdp_compra_internacional": pdp_compra_internacional,
                                "pdp_envio_gratis_app": pdp_envio_gratis_app,
                                "promesa": "Producto no disponible (¡Qué mal! Justo se agotó)",
                                "precio": "Producto no disponible (¡Qué mal! Justo se agotó)",
                                "free_shipping_label": False,
                                "envio_gratis_app": False,
                                "specificDate": "",
                                "dateRangeLB": "",
                                "dateRangeUB": ""
                            }

                        filas_para_excel.append(fila)

                        continue

                except NoSuchElementException:
                    pass
                # ---------------------------------------------------------------------------------------------------------

                # ✅ Problemas para acceder a la página ------------------------------------------------------------------
                max_tries = 5
                for attempt in range(max_tries):

                    try:
                        await tab_driver.find_elements(By.XPATH, "//span[text()='No se puede acceder a este sitio web']", timeout=5)
                    except NoSuchElementException:
                        break # Éxito, se logró acceder a la página

                    if attempt < max_tries:
                        print("🟡 Error al cargar la página: 'No se puede acceder a este sitio web'.")
                        print("➡️ Refrescando la página para reintentar.")
                        await tab_driver.refresh()
                        await asyncio.sleep(5)
                    else:
                        print("🔴 Se agotaron intentos para cargar la página.")

                        fila = {
                                "region": "",
                                "comuna": "",
                                "calle": "",
                                "numero": "",
                                "product_id": product_id,
                                "fecha_actual": fecha_actual_str,
                                "seller_name": seller_name,
                                "pdp_compra_internacional": pdp_compra_internacional,
                                "pdp_envio_gratis_app": pdp_envio_gratis_app,
                                "promesa": "Producto no disponible (No se pudo acceder al sitio web)",
                                "precio": "Producto no disponible (No se pudo acceder al sitio web)",
                                "free_shipping_label": False,
                                "envio_gratis_app": False,
                                "specificDate": "",
                                "dateRangeLB": "",
                                "dateRangeUB": ""
                            }

                        filas_para_excel.append(fila)

                        continue
            # ---------------------------------------------------------------------------------------------------------

            # 🔎 Datos en PDP  ----------------------------------------------------------------------------------------
            try:
                await tab_driver.find_element(By.XPATH, "//p[contains(@class, 'international-text') and contains(., 'Compra internacional')]")
                pdp_compra_internacional = True
                print("✅ Encontrado en PDP: 'Compra internacional'")
            except NoSuchElementException:
                pass

            try:
                await tab_driver.find_element(By.XPATH, "//span[contains(@class, 'pod-badges-item-PDP') and contains(., 'gratis') and contains(., 'app')]")
                pdp_envio_gratis_app = True
                print("✅ Encontrado en PDP: 'Envío gratis app'")
            except NoSuchElementException:
                pass

            try:
                seller_element = await tab_driver.find_element(By.ID, "testId-SellerInfo-sellerName")
                seller_span_element = await seller_element.find_element(By.TAG_NAME, "span")
                seller_name = await seller_span_element.text

                print("✅ Encontrado en PDP: 'Seller Name'")
            except NoSuchElementException:
                pass
            # ---------------------------------------------------------------------------------------------------------


            # ✅ Opciones extra ---------------------------------------------------------------------------------------
            try:
                print("🔎 Verificando si se puede acceder directamente al carro.")
                await tab_driver.find_element(By.CSS_SELECTOR, "a#linkButton[href='https://www.falabella.com/falabella-cl/basket']")

            # 🔎 Variantes --------------------------------------------------------------------------------------------
            except NoSuchElementException:
                print("⏳ Verificando opciones extra.")
                variant_selected = False
                button_text = ""

                # ✅ Operador telefonía -------------------------------------------------------------------------------
                try:
                    operator_container = await tab_driver.find_element(By.ID, "testId-Operator-container", timeout=2)
                    print("✅ Contenedor de 'Operador' encontrado.")

                    first_available_option = await operator_container.find_element(By.CSS_SELECTOR, "button.operator:not([disabled])")

                    button_text = await first_available_option.text
                    await tab_driver.execute_script("arguments[0].click();", first_available_option)
                    print(f"🟢 Se hizo click en la opción de operador: '{button_text}'")
                    variant_selected = True

                # ✅ Selector de talla --------------------------------------------------------------------------------
                except NoSuchElementException:
                    try:
                        size_container = await tab_driver.find_element(By.CSS_SELECTOR, "div.size-options", timeout=2)
                        print("✅ Contenedor de 'Talla' encontrado.")

                        first_available_option = await size_container.find_element(By.CSS_SELECTOR, "button.size-button:not([disabled])")

                        button_text = await first_available_option.text
                        await tab_driver.execute_script("arguments[0].click();", first_available_option)
                        print(f"🟢 Se hizo click en la opción de talla: '{button_text}'")
                        variant_selected = True

                    except NoSuchElementException:
                        pass

                # 🟢 Agregar al carro ------------------------------------------------------------------------------
                if variant_selected:
                    go_to_cart_button = await tab_driver.find_element(By.ID, "add-to-cart-button-lightbox", timeout=20)
                    await tab_driver.execute_script("arguments[0].click();", go_to_cart_button)
                    print("🟢 Click en 'Agregar al Carro (variant)'.")
                # ---------------------------------------------------------------------------------------------------------

                # ✅ Garantía extendida ----------------------------------------------------------------------------------
                try:
                    await tab_driver.find_element(By.XPATH, "//p[contains(., 'Protege tu producto')]", timeout=2)
                    print("✅ Opción de Garantía encontrado.")

                    continuar_sin_proteccion_btn = await tab_driver.find_element(By.XPATH, "//button[normalize-space()='Continuar sin protección']", timeout=2)
                    await tab_driver.execute_script("arguments[0].click();", continuar_sin_proteccion_btn)

                    print("🟢 Click en 'Continuar sin protección'.")

                except NoSuchElementException:
                    pass
                # -------------------------------------------------------------------------------------------------------------

            finally:
                # 🟢 Acceder al checkout --------------------------------------------------------------------------------------
                print("⏳ Accediendo manualmente a url del checkout.")
                await asyncio.sleep(2)
                await tab_driver.get('https://www.falabella.com/falabella-cl/checkout/delivery', wait_load=True)
            # -----------------------------------------------------------------------------------------------------------------

            # 🟢 Para cada producto, iterar para cada CEP ---------------------------------------------------------------------
            for address in ADDRESS_DATA:

                opciones_de_envio = []

                # 🟢 Productos no disponibles: click en 'Cambiar dirección' para cerrar pop-up --------------------------------
                try:
                    await asyncio.sleep(2)
                    print('🔍 Buscando pop-up')
                    await tab_driver.find_element(By.ID, "testId-modal-close", timeout=5)

                    await click_verificado_elemento(driver=tab_driver,
                                                    by=By.XPATH,
                                                    element="//*[@id='testId-button-secondary'] | //*[@datatestid='testId-button-secondary'] | //button[text()='Cambiar dirección'] | //button[@id='testId-button-secondary']",
                                                    by_verifier=By.XPATH,
                                                    verifier_element="/span[contains(text(), 'Productos no disponibles')]",
                                                    element_description="Cambiar dirección (pop-up)",
                                                    elemento_actual=True,
                                                    auto_refresh=False)
                except NoSuchElementException:
                    pass
                # -----------------------------------------------------------------------------------------------------------------

                # 🟢 Click en 'Cambiar dirección' ---------------------------------------------------------------------------------
                await click_verificado_elemento(driver=tab_driver,
                                                by=By.ID,
                                                element="clic_cambiar_fecha_ShippingAddressHolder",
                                                by_verifier=By.XPATH,
                                                verifier_element="//span[contains(text(), 'Selecciona una dirección')]",
                                                element_description="Cambiar dirección",
                                                elemento_actual=False,
                                                auto_refresh=False)

                # 🟢 Buscar y marcar Dirección ------------------------------------------------------------------------------------
                print(f"⏳ Buscando la dirección para: {address['calle']}, {address['numero']}")

                xpath_address_text = f"//span[contains(text(), '{address['calle']}, {address['numero']}')]"
                xpath_radio_button = "/ancestor::div[starts-with(@datatestid, 'testId-ShippingAddressModal-addressHolder-')]/descendant::span[starts-with(@datatestid, 'testId-ShippingAddressModal-radioButton-') and @class='chakra-radio__control css-1y9m0lj']"

                address_text_element = await tab_driver.find_element(By.XPATH, xpath_address_text, timeout=5)
                await tab_driver.execute_script("arguments[0].scrollIntoView(true);", address_text_element)
                await asyncio.sleep(0.5)
                selector_direccion = await tab_driver.find_element(By.XPATH, xpath_address_text + xpath_radio_button, timeout=5)
                await selector_direccion.click(move_to=True)
                print(f"🟢 Click exitoso en la dirección: {address['calle']}, {address['numero']}")

                # 🟢 Click en 'Seleccionar' dirección -----------------------------------------------------------------------------
                await click_verificado_elemento(driver=tab_driver,
                                                by=By.ID,
                                                element="testId-infoModalFooter-button",
                                                by_verifier=By.XPATH,
                                                verifier_element="//span[contains(text(), 'Selecciona una dirección')]",
                                                element_description="Seleccionar",
                                                elemento_actual=True,
                                                auto_refresh=False)

                print("⏳ Esperando recálculo de envío...")
                await asyncio.sleep(5)

                # ✅ Extracción de datos de envío ---------------------------------------------------------------------------------
                try:
                    await tab_driver.find_element(By.XPATH, '//p[contains(normalize-space(), "Envío a domicilio")]', timeout=20)
                    print("✅ Opción 'Envío a domicilio' encontrada.")

                except NoSuchElementException:
                    await tab_driver.find_element(By.XPATH, "//span[contains(text(), 'Productos no disponibles')] | //span[contains(text(), 'No disponible para la comuna')] | //p[contains(text(), 'Producto solo disponible en tienda.')]", timeout=20)
                    print("✅ Producto no disponible en CEP.")

                    fila = {
                            "region": address["region"],
                            "comuna": address["comuna"],
                            "calle": address["calle"],
                            "numero": address["numero"],
                            "product_id": product_id,
                            "fecha_actual": fecha_actual_str,
                            "seller_name": seller_name,
                            "pdp_compra_internacional": pdp_compra_internacional,
                            "pdp_envio_gratis_app": pdp_envio_gratis_app,
                            "promesa": "envío a domicilio no disponible",
                            "precio": "envío a domicilio no disponible",
                            "free_shipping_label": False,
                            "envio_gratis_app": False,
                            "specificDate": "",
                            "dateRangeLB": "",
                            "dateRangeUB": ""
                        }

                    filas_para_excel.append(fila)
                    print("🟢 El producto no está disponible para envío a domicilio.")
                    continue


                # 🔎 Opciones de envío ---------------------------------------------------------------------------------------------------------------------
                seccion_envio_domicilio = await tab_driver.find_element(By.XPATH, '//p[contains(normalize-space(), "Envío a domicilio")]/../..')
                hijos_directos = await seccion_envio_domicilio.find_elements(By.XPATH, "./div")

                contenedores_de_opciones = hijos_directos[1:]
                print(f"⌛ Se procesará(n) {len(contenedores_de_opciones)} opcion(es) de envío.")

                for i, opcion_contenedor in enumerate(contenedores_de_opciones):

                    # ✅ Variables de búsqueda en checkout -------------------------------------------------------------------------------------------------
                    promesa = ""
                    precio =  ""
                    free_shipping_label = False
                    envio_gratis_app = False

                    # ✅ Promesa de entrega ----------------------------------------------------------------------------------------------------------------
                    try:
                        # Fecha específica -----------------------------------------------------------------------------------------------------------------
                        promise_container = await opcion_contenedor.find_element(By.XPATH, ".//div[p[starts-with(@id, 'shipment-')]]", timeout=1)
                        raw_text = await promise_container.text
                        promesa = " ".join(raw_text.split()).replace(" ,", ",")
                    except NoSuchElementException:
                        # Rango de fechas ------------------------------------------------------------------------------------------------------------------
                        promise_container = await opcion_contenedor.find_element(By.ID, "shipment-option-homeDeliveryDateRange", timeout=1)
                        raw_text = await promise_container.text
                        promesa = " ".join(raw_text.split())

                    # ✅ Precio de envío ------------------------------------------------------------------------------------------------------------------
                    price_elem = await opcion_contenedor.find_element(By.CSS_SELECTOR, "span[data-testid='shipment-price']", timeout=1)
                    precio = await price_elem.text

                    # ✅ Envío gratis ---------------------------------------------------------------------------------------------------------------------
                    try:
                        await opcion_contenedor.find_element(By.CSS_SELECTOR, "span[data-testid='free-shipment-label']", timeout=1)
                        free_shipping_label = True
                    except NoSuchElementException:
                        pass

                    # ✅ Envío gratis en APP --------------------------------------------------------------------------------------------------------------
                    try:
                        await opcion_contenedor.find_element(By.CSS_SELECTOR, "div[data-testid='free-shipping-badge']", timeout=1)
                        envio_gratis_app = True
                    except NoSuchElementException:
                        pass

                    opciones_de_envio.append({
                        "opcion_nro": i + 1,
                        "promesa_entrega": promesa,
                        "precio_envio": precio,
                        "tiene_free_shipping_label": free_shipping_label,
                        "tiene_envio_gratis_app": envio_gratis_app
                    })
                # ------------------------------------------------------------------------------------------------------------------------------------------

                # Mejor opción de entrega ------------------------------------------------------------------------------------------------------------------
                await formato_promesa(opciones_de_envio, fecha_hoy = hoy)
                mejor_opcion = encontrar_mejor_shipping(opciones_de_envio)

                if mejor_opcion:
                    fila = {
                        "region": address["region"],
                        "comuna": address["comuna"],
                        "calle": address["calle"],
                        "numero": address["numero"],
                        "product_id": product_id,
                        "fecha_actual": fecha_actual_str,
                        "seller_name": seller_name,
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
                    print(f"🟢 Datos guardados para {address['calle']}, {address['numero']}.")
            # ----------------------------------------------------------------------------------------------------------------------------------------------

            # 🟢 Volver al carro ---------------------------------------------------------------------------------------------------------------------------
            print("🟢 Volviendo al carro...")
            await tab_driver.get("https://www.falabella.com/falabella-cl/basket", wait_load=True, timeout=60)

            # 🟢 Limpiar carro -----------------------------------------------------------------------------------------------------------------------------
            print("⏳ Eliminando producto del carro...")
            await seleccionar_productos_carro(driver=tab_driver)
            await delete_cart_item(driver=tab_driver)
            # ----------------------------------------------------------------------------------------------------------------------------------------------

            # ⏩ Imprimir resultados -----------------------------------------------------------------------------------------------------------------------
            print("\n--- Resultados: ---")
            print(json.dumps(filas_para_excel, indent=2, ensure_ascii=False))
            # ----------------------------------------------------------------------------------------------------------------------------------------------


        except Exception as e:
            print(f"❌ Ocurrió un error al procesar el producto {product_id}.")
            print(f"Detalles del error: {e}")
            print("---------------------------------------\n")
            print("⏩ Avanzando al siguiente producto.")
            continue
    # ------------------------------------------------------------------------------------------------------------------------------------------------------

    # 🟢 Al terminar todos los item_id en product_list, cerrar el contexto del navegador -------------------------------------------------------------------
    await tab_driver.close()
    print(f"✅ Contexto para task id {task_id} cerrado.")
    delete_all_falabella_notifications(ACCOUNT_DATA[task_id]["user"], ACCOUNT_DATA[task_id]["api"])
    return filas_para_excel
# ----------------------------------------------------------------------------------------------------------------------------------------------------------




async def main():
    global driver_global # pylint: disable=W0601
    start_time = time.time()

    # Instancia global del driver -------------------------------------------------------------------------------------------------------------------------
    driver_global = await setup_driver()
    await driver_global.close()
    print("🚀 Driver global iniciado.")

    # Procesamiento paralelo ------------------------------------------------------------------------------------------------------------------------------
    all_products_data = []
    concurrent_tasks = 2

    chunks = [[] for _ in range(concurrent_tasks)]
    for i, product_id in enumerate(product_ids):
        chunks[i % concurrent_tasks].append(product_id)

    tasks = []

    for i, chunk in enumerate(chunks):
        tasks.append(run_scraping(chunk, i))

    results = await asyncio.gather(*tasks)

    for product_data_list in results:
        if product_data_list:
            all_products_data.extend(product_data_list)

    # Guardar resultados en un archivo Excel --------------------------------------------------------------------------------------------------------------
    df = pd.DataFrame(all_products_data)
    df.to_excel("resultados_scraping.xlsx", index=False)

    # Finalizar el driver global --------------------------------------------------------------------------------------------------------------------------
    await driver_global.quit()
    print("✅ Cerrando instancia global del driver.")

    # Tiempo total de ejecución ---------------------------------------------------------------------------------------------------------------------------
    end_time = time.time()
    print(f"El tiempo total de ejecución fue de {(end_time - start_time)/60:.2f} minutos.")
# ----------------------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    asyncio.run(main())
