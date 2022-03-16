from unicodedata import name
import cv2
from cv2 import FlannBasedMatcher
import numpy as np
import ctypes
import time
import datetime
import glob
import matplotlib.pyplot as plt


def get_img_name():   #画像のファイルパスを取得する
    files = glob.glob("./main_wallpaper/*")
    return files[0]

class create_wallpaper:
    def __init__ (self, img_path, center_xy=[1550, 400], dial_color=[50, 25, 40], clockhand_color=[0, 0, 200], reverse=False):
        self.reverse = reverse
        self.img = cv2.imread(img_path)
        self.img = np.array(self.img, dtype="int16")
        dial_color = np.array(dial_color)
        self.center_xy = center_xy

        self.clockhand_colorh = np.array(clockhand_color) + np.array([20, 80, 20])
        self.clockhand_colorm = np.array(clockhand_color) + np.array([10, 50, 20])
        self.clockhand_colors = np.array(clockhand_color) + np.array([40, 20, 40])

        self.moving_color = dial_color + np.array([0, 10, 30])

        outer_radius = 300
        inner_radius = 220

        self.mask = np.zeros_like(self.img)
        self.mask = cv2.circle(img=self.mask, center=center_xy, radius=outer_radius, color=dial_color.tolist(), thickness=-1)

        dial_color2 = dial_color + np.array([0, 20, 20])
        self.mask = cv2.circle(img=self.mask, center=center_xy, radius=inner_radius, color=dial_color2.tolist(), thickness=-1)

        dial_color3 = dial_color2 + np.array([0, 20, 20])
        self.mask = cv2.circle(img=self.mask, center=center_xy, radius=inner_radius-60, color=dial_color3.tolist(), thickness=-1)

        dial_color3 = dial_color2 + np.array([10, 10, 60])
        self.mask = cv2.circle(img=self.mask, center=center_xy, radius=inner_radius-180, color=dial_color3.tolist(), thickness=-1)

        scale_color = dial_color + np.array([50, 60, 50])
        #盤面の作成
        for i in range(12):    #5分毎の目盛
            x1, y1 = 0, inner_radius
            x2, y2 = 0, outer_radius+8
            angle = np.pi/6 * i

            x1, y1 = self.rotate_xy([x1, y1], angle)
            x2, y2 = self.rotate_xy([x2, y2], angle)

            self.mask = cv2.line(self.mask, pt1=(x1, y1), pt2=(x2, y2), color=scale_color.tolist(), thickness=5)

            #5分毎の目盛(内側)
            x1, y1 = 0, inner_radius-62
            x2, y2 = 0, inner_radius-100

            x1, y1 = self.rotate_xy([x1, y1], angle)
            x2, y2 = self.rotate_xy([x2, y2], angle)

            self.mask = cv2.line(self.mask, pt1=(x1, y1), pt2=(x2, y2), color=scale_color.tolist(), thickness=5)

        for i in range(60):    #1分毎の目盛
            x1, y1 = 0, inner_radius+60
            x2, y2 = 0, outer_radius-2
            angle = np.pi/30 * i

            x1, y1 = self.rotate_xy([x1, y1], angle)
            x2, y2 = self.rotate_xy([x2, y2], angle)

            self.mask = cv2.line(self.mask, pt1=(x1, y1), pt2=(x2, y2), color=scale_color.tolist(), thickness=3)

            #1分毎の目盛(内側)
            x1, y1 = 0, inner_radius-62
            x2, y2 = 0, inner_radius-80

            x1, y1 = self.rotate_xy([x1, y1], angle)
            x2, y2 = self.rotate_xy([x2, y2], angle)

            self.mask = cv2.line(self.mask, pt1=(x1, y1), pt2=(x2, y2), color=scale_color.tolist(), thickness=3)

        scale_color = dial_color + np.array([10, 10, 10])

        for i in range(7):    #装飾七角形
            x1, y1 = 0, outer_radius+49
            x2, y2 = 0, outer_radius+49
            angle1 = np.pi/3.5 * (i-0.5)
            angle2 = np.pi/3.5 * (i+0.5)

            x1, y1 = self.rotate_xy([x1, y1], angle1)
            x2, y2 = self.rotate_xy([x2, y2], angle2)

            self.mask = cv2.circle(img=self.mask, center=(x1, y1), radius=50, color=scale_color.tolist(), thickness=3)    #各頂点の円
            self.mask = cv2.line(self.mask, pt1=(x1, y1), pt2=(x2, y2), color=scale_color.tolist(), thickness=3)


        self.mask = cv2.circle(img=self.mask, center=center_xy, radius=outer_radius, color=(180, 100, 100), thickness=3)  #外枠二重線内側
        self.mask = cv2.circle(img=self.mask, center=center_xy, radius=outer_radius+10, color=(180, 100, 100), thickness=3)   #外枠二重線外側
        self.mask = cv2.circle(img=self.mask, center=center_xy, radius=inner_radius-70, color=(180, 100, 100), thickness=2)   #内枠
        self.mask = cv2.circle(img=self.mask, center=center_xy, radius=inner_radius-120, color=(180, 100, 100), thickness=2)   #内枠

        #針の初期位置
        self.xh1, self.yh1 = 0, -(inner_radius-60)    #短針 順方向
        self.xh2, self.yh2 = 0, -(inner_radius-180)    #短針 逆方向

        self.xm1, self.ym1 = 0, -(outer_radius-20)    #長針 順方向
        self.xm2, self.ym2 = 0, -(outer_radius-260)    #長針 逆方向

        self.xs1, self.ys1 = 0, -(outer_radius-20)    #長針 順方向
        self.xs2, self.ys2 = 0, -(outer_radius-260)    #長針 逆方向

        if reverse:
            self.img -= self.mask
        else:
            self.img += self.mask

    def rotate_xy(self, xy, angle):
        x, y = np.int16(np.dot([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]], xy))
        x, y = np.array([x, y]) + self.center_xy
        return x, y 

    def move_dial(self, img, i0):
        moving_dial = np.zeros_like(self.img)
        
        angle = np.pi/30 
        for i in range(60):
            x, y = 0, 100
            x, y = self.rotate_xy([x, y], angle*i + (i0*np.pi)/120)
            self.center_xy

            moving_dial= cv2.line(moving_dial, pt1=self.center_xy, pt2=(x, y), color=self.moving_color.tolist(), thickness=2)
        
        if self.reverse:
            img -= moving_dial
        else:
            img += moving_dial

        return img, moving_dial

    def create_clock (self, i0):
        clock = np.zeros_like(self.img)
        img = self.img.copy()

        dt_now = datetime.datetime.now()
        second = int(dt_now.strftime("%S"))
        minute = int(dt_now.strftime("%M")) + second/60
        hour = int(dt_now.strftime("%H")) + minute/60

        angleh1 = np.pi/6 * hour
        angleh2 = np.pi/6 * hour + np.pi
        xh1, yh1 = self.rotate_xy([self.xh1, self.yh1], angleh1)
        xh2, yh2 = self.rotate_xy([self.xh2, self.yh2], angleh2)
        clock = cv2.line(clock, pt1=(xh1, yh1), pt2=(xh2, yh2), color=self.clockhand_colorh.tolist(), thickness=8)

        anglem1 = np.pi/30 * minute
        anglem2 = np.pi/30 * minute + np.pi

        xm1, ym1 = self.rotate_xy([self.xm1, self.ym1], anglem1)
        xm2, ym2 = self.rotate_xy([self.xm2, self.ym2], anglem2)
        clock = cv2.line(clock, pt1=(xm1, ym1), pt2=(xm2, ym2), color=self.clockhand_colorm.tolist(), thickness=5)

        angles1 = np.pi/30 * second
        angles2 = np.pi/30 * second + np.pi

        xs1, ys1 = self.rotate_xy([self.xs1, self.ys1], angles1)
        xs2, ys2 = self.rotate_xy([self.xs2, self.ys2], angles2)
        clock = cv2.line(clock, pt1=(xs1, ys1), pt2=(xs2, ys2), color=self.clockhand_colors.tolist(), thickness=2)

        img, moving_dial = self.move_dial(img, i0)

        if self.reverse:
            img += clock
        else:
            img -= clock

        img = np.clip(img, 0, 255)
        return img, self.mask, clock, moving_dial


