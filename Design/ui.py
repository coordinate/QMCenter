from PyQt5.QtWidgets import QApplication, QMessageBox, QProgressDialog

photos = ['photos', 'фотографии']
filter_photos_by_markers_lbl = ["Filter Photos by Markers", "Отфильтровать по маркерам"]


def show_info(title, message):
    app = QApplication.instance()
    win = app.activeWindow()
    QMessageBox.information(win, title, message, QMessageBox.Ok)


def show_error(title, message):
    app = QApplication.instance()
    win = app.activeWindow()
    QMessageBox.critical(win, title, message, QMessageBox.Ok)
    # logger.log(loglevels.S_DEBUG, ("Got error: {} / {}".format(title, message))
    # logger.log(loglevels.S_DEBUG, ("Traceback: ", exc_info=1)


def show_warning_yes_no(title, message):
    app = QApplication.instance()
    win = app.activeWindow()
    return QMessageBox.warning(win, title, message, QMessageBox.Yes | QMessageBox.No)


def show_message_saveas_cancel_add(title, message):
    msg = QMessageBox()
    msg.setWindowTitle(title)
    msg.setIcon(QMessageBox.Warning)
    msg.setText(message)
    msg.addButton('Save as', QMessageBox.YesRole)
    msg.addButton('Cancel', QMessageBox.NoRole)
    msg.addButton('Add to project', QMessageBox.ApplyRole)

    return msg.exec_()


class ProgressBar:
    def __init__(self, text="", window_title="", modality=True, cancel_button=None):
        self.progress = QProgressDialog(text, cancel_button, 0, 100)
        # self.progress.setLabelText(text)
        self.progress.setModal(modality)
        self.progress.setWindowTitle(window_title)
        self.progress.show()
        self.update(0)

    def update(self, val):
        self.progress.setValue(val)
        self.progress.update()

    def __getattr__(self, *args, **kwargs):
        return self.progress.__getattribute__(*args, **kwargs)

