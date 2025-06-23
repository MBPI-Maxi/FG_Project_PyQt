#!/usr/bin/env python3
import sys
import psycopg2
import qtawesome as qta
from psycopg2 import sql
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLineEdit, QLabel, QComboBox,
    QDateEdit, QTextEdit, QFormLayout, QMessageBox, QCheckBox, QFrame,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QValidator, QColor

# --- Constants ---

# Database constants
TBL_INCOMING = "tbl_incoming"
COL_ID = "id"
COL_RECEIPT_NO = "receipt_no"
COL_RECEIPT_DATE = "receipt_date"
COL_MATERIAL_TYPE = "material_type"
COL_MATERIAL_NAME = "material_name"
COL_QUANTITY = "quantity"
COL_NOTES = "notes"
COL_ENCODED_BY = "encoded_by"
COL_IS_DELETED = "is_deleted"
COL_CREATED_AT = "created_at"
COL_UPDATED_AT = "updated_at"

# Material Design Stylesheet (remains the same)
MATERIAL_STYLESHEET = """
    /* Main Window */
    QWidget {
        background-color: #f5f5f5;
        color: #212121;
        font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', sans-serif;
        font-size: 10pt;
    }
    /* ... (rest of the stylesheet is unchanged) ... */
    QFrame#card {
        background-color: #ffffff;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    QLineEdit, QComboBox, QDateEdit, QTextEdit {
        background-color: #ffffff;
        border: 1px solid #bdbdbd;
        border-radius: 4px;
        padding: 8px;
        font-size: 10pt;
    }
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
        border: 1px solid #42a5f5; /* Material Blue */
    }
    QPushButton {
        background-color: #e0e0e0;
        color: #212121;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #d5d5d5; }
    QPushButton:pressed { background-color: #bdbdbd; }
    QPushButton#primary {
        background-color: #1976d2; /* Material Blue */
        color: #ffffff;
    }
    QPushButton#primary:hover { background-color: #1565c0; }
    QPushButton#danger {
        background-color: #d32f2f; /* Material Red */
        color: #ffffff;
    }
    QPushButton#danger:hover { background-color: #c62828; }
    QTableWidget {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        gridline-color: #e0e0e0;
    }
    QHeaderView::section {
        background-color: #f5f5f5;
        padding: 8px;
        border: none;
        border-bottom: 1px solid #e0e0e0;
        font-weight: bold;
    }
    QTableWidget::item { padding: 8px; border-bottom: 1px solid #f0f0f0; }
    QTableWidget::item:selected {
        background-color: #bbdefb; /* Light Blue */
        color: #212121;
    }
    QTabWidget::pane { border: none; }
    QTabBar::tab {
        background: transparent; color: #757575;
        padding: 10px 20px; font-weight: bold;
        border-bottom: 2px solid transparent;
    }
    QTabBar::tab:selected {
        color: #1976d2;
        border-bottom: 2px solid #1976d2;
    }
    QLabel { font-size: 10pt; }
    QFormLayout QLabel { font-weight: bold; }
    QCheckBox::indicator { width: 16px; height: 16px; }
"""


def create_table_if_not_exists(conn):
    """
    Checks for the existence of the main table and creates it if it's missing.
    Also sets up a trigger to automatically update the 'updated_at' column.
    """
    create_table_query = sql.SQL("""
    CREATE TABLE IF NOT EXISTS {table} (
        {id}            SERIAL PRIMARY KEY,
        {receipt_no}    VARCHAR(50) NOT NULL,
        {receipt_date}  DATE NOT NULL,
        {material_type} VARCHAR(50) NOT NULL,
        {material_name} VARCHAR(255) NOT NULL,
        {quantity}      NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
        {notes}         TEXT,
        {encoded_by}    VARCHAR(50),
        {is_deleted}    BOOLEAN NOT NULL DEFAULT FALSE,
        {created_at}    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        {updated_at}    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );
    """).format(
        table=sql.Identifier(TBL_INCOMING),
        id=sql.Identifier(COL_ID),
        receipt_no=sql.Identifier(COL_RECEIPT_NO),
        receipt_date=sql.Identifier(COL_RECEIPT_DATE),
        material_type=sql.Identifier(COL_MATERIAL_TYPE),
        material_name=sql.Identifier(COL_MATERIAL_NAME),
        quantity=sql.Identifier(COL_QUANTITY),
        notes=sql.Identifier(COL_NOTES),
        encoded_by=sql.Identifier(COL_ENCODED_BY),
        is_deleted=sql.Identifier(COL_IS_DELETED),
        created_at=sql.Identifier(COL_CREATED_AT),
        updated_at=sql.Identifier(COL_UPDATED_AT)
    )

    # This function and trigger automatically update the `updated_at` timestamp on any row update
    trigger_function_query = """
    CREATE OR REPLACE FUNCTION update_modified_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """

    # Drop existing trigger to ensure we can re-apply it safely
    drop_trigger_query = sql.SQL("DROP TRIGGER IF EXISTS update_tbl_incoming_modtime ON {table};").format(
        table=sql.Identifier(TBL_INCOMING)
    )

    create_trigger_query = sql.SQL("""
    CREATE TRIGGER update_tbl_incoming_modtime
    BEFORE UPDATE ON {table}
    FOR EACH ROW
    EXECUTE PROCEDURE update_modified_column();
    """).format(table=sql.Identifier(TBL_INCOMING))

    try:
        with conn.cursor() as cursor:
            print("Checking for database table...")
            cursor.execute(create_table_query)
            print(f"Table '{TBL_INCOMING}' is ready.")

            print("Setting up 'updated_at' trigger...")
            cursor.execute(trigger_function_query)
            cursor.execute(drop_trigger_query)
            cursor.execute(create_trigger_query)
            print("Trigger is ready.")

        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        # Re-raise the exception to be caught by the main block
        raise e


