from math import ceil
from django.db.models import Q
from django.contrib.postgres.search import TrigramWordSimilarity


class TextSearch:
    """ Free-text search within TEXT or CHAR fields of any given model. At least three characters are required for this
        class to start searching. Each next query field counts for half the weight in the result score. Only results
        where the search query is found as-is (adjacent) are returned. The results are returned in descending score as
        a paginated result.

        For this class to function your database is required to support the extension 'pg_trgm' (TrigramWordSimilarity)
        and 'unaccent' (search agnostic for accents e.g. ü or u are equivalent)

        model: model object class
        query: string
        query_fields: comma separated string of model fields
        return_fields: comma separated string of model fields
        page_size: maximum number items in paginated result
        page: the result page
    """

    def __init__(self, model, query, query_fields, return_fields=None, page_size=10, page=0):
        self.model = model
        self.query = query
        self.query_fields = query_fields.split(',')
        self.return_fields = None if return_fields is None else return_fields.split(',')
        self.threshold = 0.1  # only scores above this threshold are considered
        self.page_size = page_size
        self.page = page
        self.pages = 0
        self.result = []

    def search(self):
        # Only start the search with at least three characters
        if len(self.query) < 3:
            return {'page': self.result, 'pages': self.pages}

        # Dynamically get appropriate model fields and build a filter for the requested return fields
        model_fields = [x.name for x in self.model._meta.get_fields() if x.name != 'data']
        if self.return_fields is not None:
            model_fields = [x for x in model_fields if x in self.return_fields]
        model_fields += ['score']

        # Build a 'TrigramWordSimilarity' and 'accents agnostic adjacent characters' filter
        score = 0
        weight = 1.0
        condition = None
        for query_field in self.query_fields:
            # Set half the weight for each next search field
            score += weight * TrigramWordSimilarity(self.query, query_field)
            weight = weight / 2

            # Build accents agnostic filter for adjacent characters in TrigramWordSimilarity search results
            q = Q(**{'{query_field}__unaccent__icontains'.format(query_field=query_field): self.query})
            condition = q if condition is None else condition | q

        # Query and filter
        objects = self.model.objects.annotate(score=score).filter(score__gte=self.threshold).filter(condition).order_by('-score')
        sorted_objects = list(objects)

        # Set paginated result and calculate number of pages
        start_index = self.page * self.page_size
        stop_index = self.page * self.page_size + self.page_size
        page = sorted_objects[start_index:stop_index]
        self.pages = int(ceil(len(sorted_objects) / float(self.page_size)))

        # Filter the requested return fields (note: It functions as a serializer)
        for item in page:
            data = {}
            for model_field in model_fields:
                data[model_field] = getattr(item, model_field)
            self.result.append(data)

        # Return result and page count
        return {'page': self.result, 'pages': self.pages}
