"""Tests JARVIS DUAL — stdlib unittest, aucun LLM requis.

Un faux serveur HTTP reproduit les pannes réelles : serveur mort, modèle
absent, HTTP 200 vide, silence prolongé, streaming normal. Ce qui ne peut
pas être simulé (débit d'un vrai modèle) relève du benchmark, pas d'ici.

Lancer :  python3 -m unittest discover -s dual/tests -v
"""

from __future__ import annotations

import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

from dual import checkpoint as cp
from dual.dispatcher import DualDispatcher, aggregate
from dual.providers import Timeouts, build_provider
from dual.worker import Worker

MODE = {"value": "ok"}  # piloté par chaque test


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # silence
        pass

    def _json(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/v1/models":
            self._json(200, {"data": [{"id": "fake-model"}, {"id": "ghost-model"}]})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        mode = MODE["value"]

        if mode == "model_missing" or body.get("model") == "ghost-model":
            self._json(400, {"error": {"message": "Failed to load model"}})
            return
        if mode == "server_error":
            self._json(500, {"error": "boom"})
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()  # HTTP/1.1 sans Content-Length → chunked implicite fermé à la fin

        def sse(obj):
            self.wfile.write(f"data: {json.dumps(obj)}\n\n".encode())
            self.wfile.flush()

        if mode == "empty":
            sse({"choices": [{"delta": {}}]})
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
            self.close_connection = True
            return
        if mode == "silent":
            time.sleep(3.0)  # dépasse first_token_timeout des tests
            self.close_connection = True
            return

        for tok in ("Bon", "jour", " le", " monde"):
            sse({"choices": [{"delta": {"content": tok}}]})
            time.sleep(0.01)
        sse(
            {
                "usage": {
                    "prompt_tokens": 7,
                    "completion_tokens": 4,
                    "total_tokens": 11,
                },
                "choices": [{"delta": {}}],
            }
        )
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()
        self.close_connection = True


class FakeServer:
    def __init__(self):
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.srv.server_address[1]
        self.t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.t.start()

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}"

    def stop(self):
        self.srv.shutdown()
        self.srv.server_close()


class ProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = FakeServer()
        cls.t = Timeouts(connect=2, first_token=1.5, idle=1.5, request=10)

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()

    def provider(self):
        return build_provider("lmstudio", self.srv.url, self.t)

    def test_discover_models(self):
        self.assertIn("fake-model", self.provider().discover_models())

    def test_health_up(self):
        self.assertEqual(self.provider().health()["status"], "up")

    def test_health_down_when_server_unavailable(self):
        p = build_provider("lmstudio", "http://127.0.0.1:1", self.t)
        self.assertEqual(p.health()["status"], "down")

    def test_model_status(self):
        p = self.provider()
        self.assertEqual(p.model_status("fake-model"), "AVAILABLE")
        self.assertEqual(p.model_status("absent"), "UNAVAILABLE")

    def test_success_and_metrics(self):
        MODE["value"] = "ok"
        r = self.provider().chat("fake-model", [{"role": "user", "content": "hi"}])
        self.assertEqual(r.status, "success")
        self.assertEqual(r.content, "Bonjour le monde")
        self.assertNotEqual(r.metrics["ttft_ms"], "UNAVAILABLE")
        self.assertEqual(r.metrics["completion_tokens"], 4)
        self.assertIsInstance(r.metrics["tokens_per_second"], (int, float))

    def test_empty_response_is_not_success(self):
        MODE["value"] = "empty"
        r = self.provider().chat("fake-model", [{"role": "user", "content": "hi"}])
        self.assertEqual(r.status, "empty_response")
        self.assertFalse(r.ok)

    def test_ghost_model_detected(self):
        MODE["value"] = "ok"
        r = self.provider().chat("ghost-model", [{"role": "user", "content": "hi"}])
        self.assertEqual(r.status, "model_unavailable")

    def test_first_token_timeout(self):
        MODE["value"] = "silent"
        r = self.provider().chat("fake-model", [{"role": "user", "content": "hi"}])
        self.assertEqual(r.status, "timeout_first_token")
        MODE["value"] = "ok"

    def test_server_unavailable(self):
        p = build_provider("lmstudio", "http://127.0.0.1:1", self.t)
        r = p.chat("fake-model", [{"role": "user", "content": "hi"}])
        self.assertIn(r.status, ("server_unavailable", "timeout_connect"))

    def test_metrics_never_invented(self):
        """Sans usage fourni, tokens_per_second doit valoir UNAVAILABLE."""
        MODE["value"] = "silent"
        r = self.provider().chat("fake-model", [{"role": "user", "content": "hi"}])
        self.assertEqual(r.metrics["tokens_per_second"], "UNAVAILABLE")
        self.assertEqual(r.metrics["prompt_tokens"], "UNAVAILABLE")
        MODE["value"] = "ok"


class WorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = FakeServer()
        cls.t = Timeouts(connect=2, first_token=1.5, idle=1.5, request=10)

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()

    def worker(self, model="fake-model", attempts=2):
        p = build_provider("lmstudio", self.srv.url, self.t)
        return Worker(
            "worker_a",
            p,
            model,
            retry={"max_attempts": attempts, "backoff_base_s": 1.01},
        )

    def test_run_success_and_heartbeat(self):
        MODE["value"] = "ok"
        w = self.worker()
        r = w.run("bonjour")
        self.assertTrue(r.ok)
        self.assertEqual(w.hb.status, "COMPLETED")
        self.assertGreater(w.hb.tokens, 0)

    def test_no_blind_retry_on_model_unavailable(self):
        MODE["value"] = "ok"
        w = self.worker(model="ghost-model", attempts=3)
        t0 = time.perf_counter()
        r = w.run("bonjour")
        self.assertEqual(r.status, "model_unavailable")
        self.assertLess(time.perf_counter() - t0, 1.0)  # pas de backoff inutile

    def test_retry_on_transient_error(self):
        MODE["value"] = "server_error"
        w = self.worker(attempts=2)
        r = w.run("bonjour")
        self.assertIn(r.status, ("http_error", "empty_response"))
        self.assertEqual(w.hb.status, "FAILED")
        MODE["value"] = "ok"

    def test_health_reports_unhealthy_for_ghost(self):
        MODE["value"] = "ok"
        self.assertFalse(self.worker(model="absent").health()["healthy"])


class DispatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = FakeServer()

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()

    def cfg(self, two=True):
        c = {
            "timeouts": {"connect": 2, "first_token": 2, "idle": 2, "request": 10},
            "retry": {"max_attempts": 1, "backoff_base_s": 1.01},
            "providers": {
                "fakeA": {
                    "kind": "lmstudio",
                    "base_url": self.srv.url,
                    "models": ["fake-model"],
                }
            },
            "workers": {
                "worker_a": {
                    "provider": "fakeA",
                    "model": "fake-model",
                    "role": "primary",
                }
            },
        }
        if two:
            c["providers"]["fakeB"] = {
                "kind": "lmstudio",
                "base_url": self.srv.url,
                "models": ["fake-model"],
            }
            c["workers"]["worker_b"] = {
                "provider": "fakeB",
                "model": "fake-model",
                "role": "secondary",
            }
        return c

    def test_split_only_on_explicit_markers(self):
        self.assertEqual(len(DualDispatcher.split("fais un truc")), 1)
        multi = DualDispatcher.split("1. faire A\n2. faire B\n3. faire C")
        self.assertEqual(multi, ["faire A", "faire B", "faire C"])

    def test_single_mode(self):
        MODE["value"] = "ok"
        with TemporaryDirectory() as d:
            self._isolate(d)
            out = DualDispatcher(self.cfg()).run("bonjour", mode="single")
        self.assertEqual(out["status"], "SUCCESS")
        self.assertEqual(len(out["results"]), 1)

    def test_parallel_runs_both_workers(self):
        MODE["value"] = "ok"
        with TemporaryDirectory() as d:
            self._isolate(d)
            out = DualDispatcher(self.cfg()).run("bonjour", mode="parallel")
        self.assertEqual(len(out["results"]), 2)
        self.assertEqual(
            {r["worker"] for r in out["results"]}, {"worker_a", "worker_b"}
        )

    def test_parallel_degrades_to_single_with_one_worker(self):
        MODE["value"] = "ok"
        with TemporaryDirectory() as d:
            self._isolate(d)
            out = DualDispatcher(self.cfg(two=False)).run("bonjour", mode="parallel")
        self.assertEqual(len(out["results"]), 1)

    def test_blocked_without_workers(self):
        with TemporaryDirectory() as d:
            self._isolate(d)
            c = self.cfg()
            c["workers"] = {}
            out = DualDispatcher(c).run("bonjour", mode="single")
        self.assertEqual(out["status"], "BLOCKED")

    def test_checkpoint_written_and_resumable(self):
        MODE["value"] = "ok"
        with TemporaryDirectory() as d:
            self._isolate(d)
            disp = DualDispatcher(self.cfg())
            out = disp.run("1. tache A\n2. tache B", mode="single")
            state = cp.JobStore(out["job_id"]).load()
            self.assertEqual(len(state["tasks"]), 2)
            self.assertTrue(all(t["status"] == "SUCCESS" for t in state["tasks"]))
            self.assertFalse(cp.JobStore(out["job_id"]).resumable())

    def test_recovery_after_simulated_crash(self):
        """Job à moitié fait → seules les tâches non SUCCESS sont rejouées."""
        MODE["value"] = "ok"
        with TemporaryDirectory() as d:
            self._isolate(d)
            disp = DualDispatcher(self.cfg())
            tasks = [cp.make_task(1, "tache A"), cp.make_task(2, "tache B")]
            disp.store.create("x", "single", tasks)
            disp.store.update_task("TASK-001", status="SUCCESS")
            disp.store.set_status("RUNNING")
            self.assertTrue(disp.store.resumable())
            out = disp.run("", mode="single", resume=True)
            self.assertEqual(len(out["results"]), 1)  # TASK-002 seulement
            self.assertEqual(out["results"][0]["task"], "TASK-002")

    def test_journal_records_events(self):
        MODE["value"] = "ok"
        with TemporaryDirectory() as d:
            self._isolate(d)
            disp = DualDispatcher(self.cfg())
            disp.run("bonjour", mode="single")
            evs = {e["event"] for e in disp.journal.read()}
        for required in (
            "JOB_CREATED",
            "TASK_DISPATCHED",
            "WORKER_STARTED",
            "FIRST_TOKEN",
            "WORKER_COMPLETED",
            "CHECKPOINT",
            "JOB_COMPLETED",
        ):
            self.assertIn(required, evs)

    @staticmethod
    def _isolate(d):
        """Redirige logs et checkpoints vers un répertoire temporaire."""
        from dual import checkpoint, config, journal

        p = Path(d)
        config.LOG_DIR = journal.LOG_DIR = p / "logs"
        config.JOB_DIR = checkpoint.JOB_DIR = p / "jobs"


class AggregatorTests(unittest.TestCase):
    R = [
        {
            "status": "success",
            "worker": "worker_a",
            "model": "m1",
            "content": "court",
            "metrics": {"ttft_ms": 100},
        },
        {
            "status": "success",
            "worker": "worker_b",
            "model": "m2",
            "content": "une reponse nettement plus longue",
            "metrics": {"ttft_ms": 300},
        },
    ]

    def test_first(self):
        self.assertEqual(aggregate(self.R, "first")["worker"], "worker_a")

    def test_best_prefers_substance(self):
        self.assertEqual(aggregate(self.R, "best")["worker"], "worker_b")

    def test_merge_keeps_both(self):
        out = aggregate(self.R, "merge")
        self.assertIn("worker_a", out["content"])
        self.assertIn("worker_b", out["content"])

    def test_failed_when_nothing_succeeded(self):
        out = aggregate([{"status": "timeout_idle", "worker": "worker_a"}], "first")
        self.assertEqual(out["status"], "FAILED")


class WatchdogTests(unittest.TestCase):
    def test_stale_job_detected_and_marked(self):
        from dual import watchdog

        with TemporaryDirectory() as d:
            DispatcherTests._isolate(d)
            jid = cp.new_job_id("stale")
            store = cp.JobStore(jid)
            store.create("x", "single", [cp.make_task(1, "a")])
            store.set_status("RUNNING")
            rep = watchdog.sweep(max_age_s=-1, act=True)
            self.assertGreaterEqual(rep["stale"], 1)
            self.assertEqual(cp.JobStore(jid).load()["status"], "RECOVERABLE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
