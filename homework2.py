"""############################################################
# HOMEWORK 2
#
# Team members:
#
# Emails:
#
# Remarks:
#We used:
 https://docs.racket-lang.org/guide/let.html, 
 https://books.google.com/books?id=YeJL2kechd8C&pg=PA27&lpg=PA27&dq=sequential+bindings+programming+languages&source=bl&ots=i6lZ7A-t1I&sig=GFUbweJeFPwCAFxchZGIrnCBmyc&hl=en&sa=X&ved=0ahUKEwih8ubynpfPAhVk5IMKHWDgBQsQ6AEIIzAB#v=onepage&q=sequential%20bindings%20programming%20languages&f=false
 to help us understand the bindings stuff

 We found this assignment pretty hard and went down a few wrong turns
 before realizing that what we were doing was a lot more complecated
 than it needed to be
"""

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


# class ELet (Exp):
#     # local binding

#     def __init__ (self,id,e1,e2):
#         self._id = id
#         self._e1 = e1
#         self._e2 = e2

#     def __str__ (self):
#         return "ELet({},{},{})".format(self._id,self._e1,self._e2)

#     def eval (self,prim_dict):
#         new_e2 = self._e2.substitute(self._id,self._e1)
#         return new_e2.eval(prim_dict)

#     def substitute (self,id,new_e):
#         if id == self._id:
#             print "in"
#             return ELet(self._id,
#                         self._e1.substitute(id,new_e),
#                         self._e2)
#         return ELet(self._id,
#                     self._e1.substitute(id,new_e),
#                     self._e2.substitute(id,new_e))


class ELet (Exp):
    # binding simultaneously

    def __init__ (self,bindings,exp):
        self._bindings = bindings
        self._exp = exp

    def __str__ (self):
        return "ELet({},{})".format(self._bindings,self._exp)

    def eval (self,prim_dict):
        for i in self._bindings:
            self._exp = self._exp.substitute(i[0], i[1])
        return self._exp.eval(prim_dict)

    def substitute (self, id, new_e):
        new_bindings = []
        for b in self._bindings:
            new_bindings.append((b[0], b[1].substitute(id, new_e)))

        if id in [x[0] for x in self._bindings]:
            return ELet(new_bindings, self._exp)
        return ELet(new_bindings, self._letExp.substitute(id, new_e))
        

class ELetS (Exp):
# sequential binding

    def __init__ (self,bindings,exp):
        self._bindings = bindings
        self._exp = exp

    def __str__ (self):
        return "ELetS({},{})".format(self._id,self._e1,self._e2)

    def eval (self,prim_dict):
        for i in self._bindings:
            self._exp = self._exp.substitute(i[0], i[1]) 
        return self._exp.eval(prim_dict)

    def substitute (self,id,new_e):
        new_binds = []
        for (b1, b2) in self._bindings:
            for nb in new_binds:
                #going down to get what b2 should really be before adding
                b2 = b2.substitute(nb[0], nb[1])
            new_binds.append((b1, b2))

        if id in [x[0] for x in self._bindings]:
            return ELet(new_binds, self._exp)
        return ELet(new_binds, self._exp.substitute(id, new_e))
     
class ELetV (Exp):
    # local binding

    def __init__ (self,id,e1,e2):
        self._id = id
        self._e1 = e1
        self._e2 = e2

    def __str__ (self):
        return "ELetV({},{},{})".format(self._id,self._e1,self._e2)

    def eval (self,prim_dict):
        print EInteger(self._e1.eval(INITIAL_PRIM_DICT).value)
        new_e2 = self._e2.substitute(self._id,EInteger(self._e1.eval(INITIAL_PRIM_DICT).value))
        return new_e2.eval(prim_dict)

    def substitute (self,id,new_e):
        print ("new_e",new_e.eval(INITIAL_PRIM_DICT).value)
        if id == self._id:
            return ELetV(self._id,
                        self._e1.substitute(id,new_e),
                        self._e2)
        return ELetV(self._id,
                    self._e1.substitute(id,new_e),
                    self._e2.substitute(id,new_e))

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


# Tests for 1a
# print ELet([('x',EInteger(10)), ('y', EInteger(9))], EPrimCall("*", [EId('x'), EId('y')])).eval(INITIAL_PRIM_DICT).value
# print ELet([("x",EInteger(10)), ("y",EInteger(20)),("z",EInteger(30))],
#        EPrimCall("*", [EPrimCall("+",[EId("x"),EId("y")]),EId("z")])).eval(INITIAL_PRIM_DICT).value
# print ELet([("a",EInteger(5)),
#         ("b",EInteger(20))],
#        ELet([("a",EId("b")),
#              ("b",EId("a"))],
#             EPrimCall("-",[EId("a"),EId("b")]))).eval(INITIAL_PRIM_DICT).value
# print ELet([("a",EInteger(99))],EId("a")).eval(INITIAL_PRIM_DICT).value
# print ELet([("a",EInteger(99)),
#           ("b",EInteger(66))],EId("a")).eval(INITIAL_PRIM_DICT).value
# print ELet([("a",EInteger(99)),
#           ("b",EInteger(66))],EId("b")).eval(INITIAL_PRIM_DICT).value
# print ELet([("a",EInteger(99))],
#          ELet([("a",EInteger(66)),
#                ("b",EId("a"))],
#               EId("a"))).eval(INITIAL_PRIM_DICT).value
# print ELet([("a",EInteger(99))],
#          ELet([("a",EInteger(66)),
#                ("b",EId("a"))],
#               EId("b"))).eval(INITIAL_PRIM_DICT).value


#Tests for 1b
# print ELetS([("a",EInteger(99))],EId("a")).eval(INITIAL_PRIM_DICT).value
# print ELetS([("a",EInteger(99)),
#            ("b",EInteger(66))],EId("a")).eval(INITIAL_PRIM_DICT).value
# print ELetS([("a",EInteger(99)),
#            ("b",EInteger(66))],EId("b")).eval(INITIAL_PRIM_DICT).value
# print ELet([("a",EInteger(99))],
#          ELetS([("a",EInteger(66)),
#                 ("b",EId("a"))],
#                EId("a"))).eval(INITIAL_PRIM_DICT).value
# print ELet([("a",EInteger(99))],
#          ELetS([("a",EInteger(66)),
#                 ("b",EId("a"))],
#                EId("b"))).eval(INITIAL_PRIM_DICT).value
# print ELetS([("a",EInteger(5)),
#            ("b",EInteger(20))],
#           ELetS([("a",EId("b")),
#                  ("b",EId("a"))],
#                 EPrimCall("-",[EId("a"),EId("b")]))).eval(INITIAL_PRIM_DICT).value

#Tests for Problem 2
# print ELetV("a",EInteger(10),EId("a")).eval(INITIAL_PRIM_DICT).value
# print ELetV("a",EInteger(10),
#           ELetV("b",EInteger(20),EId("a"))).eval(INITIAL_PRIM_DICT).value
# print ELetV("a",EInteger(10),
#           ELetV("a",EInteger(20),EId("a"))).eval(INITIAL_PRIM_DICT).value
# print ELetV("a",EPrimCall("+",[EInteger(10),EInteger(20)]),
#           ELetV("b",EInteger(20),EId("a"))).eval(INITIAL_PRIM_DICT).value
# print ELetV("a",EPrimCall("+",[EInteger(10),EInteger(20)]),
#           ELetV("b",EInteger(20),
#                 EPrimCall("*",[EId("a"),EId("a")]))
#           ).eval(INITIAL_PRIM_DICT).value