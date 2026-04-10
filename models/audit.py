from . import db
from sqlalchemy.dialects.postgresql import JSONB


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.BigInteger, primary_key=True)
    actor_user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action = db.Column(db.String(80), nullable=False)
    entity_type = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.BigInteger, nullable=True)
    old_data = db.Column(JSONB, nullable=True)
    new_data = db.Column(JSONB, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
