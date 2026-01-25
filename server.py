import asyncio
import json
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import websockets

from llm_adapter import ask_llm

CONFIG_PATH = Path(__file__).with_name("config.json")


def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@dataclass
class AnswerState:
    text: str = ""
    status: str = "waiting"


@dataclass
class RoundState:
    question: str = ""
    answers: Dict[str, AnswerState] = field(default_factory=dict)
    llm_release_at: float = 0.0
    llm_release_epoch: float = 0.0


class GameState:
    def __init__(self, config):
        self.config = config
        self.round_index = 0
        self.max_rounds = 3
        self.assignment = self._random_assignment()
        self.current_round: Optional[RoundState] = None
        self.question_log = []
        self.examiner_clients = set()
        self.human_client = None
        self.human_connected = False
        self.lock = asyncio.Lock()
        self.human_timeout_task = None
        self.llm_task = None
        self.llm_release_task = None
        self.llm_response_ready = False
        self.llm_error = None

    def _random_assignment(self):
        if random.choice([True, False]):
            return {"A": "human", "B": "llm"}
        return {"A": "llm", "B": "human"}

    def reset_round_state(self, question: str, llm_release_at: float, llm_release_epoch: float):
        self.current_round = RoundState(
            question=question,
            answers={
                "human": AnswerState(),
                "llm": AnswerState(),
            },
            llm_release_at=llm_release_at,
            llm_release_epoch=llm_release_epoch,
        )
        self.llm_response_ready = False
        self.llm_error = None


async def send_json(websocket, payload):
    await websocket.send(json.dumps(payload))


def map_slot(assignment, role):
    for slot, value in assignment.items():
        if value == role:
            return slot
    return "A"


def round_complete(state: GameState):
    if state.current_round is None:
        return False
    human_status = state.current_round.answers["human"].status
    llm_status = state.current_round.answers["llm"].status
    return human_status != "waiting" and llm_status != "waiting"


async def broadcast_examiner(state: GameState, payload):
    if not state.examiner_clients:
        return
    await asyncio.gather(*(send_json(ws, payload) for ws in state.examiner_clients))


async def handle_question(state: GameState, text: str):
    async with state.lock:
        if state.round_index >= state.max_rounds:
            return
        if state.current_round and not round_complete(state):
            return
        state.round_index += 1
        question = text.strip()
        llm_delay = state.config.get("llm_delay_seconds", 40)
        release_at = time.monotonic() + llm_delay
        release_epoch = time.time() + llm_delay
        state.reset_round_state(question, release_at, release_epoch)
        state.question_log.append(question)

    await broadcast_examiner(
        state,
        {
            "type": "question_sent",
            "round": state.round_index,
            "question": question,
            "llm_release_epoch": release_epoch,
        },
    )

    await broadcast_examiner(
        state,
        {
            "type": "answer_update",
            "slot": map_slot(state.assignment, "human"),
            "status": "waiting",
            "text": "",
        },
    )
    await broadcast_examiner(
        state,
        {
            "type": "answer_update",
            "slot": map_slot(state.assignment, "llm"),
            "status": "waiting",
            "text": "",
        },
    )
    await broadcast_examiner(state, {"type": "human_waiting", "waiting": True})

    if state.human_client:
        await send_json(
            state.human_client,
            {
                "type": "new_question",
                "round": state.round_index,
                "question": question,
            },
        )

    if state.human_timeout_task:
        state.human_timeout_task.cancel()
    if state.llm_task:
        state.llm_task.cancel()
    if state.llm_release_task:
        state.llm_release_task.cancel()

    state.human_timeout_task = asyncio.create_task(human_timeout(state))
    state.llm_task = asyncio.create_task(run_llm(state, question))
    state.llm_release_task = asyncio.create_task(release_llm(state))


async def human_timeout(state: GameState):
    timeout_seconds = state.config.get("human_timeout_seconds", 120)
    try:
        await asyncio.sleep(timeout_seconds)
    except asyncio.CancelledError:
        return

    async with state.lock:
        if state.current_round is None:
            return
        if state.current_round.answers["human"].status != "waiting":
            return
        state.current_round.answers["human"].status = "skipped"

    await broadcast_examiner(
        state,
        {
            "type": "answer_update",
            "slot": map_slot(state.assignment, "human"),
            "status": "skipped",
            "text": "Risposta umana non ricevuta.",
        },
    )
    await broadcast_examiner(state, {"type": "human_waiting", "waiting": False})
    await check_round_completion(state)


async def run_llm(state: GameState, question: str):
    try:
        response = await asyncio.to_thread(ask_llm, question)
    except Exception as exc:
        async with state.lock:
            state.llm_error = str(exc)
            state.llm_response_ready = True
        await maybe_release_llm(state)
        return

    async with state.lock:
        if state.current_round is None:
            return
        state.current_round.answers["llm"].text = response
        state.llm_response_ready = True

    await maybe_release_llm(state)


async def release_llm(state: GameState):
    if state.current_round is None:
        return
    now = time.monotonic()
    delay = max(state.current_round.llm_release_at - now, 0)
    try:
        await asyncio.sleep(delay)
    except asyncio.CancelledError:
        return

    await maybe_release_llm(state, release_forced=True)


