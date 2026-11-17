def factor(tokens, pos):
    if pos >= len(tokens):
        return -1

    if tokens[pos] == "not":
        return factor(tokens, pos + 1)

    if tokens[pos] == "True" or tokens[pos] == "False":
        return pos + 1

    if tokens[pos] == "(":
        nuevo = expresion_logica(tokens, pos + 1)

        if nuevo != -1 and nuevo < len(tokens):
            if tokens[nuevo] == ")":
                return nuevo + 1

    return -1


def termino(tokens, pos):
    pos = factor(tokens, pos)

    if pos == -1:
        return -1

    while pos < len(tokens) and tokens[pos] == "and":
        pos = factor(tokens, pos + 1)

        if pos == -1:
            return -1

    return pos


def expresion_logica(tokens, pos):
    pos = termino(tokens, pos)

    if pos == -1:
        return -1

    while pos < len(tokens) and tokens[pos] == "or":
        pos = termino(tokens, pos + 1)

        if pos == -1:
            return -1

    return pos


def analizar_logica(texto):
    tokens = texto.replace("(", " ( ")
    tokens = tokens.replace(")", " ) ")
    tokens = tokens.split()

    if len(tokens) == 0:
        return False

    resultado = expresion_logica(tokens, 0)
    return resultado == len(tokens)

def es_nombre(texto):
    if texto == "":
        return False

    reservadas = [
        "for", "in", "else", "def", "return",
        "if", "while", "True", "False",
        "and", "or", "not", "pass", "break",
        "continue", "class", "import",
        "from", "as", "lambda"
    ]

    if texto in reservadas:
        return False

    if not (texto[0].isalpha() or texto[0] == "_"):
        return False

    for letra in texto:
        if not (letra.isalnum() or letra == "_"):
            return False

    return True


def expresion_basica(texto):
    texto = texto.strip()

    if texto == "":
        return False

    if texto[-1] in "+-*/=," or ";" in texto:
        return False

    pila = []
    comilla = ""
    escapado = False

    for letra in texto:
        if comilla != "":
            if letra == "\\" and not escapado:
                escapado = True
            elif letra == comilla and not escapado:
                comilla = ""
            else:
                escapado = False

        elif letra == "'" or letra == '"':
            comilla = letra

        elif letra == "(" or letra == "[":
            pila.append(letra)

        elif letra == ")":
            if len(pila) == 0 or pila.pop() != "(":
                return False

        elif letra == "]":
            if len(pila) == 0 or pila.pop() != "[":
                return False

    return comilla == "" and len(pila) == 0


def sentencia_simple(texto, tipo):
    texto = texto.strip()

    if texto == "pass":
        return True

    if tipo == "for":
        if texto == "break" or texto == "continue":
            return True

    if tipo == "def":
        if texto == "return":
            return True

        if texto.startswith("return "):
            return expresion_basica(texto[7:])

    if texto.startswith("print(") and texto.endswith(")"):
        contenido = texto[6:-1]

        if contenido.strip() == "":
            return True

        return expresion_basica(contenido)

    if "=" in texto and "==" not in texto:
        partes = texto.split("=", 1)

        nombre = partes[0].strip()
        valor = partes[1]

        return es_nombre(nombre) and expresion_basica(valor)

    return False

def validar_cuerpo(lineas, en_la_misma_linea, permite_else, tipo):
    cantidad = 0
    cantidad_else = 0
    en_else = False
    inline = en_la_misma_linea.strip()

    if inline != "":
        if not sentencia_simple(inline, tipo):
            return False
        cantidad = 1

    for linea in lineas:
        if linea.strip() == "":
            continue

        espacios = len(linea) - len(linea.lstrip(" "))
        limpia = linea.strip()

        if permite_else and espacios == 0:
            if limpia.startswith("else:"):
                if en_else or cantidad == 0:
                    return False

                en_else = True
                resto = limpia[5:].strip()

                if resto != "":
                    if not sentencia_simple(resto, tipo):
                        return False
                    cantidad_else = 1

                continue

        # Los bloques utilizan 4 espacios.
        if espacios != 4:
            return False

        if inline != "" and not en_else:
            return False

        if not sentencia_simple(limpia, tipo):
            return False

        if en_else:
            cantidad_else += 1
        else:
            cantidad += 1

    if cantidad == 0:
        return False

    if en_else and cantidad_else == 0:
        return False

    return True


def separar_codigo(codigo):
    lineas = codigo.strip("\n").split("\n")

    while len(lineas) > 0 and lineas[0].strip() == "":
        lineas.pop(0)

    if len(lineas) == 0:
        return "", "", []

    if lineas[0].startswith(" "):
        return "", "", []

    if ":" not in lineas[0]:
        return "", "", []

    partes = lineas[0].split(":", 1)

    cabeza = partes[0].strip()
    inline = partes[1].strip()
    cuerpo = lineas[1:]

    return cabeza, inline, cuerpo

def analizar_for(codigo):
    cabeza, inline, cuerpo = separar_codigo(codigo)

    if not cabeza.startswith("for "):
        return False

    datos = cabeza[4:].split(" in ", 1)

    if len(datos) != 2:
        return False

    if not expresion_basica(datos[1]):
        return False

    nombres = datos[0].split(",")

    for nombre in nombres:
        if not es_nombre(nombre.strip()):
            return False

    return validar_cuerpo(cuerpo, inline, True, "for")

def analizar_def(codigo):
    cabeza, inline, cuerpo = separar_codigo(codigo)

    if not cabeza.startswith("def "):
        return False

    if not cabeza.endswith(")"):
        return False

    datos = cabeza[4:]
    inicio = datos.find("(")

    if inicio == -1:
        return False

    nombre_funcion = datos[:inicio].strip()

    if not es_nombre(nombre_funcion):
        return False

    parametros = datos[inicio + 1:-1].strip()

    if parametros != "":
        nombres = parametros.split(",")
        usados = []

        for nombre in nombres:
            nombre = nombre.strip()

            if not es_nombre(nombre):
                return False

            if nombre in usados:
                return False

            usados.append(nombre)

    return validar_cuerpo(cuerpo, inline, False, "def")