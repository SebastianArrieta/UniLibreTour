from config.database import get_cursor


class UsuarioModel:
    @staticmethod
    def find_all():
        with get_cursor() as cur:
            cur.execute("SELECT id, nombre, email, rol, created_at FROM usuarios")
            rows = cur.fetchall()
            return [
                {
                    'id': r[0],
                    'nombre': r[1],
                    'email': r[2],
                    'rol': r[3],
                    'created_at': r[4].isoformat() if r[4] else None
                }
                for r in rows
            ]

    @staticmethod
    def find_by_id(usuario_id):
        with get_cursor() as cur:
            cur.execute(
                "SELECT id, nombre, email, rol, created_at FROM usuarios WHERE id = %s",
                (usuario_id,)
            )
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0],
                    'nombre': row[1],
                    'email': row[2],
                    'rol': row[3],
                    'created_at': row[4].isoformat() if row[4] else None
                }
            return None

    @staticmethod
    def create(data):
        from services.auth import hash_password
        password_hash = hash_password(data['password'])
        with get_cursor() as cur:
            cur.execute(
                """INSERT INTO usuarios (nombre, email, password_hash, rol)
                   VALUES (%s, %s, %s, %s)
                   RETURNING id, nombre, email, rol, created_at""",
                (data['nombre'], data['email'], password_hash, data.get('rol', 'visitante'))
            )
            row = cur.fetchone()
            return {
                'id': row[0],
                'nombre': row[1],
                'email': row[2],
                'rol': row[3],
                'created_at': row[4].isoformat() if row[4] else None
            }

    @staticmethod
    def update(usuario_id, data):
        with get_cursor() as cur:
            fields = []
            values = []
            for key in ('nombre', 'email', 'rol'):
                if key in data:
                    fields.append(f"{key} = %s")
                    values.append(data[key])

            if not fields:
                return None

            values.append(usuario_id)
            query = f"UPDATE usuarios SET {', '.join(fields)} WHERE id = %s RETURNING id, nombre, email, rol, created_at"
            cur.execute(query, values)
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0],
                    'nombre': row[1],
                    'email': row[2],
                    'rol': row[3],
                    'created_at': row[4].isoformat() if row[4] else None
                }
            return None

    @staticmethod
    def delete(usuario_id):
        with get_cursor() as cur:
            cur.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
            return cur.rowcount > 0
