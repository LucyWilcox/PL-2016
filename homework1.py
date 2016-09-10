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

def pair (v): return (v.get(0).value,v.get(1).value)

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
        return self.vector[n].eval()

class VRational (Value):
    def __init__ (self, n, d):
        self.type = "rational"
        self.numer = n
        self.denom = d

# print VVector([VInteger(10),VInteger(20),VInteger(30)]).length

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

class ERational (Exp):
    # Rational literal

    def __init__ (self, r1, r2):
        self.numer = r1
        self.denom = r2

    def __str__ (self):
        return "ERational({},{})".format(self.numer, self.denom)

    def eval (self):
        return VRational(self.numer, self.denom)



class EPlus (Exp):
    # Addition operation

    def __init__ (self,e1,e2):
        self._exp1 = e1
        self._exp2 = e2

    def __str__ (self):
        return "EPlus({},{})".format(self._exp1,self._exp2)

    def eval (self):
        v1 = self._exp1.eval()
        v2 = self._exp2.eval()
        if v1.type == "vector":
            sum_vector = []
            for i in range(len(v1.vector)):
                sum_vector.append(EPlus(v1.vector[i], v2.vector[i]))
            return VVector(sum_vector)
        elif v1.type == "integer" and v2.type == "integer":
            return VInteger(v1.value + v2.value)
        raise Exception ("Runtime error: trying to add non-numbers")

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
                minus_vector.append(EMinus(v1.vector[i], v2.vector[i]))
            return VVector(minus_vector)
        if v1.type == "integer" and v2.type == "integer":
            return VInteger(v1.value - v2.value)
        raise Exception ("Runtime error: trying to subtract non-numbers")


class ETimes (Exp):
    # Multiplication operation

    def __init__ (self,e1,e2):
        self._exp1 = e1
        self._exp2 = e2

    def __str__ (self):
        return "ETimes({},{})".format(self._exp1,self._exp2)

    def eval (self):
        v1 = self._exp1.eval()
        v2 = self._exp2.eval()
        if v1.type == "vector":
            dot_product = EInteger(0)
            for i in range(len(v1.vector)):
                v_times = ETimes(v1.vector[i], v2.vector[i]).eval().value
                e_times = EInteger(v_times)
                v_plus = EPlus(dot_product, e_times).eval().value
                dot_product = EInteger(v_plus)
            return dot_product.eval()
        if v1.type == "integer" and v2.type == "integer":
            return VInteger(v1.value * v2.value)
        raise Exception ("Runtime error: trying to multiply non-numbers")


class EIf (Exp):
    # Conditional expression

    def __init__ (self,e1,e2,e3):
        self._cond = e1
        self._then = e2
        self._else = e3

    def __str__ (self):
        return "EIf({},{},{})".format(self._cond,self._then,self._else)

    def eval (self):
        v = self._cond.eval()
        if v.type != "boolean":
            raise Exception ("Runtime error: condition not a Boolean")
        if v.value:
            return self._then.eval()
        else:
            return self._else.eval()



class EIsZero (Exp):
    def __init__ (self,e):
        self._exp=e
    def eval(self):
        v=self._exp.eval()
        if v.type != "integer":
            raise Exception ("Runtime error: not an integer")
        return EIf(EBoolean(v.value==0),EBoolean(True),EBoolean(False)).eval()
# EIsZero(EBoolean(True)).eval().value
# print EIsZero(EPlus(EInteger(1),EInteger(1))).eval().value

class EAnd(Exp):
    def __init__ (self,e1,e2):
        self._exp1=e1
        self._exp2=e2
    def eval(self):
        v1=self._exp1.eval()
        v2=self._exp2.eval()
        if v1.type == "vector":
            sum_vector = []
            for i in range(len(v1.vector)):
                sum_vector.append(EAnd(v1.vector[i], v2.vector[i]))
            return VVector(sum_vector)
        if v1.type == "boolean" and v2.type == "boolean":
            return EIf(EBoolean(v1.value==False),EBoolean(False),EIf(EBoolean(v2.value==False),EBoolean(False),EBoolean(True))).eval()
        raise Exception ("Runtime error: conditions are not booleans")
# EAnd(EInteger(12),EBoolean(False)).eval().value     
# print EAnd(EBoolean(True),EBoolean(False)).eval().value
# print EAnd(EBoolean(True),EBoolean(True)).eval().value
# print EAnd(EBoolean(False),EBoolean(False)).eval().value
# print EAnd(EBoolean(False),EBoolean(True)).eval().value

