window.STATE =
{
  "version": 2,
  "slug": "checksite-fixes",
  "dir": "2026-11-09-checksite-fixes--wip",
  "title": "Checksite и Signum: проверка и публикация",
  "mode": "semi",
  "depth": "normal",
  "tier": "T0",
  "briefFile": "2026-11-09-brief.md",
  "memoryFile": "AGENTS.md",
  "memoryOwner": "user",
  "skillDir": "C:/Users/Alexandr/.codex/skills/autopilot",
  "baseCommit": "ca20fe1",
  "startedAt": "2026-11-09T22:19:15+03:00",
  "updatedAt": "2026-11-10T12:19:28+03:00",
  "finishedAt": null,
  "stages": [
    {
      "id": "preflight",
      "status": "done",
      "startedAt": "2026-11-09T22:19:15+03:00",
      "finishedAt": "2026-11-09T22:19:46+03:00"
    },
    {
      "id": "manifest",
      "status": "done",
      "startedAt": "2026-11-09T22:19:46+03:00",
      "finishedAt": "2026-11-09T22:21:18+03:00"
    },
    {
      "id": "briefing",
      "status": "skipped",
      "startedAt": "2026-11-09T22:19:48+03:00",
      "finishedAt": "2026-11-09T22:19:48+03:00",
      "note": "Факты проверяются в проекте; новые коммерческие условия не вводятся"
    },
    {
      "id": "spec",
      "status": "done",
      "startedAt": "2026-11-09T22:21:18+03:00",
      "finishedAt": "2026-11-09T22:32:05+03:00"
    },
    {
      "id": "plan",
      "status": "done",
      "startedAt": "2026-11-09T22:22:02+03:00",
      "finishedAt": "2026-11-09T22:32:05+03:00"
    },
    {
      "id": "build",
      "status": "done",
      "startedAt": "2026-11-09T22:22:08+03:00",
      "finishedAt": "2026-11-09T22:29:19+03:00"
    },
    {
      "id": "review",
      "status": "done",
      "startedAt": "2026-11-09T22:29:19+03:00",
      "finishedAt": "2026-11-09T22:32:05+03:00"
    },
    {
      "id": "final",
      "status": "active",
      "startedAt": "2026-11-09T22:32:05+03:00"
    }
  ],
  "requirements": {
    "total": 6,
    "done": 2,
    "inTicket": 4,
    "inSpec": 0,
    "placeholder": 0,
    "deferred": 0,
    "dropped": 0
  },
  "tickets": [
    {
      "id": "01",
      "title": "Замечания проверки сайта",
      "requirements": [
        "R01",
        "R02",
        "R03"
      ],
      "blockedBy": [],
      "wave": 1,
      "zone": [
        "build.py",
        "seo.py",
        "public/assets/style.css",
        "docs/PRIVACY.md",
        "docs/CHECKSITE-2026-11-09.md"
      ],
      "review": "нет",
      "model": "обычная",
      "status": "done",
      "startedAt": "2026-11-09T22:22:08+03:00",
      "finishedAt": "2026-11-09T22:29:19+03:00",
      "retries": 0,
      "repairs": 0,
      "tests": {
        "passed": 53,
        "failed": 0
      },
      "commit": "81f2567"
    },
    {
      "id": "02",
      "title": "Машиночитаемые представления и публикация",
      "requirements": [
        "G01",
        "G02",
        "G03",
        "R03"
      ],
      "blockedBy": [
        "01"
      ],
      "wave": 2,
      "zone": [
        "build.py",
        "seo.py",
        "apache_config.py",
        "src/worker-runtime.mjs",
        "tests/agent_content.test.py",
        "tests/test_apache_config.py",
        "tests/httpd_routing_integration.py",
        "tests/routing.test.mjs",
        "docs/SIGNUM-2026-11-10.md"
      ],
      "review": "нет",
      "model": "обычная",
      "status": "pending",
      "retries": 0,
      "repairs": 0
    }
  ],
  "tests": {
    "passed": 53,
    "failed": 0
  },
  "debt": {
    "placeholders": [],
    "assumptions": [],
    "emptyEnv": []
  },
  "additions": [],
  "coverage": {
    "found": 0,
    "fixed": 0,
    "deferred": 0,
    "items": []
  },
  "concerns": [],
  "blind": {
    "checked": 3,
    "matched": 2,
    "mismatches": [
      "R03: исходники приняты, публикация ожидает отдельного согласования массового пакета"
    ]
  },
  "beats": [
    "2026-11-09T22:19:15+03:00",
    "2026-11-09T22:19:46+03:00",
    "2026-11-09T22:19:47+03:00",
    "2026-11-09T22:19:48+03:00",
    "2026-11-09T22:21:18+03:00",
    "2026-11-09T22:22:02+03:00",
    "2026-11-09T22:22:03+03:00",
    "2026-11-09T22:22:04+03:00",
    "2026-11-09T22:22:05+03:00",
    "2026-11-09T22:22:07+03:00",
    "2026-11-09T22:22:08+03:00",
    "2026-11-09T22:22:16+03:00",
    "2026-11-09T22:22:17+03:00",
    "2026-11-09T22:29:19+03:00",
    "2026-11-09T22:32:05+03:00",
    "2026-11-09T22:32:06+03:00",
    "2026-11-09T22:32:25+03:00",
    "2026-11-10T12:17:50+03:00",
    "2026-11-10T12:17:51+03:00",
    "2026-11-10T12:18:51+03:00",
    "2026-11-10T12:18:52+03:00",
    "2026-11-10T12:19:24+03:00",
    "2026-11-10T12:19:25+03:00",
    "2026-11-10T12:19:26+03:00",
    "2026-11-10T12:19:27+03:00",
    "2026-11-10T12:19:28+03:00"
  ],
  "rev": 32,
  "waiting": null,
  "waits": [],
  "log": [
    {
      "t": "2026-11-09T22:19:15+03:00",
      "k": "init"
    },
    {
      "t": "2026-11-09T22:19:46+03:00",
      "k": "stage",
      "id": "manifest",
      "act": "start"
    },
    {
      "t": "2026-11-09T22:19:48+03:00",
      "k": "stage",
      "id": "briefing",
      "act": "skip",
      "note": "Факты проверяются в проекте; новые коммерческие условия не вводятся"
    },
    {
      "t": "2026-11-09T22:21:18+03:00",
      "k": "gate",
      "g": "G1",
      "ok": true,
      "open": 0,
      "total": 3
    },
    {
      "t": "2026-11-09T22:21:18+03:00",
      "k": "stage",
      "id": "spec",
      "act": "start"
    },
    {
      "t": "2026-11-09T22:22:02+03:00",
      "k": "gate",
      "g": "G2",
      "ok": true,
      "found": 0,
      "fixed": 0,
      "deferred": 0
    },
    {
      "t": "2026-11-09T22:22:02+03:00",
      "k": "stage",
      "id": "plan",
      "act": "start"
    },
    {
      "t": "2026-11-09T22:22:03+03:00",
      "k": "tier",
      "v": "T0"
    },
    {
      "t": "2026-11-09T22:22:04+03:00",
      "k": "tickets",
      "n": 1
    },
    {
      "t": "2026-11-09T22:22:05+03:00",
      "k": "gate",
      "g": "G3",
      "ok": false,
      "problems": 1
    },
    {
      "t": "2026-11-09T22:22:08+03:00",
      "k": "stage",
      "id": "build",
      "act": "start"
    },
    {
      "t": "2026-11-09T22:22:08+03:00",
      "k": "ticket",
      "ids": [
        "01"
      ],
      "act": "start"
    },
    {
      "t": "2026-11-09T22:22:16+03:00",
      "k": "tickets",
      "n": 1
    },
    {
      "t": "2026-11-09T22:22:17+03:00",
      "k": "gate",
      "g": "G3",
      "ok": true,
      "problems": 0
    },
    {
      "t": "2026-11-09T22:29:19+03:00",
      "k": "ticket",
      "ids": [
        "01"
      ],
      "act": "done",
      "tests": {
        "passed": 53,
        "failed": 0
      }
    },
    {
      "t": "2026-11-09T22:29:19+03:00",
      "k": "stage",
      "id": "review",
      "act": "start"
    },
    {
      "t": "2026-11-09T22:32:05+03:00",
      "k": "stage",
      "id": "final",
      "act": "start"
    },
    {
      "t": "2026-11-09T22:32:05+03:00",
      "k": "gate",
      "g": "G4",
      "ok": false,
      "checked": 3,
      "matched": 2
    },
    {
      "t": "2026-11-09T22:32:06+03:00",
      "k": "tests",
      "passed": 53,
      "failed": 0
    },
    {
      "t": "2026-11-09T22:32:25+03:00",
      "k": "add",
      "key": "report",
      "n": 1
    },
    {
      "t": "2026-11-10T12:17:51+03:00",
      "k": "gate",
      "g": "G1",
      "ok": true,
      "open": 0,
      "total": 6
    },
    {
      "t": "2026-11-10T12:17:51+03:00",
      "k": "stage",
      "id": "spec",
      "act": "start"
    },
    {
      "t": "2026-11-10T12:18:51+03:00",
      "k": "tickets",
      "n": 2
    },
    {
      "t": "2026-11-10T12:18:52+03:00",
      "k": "gate",
      "g": "G3",
      "ok": true,
      "problems": 0
    },
    {
      "t": "2026-11-10T12:19:24+03:00",
      "k": "gate",
      "g": "G2",
      "ok": true,
      "found": 0,
      "fixed": 0,
      "deferred": 0
    },
    {
      "t": "2026-11-10T12:19:26+03:00",
      "k": "stage",
      "id": "plan",
      "act": "start"
    },
    {
      "t": "2026-11-10T12:19:27+03:00",
      "k": "tickets",
      "n": 2
    },
    {
      "t": "2026-11-10T12:19:28+03:00",
      "k": "gate",
      "g": "G3",
      "ok": true,
      "problems": 0
    }
  ],
  "reqList": [
    {
      "id": "R01",
      "text": "«Посмотри на ошибки»",
      "status": "done"
    },
    {
      "id": "R02",
      "text": "«проверь по нашему»",
      "status": "done"
    },
    {
      "id": "R03",
      "text": "«реши проблемы»",
      "status": "in-ticket"
    },
    {
      "id": "G01",
      "text": "«с этим тоже разберись»",
      "status": "in-ticket"
    },
    {
      "id": "G02",
      "text": "«с этим тоже разберись»",
      "status": "in-ticket"
    },
    {
      "id": "G03",
      "text": "«а потом публикуй»",
      "status": "in-ticket"
    }
  ],
  "gates": {
    "G1": {
      "ok": true,
      "at": "2026-11-10T12:17:51+03:00",
      "open": 0,
      "total": 6
    },
    "G2": {
      "ok": true,
      "at": "2026-11-10T12:19:24+03:00",
      "found": 0,
      "fixed": 0,
      "deferred": 0
    },
    "G3": {
      "ok": true,
      "at": "2026-11-10T12:19:28+03:00",
      "problems": 0
    },
    "G4": {
      "ok": false,
      "at": "2026-11-09T22:32:05+03:00",
      "checked": 3,
      "matched": 2
    }
  },
  "result": null,
  "report": [
    "Исходники приняты; live deployment ожидает согласования конкретного массового пакета"
  ]
}
