from collections import defaultdict

from models import db
from models.audit import AuditLog
from models.score import SCORE_CATEGORIES, Score
from models.team import Team

CATEGORY_DEFINITIONS = (
    {
        "key": "innovation_originality",
        "label": "Innovation and Originality",
        "weight_percent": 30,
        "multiplier": 3.0,
    },
    {
        "key": "technical_implementation",
        "label": "Technical Implementation",
        "weight_percent": 30,
        "multiplier": 3.0,
    },
    {
        "key": "business_value_impact",
        "label": "Business Value and Impact",
        "weight_percent": 25,
        "multiplier": 2.5,
    },
    {
        "key": "presentation_clarity",
        "label": "Presentation and Clarity",
        "weight_percent": 15,
        "multiplier": 1.5,
    },
)

CATEGORY_COUNT = len(CATEGORY_DEFINITIONS)
CATEGORY_LABELS = {item["key"]: item["label"] for item in CATEGORY_DEFINITIONS}
CATEGORY_MULTIPLIERS = {item["key"]: item["multiplier"] for item in CATEGORY_DEFINITIONS}


def _add_audit_log(actor_user_id, action, entity_type, entity_id, old_data, new_data):
    db.session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_data=old_data,
            new_data=new_data,
        )
    )


def calculate_total_from_raw_scores(raw_scores):
    total = 0.0
    for category_key in SCORE_CATEGORIES:
        value = float(raw_scores.get(category_key, 0) or 0)
        total += value * CATEGORY_MULTIPLIERS[category_key]
    return round(total, 2)


def get_judge_team_score_snapshot(judge_id, team_id):
    rows = Score.query.filter_by(judge_id=judge_id, team_id=team_id).all()

    score_values = {category_key: None for category_key in SCORE_CATEGORIES}
    remarks = ""
    weighted_total = 0.0
    scored_categories = set()
    is_locked = False

    for row in rows:
        score_values[row.category] = float(row.raw_score)
        weighted_total += float(row.weighted_score or 0)
        scored_categories.add(row.category)
        is_locked = is_locked or bool(row.is_locked)
        if row.remarks and not remarks:
            remarks = row.remarks

    return {
        "score_values": score_values,
        "remarks": remarks,
        "categories_scored": len(scored_categories),
        "weighted_total": round(weighted_total, 2),
        "is_complete": len(scored_categories) == CATEGORY_COUNT,
        "is_locked": is_locked,
    }


def get_judge_dashboard_rows(judge_id):
    teams = Team.query.filter(Team.is_active.is_(True)).order_by(Team.id.asc()).all()
    if not teams:
        return []

    team_ids = [team.id for team in teams]
    score_rows = Score.query.filter(
        Score.judge_id == judge_id,
        Score.team_id.in_(team_ids),
    ).all()

    grouped_rows = defaultdict(list)
    for row in score_rows:
        grouped_rows[row.team_id].append(row)

    dashboard_rows = []
    for team in teams:
        team_scores = grouped_rows.get(team.id, [])
        categories_scored = len({row.category for row in team_scores})
        judge_total = round(sum(float(row.weighted_score or 0) for row in team_scores), 2)

        dashboard_rows.append(
            {
                "id": team.id,
                "team_name": team.team_name,
                "theme": team.theme,
                "project_title": team.project.project_title if team.project else "-",
                "project_summary": team.project.project_summary if team.project else "-",
                "categories_scored": categories_scored,
                "judge_total": judge_total,
                "is_completed": categories_scored == CATEGORY_COUNT,
                "is_locked": any(bool(row.is_locked) for row in team_scores),
            }
        )

    return dashboard_rows


