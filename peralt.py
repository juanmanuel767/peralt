#!/usr/bin/env python3
# ============================================
#   PERALT - Intérprete v1.0
#   Un lenguaje de programación en español
#   potente, simple y amigable con la IA
# ============================================

import re
import math
import sys
import os

# ─────────────────────────────────────────────
# TOKENS — Las piezas del lenguaje
# ─────────────────────────────────────────────

TOKEN_TIPOS = [
    ('COMENTARIO',    r'--[^\n]*'),
    ('DECIMAL',       r'\d+\.\d+'),
    ('NUMERO',        r'\d+'),
    ('TEXTO',         r'"[^"]*"'),
    ('VERDADERO',     r'\bverdadero\b'),
    ('FALSO',         r'\bfalso\b'),
    ('VACIO',         r'\bvacio\b'),
    ('DEFINIR',       r'\bdefinir\b'),
    ('MOSTRAR',       r'\bmostrar\b'),
    ('SI',            r'\bsi\b'),
    ('ENTONCES',      r'\bentonces\b'),
    ('SINO',          r'\bsino\b'),
    ('FIN',           r'\bfin\b'),
    ('REPETIR',       r'\brepetir\b'),
    ('VECES',         r'\bveces\b'),
    ('PARA',          r'\bpara\b'),
    ('CADA',          r'\bcada\b'),
    ('EN',            r'\ben\b'),
    ('HACER',         r'\bhacer\b'),
    ('FUNCION',       r'\bfuncion\b'),
    ('RETORNAR',      r'\bretornar\b'),
    ('CLASE',         r'\bclase\b'),
    ('NUEVO',         r'\bnuevo\b'),
    ('INTENTAR',      r'\bintentar\b'),
    ('CAPTURAR',      r'\bcapturar\b'),
    ('SIEMPRE',       r'\bsiempre\b'),
    ('USAR',          r'\busar\b'),
    ('LIBRERIA',      r'\blibreria\b'),
    ('Y',             r'\by\b'),
    ('O',             r'\bo\b'),
    ('NO',            r'\bno\b'),
    ('IGUAL',         r'=='),
    ('DIFERENTE',     r'!='),
    ('MAYOR_IGUAL',   r'>='),
    ('MENOR_IGUAL',   r'<='),
    ('MAYOR',         r'>'),
    ('MENOR',         r'<'),
    ('ASIGNAR',       r'='),
    ('MAS',           r'\+'),
    ('MENOS',         r'-'),
    ('POTENCIA',      r'\^'),
    ('MULT',          r'\*'),
    ('DIV',           r'/'),
    ('MODULO',        r'%'),
    ('LPAREN',        r'\('),
    ('RPAREN',        r'\)'),
    ('LBRACKET',      r'\['),
    ('RBRACKET',      r'\]'),
    ('LBRACE',        r'\{'),
    ('RBRACE',        r'\}'),
    ('COMA',          r','),
    ('PUNTO',         r'\.'),
    ('DOSPUNTOS',     r':'),
    ('IDENT',         r'[a-záéíóúüñA-ZÁÉÍÓÚÜÑ_][a-záéíóúüñA-ZÁÉÍÓÚÜÑ0-9_]*'),
    ('NUEVA_LINEA',   r'\n'),
    ('ESPACIO',       r'[ \t]+'),
]

class Token:
    def __init__(self, tipo, valor, linea=0):
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
    def __repr__(self):
        return f'Token({self.tipo}, {self.valor!r})'

# ─────────────────────────────────────────────
# LEXER — Convierte texto en tokens
# ─────────────────────────────────────────────

def lexer(codigo):
    tokens = []
    linea = 1
    pos = 0
    patron_maestro = '|'.join(f'(?P<{nombre}>{patron})' for nombre, patron in TOKEN_TIPOS)
    for m in re.finditer(patron_maestro, codigo):
        tipo = m.lastgroup
        valor = m.group()
        if tipo == 'ESPACIO' or tipo == 'COMENTARIO':
            pass
        elif tipo == 'NUEVA_LINEA':
            linea += 1
        elif tipo == 'DECIMAL':
            tokens.append(Token(tipo, float(valor), linea))
        elif tipo == 'NUMERO':
            tokens.append(Token(tipo, int(valor), linea))
        elif tipo == 'TEXTO':
            tokens.append(Token(tipo, valor[1:-1], linea))
        elif tipo in ('VERDADERO', 'FALSO', 'VACIO'):
            val = True if tipo == 'VERDADERO' else (False if tipo == 'FALSO' else None)
            tokens.append(Token(tipo, val, linea))
        else:
            tokens.append(Token(tipo, valor, linea))
    return tokens

