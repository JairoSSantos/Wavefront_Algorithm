import pygame as pg
from random import choices
from numpy import concatenate, amin, amax

def nrange(x0 ,xi=None, dx=1): # contagem; intervalo: {x0 o- xi}
    if not xi: xi = x0; x0 = 0
    while x0 < xi: yield x0; x0 += dx

def value_map(h, ymin, ymax, hmin, hmax): return (ymax-ymin)/(hmax-hmin)*(h - hmin) + ymin # mapear valor

def check_evets(): # verificar eventos
    for event in pg.event.get():
        if event.type == pg.QUIT: quit()

def skew(a, bias): return [i+(i*b) for i, b in zip(a, bias)] # enviesar lista a

SCALE = 30
MOVIMENTS = {'u':(0, -1), 'd':(0, 1), 'r':(1, 0), 'l':(-1, 0)}
BIAS = [0, 0, 0, 0] # respectivamente: up, down, right, left

class Cell:
    def __init__(self, x, y, s, scale):
        self.x, self.y, self.status = x, y, s
        self.walls = list(MOVIMENTS.keys()) # paredes da célula
        self.walls_removed = [] # parades que ja foram removidas
        self.rect = pg.Rect(int(self.x*scale), int(self.y*scale), int(scale), int(scale)) # rect para desenhar
        self.walls_points = { # arestas da célula
            'u':[self.rect.topleft, self.rect.topright],
            'd':[self.rect.bottomleft, self.rect.bottomright],
            'r':[self.rect.topright, self.rect.bottomright],
            'l':[self.rect.topleft, self.rect.bottomleft]
        }

    def draw(self, surface, color=None): # desenhar em surface
        if not color: color = {None:(100, 150, 255), 'visited1':(100, 255, 150), 'visited2':(255,255,255)}[self.status]
        pg.draw.rect(surface, color, self.rect)
        for wall in self.walls: pg.draw.line(surface, (0,0,0), *self.walls_points[wall])

    def remove_wall(self, d): # remover parede
        self.walls.remove(d)
        self.walls_removed.append(d)

