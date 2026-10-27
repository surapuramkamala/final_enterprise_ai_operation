
import sqlite3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("IncidentDatabase")

DB_PATH = "incidents.db"


def initialize_database():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id TEXT PRIMARY KEY,
                description TEXT,
                status TEXT,
                resolution TEXT
            )
        """)

        conn.execute("""
            INSERT OR IGNORE INTO incidents
            VALUES (
                'INC-101',
                'Production login failure',
                'Resolved',
                'Expired authentication token was renewed'
            )
        """)


@mcp.tool()
def search_incidents(keyword: str) -> list[dict]:
    """Search incident records by keyword."""
    initialize_database()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT incident_id, description, status, resolution
            FROM incidents
            WHERE incident_id LIKE ?
               OR description LIKE ?
            LIMIT 10
        """, (f"%{keyword}%", f"%{keyword}%")).fetchall()

        return [dict(row) for row in rows]


if __name__ == "__main__":
    mcp.run()
