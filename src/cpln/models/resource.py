from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from cpln.client import CPLNClient


class Model:
    """
    A base class for representing a single object on the server.
    """

    id_attribute = "id"
    label_attribute = "name"

    def __init__(
        self,
        client: "CPLNClient",
        attrs: Optional[dict[str, Any]] = None,
        collection: Optional["Collection"] = None,
        state: Optional[dict[str, Any]] = None,
    ) -> None:
        #: A client pointing at the server that this object is on.
        self.client: "CPLNClient" = client

        #: The collection that this model is part of.
        self.collection: Optional["Collection"] = collection

        #: The state that represents this model.
        self.state: dict[str, Any] = state if state is not None else {}

        #: The raw representation of this object from the API
        self.attrs: dict[str, Any] = attrs if attrs is not None else {}

    def __repr__(self) -> str:
        short_id: Optional[str] = self.short_id or "None"
        return f"<{self.__class__.__name__}: {short_id} - {self.label}>"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.id == other.id

    def __hash__(self) -> int:
        return hash(f"{self.__class__.__name__}:{self.id}")

    def __getattr__(self, name: str) -> Any:
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

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Handle attribute assignment, storing values in attrs if they're not
        special attributes.

        Args:
            name: The name of the attribute to set
            value: The value to set the attribute to
        """
        # List of attributes that should be set directly on the instance
        direct_attrs: set[str] = {"client", "collection", "state", "attrs"}

        if name in direct_attrs:
            super().__setattr__(name, value)
        else:
            # If attrs hasn't been initialized yet, initialize it
            if not hasattr(self, "attrs"):
                self.attrs = {}
            self.attrs[name] = value

    def __delattr__(self, name: str) -> None:
        """
        Handle attribute deletion, removing values from attrs if they're not
        special attributes.

        Args:
            name: The name of the attribute to delete

        Raises:
            AttributeError: If trying to delete a special attribute
        """
        # List of attributes that should not be deleted
        protected_attrs: set[str] = {"client", "collection", "state", "attrs"}

        if name in protected_attrs:
            raise AttributeError(f"Cannot delete protected attribute '{name}'")

        if name in self.attrs:
            del self.attrs[name]
        else:
            raise AttributeError(
                f"'{self.__class__.__name__}' has no attribute '{name}'"
            )

    @property
    def id(self) -> Optional[str]:
        """
        The ID of the object.
        """
        return self.attrs.get(self.id_attribute)

    @property
    def short_id(self) -> Optional[str]:
        """
        The ID of the object, truncated to 12 characters.
        """
        if self.id is None:
            return None
        return self.id[:12]

    @property
    def label(self) -> Optional[str]:
        """
        The label of the object.
        """
        return self.attrs.get(self.label_attribute)

    def reload(self) -> None:
        """
        Load this object from the server again and update ``attrs`` with the
        new data.
        """
        if self.collection is None:
            raise RuntimeError("Model is not part of a collection")

        new_model: Optional[Model] = self.collection.get(self.id)
        if new_model is None:
            raise RuntimeError(f"Model {self.id} not found")
        self.attrs = new_model.attrs


class Collection:
    #: The type of object this collection represents, set by subclasses
    model: type[Model]

    def __init__(self, client: "CPLNClient") -> None:
        #: The client pointing at the server that this collection of objects
        #: is on.
        self.client = client

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            f"'{self.__class__.__name__}' object is not callable. "
            "You might be trying to use the old (pre-2.0) API - "
            "use docker.APIClient if so."
        )

    def list(self) -> None:
        raise NotImplementedError

    def get(self, key: Any) -> Optional["Model"]:
        raise NotImplementedError

    def create(self, attrs: Optional[Any] = None) -> None:
        raise NotImplementedError

    def prepare_model(self, attrs: Any, state: Optional[Any] = None) -> Model:
        """
        Create a model from a set of attributes.
        """
        if isinstance(attrs, Model):
            attrs.client = self.client
            attrs.collection = self
            attrs.state = state if state is not None else {}
            return attrs
        elif isinstance(attrs, dict):
            return self.model(
                client=self.client,
                attrs=attrs,
                collection=self,
                state=state,
            )
        else:
            model_name = self.model.__name__ if self.model else "Model"
            raise ValueError(f"Can't create {model_name} from {attrs}")
