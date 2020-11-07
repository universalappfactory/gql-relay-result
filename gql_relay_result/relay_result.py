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
    def create(data):
        keys = list(data.keys())
        page_info = data[keys[0]][PAGEINFO_TOKEN]
        return PageInfo(page_info[STARTCURSOR_TOKEN], page_info[ENDCURSOR_TOKEN], page_info[HASNEXTPAGE_TOKEN], page_info[HASPREVIOUSPAGE_TOKEN])                


class DataChunk:

    def __init__(self, result=None) -> None:
        if result is not None:
            keys = list(result.keys())
            data_key = next(k for k in keys if k != PAGEINFO_TOKEN)
            self._data = result[data_key][EDGES_TOKEN]
        else:
            self._data = []

    def __getitem__(self, items):
        return self._data[items]

    def len(self):
        return len(self._data)


class GqlRelayResult:

    def __init__(self, result, query, params, executor, factory=None) -> None:
        self._index = -1
        self._query = query
        self._params = params
        self._executor = executor
        self._factory = factory
        self._parse_result(result)

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.next()

    def __getitem__(self, index):
        if self._factory is not None:
            return self._factory(self._data[index])

        return self._data[index]

    def _parse_result(self, result):
        self._pageInfo = PageInfo.create(result)
        self._data = DataChunk(result)

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
        except Exception as x:
            print(x)
            raise StopAsyncIteration

    async def next(self):
        self._index += 1
        if (self._index < self._data.len()):
            return self[self._index]              
        
        if self._pageInfo.has_next:
            self._index = -1
            self._data = DataChunk()
            await self._fetch_next_chunk()
            return await self.next()
        
        self._index = -1
        raise StopAsyncIteration