async def maybe_release_llm(state: GameState, release_forced: bool = False):
    async with state.lock:
        if state.current_round is None:
            return
        release_time_passed = time.monotonic() >= state.current_round.llm_release_at
        if not release_time_passed and not release_forced:
            return
        if not state.llm_response_ready:
            return

        if state.llm_error:
            state.current_round.answers["llm"].status = "error"
            response_text = "Errore LLM."
        else:
            state.current_round.answers["llm"].status = "received"
            response_text = state.current_round.answers["llm"].text

    await broadcast_examiner(
        state,
        {
            "type": "answer_update",
            "slot": map_slot(state.assignment, "llm"),
            "status": state.current_round.answers["llm"].status,
            "text": response_text,
        },
    )
    await check_round_completion(state)


async def check_round_completion(state: GameState):
    if not round_complete(state):
        return

    await broadcast_examiner(
        state,
        {
            "type": "round_complete",
            "round": state.round_index,
        },
    )

    if state.round_index >= state.max_rounds:
        await broadcast_examiner(
            state,
            {
                "type": "game_complete",
                "assignment": state.assignment,
            },
        )


async def handle_human_answer(state: GameState, text: str):
    async with state.lock:
        if state.current_round is None:
            return
        if state.current_round.answers["human"].status != "waiting":
            return
        state.current_round.answers["human"].status = "received"
        state.current_round.answers["human"].text = text

    await broadcast_examiner(
        state,
        {
            "type": "answer_update",
            "slot": map_slot(state.assignment, "human"),
            "status": "received",
            "text": text,
        },
    )
    await broadcast_examiner(state, {"type": "human_waiting", "waiting": False})
    if state.human_timeout_task:
        state.human_timeout_task.cancel()
    await check_round_completion(state)


async def handle_skip_human(state: GameState):
    async with state.lock:
        if state.current_round is None:
            return
        if state.current_round.answers["human"].status != "waiting":
            return
        state.current_round.answers["human"].status = "skipped"

    await broadcast_examiner(
        state,
        {
            "type": "answer_update",
            "slot": map_slot(state.assignment, "human"),
            "status": "skipped",
            "text": "Risposta umana saltata.",
        },
    )
    await broadcast_examiner(state, {"type": "human_waiting", "waiting": False})
    if state.human_timeout_task:
        state.human_timeout_task.cancel()
    await check_round_completion(state)


async def handle_retry_llm(state: GameState):
    async with state.lock:
        if state.current_round is None:
            return
        if state.current_round.answers["llm"].status != "error":
            return
        state.current_round.answers["llm"].status = "waiting"
        state.current_round.answers["llm"].text = ""
        state.llm_error = None
        state.llm_response_ready = False
        question = state.current_round.question

    await broadcast_examiner(
        state,
        {
            "type": "answer_update",
            "slot": map_slot(state.assignment, "llm"),
            "status": "waiting",
            "text": "",
        },
    )

    if state.llm_task:
        state.llm_task.cancel()
    state.llm_task = asyncio.create_task(run_llm(state, question))


async def register_client(state: GameState, websocket, role: str):
    if role == "examiner":
        state.examiner_clients.add(websocket)
        await send_json(
            websocket,
            {
                "type": "state",
                "round": state.round_index,
                "question_log": state.question_log,
                "human_connected": state.human_connected,
                "assignment": None,
            },
        )
        return

    if role == "human":
        state.human_client = websocket
        state.human_connected = True
        await broadcast_examiner(state, {"type": "human_status", "connected": True})
        await send_json(
            websocket,
            {
                "type": "state",
                "round": state.round_index,
                "question": state.current_round.question if state.current_round else "",
                "awaiting": state.current_round is not None
                and state.current_round.answers["human"].status == "waiting",
            },
        )


async def unregister_client(state: GameState, websocket):
    if websocket in state.examiner_clients:
        state.examiner_clients.discard(websocket)
        return

    if websocket == state.human_client:
        state.human_client = None
        state.human_connected = False
        await broadcast_examiner(state, {"type": "human_status", "connected": False})


async def handler(state: GameState, websocket):
    try:
        async for message in websocket:
            payload = json.loads(message)
            msg_type = payload.get("type")

            if msg_type == "register":
                await register_client(state, websocket, payload.get("role"))
                continue

            if msg_type == "question":
                await handle_question(state, payload.get("text", ""))
                continue

            if msg_type == "human_answer":
                await handle_human_answer(state, payload.get("text", ""))
                continue

            if msg_type == "skip_human":
                await handle_skip_human(state)
                continue

            if msg_type == "retry_llm":
                await handle_retry_llm(state)
                continue
    finally:
        await unregister_client(state, websocket)


async def main():
    config = load_config()
    state = GameState(config)
    host = config.get("host", "0.0.0.0")
    port = config.get("port", 8765)
    async with websockets.serve(lambda ws: handler(state, ws), host, port):
        print(f"Server avviato su ws://{host}:{port}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
