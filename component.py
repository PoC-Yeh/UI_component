from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtWidgets import QFrame, QLineEdit, QCheckBox, QLabel, QPushButton, \
    QApplication, QDialog, QStyledItemDelegate
from PySide2.QtCore import Qt, Signal, QPoint
from PySide2.QtGui import QPixmap, QIcon, QColor
from functools import partial
import sys
import os


curr_path = os.path.dirname(os.path.abspath(__file__))
file_path = "/".join(curr_path.split("\\")[:-1]) + "/icon"
sys.path.insert(0, file_path)

# control drag the button
# set move_button to True to move the button
# set move_button to False would only emit the button_move signal and the moving amount
class MovableButton(QPushButton):
    property_change = Signal()
    shift_select = Signal()
    control_pressed = Signal()
    right_click = Signal()
    button_delete = Signal()
    button_move = Signal()

    STYLE = """
        QPushButton[selected=true]{
            background-color: white;
            color: black;
            font-size: 12px;
            }
        QPushButton[selected=false]{
            background-color: #33A6F0;
            font-size: 12px;
            }
        QPushButton:hover{
            background-color: #63B7FF;
            font-size: 12px;
            }
    """

    def __init__(self, move_button=False, parent=None):
        super(MovableButton, self).__init__(parent)

        self.move_button = move_button
        # self.move_button = True

        self.press_pos = None
        self.move_pos = None
        self.delta = None

        self.setProperty("selected", False)
        self.setStyleSheet(self.STYLE)

    def setSelectionStatus(self, set_num):
        # reverse selection
        if set_num == -1:
            self.setProperty("selected", not self.property("selected"))

        # set selection to True
        elif set_num == 1:
            self.setProperty("selected", True)

        # set selection to False
        elif set_num == 0:
            self.setProperty("selected", False)

        self.setStyle(self.style())
        self.property_change.emit()
        # print("button method --->selection status set to {}".format(set_num), self)

    @staticmethod
    def adjust_pos(x, y):
        # prevent button being dragged outside of the window
        adjusted_pos = [x, y]
        for index in range(0, len(adjusted_pos)):
            if adjusted_pos[index] <= 2:
                adjusted_pos[index] = 2
        return adjusted_pos

    def mousePressEvent(self, e):
        # record the start point of dragging
        if e.button() == QtCore.Qt.LeftButton:
            self.press_pos = e.globalPos()
            self.move_pos = e.globalPos()

        elif e.button() == QtCore.Qt.RightButton:
            # right click menu
            # self.setSelectionStatus(1)
            self.right_click.emit()

        modifierPressed = QApplication.keyboardModifiers()
        if modifierPressed == QtCore.Qt.ControlModifier:
            self.setSelectionStatus(1)
            self.control_pressed.emit()

    def mouseMoveEvent(self, e):
        modifierPressed = QApplication.keyboardModifiers()
        if modifierPressed == QtCore.Qt.ControlModifier:

            # adjust offset from clicked point to origin of widget
            # mapToGlobal: translates the widget coordinate pos to global screen coordinates.
            curr_pos = self.mapToGlobal(self.pos())
            global_pos = e.globalPos()
            self.delta = global_pos - self.move_pos

            # mapFromGlobal: Translates the global screen coordinate pos to widget coordinates.
            new_pos = self.mapFromGlobal(curr_pos + self.delta)  # new_pos == local position in Panel
            # print("new pos: ", new_pos)

            # prevent negative coordinates
            adjusted_pos = self.adjust_pos(new_pos.x(), new_pos.y())
            adjusted_pos = QPoint(adjusted_pos[0], adjusted_pos[1])

            # actually move the button
            if self.move_button:
                self.move(adjusted_pos)

            self.move_pos = global_pos
            self.button_move.emit()

    def mouseReleaseEvent(self, e):
        modifierPressed = QApplication.keyboardModifiers()
        if e.button() == QtCore.Qt.LeftButton:
            if self.press_pos:

                # not dragging, but only selecting
                moved = e.globalPos() - self.press_pos
                if moved.manhattanLength() < 10:

                    # shift select reverses everything
                    if modifierPressed == QtCore.Qt.ShiftModifier:
                        self.shift_select.emit()
                        self.setSelectionStatus(-1)

                    elif modifierPressed == QtCore.Qt.NoModifier:
                        # not selected --> selected
                        # if it's already selected --> remain selected, but still need to emit signal
                        self.setSelectionStatus(1)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Delete:
            self.button_delete.emit()


