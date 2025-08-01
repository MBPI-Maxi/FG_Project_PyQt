from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QPushButton,
    QLineEdit,
)

from PyQt6.QtCore import QDate

from app.helpers import load_styles, button_cursor_pointer
from app.widgets import ModifiedComboBox, ModifiedDateEdit, TableWidget
from constants.Enums import CategoryEnum, StatusEnum
from typing import Callable, Type, Union
from sqlalchemy.orm import Session, DeclarativeMeta

import os

class EndorsementListView(QWidget):
    """View with filters and table"""
    def __init__(
        self, 
        session_factory: Callable[..., Session],
        endorsement: Type[DeclarativeMeta],
        endorsement_t2: Type[DeclarativeMeta],
        endorsemnt_excess: Type[DeclarativeMeta],
        parent=None
    ):
        super().__init__(parent)
        self.Session = session_factory
        self.table_widget = TableWidget
        self.endorsement = endorsement
        self.endorsement_t2 = endorsement_t2
        self.endorsement_excess = endorsemnt_excess
        self.setup_ui()
        self.apply_styles()

    @staticmethod
    def create_filter_group(
        label: Type[QLabel], 
        widget: Union[QLineEdit, ModifiedComboBox]
    ):
        group = QWidget()
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(label)
        layout.addWidget(widget)
            
        return group

    @staticmethod
    def set_table_policy(table: Type[TableWidget]) -> None:
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        top_filter_layout, bottom_filter_layout = self.create_filter_layout()
        view_btn_layout = self.create_view_other_table_layout()
        self.table = self.show_table()

        # ------------- Add all to main layout ----------------
        layout.addLayout(top_filter_layout)
        layout.addLayout(bottom_filter_layout)
        layout.addLayout(view_btn_layout)
        layout.addWidget(self.table)
        layout.setStretch(2, 1)

        self.create_category_menu()
        self.create_status_menu()
        self.setLayout(layout)

        # ---------------- connect the button to filter function ---------------------
        self.search_button.clicked.connect(self.filter_function)
        self.list_reset_btn.clicked.connect(self.list_reset_callback)
        
        # Connect returnPressed signals for quick filtering
        self.ref_no_input.returnPressed.connect(self.filter_function)
        self.prod_code_input.returnPressed.connect(self.filter_function)

    def apply_styles(self):
        current_dir = os.path.dirname(__file__)
        qss_path = os.path.join(current_dir, "..", "styles", "endorsement_list.css")
        qss_path = os.path.abspath(qss_path)
        button_cursor_pointer(self.list_reset_btn)
        button_cursor_pointer(self.search_button)
        button_cursor_pointer(self.excess_sheet_btn)
        button_cursor_pointer(self.breakdown_lot_sheet)

        load_styles(qss_path, self)
    
    def show_table(self):
        table = self.table_widget(
            session_factory=self.Session,
            db_model=self.endorsement,
            view_type="endorsement-list"
        )
       
        self.set_table_policy(table=table)
        table.load_data()
        
        return table

    def excess_view_table(self):
        # -------- FOR THIS SAME HEADERS SHOULD BE APPLY --------
        table = self.table_widget(
            session_factory=self.Session,
            db_model=self.endorsement_excess,
            view_type="endorsement-list"
        )

        self.set_table_policy(table=table)
        table.load_data()

        return table

    def create_category_menu(self):
        for category in CategoryEnum:
            self.category_filter.addItem(category.value, category)
        
        # ------------------ add a ALL filter in the category enum ----------------
        self.category_filter.addItem("ALL")
        self.category_filter.setCurrentText("ALL")

    def create_status_menu(self):
        for status in StatusEnum:
            self.status_filter.addItem(status.value, status)

        self.status_filter.addItem("ALL")
        self.status_filter.setCurrentText("ALL")

    def create_filter_layout(self):
        create_filter_group = self.create_filter_group
        
        # ------------- FILTERS ----------------
        self.category_filter = ModifiedComboBox()
        self.status_filter = ModifiedComboBox()
        self.prod_code_input = QLineEdit()
        self.ref_no_input = QLineEdit()

        self.prod_code_input.setPlaceholderText("Filter by production code")
        self.ref_no_input.setPlaceholderText("Filter by reference number")

        # ------------ RESET BTN ----------------
        self.list_reset_btn = QPushButton("Reset")
        self.list_reset_btn.setObjectName("endorsementList-reset-btn")

        # --------------- LABELS FOR THE FILTERS ---------------------
        category_label = QLabel("Category:")
        status_label = QLabel("Status:")
        prod_code_label = QLabel("Prod Code:")
        ref_no_label = QLabel("Ref No:")
        from_label = QLabel("From:")
        to_label = QLabel("To:")

        # --------------- DATES ---------------------
        self.date_from = ModifiedDateEdit(calendarPopup=True)
        self.date_to = ModifiedDateEdit(calendarPopup=True)
        self.date_to.setDate(QDate.currentDate())

        # --------------- QPushButton -------------------
        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("endorsementList-search-btn")

        # --- Top row filter layout (1) ---
        top_filter_layout = QHBoxLayout()
        top_filter_layout.setContentsMargins(0, 0, 0, 0)
        top_filter_layout.setSpacing(6)

        # --- Bottom row filter layout (2) ---
        bottom_filter_layout = QHBoxLayout()
        bottom_filter_layout.setContentsMargins(0, 0, 0, 0)
        bottom_filter_layout.setSpacing(6)
        
        # --------------- SIZE POLICY --------------------
        category_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        status_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        prod_code_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        ref_no_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        from_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        to_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # --- Top row add widget (1) ---
        top_filter_layout.addWidget(create_filter_group(category_label, self.category_filter), stretch=1)
        top_filter_layout.addWidget(create_filter_group(status_label, self.status_filter), stretch=1)
        top_filter_layout.addWidget(create_filter_group(prod_code_label, self.prod_code_input), stretch=1)
        top_filter_layout.addWidget(create_filter_group(ref_no_label, self.ref_no_input), stretch=1)

        # --- Bottom row filter layout (2) ---
        bottom_filter_layout.addWidget(from_label)
        bottom_filter_layout.addWidget(self.date_from)
        bottom_filter_layout.addWidget(to_label)
        bottom_filter_layout.addWidget(self.date_to)
        bottom_filter_layout.addStretch() # push the search button to the right
        bottom_filter_layout.addWidget(self.list_reset_btn)
        bottom_filter_layout.addWidget(self.search_button)

        return (
            top_filter_layout, 
            bottom_filter_layout
        )
    
    def create_view_other_table_layout(self):
        view_layout = QHBoxLayout()
        view_layout.setContentsMargins(0, 0, 0, 0)
        view_layout.setSpacing(6)

        # -------------- BUTTONS FOR THE LAYOUT -----------------
        self.excess_sheet_btn = QPushButton("Excess Sheet View")
        self.excess_sheet_btn.setObjectName("endorsementList-excess-view-btn")

        self.breakdown_lot_sheet = QPushButton("Lot Breakdown View")
        self.breakdown_lot_sheet.setObjectName("endorsementList-breakdown-view-btn")

        view_layout.addWidget(self.excess_sheet_btn)
        view_layout.addWidget(self.breakdown_lot_sheet)

        return view_layout

    def filter_function(self):
        session = self.Session()

        try:
            ref_no_filter = self.ref_no_input.text().strip()
            prod_code_filter = self.prod_code_input.text().strip()
            status_code_filter = self.status_filter.currentText().strip().upper()
            category_filter = self.category_filter.currentText().strip().upper()

            query = session.query(self.endorsement)
            
            # ---------------- FILTER LOGIC FOR REFERENCE NUMBER -----------------
            if ref_no_filter:
                query = query.filter(self.endorsement.t_refno.ilike(f"%{ref_no_filter}%"))
            
            # --------------- FILTER LOGIC FOR PRODUCTION CODE -------------------
            if prod_code_filter:
                query = query.filter(self.endorsement.t_prodcode.ilike(f"%{prod_code_filter}%"))

            # -------------- FILTER LOGIC FOR THE STATUS ------------------------
            if status_code_filter != "ALL":
                query = query.filter(
                    self.endorsement.t_status == status_code_filter
                )
            
            if status_code_filter == "ALL":
                query = query.filter(
                    self.endorsement.t_status.in_([StatusEnum.PASSED.value, StatusEnum.FAILED.value])
                )

            # -------------------  FILTER LOGIC FOR THE CATEGORY ----------------------
            if category_filter != "ALL":
                selected_category = self.category_filter.currentData()

                if selected_category:  # Ensure we have valid category data
                    query = query.filter(self.endorsement.t_category == selected_category.value)

            if category_filter == "ALL":
                query = query.filter(
                    self.endorsement.t_category.in_([CategoryEnum.MB.value, CategoryEnum.DC.value])
                )

            # --------------------  FILTER LOGIC FOR THE DATES -----------------------
            if self.date_from.date() <= self.date_to.date():
                query = query.filter(
                    self.endorsement.t_date_endorsed >= self.date_from.date().toPyDate(),
                    self.endorsement.t_date_endorsed <= self.date_to.date().toPyDate()
                )
            
            # UPDATES THE TABLE BY CALLING THE .update_table_with_results in the TableWidget class
            results = query.order_by(self.endorsement.t_date_endorsed.desc()).all()
            self.table.update_table_with_results(results, apply_pagination=True)
        finally:
            session.close()

    def list_reset_callback(self):
        filter_objects = (
            self.prod_code_input,
            self.ref_no_input
        )
        
        for input_widget in filter_objects:
            if isinstance(input_widget, QLineEdit):
                input_widget.clear()
        
        self.table.reload_table()