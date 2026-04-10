from flask import current_app
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from models import db
from models.score import Score
from models.team import Team


def get_live_scoreboard_rows():
    total_score = func.coalesce(func.sum(Score.weighted_score), 0).label("total_score")

    try:
        rows = (
            db.session.query(
                Team.id,
                Team.team_name,
                Team.theme,
                total_score,
            )
            .outerjoin(Score, Score.team_id == Team.id)
            .filter(Team.is_active.is_(True))
            .group_by(Team.id, Team.team_name, Team.theme)
            .order_by(total_score.desc(), Team.team_name.asc())
            .all()
        )
    except SQLAlchemyError as exc:
        current_app.logger.warning("Scoreboard query unavailable: %s", exc)
        return []

    return [
        {
            "rank": index,
            "team_name": row.team_name,
            "theme": row.theme,
            "total_score": float(row.total_score or 0.0),
        }
        for index, row in enumerate(rows, start=1)
    ]
