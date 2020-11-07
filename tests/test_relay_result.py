from typing import Any
import unittest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, call
from gql_relay_result.relay_result import GqlRelayResult
from gql import gql


class Data:
    def __init__(self, data):
        self.data = data

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.data == other.data
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)



class DocfayClientTest(IsolatedAsyncioTestCase):

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

    def test_that_instance_can_be_created_from_valid_result(self):
        gqlQuery = gql(DocfayClientTest.QUERY)
        executor = MagicMock()

        result = DocfayClientTest.SINGLE_PAGE_RESULT

        params = {'first': 5}
        sut = GqlRelayResult(result, gqlQuery, params, executor)
        self.assertIsNotNone(sut)

    async def test_that_async_iterator_works(self):
        gqlQuery = gql(DocfayClientTest.QUERY)
        executor = MagicMock()
        result = DocfayClientTest.SINGLE_PAGE_RESULT

        params = {'first': 5}
        sut = GqlRelayResult(result, gqlQuery, params, executor)
        
        expeced = [1]
        actual = []
        async for x in sut:
            actual.append(x["node"]["value"])

        self.assertListEqual(expeced, actual)

    async def test_that_iterator_works(self):
        gqlQuery = gql(DocfayClientTest.QUERY)
        executor = MagicMock()
        result = DocfayClientTest.FIRST_PAGE_RESULT

        params = {'first': 5}
        sut = GqlRelayResult(result, gqlQuery, params, executor)
        
        expeced = [1, 2, 3, 4, 5]
        actual = []
        for x in sut:
            actual.append(x["node"]["value"])

        self.assertListEqual(expeced, actual)

    async def test_that_result_can_iterate_through_multiple_pages(self):
        gqlQuery = gql(DocfayClientTest.QUERY)
        executor = AsyncMock()
        result = DocfayClientTest.FIRST_PAGE_RESULT
        executor.return_value = DocfayClientTest.SECOND_PAGE_RESULT

        params = {'first': 5}
        sut = GqlRelayResult(result, gqlQuery, params, executor)
        
        expeced = [1, 2, 3, 4, 5, 6, 7, 8]
        actual = []
        async for x in sut:
            actual.append(x["node"]["value"])

        self.assertListEqual(expeced, actual)


    async def test_that_query_variables_are_replaced(self):
        gqlQuery = gql(DocfayClientTest.QUERY)
        executor = AsyncMock()
        result = DocfayClientTest.FIRST_PAGE_RESULT
        executor.return_value = DocfayClientTest.SECOND_PAGE_RESULT

        params = {'first': 5}
        sut = GqlRelayResult(result, gqlQuery, params, executor)
        
        actual = []
        async for x in sut:
            actual.append(x["node"]["value"])

        # after: FirstPageResult.endCursor
        calls = [call(gqlQuery, {"first": 5, "after": "YXJyYXljb25uZWN0aW9uOjQ="})] 
        executor.assert_has_awaits(calls)
    
    async def test_that_factory_method_works(self):
        gqlQuery = gql(DocfayClientTest.QUERY)
        executor = MagicMock()
        result = DocfayClientTest.FIRST_PAGE_RESULT

        params = {'first': 5}
        sut = GqlRelayResult(result, gqlQuery, params, executor, lambda node: Data(node["node"]["value"]))
        
        expeced = [Data(1), Data(2), Data(3), Data(4), Data(5)]
        actual = []
        for x in sut:
            actual.append(x)
            self.assertIsInstance(x, Data)

        self.assertListEqual(expeced, actual)
