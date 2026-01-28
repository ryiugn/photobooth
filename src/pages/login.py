"""
Login Page (Page 0) for Photobooth Application.

Implements secure PIN-based authentication with FOFOBOOTH styling.
"""
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QGridLayout, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPalette


class LoginPage(QWidget):
    """
    Login screen with PIN entry for authentication.

    Features:
    - PIN input with masked entry
    - Numeric keypad (0-9, Clear, Enter)
    - Error display for incorrect PIN
    - Shake animation on failed attempts
    - FOFOBOOTH styling (dark background, pink accents)
    """

    # Signal emitted when authentication is successful
    authenticated = pyqtSignal()

    def __init__(self, correct_pin="1234"):
        """
        Initialize the login page.

        Args:
            correct_pin: The correct PIN for authentication (default: "1234")
        """
        super().__init__()
        self.correct_pin = correct_pin
        self._authenticated = False
        self.failed_attempts = 0
        self.max_attempts = 5

        self.init_ui()
        self.apply_styling()

    def init_ui(self):
        """Initialize the UI components."""
        # Main layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title label
        title_label = QLabel("PHOTOBOOTH")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Montserrat", 32, QFont.Bold))

        # PIN input field (masked)
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setAlignment(Qt.AlignCenter)
        self.pin_input.setPlaceholderText("Enter PIN")
        self.pin_input.setMaxLength(6)
        # Not read-only - allow physical keyboard input
        self.pin_input.textChanged.connect(self._on_text_changed)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setVisible(False)

        # Numeric keypad
        keypad_layout = self.create_keypad()

        # Add widgets to main layout
        layout.addWidget(title_label)
        layout.addSpacing(30)
        layout.addWidget(self.pin_input)
        layout.addSpacing(10)
        layout.addWidget(self.error_label)
        layout.addSpacing(20)
        layout.addLayout(keypad_layout)

        # Add stretch to center everything
        layout.addStretch()

        self.setLayout(layout)

        # Set window title
        self.setWindowTitle("Photobooth - Login")

    def create_keypad(self):
        """
        Create the numeric keypad layout.

        Returns:
            QGridLayout: The keypad layout
        """
        keypad_layout = QGridLayout()
        keypad_layout.setSpacing(10)

        # Define keypad buttons
        buttons = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('C', 3, 0), ('0', 3, 1), ('⏎', 3, 2),
        ]

        # Create buttons
        for text, row, col in buttons:
            btn = QPushButton(text)
            btn.setFixedSize(80, 80)

            if text == 'C':
                btn.clicked.connect(self.clear_input)
            elif text == '⏎':
                btn.clicked.connect(self.verify_pin)
                self.enter_button = btn  # Store reference for testing
            else:
                btn.clicked.connect(lambda checked, digit=text: self.append_digit(digit))

            keypad_layout.addWidget(btn, row, col)

        return keypad_layout

    def apply_styling(self):
        """Apply scallop seashell gradient styling to the page."""
        # Apply stylesheet with seashell gradient background
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFF8DC,
                    stop:0.3 #FFF0E0,
                    stop:0.6 #FFE4C4,
                    stop:1 #FFDAB9
                );
                color: #1A0A00;
            }

            QLabel {
                color: #1A0A00;
                font-family: 'Montserrat', 'Poppins', sans-serif;
                background: transparent;
            }

            QLineEdit {
                background-color: rgba(255, 255, 255, 0.95);
                color: #1A0A00;
                border: 3px solid #D4A574;
                border-radius: 15px;
                padding: 15px;
                font-size: 24px;
                font-family: 'Montserrat', 'Poppins', sans-serif;
            }

            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFE4C4,
                    stop:1 #FFDAB9
                );
                color: #1A0A00;
                border: 2px solid #1A0A00;
                border-radius: 12px;
                font-size: 24px;
                font-weight: bold;
                font-family: 'Montserrat', 'Poppins', sans-serif;
            }

            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFDAB9,
                    stop:1 #FFCBA4
                );
            }

            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFCBA4,
                    stop:1 #E8B090
                );
            }
        """)

        # Style the title label specifically
        self.findChild(QLabel, "title_label")

        # Style error label in red/pink
        self.error_label.setStyleSheet("""
            QLabel {
                color: #FFC0CB;
                font-size: 16px;
                font-weight: bold;
            }
        """)

    def append_digit(self, digit):
        """
        Append a digit to the PIN input.

        Args:
            digit: The digit to append (0-9)
        """
        current_pin = self.pin_input.text()
        if len(current_pin) < 6:  # Max 6 digits
            self.pin_input.setText(current_pin + digit)

    def _on_text_changed(self, text):
        """Handle text changed event - auto-submit when PIN is complete."""
        # Hide error when user starts typing
        if text:
            self.error_label.setVisible(False)
        # Auto-submit when PIN reaches correct length
        if len(text) == len(self.correct_pin):
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(300, self.verify_pin)

    def keyPressEvent(self, event):
        """Handle key press events - allow Enter/Return to submit PIN."""
        # Handle Enter/Return keys (including numpad Enter)
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            current_pin = self.pin_input.text()
            if current_pin:  # Only verify if there's input
                self.verify_pin()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def clear_input(self):
        """Clear the PIN input field."""
        self.pin_input.setText("")
        self.error_label.setVisible(False)

    def showEvent(self, event):
        """Handle show event - clear PIN when page is shown (e.g., when going back)."""
        super().showEvent(event)
        # Clear PIN input when returning to this page
        self.clear_input()

    def verify_pin(self):
        """Verify the entered PIN against the correct PIN."""
        entered_pin = self.pin_input.text()

        if entered_pin == self.correct_pin:
            # Successful authentication
            self._authenticated = True
            self.authenticated.emit()
            self.error_label.setVisible(False)
        else:
            # Failed authentication
            self._authenticated = False
            self.failed_attempts += 1

            # Show error message
            self.error_label.setText(f"Incorrect PIN. Attempt {self.failed_attempts}/{self.max_attempts}")
            self.error_label.setVisible(True)

            # Shake animation
            self.shake_animation()

            # Clear input after brief delay
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1000, self.clear_input)

            # Check max attempts
            if self.failed_attempts >= self.max_attempts:
                self.error_label.setText("Maximum attempts reached. Please try again later.")
                self.pin_input.setEnabled(False)

    def shake_animation(self):
        """Animate the PIN input with a shake effect on error."""
        from PyQt5.QtCore import QPoint

        # Simple shake by moving left and right
        original_pos = self.pin_input.pos()
        shake_distance = 10

        # Create shake animation
        animation = QPropertyAnimation(self.pin_input, b"pos")
        animation.setDuration(300)
        animation.setLoopCount(3)

        # Shake pattern: left, right, center
        animation.setKeyValueAt(0, original_pos)
        animation.setKeyValueAt(0.25, original_pos + QPoint(-shake_distance, 0))
        animation.setKeyValueAt(0.5, original_pos + QPoint(shake_distance, 0))
        animation.setKeyValueAt(1, original_pos)

        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start()

    def is_authenticated(self):
        """
        Check if the user is authenticated.

        Returns:
            bool: True if authenticated, False otherwise
        """
        return self._authenticated

    @staticmethod
    def load_config(config_path="project_files/config.json"):
        """
        Load authentication configuration from file.

        Args:
            config_path: Path to the configuration file

        Returns:
            dict: Configuration dictionary with authentication settings
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('authentication', {})
        except FileNotFoundError:
            # Return default configuration
            return {
                'method': 'pin',
                'pin_hash': None,
                'max_attempts': 5,
                'lockout_duration_seconds': 30,
                'session_timeout_minutes': 15
            }
