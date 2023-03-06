class A(object):
    def __init__(self, *args, **kwargs):
        print("Init A.")
        self.text = "I'm A."


class B(object):
    def __init__(self, *args, **kwargs):
        print("Init B.")
        self.a = A()
        a = self.a

        a.text = "I'm modified by B"


b = B()
print(b.a.text)
