def test_get_properties(properties, authenticated_client):
    response = authenticated_client.get("/properties?q=Main")
    assert response.status_code == 200
    data = response.json()
    assert data
    for item in data:
        assert item['address']['street_name'] == "Main"


def test_get_listings_endpoint(properties, authenticated_client):
    first_id = properties[0].property_id
    response = authenticated_client.get(f'/listings/{first_id}')
    assert response.status_code == 200
    data = response.json()
    assert data

    for listings in data:
        assert listings['property_id'] == first_id


def test_tax_endpoint(testing_db, properties, authenticated_client):
    first_id = properties[0].property_id
    response = authenticated_client.get(f'/taxes/{first_id}')
    assert response.status_code == 200
    data = response.json()
    assert data

    for tax in data:
        assert tax['property_id'] == first_id
        assert tax['year']
