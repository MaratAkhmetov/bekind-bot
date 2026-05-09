import csv
from app.database.db import get_connection, init_db

CSV_PATH = "app/database/seed/initiatives.csv"


def import_csv():
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    with open(CSV_PATH, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            cursor.execute("""
                INSERT INTO initiatives (
                    name, category, tags, help_types,
                    practical_help, website, instagram,
                    facebook, description, city, source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["name"],
                row["category"],
                row.get("tags", ""),
                row.get("help_types", ""),
                row.get("practical_help", ""),
                row.get("website", ""),
                row.get("instagram", ""),
                row.get("facebook", ""),
                row.get("description", ""),
                row.get("city", ""),
                row.get("source", "")
            ))

    conn.commit()
    conn.close()

    print("Import completed successfully")


if __name__ == "__main__":
    import_csv()