class EOr(Exp):
    def __init__ (self,e1,e2):
        self._exp1=e1
        self._exp2=e2
    def eval(self):
        v1=self._exp1.eval()
        v2=self._exp2.eval()
        if v1.type == "vector":
            sum_vector = []
            for i in range(len(v1.vector)):
                sum_vector.append(EOr(v1.vector[i], v2.vector[i]))
            return VVector(sum_vector)
        if v1.type == "boolean" and v2.type == "boolean":
            return EIf(EBoolean(v1.value==True),EBoolean(True),EIf(EBoolean(v2.value==True),EBoolean(True),EBoolean(False))).eval()
        raise Exception ("Runtime error: conditions are not booleans")

# EOr(EInteger(12),EBoolean(False)).eval().value     
# print EOr(EBoolean(True),EBoolean(False)).eval().value
# print EOr(EBoolean(True),EBoolean(True)).eval().value
# print EOr(EBoolean(False),EBoolean(False)).eval().value
# print EOr(EBoolean(False),EBoolean(True)).eval().value

class ENot(Exp):
    def __init__ (self,e):
        self._exp=e
    def eval(self):
        v=self._exp.eval()
        if v.type == "vector":
            sum_vector = []
            for i in range(len(v.vector)):
                sum_vector.append(ENot(v.vector[i]))
            return VVector(sum_vector)
        if v.type == "boolean":
            return EBoolean(not v.value).eval()
        raise Exception ("Runtime error: condition is not boolean")
# ENot(EInteger(12)).eval().value     
# print ENot(EBoolean(False)).eval().value
# print ENot(EBoolean(True)).eval().value

class EVector(Exp):
    def __init__ (self, e):
        self.vector = e

    def eval(self):
        return VVector(self.vector)

# print EVector([]).eval().length
# print EVector([EInteger(10),EInteger(20),EInteger(30)]).eval().length
# print EVector([EPlus(EInteger(1),EInteger(2)),EInteger(0)]).eval().get(1).value
# print EVector([EBoolean(True),EAnd(EBoolean(True),EBoolean(False))]).eval().get(0).value
# print EVector([EBoolean(True),EAnd(EBoolean(True),EBoolean(False))]).eval().get(1).value

class EDiv(Exp):
    def __init__ (self, e1, e2):
        self.e1 = e1
        self.e2 = e2

    def __str__(self):
        return "EDiv({},{})".format(self.e1, self.e2)

    def eval(self):
        v1 = self.e1.eval()
        v2 = self.e2.eval()
        if v1.type == "integer":
            v1 = VRational(v1.value, VInteger(1).value)
        if v2.type == "integer":
            v2 = VRational(v2.value, VInteger(1).value)
        v1_type = getattr(v1, "type", False)
        v2_type = getattr(v2, "type", False)
        numer = ETimes(EInteger(v1.numer), EInteger(v2.denom)).eval().value
        denom = ETimes(EInteger(v2.numer), EInteger(v1.denom)).eval().value   
        return VRational(EInteger(numer).eval().value, EInteger(denom).eval().value)


print rat(EDiv(EInteger(1),EInteger(2)).eval())
#'1/2'
print rat(EDiv(EInteger(2),EInteger(3)).eval())
# # '2/3'
print rat(EDiv(EDiv(EInteger(2),EInteger(3)),EInteger(4)).eval())
# # '1/6'
print  rat(EDiv(EInteger(2),EDiv(EInteger(3),EInteger(4))).eval())
# # '8/3'

#print EPlus(EInteger(9), EInteger(8)).eval().value
# print pair(EPlus(EVector([EInteger(2),EInteger(3)]), EVector([EInteger(33),EInteger(66)])).eval())
# print pair(EMinus(EVector([EInteger(2),EInteger(3)]), EVector([EInteger(33),EInteger(66)])).eval())

# b1 = EVector([EBoolean(True),EBoolean(False)])
# b2 = EVector([EBoolean(False),EBoolean(False)])

# print pair(EAnd(b1,b2).eval())
# print pair(EOr(b1,b2).eval())
# print pair(ENot(b1).eval())

v1 = EVector([EInteger(2),EInteger(3)])
v2 = EVector([EInteger(33),EInteger(66)])

# print ETimes(v1,v2).eval().value
# # 264
# print ETimes(v1,EPlus(v2,v2)).eval().value
# # 528
# print ETimes(v1,EMinus(v2,v2)).eval().value
# # 0