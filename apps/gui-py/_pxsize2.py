import sys, os
sys.path.insert(0, os.path.abspath("."))
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPainter, QImage, QColor, QPen
from PyQt6.QtCore import Qt
app = QApplication(sys.argv)
import ui.betterdsh_ui as U

# 手动光栅化 plus path 到 36x36 设备像素（逻辑 18，DPR=2）
path = U._parse_path("M12 5v14M5 12h14")
scale = 18 / 24.0
img2 = QImage(36, 36, QImage.Format.Format_ARGB32)
img2.fill(0)
p2 = QPainter(img2)
p2.setRenderHint(QPainter.RenderHint.Antialiasing)
p2.scale(2, 2)          # 模拟 DPR=2：逻辑坐标
p2.scale(scale, scale)  # viewBox 24 → 逻辑 18
p2.setPen(QPen(QColor("#000000"), 1.7/scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
p2.drawPath(path)
p2.end()
minx=miny=10**9; maxx=maxy=-1; cnt=0
for y in range(36):
    for x in range(36):
        if QColor(img2.pixel(x,y)).alpha() > 0:
            cnt+=1; minx=min(minx,x); miny=min(miny,y); maxx=max(maxx,x); maxy=max(maxy,y)
print(f"manual raster (logical18, dpr2): px={cnt} bbox=({minx},{miny})-({maxx},{maxy})")
print("DONE")