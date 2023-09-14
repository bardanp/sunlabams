from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem, \
    QHeaderView, QSizePolicy, QHBoxLayout, QLineEdit
from styles import normalButtonStyling, backButtonStyling, textEditBoxStyling, suspendButtonStyling, \
    reactivateButtonStyling
from firebase_admin import firestore

db = firestore.client()


# Admin Login Window that is prompted when the admin button is clicked, after the admin id is entered,
# the admin can access the admin dashboard, where the user cna chose between the user management and access logs
# noinspection PyUnresolvedReferences
class AdminLogin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Login")
        self.setFixedSize(500, 300)
        loginLayout = QVBoxLayout()

        textLabel1 = QLabel("<h1>Please enter Admin ID:</h1>")
        textLabel1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.loginTextField = QTextEdit()
        self.loginTextField.setPlaceholderText("Enter Admin ID here")

        usersButton = QPushButton("Users")
        usersButton.clicked.connect(lambda: self.authenticateAndShowWindow(self.showUsersWindow))

        accessLogsButton = QPushButton("Access Logs")
        accessLogsButton.clicked.connect(lambda: self.authenticateAndShowWindow(self.showAccessLogsWindow))

        backButton = QPushButton("Back")
        backButton.clicked.connect(self.close)

        # using the same styling with the css styles for all windows and buttons
        self.loginTextField.setStyleSheet(textEditBoxStyling)
        usersButton.setStyleSheet(normalButtonStyling)
        accessLogsButton.setStyleSheet(normalButtonStyling)
        backButton.setStyleSheet(backButtonStyling)

        # Add widgets to the layout
        loginLayout.addWidget(textLabel1)
        loginLayout.addWidget(self.loginTextField)
        loginLayout.addWidget(usersButton)
        loginLayout.addWidget(accessLogsButton)
        loginLayout.addWidget(backButton)

        self.setLayout(loginLayout)

    # This function shows the users window, where the admin can see the list of users and
    # their status, allowign the admin to suspend or reactivate the user
    def showUsersWindow(self):
        self.usersWindow = AdminUsersWindow()
        self.usersWindow.show()

    # This funcin  shows the admin access logs window, where the admin can see the list of users
    # and when they entered and exited the sunlab
    def showAccessLogsWindow(self):
        self.accessLogsWindow = AdminAccessLogsWindow()
        self.accessLogsWindow.show()

    # this function gets caled after the admin id is entered, if the admin id is correct, the
    # admin dashboard is shown, and the next window is shown, after authenticating the admin id
    def authenticateAndShowWindow(self, next_window_func):
        """Authenticate the admin ID and if correct, show the next window"""
        if self.checkAdminCredentials():
            next_window_func()

    # ADMIN ID REF = 96115607

    # the function gets the text entered, turns it into a string, and checks if it matches any admin id
    def checkAdminCredentials(self):
        # Get the input ID from the text field and trim any leading and trailing whitespace
        inputID = self.loginTextField.toPlainText().strip()

        # search Firestore to find an admin user where the FirstName is 'admin' and the ID matches the 'id' field of
        # the admin
        adminInDB = db.collection(u'users').where(u'ID', u'==', inputID).where(u'FirstName', u'==', 'admin').stream()

        # Create an empty list to hold the data of all admins that match the query
        admin_data_list = []

        # Populate the admin_data_list with data from each admin document returned by the query
        for doc in adminInDB:
            admin_data = doc.to_dict()
            admin_data_list.append(admin_data)

        # Check if any admin data was found in the database
        if len(admin_data_list) > 0:
            # go through each admin's data to verify if they are an actual admin, by checking their FirstName == 'admin'
            for admin_data in admin_data_list:
                if admin_data.get('FirstName') == 'admin':
                    # If the admin is found, clear the text field and return True
                    return True
            # If loop completes, no valid admin was found, clear field and show invalid ID message
            self.loginTextField.clear()
            self.loginTextField.setPlaceholderText("Invalid Admin ID!")
            return False
        else:
            # No admin data found, clear field and show admin not found message
            self.loginTextField.clear()
            self.loginTextField.setPlaceholderText("Admin not found!")
            return False


