Below is a complete Python script that implements a PyQt application for managing an alarm clock database using SQLite. The application includes database creation, connection, models, a main window displaying the alarm table, and functionality for adding, editing, deleting, searching, and filtering alarms—all in a single file.
import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QFormLayout, QDialog,
    QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt
from datetime import datetime

# Database Connection
def create_connection():
    conn = sqlite3.connect('alarms.db')
    return conn

# Create Database and Tables
def init_db():
    conn = create_connection()
    cursor = conn.cursor()
    # Main table: Alarms
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alarms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT NOT NULL,
            days TEXT,  -- e.g., "Mon,Wed,Fri" or "Daily"
            description TEXT,
            is_active BOOLEAN NOT NULL DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

# Alarm Model
class Alarm:
    def __init__(self, id=None, time="", days="", description="", is_active=True):
        self.id = id
        self.time = time
        self.days = days
        self.description = description
        self.is_active = is_active

    @staticmethod
    def fetch_all():
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alarms")
        rows = cursor.fetchall()
        conn.close()
        return [Alarm(id=row[0], time=row[1], days=row[2], description=row[3], is_active=bool(row[4])) for row in rows]

    @staticmethod
    def search(search_text):
        conn = create_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM alarms WHERE time LIKE ? OR days LIKE ? OR description LIKE ?"
        cursor.execute(query, (f'%{search_text}%', f'%{search_text}%', f'%{search_text}%'))
        rows = cursor.fetchall()
        conn.close()
        return [Alarm(id=row[0], time=row[1], days=row[2], description=row[3], is_active=bool(row[4])) for row in rows]

    @staticmethod
    def filter_by_status(is_active):
        conn = create_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM alarms WHERE is_active = ?"
        cursor.execute(query, (is_active,))
        rows = cursor.fetchall()
        conn.close()
        return [Alarm(id=row[0], time=row[1], days=row[2], description=row[3], is_active=bool(row[4])) for row in rows]

    def save(self):
        conn = create_connection()
        cursor = conn.cursor()
        if self.id is None:
            # Insert new alarm
            cursor.execute('''
                INSERT INTO alarms (time, days, description, is_active)
                VALUES (?, ?, ?, ?)
            ''', (self.time, self.days, self.description, self.is_active))
            self.id = cursor.lastrowid
        else:
            # Update existing alarm
            cursor.execute('''
                UPDATE alarms
                SET time = ?, days = ?, description = ?, is_active = ?
                WHERE id = ?
            ''', (self.time, self.days, self.description, self.is_active, self.id))
        conn.commit()
        conn.close()

    def delete(self):
        if self.id is not None:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alarms WHERE id = ?", (self.id,))
            conn.commit()
            conn.close()

