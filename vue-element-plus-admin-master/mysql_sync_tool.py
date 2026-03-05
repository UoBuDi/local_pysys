import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import configparser
import datetime
import logging
import os
import sys
import re
try:
    import pymysql
except ImportError:
    is_frozen = getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS')
    if is_frozen:
        print("缺少依赖库：pymysql。请使用包含依赖的安装包或联系管理员。")
        try:
            messagebox.showerror("失败", "缺少依赖库：pymysql。请使用包含依赖的安装包或联系管理员！")
        except Exception:
            pass
        sys.exit(1)
    else:
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pymysql"])
            import pymysql
        except Exception as e:
            print(f"安装 pymysql 失败：{e}")
            try:
                messagebox.showerror("失败", f"安装 pymysql 失败，请手动安装！")
            except Exception:
                pass
            sys.exit(1)
# 已移除对 python-dateutil 的依赖，相关日期计算改为标准库实现
from typing import List, Tuple, Dict, Optional
import time
import threading

# -------------------------- 基础配置与工具函数 --------------------------
def get_app_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def ensure_dir(path):
    """确保目录存在，不存在则创建"""
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            return True
        except Exception as e:
            logging.error(f"创建目录失败：{path}，错误：{e}")
            return False
    return True

# 配置文件路径
CONFIG_FILE = os.path.join(get_app_path(), "config.ini")
# 确保配置文件目录可写
ensure_dir(get_app_path())

DEFAULT_LOG_DIR = os.path.join(get_app_path(), "log")
ensure_dir(DEFAULT_LOG_DIR)
DEFAULT_LOG_PATH = os.path.join(DEFAULT_LOG_DIR, "mysql_sync.log")
DEFAULT_SYNC_TIME_FILE = os.path.join(DEFAULT_LOG_DIR, "last_sync_time.txt")
FIXED_TABLE_PREFIX = "gbupload_etctu_as_"
DEFAULT_SYNC_DATE_RANGE = "27,30"
FIXED_FIELDS = """msgId, tradeId, gantryId, computerOrder, hourBatchNo, gantryOrderNum, gantryHex, gantryType, gantryHexOpposite, transTime, payFee, fee, discountFee, transFee, mediaType, obuSign, tollIntervalId, tollIntervalSign, payFeeGroup, feeGroup, discountFeeGroup, vehiclePlate, vehicleType, identifyVehicleType, vehicleClass, vehicleSign, TAC, transType, terminalNo, terminalTransNo, transNo, serviceType, algorithmIdentifier, keyVersion, antennaID, rateVersion, consumeTime, passState, enTollLaneId, enTollStationHex, enTime, enLaneType, passId, lastGantryHex, lastGantryTime, OBUMAC, OBUIssueID, OBUSN, OBUVersion, OBUStartDate, OBUEndDate, OBUElectrical, OBUState, OBUVehiclePlate, OBUVehicleType, vehicleUserType, vehicleSeat, axleCount, totalWeight, vehicleLength, vehicleWidth, vehicleHight, CPUNetID, CPUIssueID, CPUVehiclePlate, CPUVehicleType, CPUStartDate, CPUEndDate, CPUVersion, CPUCardType, CPUCardId, balanceBefore, balanceAfter, gantryPassCount, gantryPassInfo, feeProvInfo, feeSumLocalBefore, feeSumLocalAfter, feeCalcSpecial, feeCalcResult, feeInfo1, feeInfo2, feeInfo3, OBUpayFeeSumBefore, OBUpayFeeSumAfter, OBUdiscountFeeSumBefore, OBUdiscountFeeSumAfter, OBUProvfeeSumBefore, OBUProvfeeSumAfter, cardfeeSumBefore, cardfeeSumAfter, noCardTimesBefore, noCardTimesAfter, provinceNumBefore, provinceNumAfter, OBUTotalTradeSuccNumBefore, OBUTotalTradeSuccNumAfter, OBUProvTradeSuccNumBefore, OBUProvTradeSuccNumAfter, OBUTradeResult, tradeType, OBUInfoTypeRead, OBUInfoTypeWrite, OBUPassState, feeVehicleType, OBULastGantryHex, OBULastGantryTime, feeMileage, OBUMileageBefore, OBUMileageAfter, tradeReadCiphertext, readCiphertextVerify, tradeWriteCiphertext, provMinFee, provMinFeeCalcMode, feeSpare1, feeSpare2, feeSpare3, feeProvBeginHex, rateCompute, rateFitCount, OBUFeeSumBefore, OBUFeeSumAfter, OBUProvPayFeeSumBefore, OBUProvPayFeeSumAfter, pathFitFlag, feeCalcSpecials, payFeeProvSumLocal, PCRSUVersion, gantryPassInfoAfter, updateResult, CPCFeeTradeResult, feeProvEF04, fitProvFlag, gantryPassCountBefore, feeProvBeginHexFit, feeProvBeginTimeFit, feeProvBeginTime, feeSumLocalAfterEF04, lastGantryFeePass, lastGantryMilePass, holidayState, tradeResult, lastGantryHexFee, lastGantryHexPass, specialType, chargesSpecialType, verifyCode, interruptSignal, vehiclePicId, vehicleTailPicId, matchStatus, validStatus, dealStatus, isFixData, relatedTradeId, allRelatedTradeId, stationDBTime, stationDealTime, stationValidTime, stationMatchTime, RSUManuid, feeDataVersion, gantryHexOppotime, CREATETIME, messageTime, LASTUPATETIME, offset, dataId, partitionId"""
FIELDS_LIST = [field.strip() for field in FIXED_FIELDS.split(',') if field.strip()]

