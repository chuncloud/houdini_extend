# -*- coding: utf-8 -*-

import sys
from . import constants

from BQt import QtCore, QtWidgets

try:
    import hou

except ImportError:
    pass


class Uploadfiles(QtWidgets.QDialog):

    def __init__(self, readfiles):
        super(Uploadfiles, self).__init__()
        self.names_list = []
        self.authors_list = []
        self.abouts_list = []
        self.is_check = False
        self.number = len(readfiles)

        self.setup_ui(readfiles)

        self.create_connect()

    def setup_ui(self, readfiles):

        vbox_layout1 = QtWidgets.QVBoxLayout()
        hbox_layout1 = QtWidgets.QHBoxLayout()
        hbox_layout2 = QtWidgets.QHBoxLayout()
        hbox_layout3 = QtWidgets.QHBoxLayout()

        name_label = QtWidgets.QLabel('Name')
        author_label = QtWidgets.QLabel('Author')
        about_label = QtWidgets.QLabel('About')
        hbox_layout1.addWidget(name_label, 5, QtCore.Qt.AlignHCenter)
        hbox_layout1.addWidget(author_label, 2, QtCore.Qt.AlignHCenter)
        hbox_layout1.addWidget(about_label, 10, QtCore.Qt.AlignHCenter)

        name_layout = QtWidgets.QVBoxLayout()
        author_layout = QtWidgets.QVBoxLayout()
        about_layout = QtWidgets.QVBoxLayout()

        # generate name,author,about lists based on the number of files dynamically
        for number in range(self.number):
            if readfiles[number].split('.')[-1] not in constants.OTL_TYPE:
                continue
            name_lineedit = 'name_lineedit' + str(number)
            author_lineedit = 'author_lineedit' + str(number)
            about_lineedit = 'about_lineedit' + str(number)
            locals()[name_lineedit] = QtWidgets.QLineEdit()
            locals()[author_lineedit] = QtWidgets.QLineEdit()
            locals()[about_lineedit] = QtWidgets.QLineEdit()

            hda_name = readfiles[number]
            locals().get(name_lineedit).setText(hda_name)

            name_layout.addWidget(locals().get(name_lineedit))
            author_layout.addWidget(locals().get(author_lineedit))
            about_layout.addWidget(locals().get(about_lineedit))

            self.names_list.append(locals().get(name_lineedit))
            self.authors_list.append(locals().get(author_lineedit))
            self.abouts_list.append(locals().get(about_lineedit))

        hbox_layout2.addLayout(name_layout, 5)
        hbox_layout2.addLayout(author_layout, 2)
        hbox_layout2.addLayout(about_layout, 10)

        self.button_box = QtWidgets.QDialogButtonBox()
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Save|
                                      QtWidgets.QDialogButtonBox.Cancel)
        self.check_box = QtWidgets.QCheckBox("External node")
        hbox_layout3.addWidget(self.check_box)
        hbox_layout3.addWidget(QtWidgets.QSplitter(), 7)
        hbox_layout3.addWidget(self.button_box, 5)

        self.setLayout(vbox_layout1)
        vbox_layout1.addLayout(hbox_layout1)
        vbox_layout1.addLayout(hbox_layout2)
        vbox_layout1.addLayout(hbox_layout3)

    def create_connect(self):
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.check_box.clicked.connect(self.checkbox_clicked)
        for number in range(self.number):
            self.names_list[number].textChanged.connect(self.check_name)

    def checkbox_clicked(self):
        self.is_check = self.check_box.isChecked()

    def check_name(self):
        for number in range(self.number):
            if self.names_list[number].text() != '':
                self.button_box.setDisabled(False)
            else:
                self.button_box.setDisabled(True)
                break

    @property
    def names(self):
        return self.names_list

    @names.setter
    def names(self, values):
        names_number = len(values)
        for number in range(names_number):
            self.names_list[number].setText(values[number])

    @property
    def authors(self):
        return self.authors_list

    @authors.setter
    def authors(self, value):
        for each_edit in self.authors_list:
            each_edit.setText(str(value))

    @property
    def abouts(self):
        return self.abouts_list


def main():
    """
    main function that's render when the script is render
    as a standalone script.
    """
    app = QtWidgets.QApplication(sys.argv)
    readfiles = ['1.hda', '2.hda', '3.hda', '4.hda']
    window = Uploadfiles(readfiles)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()