############################################################
# FUNC 
# S-expressions surface syntax
# reference cells
#
# Type checking
#
# use shell() to start

import sys
import time
import traceback



############################################################
# helper code to time the execution of a piece of code
#

class Timer(object):
    def __enter__(self):
        self.__start = time.time()
        return self

    def __exit__(self, type, value, traceback):
        # Error handling here
        self.__finish = time.time()

    def duration_in_seconds(self):
        return self.__finish - self.__start

    def time (self):
        return time.time() - self.__start




#
# Expressions
#

class Exp (object):
    pass


# evaluation function -- all the evaluation code is here now

def eval_iter (exp,env):
    current_exp = exp
    current_env = env
    while True:
        # these are all the special forms which directly
        # return the result of evaluating an expression
        if current_exp.expForm == "ECall":

            f = eval_iter(current_exp._fun,current_env)
            args = [ eval_iter(e,current_env) for e in current_exp._args]
            new_env = f._env + zip(f._params,args)
            current_exp = f._body
            current_env = new_env

        elif current_exp.expForm == "EIf":

            v = eval_iter(current_exp._cond,current_env)
            if v.value:
                current_exp = current_exp._then
            else:
                current_exp = current_exp._else

        elif current_exp.expForm == "EValue":

            return current_exp._value

        elif current_exp.expForm == "EPrimCall":

            vs = [ eval_iter(e,current_env) for e in current_exp._exps ]
            return apply(current_exp._prim,vs)

        elif current_exp.expForm == "EId":

            for (id,v) in reversed(current_env):
                if current_exp._id == id:
                    return v

        elif current_exp.expForm == "EFunction":
            
            return VClosure(current_exp._params,current_exp._body,current_env,current_exp._name)

        else:

            raise Exception("Unrecognized expression form: {}".format(current_exp.expForm))


    
class EValue (Exp):
    # Value literal
    def __init__ (self,v):
        self._value = v
        self.expForm = "EValue"
        self.is_basic = True

    def typecheck (self,symtable):
        # type is the type of the literal 
        return self._value.type
    
    def __str__ (self):
        return "EValue({})".format(self._value)

    def eval (self,env):
        return eval_iter(self,env)

    
class EPrimCall (Exp):
    # Call an underlying Python primitive, passing in Values
    #
    # simplifying the prim call
    # it takes an explicit function as first argument

    def __init__ (self,prim,es):
        self._prim = prim
        self._exps = es
        self.expForm = "EPrimCall"
        self.is_basic = True

    def typecheck (self,symtable):
        # we'll never type check EPrimCall
        raise Exception("Type error: cannot type EPrimCall")

    def __str__ (self):
        return "EPrimCall(<prim>,[{}])".format(",".join([ str(e) for e in self._exps]))

    def eval (self,env):
        return eval_iter(self,env)



COUNTER = 0
def fresh ():
    global COUNTER
    COUNTER += 1
    return COUNTER-1


class EIf (Exp):
    # Conditional expression

    def __init__ (self,e1,e2,e3):
        self._cond = e1
        self._then = e2
        self._else = e3
        self.expForm = "EIf"
        self.is_basic = False

    def typecheck (self,symtable):
        # type is the type of the then part (checking will ensure the else part has the same type)
        tcond = self._cond.typecheck(symtable)
        tthen = self._then.typecheck(symtable)
        telse = self._else.typecheck(symtable)
        if not tcond.isBoolean():
            raise Exception("Type error: EIf condition should be Boolean")
        if not tthen.isEqual(telse):
            raise Exception("Type error: EIf then and else parts should be the same type")
        # return the one type that is not TAny (if any)
        if tthen.isAny():
            return telse
        return tthen

    def __str__ (self):
        return "EIf({},{},{})".format(self._cond,self._then,self._else)

    def eval (self,env):
        return eval_iter(self,env)


    
class EId (Exp):
    # identifier

    def __init__ (self,id):
        self._id = id
        self.expForm = "EId"
        self.is_basic = True

    def typecheck (self,symtable):
        # type is that of the identifier in the symbol table
        for (name,typ) in reversed(symtable):
            if name == self._id:
                return typ
        raise Exception("Type error: cannot find identifier {}".format(self._id))

    def __str__ (self):
        return "EId({})".format(self._id)

    def eval (self,env):
        return eval_iter(self,env)


