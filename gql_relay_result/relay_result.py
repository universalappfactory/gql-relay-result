# Copyright (c) 2020 UniversalAppFactory

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import asyncio
import traceback
PAGEINFO_TOKEN = "pageInfo"
STARTCURSOR_TOKEN = "startCursor"
ENDCURSOR_TOKEN = "endCursor"
HASNEXTPAGE_TOKEN = "hasNextPage"
HASPREVIOUSPAGE_TOKEN = "hasPreviousPage"
EDGES_TOKEN = "edges"
AFTER_PARAM = "after"

class PageInfo:
    
    def __init__(self, startCursor, endCursor, hasNextPage, hasPreviousPage) -> None:
        self.start_cursor = startCursor
        self.end_cursor = endCursor
        self.has_next = hasNextPage
        self.has_prev = hasPreviousPage

    @staticmethod
    def empty():
        return PageInfo(None, None, False, False)

    @staticmethod
    def create(data):
        if len(data) == 0:
            return PageInfo.empty()

        if (type(data) == list):
            return PageInfo.empty()

        keys = list(data.keys())
        page_info = data[keys[0]][PAGEINFO_TOKEN]
        return PageInfo(page_info[STARTCURSOR_TOKEN], page_info[ENDCURSOR_TOKEN], page_info[HASNEXTPAGE_TOKEN], page_info[HASPREVIOUSPAGE_TOKEN])                


class DataFactory:

    @staticmethod
    def from_result(result) -> list:
        if result is not None:
            keys = list(result.keys())
            data_key = next(k for k in keys if k != PAGEINFO_TOKEN)
            return result[data_key][EDGES_TOKEN]
        else:
            return []

    @staticmethod
    def from_list(items) -> list:
        return items if items is not None else []

class IterableResult:
    
    def __init__(self, result, factory=None, is_async_factory=False) -> None:
        self._index = -1
        self._factory = factory
        self._parse_result(result)
        self._is_async_factory = is_async_factory

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.next()

    def __getitem__(self, index):
        return self._create_item(index)

    def _create_item(self, index):
        if self._factory is not None:
            if self._is_async_factory:
                return asyncio.run(self._factory(self._data[index]))
            
            return self._factory(self._data[index])

        return self._data[index]

    async def _create_item_async(self, index):
        if self._factory is not None:
            return await self._factory(self._data[index])

        return self._data[index]

    def _parse_result(self, result):
        self._pageInfo = PageInfo.create(result)
        self._data = None if len(result) == 0 else DataFactory.from_result(result)

    def _get_params(self):
        params = dict(self._params)
        params[AFTER_PARAM] = self._pageInfo.end_cursor
        return params

    async def _fetch_next_chunk(self):
        after = self._pageInfo.end_cursor
        params = self._get_params()

        try:
            result = await self._executor(self._query, params)
            self._parse_result(result)
        except Exception:
            traceback.print_exc() 
            raise StopAsyncIteration

    async def next(self):
        self._index += 1
        if (self._index < len(self._data)):
            if self._is_async_factory:
                return await self._create_item_async(self._index)

            return self._create_item(self._index)         
        
        if self._pageInfo.has_next:
            self._index = -1
            self._data = []
            await self._fetch_next_chunk()
            return await self.next()
        
        self._index = -1
        raise StopAsyncIteration

    @staticmethod
    async def fetch_all(iterable) -> list:
        result = []
        async for x in iterable:
            result.append(x)

        return result


class GqlRelayResult(IterableResult):

    def __init__(self, result, query, params, executor, factory=None, is_async_factory=False) -> None:
        super(GqlRelayResult, self).__init__(result, factory, is_async_factory)
        self._query = query
        self._params = params
        self._executor = executor

    async def _fetch_next_chunk(self):
        after = self._pageInfo.end_cursor
        params = self._get_params()

        try:
            result = await self._executor(self._query, params)
            self._parse_result(result)
        except Exception:
            traceback.print_exc()
            raise StopAsyncIteration

    """
    returns all items from current page while the items are created by a synchronous factory method
    """
    def all_from_current_page(self) -> list:
        result = []
        for index in range(len(self._data)):
            result.append(self._create_item(index))
        
        return result

    """
    returns all items from current page while the items are created by a async factory method
    """
    async def all_from_current_page_async(self) -> list:
        result = []
        for index in range(len(self._data)):
            item = await self._create_item_async(index)
            result.append(item)
        
        return result


class SubResult(IterableResult):
        
    def __init__(self, result, resolver, params, factory=None, is_async_factory=False, resolver_returns_complete_objects=False) -> None:
        """Create a new instance

        Keyword arguments:
        result -- contains the raw result
        resolver -- contains a resolver method to fetch all missing items
        params -- this params will be passed to the resolver method by dictionary unpacking
        factory -- a factory method to create objects from the raw result
        is_async_factory -- set this to true if the factory method is async
        resolver_returns_complete_objects -- if the resolver already returns a complete list of objects created by a factory method you can set this to true in order to prevent object create by the factory again
        """
        super(SubResult, self).__init__(result, factory, is_async_factory)
        self._params = params
        self._resolver = resolver
        self._resolver_returns_complete_objects = resolver_returns_complete_objects

    async def _fetch_next_chunk(self):
        after = self._pageInfo.end_cursor

        try:
            p = dict(self._params)
            p["after"] = after
            
            items = await self._resolver(**p)
            self._data = DataFactory.from_list(items)
            self._pageInfo = PageInfo.empty()

            if self._resolver_returns_complete_objects:
                self._factory = None 
        except Exception:
            traceback.print_exc()
            raise StopAsyncIteration

    @staticmethod
    async def get_all_children_from_node(dict, node_name, params, resolver_method, factory_method, is_async_factory=False , resolver_returns_complete_objects=False):
        children = []
        if node_name in dict:
            x = {
                node_name: dict.pop(node_name)
            }
            return await IterableResult.fetch_all(SubResult(x, resolver_method, params, factory_method, is_async_factory, resolver_returns_complete_objects))
        
        return children


    
