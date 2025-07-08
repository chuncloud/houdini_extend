# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/sw/PLE/workspace/lixy1/tickets/PLE-17641/bfx_extend_houdini/bfx_hou/tools/hda_shop/shelf_backup_tool/shelf_backup.ui'
#
# Created: Wed Sep 21 17:39:36 2022
#      by: PyQt4 UI code generator 4.10.1
#
# WARNING! All changes made in this file will be lost!

from BQt import QtCore, QtGui, QtWidgets

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(409, 92)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.verticalLayout_5 = QtWidgets.QVBoxLayout()
        self.verticalLayout_5.setObjectName(_fromUtf8("verticalLayout_5"))
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_5.addItem(spacerItem)
        self.button_update = QtWidgets.QPushButton(self.centralwidget)
        self.button_update.setText(_fromUtf8(""))
        self.button_update.setIconSize(QtCore.QSize(36, 36))
        self.button_update.setFlat(True)
        self.button_update.setObjectName(_fromUtf8("button_update"))
        self.verticalLayout_5.addWidget(self.button_update)
        self.label_update = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_update.setFont(font)
        self.label_update.setObjectName(_fromUtf8("label_update"))
        self.verticalLayout_5.addWidget(self.label_update)
        self.horizontalLayout_2.addLayout(self.verticalLayout_5)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.label_home_shelf = QtWidgets.QLabel(self.centralwidget)
        self.label_home_shelf.setMaximumSize(QtCore.QSize(30, 16777215))
        self.label_home_shelf.setObjectName(_fromUtf8("label_home_shelf"))
        self.horizontalLayout_5.addWidget(self.label_home_shelf)
        self.upload_cbbox = QtWidgets.QComboBox(self.centralwidget)
        self.upload_cbbox.setObjectName(_fromUtf8("upload_cbbox"))
        self.horizontalLayout_5.addWidget(self.upload_cbbox)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label_user = QtWidgets.QLabel(self.centralwidget)
        self.label_user.setObjectName(_fromUtf8("label_user"))
        self.horizontalLayout.addWidget(self.label_user)
        self.username_cbbox = QtWidgets.QComboBox(self.centralwidget)
        self.username_cbbox.setObjectName(_fromUtf8("username_cbbox"))
        self.horizontalLayout.addWidget(self.username_cbbox)
        self.label_server_shelf = QtWidgets.QLabel(self.centralwidget)
        self.label_server_shelf.setObjectName(_fromUtf8("label_server_shelf"))
        self.horizontalLayout.addWidget(self.label_server_shelf)
        self.shelf_cbbox = QtWidgets.QComboBox(self.centralwidget)
        self.shelf_cbbox.setObjectName(_fromUtf8("shelf_cbbox"))
        self.horizontalLayout.addWidget(self.shelf_cbbox)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.verticalLayout_6 = QtWidgets.QVBoxLayout()
        self.verticalLayout_6.setObjectName(_fromUtf8("verticalLayout_6"))
        self.up_button = QtWidgets.QPushButton(self.centralwidget)
        self.up_button.setObjectName(_fromUtf8("up_button"))
        self.verticalLayout_6.addWidget(self.up_button)
        self.down_button = QtWidgets.QPushButton(self.centralwidget)
        self.down_button.setObjectName(_fromUtf8("down_button"))
        self.verticalLayout_6.addWidget(self.down_button)
        self.horizontalLayout_3.addLayout(self.verticalLayout_6)
        self.horizontalLayout_2.addLayout(self.horizontalLayout_3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "Shelf Tool Backup", None))
        self.label_update.setText(_translate("MainWindow", "Update", None))
        self.label_home_shelf.setText(_translate("MainWindow", "shelf:", None))
        self.label_user.setText(_translate("MainWindow", "user:", None))
        self.label_server_shelf.setText(_translate("MainWindow", "shelf:", None))
        self.up_button.setText(_translate("MainWindow", "upload", None))
        self.down_button.setText(_translate("MainWindow", "download", None))

