# $LAN=PYTHON$

# Voronoi Diagram
# Python 3.9.5

# By Jahhow Tu 涂家浩 -> https://www.facebook.com/TUJAHHOW
# M103040005 TU CHIA HAO


import sys
from typing import List, Optional, Tuple, Union
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np
from functools import cmp_to_key
from math import ceil, floor, sqrt
import traceback

WIN_SIZE = 600
DEBUG = False

GRAY = QColor('#777')
RED = QColor('#f54242')
LIGHT_GREEN = QColor('#c0eb34')
GREEN = QColor('#00cf0a')
BLUE = QColor('#007bff')
PURPLE = QColor('#b434eb')


class Point:
    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'{self.x} {self.y}'

    def __eq__(self, p) -> bool:
        return self.x == p.x and self.y == p.y

    def __lt__(self, p):
        return self.x < p.x or (self.x == p.x and self.y > p.y)

    def lessThan_yFirst(self, p):
        return self.y < p.y or (self.y == p.y and self.x < p.x)

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __iadd__(self, other):
        other: Point
        self.x += other.x
        self.y += other.y
        return self

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def __truediv__(self, divisor):
        return Point(self.x/divisor, self.y/divisor)

    def __mul__(self, a):
        if isinstance(a, Point):
            ''' Cross Product '''
            return self.x*a.y-self.y*a.x
        else:
            return Point(self.x*a, self.y*a)

    def __rmul__(self, a):
        return self*a

    def __imul__(self, a: float):
        self.x *= a
        self.y *= a
        return self

    def norm(self) -> float:
        return sqrt(self.x**2 + self.y**2)


class Voronoi:
    class Edge:
        pass

    class Polygon(Point):
        pass

    class Vertex(Point):
        def __init__(self, x, y, edge, isInfinite=False) -> None:
            super().__init__(x, y)
            self.edge = edge
            self.isInfinite = isInfinite


PRECISION = .0000001


class Voronoi:
    class Edge:
        rightPolygon: Voronoi.Polygon
        leftPolygon: Voronoi.Polygon
        startVertex: Voronoi.Vertex
        endVertex: Voronoi.Vertex
        cwPredecessor: Voronoi.Edge
        ccwPredecessor: Voronoi.Edge
        cwSuccessor: Voronoi.Edge
        ccwSuccessor: Voronoi.Edge

        def __init__(self) -> None:
            self.rightPolygon = None
            self.leftPolygon = None
            self.startVertex = None
            self.endVertex = None
            self.cwPredecessor = None
            self.ccwPredecessor = None
            self.cwSuccessor = None
            self.ccwSuccessor = None
            self.intersected = False

        def __repr__(self):
            return self.__str__()

        def __str__(self):
            return f'{self.startVertex} -> {self.endVertex}'

        class Intersection(Point):
            def __init__(self, x, y, edgeP: Voronoi.Edge, edgeQ: Voronoi.Edge, r: Point, s: Point, rs, t, u) -> None:
                super().__init__(x, y)
                self.edgeP = edgeP
                self.edgeQ = edgeQ
                self.r = r
                self.s = s
                self.rs = rs
                self.t = t
                self.u = u
                # edgeQ is from the left diagram (at the merging step)
                self.isLeft = edgeQ.leftPolygon.isLeft

            @property
            def p(self):
                return self.edgeP

            @property
            def q(self):
                return self.edgeQ

        def intersection(self, e):
            '''
            return self if collinear
            return None if no intersection
            return the intersection as a Point

            https://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect
            '''
            e: Voronoi.Edge

            p: Point = self.startVertex
            q: Point = e.startVertex
            r: Point = self.endVertex-self.startVertex
            s: Point = e.endVertex-e.startVertex

            pq: Point = q-p
            pqs: float = pq * s
            rs: float = (r * s)
            if rs == 0:  # parallel
                if pqs == 0:  # collinear
                    return self
                else:  # parallel but not the same line
                    return None
            else:  # not parallel
                t: float = pqs / rs
                u: float = pq * r / rs
                intersection = p+t*r
                intersection = Voronoi.Edge.Intersection(
                    intersection.x, intersection.y, self, e, r, s, rs, t, u)

                # def checkU_exclude():
                #     if u <= 0+PRECISION:
                #         if e.startVertex.isInfinite:
                #             return intersection
                #         return None
                #     if u < 1-PRECISION:
                #         return intersection
                #     if e.endVertex.isInfinite:
                #         return intersection
                #     return None
                def checkU():
                    if u < 0-PRECISION:
                        if e.startVertex.isInfinite:
                            return intersection
                        return None
                    if u <= 1+PRECISION:
                        return intersection
                    if e.endVertex.isInfinite:
                        return intersection
                    return None
                if t < 0-PRECISION:
                    if self.startVertex.isInfinite:
                        return checkU()
                    return None
                if t <= 1+PRECISION:
                    return checkU()
                if self.endVertex.isInfinite:
                    return checkU()
                return None

    class Polygon(Point):
        def __init__(self, x, y) -> None:
            super().__init__(x, y)
            self.edge = None

            # is in the left convex hull during merge
            self.isLeft = False

        # def edges(self) -> List[Voronoi.Edge]:
        #     e: Voronoi.Edge = self.edge
        #     result = []
        #     if e is None:
        #         return result

        #     # ccw
        #     while True:
        #         # print('.',end='',flush=True)
        #         result.append(e)
        #         if e.leftPolygon is self:
        #             e = e.cwSuccessor
        #         else:
        #             e = e.cwPredecessor
        #         if e is None or e is self.edge:
        #             break

        #     e: Voronoi.Edge = self.edge
        #     # cw
        #     while True:
        #         # print('.',end='',flush=True)
        #         if e.leftPolygon is self:
        #             e = e.ccwPredecessor
        #         else:
        #             e = e.ccwSuccessor
        #         if e is None or e is self.edge:
        #             break
        #         result.append(e)

        #     return result

        def edges(self, v: Voronoi) -> List[Voronoi.Edge]:
            result = []
            for e in v.edges:
                if e.rightPolygon is self or e.leftPolygon is self:
                    result.append(e)
            return result

    class Vertex(Point):
        def __init__(self, x, y, edge, isInfinite=False) -> None:
            super().__init__(x, y)
            self.edge = edge
            self.isInfinite = isInfinite

    def __init__(self, P: List[Voronoi.Polygon], edges: List[Voronoi.Edge] = []) -> None:
        # self.P = [Voronoi.Polygon(x, y) for x, y in P]
        self.P = P
        self.edges = edges

    def save(self, fname):
        with open(fname, 'w') as f:
            def cmp1(p1: Point, p2: Point):
                a = p1.x-p2.x
                if a != 0:
                    return a
                return p1.y-p2.y
            self.P.sort(key=cmp_to_key(cmp1))

            def cmp2(e1: Voronoi.Edge, e2: Voronoi.Edge):
                e1 = e1.startVertex, e1.endVertex
                e2 = e2.startVertex, e2.endVertex
                if cmp1(e1[1], e1[0]) < 0:
                    e1 = e1[1], e1[0]
                if cmp1(e2[1], e2[0]) < 0:
                    e2 = e2[1], e2[0]
                a = e1[0].x-e2[0].x
                if a != 0:
                    return a
                a = e1[0].y-e2[0].y
                if a != 0:
                    return a
                return e1[1].y-e2[1].y
            self.edges.sort(key=cmp_to_key(cmp2))

            # write
            for p in self.P:
                f.write(f'P {p}\n')
            for e in self.edges:
                e = e.startVertex, e.endVertex
                if cmp1(e[1], e[0]) < 0:
                    e = e[1], e[0]
                f.write(f'E {e[0]} {e[1]}\n')


