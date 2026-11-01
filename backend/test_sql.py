
from app import app

with app.test_client() as client:
    with open("sample.sql", "rb") as sql_file:
        response = client.post(
            "/analyze-sql",
            data={"sql_file": (sql_file, "sample.sql")},
            content_type="multipart/form-data"
        )

    print("Status code:", response.status_code)
    print(response.get_json())
