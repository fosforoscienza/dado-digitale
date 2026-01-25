import asyncio
import json
import sys
import threading
from pathlib import Path

import websockets
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

CONFIG_PATH = Path(__file__).with_name("config.json")


def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class WebSocketClient(QObject):
    message_received = Signal(dict)
    connection_lost = Signal()

    def __init__(self, url: str, role: str):
        super().__init__()
        self.url = url
        self.role = role
        self._loop = None
        self._ws = None
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def _run(self):
        asyncio.run(self._main())

    async def _main(self):
        try:
            async with websockets.connect(self.url) as websocket:
                self._ws = websocket
                self._loop = asyncio.get_running_loop()
                await websocket.send(json.dumps({"type": "register", "role": self.role}))
                async for message in websocket:
                    payload = json.loads(message)
                    self.message_received.emit(payload)
        except Exception:
            self.connection_lost.emit()

    def send(self, payload: dict):
        if self._ws is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self._ws.send(json.dumps(payload)),
            self._loop,
        )


class HumanClientWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Turing Test - Client Umano")
        self.resize(800, 600)

        self.config = load_config()

        self.round_label = QLabel("Round: 0/3")
        self.round_label.setFont(QFont("Arial", 18, QFont.Bold))

        self.question_label = QLabel("In attesa della domanda...")
        self.question_label.setWordWrap(True)
        self.question_label.setFont(QFont("Arial", 16))

        self.answer_input = QPlainTextEdit()
        self.answer_input.setFont(QFont("Arial", 16))
        self.answer_input.setPlaceholderText("Scrivi la risposta...")
        self.answer_input.setEnabled(False)

        self.send_button = QPushButton("Invia risposta (Ctrl+Invio)")
        self.send_button.setEnabled(False)
        self.send_button.clicked.connect(self.send_answer)

        self.status_label = QLabel("Attendere la domanda.")
        self.status_label.setFont(QFont("Arial", 14))

        layout = QVBoxLayout()
        layout.addWidget(self.round_label)
        layout.addWidget(self.question_label)
        layout.addWidget(self.answer_input)
        layout.addWidget(self.send_button)
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.send_answer)

        self.ws_client = None
        self.connect_to_server()

    def connect_to_server(self):
        host = self.config.get("host", "127.0.0.1")
        port = self.config.get("port", 8765)
        url = f"ws://{host}:{port}"
        self.ws_client = WebSocketClient(url, "human")
        self.ws_client.message_received.connect(self.handle_message)
        self.ws_client.connection_lost.connect(self.handle_disconnect)
        self.ws_client.start()

    def handle_disconnect(self):
        QMessageBox.warning(self, "Connessione persa", "Connessione al server persa.")

    def handle_message(self, payload):
        msg_type = payload.get("type")
        if msg_type == "state":
            round_index = payload.get("round", 0)
            self.round_label.setText(f"Round: {round_index}/3")
            if payload.get("awaiting"):
                question = payload.get("question", "")
                self.question_label.setText(question)
                self.enable_input(True)
            return

        if msg_type == "new_question":
            round_index = payload.get("round", 0)
            question = payload.get("question", "")
            self.round_label.setText(f"Round: {round_index}/3")
            self.question_label.setText(question)
            self.enable_input(True)
            return

    def enable_input(self, enabled: bool):
        self.answer_input.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        if enabled:
            self.status_label.setText("Rispondi quando sei pronto.")
            self.answer_input.setFocus()
        else:
            self.status_label.setText("Risposta inviata. Attendi la prossima domanda.")

    def send_answer(self):
        if not self.answer_input.isEnabled():
            return
        text = self.answer_input.toPlainText().strip()
        if not text:
            return
        self.ws_client.send({"type": "human_answer", "text": text})
        self.answer_input.clear()
        self.enable_input(False)


def main():
    app = QApplication(sys.argv)
    window = HumanClientWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
