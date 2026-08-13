"""Concurrence INTER-PROCESSUS sur les checkpoints.

`jarvis-dual run` et `jarvis-dual watchdog --act` sont deux processus qui
écrivent le même fichier de job — c'est le cas d'usage prévu, pas un cas
tordu. Un `threading.Lock` ne protège que les threads d'un même processus :
sans verrou fichier, un read-modify-write concurrent perd des écritures,
c'est-à-dire perd la progression que le module promet de préserver.

Lancer :  python3 -m unittest dual.tests.test_concurrency -v
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent.parent.parent

WORKER_SRC = textwrap.dedent("""
    import sys
    sys.path.insert(0, {root!r})
    import os
    os.environ["JARVIS_DUAL_JOBS"] = {jobs!r}
    from dual import checkpoint as cp
    cp.JOB_DIR = __import__("pathlib").Path({jobs!r})

    job_id, task_id, rounds = sys.argv[1], sys.argv[2], int(sys.argv[3])
    store = cp.JobStore(job_id)
    for i in range(rounds):
        store.update_task(task_id, attempts=i + 1)
    store.update_task(task_id, status="SUCCESS")
""")


class InterProcessCheckpointTests(unittest.TestCase):
    N_PROC = 6
    ROUNDS = 12

    def test_no_lost_update_across_processes(self):
        with TemporaryDirectory() as d:
            from dual import checkpoint as cp

            cp.JOB_DIR = Path(d)
            job_id = cp.new_job_id("concurrency")
            store = cp.JobStore(job_id, job_dir=Path(d))
            tasks = [cp.make_task(i + 1, f"tâche {i + 1}") for i in range(self.N_PROC)]
            store.create("test concurrence", "single", tasks)

            src = Path(d) / "worker.py"
            src.write_text(WORKER_SRC.format(root=str(ROOT), jobs=d))

            procs = [
                subprocess.Popen(
                    [sys.executable, str(src), job_id, t["id"], str(self.ROUNDS)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for t in tasks
            ]
            for p in procs:
                _out, err = p.communicate(timeout=90)
                self.assertEqual(p.returncode, 0, f"worker en échec: {err[:300]}")

            final = cp.JobStore(job_id, job_dir=Path(d)).load()
            done = [t["id"] for t in final["tasks"] if t.get("status") == "SUCCESS"]
            missing = [t["id"] for t in final["tasks"] if t.get("status") != "SUCCESS"]
            self.assertEqual(
                len(done),
                self.N_PROC,
                f"écritures perdues — {len(missing)}/{self.N_PROC} tâches non "
                f"enregistrées: {missing}. Un verrou intra-processus ne protège "
                f"pas contre un autre processus.",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
