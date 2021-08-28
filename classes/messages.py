import time
from tkinter import StringVar, IntVar

class Messages:
    def __init__(self, other):
        self.stack = [] 
        self.max = 6 #max number of messages geted
        self.length = 0 
        self.beg = 0 #beginning index
        self.string = StringVar(other.window, ' \n \n \n \n \n ') #empty 6 lines

    def post(self,msg): #top of stack is 0th index
        self.stack.insert(0,msg)
        self.length += 1 
        self.beg = 0
        return self.get()
        
    def up(self):
        if self.length - self.beg > self.max:
            print('debug')
            self.beg += 1    
        return self.get() 

    def down(self):
        if self.beg != 0:
            self.beg -= 1
        return self.get()

    def get(self): #return message box 
        temp = []
        i = self.beg 
        for j in range(self.max):
            if i < self.length:
                temp.insert(0,self.stack[i])
                i+= 1
            else:
                break
        
        while len(temp) != 6:
            temp.append('')

        self.string = '\n'.join(temp)
        return self.string


if __name__ == '__main__':
    messages = Messages()
    for i in range(10):
        messages.post(str(i))
    print(messages.get())
    print('\ngoing up...\n')
    print(messages.down())
    print(messages.up())
    