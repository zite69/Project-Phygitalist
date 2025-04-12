import manticoresearch
from manticoresearch.rest import ApiException
from manticoresearch.models import InsertDocumentRequest, SearchQuery, SearchRequest
from shop.apps.catalogue.models import Product, Category
from shop.apps.main.utils.html import strip_tags

configuration = manticoresearch.Configuration(
        host="http://127.0.0.1:9308"
        )

SQL = {
    'CREATE_PRODUCTS_SQL': """
            CREATE TABLE IF NOT EXISTS products(title text, description text, meta_title text, 
                categories multi, meta_description text, product_id int, url string)
            """,
    'DROP_PRODUCTS_SQL': """DROP TABLE IF EXISTS products"""
}

def make_document(product):
    doc = {
        "title": product.title,
        "description": strip_tags(product.description),
        "product_id": product.id,
        "url": product.get_absolute_url(),
        "categories": [c.id for c in product.categories.all()]
    }
    if product.meta_title is not None:
        doc["meta_title"] = product.meta_title
    if product.meta_description is not None:
        doc["meta_description"] = strip_tags(product.description)

    return doc

def run(*args):
    if len(args) > 0:
        drop = args[0].startswith("d")
    else:
        drop = False

    with manticoresearch.ApiClient(configuration) as api_client:
        # Create instances of API classes
        indexApi = manticoresearch.IndexApi(api_client)
        utilsApi = manticoresearch.UtilsApi(api_client)
        searchApi = manticoresearch.SearchApi(api_client)

        try:
            if drop:
                drop_resp = utilsApi.sql(SQL['DROP_PRODUCTS_SQL'])
                print("drop table response: ", drop_resp)

            sql_create_resp = utilsApi.sql(SQL['CREATE_PRODUCTS_SQL'])
            print("create table response:", sql_create_resp)
            # truncate_response = utilsApi.sql("TRUNCATE TABLE products")
            # print("truncate response: ", truncate_response)

            for product in Product.objects.browsable():
                insert_request = InsertDocumentRequest(table="products", doc=make_document(product), id=product.id)
                indexApi.replace(insert_request)

            #sql_response = utilsApi.sql('SHOW TABLES')
            #print("SQL response:")
            # print(sql_response)
            # drop_resp = utilsApi.sql(SQL['DROP_PRODUCTS_SQL'])
            # print('drop_resp: ', drop_resp)
            api_resp = searchApi.search({"table": "products", "query": {"query_string": "Pink", "in": {"any(categories)": [1]}}})
            print("search response: ", api_resp)
            # print(api_resp.hits)
            # print(api_resp.hits.total)
            # print(api_resp.hits.hits)
            # print(api_resp.hits.hits[0].source)
            # print(dir(api_resp.hits.hits[0]))
            hit = api_resp.hits.hits[0]
            print(hit.id, hit.score, hit.source, hit.source['title'])
        except ApiException as e:
            print("Exception calling API method")
            print(e)
