import PanoAnnotator.data as data
import PanoAnnotator.configs.Params as pm
import PanoAnnotator.utils as utils
import PanoAnnotator.views as views

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtGui import QPixmap

from OpenGL.GL import *
from OpenGL.GLU import *


class ResultView(QOpenGLWidget):
    def __init__(self, parent=None):
        super(ResultView, self).__init__(parent)

        self.__isAvailable = False
        self.__mainWindow = None
        self.__mainScene = None

        ### trackball
        self.__lastPos = QPoint()
        self.camRot = [0.0, 90.0, 0.0]
        self.camPos = [0.0, 0.0, 12.0]

        self.isPointCloudEnable = False
        self.isLayoutWallEnable = True
        self.isLayoutPointEnable = False

    #####
    #Comstum Method
    #####
    def initByScene(self, scene):
        self.__mainScene = scene

        #pointCloud = utils.createPointCloud(self.__mainScene.getPanoColorData(),
        #                                        self.__mainScene.getPanoDepthData() )
        #self.__mainScene.setPanoPointCloud(pointCloud)

        self.__isAvailable = True
        self.update()

    def drawWallPlane(self, wallPlane):

        glBegin(GL_QUADS)
        rgb = wallPlane.color
        glColor4f(rgb[0], rgb[1], rgb[2], 0.75)
        #glNormal3f(0.0, 0.0, 1.0)
        for p in wallPlane.corners:
            glVertex3f(p.xyz[0], p.xyz[1], p.xyz[2])
        glEnd()

    def drawEdges(self, obj):

        glLineWidth(3)
        glBegin(GL_LINE_STRIP)
        for p in obj.corners:
            glVertex3f(p.xyz[0], p.xyz[1], p.xyz[2])
        first = obj.corners[0]
        glVertex3f(first.xyz[0], first.xyz[1], first.xyz[2])
        glEnd()

    #####
    #Override
    #####
    def initializeGL(self):

        glClearColor(0.0, 0.0, 0.0, 1.0)
        #glClearColor(1.0, 1.0, 1.0, 1.0)
        glClearDepth(1.0)

        glShadeModel(GL_SMOOTH)
        #glShadeModel(GL_FLAT)

        #glEnable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        #glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_PROGRAM_POINT_SIZE)

    def paintGL(self):

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(self.camPos[0], self.camPos[1], self.camPos[2],
                  self.camPos[0], self.camPos[1], -1.0, 0.0, 1.0, 0.0)

        glPushMatrix()

        glRotated(self.camRot[0], 0.0, 1.0, 0.0)
        glRotated(self.camRot[1], 1.0, 0.0, 0.0)

        if self.__isAvailable:
            pointCloud = self.__mainScene.getPanoPointCloud()
            layoutPoints = self.__mainScene.label.getLayoutPoints()
            layoutWalls = self.__mainScene.label.getLayoutWalls()
            layoutObject2ds = self.__mainScene.label.getLayoutObject2d()

            if pointCloud and self.isPointCloudEnable:
                glPointSize(3)
                glBegin(GL_POINTS)
                for point in pointCloud:
                    glColor3f(
                        float(point[1][0]) / 255,
                        float(point[1][1]) / 255,
                        float(point[1][2]) / 255)
                    glVertex3f(point[0][0], point[0][1], point[0][2])
                glEnd()

            if self.isLayoutPointEnable:
                glPointSize(10)
                glBegin(GL_POINTS)
                rgb = (0.0, 0.5, 0.5)
                glColor3f(rgb[0], rgb[1], rgb[2])
                for point in layoutPoints:
                    glVertex3f(point.xyz[0], point.xyz[1], point.xyz[2])
                glEnd()

            if self.isLayoutWallEnable:
                for wall in layoutWalls:
                    self.drawWallPlane(wall)

            glColor3f(1, 1, 1)
            for obj2d in layoutObject2ds:
                self.drawEdges(obj2d)

        glPopMatrix()

    def resizeGL(sel, width, height):

        side = min(width, height)
        glViewport((width - side) // 2, (height - side) // 2, side, side)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        gluPerspective(60, width / height, 1.0, 1000)

    def mousePressEvent(self, event):
        self.setFocus(True)
        self.__lastPos = event.pos()

    def mouseMoveEvent(self, event):
        #print("point : {0} {1}".format(event.pos().x(), event.pos().y()))
        dx = event.x() - self.__lastPos.x()
        dy = event.y() - self.__lastPos.y()

        if event.buttons() == Qt.LeftButton:
            self.camRot[0] += 0.5 * dx
            self.camRot[1] += 0.5 * dy

        elif event.buttons() == Qt.RightButton:
            self.camPos[0] -= 0.02 * dx
            self.camPos[1] += 0.02 * dy

        self.__lastPos = event.pos()
        self.update()

    def wheelEvent(self, event):

        numAngle = float(event.angleDelta().y()) / 120
        self.camPos[2] -= numAngle
        self.update()

    def keyPressEvent(self, event):

        if (event.key() == Qt.Key_1):
            self.isPointCloudEnable = not self.isPointCloudEnable
        if (event.key() == Qt.Key_2):
            self.isLayoutWallEnable = not self.isLayoutWallEnable
        if (event.key() == Qt.Key_3):
            self.isLayoutPointEnable = not self.isLayoutPointEnable

        self.update()

    def enterEvent(self, event):
        self.setFocus(True)

    def leaveEvent(self, event):
        pass

    def setMainWindow(self, mainWindow):
        self.__mainWindow = mainWindow