class Maze:
    def __init__(self, width, height, scale, surface):
        self.width, self.height, self.scale = width//scale, height//scale, scale # definir tamanho e escala do laberinto
        self.cells = [[Cell(x, y, None, self.scale) for y in nrange(self.height)] for x in nrange(self.width)] # matriz de células
        self.surface = surface # superfície para desenhar

        self.TOPLEFT, self.TOPRIGHT, self.BOTTOMLEFT, self.BOTTOMRIGHT, self.CENTER = [ # pontos do laberinto
            (0, 0), (self.width-1, 0), (0, self.height-1), (self.width-1, self.height-1), (self.width//2, self.height//2)
        ]

        self.limits = lambda x, y: self.width>x>=0 and self.height>y>=0 # função verifica se x e y estão dentro dos limites do laberinto

    def possible_moves(self, x, y):
        # retorna uma lista com True para um movimento possivel
        return [
            (self.limits(x+i, y+j) and not self.cells[x+i][y+j].status in ('visited1', 'visited2'))
            for d, (i, j) in MOVIMENTS.items()
        ]

    def make(self, initial_pos):
        x, y = initial_pos # posição inicial
        self.cells[x][y].status = 'visited1'
        path = [] # armazenar caminho ja visitado
        reversed_iter_path = None
        run = True
        digging = True
        while run:
            check_evets()
            self.surface.fill((255,255,255))

            if digging:
                path.append((x, y)) # adicionar posição à caminho
                possible_moves = self.possible_moves(x, y) # verificar possiveis movimentos
                if sum(possible_moves): # verificar se há movimentos possiveis
                    direction = choices(list(MOVIMENTS.keys()), weights=skew(possible_moves, BIAS), k=1)[0] # escolher aleatoriamente uma direção
                    i, j = MOVIMENTS[direction]
                    self.cells[x][y].remove_wall(direction) # remover parede que separa as células
                    self.cells[x+i][y+j].remove_wall({'u':'d', 'd':'u', 'r':'l', 'l':'r'}[direction]) # remover parede que separa as células
                    self.cells[x+i][y+j].status = 'visited1' # marcar célula como visitada
                    x, y = x+i, y+j # alterar posição
                else: digging = False; reversed_iter_path = iter(reversed(path)) # se não houver movimentos, volte

            else: # voltar no caminho
                try: x, y = next(reversed_iter_path)
                except StopIteration: run = False
                else:
                    path.remove((x, y)) # se posição foi visitada 2 vezes então é removida
                    self.cells[x][y].status = 'visited2' # marcar como segunda visita
                    if sum(self.possible_moves(x, y)): digging = True # verificar se ha movimentos possiveis

            # desenhar células
            for i in nrange(self.width):
                for j in nrange(self.height):
                    self.cells[i][j].draw(self.surface, (255,150,100) if (i, j) == (x, y) else None)

            pg.display.flip()
        print('Precione "Espaço" para usar o algoritimo Wavefront ou se deseja tentar resolver precione qualquer "seta".')

    def solve(self, initial_pos, final_pos, stop): # resolver laberinto com wavefront algorithm
        field = [[-1 for _ in nrange(self.height)] for _ in nrange(self.width)] # matriz para mapear cada célula com um valor
        loc = [(*initial_pos, 0)] # armazena as frentes de onda
        run = True
        propagation = True
        path = [] # caminho solução
        while run:
            check_evets()
            self.surface.fill((255,255,255))
            if propagation:
                stop_condition = False # iniciar condição de parada como Falso
                for x, y, h in loc: # iteração pelas frentes de onda
                    field[x][y] = h+1 # acidionar valor à célula
                    loc.remove((x, y, h)) # remover valor passado
                    for d in self.cells[x][y].walls_removed: # iteração para decidir nova frente de onda
                        i, j = MOVIMENTS[d]
                        if self.limits(x+i, y+j) and field[x+i][y+j] == -1: loc.append((x+i, y+j, h+1)) # adicionar nova frente de onda
                        if stop and (x, y) == final_pos: stop_condition = True # verificar condição de parada
                if not len(loc) or stop_condition: propagation = False; x, y = final_pos; path = [final_pos] # decidir se deve parar a propagação da onda
            elif field[x][y] > 1: # marcar caminho do valor maior ao menor
                for d in self.cells[x][y].walls_removed: # iterar pelos possiveis caminhos de volta
                    i, j = MOVIMENTS[d]
                    if self.limits(x+i, y+j) and field[x+i][y+j] == field[x][y]-1:
                        path.append((x+i, y+j)) # adicionar à caminho
                        x, y = x+i, y+j
            else: run = False # para loop principal

            hmin, hmax = amax(field), amin(field)
            for cell, h in zip(concatenate(self.cells), concatenate(field)):
                ci = value_map(h, 0, 1, hmin, hmax) # mapear o valor para intervalo 0-1
                color = (255,255,255) if h == -1 else (int(255 - 255*ci), 0, int(255*ci)) # definir cor da célula
                cell.draw(self.surface, color) # desenhar

            if len(path): # desenhar caminho
                for i, (xi, yi) in enumerate(path[:-1]): # iterar pelo caminho
                    xj, yj = path[i+1]
                    pg.draw.line(self.surface, (255,255,255), self.cells[xi][yi].rect.center, self.cells[xj][yj].rect.center)
                    pg.draw.ellipse(self.surface, (255,255,255), self.cells[xi][yi].rect.inflate(-int(8/10*self.scale), -int(8/10*self.scale)))

            pg.display.flip()
        return path

    def try_to_solve(self, initial_pos, final_pos):
        x, y = initial_pos
        path = [initial_pos]
        run = True
        clock = pg.time.Clock()
        while run:
            clock.tick(60)
            check_evets()
            self.surface.fill((255,255,255))

            if (x, y) == final_pos: run = False

            key = pg.key.get_pressed()
            direction = None
            if key[pg.K_UP]: direction = 'u'
            elif key[pg.K_DOWN]: direction = 'd'
            elif key[pg.K_RIGHT]: direction = 'r'
            elif key[pg.K_LEFT]: direction = 'l'
            if direction:
                i, j = MOVIMENTS[direction]
                if self.limits(x+i, y+j) and direction in self.cells[x][y].walls_removed:
                    if (x+i, y+j) in path: del path[path.index((x+i, y+j))+1:]
                    else: path.append((x+i, y+j))
                    x, y = x+i, y+j

            for cell in concatenate(self.cells): cell.draw(self.surface)
            if len(path): # desenhar caminho
                for i, (xi, yi) in enumerate(path[:-1]): # iterar pelo caminho
                    xj, yj = path[i+1]
                    pg.draw.line(self.surface, (100, 150, 255), self.cells[xi][yi].rect.center, self.cells[xj][yj].rect.center)
                    pg.draw.ellipse(self.surface, (100, 150, 255), self.cells[xi][yi].rect.inflate(-int(8/10*self.scale), -int(8/10*self.scale)))
            self.cells[x][y].draw(self.surface, (100, 150, 255))
            self.cells[final_pos[0]][final_pos[1]].draw(self.surface, (255, 100, 100))

            pg.display.flip()
        if not int(sum([(i - j)**2 for i, j in zip(concatenate(list(reversed(path))), concatenate(self.solve(initial_pos, final_pos, True)))])**0.5):
            print('Voçê conseguiu!')

if __name__ == '__main__':
    pg.init()
    pg.display.set_caption('Wavefront')
    size = width, height = 600, 600
    screen = pg.display.set_mode(size)

    maze = Maze(width, height, SCALE, screen)
    maze.make(maze.TOPLEFT)

    while True:
        check_evets()
        key = pg.key.get_pressed()
        if key[pg.K_UP] or key[pg.K_DOWN] or key[pg.K_RIGHT] or key[pg.K_LEFT]:
            maze.try_to_solve(maze.TOPLEFT, maze.BOTTOMRIGHT); print('Precione "n" para criar outro laberinto.')
        elif key[pg.K_SPACE]: maze.solve(maze.TOPLEFT, maze.BOTTOMRIGHT, False); print('Precione "n" para criar outro laberinto.')
        elif key[pg.K_n]:maze = Maze(width, height, 30, screen); maze.make(maze.TOPLEFT)
