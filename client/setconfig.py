import config_example
import config


def mk_write(k, v):
    if isinstance(v, str):
        return f"{k} = '{v}'\n"
    else:
        return f"{k} = {v}\n"


if __name__ == "__main__":
    with open("client/config.py", "w") as f:
        for k, v in vars(config_example).items():
            if not k.startswith("__"):
                if k in dir(config):
                    f.write(mk_write(k, getattr(config, k)))
                else:
                    f.write(mk_write(k, v))
