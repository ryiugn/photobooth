import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from src.pages.login import LoginPage

@pytest.fixture
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_login_page_initialization(app):
    page = LoginPage(correct_pin="1234")
    assert page.windowTitle() == "Photobooth - Login"
    assert not page.is_authenticated()

def test_correct_pin_authenticates(app):
    page = LoginPage(correct_pin="1234")
    # Simulate entering "1234"
    page.pin_input.setText("1234")
    QTest.mouseClick(page.enter_button, Qt.LeftButton)
    assert page.is_authenticated()

def test_wrong_pin_shows_error(app):
    page = LoginPage(correct_pin="1234")
    page.pin_input.setText("9999")
    QTest.mouseClick(page.enter_button, Qt.LeftButton)
    assert not page.is_authenticated()
    assert "Incorrect" in page.error_label.text()
