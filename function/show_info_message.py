from PyQt5.QtWidgets import (QMessageBox)

def show_info_message(parent, title, text, button_size=(150, 80)):
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        msg_box.setStyleSheet("""
            QMessageBox {
                font-size: 25px;  /* 设置消息框基础字体大小 */
            }
            QMessageBox QLabel {
                font-size: 25px;  /* 设置文本内容的字体大小 */
            }
        """)
        
        # 设置按钮大小
        ok_button = msg_box.button(QMessageBox.Ok)
        if ok_button:
            ok_button.setFixedSize(*button_size)
            ok_button.setStyleSheet("""
                QPushButton {
                    font-size: 25px;
                }
            """)
        
        return msg_box.exec_()