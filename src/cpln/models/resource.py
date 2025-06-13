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

    def __getattr__(self, name):
        """
        Allow attribute-style access to the attrs dictionary.

        Args:
            name: The name of the attribute to get

        Returns:
            The value of the attribute from attrs

        Raises:
            AttributeError: If the attribute doesn't exist in attrs
        """
        try:
            return self.attrs[name]
        except KeyError:
            raise AttributeError(
                f"'{self.__class__.__name__}' has no attribute '{name}'"
            ) from None

    def __setattr__(self, name, value):
        """
        Handle attribute assignment, storing values in attrs if they're not
        special attributes.

        Args:
            name: The name of the attribute to set
            value: The value to set the attribute to
        """
        # List of attributes that should be set directly on the instance
        direct_attrs = {"client", "collection", "state", "attrs"}

        if name in direct_attrs:
            super().__setattr__(name, value)
        else:
            # If attrs hasn't been initialized yet, initialize it
            if not hasattr(self, "attrs"):
                self.attrs = {}
            self.attrs[name] = value

    def __delattr__(self, name):
        """
        Handle attribute deletion, removing values from attrs if they're not
        special attributes.

        Args:
            name: The name of the attribute to delete

        Raises:
            AttributeError: If trying to delete a special attribute
        """
        # List of attributes that should not be deleted
        protected_attrs = {"client", "collection", "state", "attrs"}

        if name in protected_attrs:
            raise AttributeError(f"Cannot delete protected attribute '{name}'")

        if name in self.attrs:
            del self.attrs[name]
        else:
            raise AttributeError(
                f"'{self.__class__.__name__}' has no attribute '{name}'"
            )

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
            model_name = self.model.__name__ if self.model else "Model"
            raise ValueError(f"Can't create {model_name} from {attrs}")