class Canvas(QLabel):
    STEP_MS = 200

    def __init__(self):
        super().__init__()
        self.polygons = []

        self.mutex = QMutex()
        self.waitCondition = QWaitCondition()
        self.stepByStep = True
        self.continueUntilHP = False
        self.stepMs = Canvas.STEP_MS

        self.setMinimumSize(WIN_SIZE, WIN_SIZE)
        self.curX = self.curY = None
        self.ctrl = False

        self.last_x, self.last_y = None, None
        self.pen_color = GRAY
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAlignment(Qt.AlignTop)

        if len(sys.argv) > 1:
            self.setMode(self.Mode.FreeDraw)
        else:
            self.setMode(self.Mode.AddPoint)

        # Allow resize smaller than content pixmap
        sizePolicy = self.sizePolicy()
        sizePolicy.setVerticalPolicy(QSizePolicy.Ignored)
        sizePolicy.setHorizontalPolicy(QSizePolicy.Ignored)
        self.setSizePolicy(sizePolicy)

        # setFocus to receive keypress
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

        # Thread --------------------------------------------------------
        self.workerThread = WorkerThread(self)
        self.workerThread.canvasUpdate.connect(self.canvasUpdate)
        self.workerThread.clearCanvas.connect(self.clearCanvas)
        self.workerThread.drawPoints.connect(self.drawPoints)
        self.workerThread.drawPolygon.connect(self.drawPolygon)
        self.workerThread.drawVoronoiOrEdges.connect(self.drawVoronoiOrEdges)
        self.workerThread.drawEdge.connect(self.drawEdge)
        self.workerThread.start()

    def waitNext(self):
        # if self.stepByStep:
        # self.update()
        self.workerThread.canvasUpdate.emit()
        self.stepByStep = True
        self.continueUntilHP = False
        self.stepMs = Canvas.STEP_MS
        self.mutex.lock()
        self.waitCondition.wait(self.mutex)
        self.mutex.unlock()

    def waitStep(self, stepMs=None):
        # self.update()
        self.workerThread.canvasUpdate.emit()
        if self.stepByStep:
            self.mutex.lock()
            self.waitCondition.wait(self.mutex)
            self.mutex.unlock()
        elif self.stepMs > 0:
            if stepMs is None:
                stepMs = self.stepMs
            self.mutex.lock()
            self.waitCondition.wait(self.mutex, stepMs)
            self.mutex.unlock()

    def waitHP(self):
        if self.continueUntilHP:
            self.workerThread.canvasUpdate.emit()
            self.continueUntilHP = False
            self.stepByStep = True
            self.mutex.lock()
            self.waitCondition.wait(self.mutex)
            self.mutex.unlock()
        else:
            self.waitStep()

    def wakePlayCondition(self):
        self.waitCondition.wakeOne()

    def canvasUpdate(self):
        self.update()

    def clearCanvas(self):
        # pixmap = QPixmap(self.width(), self.height())
        # pixmap.fill(Qt.GlobalColor.transparent)
        # self.setPixmap(pixmap)

        self.pixmap().fill(Qt.GlobalColor.transparent)

        # painter = QPainter(self.pixmap())
        # painter.setCompositionMode(QPainter.CompositionMode_Source)
        # painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        # painter.end()

    def resizeEvent(self, event):
        if self.pixmap() is None:
            pixmap = QPixmap(self.width(), self.height())
            pixmap.fill(Qt.GlobalColor.transparent)
            self.setPixmap(pixmap)
            return
        
        pixmap = QPixmap(self.width(), self.height())
        pixmap.fill(Qt.GlobalColor.transparent)
        painter=QPainter(pixmap)
        painter.drawPixmap(0,self.height()-self.pixmap().height(),self.pixmap())
        painter.end()
        self.setPixmap(pixmap)

    class Mode:
        FreeDraw = 0
        InsertCircle = 1
        InsertRectangle = 2
        Crop = 3
        AddPoint = 4

    def setMode(self, mode):
        self.mode = mode

    def set_pen_color(self, c):
        self.pen_color = QColor(c)

    def drawPoints(self, points: List[Point], qcolor=GRAY):
        painter = QPainter(self.pixmap())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # # square point
        # p = painter.pen()
        # p.setWidth(10)
        # p.setColor(qcolor)
        # painter.setPen(p)
        # for p in points:
        #     painter.drawPoint(QPointF(p.x, self.height()-p.y))

        RADIUS = 4
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(qcolor))
        for p in points:
            # painter.drawPoint(QPointF(p.x, self.height()-p.y))
            painter.drawEllipse(
                QPointF(p.x, self.height()-p.y), RADIUS, RADIUS)

        painter.end()
        # self.update()

    def drawPolygon(self, points, qcolor):
        painter = QPainter(self.pixmap())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        p = painter.pen()
        p.setWidth(4)
        p.setColor(qcolor)
        painter.setPen(p)
        polygon = QPolygonF([QPointF(p.x, self.height()-p.y) for p in points])
        painter.drawPolygon(polygon)
        p.setWidth(10)
        painter.setPen(p)
        painter.drawPoints(polygon)
        painter.end()
        # if update:
        #     self.update()

    def drawEdge(self, edge: list, qcolor, width, penStyle: Qt.PenStyle):
        painter = QPainter(self.pixmap())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        p = painter.pen()
        p.setWidth(width)
        p.setColor(qcolor)
        p.setStyle(penStyle)
        painter.setPen(p)
        painter.drawLine(QPointF(edge[0].x, self.height()-edge[0].y),
                         QPointF(edge[1].x, self.height()-edge[1].y))
        painter.end()
        # self.update()

    def drawVoronoiOrEdges(self, voronoi: Union[Voronoi, list], qcolor, width):
        edges = voronoi
        if isinstance(voronoi, Voronoi):
            edges = voronoi.edges
            self.drawPoints(voronoi.P, qcolor)

        painter = QPainter(self.pixmap())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        p = painter.pen()
        p.setWidth(width)
        p.setColor(qcolor)
        painter.setPen(p)
        for e in edges:
            e: Voronoi.Edge
            painter.drawLine(QPointF(e.startVertex.x, self.height()-e.startVertex.y), QPointF(
                e.endVertex.x, self.height()-e.endVertex.y))
        painter.end()
        # self.update()

    def mUpdate(self, x, y):
        if self.last_x is None:  # First event.
            if self.mode != self.Mode.FreeDraw and self.mode != self.Mode.FreeDraw != self.Mode.AddPoint:
                self.startPixmap = self.pixmap().copy()
            self.last_x = x
            self.last_y = y
            return  # Ignore the first time.

        # modifiers = QApplication.keyboardModifiers() # untrustable.  Use keyPressEvent instead
        if self.mode == self.Mode.FreeDraw:
            painter = QPainter(self.pixmap())
            p = painter.pen()
            p.setWidth(4)
            p.setColor(self.pen_color)
            painter.setPen(p)
            painter.drawLine(self.last_x, self.last_y, x, y)
            painter.end()
            self.update()

            # Update the origin for next time.
            self.last_x = x
            self.last_y = y
        elif self.mode == self.Mode.InsertCircle:
            pixmap = self.startPixmap.copy()
            painter = QPainter(pixmap)
            p = painter.pen()
            p.setWidth(4)
            p.setColor(self.pen_color)
            painter.setPen(p)

            if self.ctrl:
                painter.drawEllipse(
                    QPoint(self.last_x, self.last_y), x-self.last_x, y-self.last_y)
            else:
                painter.drawEllipse(self.last_x, self.last_y,
                                    x-self.last_x, y-self.last_y)

            painter.end()
            self.setPixmap(pixmap)
        elif self.mode == self.Mode.InsertRectangle:
            pixmap = self.startPixmap.copy()
            painter = QPainter(pixmap)
            p = painter.pen()
            p.setWidth(4)
            p.setColor(self.pen_color)
            painter.setPen(p)

            if self.ctrl:
                painter.drawRect(2*self.last_x-x, 2*self.last_y-y,
                                 (x-self.last_x)*2, (y-self.last_y)*2)
            else:
                painter.drawRect(self.last_x, self.last_y,
                                 x-self.last_x, y-self.last_y)

            painter.end()
            self.setPixmap(pixmap)
        elif self.mode == self.Mode.Crop:
            pixmap = self.startPixmap.copy()
            painter = QPainter(pixmap)
            # p = painter.pen()
            # p.setWidth(4)
            # p.setColor(Qt.GlobalColor.transparent)
            # painter.setPen(p)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.fillRect(self.last_x, self.last_y, x -
                             self.last_x, y-self.last_y, QColor(0, 0, 0, 0))
            # painter.setCompositionMode (QPainter::CompositionMode_SourceOver);

            painter.end()
            self.setPixmap(pixmap)

    def keyPressEvent(self, event: QKeyEvent):
        # modifiers = QApplication.keyboardModifiers() # untrustable.  Use keyPressEvent instead
        if event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
            self.wakePlayCondition()
            self.stepByStep = True
            self.continueUntilHP = False
            self.stepMs = Canvas.STEP_MS
        elif event.key() == Qt.Key.Key_H:
            self.stepMs = 0
            self.stepByStep = False
            self.continueUntilHP = True
            self.wakePlayCondition()
        elif event.key() == Qt.Key.Key_N:
            if self.stepByStep:
                self.stepMs = Canvas.STEP_MS
                self.stepByStep = False
                self.continueUntilHP = False
            else:
                self.stepMs = int(0.5 * self.stepMs)+1
            self.wakePlayCondition()
        elif event.key() == Qt.Key.Key_M:
            self.stepByStep = False
            self.continueUntilHP = False
            self.stepMs = 0
            self.wakePlayCondition()
        elif event.key() == Qt.Key.Key_Backspace:
            if self.mode == self.Mode.AddPoint:
                if len(self.polygons) > 0:
                    self.polygons.pop()
                    self.clearCanvas()
                    self.drawPoints(self.polygons)
                    self.update()
        elif event.key() == Qt.Key.Key_0:
            if self.mode == self.Mode.AddPoint:
                self.polygons = []
                self.clearCanvas()
                self.update()
        elif event.key() == Qt.Key.Key_S:
            if event.modifiers() & Qt.Modifier.CTRL:
                if self.workerThread.voronoiResult is None:
                    print('Nothing to save.')
                else:
                    fname, _ = QFileDialog.getSaveFileName(
                        self, 'Save File', '1.txt', 'Text files (*.txt);;XML files (*.xml)')
                    if fname != '':
                        self.workerThread.voronoiResult.save(fname)
        elif event.key() == Qt.Key_Control:
            self.ctrl = True
        if self.curX is not None and self.last_x is not None:
            self.mUpdate(self.curX, self.curY)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.ctrl = False
        if self.curX is not None and self.last_x is not None:
            self.mUpdate(self.curX, self.curY)

    def addPoint(self, x, y, computeImmediatly=True):
        self.polygons.append(Voronoi.Polygon(x, y))
        if computeImmediatly:
            self.stepByStep = False
            self.continueUntilHP = False
            self.stepMs = 0
            self.wakePlayCondition()
        else:
            self.clearCanvas()
            self.drawPoints(self.polygons)
            self.update()

    def mousePressEvent(self, e):
        if self.mode == self.Mode.AddPoint:
            self.addPoint(e.x(), self.height()-e.y())

    def mouseMoveEvent(self, e):
        if self.mode == self.Mode.AddPoint:
            if e.modifiers() & Qt.Modifier.CTRL:
                self.addPoint(e.x(), self.height()-e.y(),
                              computeImmediatly=False)
        self.curX = e.x()
        self.curY = e.y()
        self.mUpdate(e.x(), e.y())

    def mouseReleaseEvent(self, e):
        self.last_x = None
        self.last_y = None


