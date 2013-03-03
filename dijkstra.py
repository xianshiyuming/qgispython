from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from qgis.networkanalysis import *
import math

#create graph from network data
vl = qgis.utils.iface.mapCanvas().currentLayer()
director = QgsLineVectorLayerDirector( vl, -1, '', '', '', 3 )
properter = QgsDistanceArcProperter()
director.addProperter( properter )
crs = qgis.utils.iface.mapCanvas().mapRenderer().destinationCrs()
builder = QgsGraphBuilder( crs )

#startpoint
pStart = QgsPoint( 	 )
delta = qgis.utils.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel() * 1

rb = QgsRubberBand( qgis.utils.iface.mapCanvas(), True )
rb.setColor( Qt.green )
rb.addPoint( QgsPoint( pStart.x() - delta, pStart.y() - delta ) )
rb.addPoint( QgsPoint( pStart.x() + delta, pStart.y() - delta ) )
rb.addPoint( QgsPoint( pStart.x() + delta, pStart.y() + delta ) )
rb.addPoint( QgsPoint( pStart.x() - delta, pStart.y() + delta ) )

#Graph analysis: calculate shortest paths using a dijkstra method.
tiedPoints = director.makeGraph( builder, [ pStart ] )
graph = builder.graph()
tStart = tiedPoints[0]

idStart = graph.findVertex( tStart )

( tree, cost ) = QgsGraphAnalyzer.dijkstra( graph, idStart, 0 )

def calc_dis(point1, point2):
  dis = (point1.x() - point2.x()) ** 2 + (point1.y() - point2.y()) ** 2
  return math.sqrt(dis)

def calc_angle(cent_pnt, around_pnt, dis):
  len = (around_pnt.x() - cent_pnt.x())
  value = len / dis
  radian = math.acos(value)
  if cent_pnt.y() - around_pnt.y() > 0:
    return 360 - (radian / 3.14) * 180
  else:
    return (radian / 3.14) * 180

#Choosing upper bound vertexes
upperBound = []
angle_dic = {}
r = 1000.0	#distance
i = 0

while i < len(cost):
	if cost[ i ] > r and tree[ i ] != -1:
		outVertexId = graph.arc( tree [ i ] ).outVertex()
		if cost[ outVertexId ] < r:
			upperBound.append( i )
			centerPoint = graph.vertex(i).point()
			qPoint = QgsPoint(centerPoint.x(),centerPoint.y())
			dis = calc_dis(pStart, qPoint)
			angle = calc_angle(pStart, qPoint, dis)
			angle_dic[angle] = qPoint
	i = i + 1

geomPolygon = []
for key, value in sorted(angle_dic.items()):
	geomPolygon.append(value)

#Create Polygon about areas of the availability
Polygonset = [geomPolygon]
gPolygon = QgsGeometry.fromPolygon(Polygonset)

#Visualization: show upperBound polygon area
r = QgsRubberBand(qgis.utils.iface.mapCanvas(), True)
r.setToGeometry(gPolygon, None)

#Visualization: show upperBound vertexes
for i in upperBound:
	centerPoint = graph.vertex( i ).point()
	rb = QgsRubberBand( qgis.utils.iface.mapCanvas(), True )
	rb.setColor( Qt.red )
	rb.addPoint( QgsPoint( centerPoint.x() - delta, centerPoint.y() - delta ) )
	rb.addPoint( QgsPoint( centerPoint.x() + delta, centerPoint.y() - delta ) )
	rb.addPoint( QgsPoint( centerPoint.x() + delta, centerPoint.y() + delta ) )
	rb.addPoint( QgsPoint( centerPoint.x() - delta, centerPoint.y() + delta ) )

#Export to Shapefile
# create & update layer
layer = QgsVectorLayer("Polygon", "temporary_polygons", "memory")
pr = layer.dataProvider()
pr.addAttributes( [ QgsField("id", QVariant.Int) ] )
feature = QgsFeature()
feature.setGeometry(gPolygon)
feature.setAttributeMap( { 0 : QVariant(1) } )
pr.addFeatures( [ feature ] )
layer.updateExtents()

# name your own file name
error = QgsVectorFileWriter.writeAsVectorFormat(layer, "C:\MGDdata\python\sample.shp", "utf-8", None, "ESRI Shapefile")

if error == QgsVectorFileWriter.NoError:
  print "success!"

