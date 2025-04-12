from django.shortcuts import render
from django.views.generic import TemplateView
from manticoresearch.rest import ApiException
from manticoresearch.models import InsertDocumentRequest, SearchQuery, SearchRequest
from shop.apps.catalogue.models import Product
import manticoresearch

configuration = manticoresearch.Configuration(
        host="http://127.0.0.1:9308"
        )

def hits_to_products(hits):
    return [{"score": x.score, "product": Product.objects.get(id=x.id)} for x in hits]

class SearchView(TemplateView):
    template_name = 'search/result.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.get('q', '')
        category = self.request.GET.get('category', '')
        if q != '':
            with manticoresearch.ApiClient(configuration) as api_client:
                searchApi = manticoresearch.SearchApi(api_client)
                try:
                    query = {"query_string": q}
                    if category != '':
                        query["in"] = {"any(categories)": category}
                    results = searchApi.search({"table": "products", "query": query})
                    if results.hits.total > 0:
                        ctx['result_count'] = results.hits.total
                        ctx['products'] = hits_to_products(results.hits.hits)
                    else:
                        ctx['result_count'] = 0
                        ctx['products'] = []
                except ApiException as e:
                    logger.warning("Manticoresearch API Exception during search operation:")
                    logger.warning(e)
                    ctx['result_count'] = 0
                    ctx['products'] = []
        else:
            ctx['result_count'] = 0
            ctx['products'] = []

        return ctx
