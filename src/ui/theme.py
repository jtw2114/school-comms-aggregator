"""macOS-inspired light theme with Apple design language."""

# =============================================================================
# COLOR PALETTE - Apple macOS inspired
# =============================================================================

COLORS = {
    # Backgrounds - all white for consistency
    "window_background": "#FFFFFF",      # Pure white
    "sidebar_background": "#FFFFFF",     # Pure white
    "surface": "#FFFFFF",                 # Pure white
    "surface_hover": "#F5F5F7",          # Subtle hover (light gray)
    "surface_selected": "rgba(0, 122, 255, 0.08)",  # Selection tint
    "surface_pressed": "rgba(0, 122, 255, 0.12)",

    # Accent colors (Apple system blue)
    "accent": "#007AFF",
    "accent_hover": "#0066D6",
    "accent_pressed": "#0055B3",
    "accent_light": "rgba(0, 122, 255, 0.1)",

    # Text
    "text_primary": "#1D1D1F",
    "text_secondary": "#86868B",
    "text_tertiary": "#AEAEB2",
    "text_on_accent": "#FFFFFF",
    "text_disabled": "#C7C7CC",

    # Separators and borders
    "separator": "#E5E5EA",
    "separator_opaque": "#D1D1D6",
    "border": "#E5E5EA",
    "border_light": "#F2F2F7",

    # Semantic colors
    "destructive": "#FF3B30",
    "success": "#34C759",
    "warning": "#FF9500",
    "info": "#5AC8FA",

    # Source badges
    "gmail_badge": "#EA4335",
    "brightwheel_badge": "#FF9500",
    "whatsapp_badge": "#25D366",
}

# =============================================================================
# TYPOGRAPHY
# =============================================================================

TYPOGRAPHY = {
    "font_family": "'Segoe UI', 'SF Pro Display', -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif",
    "title_large": "22px",
    "title_medium": "20px",
    "section_header": "15px",
    "body": "13px",
    "caption": "11px",
    "small": "10px",
}

# =============================================================================
# SPACING (8px grid)
# =============================================================================

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
    "xxl": 48,
}

# =============================================================================
# BORDER RADIUS
# =============================================================================

