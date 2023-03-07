from threading import Thread
import cv2
import sys
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap
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
    class ArmWorker(QThread):
        finished = pyqtSignal()

        def init_arm(self):
            self.arm_ctrl = XArmCtrler()
            self.finished.emit()

        def paint(self):
            self.arm_ctrl.paint()
            self.finished.emit()

        def erase(self):
            self.arm_ctrl.erase()
            self.finished.emit()

        def write(self, content: str):
            self.arm_ctrl.write(content)
            self.finished.emit()

        def reset_location_and_gripper(self):
            self.arm_ctrl.reset_location_and_gripper()
            self.finished.emit()

        def quit(self):
            self.arm_ctrl.quit()
            self.finished.emit()

    DEFAULT_VIDEO_SOURCE = 0

    def __init__(self):
        super().__init__()
        self.arm_worker = self.ArmWorker()
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
        self.force_stop_btn = QPushButton("Force Stop", self)

        #######################
        ### Congigure Widgets
        #######################

        self.timer.timeout.connect(self.update_frame)  # keep updating frames
        self.video_label.setAlignment(Qt.AlignCenter)  # center label's content
        pass  # Change self.force_stop_btn color here

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
        self.paint_btn.setDisabled(True)
        self.write_btn.setDisabled(True)
        self.write_content_input.setDisabled(True)
        self.erase_btn.setDisabled(True)
        self.disconnect_arm_btn.setDisabled(True)

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

    def init_arm(self):
        self.arm_worker.init_arm()
        pprint("xArm connected")

        # Disable connect button
        self.connect_arm_btn.setDisabled(True)
        # Enable xArm controlling widgets
        self.paint_btn.setDisabled(False)
        self.write_btn.setDisabled(False)
        self.write_content_input.setDisabled(False)
        self.erase_btn.setDisabled(False)
        self.reset_btn.setDisabled(False)
        self.disconnect_arm_btn.setDisabled(False)

    def arm_paint(self):
        def task_done():
            self.paint_btn.setDisabled(False)

        self.paint_btn.setDisabled(True)
        self.arm_worker.finished.connect(self.arm_worker.paint)
        self.arm_worker.finished.connect(task_done)
        self.arm_worker.start()

    def arm_write(self, text: str):
        self.arm_worker.finished.connect(lambda: self.arm_worker.write(text))
        self.arm_worker.start()

    def arm_erase(self):
        self.arm_worker.finished.connect(self.arm_worker.erase)
        self.arm_worker.start()

    def arm_reset_location_and_gripper(self):
        self.arm_worker.finished.connect(self.arm_worker.reset_location_and_gripper)
        self.arm_worker.start()

    def disconnet_arm(self):
        self.arm_worker.finished.connect(self.arm_worker.quit)
        pprint("xArm disconnected")

        # Enable connect button
        self.connect_arm_btn.setDisabled(False)
        # Disable xArm controlling widgets
        self.paint_btn.setDisabled(True)
        self.write_btn.setDisabled(True)
        self.write_content_input.setDisabled(True)
        self.erase_btn.setDisabled(True)
        self.reset_btn.setDisabled(True)
        self.disconnect_arm_btn.setDisabled(True)

    def force_stop_arm(self):
        pprint("Force stopping xArm...")
        self.arm_worker.terminate()
        self.arm_worker.wait()

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

    app = QApplication(
        sys.argv
    )  # Ensure that the QApplication instance is not garbage collected
    player = VideoStreamer()
    player.start_video()
    player.show()
    sys.exit(app.exec())
