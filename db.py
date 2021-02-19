from tinydb import TinyDB, Query

class DB:
    def __init__(self, suburb_name):
        self.db = TinyDB(suburb_name.lower().replace(" ","-") + '_db.json')

    def insertSuburb(self,suburb_name):
        self.db.insert({'type':'suburb','suburb_name': suburb_name, 'status': 'processing'})

    def updateSuburb(self,suburb_name,status):
        Suburb = Query()
        self.db.update({'status': status}, (Suburb.type == 'suburb') & (Suburb.suburb_name == suburb_name))

    def getSuburub(self,suburb_name):
        Suburb = Query()
        result = self.db.search((Suburb.type == 'suburb') & (Suburb.suburb_name == suburb_name))
        return result[0] if len(result) > 1 else None

    def insertStreet(self,street_name):
        self.db.insert({'type':'street','street_name': street_name, 'status': 'added'})

    def updateStreet(self,street_name,status):
        Street = Query()
        self.db.update({'status': status}, (Street.type == 'street') & (Street.street_name == street_name))

    def getStreetsByStatus(self,status):
        Street = Query()
        result = self.db.search((Street.type == 'street') & (Street.status == status))
        return list(map(lambda street: street.street_name, result))

    def insert_property(self,street_name,property_url):
        self.db.insert({'type':'property','street_name': street_name, 'status': 'processing','url':property_url})

    def update_property(self,street_name,property_url,status):
        Property = Query()
        self.db.update({'status': status}, (Property.type == 'property') & (Property.street_name == street_name) & (Property.url  == property_url))

    def update_property_by_url(self,property_url,status):
        Property = Query()
        self.db.update({'status': status}, (Property.type == 'property') & (Property.url  == property_url))

    def remove_properties(self,street_name):
        Property = Query()
        self.db.remove((Property.type == 'property') & (Property.street_name == street_name) & (Property.status != 'failed'))

    def get_failed_properties(self):
        Property = Query()
        result = self.db.search((Property.status == 'failed'))
        return result




