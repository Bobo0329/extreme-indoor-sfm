import numpy as np

import PanoAnnotator.data as data
import PanoAnnotator.utils as utils


class PushPred(object):
    def __init__(self, scene):

        self.__isAvailable = False
        self.__scene = scene

        self.__linesMapR = None
        self.__oMapR = None

        self.__size = [128, 256, 3]  #[256, 512, 3]

    def init(self):

        size = (self.__size[0], self.__size[1])
        oMap = self.__scene.getPanoOmapData()
        if oMap is not None:
            self.__oMapR = utils.imageResize(oMap, size)
        linesMap = self.__scene.getPanoLinesData()
        if linesMap is not None:
            self.__linesMapR = utils.imageResize(linesMap, size)

        if (self.__linesMapR is not None) and (self.__oMapR is not None):
            self.__isAvailable = True

    #####
    # GoldenSection search method
    #####
    def optimizeWallGS(self, wall, val):

        self.init()
        if not self.__isAvailable:
            print('PushPred not available')
            return
        utils.resetProgress(self.__scene, 3)

        step = abs(wall.planeEquation[3])
        step = step if val >= 0 else -step
        a = min(step / 10, step)
        b = max(step / 10, step)
        moveVal = self.goldenSectionSearch(wall, a, b, 3)
        self.__scene.label.moveWallByNormal(wall, moveVal)

    def optimizeLayoutGS(self):

        self.init()
        if not self.__isAvailable:
            print('PushPred not available')
            return
        utils.resetTimer()

        label = self.__scene.label
        walls = label.getLayoutWalls()
        utils.resetProgress(self.__scene, 6)

        floor = label.getLayoutFloor()
        moveVal = self.goldenSectionSearch(floor, 0, 1.0, 3)
        label.moveFloor(moveVal)

        ceiling = label.getLayoutCeiling()
        moveVal = self.goldenSectionSearch(floor, 0, 1.0, 3)
        label.moveCeiling(moveVal)

        #for wall in walls:
        #    step = abs(wall.planeEquation[3])
        #    moveVal = self.goldenSectionSearch(wall, -step, step , 3)
        #    label.moveWallByNormal(wall, moveVal)

        #utils.getRunTime()

    def goldenSectionSearch(self, obj, a, b, n):

        l = a + 0.382 * (b - a)
        h = a + 0.618 * (b - a)
        region = b - a
        num = 1

        while (region > 0.01 and num <= n):
            fl = self.lossFunction(obj, l)
            fh = self.lossFunction(obj, h)
            #print("iter{0} fl={1:.4f} fh{2:.4f}".format(num,fl,fh))
            if (fl > fh):
                a = l
                l = h
                h = a + 0.618 * (b - a)
            else:
                b = h
                h = l
                l = a + 0.382 * (b - a)
            num += 1
            region = abs(b - a)
            utils.updateProgress(self.__scene)  #0.6sec

        moveVal = (a + b) / 2
        return moveVal

    #####
    # Brute-force search method
    #####
    def optimizeWallBF(self, wall, val):

        self.init()
        utils.resetProgress(self.__scene, 5)

        step = abs(wall.planeEquation[3]) / 10
        step = step if val >= 0 else -step
        valList = [step * (i + 1) for i in range(5)]
        moveVal = self.bruteForceSearch(wall, valList)
        self.__scene.label.moveWallByNormal(wall, moveVal)

    def optimizeLayoutBF(self):

        self.init()
        label = self.__scene.label
        walls = label.getLayoutWalls()
        utils.resetProgress(self.__scene, 12 + len(walls) * 5)

        floor = label.getLayoutFloor()
        valList = [0, 0.1, 0.2, 0.3, 0.4, 0.5]
        moveVal = self.bruteForceSearch(floor, valList)
        label.moveFloor(moveVal)

        ceiling = label.getLayoutCeiling()
        valList = [0, 0.1, 0.2, 0.3, 0.4, 0.5]
        moveVal = self.bruteForceSearch(ceiling, valList)
        label.moveCeiling(moveVal)

        for wall in walls:
            step = abs(wall.planeEquation[3]) / 10
            valList = [0, 1 * step, 2 * step, 3 * step]
            moveVal = self.bruteForceSearch(wall, valList)
            label.moveWallByNormal(wall, moveVal)

    def bruteForceSearch(self, obj, valList):

        errList = []
        for val in valList:
            err = self.lossFunction(obj, val)
            errList.append(err)
            utils.updateProgress(self.__scene)
        minIdx = errList.index(min(errList))
        moveVal = valList[minIdx]

        return moveVal

    def lossFunction(self, obj, val):
        def calcMapError(self):
            #self.__scene.getMainWindows().refleshProcessEvent() #1.5sec

            normalMap = utils.genLayoutNormalMap(self.__scene, self.__size)
            omapMSE = utils.imagesMSE(normalMap, self.__oMapR)

            edgeMap = utils.genLayoutEdgeMap(self.__scene, self.__size)
            edgeMap = utils.imageDilation(edgeMap, 1)
            edgeMap = utils.imageGaussianBlur(edgeMap, 2)
            lineMSE = utils.imagesMSE(edgeMap, self.__linesMapR)
            #print('MSE lines:{0:.3f}  normal:{1:.3f}'.format(lineMSE,omapMSE))

            mix = omapMSE + lineMSE * 20
            return mix

        if (type(obj) == data.WallPlane):
            self.__scene.label.moveWallByNormal(obj, val)
            err = calcMapError(self)
            self.__scene.label.moveWallByNormal(obj, -val)

        elif (type(obj) == data.FloorPlane):
            if (obj.isCeiling()):
                self.__scene.label.moveCeiling(val)
                err = calcMapError(self)
                self.__scene.label.moveCeiling(-val)
            else:
                self.__scene.label.moveFloor(val)
                err = calcMapError(self)
                self.__scene.label.moveFloor(-val)

        return err