# ─────────────────────────────────────────────
# PARSER — Convierte tokens en árbol (AST)
# ─────────────────────────────────────────────

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token('EOF', None)

    def consumir(self, tipo=None):
        tok = self.actual()
        if tipo and tok.tipo != tipo:
            raise SyntaxError(f"Se esperaba '{tipo}' pero se encontró '{tok.tipo}' ('{tok.valor}') en línea {tok.linea}")
        self.pos += 1
        return tok

    def parsear(self):
        nodos = []
        while self.actual().tipo != 'EOF':
            nodo = self.sentencia()
            if nodo:
                nodos.append(nodo)
        return nodos

    def sentencia(self):
        tok = self.actual()

        if tok.tipo == 'DEFINIR':
            return self.definir()
        elif tok.tipo == 'MOSTRAR':
            return self.mostrar()
        elif tok.tipo == 'SI':
            return self.si()
        elif tok.tipo == 'REPETIR':
            return self.repetir()
        elif tok.tipo == 'PARA':
            return self.para_cada()
        elif tok.tipo == 'FUNCION':
            return self.funcion()
        elif tok.tipo == 'RETORNAR':
            return self.retornar()
        elif tok.tipo == 'CLASE':
            return self.clase()
        elif tok.tipo == 'INTENTAR':
            return self.intentar()
        elif tok.tipo == 'USAR':
            return self.usar()
        elif tok.tipo == 'IDENT':
            return self.asignar_o_llamar()
        else:
            self.consumir()
            return None

    def definir(self):
        self.consumir('DEFINIR')
        nombre = self.consumir('IDENT').valor
        self.consumir('ASIGNAR')
        valor = self.expresion()
        return ('definir', nombre, valor)

    def mostrar(self):
        self.consumir('MOSTRAR')
        valor = self.expresion()
        return ('mostrar', valor)

    def si(self):
        self.consumir('SI')
        condicion = self.expresion()
        self.consumir('ENTONCES')
        cuerpo = []
        sino = []
        while self.actual().tipo not in ('SINO', 'FIN', 'EOF'):
            s = self.sentencia()
            if s: cuerpo.append(s)
        if self.actual().tipo == 'SINO':
            self.consumir('SINO')
            while self.actual().tipo not in ('FIN', 'EOF'):
                s = self.sentencia()
                if s: sino.append(s)
        self.consumir('FIN')
        return ('si', condicion, cuerpo, sino)

    def repetir(self):
        self.consumir('REPETIR')
        veces = self.expresion()
        self.consumir('VECES')
        cuerpo = []
        while self.actual().tipo not in ('FIN', 'EOF'):
            s = self.sentencia()
            if s: cuerpo.append(s)
        self.consumir('FIN')
        return ('repetir', veces, cuerpo)

    def para_cada(self):
        self.consumir('PARA')
        self.consumir('CADA')
        var = self.consumir('IDENT').valor
        self.consumir('EN')
        lista = self.expresion()
        self.consumir('HACER')
        cuerpo = []
        while self.actual().tipo not in ('FIN', 'EOF'):
            s = self.sentencia()
            if s: cuerpo.append(s)
        self.consumir('FIN')
        return ('para_cada', var, lista, cuerpo)

    def funcion(self):
        self.consumir('FUNCION')
        nombre = self.consumir('IDENT').valor
        self.consumir('LPAREN')
        params = []
        while self.actual().tipo != 'RPAREN':
            params.append(self.consumir('IDENT').valor)
            if self.actual().tipo == 'COMA':
                self.consumir('COMA')
        self.consumir('RPAREN')
        self.consumir('HACER')
        cuerpo = []
        while self.actual().tipo not in ('FIN', 'EOF'):
            s = self.sentencia()
            if s: cuerpo.append(s)
        self.consumir('FIN')
        return ('funcion', nombre, params, cuerpo)

    def retornar(self):
        self.consumir('RETORNAR')
        valor = self.expresion()
        return ('retornar', valor)

    def clase(self):
        self.consumir('CLASE')
        nombre = self.consumir('IDENT').valor
        self.consumir('HACER')
        cuerpo = []
        while self.actual().tipo not in ('FIN', 'EOF'):
            s = self.sentencia()
            if s: cuerpo.append(s)
        self.consumir('FIN')
        return ('clase', nombre, cuerpo)

    def intentar(self):
        self.consumir('INTENTAR')
        cuerpo = []
        while self.actual().tipo not in ('CAPTURAR', 'FIN', 'EOF'):
            s = self.sentencia()
            if s: cuerpo.append(s)
        capturar = []
        var_error = 'error'
        siempre = []
        if self.actual().tipo == 'CAPTURAR':
            self.consumir('CAPTURAR')
            var_error = self.consumir('IDENT').valor
            while self.actual().tipo not in ('SIEMPRE', 'FIN', 'EOF'):
                s = self.sentencia()
                if s: capturar.append(s)
        if self.actual().tipo == 'SIEMPRE':
            self.consumir('SIEMPRE')
            while self.actual().tipo not in ('FIN', 'EOF'):
                s = self.sentencia()
                if s: siempre.append(s)
        self.consumir('FIN')
        return ('intentar', cuerpo, var_error, capturar, siempre)

    def usar(self):
        self.consumir('USAR')
        nombre = self.consumir('IDENT').valor
        return ('usar', nombre)

    def asignar_o_llamar(self):
        nombre = self.consumir('IDENT').valor
        # acceso a propiedad o método
        while self.actual().tipo == 'PUNTO':
            self.consumir('PUNTO')
            attr = self.consumir('IDENT').valor
            if self.actual().tipo == 'LPAREN':
                self.consumir('LPAREN')
                args = []
                while self.actual().tipo != 'RPAREN':
                    args.append(self.expresion())
                    if self.actual().tipo == 'COMA':
                        self.consumir('COMA')
                self.consumir('RPAREN')
                return ('llamar_metodo', nombre, attr, args)
            nombre = ('acceso', nombre, attr)
        if self.actual().tipo == 'ASIGNAR':
            self.consumir('ASIGNAR')
            valor = self.expresion()
            return ('asignar', nombre, valor)
        elif self.actual().tipo == 'LPAREN':
            self.consumir('LPAREN')
            args = []
            while self.actual().tipo != 'RPAREN':
                args.append(self.expresion())
                if self.actual().tipo == 'COMA':
                    self.consumir('COMA')
            self.consumir('RPAREN')
            return ('llamar', nombre, args)
        return ('expr_stmt', ('ident', nombre))

    # ── Expresiones ──

    def expresion(self):
        return self.expr_logica()

    def expr_logica(self):
        izq = self.expr_comparacion()
        while self.actual().tipo in ('Y', 'O'):
            op = self.consumir().valor
            der = self.expr_comparacion()
            izq = ('binop', op, izq, der)
        return izq

    def expr_comparacion(self):
        if self.actual().tipo == 'NO':
            self.consumir('NO')
            return ('no', self.expr_comparacion())
        izq = self.expr_suma()
        while self.actual().tipo in ('IGUAL','DIFERENTE','MAYOR','MENOR','MAYOR_IGUAL','MENOR_IGUAL'):
            op = self.consumir().valor
            der = self.expr_suma()
            izq = ('binop', op, izq, der)
        return izq

    def expr_suma(self):
        izq = self.expr_mult()
        while self.actual().tipo in ('MAS', 'MENOS'):
            op = self.consumir().valor
            der = self.expr_mult()
            izq = ('binop', op, izq, der)
        return izq

    def expr_mult(self):
        izq = self.expr_potencia()
        while self.actual().tipo in ('MULT', 'DIV', 'MODULO'):
            op = self.consumir().valor
            der = self.expr_potencia()
            izq = ('binop', op, izq, der)
        return izq

    def expr_potencia(self):
        base = self.expr_primaria()
        if self.actual().tipo == 'POTENCIA':
            self.consumir('POTENCIA')
            exp = self.expr_potencia()
            return ('binop', '^', base, exp)
        return base

    def expr_primaria(self):
        tok = self.actual()

        if tok.tipo in ('NUMERO', 'DECIMAL'):
            self.consumir()
            return ('literal', tok.valor)
        elif tok.tipo == 'TEXTO':
            self.consumir()
            return ('texto', tok.valor)
        elif tok.tipo in ('VERDADERO', 'FALSO', 'VACIO'):
            self.consumir()
            return ('literal', tok.valor)
        elif tok.tipo == 'NUEVO':
            self.consumir('NUEVO')
            nombre = self.consumir('IDENT').valor
            self.consumir('LPAREN')
            self.consumir('RPAREN')
            return ('nuevo', nombre)
        elif tok.tipo == 'LBRACKET':
            return self.lista()
        elif tok.tipo == 'LBRACE':
            return self.mapa()
        elif tok.tipo == 'LPAREN':
            self.consumir('LPAREN')
            expr = self.expresion()
            self.consumir('RPAREN')
            return expr
        elif tok.tipo == 'IDENT':
            nombre = self.consumir('IDENT').valor
            # acceso encadenado
            nodo = ('ident', nombre)
            while self.actual().tipo == 'PUNTO':
                self.consumir('PUNTO')
                attr = self.consumir('IDENT').valor
                if self.actual().tipo == 'LPAREN':
                    self.consumir('LPAREN')
                    args = []
                    while self.actual().tipo != 'RPAREN':
                        args.append(self.expresion())
                        if self.actual().tipo == 'COMA':
                            self.consumir('COMA')
                    self.consumir('RPAREN')
                    nodo = ('llamar_metodo_expr', nodo, attr, args)
                else:
                    nodo = ('acceso_expr', nodo, attr)
            if self.actual().tipo == 'LPAREN' and nodo[0] == 'ident':
                self.consumir('LPAREN')
                args = []
                while self.actual().tipo != 'RPAREN':
                    args.append(self.expresion())
                    if self.actual().tipo == 'COMA':
                        self.consumir('COMA')
                self.consumir('RPAREN')
                return ('llamar_expr', nombre, args)
            return nodo
        else:
            self.consumir()
            return ('literal', None)

    def lista(self):
        self.consumir('LBRACKET')
        elementos = []
        while self.actual().tipo != 'RBRACKET':
            elementos.append(self.expresion())
            if self.actual().tipo == 'COMA':
                self.consumir('COMA')
        self.consumir('RBRACKET')
        return ('lista', elementos)

    def mapa(self):
        self.consumir('LBRACE')
        pares = []
        while self.actual().tipo != 'RBRACE':
            clave = self.consumir('IDENT').valor
            self.consumir('DOSPUNTOS')
            valor = self.expresion()
            pares.append((clave, valor))
            if self.actual().tipo == 'COMA':
                self.consumir('COMA')
        self.consumir('RBRACE')
        return ('mapa', pares)

