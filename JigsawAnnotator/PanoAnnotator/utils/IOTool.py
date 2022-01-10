import json
import io

import PanoAnnotator.utils as utils
import PanoAnnotator.configs.Params as pm
import PanoAnnotator.configs.User as user
import PanoAnnotator.data as data

try:
    to_unicode = unicode
except NameError:
    to_unicode = str


def saveSceneAsMaps(path, scene):

    edgeMap = utils.genLayoutEdgeMap(scene, pm.layoutMapSize)
    utils.saveImage(edgeMap, path + '/label_edge_vp.png')

    oMap = utils.genLayoutOMap(scene, pm.layoutMapSize)
    utils.saveImage(oMap, path + '/label_omap.png')

    normalMap = utils.genLayoutNormalMap(scene, pm.layoutMapSize)
    utils.saveImage(normalMap, path + '/label_normal.png')

    depthMap = utils.genLayoutDepthMap(scene, pm.layoutMapSize)
    utils.saveDepth(depthMap, path + '/label_depth.png')

    obj2dMap = utils.genLayoutObj2dMap(scene, pm.layoutMapSize)
    utils.saveImage(obj2dMap, path + '/label_object2d.png')


def showLayoutMaps(scene, color=None):

    edgeMap = utils.genLayoutEdgeMap(scene, pm.layoutMapSize)
    if color is not None:
        color = utils.imageResize(color, [512, 1024])
        edgeMap = edgeMap * 0.5 + color * 0.5
    utils.showImage(edgeMap)

    obj2dMap = utils.genLayoutObj2dMap(scene, pm.layoutMapSize)
    obj2dMap = obj2dMap * 0.7 + color * 0.3
    utils.showImage(obj2dMap)

    #normalMap = utils.genLayoutNormalMap(scene, pm.layoutMapSize)
    #utils.showImage(normalMap)


def saveSceneAsJson(path, scene):

    points = scene.label.getLayoutPoints()
    pointsList = []
    for i, point in enumerate(points):
        pointDict = {
            'coords': point.coords,
            #'depth':float(point.depth),
            'xyz': list(point.xyz),
            'id': point.id
        }
        pointsList.append(pointDict)
    pointsDict = {'num': len(points), 'points': pointsList}

    walls = scene.label.getLayoutWalls()
    wallsList = []
    for i, wall in enumerate(walls):
        wallDict = {
            'pointsIdx':
            [points.index(wall.gPoints[0]),
             points.index(wall.gPoints[1])],
            'normal':
            list(wall.normal),
            'planeEquation':
            list(wall.planeEquation),
            'width':
            wall.width,
            'id':
            wall.id
        }
        wallsList.append(wallDict)
    wallsDict = {'num': len(walls), 'walls': wallsList}

    obj2ds = scene.label.getLayoutObject2d()
    obj2dsList = []
    for i, obj2d in enumerate(obj2ds):
        obj2dDict = {
            'wallIdx': walls.index(obj2d.attach),
            'points': [gp.xyz for gp in obj2d.gPoints],
            'coords': [list(obj2d.localBbox2d[0]),
                       list(obj2d.localBbox2d[1])],
            'width': obj2d.width,
            'id': obj2d.id,
            'obj_type': obj2d.obj_type,
        }
        obj2dsList.append(obj2dDict)
    obj2dsDict = {'num': len(obj2ds), 'obj2ds': obj2dsList}

    data = {
        'userName': user.name,
        'panoId': scene.getPanoColorPath(),
        'layoutHeight': scene.label.getLayoutHeight(),
        'cameraHeight': scene.label.getCameraHeight(),
        'cameraCeilingHeight': scene.label.getCam2CeilHeight(),
        'layoutPoints': pointsDict,
        'layoutWalls': wallsDict,
        'layoutObj2ds': obj2dsDict
    }

    with io.open(path, 'w', encoding='utf8') as outfile:
        str_ = json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False)
        outfile.write(to_unicode(str_))


def loadOldLabelByJson(path, scene):
    with open(path) as f:
        jdata = json.load(f)
    lh = 3.2
    jdata['z1'] = -jdata['z1']
    jdata['cameraHeight'] = jdata['z1']/(jdata['z1']+jdata['z0']) * lh
    jdata['cameraHeight'] = jdata['cameraHeight']
    jdata['layoutHeight'] = lh
    scene.label.setCameraHeight(jdata['cameraHeight'])
    scene.label.setLayoutHeight(jdata['layoutHeight'])
    print(lh, jdata['layoutHeight'], jdata['cameraHeight'])
    gPoints = []
    for i in range(1, len(jdata['uv']), 2):
        p = jdata['uv'][i]
        p[1] = 1-p[1]
        c = list(utils.coords2xyz(p, 1))
        c = list(utils.coords2xyz(p, jdata['cameraHeight']/c[1]))
        c[1] = 0
        xyz = tuple(c)
        gPoint = data.GeoPoint(scene, None, xyz)
        gPoints.append(gPoint)
    scene.label.setLayoutPoints(gPoints)


def loadLabelByJson(path, scene):

    with open(path) as f:
        jdata = json.load(f)

    scene.label.setCameraHeight(jdata['cameraHeight'])
    scene.label.setLayoutHeight(jdata['layoutHeight'])

    pointsDict = jdata['layoutPoints']
    pointsList = pointsDict['points']

    gPoints = []
    for point in pointsList:
        xyz = tuple(point['xyz'])
        gPoint = data.GeoPoint(scene, None, xyz)
        gPoints.append(gPoint)

    scene.label.setLayoutPoints(gPoints)

    walls = scene.label.getLayoutWalls()

    if 'layoutObj2ds' in jdata:

        obj2dsDict = jdata['layoutObj2ds']
        obj2dsList = obj2dsDict['obj2ds']

        object2ds = []
        for i, obj2d in enumerate(obj2dsList):
            gp1 = data.GeoPoint(scene, None, tuple(obj2d['points'][0]))
            gp2 = data.GeoPoint(scene, None, tuple(obj2d['points'][1]))
            wall = walls[int(obj2d['wallIdx'])]
            obj_type = int(obj2d['obj_type'])
            object2d = data.Object2D(scene, [gp1, gp2],
                                     wall,
                                     indx=i,
                                     obj_type=obj_type)
            object2ds.append(object2d)

        scene.label.setLayoutObject2d(object2ds)
