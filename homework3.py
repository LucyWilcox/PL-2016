"""############################################################
# HOMEWORK 3
#
# Team members:
Lucy Wilcox
Xiaofan Wu

# Emails:
lucy.wilcox@students.olin.edu
xiaozheng.xu@students.olin.edu

# Remarks:
We used the pyparsing docs
http://pyparsing.wikispaces.com/share/view/66929500 <- realized we could pass a function into setParseAction


"""
import sys
from pyparsing import Word, Literal,  Keyword, Forward, alphas, alphanums, OneOrMore, ZeroOrMore


#
# Expressions
#

class Exp (object):
    pass


class EValue (Exp):
    # Value literal (could presumably replace EInteger and EBoolean)
    def __init__ (self,v):
        self._value = v
    
    def __str__ (self):
        return "EValue({})".format(self._value)

    def eval (self,fun_dict):
        return self._value

    def substitute (self,id,new_e):
        return self


class EInteger (Exp):
    # Integer literal

    def __init__ (self,i):
        self._integer = i

    def __str__ (self):
        return "EInteger({})".format(self._integer)

    def eval (self,fun_dict):
        return VInteger(self._integer)

    def substitute (self,id,new_e):
        return self


class EBoolean (Exp):
    # Boolean literal

    def __init__ (self,b):
        self._boolean = b

    def __str__ (self):
        return "EBoolean({})".format(self._boolean)

    def eval (self,fun_dict):
        return VBoolean(self._boolean)

    def substitute (self,id,new_e):
        return self


class EPrimCall (Exp):
    # Call an underlying Python primitive, passing in Values
    #
    # simplifying the prim call
    # it takes an explicit function as first argument

    def __init__ (self,prim,es):
        self._prim = prim
        self._exps = es

    def __str__ (self):
        return "EPrimCall(<prim>,[{}])".format(",".join([ str(e) for e in self._exps]))

    def eval (self,fun_dict):
        vs = [ e.eval(fun_dict) for e in self._exps ]
        return apply(self._prim,vs)

    def substitute (self,id,new_e):
        new_es = [ e.substitute(id,new_e) for e in self._exps]
        return EPrimCall(self._prim,new_es)


class EIf (Exp):
    # Conditional expression

    def __init__ (self,e1,e2,e3):
        self._cond = e1
        self._then = e2
        self._else = e3

    def __str__ (self):
        return "EIf({},{},{})".format(self._cond,self._then,self._else)

    def eval (self,fun_dict):
        v = self._cond.eval(fun_dict)
        if v.type != "boolean":
            raise Exception ("Runtime error: condition not a Boolean")
        if v.value:
            return self._then.eval(fun_dict)
        else:
            return self._else.eval(fun_dict)

    def substitute (self,id,new_e):
        return EIf(self._cond.substitute(id,new_e),
                   self._then.substitute(id,new_e),
                   self._else.substitute(id,new_e))


class ELet (Exp):
    # local binding
    # allow multiple bindings
    # eager (call-by-avlue)
    def __init__ (self,bindings,e2):
        self._bindings = bindings
        self._e2 = e2

    def __str__ (self):
        return "ELet([{}],{})".format(",".join([ "({},{})".format(id,str(exp)) for (id,exp) in self._bindings ]),self._e2)

    def eval (self,fun_dict):
        # by this point, all substitutions in bindings expressions have happened already (!)
        new_e2 = self._e2
        for (id,e) in self._bindings:
            v = e.eval(fun_dict)
            new_e2 = new_e2.substitute(id,EValue(v))
        return new_e2.eval(fun_dict)

    def substitute (self,id,new_e):
        new_bindings = [ (bid,be.substitute(id,new_e)) for (bid,be) in self._bindings]
        if id in [ bid for (bid,_) in self._bindings]:
            return ELet(new_bindings, self._e2)
        return ELet(new_bindings, self._e2.substitute(id,new_e))


class EId (Exp):
    # identifier

    def __init__ (self,id):
        self._id = id

    def __str__ (self):
        return "EId({})".format(self._id)

    def eval (self,fun_dict):
        raise Exception("Runtime error: unknown identifier {}".format(self._id))

    def substitute (self,id,new_e):
        if id == self._id:
            return new_e
        return self


class ECall (Exp):
    # Call a defined function in the function dictionary

    def __init__ (self,name,es):
        self._name = name
        self._exps = es

    def __str__ (self):
        return "ECall({},[{}])".format(self._name,",".join([ str(e) for e in self._exps]))

    def eval (self,fun_dict):
        vs = [ e.eval(fun_dict) for e in self._exps ]
        params = fun_dict[self._name]["params"]
        body = fun_dict[self._name]["body"]
        if len(params) != len(vs):
            raise Exception("Runtime error: wrong number of argument calling function {}".format(self._name))
        for (val,p) in zip(vs,params):
            body = body.substitute(p,EValue(val))
        return body.eval(fun_dict)

    def substitute (self,var,new_e):
        new_es = [ e.substitute(var,new_e) for e in self._exps]
        return ECall(self._name,new_es)


    
