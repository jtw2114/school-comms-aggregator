"""Light professional theme with Tiffany blue + navy accents."""

COLORS = {
    # Backgrounds
    "background": "#f5f9fa",
    "surface": "#ffffff",
    "surface_hover": "#e8f4f6",

    # Borders
    "border": "#c8dfe3",
    "border_light": "#e0eef0",

    # Text
    "text_primary": "#1a2a3a",
    "text_secondary": "#5a7a8a",
    "text_muted": "#8ca8b4",

    # Accent (Tiffany blue)
    "accent": "#0abab5",
    "accent_hover": "#08a5a0",
    "accent_light": "rgba(10,186,181,0.1)",

    # Navy
    "navy": "#1a3a5c",
    "navy_light": "#2a5a7c",

    # Source badges
    "gmail_badge": "#4285f4",
    "brightwheel_badge": "#ff9800",

    # Status
    "success": "#0abab5",
    "warning": "#f0a030",
    "error": "#e05050",
}


def source_badge_html(source: str) -> str:
    """Return styled HTML badge for a communication source."""
    color = COLORS["gmail_badge"] if source == "gmail" else COLORS["brightwheel_badge"]
    return (
        f"<span style='background-color:{color};color:white;"
        f"padding:2px 8px;border-radius:3px;font-size:10px;font-weight:bold;"
        f"font-family:Helvetica,Arial,sans-serif;'>"
        f"{source.upper()}</span>"
    )