# used for TextEditableButton
class LineEditForButton(QLineEdit):
    double_clicked = Signal()
    left_clicked = Signal()
    focus_out = Signal()

    def __init__(self, parent=None):
        super(LineEditForButton, self).__init__(parent)

    def mousePressEvent(self, e):
        super(LineEditForButton, self).mousePressEvent(e)
        if e.button() == QtCore.Qt.LeftButton:
            self.left_clicked.emit()

    def mouseDoubleClickEvent(self, e):
        self.double_clicked.emit()

    # def focusOutEvent(self, e):
    #     super(LineEdit, self).focusOutEvent(e)
    #     self.focus_out.emit()
    #     print("oouttt")


# text editable QPushButton
# edit text by double clicking
# QLineEdit inside a QPushbutton
class TextEditableButton(QPushButton):
    lineEdit_leftClicked = Signal()
    STYLE = """
          QLineEdit[editMode=false]{
          background-color: transparent;
          }
          QLineEdit[editMode=true]{
          background-color: black;
          border-width: 0px;
          }    
    """

    def __init__(self, text_editable=False, text=None, parent=None):
        super(TextEditableButton, self).__init__(parent)
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        self.lineEdit = LineEditForButton()
        self.lineEdit.setFrame(False)

        self.text_editable = text_editable
        self.text = text
        if self.text:
            self.lineEdit.setText(self.text)

        self.lineEdit.setReadOnly(True)
        self.lineEdit.resize(self.lineEdit.sizeHint())
        self.lineEdit.editingFinished.connect(self.turnOffEditMode)
        self.lineEdit.editingFinished.connect(self.refreshText)
        self.lineEdit.double_clicked.connect(self.turnOnEditMode)
        self.lineEdit.left_clicked.connect(self.emitLineEditSignal)
        # self.lineEdit.focus_out.connect(self.turnOffEditMode)

        self.lineEdit.setProperty("editMode", False)
        self.layout.addWidget(self.lineEdit)
        self.layout.setContentsMargins(5, 0, 5, 0)
        self.setStyleSheet(self.STYLE)

    def turnOffEditMode(self):
        self.lineEdit.setReadOnly(True)
        self.lineEdit.setProperty("editMode", False)
        if self.text:
            self.lineEdit.setSelection(0, 0)
        self.setStyleSheet(self.STYLE)
        print("turn off edit mode")

    def turnOnEditMode(self):
        if self.text:
            self.lineEdit.setSelection(0, len(self.text))
        self.lineEdit.setReadOnly(False)
        self.lineEdit.setProperty("editMode", True)
        self.setStyleSheet(self.STYLE)

    def refreshText(self):
        self.text = self.lineEdit.text()
        print(self.text)

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton or e.button() == QtCore.Qt.RightButton:
            if self.lineEdit.property("editMode"):
                self.turnOffEditMode()

    def mouseDoubleClickEvent(self, e):
        if self.text_editable:
            self.turnOnEditMode()
        print("double click")

    def emitLineEditSignal(self):
        self.lineEdit_leftClicked.emit()


