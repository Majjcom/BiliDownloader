import json as _json
import socket as _socket


class RconnData:
    act: str
    data: dict
    custom_data: bytes

    def __init__(self, act: str, data: dict = {}, custom_data: bytes = b"") -> None:
        self.act = act
        self.data = data
        self.custom_data = custom_data


class RconnClient:
    def __init__(self, addr: tuple[str, int]) -> None:
        self._sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        self._sock.settimeout(None)
        self._sock.connect(addr)

    def settimeout(self, timeout: float | None):
        self._sock.settimeout(timeout)

    def close(self):
        self._sock.close()

    def send(self, data: RconnData):
        data_dict = {
            "act": data.act,
            "custom_data_size": len(data.custom_data),
            "data": data.data,
        }
        data_json_str = _json.dumps(data_dict)
        data_json_raw = data_json_str.encode("utf_8")
        data_json_len = len(data_json_raw)
        data_send = data_json_len.to_bytes(4, "big")
        data_send += data_json_raw
        data_send += data.custom_data

        self._sock.sendall(data_send)

    def read(self) -> RconnData:
        json_data_len_raw = self._sock.recv(4)
        json_data_len = int.from_bytes(json_data_len_raw, "big")
        json_data_raw = self._sock.recv(json_data_len)
        json_data_str = json_data_raw.decode("utf_8")
        json_data = _json.loads(json_data_str)
        ret = RconnData(json_data["act"], json_data["data"])
        custom_data_size = json_data["custom_data_size"]
        custom_data = b""
        while len(custom_data) < custom_data_size:
            custom_data += self._sock.recv(custom_data_size - len(custom_data))
        ret.custom_data = custom_data
        return ret

    def request(self, data: RconnData) -> RconnData:
        self.send(data)
        return self.read()
