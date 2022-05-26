# -*- coding: utf-8 -*-
"""
Created on Sun May 15 18:08:30 2022

@author: TARDIInsanity
"""

from threading import Thread
from os.path import exists
from weakref import WeakValueDictionary
import pygame as py

write_dir = None # directory to read/write files

MODULAR = WeakValueDictionary()
def modular(key:str):
    if key not in MODULAR or MODULAR[key] is None:
        exec("\n".join((
            "class Modular_{key}:",
            "    @property",
            "    def {key}(self) -> int:",
            "        return self._v{key}",
            "    @{key}.setter",
            "    def {key}(self, value:int):",
            "        self._v{key} = value % self._m{key}"
        )).format(key=key))
        MODULAR[key] = eval(f"Modular_{key}")
    return MODULAR[key]

# -*- coding: utf-8 -*-
"""

@author: Ryan
"""

eprint = lambda i: print(chr(i), end="")

HEXES = set("0123456789abcdef")

def arr_pad(array, value="."):
    widths = [len(i) for i in array]
    maw = max(widths)
    for i, w in zip(array, widths):
        i.extend([value]*(maw-w))
    return array

class Plane(modular("x"), modular("y")):
    DEFAULT = (64,64)
    def __init__(self, values=None, x:int=0, y:int=0):
        if not values or not values[0]:
            h, w = self.DEFAULT
            values = [[0 for _ in range(w)] for _ in range(h)]
        values = arr_pad(values)
        self._mx = len(values[0])
        self._my = len(values)
        self.x = x
        self.y = y
        self.values = values
    @property
    def here(self):
        return self.values[self.y][self.x]
    @here.setter
    def here(self, value):
        self.values[self.y][self.x] = value
    def move(self, dx:int, dy:int, times:int=1):
        for i in range(times):
            self.x += dx
            self.y += dy
            while self.here in (None, "."):
                self.x += dx
                self.y += dy
    @classmethod
    def empty(cls, size:tuple=None):
        if size is None:
            size = cls.DEFAULT
        return cls([[0 for _ in range(size[0])] for _ in range(size[1])])
    def op_caret(self):
        self.y -= 1
    def op_v(self):
        self.y += 1
    def op_left(self):
        self.x -= 1
    def op_right(self):
        self.x += 1
    def op_equal(self):
        pass
    def op_minus(self):
        self.here *= -1
    def op_x(self):
        self.here ^= -1
    OPS = {"^":op_caret, "v":op_v, "<":op_left, ">":op_right, "=":op_equal, "-":op_minus, "x":op_x}

class Line(modular("x")):
    DEFAULT = (1<<12,)
    def __init__(self, values=None, x:int=0):
        if not values or not values[0]:
            w, = self.DEFAULT
            values = [0 for _ in range(w)]
        self._mx = len(values)
        self.x = x
        self.values = values
    @property
    def here(self):
        return self.values[self.x]
    @here.setter
    def here(self, value):
        self.values[self.x] = value
    def move(self, dx:int, times:int=1):
        for i in range(times):
            self.x += dx
            while self.here in (None, "."):
                self.x += dx
    @classmethod
    def empty(cls, size:tuple=None):
        if size is None:
            size = cls.DEFAULT
        return cls([0 for _ in range(size[0])])
    def op_left(self):
        self.x -= 1
    def op_right(self):
        self.x += 1
    def op_equal(self):
        pass
    def op_minus(self):
        self.here *= -1
    def op_x(self):
        self.here ^= -1
    OPS = {"<":op_left, ">":op_right, "=":op_equal, "-":op_minus, "x":op_x}

class Zlist(list):
    def pop(self, index=-1):
        if not self:
            return 0
        return super().pop(index)
    def op_minus(self):
        self.append(-self.pop())
    def op_x(self):
        self.append(~self.pop())
    def op_caret(self):
        val = self.pop()
        self.extend((val, val))
    def op_v(self):
        self.pop()
    def op_left(self):
        self.append(self.pop(-1)-1)
    def op_right(self):
        self.append(self.pop(-1)+1)
    OPS = {"-":op_minus, "x":op_x, "^":op_caret, "v":op_v, "<":op_left, ">":op_right}

