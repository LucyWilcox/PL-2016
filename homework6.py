############################################################
# Simple imperative language
# C-like surface syntac
# with S-expression syntax for expressions
# (no recursive closures)
#
"""

Notes: single quotes ' and double quotes " within a string 
must be preceeded by a & so 
"testing a &"string&"" -> "testing a "string""

Q1 tests:

var not = (function (x) (if x false true));
for var x = 10; (not (zero? x)); x <- (- x 1); { print x; }
10
9
8
7
6
5
4
3
2
1

Q2 tests:

var s = "string &"test&'";
print s; # string "test'
print (length s); # 13
print (substring s 1 4); # tri
print (substring s 1 11); # tring "tes
var m = (substring s 0 4);
print m; # stri
print (concat m s); # stristring "test'
print (startswith s m); # true
print (startswith m s); # false
var t1 = "ris";
print (startswith s t1); # false
var t2 = "est&'";
print (endswith s t2); # true
print (endswith s t1); # false
var yn = "YES no";
print (lower yn); # yes no
print (upper yn); # YES NO

Q3 tests:
procedure foo (x y) print x;
foo(1 2); # 1
procedure bar (x y z) print (+ x (+ y z));
bar (1 2 5); #8
bar (1 2 (+ 5 1)) #9
"""
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


class ELet (Exp):
    # local binding
    # allow multiple bindings
    # eager (call-by-avlue)

    def __init__ (self,bindings,e2):
        self._bindings = bindings
        self._e2 = e2

    def __str__ (self):
        return "ELet([{}],{})".format(",".join([ "({},{})".format(id,str(exp)) for (id,exp) in self._bindings ]),self._e2)

    def eval (self,env):
        new_env = [ (id,e.eval(env)) for (id,e) in self._bindings] + env
        return self._e2.eval(new_env)

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
        return "ECall({},[{}])".format(str(self._fun),",".join(str(e) for e in self._args))

    def eval (self,env):
        f = self._fun.eval(env)
        if f.type != "function":
            raise Exception("Runtime error: trying to call a non-function")
        args = [ e.eval(env) for e in self._args]
        print args,f.params
        if len(args) != len(f.params):
            raise Exception("Runtime error: argument # mismatch in call")
        if hasattr(f.env, "type"):
            if f.env.type == "array":
                new_env = zip(f.params,args) + f.env.methods
        else:
            new_env = zip(f.params,args) + f.env
        return f.body.eval(new_env)


class EFunction (Exp):
    # Creates an anonymous function

    def __init__ (self,params,body):
        self._params = params
        self._body = body

    def __str__ (self):
        return "EFunction([{}],{})".format(",".join(self._params),str(self._body))

    def eval (self,env):
        return VClosure(self._params,self._body,env)


class ERefCell (Exp):
    # this could (should) be turned into a primitive
    # operation.  (WHY?)

    def __init__ (self,initialExp):
        self._initial = initialExp

    def __str__ (self):
        return "ERefCell({})".format(str(self._initial))

    def eval (self,env):
        v = self._initial.eval(env)
        return VRefCell(v)

class EDo (Exp):

    def __init__ (self,exps):
        self._exps = exps

    def __str__ (self):
        return "EDo([{}])".format(",".join(str(e) for e in self._exps))

    def eval (self,env):
        # default return value for do when no arguments
        v = VNone()
        for e in self._exps:
            v = e.eval(env)
        return v

class EWhile (Exp):

    def __init__ (self,cond,exp):
        self._cond = cond
        self._exp = exp

    def __str__ (self):
        return "EWhile({},{})".format(str(self._cond),str(self._exp))

    def eval (self,env):
        c = self._cond.eval(env)
        if c.type != "boolean":
            raise Exception ("Runtime error: while condition not a Boolean")
        while c.value:
            self._exp.eval(env)
            c = self._cond.eval(env)
            if c.type != "boolean":
                raise Exception ("Runtime error: while condition not a Boolean")
        return VNone()

