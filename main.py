import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QFileDialog, QMessageBox, QProgressBar, QHBoxLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
import time


class WhatsAppSender(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("WhatsApp Message Sender")
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.create_form()

    def create_form(self):
        # Phone number input
        phone_label = QLabel("Phone Number:")
        self.phone_input = QLineEdit()
        phone_layout = QHBoxLayout()
        phone_layout.addWidget(phone_label)
        phone_layout.addWidget(self.phone_input)

        # Message input
        message_label = QLabel("Message:")
        self.message_input = QLineEdit()
        message_layout = QHBoxLayout()
        message_layout.addWidget(message_label)
        message_layout.addWidget(self.message_input)

        # Send Button
        self.send_button = QPushButton("Send Message")
        self.send_button.clicked.connect(self.send_message)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        # Adding widgets to the main layout
        self.layout.addLayout(phone_layout)
        self.layout.addLayout(message_layout)
        self.layout.addWidget(self.send_button)
        self.layout.addWidget(self.progress_bar)

    def send_message(self):
        phone_number = self.phone_input.text()
        message = self.message_input.text()

        if phone_number and message:
            self.progress_bar.setValue(0)
            self.thread = SendMessageThread(phone_number, message)
            self.thread.progress_signal.connect(self.update_progress)
            self.thread.finished_signal.connect(self.on_message_sent)
            self.thread.start()
        else:
            QMessageBox.warning(self, "Input Error", "Please enter both phone number and message.")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_message_sent(self, success):
        if success:
            QMessageBox.information(self, "Success", "Message sent successfully!")
        else:
            QMessageBox.critical(self, "Failure", "Failed to send message.")
        self.progress_bar.setValue(0)


class SendMessageThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)

    def __init__(self, phone_number, message):
        super().__init__()
        self.phone_number = phone_number
        self.message = message

    def run(self):
        try:
            self.send_whatsapp_message(self.phone_number, self.message)
            self.finished_signal.emit(True)
        except Exception as e:
            print(f"Error: {e}")
            self.finished_signal.emit(False)

    def send_whatsapp_message(self, phone_number, message):
        driver = webdriver.Chrome()  # Ensure that chromedriver is in your PATH
        driver.get(f"https://web.whatsapp.com/send?phone={phone_number}&text={message}")

        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "._1U1xa"))
        )

        input_box = driver.find_element(By.CSS_SELECTOR, "._1U1xa")
        input_box.send_keys(Keys.ENTER)

        for i in range(100):
            time.sleep(0.1)
            self.progress_signal.emit(i + 1)

        time.sleep(5)
        driver.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhatsAppSender()
    window.show()
    sys.exit(app.exec_())
