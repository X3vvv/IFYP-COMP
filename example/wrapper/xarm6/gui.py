from threading import Thread
import cv2
import sys
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QImage, QPixmap, QColor, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QLineEdit,
    QSizePolicy,
)

from xarm_controller import XArmCtrler, pprint

from main import speak


"""
Documentation can be found [here](https://doc.qt.io/qtforpython/index.html)
"""


"""
Reference: 
- https://www.qtcentre.org/threads/67614-QThread-does-not-work-as-it-is-supposed-to-do
- https://realpython.com/python-pyqt-qthread/
- https://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
"""


class InitThread(QThread):
    arm_ctrl_created = pyqtSignal()
    connection_error = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        try:
            self.arm_ctrl = XArmCtrler()
            speak("xArm connected")
            self.arm_ctrl_created.emit()
        except Exception as e:
            speak("Connection failed, xArm is not yet ready")
            self.connection_error.emit()

    @property
    def get_arm_ctrl(self):
        return self.arm_ctrl


class PaintThread(QThread):
    video_captured = pyqtSignal()

    def __init__(self, arm_ctrl: XArmCtrler, video_capture, parent=None):
        super().__init__(parent)
        self.arm_ctrl = arm_ctrl
        self.video_capture = video_capture

    def run(self):
        speak("Start painting")
        self.arm_ctrl.paint(self.video_capture)
        self.finished.emit()


class EraseThread(QThread):
    finished = pyqtSignal()

    def __init__(self, arm_ctrl: XArmCtrler, parent=None):
        super().__init__(parent)
        self.arm_ctrl = arm_ctrl

    def run(self):
        self.arm_ctrl.erase()
        self.finished.emit()


class WriteThread(QThread):
    finished = pyqtSignal()

    def __init__(self, arm_ctrl: XArmCtrler, text: str, parent=None):
        super().__init__(parent)
        self.text = text
        self.arm_ctrl = arm_ctrl

    def run(self):
        self.arm_ctrl.write(self.text)
        self.finished.emit()


class ResetThread(QThread):
    finished = pyqtSignal()

    def __init__(self, arm_ctrl: XArmCtrler, parent=None):
        super().__init__(parent)
        self.arm_ctrl = arm_ctrl

    def run(self):
        self.arm_ctrl.reset_location_and_gripper()
        self.finished.emit()


class QuitThread(QThread):
    finished = pyqtSignal()

    def __init__(self, arm_ctrl: XArmCtrler, parent=None):
        super().__init__(parent)
        self.arm_ctrl = arm_ctrl

    def run(self):
        self.arm_ctrl.quit()
        self.finished.emit()