COLORS = [
    # 17 undertones https://lospec.com/palette-list/17undertones
    '#000000', '#141923', '#414168', '#3a7fa7', '#35e3e3', '#8fd970', '#5ebb49',
    '#458352', '#dcd37b', '#fffee5', '#ffd035', '#cc9245', '#a15c3e', '#a42f3b',
    '#f45b7a', '#c24998', '#81588d', '#bcb0c2', '#ffffff',
]


class QPaletteButton(QPushButton):

    def __init__(self, color):
        super().__init__()
        self.color = color

        self.setFixedSize(QSize(32, 32))
        self.setStyleSheet(
            "background-color: %s; border-style: solid;  border-width:1px;  border-radius:50px;" % color)
        self.setMask(QRegion(QRect(0, 0, 28, 28), QRegion.Ellipse))


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voronoi")
        # self.resize(WIN_SIZE, WIN_SIZE)
        # self.mode = self.Mode.FreeDraw

        # Menu ------------------------------------------------

        menuBar = self.menuBar()
        # Creating menus using a title
        # fileMenu = menuBar.addMenu("&File")
        insertMenu = menuBar.addMenu("&Edit")
        # helpMenu = menuBar.addMenu("&Help")

        insertFreeDrawAction = QAction("&Free Draw", self)
        insertFreeDrawAction.triggered.connect(
            lambda: self.canvas.setMode(Canvas.Mode.FreeDraw))
        insertMenu.addAction(insertFreeDrawAction)

        insertCircleAction = QAction("&Circle", self)
        insertCircleAction.triggered.connect(self.insertCircle)
        insertMenu.addAction(insertCircleAction)

        insertRectAction = QAction("&Rectangle", self)
        insertRectAction.triggered.connect(self.insertRectangle)
        insertMenu.addAction(insertRectAction)

        insertCropAction = QAction("&Crop", self)
        insertCropAction.triggered.connect(
            lambda: self.canvas.setMode(Canvas.Mode.Crop))
        insertMenu.addAction(insertCropAction)

        # UI --------------------------------------------------

        self.canvas = Canvas()

        paletteLayout = QHBoxLayout()
        paletteLayout.addWidget(QWidget(), 1)
        self.add_palette_buttons(paletteLayout)
        paletteLayout.addWidget(QWidget(), 1)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas, 1)
        layout.addLayout(paletteLayout)

        mainWidget = QWidget()
        mainWidget.setLayout(layout)
        self.setCentralWidget(mainWidget)

    # def drawInitPoints(self, points):
    #     self.canvas.drawInitPoints(points)

    def add_palette_buttons(self, layout):
        for c in COLORS:
            b = QPaletteButton(c)
            b.pressed.connect(lambda c=c: self.canvas.set_pen_color(c))
            layout.addWidget(b)

    def insertCircle(self, event):
        # print('insertCircle')
        self.canvas.setMode(Canvas.Mode.InsertCircle)
        # self.mode = self.Mode.InsertCircle

    def insertRectangle(self, event):
        # print('insertRectangle')
        self.canvas.setMode(Canvas.Mode.InsertRectangle)
        # self.mode = self.Mode.InsertRectangle