class Lastn(list):
    def __init__(self, iterable, n:int):
        super().__init__(iterable)
        self.n = n
        self.prune()
    def append(self, item):
        super().append(item)
        if len(self) >= self.n:
            self.prune()
    def prune(self):
        self[:-self.n] = []

class Engine:
    def __init__(self, program:Plane, memory:Line, stack:Zlist, alpha:str="p",
                 direction:tuple=(1, 0), buffer:str="", done:bool=False):
        self.program = program
        if memory is None:
            memory = Line.empty()
        self.memory = memory
        self.stack = Zlist(stack)
        self.alpha = alpha
        self.direction = direction
        self.buffer = buffer
        self.done = False
        self.recent_history = Lastn([self.prog_position], n=20)
    def step(self):
        #print("Program step: "+self.alpha+self.program.here)
        self.tick()
        self.move(1)
        self.recent_history.append(self.prog_position)
    @property
    def prog_position(self):
        return (self.program.x, self.program.y)
    def move(self, times:int):
        dx, dy = self.direction
        self.program.move(dx, dy, times)
    def tick(self):
        arg = self.program.here
        if arg == " ":
            return None # NOP
        if arg in "spijmg":
            self.alpha = arg
            return None
        code = self.alpha
        if code == "s":
            return self.s_tick(arg)
        if code == "p":
            return self.p_tick(arg)
        if code == "i":
            self.alpha = "p" # "i" only checks ONCE now
            if not self.stack.pop():
                return None
            return self.p_tick(arg)
        if code == "j":
            self.alpha = "i"
            return self.p_tick(arg)
        if code == "m":
            return self.m_tick(arg)
        if code == "g":
            return self.a_tick(arg)
    def get_char(self):
        if not self.buffer:
            self.buffer = input()
            if not self.buffer:
                self.buffer = "\n"
        first = self.buffer[0]
        self.buffer = self.buffer[1:]
        return first
    def s_tick(self, code:str):
        if code in self.stack.OPS:
            return self.stack.OPS[code](self.stack)
        if code in HEXES:
            self.stack.append(int(code, 16))
            return
        if code == "/>":
            self.stack.append(self.stack.pop()+1)
            return
        if code in "\\`<":
            self.stack.append(self.stack.pop()-1)
            return
        if code == "+":
            self.stack.append(ord(self.get_char()))
            return
        if code == "|":
            eprint(self.stack.pop())
            return
        if code == "=":
            ult = self.stack.pop()
            penult = self.stack.pop()
            self.stack.extend((ult, penult))
            return
        if code == "?":
            self.stack.append(len(self.stack))
            self.stack.append(len(self.buffer))
            return
        raise ValueError("Invalid argument for stack operation: "+code)
    def p_tick(self, code:str):
        if code in self.ROTOR:
            return self.ROTOR[code](self)
        if code in self.MOVES:
            self.direction = self.MOVES[code]
            return
        if code in HEXES:
            self.move(int(code, 16))
            return
        if code == "+":
            self.direction = (0, 0)
            self.done = True
            return
        if code == "=":
            return # NOP
        if code == "?":
            return self.quest(self.program)
        raise ValueError("Invalid argument for program operation: "+code)
    def m_tick(self, code:str):
        if code in self.memory.OPS:
            return self.memory.OPS[code](self.memory)
        if code in HEXES:
            self.memory.here = int(code, 16)
            return
        if code == "+":
            self.memory.here = ord(self.get_char())
            return
        if code == "^":
            self.stack.append(self.memory.here)
            return
        if code == "v":
            self.memory.here = self.stack.pop()
            return
        if code == "/":
            self.memory.here += 1
            return
        if code in "\\`":
            self.memory.here -= 1
            return
        if code == "|":
            eprint(self.memory.here)
            return
        if code == "?":
            self.stack.append(self.memory.x)
            return
        raise ValueError("Invalid argument for memory operation: "+code)
    def a_tick(self, code:str):
        if code in "+|-x^v<>=?":
            first = self.stack.pop()
            second = self.stack.pop()
            if code in self.INTOPS:
                self.stack.append(self.INTOPS[code](first, second))
                return
            if code in self.INTBOOL:
                self.stack.append(-self.INTBOOL[code](first, second))
                return
            if code == "v":
                self.stack.append(first << second if second >= 0 else first >> -second)
                return
            raise NotImplementedError("Invalid argument for algebraic operation: "+code
                +"; operation should have been implemented")
        if code in HEXES:
            self.stack.append(int(code, 16))
            return
        if code == "/":
            denominator = self.stack.pop()
            numerator = self.stack.pop()
            if denominator == 0:
                self.stack.extend((numerator, 0))
            else:
                self.stack.extend(divmod(numerator, denominator)[::-1])
            return
        if code in "\\`":
            self.stack.append(abs(self.stack.pop()))
            return
        raise ValueError("Invalid argument for algebraic operation: "+code)
    INTOPS = {"+":int.__add__, "|":int.__or__, "-":int.__sub__,
              "x":int.__mul__, "^":int.__xor__, "?":int.__and__}
    INTBOOL = {"<":int.__lt__, ">":int.__gt__, "=":int.__eq__}
    MOVES = {"^":(0,-1), "v":(0,1), "<":(-1,0), ">":(1,0)}
    def rot_1(self):
        self.direction = (-self.direction[1], -self.direction[0])
    def rot_2(self):
        self.direction = (self.direction[1], self.direction[0])
    #(-self.direction[1], self.direction[0]) is CLOCKWISE, NotImplemented
    #(self.direction[1], -self.direction[0]) is CCW, NotImplemented
    #(self.direction[0], self.direction[1]) is NOP
    def rot_3(self):
        self.direction = (-self.direction[0], self.direction[1])
    def rot_4(self):
        self.direction = (self.direction[0], -self.direction[1])
    def rot_5(self):
        self.direction = (-self.direction[0], -self.direction[1])
    ROTOR = {"/":rot_1, "`":rot_2, "\\":rot_2, "|":rot_3, "-":rot_4, "x":rot_5}
    
    def quest(self, plane:Plane):
        self.stack.append(plane.x)
        self.stack.append(plane.y)

