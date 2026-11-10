import json
import sys
import tempfile
import unittest
import urllib.error

from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body

    def close(self):
        pass


class TestInputValidation(unittest.TestCase):

    def test_rejects_empty_question(self):
        with patch("builtins.input", return_value="   "):
            with self.assertRaises(ValueError):
                main.get_research_question()

    def test_rejects_oversized_question(self):
        with patch("builtins.input", return_value="x" * 5001):
            with self.assertRaises(ValueError):
                main.get_research_question()


class TestOllamaClient(unittest.TestCase):

    def test_accepts_valid_response(self):
        body = json.dumps({
            "message": {"content": "Research analysis"}
        }).encode("utf-8")

        with patch(
            "main.urllib.request.urlopen",
            return_value=FakeResponse(body)
        ):
            result = main.query_ollama("Test question")

        self.assertEqual(result, "Research analysis")

    def test_rejects_non_dictionary_response(self):
        with patch(
            "main.urllib.request.urlopen",
            return_value=FakeResponse(b"[]")
        ):
            with self.assertRaises(RuntimeError):
                main.query_ollama("Test question")

    def test_rejects_missing_message(self):
        with patch(
            "main.urllib.request.urlopen",
            return_value=FakeResponse(b"{}")
        ):
            with self.assertRaises(RuntimeError):
                main.query_ollama("Test question")

    def test_rejects_empty_content(self):
        body = b'{"message":{"content":" "}}'

        with patch(
            "main.urllib.request.urlopen",
            return_value=FakeResponse(body)
        ):
            with self.assertRaises(RuntimeError):
                main.query_ollama("Test question")

    def test_handles_invalid_json(self):
        with patch(
            "main.urllib.request.urlopen",
            return_value=FakeResponse(b"invalid json")
        ):
            with self.assertRaises(RuntimeError):
                main.query_ollama("Test question")

    def test_handles_connection_failure(self):
        with patch(
            "main.urllib.request.urlopen",
            side_effect=urllib.error.URLError("offline")
        ):
            with self.assertRaises(RuntimeError):
                main.query_ollama("Test question")

    def test_handles_http_error(self):
        error_response = FakeResponse(b"model not found")
        http_error = urllib.error.HTTPError(
            url="http://localhost:11434/api/chat",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=error_response,
        )
        with patch(
            "main.urllib.request.urlopen",
            side_effect=http_error,
        ):
            with self.assertRaises(RuntimeError) as ctx:
                main.query_ollama("Test question")
            self.assertIn("Ollama HTTP error (404)", str(ctx.exception))
            self.assertIn("model not found", str(ctx.exception))

    def test_handles_timeout_error(self):
        with patch(
            "main.urllib.request.urlopen",
            side_effect=TimeoutError("timed out"),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                main.query_ollama("Test question")
            self.assertIn("Ollama request timed out.", str(ctx.exception))


class TestResearchOutput(unittest.TestCase):

    def test_sanitizes_filename(self):
        result = main.sanitize_filename('bad<>:"/\\|?*name')
        self.assertNotIn("<", result)
        self.assertNotIn(":", result)
        self.assertNotIn("/", result)

    def test_sanitizes_filename_control_characters(self):
        result = main.sanitize_filename("bad\x00\x1f\x0a\x0dname")
        self.assertEqual(result, "badname")

    def test_generates_markdown_with_provenance(self):
        result = main.create_markdown(
            "Test question",
            "Test analysis"
        )

        self.assertIn("Test question", result)
        self.assertIn("Test analysis", result)
        self.assertIn("not independently verified", result)
        self.assertIn(main.MODEL, result)

    def test_saves_research_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(
                main,
                "RESEARCH_DIR",
                Path(temp_dir)
            ):
                output = main.save_research(
                    "Test research question",
                    "Test research analysis"
                )

                self.assertTrue(output.exists())
                self.assertEqual(output.suffix, ".md")
                self.assertIn(
                    "Test research analysis",
                    output.read_text(encoding="utf-8")
                )

    def test_saves_research_resolves_filename_collision(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(main, "RESEARCH_DIR", Path(temp_dir)):
                output1 = main.save_research(
                    "Collision question", "Analysis 1"
                )
                output2 = main.save_research(
                    "Collision question", "Analysis 2"
                )

                self.assertTrue(output1.exists())
                self.assertTrue(output2.exists())
                self.assertNotEqual(output1, output2)
                self.assertTrue(output2.name.endswith("-1.md"))


class TestApplicationMain(unittest.TestCase):

    def test_main_completes_successful_workflow(self):
        with patch(
            "main.get_research_question",
            return_value="Test research question"
        ) as get_question, patch(
            "main.query_ollama",
            return_value="Test analysis"
        ) as query, patch(
            "main.save_research",
            return_value=Path("test-report.md")
        ) as save, patch("builtins.print"):

            result = main.main()

        self.assertEqual(result, 0)
        get_question.assert_called_once_with()
        query.assert_called_once_with("Test research question")
        save.assert_called_once_with(
            "Test research question",
            "Test analysis"
        )

class TestApplicationFailures(unittest.TestCase):

    def test_main_returns_error_when_ollama_fails(self):
        with patch("main.get_research_question", return_value="Test question"), \
             patch("main.query_ollama", side_effect=RuntimeError("Ollama offline")), \
             patch("builtins.print"):
            result = main.main()

        self.assertEqual(result, 1)

if __name__ == "__main__":
    unittest.main()
