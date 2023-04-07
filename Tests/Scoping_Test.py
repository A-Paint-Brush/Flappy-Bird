class MainScope:
    def __init__(self):
        self.a = 10
        self.b = 20
        self.c = 30
        self.alt_obj = AltScope()

    def run(self):
        self.alt_obj.pass_func_ref(self.function)

    def function(self):
        print(self.a, self.b, self.c)


class AltScope:
    def __init__(self):
        self.alt_alt_obj = AltAltScope()

    def pass_func_ref(self, func_ref):
        self.alt_alt_obj.exec_func(func_ref)


class AltAltScope:
    def __init__(self):
        pass

    @staticmethod
    def exec_func(func_ref):
        func_ref()


if __name__ == "__main__":
    obj = MainScope()
    obj.run()
