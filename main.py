import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QProgressBar, QHBoxLayout, QMessageBox, QFileDialog, QTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
        # Message input
        message_label = QLabel("Message:")
        self.message_input = QTextEdit()  # Changed to QTextEdit for multi-line input
        message_layout = QVBoxLayout()
        message_layout.addWidget(message_label)
        message_layout.addWidget(self.message_input)

        # File selection button
        self.file_button = QPushButton("Select Numbers File")
        self.file_button.clicked.connect(self.select_file)

        # Send Button
        self.send_button = QPushButton("Send Message")
        self.send_button.clicked.connect(self.send_messages_from_file)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        # Adding widgets to the main layout
        self.layout.addLayout(message_layout)
        self.layout.addWidget(self.file_button)
        self.layout.addWidget(self.send_button)
        self.layout.addWidget(self.progress_bar)

        self.numbers_file_path = None

    def select_file(self):
        # Open file dialog to select the numbers file
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Text Files (*.txt)")
        if file_dialog.exec_():
            self.numbers_file_path = file_dialog.selectedFiles()[0]
            QMessageBox.information(self, "File Selected", f"Selected file: {self.numbers_file_path}")

    def send_messages_from_file(self):
        message = self.message_input.toPlainText()  # Retrieve multi-line text

        if not message:
            QMessageBox.warning(self, "Input Error", "Please enter a message.")
            return

        if not self.numbers_file_path:
            QMessageBox.warning(self, "Input Error", "Please select a numbers file.")
            return

        # Open the file containing phone numbers
        try:
            with open(self.numbers_file_path, "r") as file:
                numbers = [line.strip() for line in file.readlines()]
        except Exception as e:
            QMessageBox.critical(self, "File Error", f"Failed to read the file: {str(e)}")
            return

        self.progress_bar.setValue(0)
        self.thread = SendMessagesThread(numbers, message)
        self.thread.progress_signal.connect(self.update_progress)
        self.thread.finished_signal.connect(self.on_messages_sent)
        self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_messages_sent(self, success):
        if success:
            QMessageBox.information(self, "Success", "Messages sent successfully!")
        else:
            QMessageBox.critical(self, "Failure", "Failed to send some or all messages.")
        self.progress_bar.setValue(0)


class SendMessagesThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)

    def __init__(self, numbers, message):
        super().__init__()
        self.numbers = numbers
        self.message = message

    def run(self):
        success = True
        try:
            # Start WebDriver and navigate to WhatsApp Web
            driver = webdriver.Chrome()
            driver.get("https://web.whatsapp.com")

            # Wait for the user to scan the QR code manually
            WebDriverWait(driver, 600).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "canvas"))
            )
            # Wait until the user is logged in and the chat list appears
            WebDriverWait(driver, 600).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[tabindex='-1']"))
            )

            for i, number in enumerate(self.numbers):
                self.send_whatsapp_message(driver, number, self.message)
                self.progress_signal.emit(int((i + 1) / len(self.numbers) * 100))
                time.sleep(2)  # Optional: Add a delay between messages

            driver.quit()
        except Exception as e:
            print(f"Error: {e}")
            success = False
        finally:
            self.finished_signal.emit(success)

    def send_whatsapp_message(self, driver, phone_number, message):
        try:
            search_xpath = "//div[@contenteditable='true' and @data-tab='3']"
            search_box = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, search_xpath))
            )
            search_box.click()
            search_box.clear()
            search_box.send_keys(phone_number)
            search_box.send_keys(Keys.ENTER)

            # Wait for the message box to appear and then send the message
            message_xpath = "//div[@contenteditable='true' and @data-tab='1']"
            input_box = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, message_xpath))
            )
            input_box.click()

            # Split the message into lines and send each line separately
            for line in message.split('\n'):
                input_box.send_keys(line)
                input_box.send_keys(Keys.SHIFT + Keys.ENTER)

            # Finally, send the message
            input_box.send_keys(Keys.ENTER)

            print(f"Message sent to {phone_number}.")
        except Exception as e:
            print(f"Failed to send message to {phone_number}: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhatsAppSender()
    window.show()
    sys.exit(app.exec_())
