import sys
import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QFileDialog, QSpinBox, QTextEdit, QMessageBox,
                             QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal


class WhatsAppAutomationApp(QWidget):
    customEvent = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Set window properties
        self.setWindowTitle('WhatsApp Messaging Application')
        self.setGeometry(100, 100, 700, 500)
        self.setStyleSheet('background-color: #2C2F33; color: #FFFFFF;')

        # Title Label
        self.titleLabel = QLabel('WhatsApp Automation')
        self.titleLabel.setStyleSheet('font-size: 28px; font-weight: bold; color: #FFFFFF;')
        self.titleLabel.setAlignment(Qt.AlignCenter)

        # Subtitle Label (Separate "by" and "NaeemJatt")
        self.subtitleLabel = QLabel()
        self.subtitleLabel.setAlignment(Qt.AlignCenter)

        subtitleText = '<span style="font-size: 15px; font-style: italic; color: #AAAAAA;">by </span> ' \
                       '<span style="font-size: 25px; font-weight: bold; color: #FFFFFF;">NaeemJatt</span>'
        self.subtitleLabel.setText(subtitleText)

        # Input for recipient list
        self.importButton = QPushButton('Import Recipient List', self)
        self.importButton.setStyleSheet(
            'background-color: #43B581; color: white; font-size: 16px; padding: 10px; border-radius: 10px;')
        self.importButton.clicked.connect(self.importRecipients)

        # Input for message
        self.messageInput = QTextEdit(self)
        self.messageInput.setPlaceholderText('Enter your message here')
        self.messageInput.setStyleSheet(
            'background-color: #23272A; color: #FFFFFF; border: 1px solid #7289DA; padding: 10px; font-size: 16px;')

        # Delay Input
        self.delayLabel = QLabel('Delay (seconds):')
        self.delayLabel.setStyleSheet('font-size: 16px; color: #FFFFFF;')
        self.delayInput = QSpinBox(self)
        self.delayInput.setValue(10)
        self.delayInput.setStyleSheet(
            'background-color: #23272A; color: #FFFFFF; border: 1px solid #7289DA; padding: 5px; font-size: 16px;')

        # Send Messages Button
        self.sendButton = QPushButton('Send Messages', self)
        self.sendButton.setStyleSheet(
            'background-color: #43B581; color: white; font-size: 16px; padding: 10px; border-radius: 10px;')
        self.sendButton.clicked.connect(self.sendMessages)

        # Progress Bar
        self.progressBar = QProgressBar(self)
        self.progressBar.setValue(0)
        self.progressBar.setStyleSheet('background-color: #23272A; color: #FFFFFF; font-size: 16px;')

        # Layouts
        vbox = QVBoxLayout()
        vbox.addWidget(self.titleLabel)
        vbox.addWidget(self.subtitleLabel)

        # Increased space between subtitle and import button
        vbox.addSpacing(20)

        hbox_import = QHBoxLayout()
        hbox_import.addStretch(1)
        hbox_import.addWidget(self.importButton)
        hbox_import.addStretch(1)
        vbox.addLayout(hbox_import)

        vbox.addWidget(self.messageInput)

        hbox_delay = QHBoxLayout()
        hbox_delay.addStretch(1)
        hbox_delay.addWidget(self.delayLabel)
        hbox_delay.addWidget(self.delayInput)
        hbox_delay.addStretch(1)
        vbox.addLayout(hbox_delay)

        hbox_send = QHBoxLayout()
        hbox_send.addStretch(1)
        hbox_send.addWidget(self.sendButton)
        hbox_send.addStretch(1)
        vbox.addLayout(hbox_send)

        vbox.addWidget(self.progressBar)

        self.setLayout(vbox)

        # Custom Event
        self.customEvent.connect(self.showMessageBox)

    def importRecipients(self):
        try:
            options = QFileDialog.Options()
            fileName, _ = QFileDialog.getOpenFileName(self, "Import Recipient List", "",
                                                      "Text Files (*.txt);;All Files (*)", options=options)

            if fileName:
                with open(fileName, 'r') as file:
                    self.recipients = file.read().splitlines()

                # Show a message box to confirm successful import
                self.showMessageBox("Success", "Recipient list imported successfully.")

            else:
                # If no file is selected, show a warning
                self.showMessageBox("Warning", "No file selected.")

        except Exception as e:
            # If there's an error, display it
            self.showMessageBox("Error", f"An error occurred while importing the file: {str(e)}")
            print(f"Error: {str(e)}")  # This will print to the console for debugging

    def sendMessages(self):
        message = self.messageInput.toPlainText()
        delay = self.delayInput.value()

        if not message:
            self.showMessageBox("Error", "Please enter a message to send.")
            return

        if not hasattr(self, 'recipients') or not self.recipients:
            self.showMessageBox("Error", "Please import a recipient list.")
            return

        threading.Thread(target=self.startSendingMessages, args=(message, delay)).start()

    def startSendingMessages(self, message, delay):
        driver = webdriver.Chrome()

        try:
            driver.get('https://web.whatsapp.com')

            for i, recipient in enumerate(self.recipients):
                search_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
                search_box.clear()
                search_box.send_keys(recipient)
                search_box.send_keys(Keys.ENTER)
                time.sleep(2)

                message_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="9"]')
                message_box.clear()
                message_box.send_keys(message)
                message_box.send_keys(Keys.ENTER)

                self.progressBar.setValue(int((i + 1) / len(self.recipients) * 100))
                time.sleep(delay)

        except Exception as e:
            self.customEvent.emit(f"An error occurred: {str(e)}")
        finally:
            driver.quit()
            self.customEvent.emit("Messages sent successfully.")

    def showMessageBox(self, title, message):
        QMessageBox.information(self, title, message)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = WhatsAppAutomationApp()
    ex.show()
    sys.exit(app.exec_())