def save_or_update_judge_scores(
    judge_id,
    team_id,
    raw_scores,
    remarks,
    actor_user_id,
    lock_after_save=False,
):
    existing_rows = Score.query.filter_by(judge_id=judge_id, team_id=team_id).all()
    if existing_rows and any(bool(row.is_locked) for row in existing_rows):
        raise ValueError("Scores are locked for this team and cannot be edited.")

    existing_by_category = {row.category: row for row in existing_rows}

    normalized_remarks = (remarks or "").strip() or None

    for category_key in SCORE_CATEGORIES:
        if category_key not in raw_scores:
            raise ValueError(f"Missing score for category: {CATEGORY_LABELS[category_key]}")

        try:
            score_value = float(raw_scores[category_key])
        except (TypeError, ValueError):
            raise ValueError(f"{CATEGORY_LABELS[category_key]} must be a valid number.")

        score_value = round(score_value, 2)

        if score_value < 0 or score_value > 10:
            raise ValueError(f"{CATEGORY_LABELS[category_key]} must be between 0 and 10.")

        row = existing_by_category.get(category_key)
        if row:
            old_data = {
                "raw_score": float(row.raw_score),
                "remarks": row.remarks,
                "is_locked": bool(row.is_locked),
            }

            row.raw_score = score_value
            row.remarks = normalized_remarks

            new_data = {
                "raw_score": score_value,
                "remarks": normalized_remarks,
                "is_locked": bool(row.is_locked),
            }

            if old_data != new_data:
                _add_audit_log(
                    actor_user_id=actor_user_id,
                    action="score_updated",
                    entity_type="score",
                    entity_id=row.id,
                    old_data=old_data,
                    new_data=new_data,
                )
        else:
            new_row = Score(
                judge_id=judge_id,
                team_id=team_id,
                category=category_key,
                raw_score=score_value,
                remarks=normalized_remarks,
                is_locked=False,
            )
            db.session.add(new_row)
            db.session.flush()

            _add_audit_log(
                actor_user_id=actor_user_id,
                action="score_created",
                entity_type="score",
                entity_id=new_row.id,
                old_data=None,
                new_data={
                    "raw_score": score_value,
                    "remarks": normalized_remarks,
                    "is_locked": False,
                    "category": category_key,
                },
            )

    if lock_after_save:
        rows_to_lock = Score.query.filter_by(judge_id=judge_id, team_id=team_id).all()
        if not rows_to_lock:
            raise ValueError("Cannot lock scores before saving all categories.")

        if any(bool(row.is_locked) for row in rows_to_lock):
            raise ValueError("Scores are already locked for this team.")

        for row in rows_to_lock:
            row.is_locked = True
            _add_audit_log(
                actor_user_id=actor_user_id,
                action="score_locked",
                entity_type="score",
                entity_id=row.id,
                old_data={"is_locked": False},
                new_data={"is_locked": True},
            )

        _add_audit_log(
            actor_user_id=actor_user_id,
            action="score_set_locked",
            entity_type="judge_team_scores",
            entity_id=team_id,
            old_data={"judge_id": judge_id, "locked": False},
            new_data={"judge_id": judge_id, "locked": True},
        )

    existing_rows_after = Score.query.filter_by(judge_id=judge_id, team_id=team_id).all()
    if len(existing_rows_after) != CATEGORY_COUNT:
        raise ValueError("All four scoring categories are required.")

    if any((float(row.raw_score) < 0 or float(row.raw_score) > 10) for row in existing_rows_after):
        raise ValueError("Scores must remain within the 0-10 range.")

    category_set = {row.category for row in existing_rows_after}
    if len(category_set) != CATEGORY_COUNT:
        raise ValueError("Duplicate category scores are not allowed.")

    db.session.flush()

    _add_audit_log(
        actor_user_id=actor_user_id,
        action="score_submission_saved",
        entity_type="judge_team_scores",
        entity_id=team_id,
        old_data=None,
        new_data={
            "judge_id": judge_id,
            "team_id": team_id,
            "remarks": normalized_remarks,
            "is_locked": bool(existing_rows_after[0].is_locked),
        },
    )

    db.session.commit()


def is_judge_team_locked(judge_id, team_id):
    return (
        Score.query.filter_by(judge_id=judge_id, team_id=team_id, is_locked=True).first()
        is not None
    )


def get_next_active_team_id(current_team_id):
    next_team = (
        Team.query.filter(Team.is_active.is_(True), Team.id > current_team_id)
        .order_by(Team.id.asc())
        .first()
    )
    if not next_team:
        return None
    return next_team.id
