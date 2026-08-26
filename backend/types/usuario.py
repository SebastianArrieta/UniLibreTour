from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Usuario:
    id: int
    nombre: str
    email: str
    rol: str
    created_at: datetime | None = None

    def to_dict(self):
        d = asdict(self)
        if d['created_at']:
            d['created_at'] = d['created_at'].isoformat()
        return d
