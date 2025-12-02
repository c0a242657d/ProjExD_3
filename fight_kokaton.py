import os
import random
import sys
import time
import pygame as pg
import math


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 画面上に存在する爆弾の数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
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
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire=(+5, 0)

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():# kはキー，mvは移動量
            if key_lst[k]:# 押下されているキーがあれば
                sum_mv[0] += mv[0]# x方向の移動量を加算
                sum_mv[1] += mv[1]# y方向の移動量を加算
        self.rct.move_ip(sum_mv)# こうかとんを移動させる
        if check_bound(self.rct) != (True, True):# 画面外なら
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])# 移動を元に戻す
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):# 移動量が(0,0)でなければ
            self.img = __class__.imgs[tuple(sum_mv)]# 画像を変更
            self.dire = tuple(sum_mv)# 進行方向を更新
        screen.blit(self.img, self.rct)# 画面にこうかとんを転送



class Beam: #練習１
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird:"Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load(f"fig/beam.png") # ビーム画像の読み込み
        self.rct = self.img.get_rect() # ビーム画像のRect取得
        self.rct.centery = bird.rct.centery # こうかとんの中心y座標に合わせる
        self.rct.left = bird.rct.right # こうかとんの右端に合わせる
        self.vx, self.vy = bird.dire # こうかとんの進行方向をビームの速度ベクトルに設定

        th = math.atan2(-self.vy, self.vx) # ビームの角度を計算
        deg = math.degrees(th) # ラジアンを度に変換
        self.img = pg.transform.rotozoom(self.img, deg, 1.0) # ビーム画像を回転

        self.rct = self.img.get_rect() # 回転後のビーム画像のRect取得

        cx = bird.rct.centerx + (bird.rct.width * (self.vx / 5))   # こうかとんの中心x座標に合わせる
        cy = bird.rct.centery + (bird.rct.height * (self.vy / 5))  # こうかとんの中心y座標に合わせる
        self.rct.center = cx, cy # ビームの中心座標を設定
 
    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True): # 画面内なら
            self.rct.move_ip(self.vx, self.vy)  # ビームを移動させる
            screen.blit(self.img, self.rct)   # 画面にビームを転送


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad)) # 爆弾用Surface
        pg.draw.circle(self.img, color, (rad, rad), rad) # 爆弾円を描画
        self.img.set_colorkey((0, 0, 0)) # 黒色を透過色に設定
        self.rct = self.img.get_rect() # 爆弾用Rect
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)  # 爆弾の初期位置をランダムに設定
        self.vx, self.vy = +5, +5  # 爆弾の速度ベクトル

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct) # 爆弾の画面内外判定
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

class Score:
    """
    スコアに関するクラス
    """
    def __init__(self):
        """
        スコア表示用のフォントと初期スコアを設定する
        """
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.score = 0
        self.img = self.fonto.render("好きな文字", 0, (255, 255, 255))
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT - 50)

    def update(self, screen: pg.Surface):
        """
        スコアを画面に表示させる
        引数 screen：画面Surface
        """
        self.img = self.fonto.render(f"スコア：{self.score}", True, self.color)
        screen.blit(self.img, self.rct)

class Explosion:
    """
    爆発エフェクトに関するクラス
    """
    def __init__(self, center: tuple[int,int]):
        """
        爆発エフェクトの初期化
        引数 center：爆発エフェクトの中心座標
        """
        img0 = pg.image.load("fig/explosion.gif")
        img1 = pg.transform.flip(img0, True, False)
        self.img = [img0, img1]

        self.rct = self.img[0].get_rect()
        self.rct.center = center

        self.life = 30 
        self.index = 0
    def update(self, screen: pg.Surface):
        """
        爆発エフェクトを画面に表示させる
        引数 screen：画面Surface
        """
        if self.life > 0:
            self.index = (self.index + 1) % 2
            screen.blit(self.img[self.index], self.rct)
            self.life -= 1

def main():
    """
    メインループ
    """
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    #bomb = Bomb((255, 0, 0), 10)
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]  # 複数の爆弾を生成
    beam = None  # ゲーム初期化時にはビームは存在しない
    beams = []
    clock = pg.time.Clock()
    tmr = 0
    score = Score()
    exceptions = []
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成
                beam = Beam(bird)     
                beams.append(beam)        
        screen.blit(bg_img, [0, 0])
        
        for x, bomb in enumerate(bombs):
            if bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return
        for x, bomb in enumerate(bombs):
            for y, beam in enumerate(beams):
                if beam is None or bomb is None:
                    continue
                if beam.rct.colliderect(bomb.rct):
                    # ビームが爆弾に当たったら爆弾とビームを消す
                    bombs[x] = None
                    beams[y] = None
                    exceptions.append(Explosion(bomb.rct.center))
                    bird.change_img(6, screen)
                    score.score += 1  # スコアを1点加算
                    pg.display.update()
        
        for y, beam in enumerate(beams):
            if beam is None:
                continue
            if check_bound(beam.rct) != (True, True):
                exception = Exception(beam.rct.center)
                beams[y] = None  # ビームが画面外に出たら消す
        bombs = [bomb for bomb in bombs if bomb is not None]  # Noneをリストから削除
        beams = [beam for beam in beams if beam is not None]  # Noneをリストから削除


        new_explosions = []
        for ex in exceptions:
            if ex.life > 0:
                ex.update(screen)
                new_explosions.append(ex)
        exceptions = new_explosions
        
        score.update(screen)
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        for beam in beams:
            beam.update(screen) # 練習１ビームが存在する場合は移動させる
        for bomb in bombs:
            bomb.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    """
    メイン関数の呼び出し
    """
    pg.init()
    main()
    pg.quit()
    sys.exit()