class PositiveFloatValidator(QValidator):
    def validate(self, input_string, pos):
        try:
            if input_string == "" or float(input_string) >= 0:
                return (QValidator.State.Acceptable, input_string, pos)
        except ValueError:
            pass
        return (QValidator.State.Invalid, input_string, pos)


class SimpleIncomingForm(QWidget):
    def __init__(self, username, connection):
        super().__init__()
        self.username = username
        self.conn = connection
        self.current_record_id = None

        self.setup_ui()
        self.load_records()

    def create_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 80))
        return shadow

    def setup_ui(self):
        self.setWindowTitle("Material Management")
        self.setGeometry(100, 100, 1200, 750)  # Increased size slightly for ID column

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # --- Records Tab ---
        records_tab = QWidget()
        records_layout = QVBoxLayout(records_tab)
        records_layout.setContentsMargins(0, 10, 0, 0)
        records_layout.setSpacing(15)

        search_panel = QFrame()
        search_panel.setObjectName("card")
        search_panel.setGraphicsEffect(self.create_shadow_effect())
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(15, 15, 15, 15)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search materials by name or receipt number...")
        self.search_input.setClearButtonEnabled(True)

        search_btn = QPushButton(qta.icon('fa5s.search', color='white'), " Search")
        search_btn.setObjectName("primary")
        clear_btn = QPushButton("Clear")
        self.chk_show_deleted = QCheckBox("Show Deleted Records")

        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(search_btn)
        search_layout.addWidget(clear_btn)
        search_layout.addSpacing(20)
        search_layout.addWidget(self.chk_show_deleted)

        self.table = QTableWidget()
        # Column count is 7 to include the hidden Material Type
        self.table.setColumnCount(7)
        # **MODIFIED**: "ID" is now in the header labels.
        self.table.setHorizontalHeaderLabels(["ID", "Receipt No", "Date", "Material", "Qty", "Notes", "Type"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        # **MODIFIED**: Only hide the 'Type' column, 'ID' is now visible.
        self.table.setColumnHidden(6, True)

        records_layout.addWidget(search_panel)
        records_layout.addWidget(self.table)

        # --- Entry Tab ---
        entry_tab = QWidget()
        entry_layout = QVBoxLayout(entry_tab)
        entry_layout.setContentsMargins(0, 10, 0, 0)
        entry_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        form_frame = QFrame()
        form_frame.setObjectName("card")
        form_frame.setGraphicsEffect(self.create_shadow_effect())
        form_layout = QVBoxLayout(form_frame)
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setHorizontalSpacing(15)
        form.setVerticalSpacing(15)

        self.txt_receipt = QLineEdit()
        self.date_entry = QDateEdit(QDate.currentDate())
        self.date_entry.setCalendarPopup(True)
        self.combo_type = QComboBox()
        self.combo_type.addItems(["", "Raw Material", "Non-Raw Material"])
        self.txt_material = QLineEdit()
        self.txt_qty = QLineEdit()
        self.txt_qty.setValidator(PositiveFloatValidator())
        self.txt_notes = QTextEdit()
        self.txt_notes.setMinimumHeight(100)

        form.addRow("Receipt No:", self.txt_receipt)
        form.addRow("Date:", self.date_entry)
        form.addRow("Material Type:", self.combo_type)
        form.addRow("Material Name:", self.txt_material)
        form.addRow("Quantity:", self.txt_qty)
        form.addRow("Notes:", self.txt_notes)

        button_layout = QHBoxLayout()
        self.btn_new = QPushButton(qta.icon('fa5s.plus', color='#212121'), " New")
        self.btn_save = QPushButton(qta.icon('fa5s.save', color='white'), " Save")
        self.btn_save.setObjectName("primary")
        self.btn_delete = QPushButton(qta.icon('fa5s.trash-alt', color='white'), " Delete")
        self.btn_delete.setObjectName("danger")
        self.btn_delete.setEnabled(False)

        button_layout.addWidget(self.btn_new)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_delete)
        button_layout.addWidget(self.btn_save)

        form_layout.addLayout(form)
        form_layout.addSpacing(20)
        form_layout.addLayout(button_layout)
        entry_layout.addWidget(form_frame)

        self.tabs.addTab(records_tab, qta.icon('fa5s.list-alt'), "Records")
        self.tabs.addTab(entry_tab, qta.icon('fa5s.edit'), "Entry Form")
        main_layout.addWidget(self.tabs)

        search_btn.clicked.connect(self.load_records)
        clear_btn.clicked.connect(self.clear_search)
        self.search_input.returnPressed.connect(self.load_records)
        self.chk_show_deleted.stateChanged.connect(self.load_records)
        self.table.doubleClicked.connect(self.load_selected_record_for_edit)
        self.btn_new.clicked.connect(self.clear_form)
        self.btn_save.clicked.connect(self.save_record)
        self.btn_delete.clicked.connect(self.delete_record)

    def load_records(self):
        search_term = self.search_input.text().strip()
        show_deleted = self.chk_show_deleted.isChecked()

        # Query now includes id first
        query = sql.SQL("""
            SELECT {id}, {receipt_no}, {receipt_date}, {material_name}, {quantity}, 
                   {notes}, {material_type}
            FROM {table}
            WHERE ({is_deleted} = %s OR %s = TRUE)
        """).format(
            id=sql.Identifier(COL_ID),
            receipt_no=sql.Identifier(COL_RECEIPT_NO),
            receipt_date=sql.Identifier(COL_RECEIPT_DATE),
            material_name=sql.Identifier(COL_MATERIAL_NAME),
            quantity=sql.Identifier(COL_QUANTITY),
            notes=sql.Identifier(COL_NOTES),
            material_type=sql.Identifier(COL_MATERIAL_TYPE),
            table=sql.Identifier(TBL_INCOMING),
            is_deleted=sql.Identifier(COL_IS_DELETED),
        )
        params = [False, show_deleted] if not show_deleted else [True, True]

        if search_term:
            query += sql.SQL(" AND ({material_name} ILIKE %s OR {receipt_no} ILIKE %s)").format(
                material_name=sql.Identifier(COL_MATERIAL_NAME),
                receipt_no=sql.Identifier(COL_RECEIPT_NO)
            )
            params.extend([f"%{search_term}%", f"%{search_term}%"])

        query += sql.SQL(" ORDER BY {id} DESC").format(id=sql.Identifier(COL_ID))

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                records = cursor.fetchall()

                self.table.setRowCount(0)
                for row_data in records:
                    row_pos = self.table.rowCount()
                    self.table.insertRow(row_pos)
                    # **MODIFIED**: Populate all 7 columns in the correct order
                    self.table.setItem(row_pos, 0, QTableWidgetItem(str(row_data[0])))  # ID
                    self.table.setItem(row_pos, 1, QTableWidgetItem(str(row_data[1])))  # Receipt No
                    self.table.setItem(row_pos, 2, QTableWidgetItem(row_data[2].strftime('%Y-%m-%d')))  # Date
                    self.table.setItem(row_pos, 3, QTableWidgetItem(str(row_data[3])))  # Material Name
                    self.table.setItem(row_pos, 4, QTableWidgetItem(str(row_data[4])))  # Qty
                    self.table.setItem(row_pos, 5, QTableWidgetItem(str(row_data[5])))  # Notes
                    self.table.setItem(row_pos, 6, QTableWidgetItem(str(row_data[6])))  # Material Type (hidden)

                self.table.resizeColumnsToContents()
                self.table.horizontalHeader().setStretchLastSection(True)

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load records:\n{str(e)}")

    def load_selected_record_for_edit(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return

        # **MODIFIED**: Retrieve data from table cells using correct column indices
        self.current_record_id = int(self.table.item(selected_row, 0).text())
        receipt_no = self.table.item(selected_row, 1).text()
        receipt_date_str = self.table.item(selected_row, 2).text()
        material_name = self.table.item(selected_row, 3).text()
        quantity = self.table.item(selected_row, 4).text()
        notes = self.table.item(selected_row, 5).text()
        material_type = self.table.item(selected_row, 6).text()  # Hidden column

        self.txt_receipt.setText(receipt_no)
        self.date_entry.setDate(QDate.fromString(receipt_date_str, 'yyyy-MM-dd'))
        self.txt_material.setText(material_name)
        self.txt_qty.setText(quantity)
        self.txt_notes.setPlainText(notes)

        index = self.combo_type.findText(material_type, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.combo_type.setCurrentIndex(index)
        else:
            self.combo_type.setCurrentIndex(0)

        self.tabs.setCurrentIndex(1)
        self.btn_save.setText(" Update")
        self.btn_delete.setEnabled(True)

    # The save_record, delete_record, clear_search, and clear_form methods remain unchanged...
    def save_record(self):
        """Save a new record or update an existing one."""
        if not all([self.txt_receipt.text().strip(), self.txt_material.text().strip(), self.combo_type.currentText()]):
            QMessageBox.warning(self, "Validation Error", "Receipt No, Material Name, and Material Type are required.")
            return

        try:
            qty = float(self.txt_qty.text()) if self.txt_qty.text() else 0.0
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Quantity must be a valid number.")
            return

        data = {
            'receipt_no': self.txt_receipt.text().strip(),
            'receipt_date': self.date_entry.date().toPyDate(),
            'material_type': self.combo_type.currentText(),
            'material_name': self.txt_material.text().strip(),
            'quantity': qty,
            'notes': self.txt_notes.toPlainText().strip(),
            'encoded_by': self.username,
            'id': self.current_record_id
        }

        try:
            with self.conn.cursor() as cursor:
                if self.current_record_id is None:
                    query = sql.SQL("""
                        INSERT INTO {table} ({f_receipt_no}, {f_receipt_date}, {f_material_type},
                                           {f_material_name}, {f_quantity}, {f_notes}, {f_encoded_by})
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """).format(table=sql.Identifier(TBL_INCOMING), **{f'f_{k}': sql.Identifier(k) for k in data})
                    params = (data['receipt_no'], data['receipt_date'], data['material_type'],
                              data['material_name'], data['quantity'], data['notes'], data['encoded_by'])
                    action = "saved"
                else:
                    query = sql.SQL("""
                        UPDATE {table} SET
                            {f_receipt_no} = %s, {f_receipt_date} = %s, {f_material_type} = %s,
                            {f_material_name} = %s, {f_quantity} = %s, {f_notes} = %s
                        WHERE {f_id} = %s
                    """).format(table=sql.Identifier(TBL_INCOMING), **{f'f_{k}': sql.Identifier(k) for k in data})
                    params = (data['receipt_no'], data['receipt_date'], data['material_type'],
                              data['material_name'], data['quantity'], data['notes'], data['id'])
                    action = "updated"

                cursor.execute(query, params)
                self.conn.commit()
                QMessageBox.information(self, "Success", f"Record {action} successfully.")
                self.clear_form()
                self.load_records()
                self.tabs.setCurrentIndex(0)

        except psycopg2.Error as e:
            self.conn.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to save record:\n{str(e)}")

    def delete_record(self):
        if self.current_record_id is None: return
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            "Are you sure you want to delete this record?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = sql.SQL("UPDATE {table} SET {is_deleted} = TRUE WHERE {id} = %s").format(
                    table=sql.Identifier(TBL_INCOMING), is_deleted=sql.Identifier(COL_IS_DELETED),
                    id=sql.Identifier(COL_ID)
                )
                with self.conn.cursor() as cursor:
                    cursor.execute(query, (self.current_record_id,))
                self.conn.commit()
                QMessageBox.information(self, "Success", "Record has been deleted.")
                self.clear_form()
                self.load_records()
                self.tabs.setCurrentIndex(0)
            except psycopg2.Error as e:
                self.conn.rollback()
                QMessageBox.critical(self, "Database Error", f"Failed to delete record:\n{str(e)}")

    def clear_search(self):
        self.search_input.clear()
        self.load_records()

    def clear_form(self):
        self.current_record_id = None
        self.txt_receipt.clear()
        self.date_entry.setDate(QDate.currentDate())
        self.combo_type.setCurrentIndex(0)
        self.txt_material.clear()
        self.txt_qty.clear()
        self.txt_notes.clear()
        self.btn_save.setText(" Save")
        self.btn_delete.setEnabled(False)
        self.tabs.setCurrentIndex(1)
        self.txt_receipt.setFocus()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(MATERIAL_STYLESHEET)

    DB_CONFIG = {
        "dbname": "dbinventory", "user": "postgres", "password": "mbpi",
        "host": "192.168.1.13", "port": "5432"
    }

    try:
        print("Connecting to the database...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connection successful.")

        # **NEW**: Initialize the database table before starting the UI
        create_table_if_not_exists(conn)

        username = "admin_user"
        window = SimpleIncomingForm(username, conn)
        window.show()
        sys.exit(app.exec())

    except psycopg2.Error as e:
        QMessageBox.critical(None, "Database Error",
                             f"A database error occurred.\n"
                             f"Please check your connection or table setup.\n\n"
                             f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        QMessageBox.critical(None, "Application Error", f"An unexpected error occurred:\n{e}")
        sys.exit(1)