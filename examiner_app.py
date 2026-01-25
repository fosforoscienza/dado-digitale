import asyncio
import json
import sys
import threading
import time
from pathlib import Path

import websockets
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QHBoxLayout,
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


class ExaminerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Turing Test - Esaminatore")
        self.resize(1280, 720)

        self.config = load_config()
        self.llm_release_epoch = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)

        self.round_label = QLabel("Round: 0/3")
        self.round_label.setFont(QFont("Arial", 18, QFont.Bold))

        self.human_status_label = QLabel("Client umano disconnesso")
        self.human_status_label.setStyleSheet("color: #b00020;")

        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Scrivi la domanda...")
        self.question_input.textChanged.connect(self.toggle_send)
        self.question_input.returnPressed.connect(self.send_question)
        self.question_input.setFont(QFont("Arial", 16))

        self.send_button = QPushButton("Invia domanda")
        self.send_button.clicked.connect(self.send_question)
        self.send_button.setEnabled(False)

        self.skip_button = QPushButton("Salta risposta umano")
        self.skip_button.clicked.connect(self.skip_human)
        self.skip_button.setEnabled(False)

        self.retry_llm_button = QPushButton("Retry LLM")
        self.retry_llm_button.clicked.connect(self.retry_llm)
        self.retry_llm_button.setEnabled(False)

        self.timer_label = QLabel("AI tra: 00:40")
        self.timer_label.setFont(QFont("Arial", 16, QFont.Bold))

        self.log_list = QListWidget()

        self.answer_boxes = {}
        self.answer_status = {}
        columns_layout = QHBoxLayout()
        for slot in ["A", "B"]:
            column = QVBoxLayout()
            label = QLabel(f"Risposta {slot}")
            label.setFont(QFont("Arial", 18, QFont.Bold))
            status = QLabel("In attesa...")
            status.setFont(QFont("Arial", 14))
            box = QPlainTextEdit()
            box.setReadOnly(True)
            box.setFont(QFont("Arial", 16))
            box.setPlaceholderText("In attesa...")
            column.addWidget(label)
            column.addWidget(status)
            column.addWidget(box)
            columns_layout.addLayout(column)
            self.answer_boxes[slot] = box
            self.answer_status[slot] = status

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.round_label)
        top_bar.addStretch()
        top_bar.addWidget(self.timer_label)

        question_bar = QHBoxLayout()
        question_bar.addWidget(self.question_input)
        question_bar.addWidget(self.send_button)
        question_bar.addWidget(self.skip_button)
        question_bar.addWidget(self.retry_llm_button)

        left_layout = QVBoxLayout()
        left_layout.addLayout(top_bar)
        left_layout.addWidget(self.human_status_label)
        left_layout.addLayout(question_bar)
        left_layout.addLayout(columns_layout)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Log domande"))
        right_layout.addWidget(self.log_list)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.reveal_button = QPushButton("Rivela chi è l'AI")
        self.reveal_button.clicked.connect(self.reveal_assignment)
        self.reveal_button.setVisible(False)
        left_layout.addWidget(self.reveal_button)

        self.ws_client = None
        self.assignment = None
        self.connect_to_server()

    def connect_to_server(self):
        host = self.config.get("host", "127.0.0.1")
        port = self.config.get("port", 8765)
        url = f"ws://{host}:{port}"
        self.ws_client = WebSocketClient(url, "examiner")
        self.ws_client.message_received.connect(self.handle_message)
        self.ws_client.connection_lost.connect(self.handle_disconnect)
        self.ws_client.start()

    def handle_disconnect(self):
        QMessageBox.warning(self, "Connessione persa", "Connessione al server persa.")

    def toggle_send(self, text):
        self.send_button.setEnabled(bool(text.strip()))

    def send_question(self):
        text = self.question_input.text().strip()
        if not text:
            return
        self.ws_client.send({"type": "question", "text": text})
        self.question_input.clear()
        self.send_button.setEnabled(False)

    def skip_human(self):
        self.ws_client.send({"type": "skip_human"})

    def retry_llm(self):
        self.ws_client.send({"type": "retry_llm"})

    def handle_message(self, payload):
        msg_type = payload.get("type")

        if msg_type == "state":
            self.log_list.addItems(payload.get("question_log", []))
            self.update_human_status(payload.get("human_connected", False))
            return

        if msg_type == "human_status":
            self.update_human_status(payload.get("connected", False))
            return

        if msg_type == "question_sent":
            round_index = payload.get("round", 0)
            self.round_label.setText(f"Round: {round_index}/3")
            self.log_list.addItem(payload.get("question", ""))
            self.llm_release_epoch = payload.get("llm_release_epoch")
            self.timer.start(1000)
            self.skip_button.setEnabled(True)
            self.retry_llm_button.setEnabled(False)
            for slot in ["A", "B"]:
                self.answer_boxes[slot].setPlainText("")
                self.answer_boxes[slot].setPlaceholderText("In attesa...")
                self.answer_status[slot].setText("In attesa...")
            return

        if msg_type == "answer_update":
            slot = payload.get("slot")
            status = payload.get("status")
            text = payload.get("text", "")
            self.answer_status[slot].setText(self.status_text(status))
            if text:
                self.answer_boxes[slot].setPlainText(text)
            if status == "error":
                self.retry_llm_button.setEnabled(True)
            return

        if msg_type == "human_waiting":
            self.skip_button.setEnabled(payload.get("waiting", False))
            return

        if msg_type == "round_complete":
            self.skip_button.setEnabled(False)
            self.retry_llm_button.setEnabled(False)
            return

        if msg_type == "game_complete":
            self.assignment = payload.get("assignment")
            self.reveal_button.setVisible(True)
            QMessageBox.information(self, "Fine", "Scegli chi è l'AI.")
            return

    def update_human_status(self, connected: bool):
        if connected:
            self.human_status_label.setText("Client umano connesso")
            self.human_status_label.setStyleSheet("color: #006400;")
        else:
            self.human_status_label.setText("Client umano disconnesso")
            self.human_status_label.setStyleSheet("color: #b00020;")

    def status_text(self, status: str) -> str:
        mapping = {
            "waiting": "In attesa...",
            "received": "Ricevuta",
            "skipped": "Saltata",
            "error": "Errore",
        }
        return mapping.get(status, status)

    def update_countdown(self):
        if not self.llm_release_epoch:
            return
        remaining = int(self.llm_release_epoch - time.time())
        if remaining <= 0:
            self.timer_label.setText("AI: pronta")
            self.timer.stop()
            return
        minutes, seconds = divmod(remaining, 60)
        self.timer_label.setText(f"AI tra: {minutes:02d}:{seconds:02d}")

    def reveal_assignment(self):
        if not self.assignment:
            return
        human_slot = "A" if self.assignment.get("A") == "human" else "B"
        llm_slot = "A" if self.assignment.get("A") == "llm" else "B"
        QMessageBox.information(
            self,
            "Rivelazione",
            f"Umano: Risposta {human_slot}\nLLM: Risposta {llm_slot}",
        )


def main():
    app = QApplication(sys.argv)
    window = ExaminerWindow()
    window.show()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