class VideoStreamer(QMainWindow):
    DEFAULT_VIDEO_SOURCE = 0

    CONNECT_BTN_TEXT_NORMAL = "Connect xArm"
    CONNECT_BTN_TEXT_CONNECTING = "Connecting..."
    DISCONNECT_BTN_TEXT_NORMAL = "Disconnect xArm"
    DISCONNECT_BTN_TEXT_DISCONNECTING = "Disconnecting..."
    PAINT_BTN_TEXT_NORMAL = "Paint me!"
    PAINT_BTN_TEXT_PAINTING = "Painting..."
    WRITE_BTN_TEXT_NORMAL = "Write: "
    WRITE_BTN_TEXT_WRITING = "Writing..."
    ERASE_BTN_TEXT_NORMAL = "Erase"
    ERASE_BTN_TEXT_ERASING = "Erasing..."
    RESET_BTN_TEXT_NORMAL = "Reset"
    RESET_BTN_TEXT_RESETTING = "Resetting..."
    FORCE_STOP_BTN_TEXT_NORMAL = "Force Stop and Quit"
    FORCE_STOP_BTN_TEXT_QUITTING = "Quitting..."

    def __init__(self):
        super().__init__()
        self.video = None
        self.available_sources = []
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle("xArm")
        self.setGeometry(100, 100, 840, 480)

        ####################
        ### Create Widgets
        ####################

        self.timer = QTimer(self)  # add background timer
        self.video_label = QLabel(self)  # display the video stream
        self.video_source_label = QLabel(
            "Video Source:", self
        )  # label for video source
        self.source_combobox = QComboBox(self)  # choose the video source
        self.write_content_input = QLineEdit(self)  # content for xArm to write

        # Buttons
        self.connect_arm_btn = QPushButton(self.CONNECT_BTN_TEXT_NORMAL, self)
        self.disconnect_arm_btn = QPushButton(self.DISCONNECT_BTN_TEXT_NORMAL, self)
        self.paint_btn = QPushButton(self.PAINT_BTN_TEXT_NORMAL, self)
        self.write_btn = QPushButton(self.WRITE_BTN_TEXT_NORMAL, self)
        self.erase_btn = QPushButton(self.ERASE_BTN_TEXT_NORMAL, self)
        self.reset_btn = QPushButton(self.RESET_BTN_TEXT_NORMAL, self)
        self.force_stop_btn = QPushButton(self.FORCE_STOP_BTN_TEXT_NORMAL, self)

        #######################
        ### Congigure Widgets
        #######################

        self.timer.timeout.connect(self.update_frame)  # keep updating frames
        self.video_label.setAlignment(Qt.AlignCenter)  # center label's content
        self.write_btn.setFixedWidth(60)
        self.video_source_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Set force stop button color and font
        font = QFont()
        font.setBold(True)
        self.force_stop_btn.setFont(font)
        color = QColor(255, 0, 0)
        self.force_stop_btn.setStyleSheet(f"color: {color.name()};")

        # Button callbacks
        self.connect_arm_btn.clicked.connect(self.init_arm)
        self.disconnect_arm_btn.clicked.connect(self.disconnet_arm)
        self.paint_btn.clicked.connect(self.arm_paint)
        self.write_btn.clicked.connect(
            lambda: self.arm_write(self.write_content_input.text())
        )
        self.erase_btn.clicked.connect(self.arm_erase)
        self.reset_btn.clicked.connect(self.arm_reset_location_and_gripper)
        self.force_stop_btn.clicked.connect(self.force_stop_arm)

        # Disable widgets before xArm is connected
        self.paint_btn.setEnabled(False)
        self.write_btn.setEnabled(False)
        self.write_content_input.setEnabled(False)
        self.erase_btn.setEnabled(False)
        self.disconnect_arm_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        self.force_stop_btn.setEnabled(False)

        # Set dropdown list callback and populate with video sources
        self.source_combobox.activated.connect(self.change_video_source)
        self.update_available_video_sources()
        for source in self.available_sources:
            self.source_combobox.addItem(source["name"])

        #################################
        ### Create and Congigure Layouts
        #################################

        # VBox for video source
        self.video_source_layout = QVBoxLayout()
        self.video_source_layout.addWidget(self.video_source_label)
        self.video_source_layout.addWidget(self.source_combobox)

        # Vertical layout for the arm connetion/disconnection
        self.arm_connection_layout = QVBoxLayout()
        self.arm_connection_layout.addWidget(self.connect_arm_btn)
        self.arm_connection_layout.addWidget(self.disconnect_arm_btn)

        # Vertical layout for write function
        self.write_layout = QHBoxLayout()
        self.write_layout.addWidget(self.write_btn)
        self.write_layout.addWidget(self.write_content_input)

        # Vbox for arm function widgets
        self.arm_function_layout = QVBoxLayout()
        self.arm_function_layout.addWidget(self.paint_btn)
        self.arm_function_layout.addLayout(self.write_layout)
        self.arm_function_layout.addWidget(self.erase_btn)
        self.arm_function_layout.addWidget(self.reset_btn)

        # Vertical layout for side menu
        self.side_menu = QVBoxLayout()
        self.side_menu.addLayout(self.video_source_layout)
        self.side_menu.addLayout(self.arm_connection_layout)
        self.side_menu.addLayout(self.arm_function_layout)
        self.side_menu.addWidget(self.force_stop_btn)

        # Horizontal layout for the main window
        self.main_layout = QHBoxLayout()
        self.main_layout.addWidget(self.video_label)
        self.main_layout.addLayout(self.side_menu)

        # Set the layout as the central widget
        self.central_widget = QWidget(self)
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

    def enable_function_widgets(self, state: bool):
        self.paint_btn.setEnabled(state)
        self.write_btn.setEnabled(state)
        self.write_content_input.setEnabled(state)
        self.erase_btn.setEnabled(state)
        self.reset_btn.setEnabled(state)
        self.disconnect_arm_btn.setEnabled(state)

    def init_arm(self):
        def cleanup():
            self.connect_arm_btn.setText(self.CONNECT_BTN_TEXT_NORMAL)
            # Enable xArm controlling widgets
            self.enable_function_widgets(True)
            self.force_stop_btn.setEnabled(True)

        def set_arm_ctrl():
            self.arm_ctrl = self.initThread.arm_ctrl

        def connection_error_handler():
            self.connect_arm_btn.setEnabled(True)
            self.connect_arm_btn.setText(self.CONNECT_BTN_TEXT_NORMAL)

        self.connect_arm_btn.setEnabled(False)
        self.connect_arm_btn.setText(self.CONNECT_BTN_TEXT_CONNECTING)

        self.initThread = InitThread()
        self.initThread.arm_ctrl_created.connect(set_arm_ctrl)
        self.initThread.arm_ctrl_created.connect(cleanup)
        self.initThread.connection_error.connect(connection_error_handler)
        self.initThread.start()

        pprint("xArm connected")

    def arm_paint(self):
        def cleanup():
            self.enable_function_widgets(True)
            self.paint_btn.setText(self.PAINT_BTN_TEXT_NORMAL)

        self.enable_function_widgets(False)
        self.paint_btn.setText(self.PAINT_BTN_TEXT_PAINTING)

        speak("Say cheeze")
        self.paintThread = PaintThread(self.arm_ctrl, self.video)
        self.paintThread.finished.connect(cleanup)
        self.paintThread.start()

    def arm_erase(self):
        speak("Start erasing")

        def cleanup():
            self.enable_function_widgets(True)
            self.erase_btn.setText(self.ERASE_BTN_TEXT_NORMAL)

        self.enable_function_widgets(False)
        self.erase_btn.setText(self.ERASE_BTN_TEXT_ERASING)

        self.eraseThread = EraseThread(self.arm_ctrl)
        self.eraseThread.finished.connect(cleanup)
        self.eraseThread.start()

    def arm_write(self, text: str):
        speak("Start writing")

        def cleanup():
            self.enable_function_widgets(True)
            self.write_btn.setText(self.WRITE_BTN_TEXT_NORMAL)

        self.enable_function_widgets(False)
        self.write_btn.setText(self.WRITE_BTN_TEXT_WRITING)

        self.writeThread = WriteThread(self.arm_ctrl, text)
        self.writeThread.finished.connect(cleanup)
        self.writeThread.start()

    def arm_reset_location_and_gripper(self):
        speak("Resetting arm")

        def cleanup():
            self.enable_function_widgets(True)
            self.reset_btn.setText(self.RESET_BTN_TEXT_NORMAL)

        self.enable_function_widgets(False)
        self.reset_btn.setText(self.RESET_BTN_TEXT_RESETTING)

        self.resetThread = ResetThread(self.arm_ctrl)
        self.resetThread.finished.connect(cleanup)
        self.resetThread.start()

    def disconnet_arm(self):
        def switch_btn_state():
            # Disable xArm controlling widgets
            self.enable_function_widgets(False)
            self.force_stop_btn.setEnabled(False)

        def cleanup():
            # Restore disconnect button text and enable connect button
            self.disconnect_arm_btn.setText(self.DISCONNECT_BTN_TEXT_NORMAL)
            self.connect_arm_btn.setEnabled(True)
            speak("xArm disconnected")

        switch_btn_state()  # immediately disable all buttons but connect button
        self.disconnect_arm_btn.setText(self.DISCONNECT_BTN_TEXT_DISCONNECTING)

        quitThread = QuitThread(self.arm_ctrl)
        quitThread.finished.connect(cleanup)
        quitThread.start()

        pprint("xArm disconnected")

    def force_stop_arm(self):
        pprint("Force stopping xArm...")
        self.force_stop_btn.setText(self.FORCE_STOP_BTN_TEXT_QUITTING)
        XArmCtrler().emergency_stop()
        QApplication.quit()

    def start_video(self):
        # Open the virtual camera using OpenCV
        self.video = cv2.VideoCapture(
            self.available_sources[self.DEFAULT_VIDEO_SOURCE]["index"], cv2.CAP_DSHOW
        )
        if not self.video.isOpened():
            pprint("Failed to open camera.")
            sys.exit()

        # Start the video timer
        self.timer.start(33)  # 30 fps

    def update_frame(self):
        # Read the next frame of the video
        ret, frame = self.video.read()
        if not ret:
            print("Failed to read frame.")
            return
        # Convert the frame to RGB and resize it to fit the label
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.flip(frame, 1)  # horizontally flip

        # Convert the frame to a QImage
        image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)

        # Display the QImage on the label
        self.video_label.setPixmap(QPixmap.fromImage(image))

    class VideoCaptureThread(Thread):
        def __init__(self, index):
            Thread.__init__(self)
            self.index = index
            self.source_name = None
            self.cap = None
            self.result = False

        def run(self):
            self.cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
            self.source_name = f"Video source {self.index+1}"
            self.result = self.cap.isOpened()

        def release(self):
            if self.cap:
                self.cap.release()

        def isOpened(self):
            return self.result

    def update_available_video_sources(self, max_num=5) -> list:
        threads = []
        for i in range(max_num):
            thread = self.VideoCaptureThread(i)
            thread.start()
            threads.append(thread)

        self.available_sources = []
        for thread in threads:
            thread.join()
            if thread.isOpened():
                self.available_sources.append(
                    {"index": thread.index, "name": thread.source_name}
                )
            thread.release()

        if len(self.available_sources) <= 0:
            print("No video stream source is available")

    def change_video_source(self):
        # Stop the current video and release camera
        self.timer.stop()
        if self.video:
            self.video.release()

        # Get the index of the selected video source from the dropdown list
        index = self.source_combobox.currentIndex()

        # Open the selected video source using OpenCV
        self.video = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not self.video.isOpened():
            print("Failed to open camera.")
            return

        # Start the video timer
        self.timer.start(33)  # 30 fps


if __name__ == "__main__":

    app = QApplication(sys.argv)
    player = VideoStreamer()
    player.start_video()
    player.show()
    sys.exit(app.exec())
