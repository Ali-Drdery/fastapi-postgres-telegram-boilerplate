"""
Imported exclusively by alembic/env.py.

Alembic's autogenerate needs every model to be imported at least once so
they register themselves on `Base.metadata`. Keeping that aggregation here
(instead of inside app/db/base.py) avoids a circular import, since models
import `Base` from app.db.base, not from this module.

When you add a new model, import it here too:
    from app.models.new_model import NewModel  # noqa: F401
"""

from app.db.base import Base  # noqa: F401
from app.models.user import User  # noqa: F401