class ECall (Exp):
    # Call a defined function in the function dictionary
    # uses an "apply" function in the closure for encapsulation

    def __init__ (self,fun,exps):
        self._fun = fun
        self._args = exps
        self.expForm = "ECall"
        self.is_basic = False

    def typecheck (self,symtable):
        # type is the type of the result of the function
        tfun = self._fun.typecheck(symtable)
        if not (tfun.isFunction()):
            raise Exception("Type error1: non-function in ECall, got {}".format(tfun))
        # found, expected...
        if len(tfun.params) != len(self._args):
            raise Exception("Type error2: wrong number of arguments in ECall, expected {} got {}".format(len(tfun.params),len(self._args)))
        for (t,arg) in zip(tfun.params,self._args):
            if t.isFunction():
                for i,j in zip(t.params, arg.typecheck(symtable).params):
                    if i.isGen():
                        found = search_table(i, symtable)
                        if found == False:
                            symtable = symtable + [(i.type_name, j)]
                        else:
                            if not found.type == j.type:
                                raise Exception("Type error3: wrong argument in ECall, expected {} got {}".format(found.type,j.type))            
                if not t.result.isGen():
                    if not t.result == arg.typecheck(symtable).result:
                        raise Exception("Type error4: wrong argument in ECall, expected {} got {}".format(t,arg.typecheck(symtable)))            
                else:
                    found = search_table(t.result, symtable)
                    if found == False:
                        symtable = symtable + [(t.result.type_name, arg.typecheck(symtable).result)]
                    else:
                        if not found.type == arg.typecheck(symtable).result.type:
                            raise Exception("Type error5: wrong argument in ECall, expected {} got {}".format(t,arg.typecheck(symtable)))            
           
            elif not t.isGen():
                if not t.isEqual(arg.typecheck(symtable)):
                    raise Exception("Type error6: wrong argument in ECall, expected {} got {}".format(t,arg.typecheck(symtable)))
            
            else:
                found = search_table(t, symtable)
                if found == False:
                    symtable = symtable + [(t.type_name, arg.typecheck(symtable))]  
                else:
                    if not found.isEqual(arg.typecheck(symtable)):
                        raise Exception("Type error7: wrong argument in ECall, expected {} got {}".format(t,arg.typecheck(symtable)))            
        return tfun.result
                # found = False
                # for (name,typ) in reversed(symtable):
                #     if name == t.type_name:
                #         found = True
                #         if not t.isEqual(arg.typecheck(symtable)):
                #             raise Exception("Type error: wrong argument in ECall, expected {} got {}".format(t,arg.typecheck(symtable)))            
                # if found == False:
                #     symtable = symtable + [(t.type_name, arg.typecheck(symtable))]    

    def __str__ (self):
        return "ECall({},[{}])".format(str(self._fun),",".join([str(e) for e in self._args]))

    def eval (self,env):
        return eval_iter(self,env)


class EFunction (Exp):
    # Creates an anonymous function

    def __init__ (self,params,body,types=None,name=None):
        self._params = params
        self._body = body
        self._name = name
        self.expForm = "EFunction"
        self.is_basic = False
        if types and len(types) == len(params):
            self._param_types = types
        else:
            self._param_types = [ TUnknown() for p in params]

    def typecheck (self,symtable):
        print "came here to efunction type check"
        if self._name:
            # recursive function, so type check under the assumption that the current
            # function returns a value of type TAny (basically, any type), and read off
            # the body type we get as the final type
            # If TAny is the final type, we've just identified an infinite loop!
            tself = [(self._name,TFunction(self._param_types,TAny()))]
            print tself,"tself"
            print self._body
            tbody = self._body.typecheck(symtable+zip(self._params,self._param_types)+tself)
        else:
            tbody = self._body.typecheck(zip(self._params,self._param_types) + symtable)
        return TFunction(self._param_types,tbody)

    def __str__ (self):
        return "EFunction([{}],{})".format(",".join(self._params),str(self._body))

    def eval (self,env):
        return eval_iter(self,env)


              
    
#
# Values
#

class Value (object):
    pass


class VInteger (Value):
    # Value representation of integers
    
    def __init__ (self,i):
        self.value = i
        self.type = TInteger()

    def __str__ (self):
        return str(self.value)

    
class VBoolean (Value):
    # Value representation of Booleans
    
    def __init__ (self,b):
        self.value = b
        self.type = TBoolean()

    def __str__ (self):
        return "true" if self.value else "false"

    
class VClosure (Value):
    
    def __init__ (self,params,body,env,name=None):
        self._params = params
        self._body = body
        extra = [(name,self)] if name else []
        self._env = env + extra
        self.type = TFunction([ TUnknown() for p in params],TUnknown())

    def __str__ (self):
        return "<function [{}] {}>".format(",".join(self._params),str(self._body))


    
