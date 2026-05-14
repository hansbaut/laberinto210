

import pygame as pg
import random
import time
import os

# --- Configuración de Rutas para Android ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_path(filename):
    return os.path.join(BASE_DIR, filename)

# --- Datos del Encabezado ---
NOMBRE = "Hansel Bautista"
ID = "210"
MATERIA = "INF-246"

# --- Inicialización de Pantalla Adaptativa ---
pg.init()
info = pg.display.Info()
# Ajuste automático a la resolución del celular
ANCHO, ALTO = info.current_w, info.current_h
SCREEN = pg.display.set_mode((ANCHO, ALTO), pg.FULLSCREEN)
pg.display.set_caption(f"{NOMBRE} - {ID} - {MATERIA}")

CLOCK = pg.time.Clock()
FPS = 30 

# --- Carga de Animación Personaje ---
def cargar_animaciones(tam):
    ad, ai, ar, ab = [], [], [], []
    try:
        pag = pg.image.load(get_path("unive.png")).convert_alpha()
        ancho_f = pag.get_width() // 4
        alto_f = pag.get_height() // 4
        proporcion = ancho_f / alto_f
        nuevo_ancho = int(tam * proporcion)
        
        temp_sprites = [[None for _ in range(4)] for _ in range(4)]
        for fil in range(4):
            for col in range(4):
                spr_rect = pg.Rect(col * ancho_f, fil * alto_f, ancho_f, alto_f)
                img = pg.transform.scale(pag.subsurface(spr_rect), (nuevo_ancho, tam))
                temp_sprites[fil][col] = img
        ad, ai, ar, ab = temp_sprites[1], [pg.transform.flip(i, True, False) for i in temp_sprites[1]], temp_sprites[3], temp_sprites[0]
    except Exception as e:
        print(f"Error cargando unive.png: {e}")
        s = pg.Surface((tam, tam)); s.fill((255,0,0)); ad = ai = ar = ab = [s]*4
    return ad, ai, ar, ab

# --- Clase Energía Animada ---
class Energia(pg.sprite.Sprite):
    def __init__(self, x, y, tam_celda):
        super().__init__()
        self.frames = []
        try:
            hoja = pg.image.load(get_path("comida.png")).convert_alpha()
            cols, filas = 8, 4
            w_cuadro = hoja.get_width() // cols
            h_cuadro = hoja.get_height() // filas
            fila_objetivo = 1 
            
            for c in range(cols):
                rect_cuadro = pg.Rect(c * w_cuadro, fila_objetivo * h_cuadro, w_cuadro, h_cuadro)
                img = hoja.subsurface(rect_cuadro)
                escala = int(tam_celda * 0.7)
                img_final = pg.transform.scale(img, (escala, escala))
                self.frames.append(img_final)
        except:
            s = pg.Surface((20, 20), pg.SRCALPHA)
            pg.draw.circle(s, (255, 255, 0), (10, 10), 10)
            self.frames = [s]

        self.index = 0
        self.image = self.frames[self.index]
        self.rect = self.image.get_rect(center=(x, y))
        self.brillo = 0
        self.creciendo = True

    def update(self):
        self.index += 0.2
        if self.index >= len(self.frames): self.index = 0
        self.image = self.frames[int(self.index)]
        if self.creciendo:
            self.brillo += 2
            if self.brillo >= 50: self.creciendo = False
        else:
            self.brillo -= 2
            if self.brillo <= 0: self.creciendo = True

