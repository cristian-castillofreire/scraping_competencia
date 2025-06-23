import string
import imaplib
import email
import re
import random
import time
from datetime import datetime
from functools import reduce
import asyncio
from selenium_driverless.types.webelement import By
from selenium_driverless.types.webelement import NoSuchElementException
from selenium_driverless import webdriver

class MaxRetriesException(Exception):
    pass



# -----------------------------------------------------------------------------
# FUNCIÓN para marcar todos los items del carro
# -----------------------------------------------------------------------------
async def seleccionar_productos_carro(driver):
    print("⌛ Asegurándose que los productos esten seleccionados.")

    checkbox_elements = await driver.find_elements(By.XPATH, "//label[contains(@data-testid, 'parent-partial-checkout-')]//p[text()='Seleccionar todos']/ancestor::label//span[contains(@class, 'checkbox__control')]")
    total_checkboxes_found = len(checkbox_elements)

    print(f"🟢 Se encontraron {total_checkboxes_found} checkboxes.")


    if total_checkboxes_found > 0:
        for checkbox_element in checkbox_elements:

            is_checked = await checkbox_element.get_attribute("data-checked") is not None

            if not is_checked:
                print("🟢 Seleccionando producto.")
                await checkbox_element.click(move_to=True)
                await asyncio.sleep(5)


# -----------------------------------------------------------------------------
# FUNCIÓN para leer código de verificación A2F desde Gmail
# -----------------------------------------------------------------------------
def verification_code_email(my_email, my_password, imap_server="imap.gmail.com", action="read", email_index=0, max_retries=5, retry_delay_seconds=5):

    def extract_verification_code(body):
        phrase = "Si fuiste tú, ingresa este código verificador:"
        if phrase in body:
            match = re.search(rf"{re.escape(phrase)}\s*\n*\s*(\d{{6}})", body)
            if match:
                return match.group(1)
        return None

    target_sender = "notificaciones@mail.falabella.com"

    for attempt in range(max_retries):

        if attempt == 0:
            time.sleep(5)

        print(f"➡️ Intento {attempt + 1} de {max_retries} para obtener código A2F.")
        mail = None
        try:
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(my_email, my_password)
            mail.select("inbox")

            status, messages = mail.search(None, 'FROM', f'"{target_sender}"') # pylint: disable=W0612
            email_ids = messages[0].split()

            if email_ids:
                # List to store (email_datetime, email_id) tuples
                emails_with_dates = []

                for uid in email_ids:
                    # Fetch only the 'Date' header first to avoid downloading full emails unnecessarily
                    status, msg_data = mail.fetch(uid, "(BODY.PEEK[HEADER.FIELDS (Date)])")
                    raw_header = msg_data[0][1]
                    msg_header = email.message_from_bytes(raw_header)
                    date_header = msg_header['Date']

                    email_datetime = email.utils.parsedate_to_datetime(date_header)
                    emails_with_dates.append((email_datetime, uid))

                # Sort emails by their datetime, oldest to newest
                emails_with_dates.sort(key=lambda x: x[0])

                # Check if the desired email_index is valid for both actions
                if email_index >= len(emails_with_dates):
                    print(f"Email index {email_index} Fuera de rango. Se encontraron solo {len(emails_with_dates)} emails.")
                    return None # No email at this index to read or delete

                selected_email_id_bytes = emails_with_dates[email_index][1]
                selected_email_id = selected_email_id_bytes.decode() if isinstance(selected_email_id_bytes, bytes) else selected_email_id_bytes

                if action == "delete":
                    mail.store(selected_email_id, "+FLAGS", "\\Deleted")  # Mark for deletion
                    mail.expunge()  # Permanently delete marked emails
                    print("🟢 Email eliminado exitosamente.")
                    return None # Deletion successful, no code to return

                elif action == "read":
                    # Now fetch the full content of the selected email
                    status, msg_data = mail.fetch(selected_email_id, "(RFC822)")
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                code = extract_verification_code(body)
                                if code:
                                    print(f"🟢 Se encontró código A2F: {code}")
                                    return code
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()
                        code = extract_verification_code(body)
                        if code:
                            print(f"🟢 Se encontró código A2F: {code}")
                            return code
                else:
                    print(f"🔴 Invalid action specified: '{action}'. Action must be 'read' or 'delete'.")
                    return None
            else:
                print("🔴 No emails found from the specified sender.")
        except Exception as e:
            print(f"🔴 Ocurrió un error: {e}")
        finally:
            if mail:
                try:
                    mail.logout()
                except Exception as e:
                    print(f"🔴 Error during logout: {e}")

        if action == "read":
            print(f"🟡⏳ No se encontró correo con el código A2F. Reintentando en {retry_delay_seconds} segundos.")
            time.sleep(retry_delay_seconds)
        else:
            return None

    return None