RADIUS = {
    "sm": 4,
    "md": 8,
    "lg": 10,
    "xl": 12,
    "pill": 9999,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_card_style(selected: bool = False) -> str:
    """Return QSS for communication card widgets with optional selection state."""
    c = COLORS
    if selected:
        return f"""
            background-color: {c['surface_selected']};
            border: 1px solid {c['accent']};
            border-radius: {RADIUS['lg']}px;
        """
    else:
        return f"""
            background-color: {c['surface']};
            border: 1px solid {c['separator']};
            border-radius: {RADIUS['lg']}px;
        """


def get_checkbox_label_style(checked: bool = False) -> str:
    """Return QSS for checkbox label with strikethrough when checked."""
    c = COLORS
    if checked:
        return f"color: {c['text_tertiary']}; text-decoration: line-through;"
    else:
        return f"color: {c['text_primary']}; text-decoration: none;"


def get_webview_css() -> str:
    """Return CSS for QWebEngineView HTML content."""
    c = COLORS
    t = TYPOGRAPHY
    return f"""
        body {{
            font-family: {t['font_family']};
            font-size: {t['body']};
            color: {c['text_primary']};
            background-color: {c['surface']};
            line-height: 1.5;
            margin: 0;
            padding: 16px;
        }}
        a {{
            color: {c['accent']};
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border-radius: {RADIUS['md']}px;
        }}
        pre, code {{
            background-color: {c['window_background']};
            border-radius: {RADIUS['sm']}px;
            padding: 2px 6px;
            font-family: 'SF Mono', Consolas, monospace;
            font-size: 12px;
        }}
        pre {{
            padding: 12px;
            overflow-x: auto;
        }}
        blockquote {{
            border-left: 3px solid {c['accent']};
            margin: 16px 0;
            padding-left: 16px;
            color: {c['text_secondary']};
        }}
        h1, h2, h3, h4 {{
            color: {c['text_primary']};
            margin-top: 24px;
            margin-bottom: 8px;
        }}
        hr {{
            border: none;
            border-top: 1px solid {c['separator']};
            margin: 16px 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        th, td {{
            border: 1px solid {c['separator']};
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: {c['window_background']};
            font-weight: 600;
        }}
    """


def source_badge_html(source: str) -> str:
    """Return styled HTML badge with Apple-style pill design."""
    c = COLORS
    t = TYPOGRAPHY
    colors = {
        "gmail": c["gmail_badge"],
        "brightwheel": c["brightwheel_badge"],
        "whatsapp": c["whatsapp_badge"],
    }
    bg = colors.get(source.lower(), c["text_secondary"])
    return (
        f"<span style='background-color:{bg};color:white;"
        f"padding:2px 8px;border-radius:10px;font-size:{t['small']};"
        f"font-weight:600;font-family:{t['font_family']};'>"
        f"{source.upper()}</span>"
    )


def get_landing_button_style() -> str:
    """Return stylesheet for landing page navigation buttons."""
    c = COLORS
    return f"""
        QPushButton {{
            background-color: {c['surface']};
            color: {c['text_primary']};
            border: 1px solid {c['separator']};
            border-radius: {RADIUS['xl']}px;
            padding: 24px;
            font-size: 15px;
            font-weight: 500;
            text-align: center;
        }}
        QPushButton:hover {{
            background-color: {c['surface_hover']};
            border-color: {c['separator_opaque']};
        }}
        QPushButton:pressed {{
            background-color: {c['surface_selected']};
            border-color: {c['accent']};
        }}
    """


# =============================================================================
# MAIN APPLICATION STYLESHEET
# =============================================================================

def get_app_stylesheet() -> str:
    """Comprehensive QSS stylesheet for the entire application (macOS-inspired)."""
    c = COLORS
    t = TYPOGRAPHY
    r = RADIUS
    s = SPACING

    return f"""
        /* ================================================================== */
        /* GLOBAL                                                              */
        /* ================================================================== */

        * {{
            font-family: {t['font_family']};
            font-size: {t['body']};
            color: {c['text_primary']};
        }}

        QMainWindow, QWidget, QFrame, QScrollArea, QSplitter, QTabWidget, QStackedWidget {{
            background-color: {c['surface']};
        }}

        /* ================================================================== */
        /* MENU BAR (Light macOS style)                                        */
        /* ================================================================== */

        QMenuBar {{
            background-color: {c['surface']};
            color: {c['text_primary']};
            border-bottom: 1px solid {c['separator']};
            padding: 4px 8px;
            font-size: {t['body']};
            font-weight: 500;
        }}

        QMenuBar::item {{
            background-color: transparent;
            color: {c['text_primary']};
            padding: 6px 12px;
            border-radius: {r['sm']}px;
        }}

        QMenuBar::item:selected {{
            background-color: {c['surface_selected']};
        }}

        QMenuBar::item:pressed {{
            background-color: {c['accent']};
            color: {c['text_on_accent']};
        }}

        QMenu {{
            background-color: {c['surface']};
            border: 1px solid {c['separator']};
            border-radius: {r['md']}px;
            padding: 4px;
        }}

        QMenu::item {{
            padding: 8px 24px 8px 12px;
            border-radius: {r['sm']}px;
        }}

        QMenu::item:selected {{
            background-color: {c['accent']};
            color: {c['text_on_accent']};
        }}

        QMenu::separator {{
            height: 1px;
            background: {c['separator']};
            margin: 4px 8px;
        }}

        /* ================================================================== */
        /* TOOLBAR (Light flat style)                                          */
        /* ================================================================== */

        QToolBar {{
            background-color: {c['surface']};
            border: none;
            border-bottom: 1px solid {c['separator']};
            padding: 8px 16px;
            spacing: 8px;
        }}

        QToolBar QLabel {{
            color: {c['text_secondary']};
            font-size: {t['caption']};
        }}

        QToolBar QPushButton {{
            background-color: transparent;
            color: {c['text_primary']};
            border: 1px solid {c['separator']};
            border-radius: {r['md']}px;
            padding: 6px 16px;
            font-size: {t['body']};
            font-weight: 500;
        }}

        QToolBar QPushButton:hover {{
            background-color: {c['surface_hover']};
            border-color: {c['separator_opaque']};
        }}

        QToolBar QPushButton:pressed {{
            background-color: {c['surface_selected']};
            border-color: {c['accent']};
        }}

        QToolBar QPushButton:disabled {{
            background-color: transparent;
            color: {c['text_disabled']};
            border-color: {c['border_light']};
        }}

        /* ================================================================== */
        /* TABS (Underline style)                                              */
        /* ================================================================== */

        QTabWidget {{
            background-color: {c['window_background']};
        }}

        QTabWidget::pane {{
            border: none;
            background-color: {c['window_background']};
        }}

        QTabBar::tab {{
            background-color: transparent;
            color: {c['text_secondary']};
            padding: 10px 20px;
            margin-right: 4px;
            border-bottom: 2px solid transparent;
            font-size: {t['body']};
            font-weight: 500;
        }}

        QTabBar::tab:selected {{
            color: {c['accent']};
            border-bottom: 2px solid {c['accent']};
        }}

        QTabBar::tab:hover:!selected {{
            color: {c['text_primary']};
            border-bottom: 2px solid {c['separator']};
        }}

        /* ================================================================== */
        /* BUTTONS                                                             */
        /* ================================================================== */

        QPushButton {{
            background-color: {c['accent']};
            color: {c['text_on_accent']};
            border: none;
            border-radius: {r['md']}px;
            padding: 8px 18px;
            font-weight: 500;
            font-size: {t['body']};
        }}

        QPushButton:hover {{
            background-color: {c['accent_hover']};
        }}

        QPushButton:pressed {{
            background-color: {c['accent_pressed']};
        }}

        QPushButton:disabled {{
            background-color: {c['separator']};
            color: {c['text_disabled']};
        }}

        QPushButton:flat {{
            background-color: transparent;
            color: {c['accent']};
            border: none;
        }}

        QPushButton:flat:hover {{
            background-color: {c['accent_light']};
        }}

        QPushButton:flat:pressed {{
            background-color: {c['surface_selected']};
        }}

        /* Secondary button style (use with setProperty("class", "secondary")) */
        QPushButton[class="secondary"] {{
            background-color: {c['surface']};
            color: {c['text_primary']};
            border: 1px solid {c['separator']};
        }}

        QPushButton[class="secondary"]:hover {{
            background-color: {c['surface_hover']};
            border-color: {c['separator_opaque']};
        }}

        /* Destructive button style */
        QPushButton[class="destructive"] {{
            background-color: {c['destructive']};
            color: {c['text_on_accent']};
        }}

        QPushButton[class="destructive"]:hover {{
            background-color: #E02020;
        }}

        /* ================================================================== */
        /* SCROLL AREAS                                                        */
        /* ================================================================== */

        QScrollArea {{
            border: none;
        }}

        /* ================================================================== */
        /* SCROLLBARS (Thin, modern)                                           */
        /* ================================================================== */

        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 0;
        }}

        QScrollBar::handle:vertical {{
            background: {c['separator_opaque']};
            border-radius: 4px;
            min-height: 32px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {c['text_tertiary']};
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
            background: {c['separator_opaque']};
            border-radius: 4px;
            min-width: 32px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: {c['text_tertiary']};
        }}

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0;
        }}

        QScrollBar::add-page:horizontal,
        QScrollBar::sub-page:horizontal {{
            background: none;
        }}

        /* ================================================================== */
        /* INPUT FIELDS                                                        */
        /* ================================================================== */

        QLineEdit {{
            background-color: {c['surface']};
            border: 1px solid {c['separator']};
            border-radius: {r['md']}px;
            padding: 8px 12px;
            color: {c['text_primary']};
            selection-background-color: {c['accent_light']};
        }}

        QLineEdit:focus {{
            border-color: {c['accent']};
        }}

        QLineEdit:disabled {{
            background-color: {c['window_background']};
            color: {c['text_disabled']};
        }}

        QLineEdit::placeholder {{
            color: {c['text_tertiary']};
        }}

        QTextEdit {{
            background-color: {c['surface']};
            border: 1px solid {c['separator']};
            border-radius: {r['md']}px;
            padding: 8px 12px;
            color: {c['text_primary']};
            selection-background-color: {c['accent_light']};
        }}

        QTextEdit:focus {{
            border-color: {c['accent']};
        }}

        QComboBox {{
            background-color: {c['surface']};
            border: 1px solid {c['separator']};
            border-radius: {r['md']}px;
            padding: 8px 12px;
            color: {c['text_primary']};
            min-width: 80px;
        }}

        QComboBox:focus {{
            border-color: {c['accent']};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 24px;
            padding-right: 8px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {c['surface']};
            border: 1px solid {c['separator']};
            border-radius: {r['md']}px;
            selection-background-color: {c['accent']};
            selection-color: {c['text_on_accent']};
            padding: 4px;
        }}

        QDateEdit {{
            background-color: {c['surface']};
            border: 1px solid {c['separator']};
            border-radius: {r['md']}px;
            padding: 8px 12px;
            color: {c['text_primary']};
        }}

        QDateEdit:focus {{
            border-color: {c['accent']};
        }}

        QDateEdit::drop-down {{
            border: none;
            width: 24px;
        }}

        /* ================================================================== */
        /* LABELS                                                              */
        /* ================================================================== */

        QLabel {{
            background-color: transparent;
            color: {c['text_primary']};
        }}

        QLabel#landing_title {{
            font-size: {t['title_large']};
            font-weight: 600;
            color: {c['text_primary']};
        }}

        QLabel#landing_subtitle {{
            font-size: {t['section_header']};
            font-weight: 400;
            color: {c['text_secondary']};
        }}

        QLabel#page_title {{
            font-size: {t['title_medium']};
            font-weight: 600;
            color: {c['text_primary']};
        }}

        QLabel#section_header {{
            font-size: {t['section_header']};
            font-weight: 600;
            color: {c['text_primary']};
        }}

        QLabel#card_header {{
            font-size: 14px;
            font-weight: 600;
            color: {c['text_primary']};
        }}

        QLabel#caption {{
            font-size: {t['caption']};
            color: {c['text_secondary']};
        }}

        QLabel#error_banner {{
            color: {c['destructive']};
            background-color: rgba(255, 59, 48, 0.1);
            padding: 12px 16px;
            border-radius: {r['md']}px;
            font-size: {t['body']};
        }}

        /* ================================================================== */
        /* CARDS AND FRAMES                                                    */
        /* ================================================================== */

        QFrame {{
            background-color: {c['window_background']};
        }}

        QFrame#SummaryCard,
        QFrame#ChecklistCard {{
            background-color: {c['surface']};
            border: 1px solid {c['separator']};
            border-radius: {r['lg']}px;
        }}

        QFrame#CommunicationCard {{
            background-color: {c['surface']};
            border: 1px solid {c['separator']};
            border-radius: {r['lg']}px;
        }}

        QFrame#CommunicationCard:hover {{
            background-color: {c['surface_hover']};
        }}

        QFrame#DaySectionItem {{
            background-color: {c['surface']};
            border: 1px solid {c['separator']};
            border-radius: {r['md']}px;
        }}

        QFrame#DaySectionItem:hover {{
            background-color: {c['surface_hover']};
        }}

        /* ================================================================== */
        /* SPLITTER                                                            */
        /* ================================================================== */

        QSplitter {{
            background-color: {c['window_background']};
        }}

        QSplitter::handle {{
            background-color: {c['separator']};
            width: 1px;
        }}

        QSplitter::handle:hover {{
            background-color: {c['accent']};
        }}

        /* ================================================================== */
        /* STATUS BAR                                                          */
        /* ================================================================== */

        QStatusBar {{
            background-color: {c['surface']};
            border-top: 1px solid {c['separator']};
            color: {c['text_secondary']};
            font-size: {t['caption']};
            padding: 4px 8px;
        }}

        QStatusBar QLabel {{
            color: {c['text_secondary']};
            font-size: {t['caption']};
        }}

        /* ================================================================== */
        /* PROGRESS BAR                                                        */
        /* ================================================================== */

        QProgressBar {{
            background-color: {c['separator']};
            border: none;
            border-radius: 3px;
            height: 6px;
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {c['accent']};
            border-radius: 3px;
        }}

        /* ================================================================== */
        /* CHECKBOXES                                                          */
        /* ================================================================== */

        QCheckBox {{
            spacing: 10px;
            color: {c['text_primary']};
        }}

        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {c['separator_opaque']};
            border-radius: {r['sm']}px;
            background-color: {c['surface']};
        }}

        QCheckBox::indicator:checked {{
            background-color: {c['accent']};
            border-color: {c['accent']};
        }}

        QCheckBox::indicator:hover {{
            border-color: {c['accent']};
        }}

        QCheckBox::indicator:disabled {{
            background-color: {c['window_background']};
            border-color: {c['separator']};
        }}

        /* ================================================================== */
        /* DIALOGS                                                             */
        /* ================================================================== */

        QDialog {{
            background-color: {c['window_background']};
        }}

        QGroupBox {{
            background-color: {c['surface']};
            border: 1px solid {c['separator']};
            border-radius: {r['lg']}px;
            margin-top: 20px;
            padding: 20px 16px 16px 16px;
            font-weight: 500;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            left: 12px;
            color: {c['text_primary']};
            font-size: {t['body']};
            font-weight: 600;
        }}

        /* ================================================================== */
        /* TOOLTIPS                                                            */
        /* ================================================================== */

        QToolTip {{
            background-color: {c['text_primary']};
            color: {c['surface']};
            border: none;
            border-radius: {r['sm']}px;
            padding: 6px 10px;
            font-size: {t['caption']};
        }}

        /* ================================================================== */
        /* FILTER TOOLBAR                                                      */
        /* ================================================================== */

        QWidget#FilterToolbar {{
            background-color: {c['surface']};
            border-bottom: 1px solid {c['separator']};
        }}

        QWidget#FilterToolbar QLabel {{
            color: {c['text_secondary']};
            font-size: {t['caption']};
            font-weight: 500;
        }}

        /* ================================================================== */
        /* DAY SECTION                                                         */
        /* ================================================================== */

        QWidget#DaySection {{
            border-bottom: 1px solid {c['separator']};
        }}

        QPushButton#DaySectionToggle {{
            background-color: transparent;
            color: {c['text_primary']};
            border: none;
            border-radius: 0;
            padding: 12px 0;
            text-align: left;
            font-weight: 500;
        }}

        QPushButton#DaySectionToggle:hover {{
            background-color: {c['surface_hover']};
        }}

        /* ================================================================== */
        /* PHOTO GALLERY                                                       */
        /* ================================================================== */

        QLabel#GalleryTitle {{
            font-size: 14px;
            font-weight: 600;
            color: {c['text_primary']};
        }}

        QLabel#PhotoPlaceholder {{
            background-color: {c['window_background']};
            border: 1px solid {c['separator']};
            border-radius: {r['md']}px;
            color: {c['text_tertiary']};
        }}

        /* ================================================================== */
        /* TABLES AND LISTS                                                    */
        /* ================================================================== */

        QTableView, QTreeView, QListView {{
            background-color: {c['surface']};
            border: 1px solid {c['separator']};
            border-radius: {r['md']}px;
            gridline-color: {c['separator']};
            selection-background-color: {c['accent']};
            selection-color: {c['text_on_accent']};
        }}

        QTableView::item, QTreeView::item, QListView::item {{
            padding: 8px;
        }}

        QTableView::item:hover, QTreeView::item:hover, QListView::item:hover {{
            background-color: {c['surface_hover']};
        }}

        QHeaderView::section {{
            background-color: {c['window_background']};
            color: {c['text_primary']};
            font-weight: 600;
            padding: 8px 12px;
            border: none;
            border-bottom: 1px solid {c['separator']};
        }}

        /* ================================================================== */
        /* WEB ENGINE VIEW                                                     */
        /* ================================================================== */

        QWebEngineView {{
            background-color: {c['surface']};
        }}
    """
