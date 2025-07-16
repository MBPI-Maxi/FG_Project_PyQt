from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QLabel,
    QPushButton,
    QHBoxLayout
)

from PyQt6.QtCore import Qt
from app.helpers import load_styles

import os

class HowToUseView(QWidget):
    """Interactive guide for using the endorsement system"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Content container
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Endorsement System Guide")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Sections
        self.add_section(
            layout,
            "Creating New Endorsements",
            "1. Fill all required fields\n"
            "2. Use proper lot number format (e.g., 1234AB or 1234AB-5678CD)\n"
            "3. Check 'Has excess' for partial quantities\n"
            "4. Click 'Save Endorsement' to submit"
        )

        self.add_section(
            layout,
            "Viewing Existing Records",
            "• Use filters to find specific endorsements\n"
            "• Double-click any record to view details\n"
            "• Sort columns by clicking headers"
        )

        self.add_section(
            layout,
            "Common Validation Rules",
            "• Quantity must match whole lot multiples unless 'Has excess' is checked\n"
            "• Lot numbers must follow the pattern: 4 digits + 2 letters\n"
            "• Reference numbers are auto-generated"
        )

        self.add_video_section(layout)
        self.add_contact_section(layout)

        scroll_area.setWidget(content)
        main_layout.addWidget(scroll_area)

    def add_section(self, layout, title, content):
        """Adds a titled content section"""
        section_title = QLabel(title)
        section_title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("margin-left: 10px;")
        
        layout.addWidget(section_title)
        layout.addWidget(content_label)

    def add_video_section(self, layout):
        """Adds video tutorial placeholder"""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        
        title = QLabel("Video Tutorials")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        
        video_links = [
            ("Basic Endorsement", "https://example.com/video1"),
            ("Troubleshooting", "https://example.com/video2"),
            ("Advanced Features", "https://example.com/video3")
        ]
        
        for text, url in video_links:
            btn = QPushButton(f"▶ {text}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("text-align: left; color: #0066cc;")
            btn.clicked.connect(lambda _, u=url: self.open_url(u))
            section_layout.addWidget(btn)
        
        layout.addWidget(title)
        layout.addWidget(section)

    def add_contact_section(self, layout):
        """Adds support contact information"""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        
        title = QLabel("Need Help?")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        
        contacts = [
            ("IT Support:", "support@masterbatch.com", "mailto:support@example.com"),
            ("QC Department:", "qc@masterbatch.com", "mailto:qc@example.com"),
            ("Urgent Issues:", "Ext. 1234", "")
        ]
        
        for label, text, link in contacts:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 0, 0, 0)
            
            lbl = QLabel(label)
            lbl.setFixedWidth(100)
            
            if link:
                btn = QPushButton(text)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet("text-align: left; color: #0066cc; border: none;")
                btn.clicked.connect(lambda _, u=link: self.open_url(u))
                row_layout.addWidget(lbl)
                row_layout.addWidget(btn)
            else:
                txt = QLabel(text)
                row_layout.addWidget(lbl)
                row_layout.addWidget(txt)
            
            section_layout.addWidget(row)
        
        layout.addWidget(title)
        layout.addWidget(section)

    def open_url(self, url):
        """Handles opening external links"""
        import webbrowser
        webbrowser.open(url)

    def apply_styles(self):
        current_dir = os.path.dirname(__file__)
        qss_path = os.path.join(current_dir, "..", "styles", "how_to_use_view.css")
        qss_path = os.path.abspath(qss_path)
        
        # qss_path = os.path.join(os.path.dirname(__file__), "styles", "how_to_use_view.css")
        load_styles(qss_path, self)