# ─────────────────────────────────────────────
# ENTORNO — Guarda variables y funciones
# ─────────────────────────────────────────────

class Entorno:
    def __init__(self, padre=None):
        self.vars = {}
        self.padre = padre

    def obtener(self, nombre):
        if nombre in self.vars:
            return self.vars[nombre]
        if self.padre:
            return self.padre.obtener(nombre)
        raise NameError(f"Variable '{nombre}' no definida")

    def definir(self, nombre, valor):
        self.vars[nombre] = valor

    def asignar(self, nombre, valor):
        if nombre in self.vars:
            self.vars[nombre] = valor
        elif self.padre:
            self.padre.asignar(nombre, valor)
        else:
            self.vars[nombre] = valor

# ─────────────────────────────────────────────
# CLASES PERALT
# ─────────────────────────────────────────────

class ClasePeralt:
    def __init__(self, nombre, cuerpo, entorno):
        self.nombre = nombre
        self.cuerpo = cuerpo
        self.entorno = entorno

class InstanciaPeralt:
    def __init__(self, clase):
        self.clase = clase
        self.atributos = {}

class RetornarExcepcion(Exception):
    def __init__(self, valor):
        self.valor = valor

# ─────────────────────────────────────────────
# LIBRERÍAS BUILT-IN
# ─────────────────────────────────────────────

