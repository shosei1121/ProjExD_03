import random
import sys
import time
import math
import pygame as pg

import threading


WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5

def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとん，または，爆弾SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        img0 = pg.transform.rotozoom(pg.image.load(f"ex03/fig/{num}.png"), 0, 2.0)  # 左向き，2倍
        img1 = pg.transform.flip(img0, True, False)  # 右向き，2倍
        self.imgs = {
            (+5, 0): img1,  # 右
            (+5, -5): pg.transform.rotozoom(img1, 45, 1.0),  # 右上
            (0, -5): pg.transform.rotozoom(img1, 90, 1.0),  # 上
            (-5, -5): pg.transform.rotozoom(img0, -45, 1.0), # 左上
            (-5, 0): img0,  # 左
            (-5, +5): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +5): pg.transform.rotozoom(img1, -90, 1.0),  # 下
            (+5, +5): pg.transform.rotozoom(img1, -45, 1.0),  # 右下
        }
        self.img = self.imgs[(+5, 0)] # 右向きがデフォルト
        self.rct = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"ex03/fig/{num}.png"), 0, 2.0)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            for k, mv in __class__.delta.items():
                if key_lst[k]:
                    self.rct.move_ip(-mv[0], -mv[1])
        if sum_mv != [0, 0]:
            self.dire = tuple(sum_mv)  # 移動量の合計値を方向タプルに設定
        if self.dire in self.imgs:
            self.img = self.imgs[self.dire]
        screen.blit(self.img, self.rct)


class Bomb:
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    houkou = [-5, 0, +5]
    def __init__(self):
        """
        爆弾円Surfaceを生成する
        """
        rad = random.randint(10, 50)
        color = random.choice(Bomb.colors)
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = random.choice(Bomb.houkou), random.choice(Bomb.houkou)

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

    
class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird):
        """
        ビームを生成する
        """
        super().__init__() # 親クラスのイニシャライザを呼び出す
        vx, vy = bird.dire # こうかとんが向いている方向をvx, vyに代入
        theta = math.atan2(-vy, vx) # 直交座標(x, -y)から極座標の角度Θに変換
        self.img = pg.transform.rotozoom(pg.image.load("ex03/fig/beam.png"), math.degrees(theta), 2.0) # 弧度法から度数法に変換し、rotozoomで回転
        self.rct = self.img.get_rect()
        # ビームの中心横座標＝こうかとんの中心横座標＋こうかとんの横幅✖ビームの横速度÷５
        self.rct.centerx = bird.rct.centerx + bird.rct.width * vx / 5
        # ビームの中心縦座標＝こうかとんの中心縦座標＋こうかとんの高さ✖ビームの縦速度÷５
        self.rct.centery = bird.rct.centery + bird.rct.height * vy / 5
        self.vx, self.vy = vx, vy

    def update(self, screen: pg.Surface):
        """
        ビームを速度self._vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj, life):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBomb
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load("ex03/fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rct.center)
        self.life = life

    def update(self):
        """
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
       
       
class Score:
    """
    打ち落とした爆弾をスコアとして表示するクラス
    """
    def __init__(self):
        """
        スコアの初期化と表示設定
        """
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.score = 0
        self.img = self.font.render("表示させる文字列", 0, self.color)
        self.rect = self.img.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        """
        現在のスコアを表示する文字列Surfaceを更新
        """
        self.img = self.font.render(f"  スコア: {self.score}", 0, self.color)
        screen.blit(self.img, self.rect)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("ex03/fig/pg_bg.jpg")
    bird = Bird(3, (900, 400))
    bombs = [Bomb() for _ in range(NUM_OF_BOMBS)]
    beam = None
    beams = []
    explosions = []  # 爆発エフェクトを追跡するリスト
    clock = pg.time.Clock()
    tmr = 0
    score = Score()
    
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))  # 新しいビームをリストに追加
                
        tmr += 1
        screen.blit(bg_img, [0, 0])
        
        # 爆発エフェクトを更新
        for explosion in explosions:
            explosion.update()
            if explosion.life <= 0:
                explosions.remove(explosion)  # 寿命が0以下になったエフェクトを削除
        
        for bomb in bombs:
            bomb.update(screen)
            if bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                pg.display.update()
                
                sound()
                font = pg.font.SysFont("comicsansms", 36)
                text = font.render("Hello, Pygame!", True, (255, 255, 255))
                screen.blit(text, (800, 450))

                
                time.sleep(1)
                return

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        
        if beams:
        # ビームを更新し、リストから削除する
            for beam in beams:
                beam.update(screen)
                if not (0 <= beam.rct.centerx <= WIDTH and 0 <= beam.rct.centery <= HEIGHT):
                    beams.remove(beam)

        # 爆弾との衝突をチェックし、ビームと爆弾が衝突した場合、ビームと爆弾をリストから削除
            for beam in beams:
                for i, bomb in enumerate(bombs):
                    if beam.rct.colliderect(bomb.rct):
                        beams.remove(beam)
                        del bombs[i]
                        bird.change_img(6, screen)
                        explosions.append(Explosion(bomb, 50))  # スプライトグループに追加
                        score.score += 1
                        break
          
        # 爆発エフェクトを画面に描画      
        for explosion in explosions:
            screen.blit(explosion.image, explosion.rect)
        
        score.update(screen)   
        pg.display.update()
        clock.tick(50)


def sound():
    pg.mixer.init() #初期化

    pg.mixer.music.load("ex03/gameover4.mp3") #読み込み

    pg.mixer.music.play(1) #再生

    time.sleep(3)

    pg.mixer.music.stop() #終了

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    
    sys.exit()
    