# Alarm Dialog for Add/Edit
class AlarmDialog(QDialog):
    def __init__(self, alarm=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Alarm")
        self.alarm = alarm or Alarm()
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()
        self.time_input = QLineEdit(self.alarm.time or "08:00")
        self.days_input = QLineEdit(self.alarm.days or "Daily")
        self.description_input = QLineEdit(self.alarm.description or "")
        self.is_active_combo = QComboBox()
        self.is_active_combo.addItems(["Active", "Inactive"])
        self.is_active_combo.setCurrentIndex(0 if self.alarm.is_active else 1)

        layout.addRow("Time (HH:MM):", self.time_input)
        layout.addRow("Days (e.g., Mon,Wed,Fri or Daily):", self.days_input)
        layout.addRow("Description:", self.description_input)
        layout.addRow("Status:", self.is_active_combo)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(buttons)
        self.setLayout(main_layout)

    def save(self):
        time = self.time_input.text()
        try:
            datetime.strptime(time, "%H:%M")  # Validate time format
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Time must be in HH:MM format.")
            return

        self.alarm.time = time
        self.alarm.days = self.days_input.text()
        self.alarm.description = self.description_input.text()
        self.alarm.is_active = self.is_active_combo.currentIndex() == 0
        self.alarm.save()
        self.accept()

# Main Application Window
class AlarmApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alarm Clock")
        self.setGeometry(100, 100, 600, 400)
        self.init_ui()
        init_db()  # Initialize database
        self.load_alarms()

    def init_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Time", "Days", "Description", "Active"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.table)

        # Controls
        controls_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Alarm")
        self.edit_btn = QPushButton("Edit Alarm")
        self.delete_btn = QPushButton("Delete Alarm")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Active", "Inactive"])

        self.add_btn.clicked.connect(self.add_alarm)
        self.edit_btn.clicked.connect(self.edit_alarm)
        self.delete_btn.clicked.connect(self.delete_alarm)
        self.search_input.textChanged.connect(self.search_alarms)
        self.filter_combo.currentIndexChanged.connect(self.filter_alarms)

        controls_layout.addWidget(self.add_btn)
        controls_layout.addWidget(self.edit_btn)
        controls_layout.addWidget(self.delete_btn)
        controls_layout.addWidget(self.search_input)
        controls_layout.addWidget(self.filter_combo)
        main_layout.addLayout(controls_layout)

    def load_alarms(self, alarms=None):
        if alarms is None:
            alarms = Alarm.fetch_all()
        self.table.setRowCount(0)
        for row, alarm in enumerate(alarms):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(alarm.id)))
            self.table.setItem(row, 1, QTableWidgetItem(alarm.time))
            self.table.setItem(row, 2, QTableWidgetItem(alarm.days))
            self.table.setItem(row, 3, QTableWidgetItem(alarm.description))
            self.table.setItem(row, 4, QTableWidgetItem("Yes" if alarm.is_active else "No"))

    def add_alarm(self):
        dialog = AlarmDialog(parent=self)
        if dialog.exec_():
            self.load_alarms()

    def edit_alarm(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Selection Error", "Please select an alarm to edit.")
            return
        row = self.table.currentRow()
        alarm_id = int(self.table.item(row, 0).text())
        alarms = Alarm.fetch_all()
        alarm = next((a for a in alarms if a.id == alarm_id), None)
        if alarm:
            dialog = AlarmDialog(alarm=alarm, parent=self)
            if dialog.exec_():
                self.load_alarms()

    def delete_alarm(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Selection Error", "Please select an alarm to delete.")
            return
        row = self.table.currentRow()
        alarm_id = int(self.table.item(row, 0).text())
        alarms = Alarm.fetch_all()
        alarm = next((a for a in alarms if a.id == alarm_id), None)
        if alarm:
            reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this alarm?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                alarm.delete()
                self.load_alarms()

    def search_alarms(self):
        search_text = self.search_input.text()
        if search_text:
            alarms = Alarm.search(search_text)
        else:
            alarms = Alarm.fetch_all()
        self.load_alarms(alarms)

    def filter_alarms(self):
        filter_index = self.filter_combo.currentIndex()
        if filter_index == 0:  # All
            self.load_alarms()
        elif filter_index == 1:  # Active
            self.load_alarms(Alarm.filter_by_status(True))
        elif filter_index == 2:  # Inactive
            self.load_alarms(Alarm.filter_by_status(False))

# Run Application
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AlarmApp()
    window.show()
    sys.exit(app.exec_())
Explanation of the Code
	1	Database Setup:
	◦	Connection: The create_connection function establishes a connection to an SQLite database named alarms.db.
	◦	Table Creation: The init_db function creates a table named alarms with columns: id (primary key), time (HH:MM format), days (e.g., “Mon,Wed,Fri” or “Daily”), description, and is_active (boolean).
	◦	Main Table: The alarms table is the primary table for this application, storing all alarm details.
	2	Alarm Model:
	◦	The Alarm class represents an alarm record with attributes matching the database columns.
	◦	Methods:
	▪	fetch_all: Retrieves all alarms from the database.
	▪	search: Searches alarms by time, days, or description using a LIKE query.
	▪	filter_by_status: Filters alarms by is_active status.
	▪	save: Inserts or updates an alarm in the database.
	▪	delete: Deletes an alarm by its ID.
	3	PyQt Application:
	◦	Main Window (AlarmApp):
	▪	Displays a QTableWidget showing all alarms with columns for ID, Time, Days, Description, and Active status.
	▪	Includes buttons for adding, editing, and deleting alarms.
	▪	Provides a search input for real-time searching and a combo box for filtering by status (All, Active, Inactive).
	◦	Alarm Dialog (AlarmDialog):
	▪	A modal dialog for adding or editing alarms.
	▪	Includes fields for time (validated as HH:MM), days, description, and active status.
	▪	Validates time input to ensure correct format.
	4	Functionality:
	◦	Add: Opens a dialog to create a new alarm, which is saved to the database and displayed in the table.
	◦	Edit: Opens a dialog to modify the selected alarm, updating the database upon saving.
	◦	Delete: Deletes the selected alarm after user confirmation.
	◦	Search: Filters the table in real-time based on text entered in the search input, matching time, days, or description.
	◦	Filter: Displays all alarms, only active alarms, or only inactive alarms based on the filter combo box selection.
	5	Single File:
	◦	All code (database connection, model, and UI) is contained in one file for simplicity, as requested.
	◦	The script uses PyQt5 for the GUI and SQLite for the database, with no external dependencies beyond the standard library and PyQt5.
How to Run
	1	Ensure you have Python installed (version 3.6 or higher).
	2	Install PyQt5: pip install PyQt5.
	3	Save the code in a file (e.g., alarm_clock.py).
	4	Run the script: python alarm_clock.py.
	5	The application will create alarms.db in the same directory and display the main window.
Usage
	•	Add Alarm: Click “Add Alarm” to open a dialog, enter details, and save.
	•	Edit Alarm: Select a row in the table, click “Edit Alarm,” modify details, and save.
	•	Delete Alarm: Select a row, click “Delete Alarm,” and confirm deletion.
	•	Search: Type in the search box to filter alarms by time, days, or description.
	•	Filter: Use the combo box to show all, active, or inactive alarms.
This implementation fulfills all requirements in a concise, functional manner, keeping everything in one file for ease of use. Let me know if you need further clarification or modifications!
