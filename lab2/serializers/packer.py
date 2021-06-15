from .JsonSerializer import JsonSerializer
from .TomlSerializer import TomlSerializer
from .YamlSerializer import YamlSerializer
from .PickleSerializer import PickleSerializer


class Packer:
    def create_serializer(self, ser_type: str):
        if not isinstance(ser_type, str):
            raise TypeError("Argument must be string!")
        if ser_type.lower().strip() == "json":
            return JsonSerializer()
        elif ser_type.lower().strip() == "toml":
            return TomlSerializer()
        elif ser_type.lower().strip() == "yaml":
            return YamlSerializer()
        elif ser_type.lower().strip() == "pickle":
            return PickleSerializer()
        else:
            raise NameError(f"No such serializer found: {ser_type}")