# def apply_indices(array: np.ndarray, indices: np.ndarray):
#     indices = indices.reshape([len(indices), 1])
#     array = np.take_along_axis(array, indices, 0)
#     return array


# def sortCcw(center: np.ndarray, points: np.ndarray):
#     p2 = points.copy()
#     points -= center
#     xs = points[:, 0]
#     ys = points[:, 1]
#     helpXs = np.where(xs == 0, np.where(ys < 0, 0, 2), np.where(xs > 0, 1, 3))
#     helpYs = np.where(xs == 0, ys, ys/xs)
#     points = np.stack([helpXs, helpYs, xs, ys, p2[:, 0], p2[:, 1]], axis=-1)
#     indices: np.ndarray
#     indices = np.lexsort([ys, xs, helpYs, helpXs])
#     points = apply_indices(points, indices)
#     return points

def sortCcw(leftTop: Voronoi.Polygon, points: list):
    '''
    'leftTop': all points have same x with leftTop has smaller y than it

    if some points are collinear with 'leftTop',
    sort those points by the distance between 'leftTop', nearest first.
    '''
    nppoints = np.zeros([len(points), 2], np.float32)
    for i, p in enumerate(points):
        nppoints[i] = p.x, p.y
    # nppointsBac = nppoints  # .copy()

    leftTop = [leftTop.x, leftTop.y]
    nppoints -= leftTop
    xs = nppoints[:, 0]
    ys = nppoints[:, 1]
    helpXs = np.where(xs == 0, 0, 1)
    with np.errstate(divide='ignore', invalid='ignore'):
        helpYs = np.where(xs == 0, -ys, ys/xs)
    # nppoints = np.stack(
    #     [helpXs, helpYs, xs, ys, nppointsBac[:, 0], nppointsBac[:, 1]], axis=-1)
    indices: np.ndarray
    indices = np.lexsort([xs, helpYs, helpXs])
    # print(nppoints[:,:4])

    result = []
    for i in indices:
        result.append(points[i])
    return result