#
# Values
#

class Value (object):
    pass


class VInteger (Value):
    # Value representation of integers
    
    def __init__ (self,i):
        self.value = i
        self.type = "integer"

    def __str__ (self):
        return str(self.value)

class VBoolean (Value):
    # Value representation of Booleans
    
    def __init__ (self,b):
        self.value = b
        self.type = "boolean"

    def __str__ (self):
        return "true" if self.value else "false"



# Primitive operations

def oper_plus (v1,v2): 
    if v1.type == "integer" and v2.type == "integer":
        return VInteger(v1.value + v2.value)
    raise Exception ("Runtime error: trying to add non-numbers")

def oper_minus (v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VInteger(v1.value - v2.value)
    raise Exception ("Runtime error: trying to subtract non-numbers")

def oper_times (v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VInteger(v1.value * v2.value)
    raise Exception ("Runtime error: trying to multiply non-numbers")

def oper_zero (v1):
    if v1.type == "integer":
        return VBoolean(v1.value==0)
    raise Exception ("Runtime error: type error in zero?")


# Initial primitives dictionary

INITIAL_FUN_DICT = {
    "+": {"params":["x","y"],
          "body":EPrimCall(oper_plus,[EId("x"),EId("y")])},
    "-": {"params":["x","y"],
          "body":EPrimCall(oper_minus,[EId("x"),EId("y")])},
    "*": {"params":["x","y"],
          "body":EPrimCall(oper_times,[EId("x"),EId("y")])},
    "zero?": {"params":["x"],
              "body":EPrimCall(oper_zero,[EId("x")])},
    "square": {"params":["x"],
               "body":ECall("*",[EId("x"),EId("x")])},
    "=": {"params":["x","y"],
          "body":ECall("zero?",[ECall("-",[EId("x"),EId("y")])])},
    "+1": {"params":["x"],
           "body":ECall("+",[EId("x"),EValue(VInteger(1))])},
    "sum_from_to": {"params":["s","e"],
                    "body":EIf(ECall("=",[EId("s"),EId("e")]),
                               EId("s"),
                               ECall("+",[EId("s"),
                                          ECall("sum_from_to",[ECall("+1",[EId("s")]),
                                                               EId("e")])]))}
}



##
## PARSER
##
# cf http://pyparsing.wikispaces.com/


def parse (input):
    # parse a string into an element of the abstract representation

    # Grammar:
    #
    # <expr> ::= <integer>
    #            true
    #            false
    #            <identifier>
    #            ( if <expr> <expr> <expr> )
    #            ( let ( ( <name> <expr> ) ) <expr )
    #            ( + <expr> <expr> )
    #            ( * <expr> <expr> )
    #
    def getDefunDict(result):
        name = result[2]
        params = result[4:-3]
        body = result[-2]
        newFun = {name: {"params": params, "body": body}}
        INITIAL_FUN_DICT.update(newFun)
        print "Function " + name + " added to the function dictionary"
        return {"result":"function", "name": name, "params": params, "body": body}

    idChars = alphas+"_+*-?!=<>"

    pIDENTIFIER = Word(idChars, idChars+"0123456789")
    pIDENTIFIER.setParseAction(lambda result: EId(result[0]))

    # A name is like an identifier but it does not return an EId...
    pNAME = Word(idChars,idChars+"0123456789")

    pINTEGER = Word("-0123456789","0123456789")
    pINTEGER.setParseAction(lambda result: EInteger(int(result[0])))

    pBOOLEAN = Keyword("true") | Keyword("false")
    pBOOLEAN.setParseAction(lambda result: EBoolean(result[0]=="true"))

    pEXPR = Forward()

    pDEFUN = "(" + Keyword("defun") + pNAME + "(" + OneOrMore(pNAME) + ")" + pEXPR + ")"
    pDEFUN.setParseAction(getDefunDict)

    pIF = "(" + Keyword("if") + pEXPR + pEXPR + pEXPR + ")"
    pIF.setParseAction(lambda result: EIf(result[2],result[3],result[4]))

    pBINDING = "(" + pNAME + pEXPR + ")"
    pBINDING.setParseAction(lambda result: (result[1],result[2]))

    pLET = "(" + Keyword("let") + "(" + OneOrMore(pBINDING) + ")" + pEXPR + ")"
    pLET.setParseAction(lambda result: ELet(result[3:-3], result[-2]))

    pPLUS = "(" + Keyword("+") + pEXPR + pEXPR + ")"
    pPLUS.setParseAction(lambda result: ECall("+",[result[2],result[3]]))

    pTIMES = "(" + Keyword("*") + pEXPR + pEXPR + ")"
    pTIMES.setParseAction(lambda result: ECall("*",[result[2],result[3]]))

    pUSERDEF = "(" + pNAME + OneOrMore(pEXPR) + ")"
    pUSERDEF.setParseAction(lambda result: ECall(result[1], result[2:-1]))

    pEXPR << (pINTEGER | pDEFUN | pBOOLEAN | pIDENTIFIER | pIF | pLET | pPLUS | pTIMES | pUSERDEF)

    result = pEXPR.parseString(input)[0]

    if type(result) == type(dict()):
        return result
    else:
        return {"result":"expression", "expr": result}

def shell ():
    # A simple shell
    # Repeatedly read a line of input, parse it, and evaluate the result

    print "Homework 3 - Calc Language"
    while True:
        inp = raw_input("calc> ")
        if not inp:
            return
        exp = parse(inp)
        if exp["result"] == "expression":
            print "Abstract representation:", exp["expr"]
            v = exp['expr'].eval(INITIAL_FUN_DICT)
            print v


def parse_natural(input):
    # parse a string into an element of the abstract representation

    # Grammar:
    #
    # <expr> ::= <integer>
    #            true
    #            false
    #            <identifier>
    #            ( if <expr> <expr> <expr> )
    #            ( let ( ( <name> <expr> ) ) <expr )
    #            ( + <expr> <expr> )
    #            ( * <expr> <expr> )
    #

    idChars = alphas+"_+*-?!=<>"

    pIDENTIFIER = Word(idChars, idChars+"0123456789")
    pIDENTIFIER.setParseAction(lambda result: EId(result[0]))

    # A name is like an identifier but it does not return an EId...
    pNAME = Word(idChars,idChars+"0123456789")

    pBOOLEAN = Keyword("true") | Keyword("false")
    pBOOLEAN.setParseAction(lambda result: EBoolean(result[0]=="true"))

    pINTEGER = Word("-0123456789","0123456789")
    pINTEGER.setParseAction(lambda result: EInteger(int(result[0])))

    pEXPR = Forward()

    pIF = "(" + Keyword("if") + pEXPR + ":" + pEXPR + "," + pEXPR + ")"
    pIF.setParseAction(lambda result: EIf(result[2],result[4],result[5]))

    pBINDING = pNAME + "=" + pEXPR + ZeroOrMore(",")
    pBINDING.setParseAction(lambda result: (result[0],result[2]))

    pLET = Keyword("let") + "(" + OneOrMore(pBINDING) + ")" + pEXPR
    pLET.setParseAction(lambda result: ELet(result[2:-2], result[-1]))

    pZERO = Keyword("zero?")  + pEXPR
    pZERO.setParseAction(lambda result: ECall("zero?",[result[1]]))

    pSQUARE = Keyword("square") + pEXPR
    pSQUARE.setParseAction(lambda result: ECall("square",[result[1]]))

    pPLUS = "(" + pEXPR + Keyword("+") + pEXPR + ")"
    pPLUS.setParseAction(lambda result: ECall("+",[result[1],result[3]]))

    pTIMES = "(" + pEXPR + Keyword("*") + pEXPR + ")"
    pTIMES.setParseAction(lambda result: ECall("*",[result[1],result[3]]))

    pMINUS = "(" + pEXPR + Keyword("-") + pEXPR + ")"
    pMINUS.setParseAction(lambda result: ECall("-",[result[1],result[3]]))

    pEXPR << (pBOOLEAN | pIF | pLET | pZERO | pSQUARE | pPLUS | pTIMES | pMINUS | pINTEGER | pIDENTIFIER)

    result = pEXPR.parseString(input)[0]

    if type(result) == type(dict()):
        return result
    else:
        return {"result":"expression", "expr": result}

def shell_natural ():
    # A simple shell
    # Repeatedly read a line of input, parse it, and evaluate the result

    print "Homework 3 - Calc Language"
    while True:
        inp = raw_input("calc/nat> ")
        if not inp:
            return
        exp = parse_natural(inp)
        if exp["result"] == "expression":
            print "Abstract representation:", exp
            v = exp['expr'].eval(INITIAL_FUN_DICT)
            print v

# increase stack size to let us call recursive functions quasi comfortably
sys.setrecursionlimit(10000)
shell_natural()
# shell() # run for old shell

"""
The following is our working syntax for 3a exapmle inputs/outputs.
"""

#let (x = 10) (x + 1)
#zero? 1
#zero? (10 - 10)
#(if zero? 0 : 1, 2)
#((if zero? 0 : 1, 2) + 55)
#((if zero? 1 : 1, 2) + 55)
#let (x = (4 + (5 * 6))) let (y = (x * 2)) square y
#((34 * 2) * (34 *2))

"""
Our code kept crashing when we tried to do something like define
pPLUS = pEXPR + Keyword("+") + pEXPR, so without the "(" and this would give
us errors. We're not sure exactly what is going on and tried to see if was an
issue with the order but could find a solution.

So expressions 5 + 5 is (5 + 5). If also requires () around it. We felt 
saying "if something : true-exp, false-exp" made sense syntactically. 
"""