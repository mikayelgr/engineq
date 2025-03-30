from discogs_client import Client
from discogs_client.models import MixedPaginatedList, Release

d = Client("ExampleApplication/0.1",
           user_token='WZZsGFssXwZYQSBOALJBTyoVHGJzkNuWQnANWSJQ')
rows: MixedPaginatedList = d.search('Juice WRLD Conversations', type='master')
for row in rows:
    print(row.data["master_id"])
    m = d.master(row.data["master_id"])
