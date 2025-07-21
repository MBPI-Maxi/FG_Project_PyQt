from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QStackedWidget,
    QWidget
)

from models import (
    EndorsementModel,
    EndorsementModelT2,
    EndorsementCombinedView,
    EndorsementLotExcessModel,
    User
)

from app.helpers import load_styles, button_cursor_pointer
from app.views.endorsement._EndorsementCreateView import EndorsementCreateView
from app.views.endorsement._EndorsementListView import EndorsementListView
from app.views.endorsement._HowToUseView import HowToUseView
from app.views.validatorSchema import EndorsementFormSchema

from typing import Callable
from sqlalchemy.orm import Session
from models import EndorsementModel

import os

class EndorsementMainView(QWidget):
    def __init__(
        self, 
        session_factory: Callable[..., Session], 
        parent=None
    ):
        super().__init__(parent)
        self.Session = session_factory
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        self.layout = QVBoxLayout()

        # ----------------- Navigation buttons ---------------------
        nav_layout = QHBoxLayout()
        self.create_btn = QPushButton("Create New")
        self.list_btn = QPushButton("View List")
        self.how_to_use_btn = QPushButton("How To Use")
        
        self.create_btn.setObjectName("endorsement-create-btn")
        self.list_btn.setObjectName("endorsement-list-btn")
        self.how_to_use_btn.setObjectName("endorsement-how-to-use-btn")
        
        nav_layout.addWidget(self.create_btn)
        nav_layout.addWidget(self.list_btn)
        nav_layout.addWidget(self.how_to_use_btn)
        nav_layout.addStretch()
        
        # ---------------- Stacked widget for views ---------------------
        self.stacked_widget = QStackedWidget()
        
        # --------------- Create views -----------------------
        self.create_view = EndorsementCreateView(
            session_factory=self.Session,
            endorsement_t1=EndorsementModel,
            endorsement_t2=EndorsementModelT2,
            endorsement_combined_view=EndorsementCombinedView,
            endorsement_lot_excess=EndorsementLotExcessModel,
            endorsement_form_schema=EndorsementFormSchema,
            user_model=User           
        )
        self.list_view = EndorsementListView(
            session_factory=self.Session,
            endorsement_combined_view=EndorsementCombinedView
        )
        self.how_to_use_view = HowToUseView()
        
        # ---------------- Add to stack --------------------
        self.stacked_widget.addWidget(self.create_view)
        self.stacked_widget.addWidget(self.list_view)
        self.stacked_widget.addWidget(self.how_to_use_view)

        # --------------------- Connect signals -----------------------
        self.create_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.create_view))
        self.list_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.list_view))
        self.how_to_use_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.how_to_use_view))
        
        # ----------------------- When a record is selected in list view for editing -------------------------------
        # self.list_view.table.double_clicked.connect(self.show_update_view)
        
        self.layout.addLayout(nav_layout)
        self.layout.addWidget(self.stacked_widget)
        self.setLayout(self.layout)
    
    def apply_styles(self):
        # qss_path = os.path.join(os.path.dirname(__file__), "styles", "crud_btn.css")
        current_dir = os.path.dirname(__file__)
        qss_path = os.path.join(current_dir, "..", "styles", "crud_btn.css")
        qss_path = os.path.abspath(qss_path)

        button_cursor_pointer(self.create_btn)
        button_cursor_pointer(self.list_btn)
        button_cursor_pointer(self.how_to_use_btn)
        
        load_styles(qss_path, self)

    def show_update_view(self, ref_no):
        """Load data for editing and switch to update view"""
        try:
            session = self.Session()
            record = session.query(EndorsementModel).filter_by(t_refno=ref_no).first()

            if record:
                # Populate the update form with record data
                self.update_view.form.load_data(record)
                self.stacked_widget.setCurrentWidget(self.update_view)
        finally:
            session.close()