# -----------------------------------------------------------------------------
# FUNCIÓN para eliminar todos los correos de Falabella
# -----------------------------------------------------------------------------
def delete_all_falabella_notifications(my_email, my_password, imap_server="imap.gmail.com"):
    target_sender = "notificaciones@mail.falabella.com"
    mail = None
    try:
        print(f"Connecting to IMAP server '{imap_server}' for {my_email} to delete emails from {target_sender}...")
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(my_email, my_password)
        mail.select("inbox") # Select the inbox folder

        print(f"Searching for emails from '{target_sender}'...")
        status, messages = mail.search(None, 'FROM', f'"{target_sender}"') # pylint: disable=W0612
        email_ids = messages[0].split()

        if email_ids:
            print(f"Found {len(email_ids)} emails from '{target_sender}'. Deleting them now...")
            deleted_count = 0
            for uid in email_ids:
                try:
                    # Mark the email for deletion
                    mail.store(uid, '+FLAGS', '\\Deleted')
                    deleted_count += 1
                except Exception as e:
                    print(f"Error marking email ID {uid.decode()} for deletion: {e}")

            # Permanently delete marked emails
            mail.expunge()
            print(f"Successfully deleted {deleted_count} emails from '{target_sender}'.")
            return True
        else:
            print(f"No emails found from '{target_sender}'. Nothing to delete.")
            return True

    except imaplib.IMAP4.error as e:
        print(f"IMAP login or operation error: {e}")
        print("Please check your email, password, and IMAP settings (e.g., enable IMAP, use app password for Gmail).")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False
    finally:
        if mail:
            try:
                mail.logout()
                print("Disconnected from IMAP server.")
            except Exception as e:
                print(f"Error during logout: {e}")


# -----------------------------------------------------------------------------
# FUNCIÓN para levantar el driver de Selenium
# -----------------------------------------------------------------------------
async def setup_driver():

    options = webdriver.ChromeOptions()
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
    # options.add_argument("--headless")
    options.add_argument(f"--user-agent={user_agent}")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-features=DisableLoadExtensionCommandLineSwitch")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-translate")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheet": 2,
        "profile.managed_default_content_settings.fonts": 2,
        "profile.managed_default_content_settings.popups": 2,
        "profile.managed_default_content_settings.plugins": 2,
        "profile.managed_default_content_settings.notifications": 2,
        "profile.managed_default_content_settings.automatic_downloads": 2,
    }
    options.add_experimental_option("prefs", prefs)

    return await webdriver.Chrome(options=options)


# -----------------------------------------------------------------------------
# FUNCIÓN para generar un email aleatorio
# -----------------------------------------------------------------------------
def generate_email():
    allowed_characters = string.ascii_lowercase + string.digits
    min_length = 30
    max_length = 40
    username_length = random.randint(min_length, max_length)
    random_username = ''.join(random.choice(allowed_characters) for _ in range(username_length))
    generated_email = f"{random_username}@gmail.com"

    return generated_email


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

            elemento_verificador = await driver.find_element(by_verifier, verifier_element, timeout=20)
            texto_verificador = await elemento_verificador.get_attribute('value')

            if texto_verificador == selected_item:
                print(f"🟢 {element_description} ingresado correctamente.")
                return True
            else:
                print("🟡 Problema al ingresar el texto.")
                if intento < max_retries - 1:
                    if auto_refresh:
                        print("➡️ Refrescando la página para reintentar.")
                        await driver.refresh()

        except Exception as e:
            print(f"🔴 Ocurrió un error inesperado: {e}")
            if intento < max_retries - 1:
                if auto_refresh:
                    print("➡️ Refrescando la página para reintentar.")
                    await driver.refresh()

    print(f"🔴 No se pudo avanzar en el formulario después de {max_retries} intentos.")
    raise MaxRetriesException("Se agotó el número de intentos para ingresar el texto.")


# -----------------------------------------------------------------------------
# FUNCIÓN para hacer click con reintentos capturando NoSuchElementException
# -----------------------------------------------------------------------------
async def click_con_reintentos(driver, by, element, element_description, timeout = 10, click_normal = True, max_retries=3, auto_refresh = False):
    for intento in range(max_retries):
        try:
            if intento > 0:
                print(f"🔄 Intento {intento + 1} de {max_retries}...")
            elemento = await driver.find_element(by, element, timeout)
            if click_normal:
                await elemento.click(move_to=True)
            else:
                await driver.execute_script("arguments[0].click();", elemento)

            print(f"🟢 Click en '{element_description}'.")
            return True

        except NoSuchElementException:
            print(f"🟡 Intento {intento + 1} fallido: No se encontró el elemento.")

            if intento < max_retries - 1:
                if auto_refresh:
                    print("➡️ Refrescando la página para reintentar.")
                    await driver.refresh()
                    await asyncio.sleep(2)
                else:
                    await asyncio.sleep(2)

    print(f"🔴 No se pudo hacer click en el elemento después de {max_retries} intentos.")
    raise MaxRetriesException(f"Se agotó el número de intentos para hacer click en '{element_description}'")


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
                    if auto_refresh:
                        print("➡️ Refrescando la página para reintentar.")
                        await driver.refresh()

        except Exception as e:
            print(f"🔴 Ocurrió un error inesperado: {e}")
            if intento < max_retries - 1:
                if auto_refresh:
                    print("➡️ Refrescando la página para reintentar.")
                    await driver.refresh()

    print(f"🔴 No se pudo avanzar en el formulario después de {max_retries} intentos.")
    raise MaxRetriesException("Se agotó el número de intentos para ingresar el texto.")



