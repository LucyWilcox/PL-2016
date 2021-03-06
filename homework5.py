############################################################
# HOMEWORK 5
#
# Team members:
# Lucy Wilcox
# Xiaofan Wu
# Emails:
# lucy.wilcox@students.olin.edu
# wuxiaofan1996@gmail.com
# Remarks:
#



import sys

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

    def eval (self,env):
        return self._value

    
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

    def eval (self,env):
        vs = [ e.eval(env) for e in self._exps ]
        return apply(self._prim,vs)


class EIf (Exp):
    # Conditional expression

    def __init__ (self,e1,e2,e3):
        self._cond = e1
        self._then = e2
        self._else = e3

    def __str__ (self):
        return "EIf({},{},{})".format(self._cond,self._then,self._else)

    def eval (self,env):
        v = self._cond.eval(env)
        if v.type != "boolean":
            raise Exception ("Runtime error: condition not a Boolean")
        if v.value:
            return self._then.eval(env)
        else:
            return self._else.eval(env)


class EId (Exp):
    # identifier

    def __init__ (self,id):
        self._id = id

    def __str__ (self):
        return "EId({})".format(self._id)

    def eval (self,env):
        for (id,v) in env:
            if self._id == id:
                return v
        raise Exception("Runtime error: unknown identifier {}".format(self._id))


class ECall (Exp):
    # Call a defined function in the function dictionary

    def __init__ (self,fun,exps):
        self._fun = fun
        self._args = exps

    def __str__ (self):
        return "ECall({},{})".format(str(self._fun),str(self._args))

    def eval (self,env):
        print self._fun,"before eval"
        f = self._fun.eval(env)
        if f.type != "function":
            raise Exception("Runtime error: trying to call a non-function")
        new_args = [x.eval(env) for x in self._args]
        new_vals = zip(f.params, new_args)
        new_env = new_vals + f.env
        return f.body.eval(new_env)

class EFunction (Exp):
    # Creates an anonymous function

    def __init__ (self,params,body,name = ""):
        self._params = params
        self._body = body
        self._name = name

    def __str__ (self):
        return "EFunction([{}],{})".format(self._params,str(self._body))

    def eval (self,env):
        if self._name!="":
            env.insert(0,(self._name, VClosure(self._params,self._body,env)))
        return VClosure(self._params,self._body,env)

    
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

    
class VClosure (Value):
    
    def __init__ (self,params,body,env):
        self.params = params
        self.body = body
        self.env = env
        self.type = "function"

    def __str__ (self):
        return "<function {} {}>".format(self.params,str(self.body))


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


# Initial environment

# this initial environment works with Q1 when you've completed it

def initial_env ():
    env = []
    env.insert(0,
        ("+",
         VClosure(["x","y"],EPrimCall(oper_plus,
                                      [EId("x"),EId("y")]),
                  env)))
    env.insert(0,
        ("-",
         VClosure(["x","y"],EPrimCall(oper_minus,
                                      [EId("x"),EId("y")]),
                  env)))
    env.insert(0,
        ("*",
         VClosure(["x","y"],EPrimCall(oper_times,
                                      [EId("x"),EId("y")]),
                  env)))
    env.insert(0,
        ("zero?",
         VClosure(["x"],EPrimCall(oper_zero,
                                  [EId("x")]),
                  env)))
    env.insert(0,
        ("square",
         VClosure(["x"],ECall(EId("*"),[EId("x"),EId("x")]),
                  env)))
    env.insert(0,
        ("=",
         VClosure(["x","y"],ECall(EId("zero?"),
                                  [ECall(EId("-"),[EId("x"),EId("y")])]),
                  env)))
    env.insert(0,
        ("+1",
         VClosure(["x"],ECall(EId("+"),[EId("x"),EValue(VInteger(1))]),
                  env)))
    return env

##
## PARSER
##
# cf http://pyparsing.wikispaces.com/

from pyparsing import Word, Literal, ZeroOrMore, OneOrMore, Keyword, Forward, alphas, alphanums