class EFor (Exp):

    def __init__ (self, init, cond, incre, exp):
        self._init = init
        self._cond = cond
        self._incre = incre
        self._exp = exp

    def __str__ (self):
        return "EFor({},{},{},{})".format(str(self._init), str(self._cond), str(self._incre), str(self._exp))

    def eval (self,env):
        if self._init[0] != ";":
            for i in range(len(self._init[0]) - 1):
                v = self._init[i][1].eval(env)
                env.insert(0,(self._init[i][0],VRefCell(v)))
        c = self._cond.eval(env)
        while c.value:
            self._exp.eval(env)
            self._incre.eval(env)
            c = self._cond.eval(env)
            if c.type != "boolean":
                raise Exception ("Runtime error: while condition not a Boolean")

     #change env back to what is was?? that would be nice
  
class EProcedure (Exp):
    def __init__ (self,params,body):
        self._params = params
        self._body = body

    def __str__ (self):
        return "EProcedure([{}],{})".format(",".join(self._params),str(self._body))

    def eval (self,env):
        return VClosure(self._params,self._body,env)

class EArray(Exp):
    def __init__ (self,length):
        self._length = length

    def __str__ (self):
        return "EArray(length: {})".format(str(self._length))

    def eval (self,env):
        return VArray(self._length,env)


class EObject (Exp):
    
    def __init__ (self,fields,methods):
        self._fields = fields
        self._methods = methods
        
    def __str__ (self):
        return "EObject([{}],[{}])".format(",".join([ "({},{})".format(id,str(exp)) for (id,exp) in self._fields]),
                                           ",".join([ "({},{})".format(id,str(exp)) for (id,exp) in self._methods]))
    
    def eval (self,env):
        fields = [ (id,e.eval(env)) for (id,e) in self._fields]
        methods = [ (id,e.eval(env)) for (id,e) in self._methods]
        return VObject(fields,methods)

class EWithObj (Exp):
    def __init__ (self,exp1,exp2):
        self._object = exp1
        self._exp = exp2
        
    def __str__ (self):
        return "EWithObj({},{})".format(str(self._object),str(self._exp))

    def eval (self,env):
        object = self._object.eval(env)
        # if object.type != "object":
        #     raise Exception("Runtime error: expected an object")
        all_env =object.methods+object.env+env
        return self._exp.eval(all_env)



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

class VObject (Value):

    def __init__ (self,fields,methods):
        self.type = "object"
        self._fields = fields
        self._methods = methods
        self.env = fields + [ (id,v.apply([self])) for (id,v) in methods]
         # this is the mind bending bit
    
    def __str__ (self):
        return "<object {} {}>".format(",".join( id+":"+(str(v)) for (id,v) in self._fields),
                                       ",".join( id+":"+(str(v)) for (id,v) in self._methods))

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
        return "<function [{}] {}>".format(",".join(self.params),str(self.body))

class VArray(Value):
    def __init__ (self,initial,env):
        self.content = [VNone()] * initial.eval(env).value
        self.type = "array"
        self.env = env
        self.methods = [
                ("index",
                VRefCell(VClosure(["x"],
                                    EPrimCall(self.oper_index,[EId("x")]),
                                    self))),
                ("length",
                VRefCell(VClosure([],
                                    EPrimCall(self.oper_length,[]),
                                    self))),
                ("map",
                VRefCell(VClosure(["x"],
                                    EPrimCall(self.oper_map,[EId("x")]),
                                    self))),
                ("swap",
                VRefCell(VClosure(["x","y"],
                                    EPrimCall(self.oper_swap,[EId("x"),EId("y")]),
                                    self)))
                ]

    def __str__ (self):
        return "<ref {}>".format(str(self.content))

    def oper_index(self, i):
        if i.type == "integer":
            return self.content[i.value]
        raise Exception ("Runtime error: variable is not a integer type")

    def oper_length(self):
        return len(self.content)

    def oper_swap(self,i1,i2):
        if i1.type == "integer" and i2.type == "integer":
            temp = self.content[i1.value]
            self.content[i1.value] = self.content[i2.value]
            self.content[i2.value] = temp
            return VNone()
        raise Exception ("Runtime error: variable is not a integer type")


    def oper_map(self,function):
        for i, v in enumerate(self.content):
            self.content[i] = function.body.eval([(function.params[0], v)] + function.env)
        return self


