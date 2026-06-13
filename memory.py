class SharedMemory:

    def __init__(self):
        self.store = {}

    def write(self,key,value):
        self.store[key] = value

    def read(self,key):
        return self.store.get(key)

    def get_all(self):
        return self.store