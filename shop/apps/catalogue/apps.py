import oscar.apps.catalogue.apps as apps


class CatalogueConfig(apps.CatalogueConfig):
    name = 'shop.apps.catalogue'
    label = 'catalogue'
    namespace = 'catalogue'
    verbose_name = 'Catalogue'


    def ready(self):
        import shop.apps.catalogue.signals
        return super().ready()