class VRefCell (Value):

    def __init__ (self,initial):
        self.content = initial
        self.type = "ref"

    def __str__ (self):
        return "<ref {}>".format(str(self.content))

class VString(Value):

    def __init__ (self,initial):
        self.content = list(initial) + ["&"]
        self.value = ""
        self.type = "string"
        prev = None
        for i, eachString in enumerate(self.content):
            if eachString.isalpha() or eachString == " " or eachString in ["+","*","-","?","!","=","<",">","+"]:
                self.value += eachString
            elif prev == "&" and eachString == "\"":
                self.value = self.value[:-1]
                self.value += eachString
                self.content.pop(i+3)
                self.content.pop(i+2)
                self.content.pop(i+1)
            elif prev == "&" and eachString == "\'":
                self.value = self.value[:-1]
                self.value += eachString
                self.content.pop(i+3)
                self.content.pop(i+2)
                self.content.pop(i+1)
            prev = eachString

    def __str__ (self):
        return str(self.value)

    def __len__(self):
        return len(self.value)

    def substring(self, i, e):
        sub = self.value[i.value:e.value]
        sub = sub.replace("\"", " &\"   ").replace("\'", " &\'   ")
        return sub

    def concat(self, s):
        conc = self.value + s.value
        conc = conc.replace("\"", " &\"   ").replace("\'", " &\'   ")
        return conc

    def startswith(self, s):
        if self.value[:len(s)] == s.value:
            return True
        return False 

    def endswith(self, s):
        if self.value[len(self) - len(s):] == s.value:
            return True
        return False 

    def lower(self):
        lower = self.value.lower()
        lower.replace("\"", " &\"   ").replace("\'", " &\'   ")
        return lower

    def upper(self):
        upper = self.value.upper()
        upper.replace("\"", " &\"   ").replace("\'", " &\'   ")
        return upper

class VNone (Value):

    def __init__ (self):
        self.type = "none"

    def __str__ (self):
        return "none"


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

def oper_deref (v1):
    if v1.type == "ref":
        return v1.content
    raise Exception ("Runtime error: dereferencing a non-reference value")

def oper_update (v1,v2):
    if v1.type == "ref":
        v1.content = v2
        return VNone()
    raise Exception ("Runtime error: updating a non-reference value")
 
def oper_update_arr(array,index,update):
    if array.type == "ref":
        if isinstance(update.value, int):
            array.content.content[index.value] = VInteger(update.value)
        if isinstance(update.value, str):
            array.content.content[index.value] = VString(update.value)
        if isinstance(update.value, bool):
            array.content.content[index.value] = VBoolean(update.value)
        return VNone()

def oper_print (v1):
    print v1
    return VNone()

def oper_length(v1):
    if v1.type == "string":
        return VInteger(len(v1))
    raise Exception ("Runtime error: variable is not a string type")

def oper_substring(v1, v2, v3):
    if v1.type == "string" and v2.type == "integer" and v3.type == "integer":
        return VString(v1.substring(v2, v3))
    raise Exception ("Runtime error: variable is not a string type")

def oper_concat(v1, v2):
    if v1.type == "string" and v2.type == "string":
        return VString(v1.concat(v2))
    raise Exception ("Runtime error: variable is not a string type")

def oper_startswith(v1, v2):
    if v1.type == "string" and v2.type == "string":
        return VBoolean(v1.startswith(v2))
    raise Exception ("Runtime error: variable is not a string type")

def oper_endswith(v1, v2):
    if v1.type == "string" and v2.type == "string":
        return VBoolean(v1.endswith(v2))
    raise Exception ("Runtime error: variable is not a string type")

