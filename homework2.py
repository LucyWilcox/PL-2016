############################################################
# HOMEWORK 2
#
# Team members:
#
# Emails:
#
# Remarks:
#



#
# Expressions
#

class Exp (object):
    pass



class EInteger (Exp):
    # Integer literal

    def __init__ (self,i):
        self._integer = i

    def __str__ (self):
        return "EInteger({})".format(self._integer)

    def eval (self,prim_dict):
        return VInteger(self._integer)

    def substitute (self,id,new_e):
        return self


class EBoolean (Exp):
    # Boolean literal

    def __init__ (self,b):
        self._boolean = b

    def __str__ (self):
        return "EBoolean({})".format(self._boolean)

    def eval (self,prim_dict):
        return VBoolean(self._boolean)

    def substitute (self,id,new_e):
        return self


class EPrimCall (Exp):

    def __init__ (self,name,es):
        self._name = name
        self._exps = es

    def __str__ (self):
        return "EPrimCall({},[{}])".format(self._name,",".join([ str(e) for e in self._exps]))

    def eval (self,prim_dict):
        vs = [ e.eval(prim_dict) for e in self._exps ]
        return apply(prim_dict[self._name],vs)

    def substitute (self,id,new_e):
        new_es = [ e.substitute(id,new_e) for e in self._exps]
        return EPrimCall(self._name,new_es)


class EIf (Exp):
    # Conditional expression

    def __init__ (self,e1,e2,e3):
        self._cond = e1
        self._then = e2
        self._else = e3

    def __str__ (self):
        return "EIf({},{},{})".format(self._cond,self._then,self._else)

    def eval (self,prim_dict):
        v = self._cond.eval(prim_dict)
        if v.type != "boolean":
            raise Exception ("Runtime error: condition not a Boolean")
        if v.value:
            return self._then.eval(prim_dict)
        else:
            return self._else.eval(prim_dict)

    def substitute (self,id,new_e):
        return EIf(self._cond.substitute(id,new_e),
                   self._then.substitute(id,new_e),
                   self._else.substitute(id,new_e))


class ELet (Exp):
    # local binding

    def __init__ (self,id,e1,e2):
        self._id = id
        self._e1 = e1
        self._e2 = e2

    def __str__ (self):
        return "ELet({},{},{})".format(self._id,self._e1,self._e2)

    def eval (self,prim_dict):
        new_e2 = self._e2.substitute(self._id,self._e1)
        return new_e2.eval(prim_dict)

    def substitute (self,id,new_e):
        if id == self._id:
            print "in"
            return ELet(self._id,
                        self._e1.substitute(id,new_e),
                        self._e2)
        return ELet(self._id,
                    self._e1.substitute(id,new_e),
                    self._e2.substitute(id,new_e))


class ELetN (Exp):
    # local binding

    def __init__ (self,bindings,exp):
        self._bindings = bindings
        self._exp = exp

    def __str__ (self):
        return "ELetN({},{})".format(self._bindings,self._exp)

    def eval (self,prim_dict):
        for i in self._bindings:
            self._exp = self._exp.substitute(i[0], i[1])
        return self._exp.eval(prim_dict)

    def substitute (self, i1, i2):
        if i1 not in [x[0] for x in self._bindings]:
            return ELetN(self._bindings, self._exp.substitute(i1, i2))
        else:
            bindings = self._bindings
            for b in self._bindings:
                if i1 == b[0]:
                    bindings.remove(b)
                    bindings.append((b[1]._id, i2))
                return ELetN(bindings, self._exp)

class ELetS (Exp):
    # local binding

    def __init__ (self,bindings,exp):
        self._bindings = bindings
        self._exp = exp

    def __str__ (self):
        return "ELetS({},{})".format(self._bindings,self._exp)

    def eval (self,prim_dict):
        for i in self._bindings:
            self._exp = self._exp.substitute(i[0], i[1])
        return self._exp.eval(prim_dict)

    def substitute (self, i1, i2):
        if i1 not in [x[0] for x in self._bindings]:
            return ELetN(self._bindings, self._exp.substitute(i1, i2))
        else:
            bindings = self._bindings
            for b in self._bindings:
                if i1 == b[0]:
                    bindings.remove(b)
                    bindings.append((b[1]._id, i2))
                return ELetN(bindings, self._exp)

class EId (Exp):
    # identifier

    def __init__ (self,id):
        self._id = id

    def __str__ (self):
        return "EId({})".format(self._id)

    def eval (self,prim_dict):
        raise Exception("Runtime error: unknown identifier {}".format(self._id))

    def substitute (self,id,new_e):
        if id == self._id:
            return new_e
        return self

    
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

class VBoolean (Value):
    # Value representation of Booleans
    def __init__ (self,b):
        self.value = b
        self.type = "boolean"


# Primitive operations

def oper_plus (v1,v2): 
    if v1.type == "integer" and v2.type == "integer":
        return VInteger(v1.value + v2.value)
    raise Exception ("Runtime error: trying to add non-numbers")

def oper_minus (v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VInteger(v1.value - v2.value)
    raise Exception ("Runtime error: trying to add non-numbers")

def oper_times (v1,v2):
    if v1.type == "integer" and v2.type == "integer":
        return VInteger(v1.value * v2.value)
    raise Exception ("Runtime error: trying to add non-numbers")


# Initial primitives dictionary

INITIAL_PRIM_DICT = {
    "+": oper_plus,
    "*": oper_times,
    "-": oper_minus
}

print ELet('x', EInteger(10), EPrimCall("+", [EId('x'), EId('x')])).eval(INITIAL_PRIM_DICT).value
print ELetN([('x',EInteger(10)), ('y', EInteger(9))], EPrimCall("*", [EId('x'), EId('y')])).eval(INITIAL_PRIM_DICT).value
print ELetN([("x",EInteger(10)), ("y",EInteger(20)),("z",EInteger(30))],
       EPrimCall("*", [EPrimCall("+",[EId("x"),EId("y")]),EId("z")])).eval(INITIAL_PRIM_DICT).value
print ELetN([("a",EInteger(5)),
        ("b",EInteger(20))],
       ELetN([("a",EId("b")),
             ("b",EId("a"))],
            EPrimCall("-",[EId("a"),EId("b")]))).eval(INITIAL_PRIM_DICT).value
