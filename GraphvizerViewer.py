import sys
from PySide2.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QTabWidget, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSizePolicy, QMessageBox
from PySide2.QtGui import QImage, QPixmap, QMouseEvent, QWheelEvent, QPainterPath, QGuiApplication, QDropEvent
from PySide2.QtCore import Signal, Slot, QObject, QEvent, QPointF, Qt, QFileSystemWatcher, QRectF, QUrl
from PySide2.QtWebEngineWidgets import QWebEngineView
import time, os


class ImageView(QGraphicsView):
	# Tell PageWidget that a file is dropped onto view.
	dropped_relay = Signal(QDropEvent)

	def __init__(self, image_path):
		super(ImageView, self).__init__(None)
		self.scene = QGraphicsScene()
		self.setScene(self.scene)
		self.pixmapitem = self.scene.addPixmap(QPixmap.fromImage(QImage(image_path)))
		self.last_release_time = 0
		self.watcher = QFileSystemWatcher()
		self.watcher.fileChanged.connect(self.refresh_image)
		# Register file watcher
		self.watcher.addPath(image_path)

	def dragEnterEvent(self, drag_enter_event): # QDragEnterEvent
		if drag_enter_event.mimeData().hasUrls():
			drag_enter_event.acceptProposedAction()

	# https://stackoverflow.com/a/4421835/4112667
	def dragMoveEvent(self, event):
		pass

	def dropEvent(self, drop_event): # QDropEvent
		self.dropped_relay.emit(drop_event)

	'''
	When overwriting an image file, I guess Windows will delete it and then create
	a new file with the same name. So this function will be called twice. The first
	round is triggered by deleting. In this case, the image file doesn't exist, so
	QImage and QPixmap are all invalid and as a result, the view will become white
	background. Only after the image being created and the function is called for
	the second time, will the view show the image normally. The User will notice a
	white flicker because of two rounds of callings. To resolve this problem, we
	need to detect the invalid QImage or QPixmap and skip the unintended round.
	'''
	def refresh_image(self, image_path):
		qimage = QImage(image_path)
		if qimage.isNull():
			return
		pixmap = QPixmap.fromImage(qimage)
		self.scene.removeItem(self.pixmapitem)
		self.pixmapitem = self.scene.addPixmap(pixmap)
		# This will make scrollbar fit the image
		self.setSceneRect(QRectF(pixmap.rect()))

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
				self.resetTransform() # Reset to original size (reset scale matrix)
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


