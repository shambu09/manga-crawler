class Pipe:
    def __init__(self, funcs, remove_null=False):
        self.funcs = funcs
        self.remove_null = remove_null
        self.wrap()

    def wrap(self):
        for i in range(len(self.funcs)):
            if (self.funcs[i].__defaults__ == None
                    or self.funcs[i].__defaults__.count("__no_wrap__") == 0):
                self.funcs[i] = self.__wrap(self.funcs[i])
            else:
                self.funcs[i] = self.__remove_null(self.funcs[i])

    def __wrap(self, func):
        def wrapper(seq):
            for i in range(len(seq)):
                seq[i] = func(seq[i])
                if self.remove_null and seq[i] == None:
                    seq.pop(i)
            return seq

        return wrapper

    def __remove_null(self, func):
        def wrapper(seq):
            if seq == None: return seq
            seq = func(seq)
            if seq == None: return seq

            if self.remove_null:
                for i in range(len(seq)):
                    if seq[i] == None: seq.pop(i)

            return seq

        return wrapper

    def __call__(self, seq):
        for func in self.funcs:
            seq = func(seq)
        return seq

    @classmethod
    def customize(cls, *agrs1, **kwargs1):
        def decorator(func):
            wrap = "__wrap__"
            if (func.__defaults__ != None
                    and func.__defaults__.count("__no_wrap__") != 0):
                wrap = "__no_wrap__"

            def wrapper(x, wrap=wrap):
                return func(x, *agrs1, **kwargs1)

            return wrapper

        return decorator
