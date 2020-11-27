from typing import Any
import unittest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, call
from gql_relay_result.relay_result import GqlRelayResult, SubResult, IterableResult
from gql import gql


class Data:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def create(cls, dict):
        node = dict.pop("node")
        return Data(**node)

class DataWithId:
    def __init__(self, id, value, children=None):
        self.id = id
        self.value = value
        self.children = children

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    # if your graphql api provides a query to resolve all child items by id and a 'after' cursor
    # you can use this method to query all remaining children
    # this method should probably not ne placed within the data class but for unittest readability it's here
    @classmethod
    async def get_all_children(cls, id, after):
        gqlQuery = gql(GqlRelayResultTests.QUERY)
        executor = MagicMock()

        result = GqlRelayResultTests.SINGLE_PAGE_RESULT

        params = {'id': id, 'after': after}
        return await IterableResult.fetch_all(GqlRelayResult(result, gqlQuery, params, executor))

    @classmethod
    async def create(cls, dict):
        node = dict.pop("node")

        # all these values will be passed into the 'get_all_children' method
        # and additionally the 'after' cursor which comes from the 'subElementsSet' pageInfo
        get_children_params = {"id": node["id"]}
        children = await SubResult.get_all_children_from_node(node, "subElementsSet", get_children_params, DataWithId.get_all_children, lambda x: Data.create(x))
        return DataWithId(children=children, **node)


