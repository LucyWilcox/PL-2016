############################################################
# HOMEWORK 1
#
# Team members:
#
# Emails:
#
# Remarks:
#

#
# Helper Functions 
#

import unittest

def pair (v): return (v.get(0).value, v.get(1).value)

def rat (v):
    return "{}/{}".format(v.numer, v.denom)

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


class VVector (Value):
    def __init__ (self, v):
        self.length = len(v)
        self.type = "vector"
        self.vector = v
    def get(self, n):
        return self.vector[n]


class VRational (Value):
    def __init__ (self, n, d):
        self.type = "rational"
        self.numer = n
        self.denom = d


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

    def eval (self):
        return VInteger(self._integer)


class EBoolean (Exp):
    # Boolean literal

    def __init__ (self,b):
        self._boolean = b

    def __str__ (self):
        return "EBoolean({})".format(self._boolean)

    def eval (self):
        return VBoolean(self._boolean)
        
class EInteger (Exp):
    # Integer literal

    def __init__ (self,i):
        self._integer = i

    def __str__ (self):
        return "EInteger({})".format(self._integer)

    def eval (self):
        return VInteger(self._integer)



class ERational (Exp):
    # Rational literal

    def __init__ (self, r1, r2):
        self.numer = r1
        self.denom = r2

    def __str__ (self):
        return "ERational({},{})".format(self.numer, self.denom)

    def eval (self):
        return VRational(self.numer, self.denom)

class VInteger (Value):
    # Value representation of integers
    def __init__ (self,i):
        self.value = i
        self.type = "integer"


class EMinus (Exp):
    # Subtraction operation

    def __init__ (self,e1,e2):
        self._exp1 = e1
        self._exp2 = e2

    def __str__ (self):
        return "EMinus({},{})".format(self._exp1,self._exp2)

    def eval (self):
        v1 = self._exp1.eval()
        v2 = self._exp2.eval()
        if v1.type == "vector":
            minus_vector = []
            for i in range(len(v1.vector)):
                minus_vector.append(EMinus(EInteger(v1.vector[i].value), EInteger(v2.vector[i].value)).eval())
            return VVector(minus_vector)
        if v1.type == "integer" and v2.type == "integer":
            return VInteger(v1.value - v2.value)
        if v1.type == "rational" or v2.type == "rational":
            if v1.type == "integer":
                v1 = VRational(v1.value, VInteger(1).value)
            if v2.type == "integer":
                v2 = VRational(v2.value, VInteger(1).value)
            left = ETimes(EInteger(v1.numer), EInteger(v2.denom)).eval().value
            right = ETimes(EInteger(v1.denom), EInteger(v2.numer)).eval().value
            numer = EMinus(EInteger(left),EInteger(right)).eval().value
            denom = ETimes(EInteger(v2.denom), EInteger(v1.denom)).eval().value
            return VRational(EInteger(numer).eval().value, EInteger(denom).eval().value)

        raise Exception ("Runtime error: trying to subtract non-numbers")


class EVector(Exp):
    def __init__ (self, e):
        self.vector = e

    def eval(self):
        for i, v in enumerate(self.vector):
            self.vector[i] = v.eval()
        return VVector(self.vector)


v1 = EVector([EInteger(2),EInteger(3)])
v2 = EVector([EInteger(33),EInteger(66)])
# b1 = EVector([EBoolean(True),EBoolean(False)])
# b2 = EVector([EBoolean(False),EBoolean(False)])

# print  pair(EPlus(v1,v2).eval()) #== (35, 69)
print pair(EMinus(v1,v2).eval())# == (-31, -63)