def ccw(A: Point, B: Point, C: Point = None) -> float:
    '''
    return > 0: Left turn

    return = 0: On the same line

    return < 0: Right turn
    '''
    # return (B[0] - A[0])*(C[1] - A[1]) - (B[1] - A[1])*(C[0] - A[0])
    # return (B.x - A.x)*(C.y - A.y) - (B.y - A.y)*(C.x - A.x)
    if C is None:
        return A*B
    return (B-A)*(C-A)


def GrahamScan(leftTop: Voronoi.Polygon, points: list):
    '''
    Collinear points would be kept, in both direction.
    '''
    ccwP = sortCcw(leftTop, points)

    # Repeat last collinear points
    iLast = len(ccwP)-1
    A = ccwP[0]
    C = ccwP[iLast]
    for i in range(iLast-1, 0, -1):
        if ccw(A, ccwP[i], C) != 0:
            break
        ccwP.append(ccwP[i])
    # print(ccwP)

    # GrahamScan
    i = 2
    resultCount = 2

    while i < len(ccwP):
        C = ccwP[i]
        isCcw = ccw(ccwP[resultCount-2], ccwP[resultCount-1], C)
        if isCcw >= 0:
            i += 1
            ccwP[resultCount] = C
            resultCount += 1
        else:
            resultCount -= 1

    return ccwP[:resultCount]


def getCrossEdges(points: list) -> Tuple[Optional[List[Point]]]:
    '''
    An Edge is returned left first as: [LeftPoint, RightPoint]
    '''
    i = 0
    crossEdgeTop = None
    crossEdgeBottom = None

    def checkCrossEdge(A: Voronoi.Polygon, B: Voronoi.Polygon):
        nonlocal crossEdgeTop, crossEdgeBottom
        if A.isLeft != B.isLeft:
            crossEdgeBottom = crossEdgeTop
            if A.isLeft:
                crossEdgeTop = [A, B]
            else:
                crossEdgeTop = [B, A]

    last = len(points)-1
    for i in range(last):
        checkCrossEdge(points[i], points[i+1])
    checkCrossEdge(points[0], points[last])

    if crossEdgeTop == crossEdgeBottom:
        crossEdgeBottom = crossEdgeTop

    return crossEdgeTop, crossEdgeBottom


def leftTop(points):
    ''' leftMost_thenTopMost '''
    ''' smallest x then bigger y '''
    l = points[0]
    l: Voronoi.Polygon
    p: Voronoi.Polygon
    for p in points[1:]:
        if p.x < l.x:
            l = p
        elif p.x == l.x:
            if p.y > l.y:
                l = p
    return l