# --- Generador de Laberinto ---
class Laberinto:
    def __init__(self, nivel):
        self.tam_celda = max(40, 100 - (nivel * 5))
        self.cols = (ANCHO // self.tam_celda) - 1
        self.filas = (ALTO // self.tam_celda) - 3
        if self.cols % 2 == 0: self.cols -= 1
        if self.filas % 2 == 0: self.filas -= 1
        
        self.offset_x = (ANCHO - (self.cols * self.tam_celda)) // 2
        self.offset_y = (ALTO - (self.filas * self.tam_celda)) // 2 + 40
        
        self.matriz = [[1 for _ in range(self.cols)] for _ in range(self.filas)]
        self.generar_dfs(1, 1)
        self.meta_rect = pg.Rect(self.offset_x + (self.cols-2)*self.tam_celda, 
                                 self.offset_y + (self.filas-2)*self.tam_celda, 
                                 self.tam_celda, self.tam_celda)
        self.caminos_libres = [(c, f) for f in range(1, self.filas-1) for c in range(1, self.cols-1) if self.matriz[f][c] == 0]

    def generar_dfs(self, x, y):
        self.matriz[y][x] = 0
        dirs = [(0, 2), (0, -2), (2, 0), (-2, 0)]; random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 0 < nx < self.cols-1 and 0 < ny < self.filas-1 and self.matriz[ny][nx] == 1:
                self.matriz[y + dy//2][x + dx//2] = 0; self.generar_dfs(nx, ny)

    def dibujar(self, superficie):
        for f in range(self.filas):
            for c in range(self.cols):
                x, y = self.offset_x + c * self.tam_celda, self.offset_y + f * self.tam_celda
                color = (44, 62, 80) if self.matriz[f][c] == 1 else (230, 230, 235)
                pg.draw.rect(superficie, color, (x, y, self.tam_celda, self.tam_celda))
        pg.draw.rect(superficie, (46, 204, 113), self.meta_rect)
        pg.draw.rect(superficie, (255, 255, 255), self.meta_rect, 2)

# --- Clase Jugador con Soporte de Dirección Continua ---
class Jugador(pg.sprite.Sprite):
    def __init__(self, tam):
        super().__init__()
        self.ad, self.ai, self.ar, self.ab = cargar_animaciones(int(tam * 0.8))
        self.image = self.ab[0]
        self.rect = self.image.get_rect()
        self.index = 0
        self.vel_base = 5
        self.vel = self.vel_base
        self.dir = "ABA"
        self.moving_dir = None # Para mantener el movimiento tras el swipe
        self.movio = False
        self.timer_p = 0
        self.timer_max = FPS * 8 

    def update(self, lab):
        if self.timer_p > 0:
            self.timer_p -= 1
            self.vel = 10
        else:
            self.vel = self.vel_base

        dx, dy = 0, 0
        if self.moving_dir == "IZQ": dx = -self.vel; self.dir = "IZQ"
        elif self.moving_dir == "DER": dx = self.vel; self.dir = "DER"
        elif self.moving_dir == "ARR": dy = -self.vel; self.dir = "ARR"
        elif self.moving_dir == "ABA": dy = self.vel; self.dir = "ABA"

        if dx != 0 or dy != 0:
            self.movio = True
            pos_ant = self.rect.copy()
            self.rect.x += dx
            if self.chequear_col(lab): self.rect.x = pos_ant.x
            self.rect.y += dy
            if self.chequear_col(lab): self.rect.y = pos_ant.y
            
            self.index += 0.25
            anim = {"DER":self.ad,"IZQ":self.ai,"ARR":self.ar,"ABA":self.ab}[self.dir]
            self.image = anim[int(self.index % 4)]
        else:
            anim = {"DER":self.ad,"IZQ":self.ai,"ARR":self.ar,"ABA":self.ab}[self.dir]
            self.image = anim[0]

    def chequear_col(self, lab):
        for f in range(lab.filas):
            for c in range(lab.cols):
                if lab.matriz[f][c] == 1:
                    muro = pg.Rect(lab.offset_x + c*lab.tam_celda, lab.offset_y + f*lab.tam_celda, lab.tam_celda, lab.tam_celda)
                    if self.rect.colliderect(muro): return True
        return False

def dibujar_barra_boost(superficie, x, y, ancho, alto, tiempo_actual, tiempo_max):
    if tiempo_actual <= 0: return
    porcentaje = tiempo_actual / tiempo_max
    ancho_relleno = int(ancho * porcentaje)
    pg.draw.rect(superficie, (50, 50, 50), (x, y, ancho, alto))
    pg.draw.rect(superficie, (0, 255, 255), (x, y, ancho_relleno, alto))
    pg.draw.rect(superficie, (255, 255, 255), (x, y, ancho, alto), 2)

def main():
    nivel = 1
    fuente = pg.font.SysFont("Arial", 28, bold=True)
    
    def init_lvl(n, boost=0):
        l = Laberinto(n)
        j = Jugador(l.tam_celda)
        j.timer_p = boost
        j.rect.center = (l.offset_x + 1.5*l.tam_celda, l.offset_y + 1.5*l.tam_celda)
        grupo_e = pg.sprite.Group()
        for pos in random.sample(l.caminos_libres, 3):
            grupo_e.add(Energia(l.offset_x + (pos[0]+0.5)*l.tam_celda, l.offset_y + (pos[1]+0.5)*l.tam_celda, l.tam_celda))
        return l, j, grupo_e

    lab, jgd, energias = init_lvl(nivel)
    t_inicio = None
    
    # --- Variables para Swipes ---
    swipe_start = None
    min_swipe_dist = 30

    while True:
        CLOCK.tick(FPS)
        for e in pg.event.get():
            if e.type == pg.QUIT: pg.quit(); return
            
            # Soporte para teclado (para pruebas en PC)
            if e.type == pg.KEYDOWN:
                if e.key == pg.K_LEFT: jgd.moving_dir = "IZQ"
                elif e.key == pg.K_RIGHT: jgd.moving_dir = "DER"
                elif e.key == pg.K_UP: jgd.moving_dir = "ARR"
                elif e.key == pg.K_DOWN: jgd.moving_dir = "ABA"

            # Detección de Gestos (Swipes)
            if e.type == pg.MOUSEBUTTONDOWN:
                swipe_start = e.pos
            if e.type == pg.MOUSEBUTTONUP and swipe_start:
                end_pos = e.pos
                dx = end_pos[0] - swipe_start[0]
                dy = end_pos[1] - swipe_start[1]
                
                if abs(dx) > abs(dy):
                    if abs(dx) > min_swipe_dist:
                        jgd.moving_dir = "DER" if dx > 0 else "IZQ"
                else:
                    if abs(dy) > min_swipe_dist:
                        jgd.moving_dir = "ABA" if dy > 0 else "ARR"
                swipe_start = None

        jgd.update(lab)
        energias.update()

        if pg.sprite.spritecollide(jgd, energias, True):
            jgd.timer_p = min(jgd.timer_max, jgd.timer_p + (FPS * 3))

        if jgd.movio and t_inicio is None: t_inicio = time.time()
        fmt_t = f"{int(time.time()-t_inicio)//60:02}:{int(time.time()-t_inicio)%60:02}" if t_inicio else "00:00"

        if jgd.rect.colliderect(lab.meta_rect):
            boost_actual = jgd.timer_p
            nivel += 1
            lab, jgd, energias = init_lvl(nivel, boost_actual)
            t_inicio = None

        # --- Dibujado ---
        SCREEN.fill((30, 35, 45))
        lab.dibujar(SCREEN)
        
        for e in energias:
            pg.draw.circle(SCREEN, (255, 255, 100), e.rect.center, e.rect.width//2 + (e.brillo//20), 2)
        energias.draw(SCREEN)
        SCREEN.blit(jgd.image, jgd.rect)
        
        # Interfaz Adaptada
        pg.draw.rect(SCREEN, (20, 20, 30), (0, 0, ANCHO, 80))
        txt_n = fuente.render(f"Lvl: {nivel}", True, (255, 255, 255))
        txt_t = fuente.render(fmt_t, True, (255, 215, 0))
        SCREEN.blit(txt_n, (20, 20))
        SCREEN.blit(txt_t, (ANCHO - txt_t.get_width() - 20, 20))
        
        if jgd.timer_p > 0:
            dibujar_barra_boost(SCREEN, ANCHO//2 - 60, 30, 120, 20, jgd.timer_p, jgd.timer_max)
        
        pg.display.flip()

if __name__ == "__main__":
    main()