import datetime, random, urllib.request, json, urllib.error

class LibMatematica:
    PI = math.pi
    E  = math.e
    @staticmethod
    def seno(x): return math.sin(math.radians(x))
    @staticmethod
    def coseno(x): return math.cos(math.radians(x))
    @staticmethod
    def tangente(x): return math.tan(math.radians(x))
    @staticmethod
    def raiz(x): return math.sqrt(x)
    @staticmethod
    def potencia(x, y): return math.pow(x, y)
    @staticmethod
    def piso(x): return math.floor(x)
    @staticmethod
    def techo(x): return math.ceil(x)
    @staticmethod
    def abs(x): return abs(x)
    @staticmethod
    def redondear(x): return round(x)
    @staticmethod
    def logaritmo(x): return math.log(x)
    @staticmethod
    def maximo(*args): return max(args)
    @staticmethod
    def minimo(*args): return min(args)

class LibFecha:
    @staticmethod
    def ahora():
        n = datetime.datetime.now()
        return f"{n.day}/{n.month}/{n.year} {n.hour:02d}:{n.minute:02d}:{n.second:02d}"
    @staticmethod
    def hoy():
        n = datetime.date.today()
        return f"{n.day}/{n.month}/{n.year}"
    @staticmethod
    def hora():
        n = datetime.datetime.now()
        return f"{n.hour:02d}:{n.minute:02d}:{n.second:02d}"
    @staticmethod
    def anno(): return datetime.date.today().year
    @staticmethod
    def mes(): return datetime.date.today().month
    @staticmethod
    def dia(): return datetime.date.today().day