class WorkerThread(QThread):
    canvasUpdate = pyqtSignal()
    clearCanvas = pyqtSignal()
    drawPoints = pyqtSignal(list)
    drawPolygon = pyqtSignal(list, QColor)
    drawVoronoiOrEdges = pyqtSignal(object, QColor, int)
    drawEdge = pyqtSignal(object, QColor, int, object)

    def __init__(self, canvas: Canvas):
        super(WorkerThread, self).__init__()
        self.num = 0
        self.polygons = []
        self.canvas = canvas
        self.firstDraw = True
        self.voronoiResult = None

    def run(self, *args, **kwargs):
        if len(sys.argv) > 1:
            try:
                with open(sys.argv[1], 'r', errors='ignore') as f:
                    if f.read(1) == 'P':
                        f.seek(0)
                        p = []
                        edges = []
                        for line in f.readlines():
                            words = line.split()
                            if len(words) >= 3:
                                if words[0] == 'P':
                                    p.append(Voronoi.Polygon(
                                        int(words[1]), int(words[2])))
                                else:
                                    e = Voronoi.Edge()
                                    e.startVertex = Point(
                                        float(words[1]), float(words[2]))
                                    e.endVertex = Point(
                                        float(words[3]), float(words[4]))
                                    edges.append(e)
                        self.voronoiResult = Voronoi(p, edges)
                        self.drawVoronoiOrEdges.emit(
                            self.voronoiResult, GRAY, 4)
                        return
                    else:
                        f.seek(0)
                        n = 0
                        iP = 0
                        for line in f.readlines():
                            iSharp = line.find('#')
                            if iSharp == 0:
                                continue
                            if iSharp > 0:
                                line = line[:iSharp]
                            words = line.split()
                            if len(words) == 0:
                                continue

                            # Done Extracting words, it should be like:
                            #   words = ['2']
                            #   words = ['100', '200']

                            if iP >= n:
                                n = int(words[0])
                                if n == 0:
                                    break
                                # P = np.zeros([n, 2], dtype=np.float32)
                                self.polygons = []
                                iP = 0
                                continue

                            x, y = int(words[0]), int(words[1])
                            # P[iP] = [x,y]
                            self.polygons.append(Voronoi.Polygon(x, y))
                            iP += 1

                            if iP >= n:
                                # if self.polygons is not None:
                                if DEBUG:
                                    print(
                                        '\nn =', n, '---------------------------------------------------------')
                                    print(self.polygons)
                                if self.firstDraw:
                                    self.firstDraw = False
                                else:
                                    self.canvas.waitNext()
                                self.voronoi(self.polygons)
            except Exception as e:
                print(traceback.format_exc())
                pass
            self.canvas.polygons = self.polygons
        while True:
            self.canvas.setMode(Canvas.Mode.AddPoint)
            self.canvas.waitNext()
            self.polygons = self.canvas.polygons.copy()
            n = len(self.polygons)
            if DEBUG:
                print(
                    '\nn =', n, '---------------------------------------------------------')
                print(self.polygons)
            self.voronoi(self.polygons)

    def voronoi(self, P: List[Voronoi.Polygon]) -> Voronoi:
        ''' Wrapper function '''

        if P is None or len(P) <= 0:
            return

        # sort by __lt__
        # sort small x first, then big y first
        P.sort()

        countNoDuplicate = 1
        for i in range(1, len(P)):
            if P[i] != P[countNoDuplicate-1]:
                P[countNoDuplicate] = P[i]
                countNoDuplicate += 1
        P = P[:countNoDuplicate]
        # print('After Dedup:', P)

        self.clearCanvas.emit()
        self.drawPoints.emit(self.polygons)
        try:
            self.voronoiResult = self._voronoi(P)
        except Exception as e:
            print(traceback.format_exc())
            self.canvas.waitStep()

    def _voronoi(self, polygons: List[Voronoi.Polygon]) -> Voronoi:
        '''
        P should be already sorted,
        and No duplicate Polygons allowed
        '''
        # if len(P) <= 0: # should not happen
        #     print('should not happen')
        #     return
        if len(polygons) == 1:
            return Voronoi(polygons)
        halfLen = len(polygons)//2
        vL = self._voronoi(polygons[:halfLen])
        vR = self._voronoi(polygons[halfLen:])
        for e in vL.edges:
            e.intersected = False
        for e in vR.edges:
            e.intersected = False
        chL = vL.P
        chR = vR.P
        for p in chL:
            p.isLeft = True
        for p in chR:
            p.isLeft = False
        # self.drawPolygon.emit(chL)
        # self.drawPolygon.emit(chR)
        lt = leftTop(chL)
        # print('\nLT = ',lt)
        ch = GrahamScan(lt, chL + chR)
        crossEdgeTop, crossEdgeBottom = getCrossEdges(ch)

        self.canvas.waitStep()
        self.clearCanvas.emit()
        self.drawEdge.emit(crossEdgeBottom, PURPLE, 4, Qt.PenStyle.DotLine)
        self.drawEdge.emit(crossEdgeTop, RED, 4, Qt.PenStyle.DotLine)
        self.drawPoints.emit(self.polygons)
        self.drawVoronoiOrEdges.emit(vL, BLUE, 4)
        self.drawVoronoiOrEdges.emit(vR, PURPLE, 4)
        # self.drawPolygon.emit(ch, BLUE)
        self.canvas.waitStep()
        intersection: Voronoi.Edge.Intersection = None
        bisector = Voronoi.Edge()
        HP: List[Voronoi.Edge] = []
        if DEBUG:
            print(polygons)
        while True:
            bisector.leftPolygon, bisector.rightPolygon = crossEdgeTop
            center: Point = (bisector.rightPolygon+bisector.leftPolygon)/2
            vector: Point = (bisector.rightPolygon-bisector.leftPolygon)
            vector.x, vector.y = -vector.y, vector.x
            a = ceil(WIN_SIZE*2/vector.norm())
            vector *= a
            if intersection is None:
                bisector.startVertex = Voronoi.Vertex(
                    center.x-vector.x, center.y-vector.y, bisector, isInfinite=True)
                bisector.endVertex = Voronoi.Vertex(
                    center.x+vector.x, center.y+vector.y, bisector, isInfinite=True)
            else:
                startVertex1 = Voronoi.Vertex(
                    intersection.x-vector.x, intersection.y-vector.y, bisector, isInfinite=True)
                startVertex2 = Voronoi.Vertex(
                    center.x-vector.x, center.y-vector.y, bisector, isInfinite=True)
                if startVertex1.lessThan_yFirst(startVertex2):
                    bisector.startVertex = startVertex1
                else:
                    bisector.startVertex = startVertex2

                bisector.endVertex = Voronoi.Vertex(
                    intersection.x, intersection.y, bisector, isInfinite=False)

            if DEBUG:
                print('crossEdgeTop', crossEdgeTop)
                print('  bisector.leftPolygon', bisector.leftPolygon)
                print('  bisector.rightPolygon', bisector.rightPolygon)
                print('  center', center)
                print('  vector', vector)
                print('  bisector', bisector)
            HP.append(bisector)

            # bisector has angle in range [0, 180)
            # (include angle 0 but not angle 180)

            def setBisectorPolygonEdge():
                if bisector.leftPolygon.edge is None:
                    bisector.leftPolygon.edge = bisector
                if bisector.rightPolygon.edge is None:
                    bisector.rightPolygon.edge = bisector
            setBisectorPolygonEdge()

            leftPolygonEdges = bisector.leftPolygon.edges(vL)
            rightPolygonEdges = bisector.rightPolygon.edges(vR)
            self.clearCanvas.emit()
            self.drawEdge.emit(crossEdgeBottom, PURPLE,
                               4, Qt.PenStyle.DotLine)
            self.drawEdge.emit(crossEdgeTop, RED, 4, Qt.PenStyle.DotLine)
            self.drawPoints.emit(self.polygons)
            self.drawVoronoiOrEdges.emit(vL, BLUE, 4)
            self.drawVoronoiOrEdges.emit(vR, PURPLE, 4)
            self.drawVoronoiOrEdges.emit(HP, RED, 4)
            self.drawVoronoiOrEdges.emit(leftPolygonEdges, GREEN, 8)
            self.drawVoronoiOrEdges.emit(rightPolygonEdges, LIGHT_GREEN, 4)
            if crossEdgeTop == crossEdgeBottom:
                break

            def lessThan(a: Point, b: Point):
                return a.y < b.y or (a.y == b.y and a.x < b.x)

            oldIntersection = intersection
            intersection: Voronoi.Edge.Intersection = None

            def findMaxIntersection(edges: List[Voronoi.Edge], isLeft):
                nonlocal intersection, oldIntersection
                if DEBUG:
                    if isLeft:
                        print('  left edges', edges)
                    else:
                        print('  right edges', edges)
                for e in edges:
                    # if e.intersected:
                    #     continue
                    if oldIntersection is not None:
                        if e is oldIntersection.edgeP:
                            continue
                        if e is oldIntersection.edgeQ:
                            continue
                    _intersection = bisector.intersection(e)
                    # if p is e: # collinear.  Should not happen if all points has different coordinate
                    #     continue
                    if _intersection is None or _intersection is bisector:
                        continue

                    newCrossEdgeTop = crossEdgeTop.copy()
                    if isLeft:
                        if crossEdgeTop[0] is _intersection.edgeQ.leftPolygon:
                            newCrossEdgeTop[0] = _intersection.edgeQ.rightPolygon
                        else:
                            newCrossEdgeTop[0] = _intersection.edgeQ.leftPolygon
                    else:
                        if crossEdgeTop[1] is _intersection.edgeQ.leftPolygon:
                            newCrossEdgeTop[1] = _intersection.edgeQ.rightPolygon
                        else:
                            newCrossEdgeTop[1] = _intersection.edgeQ.leftPolygon

                    # newCrossEdgeTop must move downward
                    if isLeft:
                        if ccw(crossEdgeTop[0], crossEdgeTop[1], newCrossEdgeTop[0]) > 0:
                            continue
                    else:
                        if ccw(crossEdgeTop[0], crossEdgeTop[1], newCrossEdgeTop[1]) > 0:
                            continue

                    # not working
                    # is_duplicated_crossEdgeTop = False
                    # for hp in HP:
                    #     if hp.leftPolygon is newCrossEdgeTop[0] and hp.rightPolygon is newCrossEdgeTop[1]:
                    #         is_duplicated_crossEdgeTop = True
                    #         break
                    # if is_duplicated_crossEdgeTop:
                    #     continue

                    def max(a: Point, b: Point):
                        if a is None:
                            return b
                        # if b is None:
                        #     return a
                        if lessThan(a, b):
                            return b
                        return a

                    _intersection.isLeft = isLeft
                    intersection = max(intersection, _intersection)
            findMaxIntersection(leftPolygonEdges, isLeft=True)
            findMaxIntersection(rightPolygonEdges, isLeft=False)
            if intersection is None:
                if DEBUG:
                    print('ERROR: intersection is None')
                    self.canvas.waitNext()
                break

            intersection.edgeQ.intersected = True
            if DEBUG:
                print('  edgeQ.leftPolygon', intersection.edgeQ.leftPolygon)
                print('  edgeQ.rightPolygon', intersection.edgeQ.rightPolygon)
            self.drawPolygon.emit([intersection], RED)
            self.canvas.waitStep()

            bisector.startVertex = Voronoi.Vertex(
                intersection.x, intersection.y, bisector.startVertex, isInfinite=False)
            if bisector.endVertex.isInfinite:
                if bisector.endVertex.lessThan_yFirst(intersection):
                    bisector.endVertex.x = intersection.x+vector.x
                    bisector.endVertex.y = intersection.y+vector.y
            nextBisector = Voronoi.Edge()
            if intersection.isLeft:
                bisector.ccwPredecessor = intersection.edgeQ
                bisector.cwPredecessor = nextBisector
                if intersection.rs < 0:
                    intersection.edgeQ.endVertex = Voronoi.Vertex(
                        intersection.x, intersection.y, intersection.edgeQ, isInfinite=False)
                    if intersection.u < 0:
                        intersection.edgeQ.startVertex += floor(
                            intersection.u-1)*intersection.s
                    intersection.edgeQ.cwSuccessor = bisector
                    intersection.edgeQ.ccwSuccessor = nextBisector
                else:
                    intersection.edgeQ.startVertex = Voronoi.Vertex(
                        intersection.x, intersection.y, intersection.edgeQ, isInfinite=False)
                    if intersection.u > 1:
                        intersection.edgeQ.endVertex += ceil(
                            intersection.u)*intersection.s
                    intersection.edgeQ.cwPredecessor = bisector
                    intersection.edgeQ.ccwPredecessor = nextBisector
                if crossEdgeTop[0] is intersection.edgeQ.leftPolygon:
                    crossEdgeTop[0] = intersection.edgeQ.rightPolygon
                else:
                    crossEdgeTop[0] = intersection.edgeQ.leftPolygon
            else:
                bisector.cwPredecessor = intersection.edgeQ
                bisector.ccwPredecessor = nextBisector
                if intersection.rs > 0:
                    intersection.edgeQ.endVertex = Voronoi.Vertex(
                        intersection.x, intersection.y, intersection.edgeQ, isInfinite=False)
                    if intersection.u < 0:
                        intersection.edgeQ.startVertex += floor(
                            intersection.u-1)*intersection.s
                    intersection.edgeQ.ccwSuccessor = bisector
                    intersection.edgeQ.cwSuccessor = nextBisector
                else:
                    intersection.edgeQ.startVertex = Voronoi.Vertex(
                        intersection.x, intersection.y, intersection.edgeQ, isInfinite=False)
                    if intersection.u > 1:
                        intersection.edgeQ.endVertex += ceil(
                            intersection.u)*intersection.s
                    intersection.edgeQ.ccwPredecessor = bisector
                    intersection.edgeQ.cwPredecessor = nextBisector
                if crossEdgeTop[1] is intersection.edgeQ.leftPolygon:
                    crossEdgeTop[1] = intersection.edgeQ.rightPolygon
                else:
                    crossEdgeTop[1] = intersection.edgeQ.leftPolygon

            oldBisector = bisector
            bisector = nextBisector

        v = Voronoi(polygons, vL.edges+HP+vR.edges)
        self.canvas.waitHP()
        self.clearCanvas.emit()
        self.drawPoints.emit(self.polygons)
        self.drawVoronoiOrEdges.emit(v, GRAY, 4)

        def isOfHP(vertex, isLeft):
            for hp in HP:
                if vertex.y > hp.endVertex.y+PRECISION and not hp.endVertex.isInfinite:
                    return False
                if vertex.y >= hp.startVertex.y or hp.startVertex.isInfinite:
                    _ccw = ccw(hp.startVertex, hp.endVertex, vertex)
                    if (isLeft and _ccw > PRECISION) or (not isLeft and _ccw < -PRECISION):
                        if DEBUG:
                            if isLeft:
                                print('  Delete Left Edge')
                            else:
                                print('  Delete Right Edge')
                            print('    hp.startVertex.isInfinite',
                                  hp.startVertex.isInfinite)
                            print('    hp.startVertex', hp.startVertex)
                            print('    hp.endVertex', hp.endVertex)
                            print('    vertex', vertex)
                            print('    ccw', _ccw)
                        return True
            return False
        deletedEdge = False
        count = 0
        for e in vL.edges:
            e: Voronoi.Edge
            if isOfHP(e.startVertex, isLeft=False):
                deletedEdge = True
                continue
            if isOfHP(e.endVertex, isLeft=False):
                deletedEdge = True
                continue
            vL.edges[count] = e
            count += 1
        vL.edges = vL.edges[:count]

        count = 0
        for e in vR.edges:
            e: Voronoi.Edge
            if isOfHP(e.startVertex, isLeft=True):
                deletedEdge = True
                continue
            if isOfHP(e.endVertex, isLeft=True):
                deletedEdge = True
                continue
            vR.edges[count] = e
            count += 1
        vR.edges = vR.edges[:count]

        if deletedEdge:
            v = Voronoi(polygons, vL.edges+HP+vR.edges)
            self.canvas.waitStep()
            self.clearCanvas.emit()
            self.drawPoints.emit(self.polygons)
            self.drawVoronoiOrEdges.emit(v, GRAY, 4)
        return v


if __name__ == '__main__':
    def main():
        global DEBUG
        for argv in sys.argv:
            if argv == '-debug':
                DEBUG = True
                break
        app = QApplication(sys.argv[:1])
        window = MainWindow()
        window.show()
        app.exec_()

    main()
