"""Assemble content/curriculum.json from the stage data modules.

Adds stable ids, per-stage/module totals, and a `hasContent` flag for every
lesson based on whether content/lessons/<id>.json exists.
"""
import json
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from stages_a import STAGES_A  # noqa: E402
from stages_b import STAGES_B  # noqa: E402

LESSONS_DIR = os.path.join(ROOT, "content", "lessons")


def main():
    stages_out = []
    total_lessons = 0
    total_minutes = 0
    authored = 0

    for si, stage in enumerate(STAGES_A + STAGES_B, start=1):
        sid = f"s{si}"
        modules_out = []
        s_lessons = 0
        s_minutes = 0

        for mi, mod in enumerate(stage["modules"], start=1):
            mid = f"{sid}-m{mi}"
            lessons_out = []
            for li, lesson in enumerate(mod["lessons"], start=1):
                lid = f"{mid}-l{li}"
                has_content = os.path.isfile(os.path.join(LESSONS_DIR, f"{lid}.json"))
                item = {
                    "id": lid,
                    "title": lesson["title"],
                    "titleEn": lesson["title_en"],
                    "summary": lesson["summary"],
                    "minutes": lesson["minutes"],
                    "kind": lesson["kind"],
                    "objectives": lesson["objectives"],
                    "resources": lesson["resources"],
                    "hasContent": has_content,
                }
                lessons_out.append(item)
                s_lessons += 1
                s_minutes += lesson["minutes"]
                if has_content:
                    authored += 1
            modules_out.append({
                "id": mid,
                "title": mod["title"],
                "titleEn": mod["title_en"],
                "summary": mod["summary"],
                "lessons": lessons_out,
                "lessonCount": len(lessons_out),
                "minutes": sum(l["minutes"] for l in lessons_out),
            })

        stages_out.append({
            "id": sid,
            "index": si,
            "title": stage["title"],
            "titleEn": stage["title_en"],
            "summary": stage["summary"],
            "outcome": stage["outcome"],
            "level": stage["level"],
            "weeks": stage["weeks"],
            "modules": modules_out,
            "lessonCount": s_lessons,
            "minutes": s_minutes,
            "hours": round(s_minutes / 60, 1),
        })
        total_lessons += s_lessons
        total_minutes += s_minutes

    curriculum = {
        "meta": {
            "title": "مسار .NET: من بعد EF Core لحد الوظيفة",
            "titleEn": "The .NET Track: From Post-EF Core to Hired",
            "tagline": "مسار عملي مبني على رودماب .NET الحديث — دروس، مهام كود، اختبارات ذاتية، ومشاريع مرحلة، بدون تسجيل دخول، والتقدّم محفوظ على جهازك.",
            "target": ".NET 10 (LTS) · C# 14 · EF Core 10 · ASP.NET Core 10 · Aspire 13",
            "updatedAt": date.today().isoformat(),
            "version": "1.0.0",
            "entryPoint": "بعد ما تكون خلصت: C# → OOP → LINQ → ASP.NET Core Web API → Entity Framework Core",
            "prerequisites": [
                "C# والأساسيات (types، collections، LINQ، async/await بشكل مبدئي)",
                "بناء Web API بسيط بـASP.NET Core (controllers أو minimal APIs)",
                "EF Core: DbContext، Migrations، العلاقات، واستعلامات LINQ",
                "Git وأساسيات سطر الأوامر",
            ],
            "sources": [
                {"label": "roadmap.sh — .NET", "url": "https://roadmap.sh/dotnet"},
                {"label": ".NET Developer Roadmap 2026 (milanm)", "url": "https://github.com/milanm/DotNet-Developer-Roadmap"},
                {"label": "ASP.NET Core Developer Roadmap", "url": "https://github.com/MoienTajik/AspNetCore-Developer-Roadmap"},
                {"label": "Microsoft Learn — .NET architecture guides", "url": "https://learn.microsoft.com/dotnet/architecture/"},
                {"label": "What's new in .NET 10 (Microsoft)", "url": "https://learn.microsoft.com/dotnet/core/whats-new/dotnet-10/overview"},
                {"label": "Azure Architecture Center — patterns", "url": "https://learn.microsoft.com/azure/architecture/patterns/"},
            ],
            "stats": {
                "stages": len(stages_out),
                "modules": sum(len(s["modules"]) for s in stages_out),
                "lessons": total_lessons,
                "minutes": total_minutes,
                "hours": round(total_minutes / 60, 1),
                "authoredLessons": authored,
                "capstones": sum(
                    1 for s in stages_out for m in s["modules"] for l in m["lessons"] if l["kind"] == "capstone"
                ),
            },
            "kinds": {
                "lesson": "درس: شرح + كود + نقاط تحقق",
                "lab": "تمرين عملي موقوت أو معمل",
                "quiz": "بنك أسئلة واختبار ذاتي",
                "capstone": "مشروع المرحلة: يُقيَّم بمعايير قبول",
            },
        },
        "stages": stages_out,
    }

    out_path = os.path.join(ROOT, "content", "curriculum.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(curriculum, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    st = curriculum["meta"]["stats"]
    print(f"curriculum.json written: {st['stages']} stages, {st['modules']} modules, "
          f"{st['lessons']} lessons ({st['hours']}h), {st['authoredLessons']} authored, "
          f"{st['capstones']} capstones -> {out_path}")


if __name__ == "__main__":
    main()
