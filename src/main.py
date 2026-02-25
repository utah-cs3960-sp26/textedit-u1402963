import sys

from editor.frame_timer import FrameTimerApp
from editor.window import MainWindow


def main():
    app = FrameTimerApp(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
