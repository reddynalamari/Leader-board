from sqlalchemy import CheckConstraint, Computed, Enum, UniqueConstraint

from . import db


SCORE_CATEGORIES = (
    "innovation_originality",
    "technical_implementation",
    "business_value_impact",
    "presentation_clarity",
)


class Score(db.Model):
    __tablename__ = "scores"
    __table_args__ = (
        UniqueConstraint(
            "judge_id",
            "team_id",
            "category",
            name="uq_scores_judge_team_category",
        ),
        CheckConstraint("raw_score >= 0 AND raw_score <= 10", name="ck_scores_raw_score_range"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    judge_id = db.Column(
        db.BigInteger,
        db.ForeignKey("judges.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id = db.Column(
        db.BigInteger,
        db.ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    category = db.Column(Enum(*SCORE_CATEGORIES, name="score_category"), nullable=False)
    raw_score = db.Column(db.Numeric(4, 2), nullable=False)
    weighted_score = db.Column(
        db.Numeric(6, 2),
        Computed(
            "ROUND(CASE "
            "WHEN category = 'innovation_originality' THEN raw_score * 3.00 "
            "WHEN category = 'technical_implementation' THEN raw_score * 3.00 "
            "WHEN category = 'business_value_impact' THEN raw_score * 2.50 "
            "WHEN category = 'presentation_clarity' THEN raw_score * 1.50 "
            "END, 2)",
            persisted=True,
        ),
    )
    remarks = db.Column(db.Text, nullable=True)
    is_locked = db.Column(db.Boolean, nullable=False, default=False)
    submitted_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    judge = db.relationship("Judge", back_populates="scores")
    team = db.relationship("Team", back_populates="scores")
