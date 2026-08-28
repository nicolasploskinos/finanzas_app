"""Login y registro: son los endpoints donde un bug se traduce directo en
'cualquiera entra a la cuenta de cualquiera', así que son los que más vale
la pena tener cubiertos."""
from werkzeug.security import generate_password_hash

import montor_server as app_module


def test_login_usuario_inexistente_no_filtra_informacion(client, fake_db):
    fake_db.tables["usuarios"] = []  # nadie se llama así

    r = client.post("/api/montor/login",
                     json={"username": "fantasma", "password": "loquesea"})

    assert r.status_code == 401
    body = r.get_json()
    assert body["ok"] is False
    # El mensaje tiene que ser el mismo código genérico tanto si el usuario
    # no existe como si existe pero la contraseña está mal, para no
    # confirmarle a un atacante qué usuarios son válidos.
    assert body["error"] == "invalid_credentials"


def test_login_contrasena_incorrecta(client, fake_db):
    fake_db.tables["usuarios"] = [{
        "id": "u1", "username": "nico",
        "password_hash": generate_password_hash("laposta123"),
    }]

    r = client.post("/api/montor/login",
                     json={"username": "nico", "password": "cualquiercosa"})

    assert r.status_code == 401
    assert r.get_json()["error"] == "invalid_credentials"


def test_login_se_bloquea_al_sexto_intento_fallido(client, fake_db):
    fake_db.tables["usuarios"] = [{
        "id": "u1", "username": "nico",
        "password_hash": generate_password_hash("laposta123"),
    }]

    for _ in range(5):
        r = client.post("/api/montor/login",
                         json={"username": "nico", "password": "mal"})
        assert r.status_code == 401

    r = client.post("/api/montor/login",
                     json={"username": "nico", "password": "mal"})
    assert r.status_code == 429
    assert r.get_json()["error"] == "too_many_attempts"

    # Ni siquiera con la contraseña correcta se entra mientras dure el bloqueo.
    r = client.post("/api/montor/login",
                     json={"username": "nico", "password": "laposta123"})
    assert r.status_code == 429


def test_login_exitoso_resetea_el_contador_de_intentos(client, fake_db):
    fake_db.tables["usuarios"] = [{
        "id": "u1", "username": "nico",
        "password_hash": generate_password_hash("laposta123"),
    }]

    for _ in range(4):
        client.post("/api/montor/login", json={"username": "nico", "password": "mal"})

    r = client.post("/api/montor/login",
                     json={"username": "nico", "password": "laposta123"})
    assert r.status_code == 200

    assert "nico" not in app_module._login_intentos


def test_login_correcto_abre_sesion(client, fake_db):
    fake_db.tables["usuarios"] = [{
        "id": "u1", "username": "nico",
        "password_hash": generate_password_hash("laposta123"),
    }]

    r = client.post("/api/montor/login",
                     json={"username": "nico", "password": "laposta123"})

    assert r.status_code == 200
    assert r.get_json() == {"ok": True}
    with client.session_transaction() as sess:
        assert sess["user_id"] == "u1"
        assert sess["username"] == "nico"


def test_register_campos_faltantes(client, fake_db):
    r = client.post("/api/montor/register", json={"username": "", "password": ""})

    assert r.status_code == 400
    assert r.get_json()["error"] == "missing_fields"


def test_register_password_muy_corta(client, fake_db):
    r = client.post("/api/montor/register",
                     json={"username": "nico", "password": "corta1"})

    assert r.status_code == 400
    assert r.get_json()["error"] == "weak_password"


def test_register_usuario_ya_existe(client, fake_db):
    fake_db.tables["usuarios"] = [{"id": "u1"}]  # el select por username lo encuentra

    r = client.post("/api/montor/register",
                     json={"username": "nico", "password": "algo12345"})

    assert r.status_code == 400
    assert r.get_json()["error"] == "username_taken"


def test_register_exitoso_no_guarda_email(client, fake_db):
    # Vacío = "no existe ese username todavía", pasa la validación. El
    # insert que sigue es una consulta aparte (ver FakeQuery en conftest):
    # se le hace eco automáticamente a lo que se le mandó insertar.
    fake_db.tables["usuarios"] = []
    fake_db.tables["transacciones"] = []

    r = client.post("/api/montor/register",
                     json={"username": "nico_nuevo", "password": "algo12345"})

    assert r.status_code == 201
    assert r.get_json() == {"ok": True}

    # Regresión del fix de esta sesión: la columna email se borró de la
    # base, así que el insert no puede seguir mandándola.
    insert_calls = [
        call for (tabla, q) in fake_db.queries if tabla == "usuarios"
        for call in q.calls if call[0] == "insert"
    ]
    assert len(insert_calls) == 1
    payload = insert_calls[0][1][0]
    assert "email" not in payload

    # Regresión: el registro no debe reclamar transacciones huérfanas
    # (user_id nulo) para la cuenta recién creada - ver fix de esta sesión.
    assert not any(tabla == "transacciones" for (tabla, _q) in fake_db.queries)
    assert payload["username"] == "nico_nuevo"
