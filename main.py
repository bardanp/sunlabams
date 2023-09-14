"""
Author: Bardan Phuyel
E-mail: bvp5359@psu.edu
Course: CMPSC 487W
Assignment: Project 1
Due date: 9/13/2023
File: main.py
Purpose: Python application that handles SunLab AMS Main Dashboard and Access Control
Reference(s):
1. PyQt6 Documentation: https://www.riverbankcomputing.com/static/Docs/PyQt6/index.html
2. Firebase Admin SDK: https://firebase.google.com/docs/admin/setup
3. Qt Layout Management: https://doc.qt.io/qt-6/layout.html
4. QMessageBox: https://doc.qt.io/qt-6/qmessagebox.html
5. Python Datetime: https://docs.python.org/3/library/datetime.html
6. Firestore Server Timestamp: https://firebase.google.com/docs/firestore/manage-data/add-data#server_timestamp
7. Qt Event Handling: https://doc.qt.io/qt-6/eventsandfilters.html
8. Python String Methods: https://docs.python.org/3/library/stdtypes.html#string-methods
9. PyQt6 QWidget: https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qwidget.html
10. Python sys library: https://docs.python.org/3/library/sys.html
11. https://www.pythonguis.com/tutorials/creating-multiple-windows/
12. https://www.youtube.com/watch?v=82v2ZR-g6wY
13. https://firebase.google.com/docs/admin/setup
"""
import datetime
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton, QWidget, QLabel, QTextEdit, QVBoxLayout, QMessageBox, QApplication
from firebase_admin import firestore

import firebase_init
from styles import *

# Initialize firebase and get the db client
firebase_init.initialize_firebase()
db = firestore.client()


# Access Window for SunLab Door
class AccessWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SunLab Door Access")
        self.setFixedSize(500, 300)

        # Create and set the layout for the widgets
        accessLayout = QVBoxLayout()

        # Create widgets and set their properties
        accessLabel = QLabel("<h1>Please enter your PSU ID:</h1>")
        accessLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.accessField = QTextEdit()
        self.accessField.setPlaceholderText("Enter your ID here (EX: 912345678)")

        # Create action buttons and connect to their slots
        accessButton = QPushButton("Sign In/Out")
        accessButton.clicked.connect(self.process_access_request)
        backButton = QPushButton("Back")
        backButton.clicked.connect(self.show_dashboards)

        # Apply CSS styles to the widgets
        self.accessField.setStyleSheet(textEditBoxStyling)
        accessButton.setStyleSheet(normalButtonStyling)
        backButton.setStyleSheet(backButtonStyling)

        # Add widgets to the layout
        accessLayout.addWidget(accessLabel)
        accessLayout.addWidget(self.accessField)
        accessLayout.addWidget(accessButton)
        accessLayout.addWidget(backButton)

        # Set the window's layout
        self.setLayout(accessLayout)

    # Slot to close the current window and go back to the dashboard
    def show_dashboards(self):
        self.close()

    # Slot to process the access request when the "Sign In/Out" button is clicked
    def process_access_request(self):
        # Get the PSU ID from the input field, strip any whitespace
        inputPSUID = self.accessField.toPlainText().strip()

        # Validate the PSU ID format
        if not inputPSUID.isdigit() or len(inputPSUID) != 9:
            QMessageBox.warning(self, "Invalid ID", "Please enter a valid PSU ID!")
            return

        # Retrieve the user info from Firestore
        allUsersfromDB = db.collection(u'users')
        userInfo = allUsersfromDB.document(inputPSUID).get().to_dict()

        # Check if the user exists and their status
        if not userInfo:
            QMessageBox.warning(self, "Access Denied", "ID not found!")
            return
        if userInfo.get("Status") == "suspended":
            QMessageBox.warning(self, "Access Denied", "Your access has been suspended!")
            return

        # get or create the access log from Firestore
        accessLogsfromDB = db.collection(u'access_logs')
        existingAccessLog = accessLogsfromDB.where("id", "==", inputPSUID).where("exited", "==", None).limit(1).get()

        # Check if an existing log is found for the user
        if existingAccessLog:
            for doc in existingAccessLog:
                doc.reference.update({"exited": firestore.SERVER_TIMESTAMP})
            QMessageBox.information(self, "Access Log", "Successfully logged exit from Sunlab.")
        else:
            log_id = f"LOG#{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            accessLogsfromDB.document(log_id).set({
                "id": inputPSUID,
                "name": userInfo.get("FirstName") + " " + userInfo.get("LastName"),
                "entered": firestore.SERVER_TIMESTAMP,
                "exited": None
            })
            QMessageBox.information(self, "Access Log", "Successfully logged entry into Sunlab.")


# Main dashboard, asks the user to either sign-in/sign-out or go to the admin panel, which has user management
# and history logs access control
class mainDashboard(QWidget):
    # noinspection PyUnresolvedReferences
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SunLab AMS")
        self.setFixedSize(650, 250)
        layout = QVBoxLayout()

        headerLabel = QLabel("<h1>SunLab Access Dashboard</h1>")
        headerLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        headerLabel.setStyleSheet("font-size: 20px; font-weight: bold;")

        accessButton = QPushButton("Sign-in/Sign-out")
        accessButton.clicked.connect(self.showAccessWindow)

        adminButton = QPushButton("Admin Panel")
        adminButton.clicked.connect(self.showAdminLogin)  # Connect the button to the method

        quitButton = QPushButton("Exit")
        quitButton.clicked.connect(self.close)

        layout.addWidget(headerLabel)
        layout.addWidget(accessButton)
        layout.addWidget(adminButton)
        layout.addWidget(quitButton)

        accessButton.setStyleSheet(normalButtonStyling)
        adminButton.setStyleSheet(normalButtonStyling)
        quitButton.setStyleSheet(backButtonStyling)

        self.setLayout(layout)

    # this function is called when the user presses the sign-in/sign-out button, then it displayes teh accessWindow
    def showAccessWindow(self):
        self.accessWindow = AccessWindow()
        self.accessWindow.show()

    # this function is called when the user presses the admin panel button, then it displayes the admin login window
    def showAdminLogin(self):
        from admin import AdminLogin

        # Opens the admin login window if the user pressed the admin panel button
        self.adminLoginWindow = AdminLogin()
        self.adminLoginWindow.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = mainDashboard()
    window.show()
    app.exec()