class LibTexto:
    @staticmethod
    def mayusculas(t): return str(t).upper()
    @staticmethod
    def minusculas(t): return str(t).lower()
    @staticmethod
    def longitud(t): return len(str(t))
    @staticmethod
    def contiene(t, sub): return sub in str(t)
    @staticmethod
    def reemplazar(t, viejo, nuevo): return str(t).replace(viejo, nuevo)
    @staticmethod
    def separar(t, sep=","): return str(t).split(sep)
    @staticmethod
    def unir(lista, sep=""): return sep.join(str(x) for x in lista)
    @staticmethod
    def recortar(t): return str(t).strip()
    @staticmethod
    def empieza_con(t, sub): return str(t).startswith(sub)
    @staticmethod
    def termina_con(t, sub): return str(t).endswith(sub)
    @staticmethod
    def repetir(t, n): return str(t) * int(n)
    @staticmethod
    def invertir(t): return str(t)[::-1]

class LibLista:
    @staticmethod
    def ordenar(lista): return sorted(lista)
    @staticmethod
    def ordenar_inverso(lista): return sorted(lista, reverse=True)
    @staticmethod
    def longitud(lista): return len(lista)
    @staticmethod
    def agregar(lista, elem): lista.append(elem); return lista
    @staticmethod
    def primero(lista): return lista[0] if lista else None
    @staticmethod
    def ultimo(lista): return lista[-1] if lista else None
    @staticmethod
    def contiene(lista, elem): return elem in lista
    @staticmethod
    def invertir(lista): return list(reversed(lista))
    @staticmethod
    def sumar(lista): return sum(lista)
    @staticmethod
    def promedio(lista): return sum(lista)/len(lista) if lista else 0
    @staticmethod
    def maximo(lista): return max(lista)
    @staticmethod
    def minimo(lista): return min(lista)
    @staticmethod
    def unico(lista): return list(dict.fromkeys(lista))

class LibAzar:
    @staticmethod
    def numero(minimo=0, maximo=100): return random.randint(int(minimo), int(maximo))
    @staticmethod
    def decimal(minimo=0.0, maximo=1.0): return random.uniform(minimo, maximo)
    @staticmethod
    def elegir(lista): return random.choice(lista)
    @staticmethod
    def mezclar(lista): random.shuffle(lista); return lista
    @staticmethod
    def dado(caras=6): return random.randint(1, int(caras))
    @staticmethod
    def moneda(): return "cara" if random.random() > 0.5 else "sello"