# SECTION 2 #

# use for converting condensed programs to arrays
def lex_program(program_code:str):
    return [list(i) for i in program_code.replace("`","\\").split("\n")]

def parse(text:str, input_buffer:str="", *, engine_class=Engine):
    '''for purists, this is the way to make your programs.'''
    program = lex_program(text)
    return engine_class(Plane(program), None, [], buffer=input_buffer)

def string_to_engine(text:str, *, engine_class=Engine):
    values = eval(text)
    def meval(key):
        return values[key]
    program = meval("program")
    memory = meval("memory")
    px, py = meval("program_pointer")
    mx, my = meval("memory_pointer")
    program_direction = meval("program_direction")
    alpha = meval("alpha")
    stack = meval("stack")
    input_buffer = meval("input_buffer")
    done = meval("done")
    return engine_class(Plane(program, px, py), Plane(memory, mx, my), Zlist(stack), alpha=alpha,
            direction=program_direction, buffer=input_buffer, done=done)

def engine_to_string(engine:Engine):
    result = {
    "program":Engine.program.values,
    "memory":Engine.memory.values,
    "px":Engine.program.x, "py":Engine.program.y,
    "mx":Engine.memory.x, "my":Engine.memory.y,
    "program_direction":Engine.direction,
    "alpha":Engine.alpha,
    "stack":Engine.stack,
    "input_buffer":Engine.buffer,
    "done":Engine.done
    }
    return str(result)

def write_file(filename, text, append:bool=True):
    with open(write_dir+filename+".txt", "wa"[append]) as file:
        file.write(text)

