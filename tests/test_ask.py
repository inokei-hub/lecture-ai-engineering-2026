from types import SimpleNamespace
import sys

from app import ask as ask_module


def test_ask_prints_input_and_output_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        text="answer",
        usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=4),
    )
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kwargs: response)
    )
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("question") == "answer"
    assert "[tokens] input=12, output=4" in capsys.readouterr().out


def test_ask_without_usage_metadata_still_returns_answer(monkeypatch, capsys):
    response = SimpleNamespace(text="answer", usage_metadata=None)
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kwargs: response)
    )
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    assert ask_module.ask("question") == "answer"
    assert capsys.readouterr().out == ""


def test_interactive_mode_sends_followups_to_the_same_chat(monkeypatch, capsys):
    responses = iter(
        [
            SimpleNamespace(
                text="first answer",
                usage_metadata=SimpleNamespace(prompt_token_count=3, candidates_token_count=2),
            ),
            SimpleNamespace(
                text="follow-up answer",
                usage_metadata=SimpleNamespace(prompt_token_count=8, candidates_token_count=3),
            ),
        ]
    )
    sent_messages = []

    def send_message(question):
        sent_messages.append(question)
        return next(responses)

    chat = SimpleNamespace(send_message=send_message)
    client = SimpleNamespace(chats=SimpleNamespace(create=lambda **kwargs: chat))
    questions = iter(["first question", "follow-up", "/exit"])
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("builtins.input", lambda prompt: next(questions))
    monkeypatch.setattr(sys, "argv", ["app.ask", "--interactive"])

    ask_module.main()

    output = capsys.readouterr().out
    assert sent_messages == ["first question", "follow-up"]
    assert "first answer" in output
    assert "follow-up answer" in output