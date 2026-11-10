import json
import sys
import tempfile
import unittest
import urllib.error

from datetime import datetime, timezone
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
        http_error.close()

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
        fixed_dt = datetime(2026, 11, 10, 12, 0, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(main, "RESEARCH_DIR", Path(temp_dir)):
                with patch("main.datetime") as mock_datetime:
                    mock_datetime.now.return_value = fixed_dt
                    mock_datetime.fromtimestamp = datetime.fromtimestamp
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


class TestCLIAndArchive(unittest.TestCase):

    def test_parser_defaults(self):
        parser = main.build_parser()
        args = parser.parse_args([])
        self.assertIsNone(args.question)
        self.assertEqual(args.model, main.MODEL)
        self.assertEqual(args.url, main.OLLAMA_URL)
        self.assertEqual(args.timeout, main.REQUEST_TIMEOUT)
        self.assertFalse(args.list)
        self.assertIsNone(args.view)

    def test_parser_custom_args(self):
        parser = main.build_parser()
        args = parser.parse_args([
            "-q", "My custom question",
            "-m", "custom-model",
            "--url", "http://custom:11434/api/chat",
            "--timeout", "60",
            "-l",
        ])
        self.assertEqual(args.question, "My custom question")
        self.assertEqual(args.model, "custom-model")
        self.assertEqual(args.url, "http://custom:11434/api/chat")
        self.assertEqual(args.timeout, 60)
        self.assertTrue(args.list)

    def test_get_research_question_uses_cli_argument(self):
        result = main.get_research_question("   Valid CLI question   ")
        self.assertEqual(result, "Valid CLI question")

    def test_main_with_cli_question(self):
        with patch(
            "main.query_ollama",
            return_value="CLI analysis"
        ) as query, patch(
            "main.save_research",
            return_value=Path("cli-report.md")
        ) as save, patch("builtins.print"):

            result = main.main(["-q", "Direct CLI question"])

        self.assertEqual(result, 0)
        query.assert_called_once_with("Direct CLI question")
        save.assert_called_once_with("Direct CLI question", "CLI analysis")

    def test_main_list_invokes_display_report_list(self):
        with patch("main.display_report_list", return_value=0) as mock_list:
            result = main.main(["--list"])
        self.assertEqual(result, 0)
        mock_list.assert_called_once_with()

    def test_main_view_invokes_display_report(self):
        with patch("main.display_report", return_value=0) as mock_view:
            result = main.main(["--view", "sample.md"])
        self.assertEqual(result, 0)
        mock_view.assert_called_once_with("sample.md")

    def test_display_report_list_empty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("builtins.print") as mock_print:
                result = main.display_report_list(research_dir=Path(temp_dir))
            self.assertEqual(result, 0)
            mock_print.assert_any_call("\nNo research reports found in archive.")

    def test_display_report_list_with_reports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            report_file = temp_path / "20261110-000000-Test-Report.md"
            report_file.write_text("sample content", encoding="utf-8")
            with patch("builtins.print") as mock_print:
                result = main.display_report_list(research_dir=temp_path)
            self.assertEqual(result, 0)
            printed = [
                call.args[0]
                for call in mock_print.call_args_list
                if call.args
            ]
            self.assertTrue(
                any("20261110-000000-Test-Report.md" in text for text in printed)
            )

    def test_display_report_not_found(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("sys.stderr.write"):
                result = main.display_report(
                    "nonexistent.md", research_dir=Path(temp_dir)
                )
            self.assertEqual(result, 1)

    def test_display_report_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            report_file = temp_path / "valid-report.md"
            report_file.write_text("# Test Report Content", encoding="utf-8")
            with patch("builtins.print") as mock_print:
                result = main.display_report(
                    "valid-report.md", research_dir=temp_path
                )
            self.assertEqual(result, 0)
            mock_print.assert_any_call("# Test Report Content")

if __name__ == "__main__":
    unittest.main()
