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
)

from xarm_controller import XArmCtrler, pprint


"""
Documentation can be found [here](https://doc.qt.io/qtforpython/index.html)
"""


class VideoStreamer(QMainWindow):
    class ArmWorker(QObject):
        # tutorial: https://realpython.com/python-pyqt-qthread/
        finished = pyqtSignal()

        def init_arm(self):
            self.arm_ctrl = XArmCtrler()
            self.finished.emit()

        def paint(self):
            XArmCtrler().paint()
            self.finished.emit()

        def erase(self):
            XArmCtrler().erase()
            self.finished.emit()

        def write(self, content: str):
            XArmCtrler().write(content)
            self.finished.emit()

        def reset_location_and_gripper(self):
            XArmCtrler().reset_location_and_gripper()
            self.finished.emit()

        def quit(self):
            XArmCtrler().quit()
            self.finished.emit()

    DEFAULT_VIDEO_SOURCE = 0

    def __init__(self):
        super().__init__()
        self.video = None
        self.available_sources = []
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle("xArm")
        self.setGeometry(100, 100, 640, 480)

        ####################
        ### Create Widgets
        ####################

        self.timer = QTimer(self)  # add background timer
        self.video_label = QLabel(self)  # display the video stream
        self.source_combobox = QComboBox(self)  # choose the video source
        self.write_content_input = QLineEdit(self)  # content for xArm to write

        # Buttons
        self.connect_arm_btn = QPushButton("Connect xArm", self)
        self.disconnect_arm_btn = QPushButton("Disconnect xArm", self)
        self.paint_btn = QPushButton("Paint", self)
        self.write_btn = QPushButton("Write", self)
        self.erase_btn = QPushButton("Erase", self)
        self.reset_btn = QPushButton("Reset", self)  # reset arm location and gripper
        self.force_stop_btn = QPushButton("Force Stop and Quit", self)

        #######################
        ### Congigure Widgets
        #######################

        self.timer.timeout.connect(self.update_frame)  # keep updating frames
        self.video_label.setAlignment(Qt.AlignCenter)  # center label's content

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

        # Vertical layout for the arm connetion
        self.arm_connection_layout = QVBoxLayout()
        self.arm_connection_layout.addWidget(self.connect_arm_btn)
        self.arm_connection_layout.addWidget(self.disconnect_arm_btn)

        # Vertical layout for write function
        self.write_layout = QVBoxLayout()
        self.write_layout.addWidget(self.write_btn)
        self.write_layout.addWidget(self.write_content_input)

        # Vertical layout for side menu
        self.side_menu = QVBoxLayout()
        self.side_menu.addWidget(self.source_combobox)
        self.side_menu.addLayout(self.arm_connection_layout)
        self.side_menu.addWidget(self.paint_btn)
        self.side_menu.addLayout(self.write_layout)
        self.side_menu.addWidget(self.erase_btn)
        self.side_menu.addWidget(self.reset_btn)
        self.side_menu.addWidget(self.force_stop_btn)

        # Horizontal layout for the main window
        self.main_layout = QHBoxLayout()
        self.main_layout.addWidget(self.video_label)
        self.main_layout.addLayout(self.side_menu)

        # Set the layout as the central widget
        self.central_widget = QWidget(self)
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

    def arm_worker_start(self, worker, task_func, btn: QPushButton = None):
        self.work_thread = QThread()
        worker.moveToThread(self.work_thread)
        self.work_thread.started.connect(task_func)
        worker.finished.connect(self.work_thread.quit)
        worker.finished.connect(worker.deleteLater)
        self.work_thread.finished.connect(self.work_thread.deleteLater)
        self.work_thread.start()

        if btn is not None:
            btn.setEnabled(False)
            self.work_thread.finished.connect(lambda: btn.setEnabled(True))

    def init_arm(self):
        def core():
            self.worker.init_arm()
            # Disable connect button
            self.connect_arm_btn.setEnabled(False)
            # Enable xArm controlling widgets
            self.paint_btn.setEnabled(True)
            self.write_btn.setEnabled(True)
            self.write_content_input.setEnabled(True)
            self.erase_btn.setEnabled(True)
            self.reset_btn.setEnabled(True)
            self.disconnect_arm_btn.setEnabled(True)
            self.force_stop_btn.setEnabled(True)

        # worker = self.ArmWorker()
        # worker.init_arm()
        self.worker = self.ArmWorker()
        self.arm_worker_start(self.worker, core)

        pprint("xArm connected")

    def arm_paint(self):
        worker = self.ArmWorker()
        self.arm_worker_start(worker, worker.paint, self.paint_btn)

    def arm_erase(self):
        self.worker = self.ArmWorker()
        self.arm_worker_start(self.worker, self.worker.erase, self.erase_btn)

    def arm_write(self, text: str):
        self.worker = self.ArmWorker()
        self.arm_worker_start(
            self.worker, lambda: self.worker.write(text), self.write_btn
        )

    def arm_reset_location_and_gripper(self):
        self.worker = self.ArmWorker()
        self.arm_worker_start(
            self.worker, self.worker.reset_location_and_gripper, self.reset_btn
        )

    def disconnet_arm(self):
        worker = self.ArmWorker()
        self.arm_worker_start(worker, worker.quit)
        pprint("xArm disconnected")

        # Enable connect button
        self.connect_arm_btn.setEnabled(True)
        # Disable xArm controlling widgets
        self.paint_btn.setEnabled(False)
        self.write_btn.setEnabled(False)
        self.write_content_input.setEnabled(False)
        self.erase_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        self.disconnect_arm_btn.setEnabled(False)

    def force_stop_arm(self):
        pprint("Force stopping xArm...")
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
