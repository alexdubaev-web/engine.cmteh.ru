window.STATE =
{
  "version": 2,
  "slug": "checksite-fixes",
  "dir": "2026-11-09-checksite-fixes--wip",
  "title": "Проверка замечаний checksite.ru",
  "mode": "semi",
  "depth": "normal",
  "tier": "T0",
  "briefFile": "2026-11-09-brief.md",
  "memoryFile": "AGENTS.md",
  "memoryOwner": "user",
  "skillDir": "C:/Users/Alexandr/.codex/skills/autopilot",
  "baseCommit": null,
  "startedAt": "2026-11-09T22:19:15+03:00",
  "updatedAt": "2026-11-09T22:22:05+03:00",
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
      "finishedAt": "2026-11-09T22:22:02+03:00"
    },
    {
      "id": "plan",
      "status": "active",
      "startedAt": "2026-11-09T22:22:02+03:00"
    },
    {
      "id": "build",
      "status": "pending"
    },
    {
      "id": "review",
      "status": "pending"
    },
    {
      "id": "final",
      "status": "pending"
    }
  ],
  "requirements": {
    "total": 3,
    "done": 0,
    "inTicket": 3,
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
      "zone": [],
      "review": "нет",
      "model": "обычная",
      "status": "pending",
      "retries": 0,
      "repairs": 0
    }
  ],
  "tests": null,
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
  "blind": null,
  "beats": [
    "2026-11-09T22:19:15+03:00",
    "2026-11-09T22:19:46+03:00",
    "2026-11-09T22:19:47+03:00",
    "2026-11-09T22:19:48+03:00",
    "2026-11-09T22:21:18+03:00",
    "2026-11-09T22:22:02+03:00",
    "2026-11-09T22:22:03+03:00",
    "2026-11-09T22:22:04+03:00",
    "2026-11-09T22:22:05+03:00"
  ],
  "rev": 11,
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
    }
  ],
  "reqList": [
    {
      "id": "R01",
      "text": "«Посмотри на ошибки»",
      "status": "in-ticket"
    },
    {
      "id": "R02",
      "text": "«проверь по нашему»",
      "status": "in-ticket"
    },
    {
      "id": "R03",
      "text": "«реши проблемы»",
      "status": "in-ticket"
    }
  ],
  "gates": {
    "G1": {
      "ok": true,
      "at": "2026-11-09T22:21:18+03:00",
      "open": 0,
      "total": 3
    },
    "G2": {
      "ok": true,
      "at": "2026-11-09T22:22:02+03:00",
      "found": 0,
      "fixed": 0,
      "deferred": 0
    },
    "G3": {
      "ok": false,
      "at": "2026-11-09T22:22:05+03:00",
      "problems": 1
    }
  },
  "result": null
}