def read_file(filename):
    with open(write_dir+filename+".txt", "r") as file:
        return file.read()

def save_engine(engine:Engine, filename, override:bool=False):
    path = write_dir+filename+".txt"
    if exists(path) and not override:
        print("File already exists! Try a different name or use 'override=True'")
        return engine
    write_file(filename, engine_to_string(engine))
    return engine

def load_engine(filename):
    return string_to_engine(read_file())


# SECTION 3 #

py.font.init()

cell_size = 20
#font_name = "DEJAVUSANSMONO.ttf"
font_obj = py.font.SysFont("mono", cell_size)

color_text = py.Color(250, 250, 250)
color_bg = py.Color(50, 50, 50)
color_high = py.Color(200, 125, 50)
color_strong = py.Color(250, 50, 50)

def mem_to_str(array):
    '''assumes a SMALL array'''
    buffer = []
    for i in array:
        buffer.append([])
        for j in i:
            buffer[-1].append(str(j))
    result = []
    for column in zip(*buffer):
        width = max(len(i) for i in column)+1
        result.append([" "*(width-len(i))+i for i in column])
    return "\n".join("".join(i) for i in zip(*result))

def program_to_str(array):
    return "\n".join("".join(i) for i in array)

def make_text(string:str, font, highlights:list=(), strong_highlights:list=()):
    text = font.render(string, False, color_text, (0, 0, 0))
    text.convert_alpha()
    text.set_colorkey((0, 0, 0))
    surface = py.Surface(text.get_size())
    surface.fill(color_bg)
    dx, dy = font.size("a")
    for x, y in highlights:
        surface.fill(color_high, (x*dx, 0, dx, dy))
    for x, y in strong_highlights:
        surface.fill(color_strong, (x*dx, 0, dx, dy))
    surface.blit(text, (0, 0))
    return surface

def get_slice(array, x):
    cells = []
    lar = len(array)
    i = x-3
    while i < x+4:
        cells.append(array[i%lar])
        i += 1
    return cells

def stack_string(stack:list):
    result = "Stack: "+str(stack[-15:])[1:-1]
    if len(result) > 200:
        result = result[:200] + "…"
    return result

def info_string(memx, slen, code, direction, px, py):
    return (f"Memory at {memx}; Stack length: {slen};"+
            f"\nProgram direction: {direction} at ({px}, {py}); Current code: {code}")

def make_screen(program, memory, stack:list, direction:tuple, code:str, font, history:list=()):
    '''assumes that program & memory are planes with: .values, .x, and .y attributes.'''
    if not history:
        history = [program.position]
    main_text = program_to_str(program.values)
    main_text += "\n\n"+stack_string(stack)
    main_text += "\n"+info_string(memory.x, len(stack), code, direction, program.x, program.y)
    main_text += "\n\n"+mem_to_str([get_slice(memory.values, memory.x)])
    items = main_text.split("\n")
    #print("Lines: "+str(len(items)))
    history = history[-HIST:-HI]
    focus = history[-HI:]
    def geth(y):
        result = [[], []]
        for i in history:
            if i[1] == y:
                result[0].append(i)
        for i in focus:
            if i[1] == y:
                result[1].append(i)
        return result
    surfaces = [make_text(j, font, *geth(i)) for i, j in enumerate(items)]
    height = sum(i.get_size()[1] for i in surfaces)
    width = max(i.get_size()[0] for i in surfaces)
    result = py.Surface((width, height))
    y = 0
    for i in surfaces:
        result.blit(i, (0, y))
        y += i.get_size()[1]
    #return make_text(main_text, font, history[-6:-1], history[-1:])
    return result

