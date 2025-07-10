# THIS WILL BE A REUSABLE TABLE ACROSS ALL THE FORMS THAT WILL BE GENERATED

from PyQt6.QtWidgets import (
    QWidget, QSizePolicy, QVBoxLayout, QHBoxLayout,
    QTableWidget, QScrollArea, QPushButton, QFileDialog, QHeaderView,
    QTableWidgetItem, QMenu, QLabel, QComboBox, QInputDialog, QLineEdit
)

from PyQt6.QtCore import Qt, pyqtSignal

from typing import Union, Callable, Type, Literal
from sqlalchemy.orm import Session, DeclarativeMeta
from app.helpers import button_cursor_pointer
from app.StyledMessage import StyledMessageBox
from constants.Enums import TableHeader
import pandas as pd
import os

class TableWidget(QWidget):
    double_clicked = pyqtSignal(str)

    def __init__(
        self,
        session_factory: Callable[..., Session],
        db_model: Type[DeclarativeMeta] = None,
        view_type: Union[
            Literal[
                "endorsement-list", 
                "endorsement-create"
            ], 
            None
        ] = None,
        parent=None,
        items_per_page: int = 20, # New: items per page for pagination
    ):
        super().__init__(parent)
        self.export_btn = QPushButton("Export Excel")
        self.export_btn.setObjectName("endorsement-export-btn")

        self.valid_views_to_show_export_btn = [
            "endorsement-list",
        ]

        self.excluded_views_for_show_export_btn = [
            "endorsement-create"
        ]

        if view_type in self.excluded_views_for_show_export_btn:
            self.export_btn.hide()

        self.Session = session_factory
        self.db_model = db_model
        self.view_type = view_type
        self.items_per_page = items_per_page # Store items per page
        self.current_page = 1 # Initialize current page
        self.total_pages = 1 # Initialize total pages
        
        self.init_ui()
        self.load_data()
        self.apply_styles()

    def init_ui(self):
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.layout = QVBoxLayout(self)

        # CREATE THE ACTUAL TABLE HERE
        self.table = QTableWidget()
        self.table.setObjectName("endorsementTable")
        self.table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setMinimumHeight(700)

        # THIS IS FOR HAVING A RIGHT CLICK BUTTON THE ROWS
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # CONFIGURE HEADERS
        self.table.setColumnCount(8)
        # self.table.setHorizontalHeaderLabels()

        # IF ELSE STATEMENT HERE TO CHANGE THE COLUMN BASED ON CONDITION
        # if selfF.view_type and self.view_type == self.valid_views_to_show_export_btn[0]:

        if self.view_type and self.view_type.startswith("endorsement"):
            self.table.setHorizontalHeaderLabels(TableHeader.get_header("endorsement"))

        self.table.horizontalHeader().setStretchLastSection(True)

        # CREATING A CONTAINER WIDGET FOR PROPER RESIZING
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        container.setLayout(QVBoxLayout())
        container.layout().setContentsMargins(0, 0, 0, 0)
        container.layout().addWidget(self.table)

        # ADD SCROLL AREA
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container)

        self.layout.addWidget(scroll_area)

        # CONNECT SIGNALS
        self.table.doubleClicked.connect(self.on_row_double_click)

        # Pagination controls
        self.pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setObjectName("tablewidget-prev-btn")

        self.page_label = QLabel(f"Page {self.current_page} of {self.total_pages}")
        self.page_label.setObjectName("table-widget-page-label")
        
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setObjectName("tablewidget-next-btn")

        self.items_per_page_combo = QComboBox()
        self.items_per_page_combo.addItems(["10", "20", "50", "100"])
        self.items_per_page_combo.setCurrentText(str(self.items_per_page))
        self.items_per_page_combo.currentIndexChanged.connect(self.update_items_per_page)
        self.items_per_page_combo.setObjectName("table-widget-items-per-page-combo")

        self.items_per_page_label = QLabel("Items per page:")
        self.items_per_page_label.setObjectName("table-widget-items-per-page-label")

        self.pagination_layout.addWidget(self.items_per_page_label)
        self.pagination_layout.addWidget(self.items_per_page_combo)
        self.pagination_layout.addStretch()
        self.pagination_layout.addWidget(self.prev_btn)
        self.pagination_layout.addWidget(self.page_label)
        self.pagination_layout.addWidget(self.next_btn)

        self.layout.addLayout(self.pagination_layout)

        btn_container = QHBoxLayout()
        btn_container.addWidget(self.export_btn)
        btn_container.addStretch()
        self.layout.addLayout(btn_container)
        self.export_btn.clicked.connect(self.export_to_excel)

    def apply_styles(self):
        qss_path = os.path.join(os.path.dirname(__file__), "styles", "table.css")
        button_cursor_pointer(self.export_btn)
        button_cursor_pointer(self.prev_btn)
        button_cursor_pointer(self.next_btn)

        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # This is correct: The scrollbar will appear only if needed
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        try:
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Warning: Style file not found. Default styles will be used.")

        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # You correctly commented this out, which is essential for scrollbar to appear
        # self.table.horizontalHeader().setStretchLastSection(True)

        # Set column widths (adjust as needed)
        self.table.setColumnWidth(0, 100)  # Ref No
        self.table.setColumnWidth(1, 100)  # Date
        self.table.setColumnWidth(2, 100)  # Category
        self.table.setColumnWidth(3, 150)  # Product Code
        self.table.setColumnWidth(4, 150)  # Lot Number
        self.table.setColumnWidth(5, 80)   # Qty (kg)
        self.table.setColumnWidth(6, 80)   # Status
        # Don't forget the 8th column (index 7) from your header labels
        self.table.setColumnWidth(7, 120)  # Endorsed By - Give it an initial width

        # Add these lines to explicitly set resize mode for each column.
        # If you want them to cause a scrollbar when exceeding width,
        # use Interactive or Fixed.
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive) # And for the last column too

    def export_to_excel(self):
        """Export table data to Excel file."""
        try:
            # Get save file path
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save as Excel",
                "Endorsement_Summary",
                "Excel Files (*.xlsx)"
            )

            if not path:
                return

            # Create DataFrame from table data
            data = []

            for row in range(self.table.rowCount()):
                row_data = []

                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")

                data.append(row_data)

            headers = [
                self.table.horizontalHeaderItem(i).text()
                for i in range(self.table.columnCount())
            ]

            df = pd.DataFrame(data, columns=headers)

            # Export using pandas
            df.to_excel(path, index=False)
            StyledMessageBox.information(
                self,
                "Success",
                f"Exported to {path}"
            )

        except Exception as e:
            StyledMessageBox.critical(
                self,
                "Error",
                f"Export failed: {str(e)}"
            )

    # def load_data(self):
    #     """Load data from the database with pagination."""
    #     try:
    #         session = self.Session()
    #         endorsement_model = self.db_model
    #         # Get total count for pagination calculation
    #         total_items = session.query(endorsement_model).count()
    #         self.total_pages = (total_items + self.items_per_page - 1) // self.items_per_page

    #         # Calculate offset and limit for the current page
    #         offset = (self.current_page - 1) * self.items_per_page
    #         limit = self.items_per_page

    #         # ADD A JOIN CLAUSE HERE SO THAT DATA FROM THE TABLE ENDORSEMENT 1
    #         if endorsement_model.__tablename__ == "tbl_endorsement_t1":
    #             endorsement_t2 = self.supplement_model.get("endorsement_t2", None)
                
    #             if endorsement_t2 is not None:
    #                 # endorsements = session.query(
    #                 #     endorsement_model,
    #                 #     endorsement_t2
    #                 # ).join(
    #                 #     endorsement_t2,
    #                 #     endorsement_model.t_refno == endorsement_t2.t_refno
    #                 # ).order_by(
    #                 #     endorsement_model.t_date_endorsed.desc(), 
    #                 #     endorsement_model.t_refno.desc()
    #                 # ).offset(offset).limit(limit).all()

    #                 # for row, (t1_endorsement, t2_endorsement) in enumerate(endorsements):
    #                 #     # for each entry on the endorsement model the rows are being populated.
    #                 #     self._set_table_item(row, 0, t1_endorsement.t_refno)
    #                 #     self._set_table_item(row, 1, t1_endorsement.t_date_endorsed.strftime("%Y-%m-%d"))
    #                 #     self._set_table_item(row, 2, t1_endorsement.t_category.value)
    #                 #     self._set_table_item(row, 3, t1_endorsement.t_prodcode)
    #                 #     self._set_table_item(row, 4, t1_endorsement.t_lotnumberwhole)
    #                 #     self._set_table_item(row, 5, f"{t1_endorsement.t_qtykg:.2f}")
    #                 #     self._set_table_item(row, 6, t1_endorsement.t_status.value)
    #                 #     self._set_table_item(row, 7, t1_endorsement.t_endorsed_by)

    #                 endorsements = session.query(
    #                     endorsement_model,
    #                 ).order_by(
    #                     endorsement_model.t_date_endorsed.desc(), 
    #                     endorsement_model.t_refno.desc()
    #                 ).offset(offset).limit(limit).all()

    #                 self.table.setRowCount(len(endorsements))

    #                 for row, endorsement in enumerate(endorsements):
    #                     self._set_table_item(row, 0, endorsement.t_refno)
    #                     self._set_table_item(row, 1, endorsement.t_date_endorsed.strftime("%Y-%m-%d"))
    #                     self._set_table_item(row, 2, endorsement.t_category.value)
    #                     self._set_table_item(row, 3, endorsement.t_prodcode)
    #                     self._set_table_item(row, 4, endorsement.t_lotnumberwhole)
    #                     self._set_table_item(row, 5, f"{endorsement.t_qtykg:.2f}")
    #                     self._set_table_item(row, 6, endorsement.t_status.value)
    #                     self._set_table_item(row, 7, endorsement.t_endorsed_by)

    #                 self.table.verticalHeader().setDefaultSectionSize(24)
    #                 self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    #                 self.table.resizeColumnsToContents()

    #                 self.update_pagination_controls() # Update button states and label
    #             else:
    #                 raise KeyError("Supplement model 'endorsement_t2' is required but not provided")
    #     finally:
    #         session.close()

    def load_data(self):
        """Load data from the endorsement_combined view with pagination."""
        try:
            session = self.Session()
            model = self.db_model

            total_items = session.query(model).count()
            self.total_pages = (total_items + self.items_per_page - 1) // self.items_per_page

            offset = (self.current_page - 1) * self.items_per_page
            limit = self.items_per_page

            if model.__tablename__ == "endorsement_combined":
                endorsement_combined = session.query(model).offset(offset).limit(limit).all()

                self.table.setRowCount(len(endorsement_combined))

                for row_idx, endorsement in enumerate(endorsement_combined):
                    self._set_table_item(row_idx, 0, endorsement.t_refno)
                    self._set_table_item(row_idx, 0, endorsement.t_date_endorsed.strftime("%Y-%m-%d"))
                    self._set_table_item(row_idx, 2, endorsement.t_category)
                    self._set_table_item(row_idx, 3, endorsement.t_prodcode)
                    self._set_table_item(row_idx, 4, endorsement.t_lot_number)
                    self._set_table_item(row_idx, 5, f"{endorsement.t_total_quantity:.2f}")
                    self._set_table_item(row_idx, 6, endorsement.t_status)
                    self._set_table_item(row_idx, 7, endorsement.t_endorsed_by)

                self.table.verticalHeader().setDefaultSectionSize(24)
                self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
                self.table.resizeColumnsToContents()

                self.update_pagination_controls()
            else:

                print("Add an error statement here if this class is used that the ")
        finally:
            session.close()

    def _set_table_item(self, row: int, col: int, value: str):
        """Helper method to set table items."""
        item = QTableWidgetItem(str(value))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, col, item)

    def on_row_double_click(self, index):
        """Emit signal when row is double-clicked."""
        ref_no = self.table.item(index.row(), 0).text()
        self.double_clicked.emit(ref_no)

    def show_context_menu(self, pos):
        # Get the clicked row
        row = self.table.rowAt(pos.y())

        if row < 0:  # Clicked outside a row
            return

        # EXTRACT SPECIFIC VALUES FROM THE ROW
        # the number should match the index based on the table layout
        ref_no = self.table.item(row, 0).text() if self.table.item(row, 0) else "N/A"
        product_code = self.table.item(row, 3).text() if self.table.item(row, 3) else "N/A"

        # Create the menu
        menu = QMenu(self)

        # Add actions
        edit_action = menu.addAction("Edit Record")
        # delete_action = menu.addAction("Delete Record")
        # add_action = menu.addAction("Add New Record")

        # Connect actions to functions
        # TODO: Add a dialog box before they edit anything
        edit_action.triggered.connect(lambda: print(f"Edit action triggered - Row: {row}, Ref No: {ref_no}, Product Code: {product_code}"))

        # Show the menu at the cursor position
        menu.exec(self.table.viewport().mapToGlobal(pos))
    
    def show_edit_confirmation_message(self):
        warehouse_password, ok = QInputDialog.getText(
            self,
            "Warehouse Authentication",
            "Enter warehouse password to modify this entry:",
            QLineEdit.EchoMode.Password
        )

        # TODO: CONTINUE THIS CODE ON MONDAY
        # REFERENCE: https://chatgpt.com/c/686878e2-1b0c-8003-971b-f06228f30ec9
        if ok:
            if warehouse_password == "test":
                pass

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()

    def update_pagination_controls(self):
        self.page_label.setText(f"Page {self.current_page} of {self.total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)

    def update_items_per_page(self):
        self.items_per_page = int(self.items_per_page_combo.currentText())
        self.current_page = 1 # Reset to first page when items per page changes
        self.load_data()