class VRefCell (Value):

    def __init__ (self,initial):
        self.content = initial
        self.type = TRef(initial.type)

    def __str__ (self):
        return "<ref {}>".format(str(self.content))


class VNone (Value):

    def __init__ (self):
        self.type = TNone()

    def __str__ (self):
        return "none"




# Primitive operations

def oper_plus (v1,v2): 
    return VInteger(v1.value + v2.value)

def oper_minus (v1,v2):
    return VInteger(v1.value - v2.value)

def oper_times (v1,v2):
    return VInteger(v1.value * v2.value)

def oper_zero (v1):
    return VBoolean(v1.value==0)

def oper_ref (v1):
    return VRefCell(v1)

def oper_deref (v1):
    return v1.content

def oper_update (v1,v2):
    v1.content = v2
    return VNone()
 
def oper_print (v1):
    print v1
    return VNone()





##
## PARSER
##
# cf http://pyparsing.wikispaces.com/

from pyparsing import Word, Literal, ZeroOrMore, OneOrMore, Keyword, Forward, alphas, alphanums, NoMatch, Group


def parse (input):
    # parse a string into an element of the abstract representation


    idChars = alphas+"_+*-?!="

    pIDENTIFIER = Word(idChars, idChars+"0123456789")
    pIDENTIFIER.setParseAction(lambda result: EId(result[0]))

    # A name is like an identifier but it does not return an EId...
    pNAME = Word(idChars,idChars+"0123456789")

    pNAMES = ZeroOrMore(pNAME)
    pNAMES.setParseAction(lambda result: [result])

    # Types!
    pTYPE = Forward()

    pTYPE_INT = Keyword("int")
    pTYPE_INT.setParseAction(lambda result: TInteger())

    pTYPE_BOOL = Keyword("bool")
    pTYPE_BOOL.setParseAction(lambda result: TBoolean())

    pTYPE_REF = "(" + Keyword("ref") + pTYPE + ")"
    pTYPE_REF.setParseAction(lambda result: TRef(result[2]))

    pTYPE_FUN = "(" + Literal("->") + "(" + Group(OneOrMore(pTYPE)) + ")" + pTYPE + ")"
    pTYPE_FUN.setParseAction(lambda result: TFunction(result[3],result[5]))

    def cameHere(result):
        print result[1],"came here?????"
    pTYPE_GEN = "<" + pNAME + ">"
    pTYPE_GEN.setParseAction(lambda result: TGen(result[1]))
    # pTYPE_GEN.setParseAction(cameHere)

    pTYPE << (pTYPE_INT | pTYPE_BOOL | pTYPE_REF | pTYPE_GEN | pTYPE_FUN)


    pTYPES = "(" + Group(OneOrMore(pTYPE)) + ")"
    pTYPES.setParseAction(lambda result: [result[1]])

    pINTEGER = Word("0123456789")
    pINTEGER.setParseAction(lambda result: EValue(VInteger(int(result[0]))))

    pBOOLEAN = Keyword("true") | Keyword("false")
    pBOOLEAN.setParseAction(lambda result: EValue(VBoolean(result[0]=="true")))

    pEXPR = Forward()

    pEXPRS = ZeroOrMore(pEXPR)
    pEXPRS.setParseAction(lambda result: [result])

    pIF = "(" + Keyword("if") + pEXPR + pEXPR + pEXPR + ")"
    pIF.setParseAction(lambda result: EIf(result[2],result[3],result[4]))

    pBINDING = "(" + pNAME + pEXPR + ")"
    pBINDING.setParseAction(lambda result: (result[1],result[2]))

    pBINDINGS = ZeroOrMore(pBINDING)
    pBINDINGS.setParseAction(lambda result: [ result ])

    def makeLet (bindings,types,body):
        params = [ param for (param,exp) in bindings ]
        args = [ exp for (param,exp) in bindings ]
        return ECall(EFunction(params,body,types=types),args)

    pLET = "(" + Keyword("let") + "(" + pBINDINGS + ")" + pTYPES + pEXPR + ")"
    pLET.setParseAction(lambda result: makeLet(result[3],result[5],result[6]))

    pCALL = "(" + pEXPR + pEXPRS + ")"
    pCALL.setParseAction(lambda result: ECall(result[1],result[2]))

    # ADDED TYPE!!
    pFUN = "(" + Keyword("function") + "(" + pNAMES + ")" + pTYPES +  pEXPR + ")"
    pFUN.setParseAction(lambda result: EFunction(result[3],result[6],types=result[5]))
    #pFUN.setDebug()
    #pFUN.setName("pFUN")

    pFUNrec = "(" + Keyword("function") + pNAME + "(" + pNAMES + ")" + pTYPES + pEXPR + ")"
    pFUNrec.setParseAction(lambda result: EFunction(result[4],result[7],types=result[6],name=result[2]))

    def makeDo (exprs):
        result = exprs[-1]
        for e in reversed(exprs[:-1]):
            # space is not an allowed identifier in the syntax!
            result = makeLet([(" ",e)],[TNone()],result)
        return result

    pDO = "(" + Keyword("do") + pEXPRS + ")"
    pDO.setParseAction(lambda result: makeDo(result[2]))

    def makeWhile (cond,body):
        return makeLet([(" while",
                         EFunction([],EIf(cond,makeLet([(" ",body)],ECall(EId(" while"),[])),EValue(VNone())),name=" while"))],
                       [TFunction([],TNone())],
                       ECall(EId(" while"),[]))

    pWHILE = "(" + Keyword("while") + pEXPR + pEXPR + ")"
    pWHILE.setParseAction(lambda result: makeWhile(result[2],result[3]))

    pEXPR << (pINTEGER | pBOOLEAN | pIDENTIFIER | pIF | pLET | pFUN | pFUNrec| pDO | pWHILE | pCALL)

    # can't attach a parse action to pEXPR because of recursion, so let's duplicate the parser
    pTOPEXPR = pEXPR.copy()
    pTOPEXPR.setParseAction(lambda result: {"result":"expression","expr":result[0]})

    pDEFINE = "(" + Keyword("define") + pNAME + pEXPR + ")"
    pDEFINE.setParseAction(lambda result: {"result":"value",
                                           "name":result[2],
                                           "expr":result[3]})

    pDEFUN = "(" + Keyword("defun") + pNAME + "(" + pNAMES + ")" + pTYPES + pEXPR + ")"
    pDEFUN.setParseAction(lambda result: {"result":"function",
                                          "name":result[2],
                                          "params":result[4],
                                          "types":result[6],
                                          "body":result[7]})

    pABSTRACT = "#abs" + pEXPR
    pABSTRACT.setParseAction(lambda result: {"result":"abstract",
                                             "expr":result[1]})

    pQUIT = Keyword("#quit")
    pQUIT.setParseAction(lambda result: {"result":"quit"})
    
    pTOP = (pDEFUN | pDEFINE | pQUIT | pABSTRACT | pTOPEXPR)

    result = pTOP.parseString(input)[0]
    return result    # the first element of the result is the expression