def letUnimplementedError ():
    raise Exception ("ERROR: let functionality not implemented yet")

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
    #            (function ( <name> ) <expr> )
    #            ( <expr> <expr> )
    #
    # <definition> ::= ( defun <name> ( <name> ) <expr> )
    #
    def letToFun(result):
        func = result[5]
        binds = result[3]
        params = []
        vals = []
        for p, v in binds:
            params.append(p)
            vals.append(v)
        return ECall(EFunction(params, func), vals)

    def eFunName(result):
        varName = result[2]
        variables = result[4:-3]
        expression = result[-2]
        return EFunction(variables, expression, varName)

    idChars = alphas+"_+*-~/?!=<>"

    pIDENTIFIER = Word(idChars, idChars+"0123456789")
    pIDENTIFIER.setParseAction(lambda result: EId(result[0]))

    # A name is like an identifier but it does not return an EId...
    pNAME = Word(idChars,idChars+"0123456789")

    pINTEGER = Word("0123456789")
    pINTEGER.setParseAction(lambda result: EValue(VInteger(int(result[0]))))

    pBOOLEAN = Keyword("true") | Keyword("false")
    pBOOLEAN.setParseAction(lambda result: EValue(VBoolean(result[0]=="true")))

    pEXPR = Forward()

    pIF = "(" + Keyword("if") + pEXPR + pEXPR + pEXPR + ")"
    pIF.setParseAction(lambda result: EIf(result[2],result[3],result[4]))

    pBINDING = "(" + pNAME + pEXPR + ")"
    pBINDING.setParseAction(lambda result: (result[1],result[2]))

    pBINDINGS = OneOrMore(pBINDING)
    pBINDINGS.setParseAction(lambda result: [ result ])

    pLET = "(" + Keyword("let") + "(" + pBINDINGS + ")" + pEXPR + ")"
    pLET.setParseAction(letToFun)

    pCALL = "(" + pEXPR + OneOrMore(pEXPR) + ")"
    pCALL.setParseAction(lambda result: ECall(result[1],result[2:-1]))

    pFUN = "(" + Keyword("function") + "(" + OneOrMore(pNAME) + ")" + pEXPR + ")"
    pFUN.setParseAction(lambda result: EFunction(result[3:-3],result[-2]))

    pFUNNAME = "(" + Keyword("function") + pNAME + "(" + OneOrMore(pNAME) + ")" + pEXPR + ")"
    pFUNNAME.setParseAction(eFunName)

    pEXPR << (pINTEGER | pBOOLEAN | pIDENTIFIER | pIF | pLET | pFUN | pFUNNAME | pCALL)

    # can't attach a parse action to pEXPR because of recursion, so let's duplicate the parser
    pTOPEXPR = pEXPR.copy()
    pTOPEXPR.setParseAction(lambda result: {"result":"expression","expr":result[0]})

    pDEFUN = "(" + Keyword("defun") + pNAME + "(" + OneOrMore(pNAME) + ")" + pEXPR + ")"
    pDEFUN.setParseAction(lambda result: {"result":"function",
                                          "name":result[2],
                                          "params":result[4:-3],
                                          "body":result[-2]})
    pTOP = (pDEFUN | pTOPEXPR)

    result = pTOP.parseString(input)[0]
    return result    # the first element of the result is the expression


def shell ():
    # A simple shell
    # Repeatedly read a line of input, parse it, and evaluate the result

    print "Homework 5 - Func Language"
    print "#quit to quit"
    env = []

    env = initial_env()
    while True:
        inp = raw_input("func> ")

        if inp == "#quit":
            return

        try:
            result = parse(inp)

            if result["result"] == "expression":
                exp = result["expr"]
                print "Abstract representation:", exp
                v = exp.eval(env)
                print v

            elif result["result"] == "function":
                # the top-level environment is special, it is shared
                # amongst all the top-level closures so that all top-level
                # functions can refer to each other
                env.insert(0,(result["name"],VClosure(result["params"],result["body"],env)))
                print "Function {} added to top-level environment".format(result["name"])

        except Exception as e:
            print "Exception: {}".format(e)

# increase stack size to let us call recursive functions quasi comfortably
sys.setrecursionlimit(10000)


def initial_env_curry ():
    env = []
    env.insert(0,
        ("+",
         VClosure(["x"],EFunction("y",EPrimCall(oper_plus,
                                              [EId("x"),EId("y")])),
                  env)))
    env.insert(0,
        ("-",
         VClosure(["x"],EFunction("y",EPrimCall(oper_minus,
                                              [EId("x"),EId("y")])),
                  env)))
    env.insert(0,
        ("*",
         VClosure(["x"],EFunction("y",EPrimCall(oper_times,
                                              [EId("x"),EId("y")])),
                  env)))
    env.insert(0,
        ("zero?",
         VClosure(["x"],EPrimCall(oper_zero,
                                         [EId("x")]),
                           env)))
    env.insert(0,
        ("square",
         VClosure(["x"],ECall(ECall(EId("*"),[EId("x")]),
                            [EId("x")]),
                  env)))
    env.insert(0,
        ("=",
         VClosure(["x"],EFunction("y",ECall(EId("zero?"),
                                          [ECall(ECall(EId("-"),[EId("x")]),
                                                 [EId("y")])])),
                  env)))
    env.insert(0,
        ("+1",
         VClosure(["x"],ECall(ECall(EId("+"),[EId("x")]),
                            [EValue(VInteger(1))]),
                  env)))
    return env