if __name__ == "__main__":
    img_path = get_img_name()
    dial_color=[50, 25, 40]
    wp = create_wallpaper(img_path, dial_color=dial_color)

    i=0
    while True:
        colorx = i%60
        if colorx < 30:
            dial_color=[50 - i, 25, 40 + 2*i]
        elif colorx <60:
            dial_color=[-10 + i, 25, 160 - 2*i]

        img, mask, clock, moving_dial = wp.create_clock(i)

        time_delta=0

        cv2.imwrite("clock_img.jpg", img)
        """
        cv2.imwrite("mask.jpg", mask)
        cv2.imwrite("clock.jpg", clock)
        cv2.imwrite("moving_dial.jpg", moving_dial)
        """

        SPI_SETDESKWALLPAPER = 20
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, r"C:\Users\Takan\OneDrive\デスクトップ\python\時計付壁紙\clock_img.jpg", 0)
        time.sleep(0.24)

        pre_s = int(datetime.datetime.now().strftime("%S"))
        now_s = int(datetime.datetime.now().strftime("%S"))

        while pre_s == now_s:    #秒数が1進んだら壁紙を更新
            now_s = int(datetime.datetime.now().strftime("%S"))
            time.sleep(0.1)

        i += 1
        print("i:", i, dial_color)
