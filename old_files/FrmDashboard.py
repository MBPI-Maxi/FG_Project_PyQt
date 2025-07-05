# FILE: FrmDashboard.py

import sys
import datetime
import psycopg2
from psycopg2 import sql
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QTextEdit,
    QFormLayout,
    QMessageBox,
    QCheckBox,
    QGraphicsDropShadowEffect,
    QTabWidget,
)
from PyQt6.QtGui import QFont, QIcon, QPixmap, QValidator, QColor
from PyQt6.QtCore import (
    Qt,
    QSize,
    QPropertyAnimation,
    QEasingCurve,
    QEvent,
    QTimer,
    QDate,
)

try:
    import qtawesome as fa
except ImportError:
    print("Error: qtawesome is not installed. Please run 'pip install qtawesome'")
    sys.exit(1)

# --- CONSTANTS FOR MATERIAL MANAGEMENT (UPDATED TO MATCH IMAGE) ---
TBL_INCOMING = "tbl_incoming"
COL_SEQ = "t_seq"
COL_CTRLNUM = "t_ctrlnum"
COL_DATE = "t_date"
COL_MATCODE = "t_matcode"
COL_QTY = "t_qty"
COL_NOTE = "t_note"
COL_UID = "t_uid"
COL_DELETED = "t_deleted"
COL_CREATED_AT = "t_created_at"
COL_UPDATED_AT = "t_updated_at"


# --- HELPER FUNCTION FOR DATABASE SETUP (UPDATED TO MATCH IMAGE) ---
def create_table_if_not_exists(conn):
    """
    Creates the database table based on the provided schema image if it doesn't exist.
    Also sets up a trigger to automatically update the timestamp on modification.
    """
    create_table_query = sql.SQL(
        """
    CREATE TABLE IF NOT EXISTS {table} (
        {t_seq}         SERIAL PRIMARY KEY,
        {t_ctrlnum}     VARCHAR(7),
        {t_date}        DATE,
        {t_matcode}     VARCHAR(50),
        {t_qty}         NUMERIC(12, 6),
        {t_note}        VARCHAR(254),
        {t_uid}         VARCHAR(254),
        {t_deleted}     BOOLEAN NOT NULL DEFAULT FALSE,
        {t_created_at}  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        {t_updated_at}  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );
    """
    ).format(
        table=sql.Identifier(TBL_INCOMING),
        t_seq=sql.Identifier(COL_SEQ),
        t_ctrlnum=sql.Identifier(COL_CTRLNUM),
        t_date=sql.Identifier(COL_DATE),
        t_matcode=sql.Identifier(COL_MATCODE),
        t_qty=sql.Identifier(COL_QTY),
        t_note=sql.Identifier(COL_NOTE),
        t_uid=sql.Identifier(COL_UID),
        t_deleted=sql.Identifier(COL_DELETED),
        t_created_at=sql.Identifier(COL_CREATED_AT),
        t_updated_at=sql.Identifier(COL_UPDATED_AT),
    )

    trigger_function_query = sql.SQL(
        """
    CREATE OR REPLACE FUNCTION update_modified_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.{updated_at_col} = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """
    ).format(updated_at_col=sql.Identifier(COL_UPDATED_AT))

    drop_trigger_query = sql.SQL(
        "DROP TRIGGER IF EXISTS update_tbl_incoming_modtime ON {table};"
    ).format(table=sql.Identifier(TBL_INCOMING))
    create_trigger_query = sql.SQL(
        """
    CREATE TRIGGER update_tbl_incoming_modtime
    BEFORE UPDATE ON {table}
    FOR EACH ROW
    EXECUTE PROCEDURE update_modified_column();
    """
    ).format(table=sql.Identifier(TBL_INCOMING))

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
        raise e