class Game:
    def __init__(self, engine):
        '''assumes <engine> is a euclid engine object'''
        self.engine = engine
        self.need_redraw = False
        self.waiting = False
        self.redraw()
    def engine_step(self):
        self.engine.step()
        self.waiting = False
        self.need_redraw = True
    def step(self):
        if not self.waiting:
            self.waiting = True
            # why do this? because pygame will crash if it doesn't
            # perform graphics updates for too long,
            # and one of the operations is 'take console input'
            Thread(target = self.engine_step).start()
    def redraw(self):
        self.surface = make_screen(self.engine.program, self.engine.memory,
            self.engine.stack, self.engine.direction, self.engine.alpha, font_obj, self.engine.recent_history)
        self.need_redraw = False
    def every_frame(self, surface):
        if self.need_redraw:
            self.redraw()
        surface.blit(self.surface, (0, 0))

ADVANCERS = {py.K_SPACE}
AUTOMATIC = {py.K_a}
HYPER = {py.K_h}
MANUAL = {py.K_m}
HISTOGRAM = []
def play(screen, game:Game):
    print("playing")
    clock = py.time.Clock()
    py.display.set_caption("Euclid Graphical Display")
    loop = True
    keep_running = True
    do_quit = False
    automatic = False
    hyper = False
    while loop:
        clock.tick(60)*0.001
        #print("looping")
        #keys = py.key.get_pressed()
        if automatic:
            game.step()
        if hyper:
            game.step()
            game.step()
            game.step()
            game.step()
        for event in py.event.get():
            if event.type == py.QUIT:
                loop &= False
                do_quit |= True
                keep_running &= False
            if event.type == py.KEYDOWN:
                if event.key == py.K_ESCAPE:
                    loop &= False
                elif event.key in ADVANCERS and not (automatic or hyper):
                    game.step()
                elif event.key in AUTOMATIC:
                    automatic ^= True
                    hyper = False
                elif event.key in HYPER:
                    hyper ^= True
                    automatic = False
                elif event.key in MANUAL:
                    automatic = False
                    hyper = False
        screen.fill(color_bg)
        game.every_frame(screen)
        py.display.flip()
    return (keep_running, do_quit)

def main(engine:Engine, screen_x:int=800, screen_y:int=720):
    screen = py.display.set_mode((screen_x, screen_y))
    return play(screen, Game(engine))

def mainf(engine:Engine, screen_x:int=800, screen_y:int=720):
    py.init()
    main(engine, screen_x, screen_y)
    py.quit()

def newjoin(*args):
    '''newline-join many strings. remember to use commas.'''
    # remember: python has IMPLICIT string concatenation
    #    this DISRUPTS the expected behavior of newjoin
    return "\n".join(str(i) for i in args)

samples = {
    "truth_machine":newjoin(
        "g86xmv^s+g-ivm|p+",
        "        vp/m<    ",
        "|||||||p>m|||||||"),
    "swap_test":"s+++=|||p+",
    "alg_test":"s12543g+-*=/|p+",
}
def test_sample(key, input_buffer=""):
    mainf(engine=parse(samples[key], input_buffer=input_buffer, engine_class=Engine))
def test_calc(key, input_buffer=""):
    mainf(engine=parse(calculators[key], input_buffer=input_buffer, engine_class=Engine))
def test_fibu(key):
    mainf(engine=parse(fizzbuzz[key], engine_class=Engine))
def test_dec(key):
    mainf(engine=parse(decimal[key], engine_class=Engine))

decimal = {
    "verbose":newjoin( # 10x18, 68 spaces, 42 dots
        "g45x9vs-........pv",
        "s^g0>i1vg59xpv   >",
        " vp=-1s<p.-|s<    ",
        " .                ",
        " >ga/s^g9<iv.....v",
        " ^.........<     .",
        "                 .",
        ".>g68x+s|^1-g<iv.`",
        " ^.............< .",
        "                 +",
    ),
    "compact":newjoin( # 8x14, 34 spaces, 7 dots
        "g45x9vs-....pv",
        "s^g0>i1vg59xp`",
        "  vp=-1s<p-|s<",
        "  >ga/..pv    ",
        " v^i<9g^s<    ",
        " >g68x+s|pv   ",
        " ^vi.>g0^s<   ",
        "  +           ",
    ),
    "comp_2":newjoin( # no negative numbers; 3x17, 7 spaces, 3 dots
        "s1-gffv.p>..ga/pv",
        "v.+i>0g^s\i<g9^s<",
        ">g68x+s|p^       ",
    )
    }
