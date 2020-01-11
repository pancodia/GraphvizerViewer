import sys
from PySide2.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PySide2.QtGui import QImage, QPixmap, QMouseEvent, QWheelEvent
from PySide2.QtCore import Signal, Slot, QObject, QEvent, QPointF, Qt

class GraphvizerViewer(QObject):
	mouse_middle_button_wheeled = Signal(QWheelEvent)
	mouse_left_button_pressed = Signal(QMouseEvent)
	mouse_right_button_pressed = Signal(QMouseEvent)
	mouse_left_button_released = Signal(QMouseEvent)
	mouse_right_button_released = Signal(QMouseEvent)
	mouse_moved = Signal(QMouseEvent)

	def __init__(self):
		super(GraphvizerViewer, self).__init__(None)
		self.view = QGraphicsView()
		self.scene = QGraphicsScene()
		self.view.setScene(self.scene)
		self.image = QImage("E:\\multimedia\\picture\\忍者神龟\\F200705151517471444526594.jpg")
		self.scene.addPixmap(QPixmap.fromImage(self.image))
		self.view.show()
		self.mouse_middle_button_wheeled.connect(self.zoom)
		self.mouse_left_button_pressed.connect(self.pan)
		self.mouse_left_button_released.connect(self.pan_done)

	@Slot(QWheelEvent)
	def zoom(self, wheel_event):
		# https://doc.qt.io/qtforpython/PySide2/QtGui/QWheelEvent.html#PySide2.QtGui.PySide2.QtGui.QWheelEvent.angleDelta
		num_degrees = wheel_event.angleDelta().y() / 8
		num_steps = num_degrees / 15
		coefficient = 1 + (num_steps * 0.25)
		self.view.scale(coefficient, coefficient)

	@Slot(QMouseEvent)
	def pan(self, mouse_event):
		self.view.setDragMode(QGraphicsView.ScrollHandDrag)

	@Slot(QMouseEvent)
	def pan_done(self, mouse_event):
		self.view.setDragMode(QGraphicsView.NoDrag)

	# https://git.io/JepEs
	# https://www.qtcentre.org/threads/18447-wheelEvent-not-working-in-an-eventFilter
	def eventFilter(self, obj, event):
		if event.type() == QEvent.Wheel:
			self.mouse_middle_button_wheeled.emit(event)
			return True
		elif event.type() == QEvent.MouseButtonPress:
			if event.button() == Qt.LeftButton:
				self.mouse_left_button_pressed.emit(event)
			elif event.button() == Qt.RightButton:
				self.mouse_right_button_pressed.emit(event)
			elif event.button() == Qt.MidButton:
				pass
			return False
		elif event.type() == QEvent.MouseButtonRelease:
			if event.button() == Qt.LeftButton:
				self.mouse_left_button_released.emit(event)
			elif event.button() == Qt.RightButton:
				self.mouse_right_button_released.emit(event)
			elif event.button() == Qt.MidButton:
				pass
			return False
		else:
			return QObject.eventFilter(self, obj, event)

if __name__ == "__main__":
	app = QApplication(sys.argv)
	viewer = GraphvizerViewer()
	app.installEventFilter(viewer)
	sys.exit(app.exec_())