class GqlRelayResultTests(IsolatedAsyncioTestCase):

    QUERY = """ 
            query getNumericValues($first: Int, $after: String) {
                numericValues(first: $first, after: $after) {
                    pageInfo {
                      hasNextPage,
                      hasPreviousPage,
                      startCursor,
                      endCursor
                    }
                    edges {
                        node {
                            value                          
                        }
                    }
                }
            }
            """

    SINGLE_PAGE_RESULT = {"numericvalues": {
            "edges": [
                {
                    "node": {
                        "value": 1
                    }
                }                    
            ],
            "pageInfo": {
                "startCursor": "YXJyYXljb25uZWN0aW9uOjA=",
                "endCursor": "YXJyYXljb25uZWN0aW9uOjA=",
                "hasNextPage": False,
                "hasPreviousPage": False
            }
        }}

    FIRST_PAGE_RESULT = {"numericvalues": {
            "edges": [
                {
                    "node": {
                        "value": 1
                    }
                },
                {
                    "node": {
                        "value": 2
                    },
                },
                    {
                    "node": {
                        "value": 3
                    },
                },
                {
                    "node": {
                        "value": 4
                    },
                },
                {
                    "node": {
                        "value": 5
                    }
                }
            ],
            "pageInfo": {
                "startCursor": "YXJyYXljb25uZWN0aW9uOjA=",
                "endCursor": "YXJyYXljb25uZWN0aW9uOjQ=",
                "hasNextPage": True,
                "hasPreviousPage": False
            }
        }}

    SECOND_PAGE_RESULT = {"numericvalues": {
            "edges": [
                {
                    "node": {
                        "value": 6
                    },
                },
                    {
                    "node": {
                        "value": 7
                    },
                },
                {
                    "node": {
                        "value": 8
                    }
                }
            ],
            "pageInfo": {
                "startCursor": "YXJyYXljb25uZWN0aW9uOjU=",
                "endCursor": "YXJyYXljb25uZWN0aW9uOjc=",
                "hasNextPage": False,
                "hasPreviousPage": False
            }
        }}
    
    NESTED_RESULT = {"numericvalues": {
            "edges": [
                {
                    "node": {
                        "id": "id1",
                        "value": 6,
                        "subElementsSet": {
                            "pageInfo": {
                                "hasNextPage": False,
                                "hasPreviousPage": False,
                                "startCursor": None,
                                "endCursor": None
                            },
                            "edges": []
                        },
                    },
                },
                    {
                    "node": {
                        "id": "id2",
                        "value": 7,
                        "subElementsSet": {
                            "pageInfo": {
                                "hasNextPage": False,
                                "hasPreviousPage": False,
                                "startCursor": None,
                                "endCursor": None
                            },
                            "edges": []
                        },
                    },
                },
                {
                    "node": {
                        "id": "id3",
                        "value": 8,

                        "subElementsSet": {
                            "pageInfo": {
                                "hasNextPage": True,
                                "hasPreviousPage": False,
                                "startCursor": "YXJyYXljb25uZWN0aW9uOjA=",
                                "endCursor": "YXJyYXljb25uZWN0aW9uOjA="
                            },
                            "edges": [
                                {
                                    "node": {
                                        "value": "subitem_1"
                                    }
                                },
                                {
                                    "node": {
                                        "value": "subitem_2"
                                    }
                                },
                            ]
                        },
                    }
                }
            ],
            "pageInfo": {
                "startCursor": "YXJyYXljb25uZWN0aW9uOjU=",
                "endCursor": "YXJyYXljb25uZWN0aW9uOjc=",
                "hasNextPage": False,
                "hasPreviousPage": False
            }
        }}

    def test_that_instance_can_be_created_from_valid_result(self):
        gqlQuery = gql(GqlRelayResultTests.QUERY)
        executor = MagicMock()

        result = GqlRelayResultTests.SINGLE_PAGE_RESULT

        params = {'first': 5}
        sut = GqlRelayResult(result, gqlQuery, params, executor)
        self.assertIsNotNone(sut)

    async def test_that_async_iterator_works(self):
        gqlQuery = gql(GqlRelayResultTests.QUERY)
        executor = MagicMock()
        result = GqlRelayResultTests.SINGLE_PAGE_RESULT

        params = {'first': 5}
        sut = GqlRelayResult(result, gqlQuery, params, executor)
        
        expeced = [1]
        actual = []
        async for x in sut:
            actual.append(x["node"]["value"])

        self.assertListEqual(expeced, actual)

    async def test_that_iterator_works(self):
        gqlQuery = gql(GqlRelayResultTests.QUERY)
        executor = MagicMock()
        result = GqlRelayResultTests.FIRST_PAGE_RESULT

        params = {'first': 5}
        sut = GqlRelayResult(result, gqlQuery, params, executor)
        
        expeced = [1, 2, 3, 4, 5]
        actual = []
        for x in sut:
            actual.append(x["node"]["value"])

        self.assertListEqual(expeced, actual)

    async def test_that_result_can_iterate_through_multiple_pages(self):
        gqlQuery = gql(GqlRelayResultTests.QUERY)
        executor = AsyncMock()
        result = GqlRelayResultTests.FIRST_PAGE_RESULT
        executor.return_value = GqlRelayResultTests.SECOND_PAGE_RESULT

        params = {'first': 5}
        sut = GqlRelayResult(result, gqlQuery, params, executor)
        
        expeced = [1, 2, 3, 4, 5, 6, 7, 8]
        actual = []
        async for x in sut:
            actual.append(x["node"]["value"])

        self.assertListEqual(expeced, actual)


    async def test_that_query_variables_are_replaced(self):
        gqlQuery = gql(GqlRelayResultTests.QUERY)
        executor = AsyncMock()
        result = GqlRelayResultTests.FIRST_PAGE_RESULT
        executor.return_value = GqlRelayResultTests.SECOND_PAGE_RESULT

        params = {'first': 5}
        sut = GqlRelayResult(result, gqlQuery, params, executor)
        
        actual = []
        async for x in sut:
            actual.append(x["node"]["value"])

        # after: FirstPageResult.endCursor
        calls = [call(gqlQuery, {"first": 5, "after": "YXJyYXljb25uZWN0aW9uOjQ="})] 
        executor.assert_has_awaits(calls)
    
    async def test_that_factory_method_works(self):
        gqlQuery = gql(GqlRelayResultTests.QUERY)
        executor = MagicMock()
        result = GqlRelayResultTests.FIRST_PAGE_RESULT

        params = {'first': 5}
        sut = GqlRelayResult(result, gqlQuery, params, executor, lambda node: Data(node["node"]["value"]))
        
        expeced = [Data(1), Data(2), Data(3), Data(4), Data(5)]
        actual = []
        async for x in sut:
            actual.append(x)
            self.assertIsInstance(x, Data)

        self.assertListEqual(expeced, actual)

    async def test_that_resolve_nested_items_works(self):
        gqlQuery = gql(GqlRelayResultTests.QUERY)
        executor = MagicMock()
        result = GqlRelayResultTests.NESTED_RESULT

        params = {'first': 5}
        sut = GqlRelayResult(result, gqlQuery, params, executor, lambda x: DataWithId.create(x), True)
        
        expeced = [DataWithId("id1", 6), DataWithId("id1", 7), DataWithId("id1", 8)]
        actual = []
        async for x in sut:
            actual.append(x)
            self.assertIsInstance(x, DataWithId)

        itemWithChildren = actual[2]
        self.assertListEqual(expeced, actual)
        self.assertEqual(len(itemWithChildren.children), 3)