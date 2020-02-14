import sys
from PySide2.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QTabWidget, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSizePolicy, QMessageBox
from PySide2.QtGui import QImage, QPixmap, QMouseEvent, QWheelEvent, QPainterPath, QGuiApplication, QPainter
from PySide2.QtCore import Signal, Slot, QObject, QEvent, QPointF, Qt, QFileSystemWatcher, QRectF
from PySide2.QtSvg import QSvgRenderer
import time, os


class View(QGraphicsView):
	# Tell TabWidget to set title for current tab
	image_dropped = Signal(str)

	def __init__(self):
		super(View, self).__init__(None)
		self.scene = QGraphicsScene()
		self.setScene(self.scene)
		self.pixmapitem = self.scene.addPixmap(QPixmap.fromImage(QImage()))
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
		extension = os.path.splitext(imagepath)[1]
		if extension.lower() in [".png", ".jpg", ".jpeg", ".gif", ".bmp"]:
			qimage = QImage(imagepath)
			pixmap = QPixmap.fromImage(qimage)
		elif extension == ".svg":
			# https://stackoverflow.com/a/25029983/4112667
			renderer = QSvgRenderer(imagepath)
			# The size of PNG is 33.3% bigger than SVG, so we expand SVG artificially.
			pixmap = QPixmap(renderer.defaultSize()*1.333)
			pixmap.fill(Qt.transparent)
			painter = QPainter(pixmap)
			renderer.render(painter, pixmap.rect())
			# https://www.cnblogs.com/cszlg/p/3355062.html
			painter.end()
		else:
			msgbox = QMessageBox(self)
			msgbox.setText("Doesn't support this format")
			msgbox.show()

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

	# When overwriting an image file, I guess Windows will delete it and then create
	# a new file with the same name. So this function will be called twice. The first
	# round is triggered by deleting. In this case, the image file doesn't exist, so
	# QImage and QPixmap are all invalid and as a result, the view will become white
	# background. Only after the image being created and the function is called for
	# the second time, will the view show the image normally. The User will notice a
	# white flicker because of two rounds of callings. To resolve this problem, we
	# need to detect the invalid QImage or QPixmap and skip the unintended round.
	def refresh_image(self, imagepath):
		qimage = QImage(imagepath)
		if qimage.isNull():
			return
		self.scene.removeItem(self.pixmapitem)
		self.pixmapitem = self.scene.addPixmap(QPixmap.fromImage(qimage))

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
		view = View()
		layout.addWidget(view)
		tab.setLayout(layout)
		self.addTab(tab, "A Tab")
		view.image_dropped.connect(self.set_tab_name)
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
