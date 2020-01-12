import sys
from PySide2.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PySide2.QtGui import QImage, QPixmap, QMouseEvent, QWheelEvent, QPainterPath
from PySide2.QtCore import Signal, Slot, QObject, QEvent, QPointF, Qt
import time

class GraphvizerViewer(QGraphicsView):
	def __init__(self):
		super(GraphvizerViewer, self).__init__(None)
		self.scene = QGraphicsScene()
		self.setScene(self.scene)
		self.image = QImage("E:\\multimedia\\picture\\忍者神龟\\F200705151517471444526594.jpg")
		self.scene.addPixmap(QPixmap.fromImage(self.image))
		self.last_release_time = 0

	def mousePressEvent(self, mouse_event): # QMouseEvent
		if mouse_event.button() == Qt.LeftButton:
			self.setDragMode(QGraphicsView.ScrollHandDrag)
		elif mouse_event.button() == Qt.RightButton:
			self.setDragMode(QGraphicsView.RubberBandDrag)
		QGraphicsView.mousePressEvent(self, mouse_event)

	def mouseReleaseEvent(self, mouse_event): # QMouseEvent
		QGraphicsView.mouseReleaseEvent(self, mouse_event)
		if mouse_event.button() == Qt.LeftButton:
			self.setDragMode(QGraphicsView.NoDrag)
		elif mouse_event.button() == Qt.RightButton:
			self.setDragMode(QGraphicsView.NoDrag)

			now = time.time()
			delta = now - self.last_release_time
			self.last_release_time = now
			if delta < 0.3: # fast double click
				self.resetTransform() # Reset to original size
				return
			# Maybe a selection
			selection = self.scene.selectionArea().boundingRect()
			self.scene.setSelectionArea(QPainterPath())
			if selection.isValid():
				self.fitInView(selection, Qt.KeepAspectRatio)

	def wheelEvent(self, wheel_event): # QWheelEvent
		num_degrees = wheel_event.angleDelta().y() / 8
		num_steps = num_degrees / 15
		coefficient = 1 + (num_steps * 0.25)
		self.scale(coefficient, coefficient)

if __name__ == "__main__":
	app = QApplication(sys.argv)
	viewer = GraphvizerViewer()
	viewer.setWindowTitle("Graphvizer Viewer")
	viewer.show()
	sys.exit(app.exec_())