def add_binding (name,value,env):
    return env + [(name,value)]

def initial_env ():
    env = []
    env = add_binding("+",
                      VClosure(["x","y"],
                               EPrimCall(oper_plus,[EId("x"),EId("y")]),
                               []),
                      env)
    env = add_binding("-",
                      VClosure(["x","y"],
                               EPrimCall(oper_minus,[EId("x"),EId("y")]),
                               []),
                      env)
    env = add_binding("*",
                      VClosure(["x","y"],
                               EPrimCall(oper_times,[EId("x"),EId("y")]),
                               []),
                      env)
    env = add_binding("zero?",
                      VClosure(["x"],
                               EPrimCall(oper_zero,[EId("x")]),
                               []),
                      env)
    env = add_binding("ref",
                      VClosure(["x"],
                               EPrimCall(oper_ref, [EId("x")]),
                               []),
                      env)
    env = add_binding("deref",
                      VClosure(["x"],
                               EPrimCall(oper_deref, [EId("x")]),
                               []),
                      env)
    env = add_binding("update!",
                      VClosure(["x","y"],
                               EPrimCall(oper_update,[EId("x"),EId("y")]),
                               []),
                      env)
    env = add_binding("print!",
                      VClosure(["x"],
                               EPrimCall(oper_print,[EId("x")]),
                               []),
                      env)
    return env

def initial_symtable ():
    # keep in sync with initial_env_cps()
    return [("+",TFunction([TInteger(),TInteger()],TInteger())),
            ("-",TFunction([TInteger(),TInteger()],TInteger())),
            ("*",TFunction([TInteger(),TInteger()],TInteger())),
            ("zero?",TFunction([TInteger()],TBoolean())),
            # these types are not great for ref and company
            # they restrict reference cells to contain integers only
            # we need a better type system
            ("ref",TFunction([TInteger()],TRef(TInteger()))),
            ("deref",TFunction([TRef(TInteger())],TInteger())),
            ("update!",TFunction([TRef(TInteger()),TInteger()],TNone())),
            ("print!",TFunction([TInteger()],TNone()))]