def parse_curry (input):
    def letToFun(result):
        func = result[5]
        binds = result[3]
        params = []
        vals = []
        for p, v in binds:
            params.append(p)
            vals.append(v)
        return ECall(EFunction(params, func), vals)

    def eCallHelper(first, rest):
        if len(rest) == 1:
            return ECall(first, rest)
        else:
            return ECall(eCallHelper(first, rest[:-1]), [rest[-1]])

    def eCall(result):
        first = result[1]
        rest = result[2:-1]
        return eCallHelper(first, rest)
        
    def eFunHelper(variables, expression):
        if len(variables) == 1:
            return EFunction(variables[0], expression)
        else:
            return EFunction(variables[0], eFunHelper(variables[1:], expression))

    def eFun(result):
        variables = result[3:-3]
        expression = result[-2]
        return eFunHelper(variables, expression)

    def eDeFun(result):
        expression = result[-2]
        variables = result[5:-3]
        build_list = ["(","function","("]
        build_list.extend(variables)
        build_list.extend([")",result[-2],")"])
        fun = eFun(build_list)
        return {"result":"function",
                "name":result[2],
                "params":result[4],
                "body":fun}

    idChars = alphas+"_+*-~/?!=<>"

    pIDENTIFIER = Word(idChars, idChars+"0123456789")
    pIDENTIFIER.setParseAction(lambda result: EId(result[0]))

    # A name is like an identifier but it does not return an EId...
    pNAME = Word(idChars,idChars+"0123456789")

    pINTEGER = Word("0123456789")
    pINTEGER.setParseAction(lambda result: EValue(VInteger(int(result[0]))))

    pBOOLEAN = Keyword("true") | Keyword("false")
    pBOOLEAN.setParseAction(lambda result: EValue(VBoolean(result[0]=="true")))

    pEXPR = Forward()

    pIF = "(" + Keyword("if") + pEXPR + pEXPR + pEXPR + ")"
    pIF.setParseAction(lambda result: EIf(result[2],result[3],result[4]))

    pBINDING = "(" + pNAME + pEXPR + ")"
    pBINDING.setParseAction(lambda result: (result[1],result[2]))

    pBINDINGS = OneOrMore(pBINDING)
    pBINDINGS.setParseAction(lambda result: [ result ])

    pLET = "(" + Keyword("let") + "(" + pBINDINGS + ")" + pEXPR + ")"
    pLET.setParseAction(letToFun)

    pCALL = "(" + pEXPR + OneOrMore(pEXPR) + ")"
    pCALL.setParseAction(eCall)
    # pCALL.setParseAction(lambda result: ECall(result[1],result[2:-1]))

    pFUN = "(" + Keyword("function") + "(" + OneOrMore(pNAME) + ")" + pEXPR + ")"
    pFUN.setParseAction(eFun)

    # pFUN.setParseAction(lambda result: EFunction(result[3:-3],result[-2]))

    pEXPR << (pINTEGER | pBOOLEAN | pIDENTIFIER | pIF | pLET | pFUN | pCALL)

    # can't attach a parse action to pEXPR because of recursion, so let's duplicate the parser
    pTOPEXPR = pEXPR.copy()
    pTOPEXPR.setParseAction(lambda result: {"result":"expression","expr":result[0]})

    pDEFUN = "(" + Keyword("defun") + pNAME + "(" + OneOrMore(pNAME) + ")" + pEXPR + ")"
    pDEFUN.setParseAction(eDeFun)

    pTOP = (pDEFUN | pTOPEXPR)

    result = pTOP.parseString(input)[0]
    return result    # the first element of the result is the expression


def shell_curry ():

    print "Homework 5 - Func Language"
    print "#quit to quit"
    env = initial_env_curry()
    
    while True:
        inp = raw_input("func/curry> ")

        if inp == "#quit":
            return

        try:
            result = parse_curry(inp)

            if result["result"] == "expression":
                exp = result["expr"]
                print "Abstract representation:", exp
                v = exp.eval(env)
                print v

            elif result["result"] == "function":
                # the top-level environment is special, it is shared
                # amongst all the top-level closures so that all top-level
                # functions can refer to each other
                env.insert(0,(result["name"],VClosure([result["params"]],result["body"],env)))
                print "Function {} added to top-level environment".format(result["name"])

        except Exception as e:
            print "Exception: {}".format(e)

shell()
# shell_curry()
