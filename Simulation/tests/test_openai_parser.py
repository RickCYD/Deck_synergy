import types
import oracle_text_parser
from boardstate import BoardState


def test_parse_triggers_with_gpt(monkeypatch):
    dummy_resp = types.SimpleNamespace(
        output_text='[{"event": "attack", "effect": "draw_cards", "amount": 2, "conditions": ["requires_haste"]}]'
    )

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        class responses:
            @staticmethod
            def create(*args, **kwargs):
                return dummy_resp

    monkeypatch.setattr(oracle_text_parser, "OpenAI", lambda api_key=None: DummyClient())

    text = "Whenever CARD attacks, draw two cards. CARD must have haste to trigger."
    triggers = oracle_text_parser.parse_triggers_with_gpt(text)
    assert len(triggers) == 1
    trig = triggers[0]
    assert trig.event == "attack"
    assert trig.requires_haste

    class Cmdr:
        name = "Commander"

    board = BoardState(["A", "B", "C", "D"], Cmdr())
    trig.effect(board)
    assert len(board.hand) == 2