def oper_lower(v1):
    if v1.type == "string":
        return VString(v1.lower())
    raise Exception ("Runtime error: variable is not a string type")

def oper_upper(v1):
    if v1.type == "string":
        return VString(v1.upper())
    raise Exception ("Runtime error: variable is not a string type")



############################################################
# IMPERATIVE SURFACE SYNTAX
#



##
## PARSER
##
# cf http://pyparsing.wikispaces.com/

from pyparsing import Word, Literal, ZeroOrMore, OneOrMore, Keyword, Forward, alphas, alphanums, NoMatch, QuotedString, Combine


def initial_env_imp ():
    # A sneaky way to allow functions to refer to functions that are not
    # yet defined at top level, or recursive functions
    env = []
    env.insert(0,
               ("+",
                VRefCell(VClosure(["x","y"],
                                  EPrimCall(oper_plus,[EId("x"),EId("y")]),
                                  env))))
    env.insert(0,
               ("-",
                VRefCell(VClosure(["x","y"],
                                  EPrimCall(oper_minus,[EId("x"),EId("y")]),
                                  env))))
    env.insert(0,
               ("*",
                VRefCell(VClosure(["x","y"],
                                  EPrimCall(oper_times,[EId("x"),EId("y")]),
                                  env))))
    env.insert(0,
               ("zero?",
                VRefCell(VClosure(["x"],
                                  EPrimCall(oper_zero,[EId("x")]),
                                  env))))
    env.insert(0,
                ("length",
                VRefCell(VClosure(["x"],
                                    EPrimCall(oper_length,[EId("x")]),
                                    env))))
    env.insert(0,
                ("substring",
                VRefCell(VClosure(["x", "y", "Z"],
                                    EPrimCall(oper_substring,[EId("x"), EId("y"), EId("Z")]),
                                    env))))
    env.insert(0,
                ("concat",
                VRefCell(VClosure(["x", "y"],
                                    EPrimCall(oper_concat,[EId("x"), EId("y")]),
                                    env))))  
    env.insert(0,
                ("startswith",
                VRefCell(VClosure(["x", "y"],
                                    EPrimCall(oper_startswith,[EId("x"), EId("y")]),
                                    env))))  
    env.insert(0,
                ("endswith",
                VRefCell(VClosure(["x", "y"],
                                    EPrimCall(oper_endswith,[EId("x"), EId("y")]),
                                    env)))) 
    env.insert(0,
                ("lower",
                VRefCell(VClosure(["x"],
                                    EPrimCall(oper_lower,[EId("x")]),
                                    env)))) 
    env.insert(0,
                ("upper",
                VRefCell(VClosure(["x"],
                                    EPrimCall(oper_upper,[EId("x")]),
                                    env)))) 

    return env



