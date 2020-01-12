import sys
from PySide2.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PySide2.QtGui import QImage, QPixmap, QMouseEvent, QWheelEvent, QPainterPath, QGuiApplication
from PySide2.QtCore import Signal, Slot, QObject, QEvent, QPointF, Qt
import time, os


class GraphvizerViewer(QGraphicsView):
	def __init__(self):
		super(GraphvizerViewer, self).__init__(None)
		self.scene = QGraphicsScene()
		self.setScene(self.scene)
		self.image = QImage()
		self.pixmapitem = self.scene.addPixmap(QPixmap.fromImage(self.image))
		self.last_release_time = 0
		# Default window size
		screen_rect = QGuiApplication.primaryScreen().availableGeometry()
		self.resize(screen_rect.width() * 3/5, screen_rect.height() * 4/5)

	def dragEnterEvent(self, drag_enter_event): # QDragEnterEvent
		if drag_enter_event.mimeData().hasUrls():
			drag_enter_event.acceptProposedAction()

	# https://stackoverflow.com/a/4421835/4112667
	def dragMoveEvent(self, event):
		pass

	def dropEvent(self, drop_event): # QDropEvent
		url = drop_event.mimeData().urls()
		imagepath = url[0].toLocalFile()
		self.image = QImage(imagepath)
		self.scene.removeItem(self.pixmapitem)
		self.pixmapitem = self.scene.addPixmap(QPixmap.fromImage(self.image))
		self.setWindowTitle(os.path.basename(imagepath))

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
