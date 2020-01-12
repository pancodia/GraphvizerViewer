import sys
from PySide2.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QTabWidget, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSizePolicy
from PySide2.QtGui import QImage, QPixmap, QMouseEvent, QWheelEvent, QPainterPath, QGuiApplication
from PySide2.QtCore import Signal, Slot, QObject, QEvent, QPointF, Qt, QFileSystemWatcher, QRectF
import time, os


class GraphvizerViewer(QGraphicsView):
	# Tell TabWidget to set title for current tab
	image_dropped = Signal(str)

	def __init__(self):
		super(GraphvizerViewer, self).__init__(None)
		self.scene = QGraphicsScene()
		self.setScene(self.scene)
		self.image = QImage()
		self.pixmapitem = self.scene.addPixmap(QPixmap.fromImage(self.image))
		self.last_release_time = 0
		self.watcher = QFileSystemWatcher()
		self.watcher.fileChanged.connect(self.refresh_image)

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
		pixmap = QPixmap.fromImage(self.image)
		self.scene.removeItem(self.pixmapitem)
		self.pixmapitem = self.scene.addPixmap(pixmap)
		# This will make scrollbar fit the image
		self.setSceneRect(QRectF(pixmap.rect()))
		# This will reset scale matrix, otherwise the new image will be scaled as the old image
		self.resetTransform()
		self.image_dropped.emit(os.path.basename(imagepath))
		# Register file watcher
		if len(self.watcher.files()) != 0:
			self.watcher.removePath(self.watcher.files()[0])
		self.watcher.addPath(imagepath)

	def refresh_image(self, imagepath):
		self.image = QImage(imagepath)
		self.scene.removeItem(self.pixmapitem)
		self.pixmapitem = self.scene.addPixmap(QPixmap.fromImage(self.image))

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


class TabWidget(QTabWidget):
	def __init__(self):
		super(TabWidget, self).__init__(None)
		self.setTabsClosable(True)
		self.tabCloseRequested.connect(self.close_tab)
		self.new_tab() # initial tab

	def close_tab(self, index):
		self.removeTab(index)

	def new_tab(self):
		tab = QWidget()
		layout = QHBoxLayout()
		viewer = GraphvizerViewer()
		layout.addWidget(viewer)
		tab.setLayout(layout)
		self.addTab(tab, "A Tab")
		viewer.image_dropped.connect(self.set_tab_name)
		self.setCurrentIndex(self.count()-1) # Switch to the new tab

	def set_tab_name(self, filebasename):
		self.setTabText(self.currentIndex(), filebasename)


class MainWindow(QWidget):
	def __init__(self):
		super(MainWindow, self).__init__(None)
		self.layout = QVBoxLayout()
		self.setLayout(self.layout)
		self.setWindowTitle("Graphvizer Viewer")
		# Default window size
		screen_rect = QGuiApplication.primaryScreen().availableGeometry()
		self.resize(screen_rect.width() * 3/5, screen_rect.height() * 4/5)
		# Add a button
		button = QPushButton("New Tab")
		button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
		self.layout.addWidget(button)
		# Add TabWidget
		tab_widget = TabWidget()
		self.layout.addWidget(tab_widget)
		# Create a new tab when the button is pressed
		button.clicked.connect(tab_widget.new_tab)


if __name__ == "__main__":
	app = QApplication(sys.argv)
	mainwindow = MainWindow()
	mainwindow.show()
	sys.exit(app.exec_())
