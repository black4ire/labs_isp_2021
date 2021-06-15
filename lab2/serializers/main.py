from serializers.packer import Packer
import argparse
import os


class Config:
    def __init__(self, conf: dict):
        self.source_path = conf["source path"]
        self.old_ext = get_extension(conf["source path"])
        self.target_path = conf["target path"]
        self.new_ext = conf["new extension"]


def create_argument_parser() -> argparse.ArgumentParser:
    cmd_parser = argparse.ArgumentParser()
    cmd_parser.add_argument(
        "--ofp",
        type=str,
        dest="old_file_fullpath",
        help="Path to file to convert")

    cmd_parser.add_argument(
        "--np",
        type=str,
        dest="new_dir_path",
        help="Converted file directory")

    cmd_parser.add_argument(
        "--ext",
        type=str,
        dest="new_ext",
        help="Extension for converted file")

    cmd_parser.add_argument(
        "--cfg",
        type=str,
        dest="cfg_path",
        help="Path to config file (all other arguments will be ignored)")

    return cmd_parser


def get_extension(fp: str) -> str:
    return os.path.splitext(fp)[1][1:]


def main():
    ser_fabric = Packer()
    cmd_args = create_argument_parser().parse_args()
    conf_dict = None

    if cmd_args.cfg_path is not None:
        config_reader = ser_fabric\
                .create_serializer(get_extension(cmd_args.cfg_path))
        conf_dict = config_reader.load(cmd_args.cfg_path)

    try:
        if conf_dict is not None:
            config = Config(conf_dict)
        else:
            if cmd_args.old_file_fullpath is None \
                    or cmd_args.new_dir_path is None \
                    or cmd_args.new_ext is None:
                raise ValueError("Missing one of arguments: --ofp, --nfp,"
                                 + " --ext")
            config = Config({
                    "source path": cmd_args.old_file_fullpath,
                    "target path": cmd_args.new_dir_path,
                    "new extension": cmd_args.new_ext.lower()
                })
    except Exception as e:
        print(e)
        exit()

    try:
        if config.old_ext == config.new_ext:
            raise ValueError("Same extensions provided.")

        deserializer = ser_fabric.create_serializer(config.old_ext)
        serializer = ser_fabric.create_serializer(config.new_ext)

        obj = deserializer.load(config.source_path)
        new_path = config.target_path \
            + os.path.splitext(os.path.split(config.source_path)[1])[0] \
            + '.' + config.new_ext
        serializer.dump(obj, new_path)
        print(f"New file path: {new_path}")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