def get_app_stylesheet() -> str:
    """Comprehensive QSS stylesheet for the entire application."""
    c = COLORS
    return f"""
        /* ---- Global ---- */
        * {{
            font-family: Helvetica, Arial, sans-serif;
            font-size: 13px;
            color: {c['text_primary']};
        }}

        QMainWindow {{
            background-color: {c['background']};
        }}

        QWidget {{
            background-color: transparent;
        }}

        /* ---- Menu bar ---- */
        QMenuBar {{
            background-color: {c['navy']};
            color: white;
            padding: 2px;
            font-size: 13px;
        }}
        QMenuBar::item {{
            background-color: transparent;
            color: white;
            padding: 4px 10px;
            border-radius: 3px;
        }}
        QMenuBar::item:selected {{
            background-color: {c['navy_light']};
        }}
        QMenu {{
            background-color: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 4px;
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 24px;
            border-radius: 3px;
        }}
        QMenu::item:selected {{
            background-color: {c['accent_light']};
            color: {c['accent']};
        }}
        QMenu::separator {{
            height: 1px;
            background: {c['border_light']};
            margin: 4px 8px;
        }}

        /* ---- Toolbar ---- */
        QToolBar {{
            background-color: {c['navy']};
            border: none;
            padding: 4px 8px;
            spacing: 6px;
        }}
        QToolBar QLabel {{
            color: rgba(255,255,255,0.85);
            font-size: 12px;
        }}
        QToolBar QPushButton {{
            background-color: rgba(255,255,255,0.15);
            color: white;
            border: 1px solid rgba(255,255,255,0.25);
            border-radius: 4px;
            padding: 5px 14px;
            font-size: 12px;
            font-weight: bold;
        }}
        QToolBar QPushButton:hover {{
            background-color: rgba(255,255,255,0.25);
            border-color: rgba(255,255,255,0.4);
        }}
        QToolBar QPushButton:pressed {{
            background-color: rgba(255,255,255,0.1);
        }}
        QToolBar QPushButton:disabled {{
            background-color: rgba(255,255,255,0.05);
            color: rgba(255,255,255,0.4);
            border-color: rgba(255,255,255,0.1);
        }}

        /* ---- Tabs ---- */
        QTabWidget::pane {{
            border: 1px solid {c['border']};
            background-color: {c['background']};
            border-radius: 0 0 6px 6px;
        }}
        QTabBar::tab {{
            background-color: transparent;
            color: {c['text_secondary']};
            padding: 8px 20px;
            margin-right: 2px;
            border-bottom: 3px solid transparent;
            font-size: 13px;
            font-weight: bold;
        }}
        QTabBar::tab:selected {{
            color: {c['accent']};
            border-bottom: 3px solid {c['accent']};
        }}
        QTabBar::tab:hover:!selected {{
            color: {c['text_primary']};
            border-bottom: 3px solid {c['border']};
        }}

        /* ---- Buttons ---- */
        QPushButton {{
            background-color: {c['accent']};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 16px;
            font-weight: bold;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: {c['accent_hover']};
        }}
        QPushButton:pressed {{
            background-color: {c['navy']};
        }}
        QPushButton:disabled {{
            background-color: {c['border']};
            color: {c['text_muted']};
        }}
        QPushButton:flat {{
            background-color: transparent;
            color: {c['text_primary']};
            border: none;
        }}
        QPushButton:flat:hover {{
            background-color: {c['surface_hover']};
        }}

        /* ---- Scroll areas ---- */
        QScrollArea {{
            background-color: {c['background']};
            border: none;
        }}

        /* ---- Scrollbars ---- */
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {c['border']};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {c['text_muted']};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: none;
        }}
        QScrollBar:horizontal {{
            background: transparent;
            height: 8px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: {c['border']};
            border-radius: 4px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {c['text_muted']};
        }}
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        QScrollBar::add-page:horizontal,
        QScrollBar::sub-page:horizontal {{
            background: none;
        }}

        /* ---- Inputs ---- */
        QLineEdit {{
            background-color: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 4px;
            padding: 5px 8px;
            color: {c['text_primary']};
        }}
        QLineEdit:focus {{
            border-color: {c['accent']};
            background-color: {c['surface']};
        }}
        QComboBox {{
            background-color: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 4px;
            padding: 4px 8px;
            color: {c['text_primary']};
        }}
        QComboBox:focus {{
            border-color: {c['accent']};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {c['surface']};
            border: 1px solid {c['border']};
            selection-background-color: {c['accent_light']};
            selection-color: {c['accent']};
        }}
        QDateEdit {{
            background-color: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 4px;
            padding: 4px 8px;
            color: {c['text_primary']};
        }}
        QDateEdit:focus {{
            border-color: {c['accent']};
        }}

        /* ---- Labels ---- */
        QLabel {{
            background-color: transparent;
            color: {c['text_primary']};
        }}

        /* ---- Frames / cards ---- */
        QFrame#SummaryCard, QFrame#ChecklistCard {{
            background-color: {c['surface']};
            border: 1px solid {c['border_light']};
            border-radius: 8px;
        }}

        /* ---- Splitter ---- */
        QSplitter::handle {{
            background-color: {c['border_light']};
            width: 2px;
        }}
        QSplitter::handle:hover {{
            background-color: {c['accent']};
        }}

        /* ---- Status bar ---- */
        QStatusBar {{
            background-color: {c['surface']};
            border-top: 1px solid {c['border_light']};
            color: {c['text_secondary']};
            font-size: 12px;
        }}
        QStatusBar QLabel {{
            color: {c['text_secondary']};
            font-size: 12px;
        }}

        /* ---- Progress bar ---- */
        QProgressBar {{
            background-color: {c['border_light']};
            border: none;
            border-radius: 3px;
            height: 6px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {c['accent']};
            border-radius: 3px;
        }}

        /* ---- Checkboxes ---- */
        QCheckBox {{
            spacing: 8px;
            color: {c['text_primary']};
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {c['border']};
            border-radius: 4px;
            background-color: {c['surface']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {c['accent']};
            border-color: {c['accent']};
        }}
        QCheckBox::indicator:hover {{
            border-color: {c['accent']};
        }}

        /* ---- Dialogs ---- */
        QDialog {{
            background-color: {c['background']};
        }}
        QGroupBox {{
            background-color: {c['surface']};
            border: 1px solid {c['border_light']};
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 16px;
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 6px;
            color: {c['navy']};
        }}
    """
