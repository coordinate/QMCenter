from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QTextEdit


class HelpWidget(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setWindowIcon(QIcon('images/logo.ico'))
        self.setWindowTitle(_('About QMCenter'))
        self.setFixedSize(400, 200)
        self.layout = QGridLayout(self)
        self.logo = QLabel()
        self.logo.setPixmap(QPixmap('images/logo.png').scaled(100, 100))
        self.main_text = QLabel(_('QMCenter v0.8\nGeoscan, LTD\nSome information'))
        self.third_party_text = QTextEdit()
        self.third_party_text.setText(_('This program use GDAL, OpenGL, PyQt,\n'
                                        'InnoSetup: Copyright (C) 1997-2019 Jordan Russell. All rights reserved.\n'
                                        'Portions Copyright (C) 2000-2019 Martijn Laan. All rights reserved.\n'
                                        'Icons used in this software are made by Freepik, from www.flaticon.com.'))
        self.third_party_text.setReadOnly(True)
        self.wiki = QLabel()
        self.wiki.setText("<html><a href=\"https://www.geoscan.aero/ru/services/aeromagnetic_survey\">" +
                          _("Support") + "</a></html>")
        self.wiki.setOpenExternalLinks(True)

        self.layout.addWidget(self.logo, 0, 0, 1, 1)
        self.layout.addWidget(self.main_text, 0, 1, 1, 1)
        self.layout.addWidget(self.third_party_text, 1, 0, 1, 2)
        self.layout.addWidget(self.wiki, 2, 0, 1, 2)
