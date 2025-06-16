
from datetime import datetime
from functools import reduce


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