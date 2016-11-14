############################################################
# Simple imperative language
# C-like surface syntac
# with S-expression syntax for expressions
# (no recursive closures)
#
import random
"""
Names:
Lucy Wilcox and Xiaofan Wu

Emails:
lucy.wilcox@students.olin.edu
wuxiaofan1996@gmail.com

Remarks:

Parenthesis must be used for expression in some expressions, for example:
print true ? 2 : 3; is vaild
print not true ? 2 : 3; is not valid
print (not true) ? 2 : 3; is valid


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
        if len(args) != len(f.params):
            raise Exception("Runtime error: argument # mismatch in call")
        if hasattr(f.env, "type"):
            if f.env.type == "array":
                new_env = zip(f.params,args) + f.env.methods
        else:
            # new_args = [x.eval(env) for x in self._args]
            # new_vals = zip(f.params, new_args)
            # new_env = new_vals + f.env
            new_env = zip(f.params,args) + f.env
        return f.body.eval(new_env)


class EFunction (Exp):
    # Creates an anonymous function

    def __init__ (self,params,body, name = ""):
        self._params = params
        self._body = body
        self._name = name

    def __str__ (self):
        return "EFunction([{}],{})".format(",".join(self._params),str(self._body))

    def eval (self,env):
        if self._name!="":
            env.insert(0,(self._name, VClosure(self._params,self._body,env)))
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

    def __init__ (self, i, exp, body):
        self._i = i
        self._body = body
        self._exp = exp

    def __str__ (self):
        return "EFor({},{},{},{})".format(str(self._i), str(self._body), str(self._exp))

    def eval (self,env):
        for i in self._exp.eval(env).value:
            if hasattr(i, "_value"):
                i_val = (self._i, VRefCell(i.eval(env)))
            else:
                i_val = (self._i, VRefCell(i))
            self._body.eval([i_val] + env)
  
class EProcedure (Exp):
    def __init__ (self,params,body):
        self._params = params
        self._body = body

    def __str__ (self):
        return "EProcedure([{}],{})".format(",".join(self._params),str(self._body))

    def eval (self,env):
        return VClosure(self._params,self._body,env)

class EArray(Exp):
    def __init__ (self,itemOne,arrayItems):
        self._content = []
        self._content.append(itemOne)
        for i, each in enumerate(arrayItems):
            self._content.append(each)


    def __str__ (self):
        return "EArray(length: {})".format(str(self._length))

    def eval (self,env):
        return VArray(self._content,env)

class EDict(Exp):
    def __init__ (self,firstitem,dictItems):
        self._dict = dict()
        self._dict[firstitem[0]] = firstitem[1]
        for key, value in dictItems:
            self._dict[key] = value

    def __str__ (self):
        return "EDICT(length: {})".format(str(self._length))

    def eval (self,env):
        return VDict(self._dict,env)



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
        
class VDict(Value):
    def __init__ (self,content,env):
        self.value = content
        self.type = "dict"
        self.env = env


class VArray(Value):
    def __init__ (self,content,env):
        self.value = content
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
        return "<ref {}>".format(str(self.value))

    def oper_index(self, i):
        if i.type == "integer":
            return self.value[i.value]
        raise Exception ("Runtime error: variable is not a integer type")

    def oper_length(self):
        return VInteger(len(self.value))

    def oper_swap(self,i1,i2):
        if i1.type == "integer" and i2.type == "integer":
            temp = self.value[i1.value]
            self.value[i1.value] = self.value[i2.value]
            self.value[i2.value] = temp
            return VNone()
        raise Exception ("Runtime error: variable is not a integer type")


    def oper_map(self,function):
        for i, v in enumerate(self.value):
            self.value[i] = function.body.eval([(function.params[0], v)] + function.env)
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
    elif v1.type == "string" and v2.type == "string":
        return VString(v1.value + v2.value)
    elif v1.type == "array" and v2.type == "array":
        return VArray(v1.value + v2.value)
    raise Exception ("Runtime error: trying to add inncorrect types")

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
            array.content.value[index.value] = EValue(VInteger(update.value))
        if isinstance(update.value, str):
            array.content.value[index.value] = EValue(VString(update.value))
        if isinstance(update.value, bool):
            array.content.value[index.value] = EValue(VBoolean(update.value))
        return VNone()

def oper_access_arr(arrayOrDict,index):
    if arrayOrDict.type == "ref":
        current = arrayOrDict.content.value[index.value]._value.value
        if isinstance(current, int):
            return VInteger(current)
        if isinstance(current, str):
            return VString(current)
        if isinstance(current, bool):
            return VBoolean(current)

def forEachPrint (v1):
    if hasattr(v1, 'type'):
        if v1.type == "array":
            newArray = []
            for each in v1.value:
                newArray.append(each._value.value)
            print newArray
            return VNone()
        else:
            print v1.value
            return VNone()
    print v1
    return VNone()

def oper_print(*args):
    if len(args) == 1:
        forEachPrint(args[0])
    else:
        for eachArg in args:
            forEachPrint(eachArg)

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

def oper_random(first,last):
    if first.type == "integer" and last.type == "integer":
        return VInteger(random.randrange(last.value - first.value + 1))
    raise Exception ("Runtime error: variable is not a integer type")

def oper_lessEqual(v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VBoolean(v1.value <= v2.value)
    elif v1.type == "string" and v2.type == "string":
        return VBoolean(v1.value <= v2.value)
    raise Exception ("Runtime error: variable is not a string or int type")

def oper_greaterEqual(v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VBoolean(v1.value >= v2.value)
    elif v1.type == "string" and v2.type == "string":
        return VBoolean(v1.value >= v2.value)
    raise Exception ("Runtime error: variable is not a string or int type")

def oper_less(v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VBoolean(v1.value < v2.value)
    elif v1.type == "string" and v2.type == "string":
        return VBoolean(v1.value < v2.value)
    raise Exception ("Runtime error: variable is not a string or int type")

def oper_greater(v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VBoolean(v1.value > v2.value)
    elif v1.type == "string" and v2.type == "string":
        return VBoolean(v1.value > v2.value)
    raise Exception ("Runtime error: variable is not a string or int type")

def oper_notequal(v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VBoolean(v1.value != v2.value)
    elif v1.type == "string" and v2.type == "string":
        return VBoolean(v1.value != v2.value)
    elif v1.type == "boolean" and v2.type == "boolean":
        return VBoolean(v1.value != v2.value)
    elif v1.type == "array" and v2.type == "array":
        return VBoolean(v1.value != v2.value)
    raise Exception ("Runtime error: variable is not a recognized type")

def oper_equal(v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VBoolean(v1.value == v2.value)
    elif v1.type == "string" and v2.type == "string":
        return VBoolean(v1.value == v2.value)
    elif v1.type == "boolean" and v2.type == "boolean":
        return VBoolean(v1.value == v2.value)
    elif v1.type == "array" and v2.type == "array":
        return VBoolean(v1.value == v2.value)
    raise Exception ("Runtime error: variable is not a recognized type")

def oper_not(v1):
    if v1.type == "boolean":
        if v1.value == True:
            return VBoolean(False)
        elif v1.value == False:
            return VBoolean(True)
    raise Exception ("Runtime error: variable is not a boolean type")

def oper_and(v1, v2):
    if v1.type == "boolean" and v2.type == "boolean":
        if v1.value == False:
            return VBoolean(False)
        elif v2.value == False:
            return VBoolean(False)
        else:
            return VBoolean(True)
    raise Exception ("Runtime error: variable is not a boolean type")

def oper_or(v1, v2):
    if v1.type == "boolean" and v2.type == "boolean":
        if v1.value == True:
            return VBoolean(True)
        elif v2.value == True:
            return VBoolean(True)
        else:
            return VBoolean(False)
    raise Exception ("Runtime error: variable is not a boolean type")

def oper_len(v1):
    if v1.type =="string":
        return VInteger(len(v1))
    if v1.type == "array":
        return VInteger(len(v1.value))


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
    env.insert(0,
                ("random",
                VRefCell(VClosure(["x","y"],
                                    EPrimCall(oper_random,[EId("x"),EId("y")]),
                                    env)))) 
    env.insert(0,
                ("<=",
                VRefCell(VClosure(["x","y"],
                                    EPrimCall(oper_lessEqual,[EId("x"),EId("y")]),
                                    env)))) 
    env.insert(0,
                (">=",
                VRefCell(VClosure(["x","y"],
                                    EPrimCall(oper_greaterEqual,[EId("x"),EId("y")]),
                                    env)))) 
    env.insert(0,

                ("<",
                VRefCell(VClosure(["x","y"],
                                    EPrimCall(oper_less,[EId("x"),EId("y")]),
                                    env)))) 
    env.insert(0,
                (">",
                VRefCell(VClosure(["x","y"],
                                    EPrimCall(oper_greater,[EId("x"),EId("y")]),
                                    env))))     
    env.insert(0,
                ("<>",
                VRefCell(VClosure(["x","y"],
                                    EPrimCall(oper_notequal,[EId("x"),EId("y")]),
                                    env))))
    env.insert(0,
                ("==",
                VRefCell(VClosure(["x","y"],
                                    EPrimCall(oper_equal,[EId("x"),EId("y")]),
                                    env))))
    env.insert(0,
                ("not",
                VRefCell(VClosure(["x"],
                                    EPrimCall(oper_not,[EId("x")]),
                                    env))))
    env.insert(0,
                ("and",
                VRefCell(VClosure(["x", "y"],
                                    EPrimCall(oper_and,[EId("x"), EId("y")]),
                                    env))))
    env.insert(0,
                ("or",
                VRefCell(VClosure(["x", "y"],
                                    EPrimCall(oper_or,[EId("x"), EId("y")]),
                                    env))))
    env.insert(0,
                ("print",
                VRefCell(VClosure(["x"],
                                    EPrimCall(oper_print,[EId("x")]),
                                    env))))
    env.insert(0,
                ("len",
                VRefCell(VClosure(["x"],
                                    EPrimCall(oper_len,[EId("x")]),
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

    pNAMECON = "," + pNAME
    pNAMECON.setParseAction(lambda result: result[1])

    pNAMES = pNAME + ZeroOrMore(pNAMECON)
    pNAMES.setParseAction(lambda result: [result])

    pINTEGER = Word("0123456789")
    pINTEGER.setParseAction(lambda result: EValue(VInteger(int(result[0]))))

    QUOTE = Literal("&\"") | Literal("&\'") 
    pSTRING = Literal('"') + ZeroOrMore(Combine( Word(idChars+"0123456789'"+" ") | QUOTE)) + Literal('"')
    pSTRING.setParseAction(lambda result: EValue(VString(str(result[1:-1]))))

    pBOOLEAN = Keyword("true") | Keyword("false")
    pBOOLEAN.setParseAction(lambda result: EValue(VBoolean(result[0]=="true")))

    pEXPR = Forward()
    pEXPR2 = Forward()
    pSTMT_BLOCK = Forward()
    pSTMT = Forward()

    pEXPRS = ZeroOrMore(pEXPR)
    pEXPRS.setParseAction(lambda result: [result])

    pIF = pEXPR + Keyword("?") + pEXPR + Keyword(':') + pEXPR
    pIF.setParseAction(lambda result: EIf(result[0], result[2], result[4]))


    def mkFunBody (params,body):
        bindings = [ (p,ERefCell(EId(p))) for p in params ]
        return ELet(bindings,body)

    def mkLetBody (bindings,body):
        bindings = [ (p[0],ERefCell(p[1])) for p in bindings ]
        return ELet(bindings,body)

    def multiCall(result):
        first = ECall(result[1][0][0],[result[0], result[1][0][1]])
        for i in range(1, len(result[1])):
            first = ECall(result[1][i][0], [first, result[1][i][1]])
        return first

    pFUN = Keyword("fun") + "(" + pNAMES + ")" + pSTMT
    pFUN.setParseAction(lambda result: EFunction(result[2],mkFunBody(result[2],result[4])))

    pFUNR = Keyword("fun") + pNAME + "(" + pNAMES + ")" + pSTMT
    pFUNR.setParseAction(lambda result: EFunction(result[3],mkFunBody(result[3],result[5]), result[1]))

    pEXPR2CAR = "," + pEXPR2
    pEXPR2CAR.setParseAction(lambda result: result[1])

    pEXPR2MULTI = pEXPR2 + ZeroOrMore(pEXPR2CAR)
    pEXPR2MULTI.setParseAction(lambda result: [result])

    pFUNCALL = pIDENTIFIER + "(" + pEXPR2MULTI + ")"
    pFUNCALL.setParseAction(lambda result: ECall(result[0], result[2]))

    pBINDINGCAR = "," + pNAME + "=" + pEXPR2
    pBINDINGCAR.setParseAction(lambda result: (result[1], result[3]))
    
    pBINDINGCON = pNAME + "=" + pEXPR2
    pBINDINGCON.setParseAction(lambda result: (result[0], result[2]))

    pBINDINGS = pBINDINGCON  + ZeroOrMore(pBINDINGCAR)
    pBINDINGS.setParseAction(lambda result: [result])

    pLET = Keyword("let") + "(" + pBINDINGS + ")" + pEXPR2
    pLET.setParseAction(lambda result: mkLetBody(result[2], result[4]))

    pCALLG = pIDENTIFIER + pEXPR2
    pCALLG.setParseAction(lambda result: (result[0], result[1]))

    pCALL1S = OneOrMore(pCALLG)
    pCALL1S.setParseAction(lambda result: [ result ])

    pCALL =  pEXPR + pCALL1S 
    pCALL.setParseAction(multiCall)

    pCALL1 = pIDENTIFIER + pEXPR2
    pCALL1.setParseAction(lambda result: ECall(result[0], [result[1]]))

    pNOT = "not" + pEXPR2
    pNOT.setParseAction(lambda result: EPrimCall(oper_not, [result[1]]))

    pARRAYITEM = "," + pEXPR
    pARRAYITEM.setParseAction(lambda result: (result[1]))

    pARRAYITEMS = ZeroOrMore(pARRAYITEM)
    pARRAYITEMS.setParseAction(lambda result: [result])

    pARRAY = "[" + pEXPR + pARRAYITEMS + "]"
    pARRAY.setParseAction(lambda result: EArray(result[1],result[2]))

    pDICTPAIR = pNAME + ":" + pEXPR
    pDICTPAIR.setParseAction(lambda result: (result[0],result[2]))

    pDICTPAIRWITHCOMMA = "," + pNAME + ":" + pEXPR
    pDICTPAIRWITHCOMMA.setParseAction(lambda result: (result[1],result[3]))

    pDICTS = ZeroOrMore(pDICTPAIRWITHCOMMA)
    pDICTS.setParseAction(lambda result: [ result ])

    pDICT = "{" + pDICTPAIR + pDICTS + "}"
    pDICT.setParseAction(lambda result:EDict(result[1],result[2]))

    pEXPR2P = "(" + pEXPR2 + ")"
    pEXPR2P.setParseAction(lambda result: result[1])

    pACCESS = pNAME + "[" + pEXPR + "]"
    pACCESS.setParseAction(lambda result: EPrimCall(oper_access_arr,[EId(result[0]),result[2]]))

    pLEN = Keyword("len") + "(" + pNAME + ")"
    pLEN.setParseAction(lambda result: EPrimCall(oper_len,[EId(result[2])]))

    pEXPR << ( pEXPR2P | pINTEGER | pNOT | pARRAY | pACCESS | pDICT | pSTRING | pBOOLEAN | pIDENTIFIER | pCALL1 | pLEN )

    pEXPR2 << ( pLET | pFUN | pFUNR | pFUNCALL | pIF | pCALL | pEXPR)

    pDECL_VAR_E = "var" + pNAME + ";"
    pDECL_VAR_E.setParseAction(lambda result: (result[1], EValue(VNone)))

    pDECL_VAR = "var" + pNAME + "=" + pEXPR2 + ";"
    pDECL_VAR.setParseAction(lambda result: (result[1],result[3]))

    pDECL_PROCEDURE = "def" + pNAME + "(" + pNAMES + ")" + pSTMT
    pDECL_PROCEDURE.setParseAction(lambda result: (result[1], EProcedure(result[3], mkFunBody(result[3], result[5]))))

    # hack to get pDECL to match only PDECL_VAR (but still leave room
    # to add to pDECL later)
    pDECL = ( pDECL_VAR_E | pDECL_VAR | pDECL_PROCEDURE | NoMatch() | ";" )

    pDECLS = ZeroOrMore(pDECL)
    pDECLS.setParseAction(lambda result: [result])

    pSTMT_IF_1 = "if (" + pEXPR2 + ")" + pSTMT + "else" + pSTMT
    pSTMT_IF_1.setParseAction(lambda result: EIf(result[1],result[3],result[5]))

    pSTMT_IF_2 = "if (" + pEXPR2 + ")" + pSTMT
    pSTMT_IF_2.setParseAction(lambda result: EIf(result[1],result[3],EValue(VBoolean(True))))
   
    pSTMT_WHILE = "while (" + pEXPR2 + ")" + pSTMT
    pSTMT_WHILE.setParseAction(lambda result: EWhile(result[1],result[3]))

    pSTMT_FOR = "for (" + pNAME + "in" + pEXPR2 + ")" + pSTMT
    pSTMT_FOR.setParseAction(lambda result: EFor(result[1], result[3], result[5]))

    pSTMT_PRINT_STMS = "," + pEXPR2
    pSTMT_PRINT_STMS.setParseAction(lambda result: [ result[1] ])

    pSTMT_PRINT_ZERO = ZeroOrMore(pSTMT_PRINT_STMS)
    pSTMT_PRINT_ZERO.setParseAction(lambda result: [ result ])

    def printStmEval(result):
        newArray = []
        newArray.append(result[1])
        for i in result[2]:
            newArray.append(i)
        return EPrimCall(oper_print,newArray)

    pSTMT_PRINT = "print" + pEXPR2 + pSTMT_PRINT_ZERO + ";"
    pSTMT_PRINT.setParseAction(printStmEval)

    # pSTMT_PRINT = "print" + pEXPR2 + ";"
    # pSTMT_PRINT.setParseAction(lambda result: EPrimCall(oper_print,[result[1]]));

    pSTMT_UPDATE_ARR = pNAME + "[" + pINTEGER +"]" + "=" + pEXPR + ";"
    pSTMT_UPDATE_ARR.setParseAction(lambda result: EPrimCall(oper_update_arr,[EId(result[0]),result[2],result[5]]))

    pSTMT_UPDATE = pNAME + "=" + pEXPR2 + ";"
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

    pSTMT << ( pSTMT_IF_1 | pSTMT_IF_2 | pSTMT_WHILE | pSTMT_FOR | pSTMT_PRINT | pSTMT_UPDATE_ARR | pSTMT_UPDATE |  pSTMT_PROCEDURE | pSTMT_BLOCK | pEXPR2)

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




def tryImp(env, inp):
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


def shell_imp ():

    # A simple shell
    # Repeatedly read a line of input, parse it, and evaluate the result

    print "Homework 6 - Imp Language"
    print "#quit to quit, #abs to see abstract representation"
    env = initial_env_imp()
    if len(sys.argv) == 2:
        fileName = sys.argv[1]
        # with open(fileName) as f:
        #     mylist = f.read().splitlines()
        # line = ""
        # for each in mylist:
        #     if each.endswith("};"):

        #         line+=each
        #         print line
        #         tryImp(env,line)
        #         line = ""
        #         print line
        #     else:
        #         line+=each

        # tryImp(env,"main();")

        f = open(fileName)
        for each in f:
            tryImp(env,each)

    else:
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
                print inp
            tryImp(env,inp)
                

shell_imp ()