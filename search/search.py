from typing import List, Dict

from lunr import lunr
from lunr.index import Index


class Search:
    """
    A class used to perform search operations on a given dataset using the lunr library.
    The search index is created on the initialization of the class instance.

    Attributes
    ----------
    idx : lunr.Index
        The lunr search index.

    Methods
    -------
    search(self, q: str) -> List[str]
        Performs a search operation on the indexed data and returns the matching IDs.

    """

    idx: Index

    def __init__(self, data: List[Dict], fields_to_search: List[str], id_field: str):
        """
        Initializes the Search object by creating the search index on the given data using
        the specified fields and id field.

        Parameters
        ----------
        data- List[Dict]
        fields_to_search: List[str]
        id_field: str
        """
        self.idx = lunr(ref=id_field, fields=fields_to_search, documents=data)

    def search(self, q: str) -> List[str]:
        """
        Performs a search operation on the indexed data using the given query 'q'.
        Returns the IDs of the matching records.

        Parameters
        ----------
        q- str

        Returns
        -------
        matching_ids - List[str]
        """
        result = self.idx.search(q)
        matching_ids = [value for dictionary in result for key, value in dictionary.items() if key == 'ref']
        return matching_ids