# list of users and their status, displays the name, id, and suspended/active status of the user, imported from firebase
# Admin Users Management Window
# noinspection PyUnresolvedReferences
class AdminUsersWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Users Management")
        self.setFixedSize(1000, 700)
        layout = QVBoxLayout()

        # displays the Users in a table, with their name, id, and status, and a button to suspend or reactivate the user
        # Create a table to display users
        self.usersTable = QTableWidget()
        self.usersTable.setRowCount(0)
        self.usersTable.setColumnCount(5)  # FirstName, LastName, PSU ID, Status, Action
        self.usersTable.setHorizontalHeaderLabels(["FirstName", "LastName", "PSU ID", "Status", "Action"])
        self.usersTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.usersTable)

        self.setLayout(layout)
        self.loadUserstoTable()

    # populate the table with the users from the database with their FirstName, LastName, PSU ID, and Status
    def loadUserstoTable(self):
        # gets all the users in the database and stores it into a list
        self.usersTable.setRowCount(0)
        allUsersfromDB = db.collection(u'users').get()

        for user_doc in allUsersfromDB:
            user_data = user_doc.to_dict()
            if not user_data.get("FirstName") or not user_data.get("ID"):
                continue
            row_position = self.usersTable.rowCount()
            self.usersTable.insertRow(row_position)

            self.usersTable.setRowHeight(row_position, 40)

            self.usersTable.setItem(row_position, 0, QTableWidgetItem(user_data.get("FirstName")))
            self.usersTable.setItem(row_position, 1, QTableWidgetItem(user_data.get("LastName")))
            self.usersTable.setItem(row_position, 2, QTableWidgetItem(user_data.get("ID")))
            self.usersTable.setItem(row_position, 3, QTableWidgetItem(user_data.get("Status").capitalize()))

            # Create a button to suspend or reactivate the user based on their current status
            # if they are suspened, dispal the 'activate' buttons, if they are active, display the 'suspend' button
            if user_data.get("Status") == "active":
                action_button = QPushButton("Suspend")
                action_button.setStyleSheet(suspendButtonStyling)
            else:
                action_button = QPushButton("Reactivate")
                action_button.setStyleSheet(reactivateButtonStyling)

            # sets teh size policy of the button to expanding, so it will expand to take up available
            # space on all the sides
            action_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            # if the button is clicked, it will call the toggle_user_status function, and pass the user id
            # as a parameter and update firebae 'status' field to 'active' or 'suspended'
            action_button.clicked.connect(lambda _, user_id=user_data.get("ID"): self.toggleUserStatus(user_id))

            # adds a new column for the 'action' button, leting the admin suspend or reactiavate the user
            action_hbox = QHBoxLayout()
            action_hbox.setContentsMargins(0, 0, 0, 0)
            action_hbox.addWidget(action_button)
            action_hbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
            action_widget = QWidget()
            action_widget.setLayout(action_hbox)
            self.usersTable.setCellWidget(row_position, 4, action_widget)

    # this function toggles the user status, if the user is active, it will suspend them, if they are suspended,
    # it will reactivate them
    def toggleUserStatus(self, user_id):
        user_data = db.collection(u'users').document(user_id).get().to_dict()
        new_status = "active" if user_data.get("Status") != "active" else "suspended"
        db.collection(u'users').document(user_id).update({"Status": new_status})
        self.loadUserstoTable()  # Refresh the table

    # this function suspends the user, by setting their status to 'suspended' in the database
    def suspendUserAccess(self, user_id):
        """Suspend the specified user by setting their status to 'suspended' in the database"""
        db.collection(u'users').document(user_id).update({
            "Status": "suspended"
        })
        # Refresh the table after updating the status
        self.loadUserstoTable()

    # same as suspendUserAccess function, but it resets it back to actiavte instead of suspeded
    def reactivateUserAccess(self, user_id):
        """Reactivate the specified user by setting their status to 'active' in the database"""
        db.collection(u'users').document(user_id).update({
            "Status": "active"
        })
        # Refresh the table after updating the status
        self.loadUserstoTable()


# this is acess logs window, where the admin can see the list of users and when they entered and exited the sunlab
# with the funcaliotionality of master search, where the admin can search by date, PSU ID, first name, last name, etc.
class AdminAccessLogsWindow(QWidget):
    # noinspection PyUnresolvedReferences
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Access Logs")
        self.setFixedSize(1000, 700)
        layout = QVBoxLayout()

        # Master search text field and search button which fiters the data bsed on what is entered in the
        # master search text field
        searchLayout = QHBoxLayout()

        self.FilterTextField = QLineEdit()
        self.FilterTextField.setPlaceholderText("Search by date (%Y-%m-%d), PSU ID, first name, last name, etc.")
        searchLayout.addWidget(self.FilterTextField)

        # Search button
        self.searchButton = QPushButton("Search")
        self.searchButton.clicked.connect(self.load_access_logs)
        searchLayout.addWidget(self.searchButton)

        layout.addLayout(searchLayout)

        # Table to display access logs just like in the admin users pannel class. Displays the PSU ID, name, and
        # when they entered and exited the sunlab
        self.accessLogsTable = QTableWidget()
        self.accessLogsTable.setRowCount(0)
        self.accessLogsTable.setColumnCount(4)  # PSU ID, Name, Entered SunLab, Exited SunLab
        self.accessLogsTable.setHorizontalHeaderLabels(["PSU ID", "Name", "Entered SunLab", "Exited SunLab"])
        self.accessLogsTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.accessLogsTable)

        # no filter on first load, shows all the user logs in the database by default
        self.setLayout(layout)
        self.load_access_logs()

    # this function loads the access logs from the database, and displays them in the table, with the PSU ID, name,
    # and when they entered and exited the sunlab. this function alsp applies the master search filter, where the admin
    # can search by date, PSU ID, first name, last name, etc.
    def load_access_logs(self):
        self.accessLogsTable.setRowCount(0)
        # Convert to lowercase for case-insensitive search and remove leading and trailing whitespace
        searchInput = self.FilterTextField.text().strip().lower()

        # noinspection SpellCheckingInspection
        allLogsfromDB = db.collection(u'access_logs').get()

        for logInfo in allLogsfromDB:
            logData = logInfo.to_dict()

            # Convert the entered/exited timestamps to local time and strings
            entered_time = logData.get("entered").strftime('%Y-%m-%d %H:%M:%S') if logData.get("entered") else "N/A"
            exited_time = logData.get("exited").strftime('%Y-%m-%d %H:%M:%S') if logData.get("exited") else "N/A"

            # Apply master search filter, by checking if the search text is in any of the values in the log data
            # If the search text is not in any of the values, skip this log
            if searchInput:
                if not any(searchInput in str(value).lower() for value in [logData.get("id"), logData.get("name"),
                                                                           entered_time, exited_time]):
                    continue

            # Add data to the table if it passes the filter
            row_position = self.accessLogsTable.rowCount()
            self.accessLogsTable.insertRow(row_position)

            self.accessLogsTable.setItem(row_position, 0, QTableWidgetItem(logData.get("id")))
            self.accessLogsTable.setItem(row_position, 1, QTableWidgetItem(logData.get("name")))
            self.accessLogsTable.setItem(row_position, 2, QTableWidgetItem(entered_time))
            self.accessLogsTable.setItem(row_position, 3, QTableWidgetItem(exited_time))
