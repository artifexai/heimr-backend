from search import Search

data = [
    {'property_id': 1, 'full_address': '123 Main St, San Francisco, CA 94105'},
    {'property_id': 2, 'full_address': '456 Some Boulevard, San Francisco, CA 94105'},
]


def test_search():
    idx = Search(data=data, fields_to_search=['full_address'], id_field='property_id')
    res = idx.search('123 Main St')
    assert res

    res = idx.search('San Francisco')
    assert len(res) == 2
    assert set(res) == {'1', '2'}

    res = idx.search('Gold Leaf')
    assert len(res) == 0
