import enum

import strawberry


class FileType(str, enum.Enum):
    parquet = "parquet"
    csv = "csv"


@strawberry.enum
class Quality(str, enum.Enum):
    very_bad = "Very Bad"
    validated = "Validated"
    checked = "Checked"
    not_checked = "Not Checked"
    bad = "Bad"


@strawberry.enum
class SignalType(str, enum.Enum):
    raw = "Raw"
    analysed = "Analysed"
    image = "Image"


@strawberry.enum
class Facility(str, enum.Enum):
    mast = "MAST"
    mast_u = "MAST-U"


@strawberry.enum
class Comissioner(str, enum.Enum):
    ukaea = "UKAEA"
    eurofusion = "EuroFusion"


@strawberry.enum
class PlasmaShape(str, enum.Enum):
    connected_double_null = "Connected Double Null"
    lower_single_null = "Lower Single Null"
    upper_single_null = "Upper Single Null"
    limiter = "Limiter"


@strawberry.enum
class DivertorConfig(str, enum.Enum):
    conventional = "Conventional"
    super_x = "Super-X"
    super_x_inner_leg = "Super-X Inner Leg)"
    snowflake = "Snowflake"
    vertical_target = "Vertical Target"
    x_divertor = "X Divertor"
    limiter = "Limiter"


@strawberry.enum
class CurrentRange(str, enum.Enum):
    _400kA = "400 kA"
    _450kA = "450 kA"
    _600kA = "600 kA"
    _700kA = "700 kA"
    _750kA = "750 kA"
    _1000kA = "1000 kA"
    _1300kA = "1300 kA"
    _1600kA = "1600 kA"
    _2000kA = "2000 kA"


@strawberry.enum
class ImageSubclass(str, enum.Enum):
    image_indexed = "IMAGE_INDEXED"
    image_truecolor = "IMAGE_TRUECOLOR"


@strawberry.enum
class ImageFormat(str, enum.Enum):
    ipx = "IPX"