# 建表语句模板（根据FIXED_FIELDS生成）
CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS `{{table_name}}` (
    `msgId` varchar(64) DEFAULT NULL COMMENT '消息ID',
    `tradeId` varchar(64) DEFAULT NULL COMMENT '交易ID',
    `gantryId` varchar(32) DEFAULT NULL COMMENT '门架ID',
    `computerOrder` int DEFAULT NULL COMMENT '计算机序号',
    `hourBatchNo` int DEFAULT NULL COMMENT '小时批次号',
    `gantryOrderNum` int DEFAULT NULL COMMENT '门架顺序号',
    `gantryHex` varchar(16) DEFAULT NULL COMMENT '门架十六进制编码',
    `gantryType` tinyint DEFAULT NULL COMMENT '门架类型',
    `gantryHexOpposite` varchar(16) DEFAULT NULL COMMENT '对向门架十六进制编码',
    `transTime` datetime DEFAULT NULL COMMENT '交易时间',
    `payFee` decimal(10,2) DEFAULT NULL COMMENT '支付金额',
    `fee` decimal(10,2) DEFAULT NULL COMMENT '费用金额',
    `discountFee` decimal(10,2) DEFAULT NULL COMMENT '优惠金额',
    `transFee` decimal(10,2) DEFAULT NULL COMMENT '交易金额',
    `mediaType` tinyint DEFAULT NULL COMMENT '介质类型',
    `obuSign` varchar(32) DEFAULT NULL COMMENT 'OBU标识',
    `tollIntervalId` varchar(32) DEFAULT NULL COMMENT '收费区间ID',
    `tollIntervalSign` varchar(32) DEFAULT NULL COMMENT '收费区间标识',
    `payFeeGroup` varchar(128) DEFAULT NULL COMMENT '支付金额组',
    `feeGroup` varchar(128) DEFAULT NULL COMMENT '费用金额组',
    `discountFeeGroup` varchar(128) DEFAULT NULL COMMENT '优惠金额组',
    `vehiclePlate` varchar(32) DEFAULT NULL COMMENT '车牌号码',
    `vehicleType` tinyint DEFAULT NULL COMMENT '车辆类型',
    `identifyVehicleType` tinyint DEFAULT NULL COMMENT '识别车辆类型',
    `vehicleClass` tinyint DEFAULT NULL COMMENT '车辆类别',
    `vehicleSign` varchar(32) DEFAULT NULL COMMENT '车辆标识',
    `TAC` varchar(32) DEFAULT NULL COMMENT 'TAC码',
    `transType` tinyint DEFAULT NULL COMMENT '交易类型',
    `terminalNo` varchar(32) DEFAULT NULL COMMENT '终端号',
    `terminalTransNo` varchar(32) DEFAULT NULL COMMENT '终端交易号',
    `transNo` varchar(32) DEFAULT NULL COMMENT '交易流水号',
    `serviceType` tinyint DEFAULT NULL COMMENT '服务类型',
    `algorithmIdentifier` tinyint DEFAULT NULL COMMENT '算法标识',
    `keyVersion` tinyint DEFAULT NULL COMMENT '密钥版本',
    `antennaID` tinyint DEFAULT NULL COMMENT '天线ID',
    `rateVersion` varchar(32) DEFAULT NULL COMMENT '费率版本',
    `consumeTime` int DEFAULT NULL COMMENT '消费时间(秒)',
    `passState` tinyint DEFAULT NULL COMMENT '通行状态',
    `enTollLaneId` varchar(32) DEFAULT NULL COMMENT '入口收费车道ID',
    `enTollStationHex` varchar(16) DEFAULT NULL COMMENT '入口收费站十六进制编码',
    `enTime` datetime DEFAULT NULL COMMENT '入口时间',
    `enLaneType` tinyint DEFAULT NULL COMMENT '入口车道类型',
    `passId` varchar(64) DEFAULT NULL COMMENT '通行ID',
    `lastGantryHex` varchar(16) DEFAULT NULL COMMENT '上一门架十六进制编码',
    `lastGantryTime` datetime DEFAULT NULL COMMENT '上一门架时间',
    `OBUMAC` varchar(64) DEFAULT NULL COMMENT 'OBU MAC地址',
    `OBUIssueID` varchar(32) DEFAULT NULL COMMENT 'OBU发行方ID',
    `OBUSN` varchar(64) DEFAULT NULL COMMENT 'OBU序列号',
    `OBUVersion` varchar(32) DEFAULT NULL COMMENT 'OBU版本',
    `OBUStartDate` date DEFAULT NULL COMMENT 'OBU生效日期',
    `OBUEndDate` date DEFAULT NULL COMMENT 'OBU失效日期',
    `OBUElectrical` tinyint DEFAULT NULL COMMENT 'OBU电量',
    `OBUState` tinyint DEFAULT NULL COMMENT 'OBU状态',
    `OBUVehiclePlate` varchar(32) DEFAULT NULL COMMENT 'OBU内车牌',
    `OBUVehicleType` tinyint DEFAULT NULL COMMENT 'OBU内车辆类型',
    `vehicleUserType` tinyint DEFAULT NULL COMMENT '车辆用户类型',
    `vehicleSeat` tinyint DEFAULT NULL COMMENT '车辆座位数',
    `axleCount` tinyint DEFAULT NULL COMMENT '轴数',
    `totalWeight` int DEFAULT NULL COMMENT '总重量(kg)',
    `vehicleLength` decimal(6,2) DEFAULT NULL COMMENT '车辆长度(m)',
    `vehicleWidth` decimal(6,2) DEFAULT NULL COMMENT '车辆宽度(m)',
    `vehicleHight` decimal(6,2) DEFAULT NULL COMMENT '车辆高度(m)',
    `CPUNetID` varchar(32) DEFAULT NULL COMMENT 'CPU卡网络ID',
    `CPUIssueID` varchar(32) DEFAULT NULL COMMENT 'CPU卡发行方ID',
    `CPUVehiclePlate` varchar(32) DEFAULT NULL COMMENT 'CPU卡内车牌',
    `CPUVehicleType` tinyint DEFAULT NULL COMMENT 'CPU卡内车辆类型',
    `CPUStartDate` date DEFAULT NULL COMMENT 'CPU卡生效日期',
    `CPUEndDate` date DEFAULT NULL COMMENT 'CPU卡失效日期',
    `CPUVersion` varchar(32) DEFAULT NULL COMMENT 'CPU卡版本',
    `CPUCardType` tinyint DEFAULT NULL COMMENT 'CPU卡类型',
    `CPUCardId` varchar(64) DEFAULT NULL COMMENT 'CPU卡ID',
    `balanceBefore` decimal(10,2) DEFAULT NULL COMMENT '余额(前)',
    `balanceAfter` decimal(10,2) DEFAULT NULL COMMENT '余额(后)',
    `gantryPassCount` int DEFAULT NULL COMMENT '门架通行次数',
    `gantryPassInfo` varchar(256) DEFAULT NULL COMMENT '门架通行信息',
    `feeProvInfo` varchar(256) DEFAULT NULL COMMENT '费用省份信息',
    `feeSumLocalBefore` decimal(10,2) DEFAULT NULL COMMENT '本地费用总和(前)',
    `feeSumLocalAfter` decimal(10,2) DEFAULT NULL COMMENT '本地费用总和(后)',
    `feeCalcSpecial` varchar(128) DEFAULT NULL COMMENT '特殊费用计算',
    `feeCalcResult` varchar(128) DEFAULT NULL COMMENT '费用计算结果',
    `feeInfo1` varchar(128) DEFAULT NULL COMMENT '费用信息1',
    `feeInfo2` varchar(128) DEFAULT NULL COMMENT '费用信息2',
    `feeInfo3` varchar(128) DEFAULT NULL COMMENT '费用信息3',
    `OBUpayFeeSumBefore` decimal(10,2) DEFAULT NULL COMMENT 'OBU支付费用总和(前)',
    `OBUpayFeeSumAfter` decimal(10,2) DEFAULT NULL COMMENT 'OBU支付费用总和(后)',
    `OBUdiscountFeeSumBefore` decimal(10,2) DEFAULT NULL COMMENT 'OBU优惠费用总和(前)',
    `OBUdiscountFeeSumAfter` decimal(10,2) DEFAULT NULL COMMENT 'OBU优惠费用总和(后)',
    `OBUProvfeeSumBefore` decimal(10,2) DEFAULT NULL COMMENT 'OBU省份费用总和(前)',
    `OBUProvfeeSumAfter` decimal(10,2) DEFAULT NULL COMMENT 'OBU省份费用总和(后)',
    `cardfeeSumBefore` decimal(10,2) DEFAULT NULL COMMENT '卡费用总和(前)',
    `cardfeeSumAfter` decimal(10,2) DEFAULT NULL COMMENT '卡费用总和(后)',
    `noCardTimesBefore` int DEFAULT NULL COMMENT '无卡次数(前)',
    `noCardTimesAfter` int DEFAULT NULL COMMENT '无卡次数(后)',
    `provinceNumBefore` int DEFAULT NULL COMMENT '省份数量(前)',
    `provinceNumAfter` int DEFAULT NULL COMMENT '省份数量(后)',
    `OBUTotalTradeSuccNumBefore` int DEFAULT NULL COMMENT 'OBU总交易成功次数(前)',
    `OBUTotalTradeSuccNumAfter` int DEFAULT NULL COMMENT 'OBU总交易成功次数(后)',
    `OBUProvTradeSuccNumBefore` int DEFAULT NULL COMMENT 'OBU省份交易成功次数(前)',
    `OBUProvTradeSuccNumAfter` int DEFAULT NULL COMMENT 'OBU省份交易成功次数(后)',
    `OBUTradeResult` tinyint DEFAULT NULL COMMENT 'OBU交易结果',
    `tradeType` tinyint DEFAULT NULL COMMENT '交易类型',
    `OBUInfoTypeRead` tinyint DEFAULT NULL COMMENT 'OBU读取信息类型',
    `OBUInfoTypeWrite` tinyint DEFAULT NULL COMMENT 'OBU写入信息类型',
    `OBUPassState` tinyint DEFAULT NULL COMMENT 'OBU通行状态',
    `feeVehicleType` tinyint DEFAULT NULL COMMENT '收费车辆类型',
    `OBULastGantryHex` varchar(16) DEFAULT NULL COMMENT 'OBU上一门架十六进制编码',
    `OBULastGantryTime` datetime DEFAULT NULL COMMENT 'OBU上一门架时间',
    `feeMileage` decimal(10,2) DEFAULT NULL COMMENT '收费里程(km)',
    `OBUMileageBefore` decimal(10,2) DEFAULT NULL COMMENT 'OBU里程(前)',
    `OBUMileageAfter` decimal(10,2) DEFAULT NULL COMMENT 'OBU里程(后)',
    `tradeReadCiphertext` varchar(256) DEFAULT NULL COMMENT '交易读取密文',
    `readCiphertextVerify` tinyint DEFAULT NULL COMMENT '读取密文验证结果',
    `tradeWriteCiphertext` varchar(256) DEFAULT NULL COMMENT '交易写入密文',
    `provMinFee` decimal(10,2) DEFAULT NULL COMMENT '省份最低费用',
    `provMinFeeCalcMode` tinyint DEFAULT NULL COMMENT '省份最低费用计算方式',
    `feeSpare1` varchar(128) DEFAULT NULL COMMENT '备用费用字段1',
    `feeSpare2` varchar(128) DEFAULT NULL COMMENT '备用费用字段2',
    `feeSpare3` varchar(128) DEFAULT NULL COMMENT '备用费用字段3',
    `feeProvBeginHex` varchar(16) DEFAULT NULL COMMENT '费用省份起始十六进制编码',
    `rateCompute` varchar(128) DEFAULT NULL COMMENT '费率计算信息',
    `rateFitCount` int DEFAULT NULL COMMENT '费率匹配次数',
    `OBUFeeSumBefore` decimal(10,2) DEFAULT NULL COMMENT 'OBU费用总和(前)',
    `OBUFeeSumAfter` decimal(10,2) DEFAULT NULL COMMENT 'OBU费用总和(后)',
    `OBUProvPayFeeSumBefore` decimal(10,2) DEFAULT NULL COMMENT 'OBU省份支付费用总和(前)',
    `OBUProvPayFeeSumAfter` decimal(10,2) DEFAULT NULL COMMENT 'OBU省份支付费用总和(后)',
    `pathFitFlag` tinyint DEFAULT NULL COMMENT '路径匹配标志',
    `feeCalcSpecials` varchar(256) DEFAULT NULL COMMENT '特殊费用计算集合',
    `payFeeProvSumLocal` decimal(10,2) DEFAULT NULL COMMENT '本地省份支付费用总和',
    `PCRSUVersion` varchar(32) DEFAULT NULL COMMENT 'PCRSU版本',
    `gantryPassInfoAfter` varchar(256) DEFAULT NULL COMMENT '门架通行信息(后)',
    `updateResult` tinyint DEFAULT NULL COMMENT '更新结果',
    `CPCFeeTradeResult` tinyint DEFAULT NULL COMMENT 'CPC费用交易结果',
    `feeProvEF04` varchar(128) DEFAULT NULL COMMENT '省份EF04费用信息',
    `fitProvFlag` tinyint DEFAULT NULL COMMENT '匹配省份标志',
    `gantryPassCountBefore` int DEFAULT NULL COMMENT '门架通行次数(前)',
    `feeProvBeginHexFit` varchar(16) DEFAULT NULL COMMENT '匹配的省份起始十六进制编码',
    `feeProvBeginTimeFit` datetime DEFAULT NULL COMMENT '匹配的省份起始时间',
    `feeProvBeginTime` datetime DEFAULT NULL COMMENT '省份起始时间',
    `feeSumLocalAfterEF04` decimal(10,2) DEFAULT NULL COMMENT 'EF04本地费用总和(后)',
    `lastGantryFeePass` varchar(16) DEFAULT NULL COMMENT '上一收费门架',
    `lastGantryMilePass` varchar(16) DEFAULT NULL COMMENT '上一里程门架',
    `holidayState` tinyint DEFAULT NULL COMMENT '节假日状态',
    `tradeResult` tinyint DEFAULT NULL COMMENT '交易结果',
    `lastGantryHexFee` varchar(16) DEFAULT NULL COMMENT '上一收费门架十六进制编码',
    `lastGantryHexPass` varchar(16) DEFAULT NULL COMMENT '上一通行门架十六进制编码',
    `specialType` tinyint DEFAULT NULL COMMENT '特殊类型',
    `chargesSpecialType` tinyint DEFAULT NULL COMMENT '收费特殊类型',
    `verifyCode` varchar(32) DEFAULT NULL COMMENT '验证码',
    `interruptSignal` tinyint DEFAULT NULL COMMENT '中断信号',
    `vehiclePicId` varchar(64) DEFAULT NULL COMMENT '车辆图片ID',
    `vehicleTailPicId` varchar(64) DEFAULT NULL COMMENT '车尾图片ID',
    `matchStatus` tinyint DEFAULT NULL COMMENT '匹配状态',
    `validStatus` tinyint DEFAULT NULL COMMENT '有效状态',
    `dealStatus` tinyint DEFAULT NULL COMMENT '处理状态',
    `isFixData` tinyint DEFAULT NULL COMMENT '是否修正数据',
    `relatedTradeId` varchar(64) DEFAULT NULL COMMENT '关联交易ID',
    `allRelatedTradeId` varchar(256) DEFAULT NULL COMMENT '所有关联交易ID',
    `stationDBTime` datetime DEFAULT NULL COMMENT '站点数据库时间',
    `stationDealTime` datetime DEFAULT NULL COMMENT '站点处理时间',
    `stationValidTime` datetime DEFAULT NULL COMMENT '站点验证时间',
    `stationMatchTime` datetime DEFAULT NULL COMMENT '站点匹配时间',
    `RSUManuid` varchar(32) DEFAULT NULL COMMENT 'RSU厂商ID',
    `feeDataVersion` varchar(32) DEFAULT NULL COMMENT '费用数据版本',
    `gantryHexOppotime` datetime DEFAULT NULL COMMENT '对向门架时间',
    `CREATETIME` datetime DEFAULT NULL COMMENT '创建时间',
    `messageTime` datetime DEFAULT NULL COMMENT '消息时间',
    `LASTUPATETIME` datetime DEFAULT NULL COMMENT '最后更新时间',
    `offset` int DEFAULT NULL COMMENT '偏移量',
    `dataId` varchar(64) NOT NULL COMMENT '数据ID(主键)',
    `partitionId` varchar(32) DEFAULT NULL COMMENT '分区ID',
    PRIMARY KEY (`dataId`),
    INDEX idx_transTime (`transTime`),
    INDEX idx_vehiclePlate (`vehiclePlate`),
    INDEX idx_gantryHex (`gantryHex`)
) ENGINE=InnoDB DEFAULT CHARSET={{charset}} COMMENT='ETCTU门架交易数据表';
"""

# -------------------------- 月份生成与时间工具 --------------------------
def generate_month_options(months_count=12):
    month_options = []
    now = datetime.datetime.now()
    for i in range(months_count):
        y = now.year
        m = now.month - i
        while m <= 0:
            y -= 1
            m += 12
        month_options.append(f"{y}-{m:02d}")
    month_options.sort()
    return month_options

def validate_month_format(month_str):
    try:
        datetime.datetime.strptime(month_str, '%Y-%m')
        return True
    except ValueError:
        return False

def get_dates_in_month(month_str):
    if not validate_month_format(month_str):
        raise ValueError(f"月份格式错误：{month_str}，正确格式YYYY-MM")
    year, month = map(int, month_str.split('-'))
    import calendar
    days = calendar.monthrange(year, month)[1]
    return [f"{year}-{month:02d}-{day:02d}" for day in range(1, days + 1)]

def validate_sync_date_range(date_range_str: str) -> Tuple[bool, Optional[Tuple[int, int]]]:
    """验证同步日期区间格式"""
    if not date_range_str:
        return False, None
    pattern = r'^\d{1,2},\d{1,2}$'
    if not re.match(pattern, date_range_str):
        return False, None
    start_day, end_day = map(int, date_range_str.split(','))
    if start_day < 1 or end_day > 31 or start_day > end_day:
        return False, None
    return True, (start_day, end_day)

def is_current_date_in_range(date_range_str: str) -> bool:
    """检查当前日期是否在允许的同步区间内"""
    valid, date_range = validate_sync_date_range(date_range_str)
    if not valid:
        return True  # 格式错误时允许同步
    current_day = datetime.datetime.now().day
    return date_range[0] <= current_day <= date_range[1]

def get_table_name_by_date(date_str: str) -> str:
    """根据日期生成表名：gbupload_etctu_as_YYYYMMDD"""
    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return f"{FIXED_TABLE_PREFIX}{date_obj.strftime('%Y%m%d')}"
    except ValueError:
        raise ValueError(f"日期格式错误：{date_str}，正确格式YYYY-MM-DD")

def save_last_sync_time(sync_time_file: str, sync_date: str):
    """保存最后同步时间"""
    try:
        dir_path = os.path.dirname(sync_time_file)
        ensure_dir(dir_path)
        with open(sync_time_file, 'w', encoding='utf-8') as f:
            f.write(f"最后同步日期：{sync_date}\n")
            f.write(f"同步时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        return True
    except Exception as e:
        logging.error(f"保存同步时间失败：{e}")
        return False

# -------------------------- 日志配置 --------------------------
def init_logger(log_path):
    log_dir = os.path.dirname(log_path)
    ensure_dir(log_dir)

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    return logging.getLogger(__name__)

# -------------------------- 配置文件处理 --------------------------
def load_config():
    """加载配置，确保节点完整性"""
    config = configparser.ConfigParser(interpolation=None)
    try:
        config.read(CONFIG_FILE, encoding='utf-8')
    except Exception as e:
        logging.warning(f"配置文件读取失败，使用默认配置：{e}")
    
    # 预设默认配置（确保节点和键完整）
    default_config = {
        'REMOTE_DB': {
            'host': '192.168.1.100',
            'port': '3306',
            'user': 'read_only',
            'password': '',
            'database': 'branchdb',
            'charset': 'utf8mb4'
        },
        'LOCAL_DB': {
            'host': '127.0.0.1',
            'port': '3306',
            'user': 'root',
            'password': '',
            'database': 'branchdb',
            'charset': 'utf8mb3'
        },
        'SYNC': {
            'sync_months': datetime.datetime.now().strftime('%Y-%m'),
            'log_path': DEFAULT_LOG_PATH,
            'sync_time_file': DEFAULT_SYNC_TIME_FILE,
            'sync_date_range': DEFAULT_SYNC_DATE_RANGE,
            'primary_keys': 'dataId',  # 修改为单主键（dataId更可靠）
            'batch_size': '1000',  # 批量大小默认1000
            'retry_count': '3',  # 重试次数
            'timeout': '30'  # 数据库超时时间
        }
    }

    # 补全缺失的节点和键
    for section, section_config in default_config.items():
        if section not in config.sections():
            config[section] = section_config
        else:
            for key, default_value in section_config.items():
                if key not in config[section]:
                    config[section][key] = default_value

    # 规范化日志与同步时间文件路径为程序log目录
    try:
        sync_section = config['SYNC']
        log_path = sync_section.get('log_path', '').strip()
        time_path = sync_section.get('sync_time_file', '').strip()
        if not log_path or not os.path.abspath(log_path).startswith(os.path.abspath(DEFAULT_LOG_DIR)):
            sync_section['log_path'] = DEFAULT_LOG_PATH
        if not time_path or not os.path.abspath(time_path).startswith(os.path.abspath(DEFAULT_LOG_DIR)):
            sync_section['sync_time_file'] = DEFAULT_SYNC_TIME_FILE
    except Exception:
        # 若SYNC不存在，直接使用默认
        config['SYNC'] = default_config['SYNC']

    # 保存补全后的配置（确保配置文件格式正确）
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            config.write(f)
        logging.info(f"配置文件初始化成功：{CONFIG_FILE}")
    except Exception as e:
        logging.error(f"配置文件保存失败：{e}")
    
    return config

def save_config(config):
    """保存配置，带权限检查"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            config.write(f)
        logging.info(f"配置文件保存成功：{CONFIG_FILE}")
        return True
    except PermissionError:
        logging.error(f"无权限写入配置文件：{CONFIG_FILE}")
        messagebox.showerror("权限错误", f"无法写入配置文件，请检查目录权限：\n{CONFIG_FILE}")
        return False
    except Exception as e:
        logging.error(f"保存配置文件失败：{e}")
        messagebox.showerror("保存失败", f"配置保存失败：{str(e)}")
        return False