def parse_imp (input):
    # parse a string into an element of the abstract representation

    # Grammar:
    #
    # <expr> ::= <integer>
    #            true
    #            false
    #            <identifier>
    #            ( if <expr> <expr> <expr> )
    #            ( function ( <name ... ) <expr> )    
    #            ( <expr> <expr> ... )
    #
    # <decl> ::= var name = expr ; 
    #
    # <stmt> ::= if <expr> <stmt> else <stmt>
    #            while <expr> <stmt>
    #            name <- <expr> ;
    #            print <expr> ;
    #            <block>
    #
    # <block> ::= { <decl> ... <stmt> ... }
    #
    # <toplevel> ::= <decl>
    #                <stmt>
    #

    idChars = alphas+"_+*-?!=<>+"

    QUOTE = Literal('"')
    INTERNAL_QUOTE = QUOTE.copy().leaveWhitespace()

    pIDENTIFIER = Word(idChars, idChars+"0123456789")
    #### NOTE THE DIFFERENCE
    pIDENTIFIER.setParseAction(lambda result: EPrimCall(oper_deref,[EId(result[0])]))

    # A name is like an identifier but it does not return an EId...
    pNAME = Word(idChars,idChars+"0123456789") #| Keyword("&\"") | Keyword("&\'")

    pNAMES = ZeroOrMore(pNAME)
    pNAMES.setParseAction(lambda result: [result])

    pINTEGER = Word("0123456789")
    pINTEGER.setParseAction(lambda result: EValue(VInteger(int(result[0]))))

    QUOTE = Literal("&\"") | Literal("&\'") 
    pSTRING = Literal('"') + ZeroOrMore(Combine( Word(idChars+"0123456789'"+" ") | QUOTE)) + Literal('"')
    pSTRING.setParseAction(lambda result: EValue(VString(str(result[1:-1]))))

    pBOOLEAN = Keyword("true") | Keyword("false")
    pBOOLEAN.setParseAction(lambda result: EValue(VBoolean(result[0]=="true")))

    pEXPR = Forward()

    pEXPRS = ZeroOrMore(pEXPR)
    pEXPRS.setParseAction(lambda result: [result])

    pIF = "(" + Keyword("if") + pEXPR + pEXPR + pEXPR + ")"
    pIF.setParseAction(lambda result: EIf(result[2],result[3],result[4]))

    def mkFunBody (params,body):
        bindings = [ (p,ERefCell(EId(p))) for p in params ]
        return ELet(bindings,body)
    def letToFun(result):
        func = result[5]
        binds = result[3]
        params = []
        vals = []
        for p, v in binds:
            params.append(p)
            vals.append(v)
        return ECall(EFunction(params, func), vals)


    pFUN = "(" + Keyword("function") + "(" + pNAMES + ")" + pEXPR + ")"
    pFUN.setParseAction(lambda result: EFunction(result[3],mkFunBody(result[3],result[5])))



    pBINDING = "(" + pNAME + pEXPR + ")"
    pBINDING.setParseAction(lambda result: (result[1],result[2]))

    pBINDINGS = OneOrMore(pBINDING)
    pBINDINGS.setParseAction(lambda result: [ result ])
    
    pLET = "(" + Keyword("let") + "(" + pBINDINGS + ")" + pEXPR + ")"
    pLET.setParseAction(letToFun)

    pCALL = "(" + pEXPR + pEXPRS + ")"
    pCALL.setParseAction(lambda result: ECall(result[1],result[2]))

    pARRAY = "(" + Keyword("new-array") + pEXPR + ")"
    pARRAY.setParseAction(lambda result: EArray(result[2]))

    pINDEX = Keyword("index") + pINTEGER
    pCALL.setParseAction(lambda result: ECall(result[1],result[2]))

    # pWITH = "(" + Keyword("with") + pNAME + pEXPR + ")"

    pWITH = "(" + Keyword("with") + pEXPR + pEXPR +")"
    pWITH.setParseAction(lambda result: EWithObj(result[2],result[3]))

    pEXPR << ( pINTEGER | pARRAY | pSTRING | pWITH | pBOOLEAN | pIDENTIFIER | pIF  | pLET | pFUN | pCALL )

    pDECL_VAR = "var" + pNAME + "=" + pEXPR + ";"
    pDECL_VAR.setParseAction(lambda result: (result[1],result[3]))

    pSTMT = Forward()

    pDECL_PROCEDURE = "procedure" + pNAME + "(" + pNAMES + ")" + pSTMT
    pDECL_PROCEDURE.setParseAction(lambda result: (result[1], EProcedure(result[3], mkFunBody(result[3], result[5]))))

    # hack to get pDECL to match only PDECL_VAR (but still leave room
    # to add to pDECL later)
    pDECL = ( pDECL_VAR | pDECL_PROCEDURE | NoMatch() | ";" )

    pDECLS = ZeroOrMore(pDECL)
    pDECLS.setParseAction(lambda result: [result])


    pSTMT_IF_1 = "if" + pEXPR + pSTMT + "else" + pSTMT
    pSTMT_IF_1.setParseAction(lambda result: EIf(result[1],result[2],result[4]))

    pSTMT_IF_2 = "if" + pEXPR + pSTMT
    pSTMT_IF_2.setParseAction(lambda result: EIf(result[1],result[2],EValue(VBoolean(True))))
   
    pSTMT_WHILE = "while" + pEXPR + pSTMT
    pSTMT_WHILE.setParseAction(lambda result: EWhile(result[1],result[2]))

    pSTMT_FOR = "for" + pDECLS + pEXPR + ";" + pSTMT + pSTMT
    pSTMT_FOR.setParseAction(lambda result: EFor(result[1], result[2], result[4], result[5]))

    pSTMT_PRINT = "print" + pEXPR + ";"
    pSTMT_PRINT.setParseAction(lambda result: EPrimCall(oper_print,[result[1]]));

    pSTMT_UPDATE_ARR = pNAME + "[" + pINTEGER +"]" + "<-" + pEXPR + ";"
    pSTMT_UPDATE_ARR.setParseAction(lambda result: EPrimCall(oper_update_arr,[EId(result[0]),result[2],result[5]]))

    pSTMT_UPDATE = pNAME + "<-" + pEXPR + ";"
    pSTMT_UPDATE.setParseAction(lambda result: EPrimCall(oper_update,[EId(result[0]),result[2]]))

    pSTMT_PROCEDURE = pEXPR + "(" + pEXPRS + ")" + ";"
    pSTMT_PROCEDURE.setParseAction(lambda result: ECall(result[0], result[2]))

    pSTMTS = ZeroOrMore(pSTMT)
    pSTMTS.setParseAction(lambda result: [result])

    def mkBlock (decls,stmts):
        bindings = [ (n,ERefCell(expr)) for (n,expr) in decls ]
        return ELet(bindings,EDo(stmts))
        
    pSTMT_BLOCK = "{" + pDECLS + pSTMTS + "}"
    pSTMT_BLOCK.setParseAction(lambda result: mkBlock(result[1],result[2]))

    pSTMT << ( pSTMT_IF_1 | pSTMT_IF_2 | pSTMT_WHILE | pSTMT_FOR | pSTMT_PRINT | pSTMT_UPDATE_ARR | pSTMT_UPDATE |  pSTMT_PROCEDURE | pSTMT_BLOCK )

    # can't attach a parse action to pSTMT because of recursion, so let's duplicate the parser
    pTOP_STMT = pSTMT.copy()
    pTOP_STMT.setParseAction(lambda result: {"result":"statement",
                                             "stmt":result[0]})

    pTOP_DECL = pDECL.copy()
    pTOP_DECL.setParseAction(lambda result: {"result":"declaration",
                                             "decl":result[0]})

    pABSTRACT = "#abs" + pSTMT
    pABSTRACT.setParseAction(lambda result: {"result":"abstract",
                                             "stmt":result[1]})
    pQUIT = Keyword("#quit")
    pQUIT.setParseAction(lambda result: {"result":"quit"})
    
    pTOP = (pQUIT | pABSTRACT | pTOP_DECL | pTOP_STMT )

    result = pTOP.parseString(input)[0]
    return result    # the first element of the result is the expression


def shell_imp ():
    # A simple shell
    # Repeatedly read a line of input, parse it, and evaluate the result

    print "Homework 6 - Imp Language"
    print "#quit to quit, #abs to see abstract representation"
    env = initial_env_imp()

    while True:
        inp = raw_input("imp> ")

        if inp.startswith("#multi"):
            # multi-line statement
            line = ""
            inp = raw_input(".... ")
            while inp:
                line += inp + " "
                inp = raw_input(".... ")
            inp = line
            
        try:
            result = parse_imp(inp)

            if result["result"] == "statement":
                stmt = result["stmt"]
                # print "Abstract representation:", exp
                v = stmt.eval(env)

            elif result["result"] == "abstract":
                print result["stmt"]

            elif result["result"] == "quit":
                return

            elif result["result"] == "declaration":
                (name,expr) = result["decl"]
                v = expr.eval(env)
                env.insert(0,(name,VRefCell(v)))
                print "{} defined".format(name)
                    
        except Exception as e:
            print "Exception: {}".format(e)

shell_imp ()