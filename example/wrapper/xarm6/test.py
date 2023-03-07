# from xarm_controller import XArmCtrler

# arm = XArmCtrler()

# arm.write("a")
# arm.erase()


class VideoSourceCheckThread(QThread):
    finished = pyqtSignal()

    def __init__(self, index: int, source_name=None):
        super().__init__(parent=None)
        self.index = index
        self.source_name = source_name
        self.is_opened = None

    def check_source(self):
        pprint("This is")
        cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
        self.source_name = self.source_name or f"Video source {self.index+1}"
        self.is_opened = cap.isOpened()
        if cap:
            cap.release()
        self.finished.emit()


def update_available_video_sources(self, max_num=5):
    pprint("Start update_available_video_sources")
    threads = []
    for i in range(max_num):
        one_thread = self.VideoSourceCheckThread(i)
        one_thread.finished.connect(one_thread.check_source)
        threads.append(one_thread)
        one_thread.start()

    pprint("Flag 1 update_available_video_sources")

    for one_thread in threads:
        one_thread.wait()
        if one_thread.is_opened:
            self.available_sources.append(
                {"index": self.index, "name": self.source_name}
            )

    pprint("Flag 2 update_available_video_sources")

    if len(self.available_sources) <= 0:
        pprint("No video stream source is available")
    else:
        pprint(f"Available video stream sources: {self.available_sources}")