# -------------------------- 数据库操作 --------------------------
def create_db_connection(db_type: str, config: configparser.ConfigParser, override: Dict[str, str] = None) -> Optional[pymysql.connections.Connection]:
    """创建数据库连接"""
    try:
        cfg = dict(config[db_type])
        if override:
            cfg.update(override)
        logging.debug(f"准备连接 {db_type}：{cfg['host']}:{cfg['port']}/{cfg['database']}")
        conn = pymysql.connect(
            host=cfg['host'],
            port=int(cfg['port']),
            user=cfg['user'],
            password=cfg['password'],
            database=cfg['database'],
            charset=cfg['charset'],
            connect_timeout=int(config['SYNC']['timeout']),
            cursorclass=pymysql.cursors.DictCursor
        )
        logging.info(f"{db_type} 数据库连接成功：{cfg['host']}:{cfg['port']}/{cfg['database']}")
        return conn
    except pymysql.err.OperationalError as e:
        logging.error(f"{db_type} 数据库连接失败（操作错误）：{e}", exc_info=True)
        messagebox.showerror("连接失败", f"{db_type} 数据库连接失败：\n{e}\n请检查主机、端口、数据库名是否正确")
    except pymysql.err.AccessDeniedError as e:
        logging.error(f"{db_type} 数据库连接失败（权限错误）：{e}", exc_info=True)
        messagebox.showerror("连接失败", f"{db_type} 数据库连接失败：\n{e}\n请检查用户名和密码是否正确")
    except Exception as e:
        logging.error(f"{db_type} 数据库连接失败：{e}", exc_info=True)
        messagebox.showerror("连接失败", f"{db_type} 数据库连接失败：\n{str(e)}")
    return None