# default edit mode is false
# double click to enable editing
class LineEdit(QLineEdit):
    double_clicked = Signal()
    left_clicked = Signal()
    STYLE = """
          QLineEdit[editMode=false]{
          background-color: transparent;
          }
          QLineEdit[editMode=true]{
          background-color: black;
          border-width: 0px;
          }
    """

    def __init__(self, text, editMode=False, parent=None):
        super(LineEdit, self).__init__(parent)

        self._text = text
        self.edit = editMode
        if self._text:
            self.setText(text)

        if self.edit:
            self.turnOnEditMode()
        else:
            self.turnOffEditMode()

        self.__selected = False
        self.setStyleSheet(self.STYLE)

    @property
    def selected(self):
        return self.__selected

    def turnOffEditMode(self):
        self.setReadOnly(True)
        self.setProperty("editMode", False)
        if self._text:
            self.setSelection(0, 0)
        self.setStyle(self.style())
        # print("turn off edit mode")

    def turnOnEditMode(self):
        if self._text:
            self.setSelection(0, len(self._text))
        self.setReadOnly(False)
        self.setProperty("editMode", True)
        self.setStyle(self.style())

    def mouseDoubleClickEvent(self, e):
        if not self.property("editMode"):
            self.turnOnEditMode()
            self.double_clicked.emit()

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self.left_clicked.emit()
            # self.__selected = not self.__selected


class CheckBox(QFrame):
    property_change = Signal()
    STYLE = """
            QPushButton{
            background-color: transparent;
            font-size: 12px;
            border: transparent;
            color: rgba(240, 240, 240, 240);
            }
            QFrame[selected=true]{
            background-color: rgba(50, 170, 240, 200);
            }
            QFrame[selected=false]{
            background-color: transparent;
            }
            QFrame:hover{
            background-color: #84CBF9;
            }
    """

    def __init__(self, text_front=False, text=None, hide_box=False, direction=None, parent=None):
        super(CheckBox, self).__init__(parent)
        if not direction or direction == "H":
            self.layout = QtWidgets.QHBoxLayout()
            self.setLayout(self.layout)
        elif direction == "V":
            self.layout = QtWidgets.QVBoxLayout()
            self.setLayout(self.layout)

        # check box
        self.checked_img = QPixmap(curr_path + "/component_icon/checked.png")
        self.unchecked_img = QPixmap(curr_path + "/component_icon/unchecked.png")

        self.unchecked_img_mask = self.unchecked_img.mask()
        self.unchecked_img.fill(QColor(240, 240, 240, 180))
        self.unchecked_img.setMask(self.unchecked_img_mask)

        self.checkBox = QPushButton()
        self.checkBox.setIcon(QIcon(self.checked_img))
        self.checkBox.clicked.connect(partial(self.setSelectionStatus, -1))
        self.checkBox.setFixedSize(self.checkBox.sizeHint())

        # check box content
        self.checkContent = QPushButton()
        self.checkContent.setText(text)
        ####
        # self.checkContent = TextEditableButton(text_editable=True, text=text)
        # self.checkContent.lineEdit_leftClicked.connect(partial(self.setSelectionStatus, -1))
        ###
        self.checkContent.clicked.connect(partial(self.setSelectionStatus, -1))

        if not hide_box:
            # [V]text
            if not text_front and text:
                self.layout.addWidget(self.checkBox)
                self.layout.addWidget(self.checkContent)
            # text[V]
            elif text_front and text:
                self.layout.addWidget(self.checkContent)
                self.layout.addWidget(self.checkBox)
            # [V]
            elif not hide_box and not text:
                self.layout.addWidget(self.checkBox)

        else:
            # text
            if text:
                self.layout.addWidget(self.checkContent)

        self.setProperty("selected", True)
        self.setStyleSheet(self.STYLE)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignLeft)

    def setSelectionStatus(self, set_num):
        # reverse selection
        if set_num == -1:
            self.setProperty("selected", not self.property("selected"))
            if self.property("selected"):
                self.checkBox.setIcon(self.checked_img)
            else:
                self.checkBox.setIcon(self.unchecked_img)

        # set selection to True
        elif set_num == 1:
            self.setProperty("selected", True)
            self.checkBox.setIcon(self.checked_img)

        # set selection to False
        elif set_num == 0:
            self.setProperty("selected", False)
            self.checkBox.setIcon(self.unchecked_img)

        self.setStyle(self.style())
        self.property_change.emit()

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self.setSelectionStatus(-1)


