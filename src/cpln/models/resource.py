class Model:
    """
    A base class for representing a single object on the server.
    """

    id_attribute = "id"
    label_attribute = "name"

    def __init__(self, attrs=None, client=None, collection=None, state=None):
        #: A client pointing at the server that this object is on.
        self.client = client

        #: The collection that this model is part of.
        self.collection = collection

        #: The state that represents this model.
        self.state = state
        if self.state is None:
            self.state = {}

        #: The raw representation of this object from the API
        self.attrs = attrs
        if self.attrs is None:
            self.attrs = {}

    def __repr__(self):
        short_id = self.short_id or "None"
        return f"<{self.__class__.__name__}: {short_id} - {self.label}>"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __hash__(self):
        return hash(f"{self.__class__.__name__}:{self.id}")

    @property
    def id(self):
        """
        The ID of the object.
        """
        return self.attrs.get(self.id_attribute)

    @property
    def short_id(self):
        """
        The ID of the object, truncated to 12 characters.
        """
        if self.id is None:
            return None
        return self.id[:12]

    @property
    def label(self):
        """
        The label of the object.
        """
        return self.attrs.get(self.label_attribute)

    def reload(self):
        """
        Load this object from the server again and update ``attrs`` with the
        new data.
        """
        new_model = self.collection.get(self.id)
        self.attrs = new_model.attrs


class Collection:
    #: The type of object this collection represents, set by subclasses
    model = None

    def __init__(self, client=None):
        #: The client pointing at the server that this collection of objects
        #: is on.
        self.client = client

    def __call__(self, *args, **kwargs):
        raise TypeError(
            f"'{self.__class__.__name__}' object is not callable. "
            "You might be trying to use the old (pre-2.0) API - "
            "use docker.APIClient if so."
        )

    def list(self):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError

    def create(self, attrs=None):
        raise NotImplementedError

    def prepare_model(self, attrs, state=None):
        """
        Create a model from a set of attributes.
        """
        if isinstance(attrs, Model):
            attrs.client = self.client
            attrs.collection = self
            attrs.state = state
            return attrs
        elif isinstance(attrs, dict):
            return self.model(
                attrs=attrs, client=self.client, collection=self, state=state
            )
        else:
            raise Exception(f"Can't create {self.model.__name__} from {attrs}")