# -------------------------- GUI界面 --------------------------
class MySQLSyncGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ETCTU数据同步工具（多月份+校验版）V1.4")
        self.root.geometry("1100x950")  # 进一步增大窗口
        self.root.resizable(True, True)

        # 初始化配置和日志
        self.config = load_config()
        self.logger = init_logger(self.config['SYNC']['log_path'])
        self.entry_vars = {}
        self.month_listbox = None
        self.progress_bar = None
        self.sync_thread = None
        self.is_sync_running = False

        # 设置全局样式
        self.setup_style()
        
        self.create_widgets()
        self.load_saved_months()

    def setup_style(self):
        """设置全局样式"""
        self.style = ttk.Style()
        # 按钮样式
        self.style.configure("Custom.TButton", 
                           font=("微软雅黑", 9, "bold"),
                           padding=8,
                           relief=tk.RAISED)
        # 标签样式
        self.style.configure("Custom.TLabel",
                           font=("微软雅黑", 8))
        # 输入框样式
        self.style.configure("Custom.TEntry",
                           font=("微软雅黑", 9),
                           padding=4)
        # 框架标题样式
        self.style.configure("Custom.TLabelframe.Label",
                           font=("微软雅黑", 9, "bold"),
                           foreground="#2c3e50")

    def create_widgets(self):
        """创建所有组件（简化布局，确保按钮可见）"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标签页控件
        tab_control = ttk.Notebook(main_frame)
        tab1 = ttk.Frame(tab_control, padding="10")
        tab2 = ttk.Frame(tab_control, padding="10")
        tab_control.add(tab1, text="配置与同步")
        tab_control.add(tab2, text="同步日志")
        tab_control.pack(fill=tk.BOTH, expand=True, pady=5)

        # -------------------------- 配置与同步标签页 --------------------------
        # 顶部配置行：远程与本地数据库配置并排显示
        top_config_row = ttk.Frame(tab1)
        top_config_row.pack(fill=tk.X, pady=6, padx=5)
        top_config_row.grid_columnconfigure(0, weight=1)
        top_config_row.grid_columnconfigure(1, weight=1)

        remote_frame = ttk.LabelFrame(top_config_row, text="远程数据库（只读）配置", style="Custom.TLabelframe")
        remote_frame.grid(row=0, column=0, sticky="nwe", padx=5)
        self.create_db_config_frame(remote_frame, "REMOTE_DB")

        local_frame = ttk.LabelFrame(top_config_row, text="本地数据库（可写）配置", style="Custom.TLabelframe")
        local_frame.grid(row=0, column=1, sticky="nwe", padx=5)
        self.create_db_config_frame(local_frame, "LOCAL_DB")

        # 同步配置
        sync_frame = ttk.LabelFrame(tab1, text="同步配置", style="Custom.TLabelframe")
        sync_frame.pack(fill=tk.X, pady=6, padx=5)
        self.create_sync_config_frame(sync_frame)

        # 进度条区域
        progress_frame = ttk.LabelFrame(tab1, text="同步进度", style="Custom.TLabelframe")
        progress_frame.pack(fill=tk.X, pady=6, padx=5)
        self.create_progress_frame(progress_frame)

        # 关键修复：按钮区域采用grid两行布局，避免横向溢出
        button_frame = ttk.Frame(tab1, padding="8")
        button_frame.pack(fill=tk.X, pady=8, padx=5)
        
        # 操作按钮（不包含测试连接按钮，测试按钮已移至各自配置框内）
        self.save_btn = ttk.Button(button_frame, text="保存配置", 
                                  command=self.save_config_click,
                                  style="Custom.TButton", width=12)
        self.save_btn.grid(row=0, column=0, padx=8, pady=4, sticky="w")

        self.sync_btn = ttk.Button(button_frame, text="开始同步", 
                                  command=self.start_sync,
                                  style="Custom.TButton", width=12)
        self.sync_btn.grid(row=0, column=1, padx=8, pady=4, sticky="w")

        self.stop_btn = ttk.Button(button_frame, text="停止同步", 
                                  command=self.stop_sync,
                                  style="Custom.TButton", width=12,
                                  state="disabled")
        self.stop_btn.grid(row=0, column=2, padx=8, pady=4, sticky="w")

        # -------------------------- 同步日志标签页 --------------------------
        log_frame = ttk.Frame(tab2)
        log_frame.pack(fill=tk.BOTH, expand=True)

        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, 
                                                 font=("Consolas", 10),
                                                 width=100, height=28)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 日志控制按钮
        log_btn_frame = ttk.Frame(tab2)
        log_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(log_btn_frame, text="刷新日志", command=self.load_log,
                  style="Custom.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(log_btn_frame, text="清空日志", command=self.clear_log,
                  style="Custom.TButton").pack(side=tk.LEFT, padx=10)

        self.load_log()

    def create_db_config_frame(self, parent, db_type):
        """创建数据库配置框架（简化布局）"""
        # 使用grid布局，2列，确保标签和输入框对齐
        parent.grid_columnconfigure(1, weight=0)
        
        fields = [("host", "主机："),
                 ("port", "端口："),
                 ("user", "用户名："),
                 ("password", "密码："),
                 ("database", "数据库名："),
                 ("charset", "字符集：")]
        
        for row, (key, label) in enumerate(fields):
            ttk.Label(parent, text=label, style="Custom.TLabel").grid(row=row, column=0, 
                                                                    sticky="w", padx=10, pady=5)
            var = tk.StringVar(value=self.config[db_type][key])
            entry = ttk.Entry(parent, textvariable=var, 
                            show="*" if key == "password" else "",
                            style="Custom.TEntry", width=28)
            entry.grid(row=row, column=1, sticky="w", padx=10, pady=5)
            self.entry_vars[f"{db_type}_{key}"] = var

        # 测试连接按钮放置在各自配置框内下方
        test_text = "测试远程连接" if db_type == "REMOTE_DB" else "测试本地连接"
        test_cmd = self.test_remote_connection if db_type == "REMOTE_DB" else self.test_local_connection
        ttk.Button(parent, text=test_text, command=test_cmd, style="Custom.TButton", width=14).grid(
            row=len(fields), column=0, columnspan=2, sticky="w", padx=10, pady=6
        )

    def create_sync_config_frame(self, parent):
        """创建同步配置框架（简化布局）"""
        # 月份选择
        month_frame = ttk.Frame(parent)
        month_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(month_frame, text="同步月份：", style="Custom.TLabel").pack(side=tk.LEFT, padx=10)
        
        self.month_listbox = tk.Listbox(month_frame, selectmode=tk.MULTIPLE,
                                       width=28, height=7, font=("微软雅黑", 9))
        self.month_listbox.pack(side=tk.LEFT, padx=10)
        
        # 月份操作按钮
        btn_frame = ttk.Frame(month_frame)
        btn_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(btn_frame, text="全选", command=self.select_all_months,
                  style="Custom.TButton").pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="取消全选", command=self.deselect_all_months,
                  style="Custom.TButton").pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="反选", command=self.invert_select_months,
                  style="Custom.TButton").pack(fill=tk.X, pady=2)

        # 其他配置项（简化为2列布局）
        config_frame = ttk.Frame(parent)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        configs = [
            ("sync_date_range", "同步日期区间：", "格式：27,30"),
            ("primary_keys", "主键字段：", "默认：dataId"),
            ("batch_size", "批量大小：", "1000-5000"),
            ("retry_count", "重试次数：", "默认：3"),
            ("timeout", "超时时间(秒)：", "默认：30"),
            ("log_path", "日志路径：", ""),
            ("sync_time_file", "同步时间文件：", "")
        ]
        
        for i, (key, label, tip) in enumerate(configs):
            row = i // 2
            col = i % 2
            
            sub_frame = ttk.Frame(config_frame)
            sub_frame.grid(row=row, column=col, sticky="we", padx=10, pady=5)
            
            ttk.Label(sub_frame, text=label, style="Custom.TLabel").pack(side=tk.LEFT, padx=5)
            var = tk.StringVar(value=self.config['SYNC'][key])
            entry = ttk.Entry(sub_frame, textvariable=var, style="Custom.TEntry", width=30)
            entry.pack(side=tk.LEFT, padx=5)
            self.entry_vars[f"SYNC_{key}"] = var
            
            if tip:
                ttk.Label(sub_frame, text=tip, font=("微软雅黑", 8), 
                         foreground="gray").pack(side=tk.LEFT, padx=5)

    def create_progress_frame(self, parent):
        """创建进度条框架"""
        self.progress_bar = ttk.Progressbar(parent, orient="horizontal", 
                                           length=900, mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=20, pady=15)
        
        self.progress_label = ttk.Label(parent, text="未开始同步", style="Custom.TLabel")
        self.progress_label.pack(pady=5)

    # -------------------------- 按钮功能实现 --------------------------
    def test_remote_connection(self):
        """测试远程数据库连接"""
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        
        try:
            override = {}
            for k in ["host","port","user","password","database","charset"]:
                v = self.entry_vars.get(f"REMOTE_DB_{k}")
                if v is not None:
                    override[k] = v.get().strip()
            conn = create_db_connection("REMOTE_DB", self.config, override)
            if conn:
                conn.close()
                messagebox.showinfo("成功", "远程数据库连接成功！")
                self.logger.info("远程数据库连接测试通过")
            else:
                messagebox.showerror("失败", "远程数据库连接失败！")
        finally:
            self.root.config(cursor="")
            self.root.update_idletasks()

    def test_local_connection(self):
        """测试本地数据库连接"""
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        
        try:
            override = {}
            for k in ["host","port","user","password","database","charset"]:
                v = self.entry_vars.get(f"LOCAL_DB_{k}")
                if v is not None:
                    override[k] = v.get().strip()
            conn = create_db_connection("LOCAL_DB", self.config, override)
            if conn:
                conn.close()
                messagebox.showinfo("成功", "本地数据库连接成功！")
                self.logger.info("本地数据库连接测试通过")
            else:
                messagebox.showerror("失败", "本地数据库连接失败！")
        finally:
            self.root.config(cursor="")
            self.root.update_idletasks()

    def save_config_click(self):
        """核心修改：直接保存所有GUI参数到配置文件，不做额外验证"""
        try:
            # 1. 读取所有输入框参数并更新到配置对象
            sections = ["REMOTE_DB", "LOCAL_DB", "SYNC"]
            for var_key, var in self.entry_vars.items():
                section = None
                for s in sections:
                    if var_key.startswith(s + "_"):
                        section = s
                        break
                if not section:
                    continue
                key = var_key[len(section) + 1:]
                new_value = var.get().strip()
                self.config[section][key] = new_value
                self.logger.info(f"保存配置：{section}.{key} = {new_value}")

            # 2. 保存选中的同步月份（Listbox中选中的所有月份）
            selected_months = self.get_selected_months()
            self.logger.debug(f"当前选中月份：{selected_months}")
            self.config['SYNC']['sync_months'] = ",".join(selected_months)
            self.logger.info(f"保存选中同步月份：{','.join(selected_months) if selected_months else '无'}")

            # 3. 直接写入配置文件（覆盖原有配置）
            if save_config(self.config):
                # 更新日志配置（如果日志路径有修改）
                self.logger = init_logger(self.config['SYNC']['log_path'])
                messagebox.showinfo("保存成功", "所有配置参数已直接保存到配置文件！")
                self.logger.info("配置保存完成：GUI中所有参数已同步到config.ini")
                return True

        except Exception as e:
            messagebox.showerror("保存失败", f"配置保存失败：{str(e)}")
            self.logger.error(f"配置保存失败：{str(e)}", exc_info=True)
        
        return False

    # -------------------------- 月份选择功能 --------------------------
    def select_all_months(self):
        for i in range(self.month_listbox.size()):
            self.month_listbox.selection_set(i)

    def deselect_all_months(self):
        self.month_listbox.selection_clear(0, tk.END)

    def invert_select_months(self):
        for i in range(self.month_listbox.size()):
            if self.month_listbox.selection_includes(i):
                self.month_listbox.selection_clear(i)
            else:
                self.month_listbox.selection_set(i)

    def get_selected_months(self):
        selected_indices = self.month_listbox.curselection()
        return [self.month_listbox.get(idx) for idx in selected_indices]

    def load_saved_months(self):
        """加载保存的月份选择"""
        saved_months = self.config['SYNC']['sync_months'].split(',')
        saved_months = [m.strip() for m in saved_months if m.strip()]
        
        # 填充月份列表
        month_options = generate_month_options(12)
        for month in month_options:
            self.month_listbox.insert(tk.END, month)
        
        # 选中保存的月份
        for i, month in enumerate(month_options):
            if month in saved_months:
                self.month_listbox.selection_set(i)

    # -------------------------- 同步功能 --------------------------
    def update_progress(self, current, total, message):
        """更新进度条"""
        def _update():
            progress = (current / total) * 100 if total > 0 else 0
            self.progress_bar["value"] = progress
            self.progress_label.config(text=f"{message}（{current}/{total}）")
        self.root.after(0, _update)

    def start_sync(self):
        """开始同步"""
        if self.is_sync_running:
            messagebox.showwarning("提示", "同步正在进行中！")
            return

        # 保存配置（直接保存，不做额外验证）
        if not self.save_config_click():
            if not messagebox.askyesno("提示", "配置保存失败，是否继续同步？"):
                return

        self.logger.debug("准备读取选中月份并开始同步")
        selected_months = self.get_selected_months()
        if not selected_months:
            messagebox.showwarning("提示", "请选择同步月份！")
            return

        # 初始化状态
        self.is_sync_running = True
        self.sync_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress_bar["value"] = 0
        self.progress_label.config(text="准备同步...")

        self.logger.debug(f"创建同步线程，月份：{selected_months}")
        self.sync_thread = threading.Thread(target=self.run_sync, args=(selected_months,))
        self.sync_thread.daemon = True
        self.sync_thread.start()

    def stop_sync(self):
        """停止同步"""
        self.is_sync_running = False
        self.stop_btn.config(state="disabled")
        self.progress_label.config(text="正在停止同步...")
        self.logger.info("用户停止同步")

    def run_sync(self, selected_months):
        """执行同步"""
        total_success = 0
        total_fail = 0
        total_tables = 0

        try:
            # 读取配置（直接使用保存的参数，不做验证）
            batch_size = int(self.config['SYNC']['batch_size']) if self.config['SYNC']['batch_size'].strip().isdigit() else 1000
            retry_count = int(self.config['SYNC']['retry_count']) if self.config['SYNC']['retry_count'].strip().isdigit() else 3
            primary_keys = [k.strip() for k in self.config['SYNC']['primary_keys'].split(',') if k.strip()] or ['dataId']
            local_charset = self.config['LOCAL_DB']['charset']

            self.logger.info(f"开始同步：{selected_months}")
            self.logger.debug(f"批量大小：{batch_size}，重试次数：{retry_count}，主键：{primary_keys}")

            # 收集表
            tables_to_sync = []
            for month in selected_months:
                dates = get_dates_in_month(month)
                for date in dates:
                    tables_to_sync.append((month, date, get_table_name_by_date(date)))
            
            total_tables = len(tables_to_sync)
            if total_tables == 0:
                self.root.after(0, lambda: messagebox.showwarning("提示", "没有找到要同步的表！"))
                return

            self.logger.debug(f"待同步表数量：{total_tables}")
            # 连接数据库
            remote_conn = None
            local_conn = None

            # 远程连接
            for i in range(retry_count):
                if not self.is_sync_running:
                    break
                self.update_progress(0, total_tables, f"连接远程数据库（{i+1}/{retry_count}）")
                remote_conn = create_db_connection("REMOTE_DB", self.config)
                if remote_conn:
                    break
                time.sleep(2)

            if not remote_conn:
                self.logger.error("远程数据库连接失败")
                self.root.after(0, lambda: messagebox.showerror("失败", "远程数据库连接失败！"))
                return

            # 本地连接
            for i in range(retry_count):
                if not self.is_sync_running:
                    break
                self.update_progress(0, total_tables, f"连接本地数据库（{i+1}/{retry_count}）")
                local_conn = create_db_connection("LOCAL_DB", self.config)
                if local_conn:
                    break
                time.sleep(2)

            if not local_conn:
                remote_conn.close()
                self.logger.error("本地数据库连接失败")
                self.root.after(0, lambda: messagebox.showerror("失败", "本地数据库连接失败！"))
                return

            # 同步每个表
            for idx, (month, date, table_name) in enumerate(tables_to_sync):
                if not self.is_sync_running:
                    break

                self.update_progress(idx + 1, total_tables, f"同步 {table_name}")
                
                try:
                    # 创建表
                    self.create_table_if_not_exists(local_conn, table_name, local_charset)
                    
                    # 分页同步
                    offset = 0
                    while True:
                        if not self.is_sync_running:
                            break
                            
                        self.logger.debug(f"查询远程表：{table_name}，limit={batch_size}，offset={offset}")
                        data, success = self.query_remote_data(remote_conn, table_name, batch_size, offset)
                        if not success or not data:
                            break
                            
                        # 批量插入更新
                        self.logger.debug(f"写入本地表：{table_name}，记录数：{len(data)}")
                        succ, fail = self.batch_upsert_local_data(local_conn, table_name, data, primary_keys)
                        total_success += succ
                        total_fail += fail
                        
                        if len(data) < batch_size:
                            break
                            
                        offset += batch_size

                except Exception as e:
                    total_fail += 1
                    self.logger.error(f"同步 {table_name} 失败：{e}", exc_info=True)

            # 保存同步时间
            if self.is_sync_running:
                save_last_sync_time(self.config['SYNC']['sync_time_file'], 
                                  datetime.datetime.now().strftime('%Y-%m-%d'))

        except Exception as e:
            self.logger.error(f"同步异常：{e}", exc_info=True)
            self.root.after(0, lambda: messagebox.showerror("失败", f"同步异常：{str(e)}"))
        finally:
            # 关闭连接
            if 'remote_conn' in locals() and remote_conn:
                try:
                    remote_conn.close()
                except:
                    pass
            if 'local_conn' in locals() and local_conn:
                try:
                    local_conn.close()
                except:
                    pass

            # 恢复状态
            self.is_sync_running = False
            self.root.after(0, lambda: self.sync_btn.config(state="normal"))
            self.root.after(0, lambda: self.stop_btn.config(state="disabled"))
            
            # 更新进度
            result_msg = f"同步完成：成功 {total_success} 条，失败 {total_fail} 条"
            self.root.after(0, lambda: self.progress_label.config(text=result_msg))
            self.root.after(0, lambda: messagebox.showinfo("同步结果", result_msg))
            
            self.logger.info(f"同步结束：{result_msg}")
            self.root.after(0, self.load_log)

    # -------------------------- 数据库操作辅助方法 --------------------------
    def create_table_if_not_exists(self, conn, table_name, charset):
        """创建表"""
        try:
            self.logger.debug(f"创建或检查本地表：{table_name}，字符集：{charset}")
            with conn.cursor() as cursor:
                create_sql = CREATE_TABLE_SQL.format(table_name=table_name, charset=charset)
                cursor.execute(create_sql)
                conn.commit()
            self.logger.info(f"表 {table_name} 创建/检查成功")
            return True
        except Exception as e:
            self.logger.error(f"创建表 {table_name} 失败：{e}", exc_info=True)
            return False

    def query_remote_data(self, conn, table_name, batch_size, offset):
        """查询远程数据"""
        try:
            fields_str = ', '.join(FIELDS_LIST)
            sql = f"SELECT {fields_str} FROM `{table_name}` LIMIT %s OFFSET %s"
            with conn.cursor() as cursor:
                cursor.execute(sql, (batch_size, offset))
                return cursor.fetchall(), True
        except Exception as e:
            self.logger.error(f"查询 {table_name} 失败：{e}", exc_info=True)
            return [], False

    def batch_upsert_local_data(self, conn, table_name, data_list, primary_keys):
        """批量插入更新"""
        if not data_list:
            return 0, 0

        try:
            fields_str = ', '.join([f'`{f}`' for f in FIELDS_LIST])
            placeholders = ', '.join(['%s'] * len(FIELDS_LIST))
            update_fields = [f'`{f}` = VALUES(`{f}`)' for f in FIELDS_LIST if f not in primary_keys]
            update_str = ', '.join(update_fields)

            sql = f"INSERT INTO `{table_name}` ({fields_str}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_str}"

            with conn.cursor() as cursor:
                values = []
                for data in data_list:
                    values.append([data.get(f) for f in FIELDS_LIST])
                
                self.logger.debug(f"执行批量写入：表={table_name}，记录数={len(values)}")
                cursor.executemany(sql, values)
                conn.commit()
                return len(data_list), 0
        except Exception as e:
            conn.rollback()
            self.logger.error(f"批量插入 {table_name} 失败：{e}", exc_info=True)
            return 0, len(data_list)

    # -------------------------- 日志处理 --------------------------
    def load_log(self):
        """加载日志"""
        self.log_text.delete(1.0, tk.END)
        log_path = self.config['SYNC']['log_path']
        
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    # 读取最后2000行，避免加载过慢
                    lines = f.readlines()[-2000:]
                    self.log_text.insert(tk.END, ''.join(lines))
            except Exception as e:
                self.log_text.insert(tk.END, f"加载日志失败：{str(e)}")
        else:
            self.log_text.insert(tk.END, "日志文件不存在")
        
        self.log_text.see(tk.END)

    def clear_log(self):
        """清空日志"""
        log_path = self.config['SYNC']['log_path']
        if os.path.exists(log_path):
            if messagebox.askyesno("确认", "确定要清空日志吗？"):
                try:
                    with open(log_path, 'w', encoding='utf-8') as f:
                        f.write(f"日志已清空 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    self.load_log()
                    messagebox.showinfo("成功", "日志已清空！")
                except Exception as e:
                    messagebox.showerror("失败", f"清空日志失败：{str(e)}")
        else:
            messagebox.showinfo("提示", "日志文件不存在！")

# -------------------------- 主函数 --------------------------
if __name__ == '__main__':
    # 处理高DPI
    if os.name == 'nt':
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

    # 检查依赖（打包环境不进行自动安装，避免异常子进程与界面阻塞）
    # python-dateutil 已有标准库回退实现，不作为硬性依赖
    required_libs = ['pymysql']
    missing_libs = []
    for lib in required_libs:
        try:
            __import__(lib)
        except ImportError:
            missing_libs.append(lib)

    is_frozen = getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS')
    if missing_libs:
        if is_frozen:
            msg = f"缺少依赖库：{','.join(missing_libs)}\n请使用包含依赖的安装包或联系管理员。"
            print(msg)
            try:
                messagebox.showerror("失败", msg)
            except Exception:
                pass
            sys.exit(1)
        else:
            print(f"缺少依赖库：{','.join(missing_libs)}")
            print("正在自动安装...")
            import subprocess
            for lib in missing_libs:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
                    print(f"{lib} 安装成功")
                except Exception as e:
                    print(f"{lib} 安装失败：{e}")
                    try:
                        messagebox.showerror("失败", f"安装 {lib} 失败，请手动安装！")
                    except Exception:
                        pass
                    sys.exit(1)

    # 启动应用
    temp_logger = init_logger(DEFAULT_LOG_PATH)
    temp_logger.info("启动ETCTU数据同步工具")
    
    root = tk.Tk()
    app = MySQLSyncGUI(root)
    root.mainloop()
    
    temp_logger.info("退出ETCTU数据同步工具")
