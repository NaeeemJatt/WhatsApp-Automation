import sys
import threading
import time
import gc
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                             QLabel, QFileDialog, QSpinBox, QTextEdit, QMessageBox,
                             QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal

class WhatsAppAutomationApp(QWidget):
    customEvent = pyqtSignal(str)
    updateProgressBar = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.recipients = []
        self.driver = None  # To store WebDriver instance
        self.initUI()
        self.initLogger()

    def initLogger(self):
        logging.basicConfig(filename='whatsapp_automation.log', level=logging.ERROR,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def initUI(self):
        # Set window properties
        self.setWindowTitle('WhatsApp Messaging Application')
        self.setGeometry(100, 100, 700, 500)
        self.setStyleSheet('background-color: #2C2F33; color: #FFFFFF;')

        # Title Label
        self.titleLabel = QLabel('WhatsApp Automation')
        self.titleLabel.setStyleSheet('font-size: 28px; font-weight: bold; color: #FFFFFF;')
        self.titleLabel.setAlignment(Qt.AlignCenter)

        # Subtitle Label
        self.subtitleLabel = QLabel()
        self.subtitleLabel.setAlignment(Qt.AlignCenter)

        subtitleText = '<span style="font-size: 15px; font-style: italic; color: #AAAAAA;">by </span> ' \
                       '<span style="font-size: 25px; font-weight: bold; color: #FFFFFF;">NaeemJatt</span>'
        self.subtitleLabel.setText(subtitleText)

        # Input for recipient list
        self.importButton = QPushButton('Import Recipient List', self)
        self.importButton.setStyleSheet(
            '''
            QPushButton {
                background-color: #43B581;
                color: white;
                font-size: 16px;
                padding: 10px;
                border-radius: 10px;
            }
            QPushButton:pressed {
                background-color: #2E8B57;
                padding-left: 5px;
                padding-top: 5px;
            }
            '''
        )
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
            '''
            QPushButton {
                background-color: #43B581;
                color: white;
                font-size: 16px;
                padding: 10px;
                border-radius: 10px;
            }
            QPushButton:pressed {
                background-color: #2E8B57;
                padding-left: 5px;
                padding-top: 5px;
            }
            '''
        )
        self.sendButton.clicked.connect(self.sendMessages)

        # Progress Bar
        self.progressBar = QProgressBar(self)
        self.progressBar.setValue(0)
        self.progressBar.setStyleSheet('background-color: #23272A; color: #FFFFFF; font-size: 16px;')

        # Layouts
        vbox = QVBoxLayout()
        vbox.addWidget(self.titleLabel)
        vbox.addWidget(self.subtitleLabel)
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

        # Custom Events
        self.customEvent.connect(self.showMessageBox)
        self.updateProgressBar.connect(self.progressBar.setValue)

    def cleanup(self):
        """
        Cleanup method to release all used resources and memory.
        """
        if self.driver:
            try:
                self.driver.quit()
            except WebDriverException as e:
                logging.error(f"Error quitting WebDriver: {str(e)}")
            finally:
                self.driver = None

        for widget in QApplication.topLevelWidgets():
            try:
                widget.close()
                widget.deleteLater()
            except Exception as e:
                logging.error(f"Error closing widget: {str(e)}")

        gc.collect()

    def importRecipients(self):
        try:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(
                self,
                "Import Recipient List",
                "",
                "Text Files (*.txt);;All Files (*)",
                options=options
            )

            if fileName:
                try:
                    with open(fileName, 'r') as file:
                        self.recipients = [line.strip() for line in file if line.strip()]
                    self.showMessageBox("Success", "Recipient list imported successfully.")
                except (IOError, OSError) as file_error:
                    self.showMessageBox("Error", f"An error occurred while reading the file: {str(file_error)}")
                    logging.error(f"File Error: {str(file_error)}")
            else:
                self.showMessageBox("Warning", "No file selected.")

        except Exception as e:
            self.showMessageBox("Error", f"An unexpected error occurred: {str(e)}")
            logging.error(f"Unexpected Error: {str(e)}")

    def sendMessages(self):
        try:
            message = self.messageInput.toPlainText()
            delay = self.delayInput.value()

            if not message.strip():
                self.showMessageBox("Error", "Please enter a message to send.")
                return

            if not hasattr(self, 'recipients') or not self.recipients:
                self.showMessageBox("Error", "Please import a recipient list.")
                return

            threading.Thread(target=self.startSendingMessages, args=(message, delay), daemon=True).start()

        except Exception as e:
            self.showMessageBox("Error", f"An unexpected error occurred: {str(e)}")
            logging.error(f"Unexpected Error: {str(e)}")

    def startSendingMessages(self, message, delay):
        try:
            # Initialize WebDriver
            self.driver = webdriver.Chrome()

            # Open WhatsApp Web
            self.driver.get('https://web.whatsapp.com')

            # Wait for WhatsApp Web to load completely
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )

            for i, recipient in enumerate(self.recipients):
                try:
                    # Search for the recipient
                    search_box = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
                    )
                    search_box.clear()
                    search_box.send_keys(recipient)
                    time.sleep(2)
                    search_box.send_keys(Keys.ENTER)

                    # Wait for the message input box to load
                    message_box = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
                    )
                    message_box.click()
                    message_box.send_keys(message)
                    message_box.send_keys(Keys.ENTER)

                    self.updateProgressBar.emit(int((i + 1) / len(self.recipients) * 100))

                    # Random delay to mimic human behavior
                    time.sleep(delay + random.uniform(1, 3))

                except (NoSuchElementException, TimeoutException) as e:
                    logging.error(f"Failed to send message to {recipient}: {str(e)}")
                    self.showMessageBox("Error", f"Failed to send message to {recipient}. Check the recipient name and try again.")
                    continue

            self.showMessageBox("Success", "All messages sent successfully!")
            self.cleanup()

        except Exception as e:
            self.showMessageBox("Error", f"An unexpected error occurred during messaging: {str(e)}")
            logging.error(f"Unexpected Error: {str(e)}")
            self.cleanup()

    def showMessageBox(self, title, message):
        msgBox = QMessageBox()
        msgBox.setWindowTitle(title)
        msgBox.setText(message)
        msgBox.exec_()

    def closeEvent(self, event):
        self.cleanup()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = WhatsAppAutomationApp()
    ex.show()
    sys.exit(app.exec_())
