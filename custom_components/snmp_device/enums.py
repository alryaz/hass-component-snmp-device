from enum import Enum
from typing import Type, Union, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from pyasn1.type import univ


def int_compatible_conversion(use_enum: Type[Enum]) -> Callable[[int], Union[Enum, int]]:
    def _int_compatible_conversion(incoming_value) -> Union[Enum, int]:
        comparing_value = int(incoming_value)
        for e in use_enum:
            if comparing_value == e.value:
                return e
        return comparing_value
    return _int_compatible_conversion

class _FriendlyEnum(Enum):
    @property
    def friendly_name(self):
        return self.name.lower().replace('_', ' ')

class SuppliesClass(_FriendlyEnum):
    OTHER = 1
    CONSUMABLE = 3
    RECEPTACLE = 4

class SuppliesType(_FriendlyEnum):
    OTHER = 1
    UNKNOWN = 2
    TONER = 3
    WASTE_TONER = 4
    INK = 5
    INK_CARTRIDGE = 6
    INK_RIBBON = 7
    WASTE_INK = 8
    OPC = 9
    DEVELOPER = 10
    FUSER_OIL = 11
    SOLID_WAX = 12
    RIBBON_WAX = 13
    WASTE_WAX = 14
    FUSER = 15
    CORONA_WIRE = 16
    FUSER_OIL_WICK = 17
    CLEANER_UNIT = 18
    FUSER_CLEANING_PAD = 19
    TRANSFER_UNIT = 20
    TONER_CARTRIDGE = 21
    FUSER_OILER = 22
    WATER = 23
    WASTE_WATER = 24
    GLUE_WATER_ADDITIVE = 25
    WASTE_PAPER = 26
    BINDING_SUPPLY = 27
    BANDING_SUPPLY = 28
    STITCHING_WIRE = 29
    SHRINK_WRAP = 30
    PAPER_WRAP = 31
    STAPLES = 32
    INSERTS = 33
    COVERS = 34

class CapacityLevelType(_FriendlyEnum):
    UNTRACKED = -1
    UNKNOWN = -2
    AVAILABLE = -3

CAPACITY_LEVEL_TYPE = lambda x: CapacityLevelType(x) if int(x) < 0 else int(x)

class PrinterActionStatus(_FriendlyEnum):
    OFFLINE = 0
    OTHER = 1
    UNKNOWN = 2
    IDLE = 3
    PRINTING = 4
    WARMUP = 5

class PrinterDeviceStatus(_FriendlyEnum):
    UNKNOWN = 1
    RUNNING = 2
    WARNING = 3
    TESTING = 4
    DOWN = 5

class PaperInputType(_FriendlyEnum):
    OTHER = 1
    UNKNOWN = 2
    SHEET_FEED_AUTO_REMOVABLE_TRAY = 3
    SHEET_FEED_AUTO_NON_REMOVABLE_TRAY = 4
    SHEET_FEED_MANUAL = 5
    CONTINUOUS_ROLL = 6
    CONTINUOUS_FAN_FOLD = 7

class CapacityUnitType(_FriendlyEnum):
    OTHER = 1
    UNKNOWN = 2
    TEN_THOUSANDTHS_OF_INCHES = 3
    MICROMETERS = 4
    SHEETS = 8
    FEET = 16
    METERS = 17
    ITEMS = 18
    PERCENT = 19
    
class PrinterDetectedErrorState(_FriendlyEnum):
    LOW_PAPER = 1
    NO_PAPER = 2
    LOW_TONER = 4
    NO_TONER = 8
    DOOR_OPEN = 16
    JAMMED = 32
    OFFLINE = 64
    SERVICE_REQUESTED = 128
    INPUT_TRAY_MISSING = 256
    OUTPUT_TRAY_MISSING = 512
    MARKER_SUPPLY_MISSING = 1024
    OUTPUT_NEAR_FULL = 2048
    OUTPUT_FULL = 4096
    INPUT_TRAY_EMPTY = 8192
    OVERDUE_PREVENT_MAINTENANCE = 16384

    @classmethod
    def decode(cls, error_value: 'univ.OctetString'):
        converted_error = sum(error_value)
        return [e for e in cls if e.value & converted_error]