class LibArchivos:
    @staticmethod
    def leer(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f: return f.read()
        except Exception as e: raise Exception(f"No se pudo leer '{ruta}': {e}")
    @staticmethod
    def escribir(ruta, contenido):
        try:
            with open(ruta, "w", encoding="utf-8") as f: f.write(str(contenido))
            return True
        except Exception as e: raise Exception(f"No se pudo escribir '{ruta}': {e}")
    @staticmethod
    def agregar(ruta, contenido):
        try:
            with open(ruta, "a", encoding="utf-8") as f: f.write(str(contenido) + "\n")
            return True
        except Exception as e: raise Exception(f"No se pudo agregar a '{ruta}': {e}")
    @staticmethod
    def existe(ruta): return os.path.exists(ruta)
    @staticmethod
    def borrar(ruta):
        try: os.remove(ruta); return True
        except Exception as e: raise Exception(f"No se pudo borrar '{ruta}': {e}")

class LibRed:
    @staticmethod
    def obtener(url):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Peralt/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.read().decode("utf-8")
        except Exception as e: raise Exception(f"Error de red: {e}")
    @staticmethod
    def obtener_json(url):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Peralt/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e: raise Exception(f"Error de red: {e}")

LIBRERIAS = {
    "matematica": LibMatematica,
    "fecha":      LibFecha,
    "texto":      LibTexto,
    "lista":      LibLista,
    "azar":       LibAzar,
    "archivos":   LibArchivos,
    "red":        LibRed,
}

# ─────────────────────────────────────────────
# INTÉRPRETE — Ejecuta el AST
# ─────────────────────────────────────────────

class Interprete:
    def __init__(self):
        self.entorno_global = Entorno()
        self._cargar_builtins()

    def _cargar_builtins(self):
        self.entorno_global.definir('raiz', lambda x: math.sqrt(x))
        self.entorno_global.definir('abs', lambda x: abs(x))
        self.entorno_global.definir('redondear', lambda x: round(x))
        self.entorno_global.definir('longitud', lambda x: len(x))
        self.entorno_global.definir('tipo', lambda x: type(x).__name__)
        self.entorno_global.definir('numero', lambda x: float(x) if '.' in str(x) else int(x))
        self.entorno_global.definir('texto', lambda x: str(x))

    def ejecutar(self, nodos, entorno=None):
        if entorno is None:
            entorno = self.entorno_global
        resultado = None
        for nodo in nodos:
            resultado = self.evaluar(nodo, entorno)
        return resultado

    def evaluar(self, nodo, entorno):
        if nodo is None:
            return None

        tipo = nodo[0]

        if tipo == 'literal':
            return nodo[1]

        elif tipo == 'texto':
            # interpolación de variables {nombre}
            val = nodo[1]
            def reemplazar(m):
                var = m.group(1)
                try:
                    return str(entorno.obtener(var))
                except:
                    return m.group(0)
            return re.sub(r'\{(\w+)\}', reemplazar, val)

        elif tipo == 'ident':
            return entorno.obtener(nodo[1])

        elif tipo == 'definir':
            val = self.evaluar(nodo[2], entorno)
            entorno.definir(nodo[1], val)
            return val

        elif tipo == 'asignar':
            nombre = nodo[1]
            val = self.evaluar(nodo[2], entorno)
            if isinstance(nombre, tuple) and nombre[0] == 'acceso':
                obj = entorno.obtener(nombre[1])
                if isinstance(obj, InstanciaPeralt):
                    obj.atributos[nombre[2]] = val
                return val
            entorno.asignar(nombre, val)
            return val

        elif tipo == 'mostrar':
            val = self.evaluar(nodo[1], entorno)
            print(val)
            return val

        elif tipo == 'binop':
            op = nodo[1]
            izq = self.evaluar(nodo[2], entorno)
            der = self.evaluar(nodo[3], entorno)
            ops = {
                '+': lambda a,b: a+b, '-': lambda a,b: a-b,
                '*': lambda a,b: a*b, '/': lambda a,b: a/b,
                '%': lambda a,b: a%b, '^': lambda a,b: a**b,
                '==': lambda a,b: a==b, '!=': lambda a,b: a!=b,
                '>': lambda a,b: a>b,  '<': lambda a,b: a<b,
                '>=': lambda a,b: a>=b,'<=': lambda a,b: a<=b,
                'y': lambda a,b: a and b, 'o': lambda a,b: a or b,
            }
            return ops[op](izq, der)

        elif tipo == 'no':
            return not self.evaluar(nodo[1], entorno)

        elif tipo == 'si':
            cond = self.evaluar(nodo[1], entorno)
            nuevo_env = Entorno(entorno)
            if cond:
                return self.ejecutar(nodo[2], nuevo_env)
            elif nodo[3]:
                return self.ejecutar(nodo[3], nuevo_env)

        elif tipo == 'repetir':
            veces = int(self.evaluar(nodo[1], entorno))
            for _ in range(veces):
                try:
                    self.ejecutar(nodo[2], entorno)
                except RetornarExcepcion as r:
                    return r.valor

        elif tipo == 'para_cada':
            var = nodo[1]
            lista = self.evaluar(nodo[2], entorno)
            for elem in lista:
                nuevo_env = Entorno(entorno)
                nuevo_env.definir(var, elem)
                try:
                    self.ejecutar(nodo[3], nuevo_env)
                except RetornarExcepcion as r:
                    return r.valor

        elif tipo == 'lista':
            return [self.evaluar(e, entorno) for e in nodo[1]]

        elif tipo == 'mapa':
            return {k: self.evaluar(v, entorno) for k, v in nodo[1]}

        elif tipo == 'funcion':
            entorno.definir(nodo[1], ('fn', nodo[2], nodo[3], entorno))
            return None

        elif tipo == 'retornar':
            raise RetornarExcepcion(self.evaluar(nodo[1], entorno))

        elif tipo == 'llamar':
            fn = entorno.obtener(nodo[1])
            args = [self.evaluar(a, entorno) for a in nodo[2]]
            return self._llamar_funcion(fn, args)

        elif tipo == 'llamar_expr':
            fn = entorno.obtener(nodo[1])
            args = [self.evaluar(a, entorno) for a in nodo[2]]
            return self._llamar_funcion(fn, args)

        elif tipo == 'expr_stmt':
            return self.evaluar(nodo[1], entorno)

        elif tipo == 'clase':
            cls = ClasePeralt(nodo[1], nodo[2], entorno)
            entorno.definir(nodo[1], cls)
            return None

        elif tipo == 'nuevo':
            cls = entorno.obtener(nodo[1])
            inst = InstanciaPeralt(cls)
            # ejecutar cuerpo de clase para definir atributos
            nuevo_env = Entorno(cls.entorno)
            nuevo_env.definir('yo', inst)
            for sentencia in cls.cuerpo:
                if sentencia[0] == 'definir':
                    val = self.evaluar(sentencia[2], nuevo_env)
                    inst.atributos[sentencia[1]] = val
                elif sentencia[0] == 'funcion':
                    inst.atributos[sentencia[1]] = ('metodo', sentencia[2], sentencia[3], inst)
            return inst

        elif tipo == 'acceso_expr':
            obj = self.evaluar(nodo[1], entorno)
            attr = nodo[2]
            if isinstance(obj, InstanciaPeralt):
                return obj.atributos.get(attr)
            elif hasattr(obj, attr):
                return getattr(obj, attr)
            raise AttributeError(f"'{attr}' no encontrado")

        elif tipo == 'llamar_metodo_expr':
            obj = self.evaluar(nodo[1], entorno)
            attr = nodo[2]
            args = [self.evaluar(a, entorno) for a in nodo[3]]
            if isinstance(obj, InstanciaPeralt):
                fn = obj.atributos.get(attr)
                return self._llamar_funcion(fn, args, instancia=obj)
            elif hasattr(obj, attr):
                return getattr(obj, attr)(*args)

        elif tipo == 'llamar_metodo':
            obj = entorno.obtener(nodo[1])
            attr = nodo[2]
            args = [self.evaluar(a, entorno) for a in nodo[3]]
            if isinstance(obj, InstanciaPeralt):
                fn = obj.atributos.get(attr)
                return self._llamar_funcion(fn, args, instancia=obj)
            elif hasattr(obj, attr):
                return getattr(obj, attr)(*args)

        elif tipo == 'intentar':
            try:
                nuevo_env = Entorno(entorno)
                self.ejecutar(nodo[1], nuevo_env)
            except RetornarExcepcion:
                raise
            except Exception as e:
                nuevo_env = Entorno(entorno)
                nuevo_env.definir(nodo[2], str(e))
                self.ejecutar(nodo[3], nuevo_env)
            finally:
                if nodo[4]:
                    self.ejecutar(nodo[4], Entorno(entorno))

        elif tipo == 'usar':
            nombre = nodo[1]
            if nombre in LIBRERIAS:
                entorno.definir(nombre, LIBRERIAS[nombre])
            else:
                raise ImportError(f"Librería '{nombre}' no encontrada")

        return None

    def _llamar_funcion(self, fn, args, instancia=None):
        if callable(fn):
            return fn(*args)
        elif isinstance(fn, tuple):
            if fn[0] == 'fn':
                _, params, cuerpo, closure_env = fn
                nuevo_env = Entorno(closure_env)
                for p, a in zip(params, args):
                    nuevo_env.definir(p, a)
                try:
                    self.ejecutar(cuerpo, nuevo_env)
                except RetornarExcepcion as r:
                    return r.valor
            elif fn[0] == 'metodo':
                _, params, cuerpo, inst = fn
                nuevo_env = Entorno(inst.clase.entorno)
                nuevo_env.definir('yo', inst)
                for p, a in zip(params, args):
                    nuevo_env.definir(p, a)
                try:
                    self.ejecutar(cuerpo, nuevo_env)
                except RetornarExcepcion as r:
                    return r.valor
        return None

# ─────────────────────────────────────────────
# MODO INTERACTIVO (REPL)
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# EJECUTAR ARCHIVO .peralt
# ─────────────────────────────────────────────

def ejecutar_archivo(ruta):
    with open(ruta, 'r', encoding='utf-8') as f:
        codigo = f.read()
    tokens = lexer(codigo)
    parser = Parser(tokens)
    ast = parser.parsear()
    interprete = Interprete()
    interprete.ejecutar(ast)

# ─────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────

def error_bonito(e, archivo=None):
    """Muestra errores de forma clara y amigable"""
    print()
    print("╔══════════════════════════════════════════╗")
    print("║           ❌ ERROR EN PERALT             ║")
    print("╠══════════════════════════════════════════╣")

    msg = str(e)

    if isinstance(e, SyntaxError):
        print(f"║  Tipo:    Error de sintaxis              ║")
        print(f"╠══════════════════════════════════════════╣")
        print(f"║  {msg[:42].ljust(42)}║")
        print(f"╠══════════════════════════════════════════╣")
        print(f"║  💡 Revisá que cada bloque tenga 'fin'  ║")
        print(f"║     y que uses 'definir' para variables  ║")

    elif isinstance(e, NameError):
        print(f"║  Tipo:    Variable no encontrada         ║")
        print(f"╠══════════════════════════════════════════╣")
        print(f"║  {msg[:42].ljust(42)}║")
        print(f"╠══════════════════════════════════════════╣")
        print(f"║  💡 ¿Escribiste 'definir' antes de      ║")
        print(f"║     usar la variable?                    ║")

    elif isinstance(e, ZeroDivisionError):
        print(f"║  Tipo:    División por cero              ║")
        print(f"╠══════════════════════════════════════════╣")
        print(f"║  No podés dividir un número por cero    ║")
        print(f"╠══════════════════════════════════════════╣")
        print(f"║  💡 Verificá el valor del divisor        ║")

    elif isinstance(e, TypeError):
        print(f"║  Tipo:    Tipos incompatibles            ║")
        print(f"╠══════════════════════════════════════════╣")
        print(f"║  {msg[:42].ljust(42)}║")
        print(f"╠══════════════════════════════════════════╣")
        print(f"║  💡 ¿Estás mezclando números y texto?    ║")

    elif isinstance(e, ImportError):
        print(f"║  Tipo:    Librería no encontrada         ║")
        print(f"╠══════════════════════════════════════════╣")
        print(f"║  {msg[:42].ljust(42)}║")
        print(f"╠══════════════════════════════════════════╣")
        print(f"║  💡 Librerías disponibles: matematica    ║")

    else:
        print(f"║  Tipo:    Error general                  ║")
        print(f"╠══════════════════════════════════════════╣")
        print(f"║  {msg[:42].ljust(42)}║")

    if archivo:
        print(f"╠══════════════════════════════════════════╣")
        nombre = os.path.basename(archivo)[:42]
        print(f"║  Archivo: {nombre.ljust(32)}║")

    print("╚══════════════════════════════════════════╝")
    print()

def repl():
    print("=" * 50)
    print("  🟡 PERALT v1.0 — Lenguaje de Programación")
    print("  Escribe 'salir' para terminar")
    print("=" * 50)
    interprete = Interprete()
    while True:
        try:
            linea = input("peralt> ").strip()
            if linea.lower() == 'salir':
                print("¡Hasta luego!")
                break
            if not linea:
                continue
            tokens = lexer(linea)
            parser = Parser(tokens)
            ast = parser.parsear()
            interprete.ejecutar(ast)
        except Exception as e:
            error_bonito(e)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            ejecutar_archivo(sys.argv[1])
        except Exception as e:
            error_bonito(e, sys.argv[1])
            sys.exit(1)
    else:
        repl()
