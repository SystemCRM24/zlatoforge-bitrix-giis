from typing import Self, Union, overload


class XMLNode:
    """Верхоуровневый интерфейс XML-узла"""

    __slots__ = ("namespace", "name", "kwargs", "_value")

    def __init__(self, namespace: str, name: str, **kwargs) -> None:
        self.namespace = namespace
        self.name = name
        self.kwargs = kwargs   # Кварги используются для обозначения дополнительных атрибутов узла.
        self._value: str | tuple[XMLNode] = ""

    @overload
    def value(self, value: str) -> Self: ...

    @overload
    def value(self, *values: "XMLNode") -> Self: ...

    def value(self, *values: Union[str, tuple["XMLNode"]]) -> Self:       #type:ignore
        """Через этот метод будем осуществлять добавление значений с проверкой на тип."""
        if len(values) == 1:
            self._value = str(values[0])
        elif len(values) > 1:
            for node in values:
                if not isinstance(node, XMLNode):
                    raise ValueError(
                        f'The {type(node)} type cannot be part of xml structure. '
                        'Use XMLNode or value() method with single argument instead.'
                    )
            self._value = values # type:ignore
        return self
