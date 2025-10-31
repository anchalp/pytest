import requests
import uuid

BASE_URL = "http://127.0.0.1:5000/artists"

def make_unique_name():
    """Generate a unique first name for testing."""
    return f"Test{str(uuid.uuid4())[:8]}"

def api_post_artist(first_name: str | None = None, last_name: str = "Artist", birth_year: str | int = "2000"):
    """Create an artist and return (user_id, payload)."""
    if not first_name:
        first_name = make_unique_name()
    # Always convert birth_year to string for API
    payload = {"first_name": first_name, "last_name": last_name, "birth_year": str(birth_year)}
    resp = requests.post(BASE_URL, json=payload)
    assert resp.status_code == 200, f"POST /artists failed: {resp.text}"
    return str(resp.json()), payload

def api_get_artist(user_id=None):
    return requests.get(f"{BASE_URL}/{user_id}" if user_id else BASE_URL)

def api_delete_artist(user_id):
    return requests.delete(f"{BASE_URL}/{user_id}")

def api_update_artist(user_id, first_name, last_name, birth_year):
    payload = {"user_id": user_id, "first_name": first_name, "last_name": last_name, "birth_year": birth_year}
    return requests.put(BASE_URL, json=payload)

def delete_artists(*artist_ids):
    """Delete one or multiple artist IDs."""
    for uid in artist_ids:
        api_delete_artist(uid)


#CRUD Tests

def test_get_artists():
    resp = api_get_artist()
    data = resp.json()
    assert resp.status_code == 200
    assert isinstance(data, list)

def test_create_artist():
    user_id, payload = api_post_artist()
    resp = api_get_artist(user_id)
    assert resp.status_code == 200
    data = resp.json()
    if isinstance(data, dict):
        for key, value in payload.items():
            assert str(data.get(key)) == str(value)
    delete_artists(user_id)

def test_create_artist_missing_fields():
    resp = requests.post(BASE_URL, json={"first_name": "Alan"})
    assert resp.status_code == 400

def test_get_artist_by_id():
    user_id, payload = api_post_artist()
    resp = api_get_artist(user_id)
    assert resp.status_code == 200
    data = resp.json()
    if isinstance(data, dict):
        for key, value in payload.items():
            assert str(data.get(key)) == str(value)
    delete_artists(user_id)

def test_update_artist():
    user_id, payload = api_post_artist()
    resp = api_update_artist(user_id, "UpdatedName", payload["last_name"], payload["birth_year"])
    assert resp.status_code == 200

    verify = api_get_artist(user_id)
    assert verify.status_code == 200
    data = verify.json()
    if isinstance(data, dict):
        assert data.get("first_name") == "UpdatedName"
    delete_artists(user_id)

def test_delete_artist():
    user_id, _ = api_post_artist()
    del_resp = api_delete_artist(user_id)
    assert del_resp.status_code == 200

    get_resp = api_get_artist(user_id)
    assert get_resp.status_code == 404

# Negative Tests

def test_create_artist_empty_strings():
    resp = requests.post(BASE_URL, json={"first_name": "", "last_name": "", "birth_year": ""})
    assert resp.status_code == 400

def test_create_artist_invalid_birth_year():
    resp = requests.post(BASE_URL, json={"first_name": "Bad", "last_name": "Input", "birth_year": "not_a_number"})
    assert resp.status_code in (400, 422)

def test_get_nonexistent_artist():
    resp = api_get_artist("99999")
    assert resp.status_code == 404

def test_delete_nonexistent_artist():
    resp = api_delete_artist("99999")
    assert resp.status_code in (200, 404)

def test_update_missing_fields():
    user_id, _ = api_post_artist()
    resp = requests.put(BASE_URL, json={"user_id": user_id, "first_name": "NewName"})
    assert resp.status_code == 400
    delete_artists(user_id)

def test_update_invalid_types():
    user_id, _ = api_post_artist()
    resp = api_update_artist(user_id, 123, 456, "year")
    assert resp.status_code in (400, 422)
    delete_artists(user_id)

def test_duplicate_artist():
    name = make_unique_name()
    user_id1, _ = api_post_artist(first_name=name)
    resp = requests.post(BASE_URL, json={"first_name": name, "last_name": "Artist", "birth_year": "2000"})
    assert resp.status_code in (200, 400)
    delete_artists(user_id1)

def test_invalid_url():
    resp = requests.get("http://127.0.0.1:5000/invalid_endpoint")
    assert resp.status_code == 404


def test_create_artist_long_names():
    long_name = "A" * 500
    user_id, _ = api_post_artist(first_name=long_name, last_name=long_name, birth_year="1990")
    if user_id:
        resp = api_get_artist(user_id)
        assert resp.status_code == 200
        data = resp.json()
        if isinstance(data, dict):
            assert data.get("first_name") == long_name
        delete_artists(user_id)

def test_invalid_http_method():
    resp = requests.patch(BASE_URL, json={"foo": "bar"})
    assert resp.status_code in (400, 405)

def test_create_artist_birth_year_as_int():
    user_id, _ = api_post_artist(first_name="John", last_name="Doe", birth_year=1985)
    resp = api_get_artist(user_id)
    assert resp.status_code == 200
    data = resp.json()
    if isinstance(data, dict):
        assert data.get("birth_year") == "1985"
    delete_artists(user_id)

def test_bulk_create_and_get_all():
    # Create 3 artists
    ids = []
    for _ in range(3):
        user_id, _ = api_post_artist()
        ids.append(user_id)

    # Get all artists
    resp = api_get_artist()
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()

    # Check that all created artists exist in the response
    for uid in ids:
        assert any(str(uid) in str(d) for d in data), f"Artist {uid} not found in response"

    # Cleanup
    delete_artists(*ids)

def test_delete_artist_twice():
    user_id, _ = api_post_artist()
    first = api_delete_artist(user_id)
    second = api_delete_artist(user_id)
    assert first.status_code == 200
    assert second.status_code in (200, 404)

def test_create_with_invalid_json():
    resp = requests.post(BASE_URL, data="not-a-json", headers={"Content-Type": "application/json"})
    assert resp.status_code in (400, 415, 422)

def test_create_without_content_type():
    payload = {"first_name": "NoHeader", "last_name": "Test", "birth_year": "1999"}
    resp = requests.post(BASE_URL, data=str(payload))
    assert resp.status_code in (400, 415)

def test_get_artists_filtering_like_behavior():
    uid1, _ = api_post_artist(first_name="Alpha")
    uid2, _ = api_post_artist(first_name="Beta")
    resp = api_get_artist()
    assert resp.status_code == 200
    delete_artists(uid1, uid2)

def test_get_artists_empty_db():
    resp = api_get_artist()
    assert resp.status_code == 200

def test_update_nonexistent_artist():
    resp = api_update_artist("99999", "Anonymous", "User", "1999")
    assert resp.status_code in (400, 404)

def test_get_artist_invalid_id_format():
    resp = api_get_artist("abc")
    assert resp.status_code in (400, 404)
