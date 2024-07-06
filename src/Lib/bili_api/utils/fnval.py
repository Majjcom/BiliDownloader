class FNVAL_PRESET:
    Dash = 16
    FourK = 128
    AV1 = 2048
    HDR = 64
    EighK = 1024

    def default(self):
        return self.Dash | self.AV1 | self.FourK