# --- WIDGET CLASS FOR MATERIAL MANAGEMENT (UPDATED) ---
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
        self.current_record_seq = None
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
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
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
        self.search_input.setPlaceholderText("Search by Material Code or Control No...")
        self.search_input.setClearButtonEnabled(True)
        search_btn = QPushButton(fa.icon("fa5s.search", color="white"), " Search")
        search_btn.setObjectName("primary")
        clear_btn = QPushButton("Clear")
        self.chk_show_deleted = QCheckBox("Show Deleted Records")
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(search_btn)
        search_layout.addWidget(clear_btn)
        search_layout.addSpacing(20)
        search_layout.addWidget(self.chk_show_deleted)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Seq", "Control No", "Date", "Material Code", "Qty", "Notes"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        records_layout.addWidget(search_panel)
        records_layout.addWidget(self.table)
        entry_tab = QWidget()
        entry_layout = QVBoxLayout(entry_tab)
        entry_layout.setContentsMargins(0, 10, 0, 0)
        entry_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        form_frame = QFrame()
        form_frame.setObjectName("card")
        form_frame.setGraphicsEffect(self.create_shadow_effect())
        form_layout_wrapper = QVBoxLayout(form_frame)
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setHorizontalSpacing(15)
        form.setVerticalSpacing(15)
        self.txt_ctrlnum = QLineEdit()
        self.date_entry = QDateEdit(QDate.currentDate())
        self.date_entry.setCalendarPopup(True)
        self.txt_matcode = QLineEdit()
        self.txt_qty = QLineEdit()
        self.txt_qty.setValidator(PositiveFloatValidator())
        self.txt_note = QTextEdit()
        self.txt_note.setMinimumHeight(100)
        form.addRow("Control No:", self.txt_ctrlnum)
        form.addRow("Date:", self.date_entry)
        form.addRow("Material Code:", self.txt_matcode)
        form.addRow("Quantity:", self.txt_qty)
        form.addRow("Notes:", self.txt_note)
        button_layout = QHBoxLayout()
        self.btn_new = QPushButton(fa.icon("fa5s.plus", color="#212121"), " New")
        self.btn_save = QPushButton(fa.icon("fa5s.save", color="white"), " Save")
        self.btn_save.setObjectName("primary")
        self.btn_delete = QPushButton(
            fa.icon("fa5s.trash-alt", color="white"), " Delete"
        )
        self.btn_delete.setObjectName("danger")
        self.btn_delete.setEnabled(False)
        button_layout.addWidget(self.btn_new)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_delete)
        button_layout.addWidget(self.btn_save)
        form_layout_wrapper.addLayout(form)
        form_layout_wrapper.addSpacing(20)
        form_layout_wrapper.addLayout(button_layout)
        entry_layout.addWidget(form_frame)
        self.tabs.addTab(records_tab, fa.icon("fa5s.list-alt"), "Records")
        self.tabs.addTab(entry_tab, fa.icon("fa5s.edit"), "Entry Form")
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
        query = sql.SQL(
            "SELECT {f_seq}, {f_ctrl}, {f_date}, {f_mat}, {f_qty}, {f_note} FROM {tbl} WHERE ({f_del} = %s OR %s = TRUE)"
        ).format(
            f_seq=sql.Identifier(COL_SEQ),
            f_ctrl=sql.Identifier(COL_CTRLNUM),
            f_date=sql.Identifier(COL_DATE),
            f_mat=sql.Identifier(COL_MATCODE),
            f_qty=sql.Identifier(COL_QTY),
            f_note=sql.Identifier(COL_NOTE),
            tbl=sql.Identifier(TBL_INCOMING),
            f_del=sql.Identifier(COL_DELETED),
        )
        params = [False, show_deleted] if not show_deleted else [True, True]
        if search_term:
            query += sql.SQL(" AND ({f_mat} ILIKE %s OR {f_ctrl} ILIKE %s)").format(
                f_mat=sql.Identifier(COL_MATCODE), f_ctrl=sql.Identifier(COL_CTRLNUM)
            )
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        query += sql.SQL(" ORDER BY {f_seq} DESC").format(f_seq=sql.Identifier(COL_SEQ))
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                records = cursor.fetchall()
                self.table.setRowCount(0)
                for row_data in records:
                    row_pos = self.table.rowCount()
                    self.table.insertRow(row_pos)
                    for i, data in enumerate(row_data):
                        item_text = (
                            str(data.strftime("%Y-%m-%d"))
                            if isinstance(data, datetime.date)
                            else str(data)
                        )
                        self.table.setItem(row_pos, i, QTableWidgetItem(item_text))
                self.table.resizeColumnsToContents()
                self.table.horizontalHeader().setStretchLastSection(True)
        except psycopg2.Error as e:
            QMessageBox.critical(
                self, "Database Error", f"Failed to load records:\n{str(e)}"
            )

    def load_selected_record_for_edit(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return
        self.current_record_seq = int(self.table.item(selected_row, 0).text())
        self.txt_ctrlnum.setText(self.table.item(selected_row, 1).text())
        self.date_entry.setDate(
            QDate.fromString(self.table.item(selected_row, 2).text(), "yyyy-MM-dd")
        )
        self.txt_matcode.setText(self.table.item(selected_row, 3).text())
        self.txt_qty.setText(self.table.item(selected_row, 4).text())
        self.txt_note.setPlainText(self.table.item(selected_row, 5).text())
        self.tabs.setCurrentIndex(1)
        self.btn_save.setText(" Update")
        self.btn_delete.setEnabled(True)

    def save_record(self):
        if not all([self.txt_ctrlnum.text().strip(), self.txt_matcode.text().strip()]):
            QMessageBox.warning(
                self, "Validation Error", "Control No and Material Code are required."
            )
            return
        try:
            qty = float(self.txt_qty.text()) if self.txt_qty.text() else 0.0
        except ValueError:
            QMessageBox.warning(
                self, "Validation Error", "Quantity must be a valid number."
            )
            return
        data = {
            "t_ctrlnum": self.txt_ctrlnum.text().strip(),
            "t_date": self.date_entry.date().toPyDate(),
            "t_matcode": self.txt_matcode.text().strip(),
            "t_qty": qty,
            "t_note": self.txt_note.toPlainText().strip(),
            "t_uid": self.username,
            "t_seq": self.current_record_seq,
        }
        try:
            with self.conn.cursor() as cursor:
                if self.current_record_seq is None:
                    cols = sql.SQL(", ").join(
                        map(
                            sql.Identifier,
                            [
                                "t_ctrlnum",
                                "t_date",
                                "t_matcode",
                                "t_qty",
                                "t_note",
                                "t_uid",
                            ],
                        )
                    )
                    vals = sql.SQL(", ").join(sql.Placeholder() * 6)
                    query = sql.SQL(
                        "INSERT INTO {tbl} ({cols}) VALUES ({vals})"
                    ).format(tbl=sql.Identifier(TBL_INCOMING), cols=cols, vals=vals)
                    params = (
                        data["t_ctrlnum"],
                        data["t_date"],
                        data["t_matcode"],
                        data["t_qty"],
                        data["t_note"],
                        data["t_uid"],
                    )
                    action = "saved"
                else:
                    set_clause = sql.SQL(", ").join(
                        [
                            sql.SQL("{} = %s").format(sql.Identifier(k))
                            for k in [
                                "t_ctrlnum",
                                "t_date",
                                "t_matcode",
                                "t_qty",
                                "t_note",
                            ]
                        ]
                    )
                    query = sql.SQL(
                        "UPDATE {tbl} SET {set_clause} WHERE {id_col} = %s"
                    ).format(
                        tbl=sql.Identifier(TBL_INCOMING),
                        set_clause=set_clause,
                        id_col=sql.Identifier(COL_SEQ),
                    )
                    params = (
                        data["t_ctrlnum"],
                        data["t_date"],
                        data["t_matcode"],
                        data["t_qty"],
                        data["t_note"],
                        data["t_seq"],
                    )
                    action = "updated"
                cursor.execute(query, params)
                self.conn.commit()
                QMessageBox.information(
                    self, "Success", f"Record {action} successfully."
                )
                self.clear_form()
                self.load_records()
                self.tabs.setCurrentIndex(0)
        except psycopg2.Error as e:
            self.conn.rollback()
            QMessageBox.critical(
                self, "Database Error", f"Failed to save record:\n{str(e)}"
            )

    def delete_record(self):
        if self.current_record_seq is None:
            return
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this record?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = sql.SQL(
                    "UPDATE {tbl} SET {del_col} = TRUE WHERE {id_col} = %s"
                ).format(
                    tbl=sql.Identifier(TBL_INCOMING),
                    del_col=sql.Identifier(COL_DELETED),
                    id_col=sql.Identifier(COL_SEQ),
                )
                with self.conn.cursor() as cursor:
                    cursor.execute(query, (self.current_record_seq,))
                self.conn.commit()
                QMessageBox.information(self, "Success", "Record has been deleted.")
                self.clear_form()
                self.load_records()
                self.tabs.setCurrentIndex(0)
            except psycopg2.Error as e:
                self.conn.rollback()
                QMessageBox.critical(
                    self, "Database Error", f"Failed to delete record:\n{str(e)}"
                )

    def clear_search(self):
        self.search_input.clear()
        self.load_records()

    def clear_form(self):
        self.current_record_seq = None
        self.txt_ctrlnum.clear()
        self.date_entry.setDate(QDate.currentDate())
        self.txt_matcode.clear()
        self.txt_qty.clear()
        self.txt_note.clear()
        self.btn_save.setText(" Save")
        self.btn_delete.setEnabled(False)
        self.tabs.setCurrentIndex(1)
        self.txt_ctrlnum.setFocus()


# --- MAIN DASHBOARD CLASS ---
class FrmDashboard(QMainWindow):
    def __init__(self, username=None, connection=None, login_window=None):
        super().__init__()
        self.username = username
        # self.conn = connection
        self.login_window = login_window

        self.setWindowTitle("Application Dashboard")
        self.setGeometry(100, 100, 1300, 800)
        self.management_submenu_visible = False
        self.icon_maximize = fa.icon("fa5s.expand-arrows-alt", color="#ecf0f1")
        self.icon_restore = fa.icon("fa5s.compress-arrows-alt", color="#ecf0f1")
        self.icon_db_ok = fa.icon("fa5s.check-circle", color="green")
        self.icon_db_fail = fa.icon("fa5s.times-circle", color="red")
        self.init_ui()

    def init_ui(self):
        self.setWindowIcon(fa.icon("fa5s.cogs", color="gray"))
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        side_menu = self.create_side_menu()
        main_layout.addWidget(side_menu)
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        # self.dashboard_page = self.create_page("Dashboard", f"Welcome, {self.username}!")
        # self.material_form_page = SimpleIncomingForm(self.username, self.conn)
        self.users_page = self.create_page("User Management", "Manage users here.")
        self.logs_page = self.create_page("System Logs", "View system logs here.")
        # self.stacked_widget.addWidget(self.dashboard_page)
        # self.stacked_widget.addWidget(self.material_form_page)
        self.stacked_widget.addWidget(self.users_page)
        self.stacked_widget.addWidget(self.logs_page)
        self.setCentralWidget(main_widget)
        # self.setup_status_bar()
        self.apply_styles()
        self.update_maximize_button()

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"Ready | Logged in as: {self.username}")
        self.db_status_icon_label = QLabel()
        self.db_status_icon_label.setFixedSize(QSize(20, 20))
        self.db_status_text_label = QLabel()
        self.time_label = QLabel()
        self.status_bar.addPermanentWidget(self.db_status_icon_label)
        self.status_bar.addPermanentWidget(self.db_status_text_label)
        self.status_bar.addPermanentWidget(self.time_label)
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        self.update_time()
        self.db_check_timer = QTimer(self)
        # self.db_check_timer.timeout.connect(self.check_db_status)
        self.db_check_timer.start(5000)
        # self.check_db_status()

    def update_time(self):
        self.time_label.setText(
            f" | {datetime.datetime.now().strftime('%b %d, %Y  %I:%M:%S %p')} "
        )

    def check_db_status(self):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.db_status_icon_label.setPixmap(self.icon_db_ok.pixmap(QSize(16, 16)))
            self.db_status_text_label.setText("DB Connected")
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            self.db_status_icon_label.setPixmap(self.icon_db_fail.pixmap(QSize(16, 16)))
            self.db_status_text_label.setText("DB Disconnected")

    def apply_styles(self):
        self.setStyleSheet(
            """
            QMainWindow, QStackedWidget > QWidget { background-color: #ecf0f1; }
            QWidget#SideMenu { background-color: #2c3e50; color: #ecf0f1; width: 230px; }
            #SideMenu QLabel { color: #ecf0f1; }
            #SideMenu QPushButton { background-color: transparent; color: #ecf0f1; border: none; padding: 12px; text-align: left; font-family: "Segoe UI"; font-size: 14px; font-weight: bold; border-radius: 5px; }
            #SideMenu QPushButton:hover { background-color: #34495e; }
            #SideMenu QPushButton:checked { background-color: #1abc9c; }
            QFrame#Separator { background-color: #34495e; height: 1px; }
            QStatusBar { background-color: #f0f0f0; font-size: 12px; }
            QStatusBar, QStatusBar QLabel { color: #000000; padding: 0 2px; font-family: "Segoe UI"; }
            QLabel#PageTitle { color: #2c3e50; }
            QWidget { font-family: 'Segoe UI', sans-serif; font-size: 10pt; color: #212121; }
            QFrame#card { background-color: #ffffff; border-radius: 8px; border: 1px solid #e0e0e0; }
            QLineEdit, QComboBox, QDateEdit, QTextEdit { background-color: #ffffff; border: 1px solid #bdbdbd; border-radius: 4px; padding: 8px; font-size: 10pt; }
            QLineEdit:focus, QDateEdit:focus, QTextEdit:focus { border: 1px solid #42a5f5; }
            QPushButton { background-color: #e0e0e0; border: none; border-radius: 4px; padding: 8px 16px; font-weight: bold; }
            QPushButton:hover { background-color: #d5d5d5; }
            QPushButton#primary { background-color: #1976d2; color: #ffffff; }
            QPushButton#primary:hover { background-color: #1565c0; }
            QPushButton#danger { background-color: #d32f2f; color: #ffffff; }
            QPushButton#danger:hover { background-color: #c62828; }
            QTableWidget { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 4px; gridline-color: #e0e0e0; }
            QHeaderView::section { background-color: #f5f5f5; padding: 8px; border: none; border-bottom: 1px solid #e0e0e0; font-weight: bold; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #f0f0f0; }
            QTableWidget::item:selected { background-color: #bbdefb; }
            QTabWidget::pane { border: none; }
            QTabBar::tab { background: transparent; color: #757575; padding: 10px 20px; font-weight: bold; border-bottom: 2px solid transparent; }
            QTabBar::tab:selected { color: #1976d2; border-bottom: 2px solid #1976d2; }
            QFormLayout QLabel { font-weight: bold; }
        """
        )

    def create_side_menu(self):
        side_menu_widget = QWidget()
        side_menu_widget.setObjectName("SideMenu")
        side_menu_layout = QVBoxLayout(side_menu_widget)
        side_menu_layout.setContentsMargins(10, 20, 10, 20)
        side_menu_layout.setSpacing(15)
        side_menu_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        profile_frame = QWidget()
        profile_layout = QHBoxLayout(profile_frame)
        profile_layout.setContentsMargins(5, 0, 0, 0)
        profile_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        user_icon = QLabel()
        user_icon.setPixmap(
            fa.icon("fa5s.user-circle", color="#ecf0f1").pixmap(QSize(40, 40))
        )
        user_label = QLabel(
            f"<b>{self.username}</b><br><font color='#bdc3c7'>Administrator</font>"
        )
        user_label.setFont(QFont("Segoe UI", 10))
        profile_layout.addWidget(user_icon)
        profile_layout.addWidget(user_label)
        self.btn_dashboard = QPushButton("  Dashboard")
        self.btn_dashboard.setIcon(fa.icon("fa5s.tachometer-alt", color="#ecf0f1"))
        self.btn_dashboard.clicked.connect(
            lambda: self.stacked_widget.setCurrentIndex(0)
        )
        self.btn_management = QPushButton("  Management")
        self.btn_management.setIcon(fa.icon("fa5s.archive", color="#ecf0f1"))
        self.btn_management.clicked.connect(self.toggle_management_submenu)
        self.management_submenu_container = QWidget()
        submenu_layout = QVBoxLayout(self.management_submenu_container)
        submenu_layout.setContentsMargins(20, 0, 0, 0)
        submenu_layout.setSpacing(10)
        self.btn_materials = QPushButton("  Material Incoming")
        self.btn_materials.setIcon(fa.icon("fa5s.boxes", color="#ecf0f1"))
        self.btn_materials.clicked.connect(
            lambda: self.stacked_widget.setCurrentIndex(1)
        )
        self.btn_users = QPushButton("  User Management")
        self.btn_users.setIcon(fa.icon("fa5s.users", color="#ecf0f1"))
        self.btn_users.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.btn_logs = QPushButton("  View Logs")
        self.btn_logs.setIcon(fa.icon("fa5s.file-alt", color="#ecf0f1"))
        self.btn_logs.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        submenu_layout.addWidget(self.btn_materials)
        submenu_layout.addWidget(self.btn_users)
        submenu_layout.addWidget(self.btn_logs)
        self.management_submenu_container.setMaximumHeight(0)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("Separator")
        self.btn_maximize = QPushButton("  Maximize")
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        self.btn_logout = QPushButton("Logout")
        self.btn_logout.setIcon(fa.icon("fa5s.sign-out-alt", color="#ecf0f1"))
        self.btn_logout.clicked.connect(self.logout)
        side_menu_layout.addWidget(profile_frame)
        side_menu_layout.addWidget(separator)
        side_menu_layout.addWidget(self.btn_dashboard)
        side_menu_layout.addWidget(self.btn_management)
        side_menu_layout.addWidget(self.management_submenu_container)
        side_menu_layout.addStretch(1)
        side_menu_layout.addWidget(self.btn_maximize)
        side_menu_layout.addWidget(self.btn_logout)
        return side_menu_widget

    def toggle_maximize(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def update_maximize_button(self):
        if self.isMaximized():
            self.btn_maximize.setText("  Restore")
            self.btn_maximize.setIcon(self.icon_restore)
        else:
            self.btn_maximize.setText("  Maximize")
            self.btn_maximize.setIcon(self.icon_maximize)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            self.update_maximize_button()
        super(FrmDashboard, self).changeEvent(event)

    def toggle_management_submenu(self):
        target_height = self.management_submenu_container.sizeHint().height()
        self.animation = QPropertyAnimation(
            self.management_submenu_container, b"maximumHeight"
        )
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuart)
        start, end = (
            (target_height, 0)
            if self.management_submenu_visible
            else (0, target_height)
        )
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.management_submenu_visible = not self.management_submenu_visible
        self.animation.start()

    def create_page(self, title, message):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title_label.setObjectName("PageTitle")
        message_label = QLabel(message)
        message_label.setFont(QFont("Segoe UI", 14))
        message_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(message_label)
        layout.addStretch()
        return page

    def logout(self):
        self.close()
        # show the login ui again.
        self.login_window.show()

    def closeEvent(self, event):
        self.login_window.close()
        event.accept()


# --- MAIN EXECUTION BLOCK ---

if __name__ == "__main__":
    app = QApplication(sys.argv)

    class DummyLogin(QWidget):
        def show(self):
            print("Logout successful.")

        def close(self):
            print("Application exit.")
            QApplication.quit()

    DB_CONFIG = {
        "dbname": "dbinventory",
        "user": "postgres",
        "password": "mbpi",
        "host": "192.168.1.13",
        "port": "5432",
    }

    try:
        print("Connecting to the database...")
        connection = psycopg2.connect(**DB_CONFIG)
        print("Connection successful.")

        create_table_if_not_exists(connection)

        dashboard = FrmDashboard("admin_user", connection, DummyLogin())
        dashboard.show()
        sys.exit(app.exec())

    except psycopg2.Error as e:
        QMessageBox.critical(None, "Database Error", f"A database error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        QMessageBox.critical(
            None, "Application Error", f"An unexpected error occurred: {e}"
        )
        sys.exit(1)
