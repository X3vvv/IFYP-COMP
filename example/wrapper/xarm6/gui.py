import cv2
import sys
from threading import Thread
from PyQt5.QtCore import Qt, QTimer
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
    DEFAULT_VIDEO_SOURCE = 0

    def __init__(self):
        super().__init__()
        self.arm = None

        self.setWindowTitle("xArm")
        self.setGeometry(100, 100, 640, 480)

        # Create a label to display the video stream
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)

        # Create a dropdown list to choose the video source
        self.source_combobox = QComboBox(self)
        self.source_combobox.activated.connect(self.change_video_source)

        # Create buttons
        self.connect_arm_btn = QPushButton("Connect xArm", self)
        self.paint_btn = QPushButton("Paint", self)
        self.write_btn = QPushButton("Write", self)
        self.erase_btn = QPushButton("Erase", self)
        self.reset_btn = QPushButton("Reset", self)
        self.quit_btn = QPushButton("Quit", self)

        # Create write content input box
        self.write_content_input = QLineEdit(self)

        # Add button callbacks
        self.connect_arm_btn.clicked.connect(self.init_arm)
        self.quit_btn.clicked.connect(self.disconnet_arm)

        # Set widgets disabled before xArm is connected
        self.paint_btn.setDisabled(True)
        self.write_btn.setDisabled(True)
        self.write_content_input.setDisabled(True)
        self.erase_btn.setDisabled(True)
        self.quit_btn.setDisabled(True)

        # Create a vertical layout for the buttons
        self.sidebar = QVBoxLayout()
        self.sidebar.addWidget(self.source_combobox)
        self.sidebar.addWidget(self.connect_arm_btn)
        self.sidebar.addWidget(self.paint_btn)
        self.sidebar.addWidget(self.write_btn)
        self.sidebar.addWidget(self.write_content_input)
        self.sidebar.addWidget(self.erase_btn)
        self.sidebar.addWidget(self.reset_btn)
        self.sidebar.addWidget(self.quit_btn)

        # Create a horizontal layout for the label and buttons
        self.main_layout = QHBoxLayout()
        self.main_layout.addWidget(self.video_label)
        self.main_layout.addLayout(self.sidebar)

        # Set the layout as the central widget
        self.central_widget = QWidget(self)
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        # Initialize variables
        self.video = None
        self.timer = QTimer(self)

        # Add update frame into timer callback
        self.timer.timeout.connect(self.update_frame)

        # Populate the video source dropdown list
        self.update_available_video_sources()
        for source in self.available_sources:
            self.source_combobox.addItem(source["name"])

    def init_arm(self):
        self.arm = XArmCtrler()
        pprint("xArm connected")
        self.paint_btn.setDisabled(False)
        self.write_btn.setDisabled(False)
        self.write_content_input.setDisabled(False)
        self.erase_btn.setDisabled(False)
        self.reset_btn.setDisabled(False)
        self.quit_btn.setDisabled(False)

        # Add button callbacks
        self.paint_btn.clicked.connect(self.arm.paint)
        self.write_btn.clicked.connect(
            lambda: self.arm.write(self.write_content_input.text())
        )
        self.erase_btn.clicked.connect(self.arm.erase)
        self.quit_btn.clicked.connect(self.arm.quit)
        self.reset_btn.clicked.connect(self.arm.reset_location_and_gripper)

    def disconnet_arm(self):
        self.arm.quit()
        pprint("xArm disconnected")
        self.paint_btn.setDisabled(True)
        self.write_btn.setDisabled(True)
        self.write_content_input.setDisabled(True)
        self.erase_btn.setDisabled(True)
        self.reset_btn.setDisabled(True)
        self.quit_btn.setDisabled(True)

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

    def stop_video(self):
        # Stop the video timer and release the virtual camera
        self.timer.stop()
        if self.video:
            self.video.release()

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
        # Stop the current video and release the virtual camera
        self.stop_video()

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
    sys.exit(app.exec_())
