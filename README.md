# gql-relayresult

gql-relayresult is a simple result datastructure for GraphQL gql queries (https://pypi.org/project/gql/, working with the latest prerelase) which supports pagination so that it's easy to iterate through all pages like this:

````
async for x in result:
    mylist.append(x["node"]["value"])

````

The result must contain pageInfo based on

https://graphql.org/learn/pagination/

# Example

Let's say you have a GraphQL query like this:

````
query = 
    """ 
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
````

Then you simply can execute the query and iterate through the resultset while the following result pages are automatically fetched when needed.

````
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql_relay_result import GqlRelayResult

transport = AIOHTTPTransport(url=url)
client = Client(transport=self._transport, fetch_schema_from_transport=True)

gqlQuery = gql(query)
params = {"first": first}
data = await client.execute_async(gqlQuery, params)

result = GqlResult(data, gqlQuery, client.execute_async)


#now you can itereate through the result

actual = []
async for x in result:
    actual.append(x["node"]["value"])

````

It's important that you work with query variables as the `after` parameter is automatically replaced by the `endCursor` provided in the `pageInfo` structure.

All other parameters won't be changed.

# Providing a factory method

If you don't want to access the resulting dictionary but create custom instances you can pass in a factory method.

````
# using a lamda to create instances of type 'Data'
result = GqlRelayResult(result, gqlQuery, params, executor, lambda x: Data(x["node"]["value"]))

for x in result:
    self.assertIsInstance(x, Data)

````

# Querying child result sets

If your resulting data has child items which can be paged as well you may use the 'SubResult' class to query all remaining children
if you need the complete data at once.

Just have a look at the 'test_that_resolve_nested_items_works' UnitTest there is an examplte to get an idea how it works.