fizzbuzz = {
    "e":newjoin( # 36x7, 16 spaces and 27 dots
        "g77x..........1bbx+5aax+2aax+1bbx+pv",
        "vp...<<<<<<v>v>v>v>v>v>m-xaa2-xbb4g<",
        ">s^^5g/sv0g=mvg3/sv0g=m^s=^m^g|sxivv",
        ".m>sxivm|>|>pv  vp/ag..<p=-1s^vvs.<>",
        "^..<  vp<<||m<  >s^9g<i^.>s^g0>iv.v ",
        "1+p^  >sxivm>>>|>|>pv    ^p|s+x68g/g",
        "....p|as<m<p<<<<<||m<   >p6mv|as<.^."
    ),
}
calculators = {
    "v1":newjoin( # 25x37, 251 spaces, 106 dots
        " g0167x+.s1-.......................pv",
        ">g84x688x-348xxmv^g36x+m^g5+m^g2+m^p`",
        " .gd+m^g37x+m^ge+m^g48x+m^g45x+m^..p`",
        " g37x+m^g44x+m^ge+988x+s|||||||||||p`",
        "         vp............vm-sxg.68|||s<",
        "   above:.print 'Input number: '     ",
        "   below:.get and convert input      ",
        "         >>s+m^g+s?=v0.g=ivpv        ",
        "          ^.................<        ",
        "    vpvi=0gxs^^v>m=s<     .          ",
        "    >m.<^pgaxmv^gx+p^pvm1s<          ",
        "  vpvs<  below: perform opergtions.  ",
        "  >s=g67x-s-mv^g0=ivm^g1=iv.m^g5=ivpv",
        " vp>0g^^m-1s^vm<pxg<  vp+g<vpv=s/g< .",
        " >.sxivg95xpv  ^......<....<.....<  .",
        "     vp..-|s<  .    >g/svp.^ >g-p^  .",
        "     >>ga/pv   ^p=g.^i=0+5g<s^i=3g<s<",
        " vp..^i^^vm<                         ",
        " >svp>mv^^s0g>ivpv                   ",
        "     ^p.|s+x68gp.< left: print result",
        "               >.sa|g84x688x-c8xmv^pv",
        " g4+m^ge+m^s>m^g36x+m^g5+m^g44x+m^.p`",
        " gf+48xm^g45x+m^g37x+m^g44x+m^ge+..p`",
        " g988x+s|||||||||||||||+=..........p`",
        "v                                   >"),
    "minimalist":newjoin( # 13x39, 171 spaces, 66 dots
        " g167x.s1-...........................pv",
        ">g68x84x688x-g57xs|||-mvp>.s+m^g+pv   >",
        "    v...vix^=s.......<p1m^i<0gv=?s<    ",
        "    .   >m^gaxmv^gx+p^                 ",
        "    >sv=g67x-s-mv^g0=ivm^g1=iv.m^g5=jv ",
        "    vpxs>0g^=-1^s<.pxg<  vp+g<vpv=s/g< ",
        "    >.ivg95xpv   ^.......<.<..<...<  . ",
        "       vp.-|s<   .   >g/svp^..>g-p^  . ",
        "       >ga/pv    ^p=g^i=0+5g^m^i=3g^m< ",
        " vp..vs^i.^s<                          ",
        " >s^g0>sxivsa|g84x688x-pv              ",
        "vp=+||||s+.1g=s+2g^sxbag<              ",
        ".^p|s+x68g<                            ",
    )
    }


# i recommend either 16,2 or 6,1.
HIST = 8
HI = 1

def get_stats(code:str):
    lines = code.count("\n")+1
    columns = (code+"\n").index("\n")
    spaces = code.count(" ")
    dots = code.count(".")
    return f"{lines=}, {columns=}, {spaces=}, {dots=}"







