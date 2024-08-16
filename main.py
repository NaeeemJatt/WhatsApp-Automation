import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox,
                             QFileDialog, QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
import time


class WhatsAppThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, recipients, message, delay):
        super().__init__()
        self.recipients = recipients
        self.message = message
        self.delay = delay

    def run(self):
        try:
            driver = webdriver.Chrome()  # Ensure chromedriver is in your PATH
            driver.get('https://web.whatsapp.com')
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')))

            for index, recipient in enumerate(self.recipients):
                try:
                    search_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
                    search_box.clear()
                    search_box.send_keys(recipient)
                    time.sleep(2)
                    search_box.send_keys(Keys.ENTER)
                    time.sleep(2)

                    message_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
                    message_box.clear()
                    for part in self.message.split('\n'):
                        message_box.send_keys(part)
                        message_box.send_keys(Keys.SHIFT, Keys.ENTER)
                    message_box.send_keys(Keys.ENTER)
                    time.sleep(self.delay)
                    self.progress.emit(index + 1)
                except Exception as e:
                    print(f"Error sending message to {recipient}: {e}")

            driver.quit()
            self.finished.emit("All messages have been sent successfully!")
        except Exception as e:
            self.finished.emit(f"An error occurred: {e}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('WhatsApp Messaging Application')
        self.setGeometry(100, 100, 800, 600)
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText('Enter your message here')
        layout.addWidget(self.message_input)

        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(1, 300)
        self.delay_spinbox.setValue(10)
        layout.addWidget(self.delay_spinbox)

        self.import_button = QPushButton('Import Recipient List')
        self.import_button.clicked.connect(self.import_recipient_list)
        layout.addWidget(self.import_button)

        self.send_button = QPushButton('Send Messages')
        self.send_button.clicked.connect(self.send_messages)
        layout.addWidget(self.send_button)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.recipient_list = []

    def import_recipient_list(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Import Recipient List", "",
                                                   "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            with open(file_name, 'r') as file:
                self.recipient_list = [line.strip() for line in file if line.strip()]
            QMessageBox.information(self, 'Recipient List', 'Recipient list imported successfully!')

    def send_messages(self):
        message = self.message_input.text()
        delay = self.delay_spinbox.value()

        if not self.recipient_list:
            QMessageBox.warning(self, 'Error', 'Please import a recipient list.')
            return

        self.whatsapp_thread = WhatsAppThread(self.recipient_list, message, delay)
        self.whatsapp_thread.progress.connect(self.update_progress_bar)
        self.whatsapp_thread.finished.connect(self.show_message)
        self.whatsapp_thread.start()

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def show_message(self, message):
        QMessageBox.information(self, 'Status', message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