# -----------------------------------------------------------------------------
# FUNCIÓN para hacer click y verificar que un elemento dezaparezca/aparezca
# -----------------------------------------------------------------------------
async def click_verificado_elemento(driver, by, element, by_verifier, verifier_element, element_description='el elemento', click_normal = True, elemento_actual = True, max_retries=3, auto_refresh = True):

    for intento in range(max_retries):
        if intento > 0:
            print(f"🔄 Intento {intento + 1} de {max_retries}...")
        try:
            try:
                elemento = await driver.find_element(by, element, timeout=10)

                if click_normal:
                    await elemento.click(move_to=True)
                else:
                    await driver.execute_script("arguments[0].click();", elemento)

                print(f"🟢 Click en '{element_description}'.")
            except Exception:
                pass

            await asyncio.sleep(1)

            elemento_verificador = await driver.find_elements(by_verifier, verifier_element, timeout=20)

            if elemento_actual:
                if len(elemento_verificador) == 0:
                    # Lista vacía = no se encontró el elemento verificador = ¡ÉXITO!
                    print("🟢 Click verificado.")
                    return True
                else:
                    # La lista tiene elementos = sigue presente el elemento verificador = FALLO.
                    print("🟡 El proceso no avanzó.")
                    if intento < max_retries - 1:
                        if auto_refresh:
                            print("➡️ Refrescando la página para reintentar.")
                            await driver.refresh()
                        else:
                            await asyncio.sleep(2)
            else:
                if len(elemento_verificador) == 0:
                    # Lista vacía = no se encontró el elemento verificador = FALLO.
                    print("🟡 El proceso no avanzó.")
                    if intento < max_retries - 1:
                        if auto_refresh:
                            print("➡️ Refrescando la página para reintentar.")
                            await driver.refresh()
                        else:
                            await asyncio.sleep(2)
                else:
                    # La lista tiene elementos = apareció el elemento verificador = ¡ÉXITO!
                    print("🟢 Click verificado.")
                    return True



        except Exception as e:
            print(f"🔴 Ocurrió un error inesperado: {e}")
            if intento < max_retries - 1:
                if auto_refresh:
                    print("➡️ Refrescando la página para reintentar.")
                    await driver.refresh()


    print(f"🔴 No se pudo avanzar después de {max_retries} intentos.")
    raise MaxRetriesException(f"Se agotó el número de intentos para hacer click en '{element_description}'")





# -----------------------------------------------------------------------------
# FUNCIÓN para hacer click y verificar que cambie la URL
# -----------------------------------------------------------------------------
async def click_verificado_url(driver, by, element, target_url = '', element_description='el elemento', max_retries=2, auto_refresh = True):

    for intento in range(max_retries):
        try:
            current_url = await driver.current_url
            if current_url == target_url:
                return True

            if intento < (max_retries - 1):
                if intento > 0:
                    print(f"🔄 Intento {intento + 1} de {max_retries}...")
                elemento = await driver.find_element(by, element, timeout=10)
                await elemento.click(move_to=True)
                print(f"🟢 Click en '{element_description}'.")
            else:
                print("⏳ Accediendo manualmente a la url target.")
                await driver.get(target_url, wait_load=True)
                return True # Con esto ya está verificado el click.

            # await asyncio.sleep(1)

            # current_url = await driver.current_url
            # if current_url == target_url:
            #     return True

            print("🟡 La URL no cambió en este intento.")
            print(f"🔍 URL después del clic: {current_url}")

            if intento < max_retries - 1:
                if auto_refresh:
                    print("➡️ Refrescando la página para reintentar.")
                    await driver.refresh()

        except Exception as e:
            print(f"🔴 Ocurrió un error en el intento {intento + 1} al interactuar con '{element_description}': {e}")
            if intento < max_retries - 1:
                if auto_refresh:
                    print("➡️ Refrescando la página para reintentar.")
                    await driver.refresh()

    print(f"🔴 Se alcanzó el número máximo de reintentos sin éxito para '{element_description}'.")
    raise MaxRetriesException(f"Se agotó el número de intentos para hacer click en '{element_description}'")






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