# https://stackoverflow.com/a/17564897/4112667
class WebView(QWebEngineView):
	# Tell PageWidget that a file is dropped onto view.
	dropped_relay = Signal(QDropEvent)

	def __init__(self, image_path):
		'''
		Execution order: parent's __init__ -> self.event() -> rest code in self.__init__
		So, we must initialize at here, otherwise it will override value which is
		assigned in self.event().
		'''
		self.child_obj = None
		super(WebView, self).__init__(None)
		self.load(QUrl(image_path))
		self.watcher = QFileSystemWatcher()
		self.watcher.fileChanged.connect(self.refresh_image)
		# Register file watcher
		self.watcher.addPath(image_path)
		self.setContextMenuPolicy(Qt.NoContextMenu) # Disable right click context menu

	def dragEnterEvent(self, drag_enter_event): # QDragEnterEvent
		if drag_enter_event.mimeData().hasUrls():
			drag_enter_event.acceptProposedAction()

	# https://stackoverflow.com/a/4421835/4112667
	def dragMoveEvent(self, event):
		pass

	def dropEvent(self, drop_event): # QDropEvent
		self.dropped_relay.emit(drop_event)

	def refresh_image(self, image_path):
		if not os.path.isfile(image_path):
			return
		self.reload()

	'''
	https://forum.qt.io/post/549615
	This bug causes the mouse event is captured by child widget of QWebEngineView
	We register a filter to capture what we need.
	https://stackoverflow.com/a/33576854/4112667
	'''
	def event(self, event):
		if event.type() == QEvent.ChildAdded:
			obj = event.child()
			if obj is not None and type(obj) == QWidget:
				self.child_obj = obj
				self.child_obj.installEventFilter(self)
		return QWebEngineView.event(self, event)

	def eventFilter(self, obj, event):
		if obj == self.child_obj and event.type() == QEvent.Wheel:
			self.do_wheel(event)
			return True
		elif obj == self.child_obj and event.type() == QEvent.MouseButtonPress:
			self.start_mouse_pos = event.localPos()
			self.start_scroll_pos = self.page().scrollPosition()
			return QWebEngineView.eventFilter(self, obj, event) # Make scrollbar work normally
		elif obj == self.child_obj and event.type() == QEvent.MouseMove:
			# Only process mouse move with left button pressed
			if event.buttons() != Qt.LeftButton:
				return QWebEngineView.eventFilter(self, obj, event)
			# If Ctrl is pressed, use the default event handler. This enable select text.
			if QGuiApplication.queryKeyboardModifiers() == Qt.ControlModifier:
				return QWebEngineView.eventFilter(self, obj, event)
			'''
			OK. This is a mouse drag without Ctrl pressed. We will change it's behavior
			to something like ImageView.
			'''
			current_mouse_pos = event.localPos()
			delta = current_mouse_pos - self.start_mouse_pos
			'''
			Note: if mouse moves down 5 pixels, it's y-pos increase 5 pixels.
			The page should also move down 5 pixels which means the scrollbar should
			move up 5 pixels and the scroll position should decrease.
			'''
			target_scroll_pos = self.start_scroll_pos - delta

			'''
			Verify value range. I don't know if this is a must or whether this has any
			effects or not.
			'''
			target_scroll_x = target_scroll_pos.x()
			target_scroll_y = target_scroll_pos.y()
			if target_scroll_x < 0:
				target_scroll_x = 0
			if target_scroll_y < 0:
				target_scroll_y = 0
			if target_scroll_x > self.page().contentsSize().width():
				target_scroll_x = self.page().contentsSize().width()
			if target_scroll_y > self.page().contentsSize().height():
				target_scroll_y = self.page().contentsSize().height()

			'''
			We notice that if the page is zoomed in, the scrollbar moves faster than
			the mouse cursor. Besides, the scrollbar may jump a large distance towards
			the end in a weird way if you place the mouse cursor at the right bottom
			corner and try to drag the page towards the left upper corner several times.
			I don't know why but I print the target_scroll_pos which seems indeed correct.
			So I guess this may be caused by the scrollTo function in JavaScript. I think
			this function doesn't do things as I thought it would. Now that the page scrolls
			faster than mouse cursor dragging only after the page is zoomed in and it seems
			they have multiples relation, I guess if I divide the target_scroll_pos by
			zoomFactor, the page scrolling speed may be slow down and maybe scrollTo can
			scroll the page to correct position. Finally, this way is indeed the solution.
			However, I don't know why.
			If the page is zoomed out, it would be the opposite. The page scrolling speed
			should be sped up to match the mouse cursor.
			'''
			target_scroll_x /= self.zoomFactor()
			target_scroll_y /= self.zoomFactor()
			# https://forum.qt.io/topic/60091/scroll-a-qwebengineview/3
			self.page().runJavaScript(f"window.scrollTo({target_scroll_x}, {target_scroll_y})")
			return QWebEngineView.eventFilter(self, obj, event) # Make scrollbar work normally
		elif obj == self.child_obj and event.type() == QEvent.MouseButtonDblClick and event.buttons() == Qt.RightButton:
			self.setZoomFactor(1)
			return True

		return QWebEngineView.eventFilter(self, obj, event)

	def do_wheel(self, wheel_event): # QWheelEvent
		num_degrees = wheel_event.angleDelta().y() / 8
		num_steps = num_degrees / 15
		coefficient = 1 + (num_steps * 0.25)
		self.setZoomFactor(self.zoomFactor() * coefficient)


class PageWidget(QWidget):
	# Tell TabWidget to set title for current tab
	image_dropped = Signal(str)

	def __init__(self):
		super(PageWidget, self).__init__(None)
		self.layout = QHBoxLayout()
		self.setLayout(self.layout)
		self.setAcceptDrops(True) # https://stackoverflow.com/a/14895393/4112667

	def dragEnterEvent(self, drag_enter_event): # QDragEnterEvent
		if drag_enter_event.mimeData().hasUrls():
			drag_enter_event.acceptProposedAction()

	# https://stackoverflow.com/a/4421835/4112667
	def dragMoveEvent(self, event):
		pass

	'''
	This function is called in two scenarios.
	1. If the PageWidget already has a image, you need to drag new image onto the edge
	of PageWidget to trigger this function. The inner space is belong to XxxView.
	2. The inner view widget will relay a signal to this function.
	'''
	def dropEvent(self, drop_event): # QDropEvent
		url = drop_event.mimeData().urls()
		image_path = url[0].toLocalFile()
		extension = os.path.splitext(image_path)[1]
		if extension.lower() in [".png", ".jpg", ".jpeg", ".gif", ".bmp"]:
			image_view = ImageView(image_path)
			self.layout.takeAt(0) # Delete possibly existed widget
			self.layout.addWidget(image_view)
			image_view.dropped_relay.connect(self.dropEvent)
		elif extension == ".svg":
			web_view = WebView(image_path)
			self.layout.takeAt(0)
			self.layout.addWidget(web_view)
			web_view.dropped_relay.connect(self.dropEvent)
		else:
			msgbox = QMessageBox(self)
			msgbox.setText("Doesn't support this format")
			msgbox.show()
			return
		self.image_dropped.emit(os.path.basename(image_path))


class TabWidget(QTabWidget):
	def __init__(self):
		super(TabWidget, self).__init__(None)
		self.setTabsClosable(True)
		self.tabCloseRequested.connect(self.close_tab)
		self.new_tab() # initial tab

	def close_tab(self, index):
		self.removeTab(index)

	def new_tab(self):
		page = PageWidget()
		self.addTab(page, "A Page")
		page.image_dropped.connect(self.set_tab_name)
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