def search_table(t, symtable):
    for (name,typ) in reversed(symtable):
        if name == t.type_name:
            return typ
    return False


def shell ():
    # A simple shell
    # Repeatedly read a line of input, parse it, and evaluate the result

    print "Lecture 10 - REF Language with static type checking"
    print "#quit to quit, #abs to see abstract representation"
    env = initial_env()
    symt = initial_symtable()
        
    while True:
        inp = raw_input("ref/types> ")

        try:
            result = parse(inp)
            print result,"result*****"

            if result["result"] == "expression":
                exp = result["expr"]
                with Timer() as timer:
                    typ = exp.typecheck(symt)
                    print "[Type {}]".format(typ)
                    v = exp.eval(env)
                    # print "Eval time: {}s".format(round(timer.time(),3))
                print v

            elif result["result"] == "abstract":
                exp = result["expr"]
                print exp

            elif result["result"] == "quit":
                return

            elif result["result"] == "function":
                # the top-level environment is special, it is shared
                # amongst all the top-level closures so that all top-level
                # functions can refer to each other
                f = EFunction(result["params"],result["body"],types=result["types"],name=result["name"])
                t = f.typecheck(symt)
                print "[Type {}]".format(t) + "right here"
                v = f.eval(env)

                env = add_binding(result["name"],v,env)
                symt = add_binding(result["name"],t,symt)
                print "{} defined".format(result["name"])

            elif result["result"] == "value":
                exp = result["expr"]
                t = exp.typecheck(symt)
                v = exp.eval(env)
                env = add_binding(result["name"],v,env)
                symt = add_binding(result["name"],t,symt)
                print "{} defined".format(result["name"])
                
        except Exception as e:
            print "Exception: {}".format(e)




############################################################
# types


class Type (object):
    def isInteger (self):
        return False
    def isBoolean (self):
        return False
    def isFunction (self):
        return False
    def isRef (self):
        return False
    def isNone (self):
        return False
    def isAny (self):
        return False
    def isEqual (self,t):
        return False
    def isGen (self):
        return False

class TInteger (Type):
    def __init__ (self):
        self.type = "integer"
    def __str__ (self):
        return "int"
    def isInteger (self):
        return True
    def isEqual (self,t):
        return (t.isInteger() or t.isAny())

class TBoolean (Type):
    def __init__ (self):
        self.type = "boolean"
    def __str__ (self):
        return "bool"
    def isBoolean (self):
        return True
    def isEqual (self,t):
        return (t.isBoolean() or t.isAny())

class TNone (Type):
    def __init__ (self):
        self.type = "none"
    def __str__ (self):
        return "none"
    def isNone (self):
        return True
    def isEqual (self,t):
        return (t.isNone() or t.isAny())

class TFunction (Type):
    def __init__ (self,params,result):
        self.type = "function"
        self.params = params
        self.result = result
    def __str__ (self):
        return "(-> ({}) {})".format(" ".join([ str(t) for t in self.params]),self.result)
    def isFunction (self):
        return True
    def isEqual (self,t):
        if t.isAny():
            return True
        if not t.isFunction():
            return False
        args = (len(self.params) == len(t.params)) and all([ a.isEqual(b) for (a,b) in zip(self.params,t.params)])
        return args and self.result.isEqual(t.result)

class TRef (Type):
    def __init__ (self,content):
        self.type = "ref"
        self.content = content
    def __str__ (self):
        return "(ref {})".format(self.content)
    def isRef (self):
        return True
    def isEqual (self,t):
        return (t.isRef() and self.content.isEqual(t.content)) or t.isAny()

class TGen(Type):
    def __init__ (self,type_name):
        self.type = "gen"
        self.type_name = type_name
    def __str__ (self):
        return "gen"
    def isGen (self):
        return True
    def isEqual (self,t):
        return t.isGen()

# This is a special type that represents "any" value
# It is equal to any type, meaning that it will satisfy type checking 
#  any place it occurs
# It is used as the initial result type for a recursive function when
#  type checking the body of the recursive function

class TAny (Type):
    def __init__ (self):
        self.type = "any"
    def __str__ (self):
        return "any"
    def isAny (self):
        return True
    def isEqual (self,t):
        return True
    

# useful as a placeholder -- this will always fail
class TUnknown (Type):
    def __init__ (self):
        self.type = "???"
    def __str__ (self):
        return "???"
    def isEqual (self,t):
        # Unknown is never equal to anything
        return False

shell()