# https://www.iana.org/assignments/ianaiftype-mib/ianaiftype-mib
# overkill, though
class NetworkConnectionType(_FriendlyEnum):
    OTHER = 1
    REGULAR_1822 = 2
    HDH_1822 = 3
    DDN_X25 = 4
    RFC877_X25 = 5
    ETHERNET_CSMACD = 6
    ISO88023_CSMACD = 7
    ISO88024_TOKEN_BUS = 8
    ISO88025_TOKEN_RING = 9
    ISO88026_MAN = 10
    STAR_LAN = 11
    PROTEON_10_MBIT = 12
    PROTEON_80_MBIT = 13
    HYPER_CHANNEL = 14
    FDDI = 15
    LAPB = 16
    SDLC = 17
    DS1 = 18
    E1 = 19
    BASIC_ISDN = 20
    PRIMARY_ISDN = 21
    PROP_POINT_TO_POINT_SERIAL = 22
    PPP = 23
    SOFTWARE_LOOPBACK = 24
    EON = 25
    ETHERNET_3_MBIT = 26
    NSIP = 27
    SLIP = 28
    ULTRA = 29
    DS3 = 30
    SIP = 31
    FRAME_RELAY = 32
    RS232 = 33
    PARA = 34
    ARCNET = 35
    ARCNET_PLUS = 36
    ATM = 37
    MIO_X25 = 38
    SONET = 39
    X25_PLE = 40
    ISO88022_LLC = 41
    LOCAL_TALK = 42
    SMDS_DXI = 43
    FRAME_RELAY_SERVICE = 44
    V35 = 45
    HSSI = 46
    HIPPI = 47
    MODEM = 48
    AAL5 = 49
    SONET_PATH = 50
    SONET_VT = 51
    SMDS_ICIP = 52
    PROP_VIRTUAL = 53
    PROP_MULTIPLEXOR = 54
    FIBRE_CHANNEL = 56
    HIPPI_INTERFACE = 57
    FRAME_RELAY_INTERCONNECT = 58
    AFLANE8023 = 59
    AFLANE8025 = 60
    CCTEMUL = 61
    FAST_ETHERNET = 62
    ISDN = 63
    V11 = 64
    V36 = 65
    G703AT64K = 66
    G703AT2MB = 67
    QLLC = 68
    FAST_ETHERNET_FX = 69
    CHANNEL = 70
    IEEE80211 = 71
    IBM370PARCHAN = 72
    ESCON = 73
    DLSW = 74
    ISDNS = 75
    ISDNU = 76
    LAPD = 77
    IPSWITCH = 78
    RSRB = 79
    ATMLOGICAL = 80
    DS0 = 81
    DS0BUNDLE = 82
    BSC = 83
    ASYNC = 84
    CNR = 85
    ISO88025DTR = 86
    EPLRS = 87
    ARAP = 88
    PROP_CNLS = 89
    HOST_PAD = 90
    TERM_PAD = 91
    FRAME_RELAY_MPI = 92
    X213 = 93
    ADSL = 94
    RADSL = 95
    SDSL = 96
    VDSL = 97
    ISO88025_CRFPINT = 98
    MYRINET = 99
    VOICEEM = 100
    VOICEFXO = 101
    VOICEFXS = 102
    VOICEENCAP = 103
    VOICEOVERIP = 104
    ATMDXI = 105
    ATMFUNI = 106
    ATMIMA = 107
    PPPMULTILINKBUNDLE = 108
    IPOVERCDLC = 109
    IPOVERCLAW = 110
    STACKTOSTACK = 111
    VIRTUALIPADDRESS = 112
    MPC = 113
    IPOVERATM = 114
    ISO88025FIBER = 115
    TDLC = 116
    GIGABITETHERNET = 117
    HDLC = 118
    LAPF = 119
    V37 = 120
    X25MLP = 121
    X25HUNTGROUP = 122
    TRANSPHDLC = 123
    INTERLEAVE = 124
    FAST = 125
    IP = 126
    DOCSCABLEMACLAYER = 127
    DOCSCABLEDOWNSTREAM = 128
    DOCSCABLEUPSTREAM = 129
    A12MPPSWITCH = 130
    TUNNEL = 131
    COFFEE = 132
    CES = 133
    ATMSUBINTERFACE = 134
    L2VLAN = 135
    L3IPVLAN = 136
    L3IPXVLAN = 137
    DIGITALPOWERLINE = 138
    MEDIAMAILOVERIP = 139
    DTM = 140
    DCN = 141
    IPFORWARD = 142
    MSDSL = 143
    IEEE1394 = 144
    IF_GSN = 145,
    DVBRCCMACLAYER = 146
    DVBRCCDOWNSTREAM = 147
    DVBRCCUPSTREAM = 148
    ATMVIRTUAL = 149
    MPLSTUNNEL = 150
    SRP = 151
    VOICEOVERATM = 152
    VOICEOVERFRAMERELAY = 153
    IDSL = 154
    COMPOSITELINK = 155
    SS7SIGLINK = 156
    PROPWIRELESSP2P = 157
    FRFORWARD = 158
    RFC1483 = 159
    USB = 160
    IEEE8023ADLAG = 161
    BGPPOLICYACCOUNTING = 162
    FRF16MFRBUNDLE = 163
    H323GATEKEEPER = 164
    H323PROXY = 165
    MPLS = 166
    MFSIGLINK = 167
    HDSL2 = 168
    SHDSL = 169
    DS1FDL = 170
    POS = 171
    DVBASIIN = 172
    DVBASIOUT = 173
    PLC = 174
    NFAS = 175
    TR008 = 176
    GR303RDT = 177
    GR303IDT = 178
    ISUP = 179
    PROPDOCSWIRELESSMACLAYER = 180
    PROPDOCSWIRELESSDOWNSTREAM = 181
    PROPDOCSWIRELESSUPSTREAM = 182
    HIPERLAN2 = 183
    PROPBWAP2MP = 184
    SONETOVERHEADCHANNEL = 185
    DIGITALWRAPPEROVERHEADCHANNEL = 186
    AAL2 = 187
    RADIOMAC = 188
    ATMRADIO = 189
    IMT = 190
    MVL = 191
    REACHDSL = 192
    FRDLCIENDPT = 193
    ATMVCIENDPT = 194
    OPTICALCHANNEL = 195
    OPTICALTRANSPORT = 196
    PROPATM = 197
    VOICEOVERCABLE = 198
    INFINIBAND = 199
    TELINK = 200
    Q2931 = 201
    VIRTUALTG = 202
    SIPTG = 203
    SIPSIG = 204
    DOCSCABLEUPSTREAMCHANNEL = 205
    ECONET = 206
    PON155 = 207
    PON622 = 208
    BRIDGE = 209
    LINEGROUP = 210
    VOICEEMFGD = 211
    VOICEFGDEANA = 212
    VOICEDID = 213
    MPEGTRANSPORT = 214
    SIXTOFOUR = 215
    GTP = 216
    PDNETHERLOOP1 = 217
    PDNETHERLOOP2 = 218
    OPTICALCHANNELGROUP = 219
    HOMEPNA = 220
    GFP = 221
    CISCOISLVLAN = 222
    ACTELISMETALOOP = 223
    FCIPLINK = 224
    RPR = 225
    QAM = 226
    LMP = 227
    CBLVECTASTAR = 228
    DOCSCABLEMCMTSDOWNSTREAM = 229
    ADSL2 = 230
    MACSECCONTROLLEDIF = 231
    MACSECUNCONTROLLEDIF = 232
    AVICIOPTICALETHER = 233
    ATMBOND = 234
    VOICEFGDOS = 235
    MOCAVERSION1 = 236
    IEEE80216WMAN = 237
    ADSL2PLUS = 238
    DVBRCSMACLAYER = 239
    DVBTDM = 240
    DVBRCSTDMA = 241
    X86LAPS = 242
    WWANPP = 243
    WWANPP2 = 244
    VOICEEBS = 245
    IFPWTYPE = 246
    ILAN = 247
    PIP = 248
    ALUELP = 249
    GPON = 250
    VDSL2 = 251
    CAPWAPDOT11PROFILE = 252
    CAPWAPDOT11BSS = 253
    CAPWAPWTPVIRTUALRADIO = 254
    BITS = 255
    DOCSCABLEUPSTREAMRFPORT = 256
    CABLEDOWNSTREAMRFPORT = 257
    VMWAREVIRTUALNIC = 258
    IEEE802154 = 259
    OTNODU = 260
    OTNOTU = 261
    IFVFITYPE = 262
    G9981 = 263
    G9982 = 264
    G9983 = 265
    ALUEPON = 266
    ALUEPONONU = 267
    ALUEPONPHYSICALUNI = 268
    ALUEPONLOGICALLINK = 269
    ALUGPONONU = 270
    ALUGPONPHYSICALUNI = 271
    VMWARENICTEAM = 272
    DOCSOFDMDOWNSTREAM = 277
    DOCSOFDMAUPSTREAM = 278
    GFAST = 279
    SDCI = 280
    XBOXWIRELESS = 281
    FASTDSL = 282
    DOCSCABLESCTE55D1FWDOOB = 283
    DOCSCABLESCTE55D1RETOOB = 284
    DOCSCABLESCTE55D2DSOOB = 285
    DOCSCABLESCTE55D2USOOB = 286
    DOCSCABLENDF = 287
    DOCSCABLENDR = 288
    PTM = 289
    GHN = 290
    OTNOTSI = 291
    OTNOTUC = 292
    OTNODUC = 293
    OTNOTSIG = 294
    MICROWAVECARRIERTERMINATION = 295
    MICROWAVERADIOLINKTERMINAL = 296
    IEEE8021AXDRNI = 297
    AX25 = 298
    IEEE19061NANOCOM = 299