from elasticsearch.client import Elasticsearch as ElasticsearchBase


class Elasticsearch(ElasticsearchBase):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        super().__init__(hosts=app.config["ELASTICSEARCH_HOSTS"],)


es = Elasticsearch()
